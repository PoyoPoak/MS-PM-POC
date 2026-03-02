"""Tests for GET /training/poll, GET /training/download, POST /training/request."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.models import PacemakerTelemetry, TrainingJobRequest

_URL_POLL = f"{settings.API_V1_STR}/training/poll"
_URL_DOWNLOAD = f"{settings.API_V1_STR}/training/download"
_URL_REQUEST = f"{settings.API_V1_STR}/training/request"


def _cleanup(db: Session) -> None:
    """Remove all training job requests and telemetry rows."""
    db.exec(delete(TrainingJobRequest))  # type: ignore[call-overload]
    db.exec(delete(PacemakerTelemetry))  # type: ignore[call-overload]
    db.commit()


def _seed_telemetry(
    db: Session,
    *,
    patient_id: int,
    ts: datetime,
) -> PacemakerTelemetry:
    """Insert a single telemetry row and return the ORM instance."""
    row = PacemakerTelemetry(
        patient_id=patient_id,
        timestamp=ts,
        lead_impedance_ohms=500.0,
        capture_threshold_v=1.0,
        r_wave_sensing_mv=8.0,
        battery_voltage_v=2.8,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# ── Poll endpoint ─────────────────────────────────────────────────


def test_poll_returns_false_when_no_jobs(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    _cleanup(db)
    r = client.get(_URL_POLL, headers=superuser_token_headers)
    assert r.status_code == 200
    assert r.json() is False


def test_poll_returns_true_when_pending_job_exists(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    _cleanup(db)
    db.add(TrainingJobRequest(is_pending=True))
    db.commit()

    r = client.get(_URL_POLL, headers=superuser_token_headers)
    assert r.status_code == 200
    assert r.json() is True


def test_poll_returns_false_when_all_jobs_consumed(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    _cleanup(db)
    db.add(
        TrainingJobRequest(
            is_pending=False,
            consumed_at=datetime.now(tz=timezone.utc),
        )
    )
    db.commit()

    r = client.get(_URL_POLL, headers=superuser_token_headers)
    assert r.status_code == 200
    assert r.json() is False


def test_poll_unauthenticated(client: TestClient) -> None:
    r = client.get(_URL_POLL)
    assert r.status_code == 401


def test_poll_not_enough_permissions(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    r = client.get(_URL_POLL, headers=normal_user_token_headers)
    assert r.status_code == 403


# ── Download endpoint ─────────────────────────────────────────────


def test_download_returns_empty_when_no_telemetry(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    _cleanup(db)
    r = client.get(
        _URL_DOWNLOAD,
        headers=superuser_token_headers,
        params={"newest_local_ts": 0},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 0
    assert body["rows"] == []
    assert body["server_newest_ts"] is None
    assert body["maturity_cutoff_ts"] is None


def test_download_respects_maturity_window(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    """Rows newer than (server_max − 7d) must be excluded."""
    _cleanup(db)

    now = datetime.now(tz=timezone.utc)

    # Old row — 10 days old → mature → should be included
    old_ts = now - timedelta(days=10)
    _seed_telemetry(db, patient_id=1, ts=old_ts)

    # Recent row — 3 days old → immature → should be excluded
    recent_ts = now - timedelta(days=3)
    _seed_telemetry(db, patient_id=2, ts=recent_ts)

    # Server max is `recent_ts`, cutoff = recent_ts − 7d = now − 10d
    # Nothing between epoch-0 and (now − 10d)? Actually old_ts = now − 10d
    # Boundary: timestamp > local_dt AND timestamp <= cutoff
    # old_ts == cutoff, so with <=, it IS included if local_ts < old_ts.

    r = client.get(
        _URL_DOWNLOAD,
        headers=superuser_token_headers,
        params={"newest_local_ts": 0},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 1
    assert len(body["rows"]) == 1
    assert body["rows"][0]["patient_id"] == 1
    assert body["server_newest_ts"] is not None
    assert body["maturity_cutoff_ts"] is not None


def test_download_filters_by_local_ts(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    """Rows with timestamp <= newest_local_ts must be excluded."""
    _cleanup(db)

    # Zero out microseconds so the int(epoch) round-trip is lossless
    now = datetime.now(tz=timezone.utc).replace(microsecond=0)

    # Three mature rows: 15, 12, and 10 days old
    ts_15d = now - timedelta(days=15)
    ts_12d = now - timedelta(days=12)
    ts_10d = now - timedelta(days=10)

    _seed_telemetry(db, patient_id=1, ts=ts_15d)
    _seed_telemetry(db, patient_id=2, ts=ts_12d)
    _seed_telemetry(db, patient_id=3, ts=ts_10d)

    # Newest row (immature anchor) to establish server_max
    _seed_telemetry(db, patient_id=4, ts=now)

    # local compute already has everything up to ts_12d
    local_epoch = int(ts_12d.timestamp())

    r = client.get(
        _URL_DOWNLOAD,
        headers=superuser_token_headers,
        params={"newest_local_ts": local_epoch},
    )
    assert r.status_code == 200
    body = r.json()
    # Only the 10-day-old row should be returned (cutoff = now − 7d = now-7d)
    # ts_10d (now-10d) <= cutoff (now-7d) → included
    # ts_15d and ts_12d are <= local_ts → excluded
    assert body["count"] == 1
    assert body["rows"][0]["patient_id"] == 3


def test_download_returns_empty_when_cutoff_before_local_ts(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    """When local compute is already caught up past the maturity window."""
    _cleanup(db)

    now = datetime.now(tz=timezone.utc)
    # Only a very recent row — maturity cutoff will be in the past
    _seed_telemetry(db, patient_id=1, ts=now)

    # local_ts far in the past but cutoff = now − 7d
    # cutoff <= local_ts? Not necessarily. Let's set local_ts to now − 5d.
    local_epoch = int((now - timedelta(days=5)).timestamp())

    r = client.get(
        _URL_DOWNLOAD,
        headers=superuser_token_headers,
        params={"newest_local_ts": local_epoch},
    )
    assert r.status_code == 200
    body = r.json()
    # cutoff = now − 7d < local_ts = now − 5d  → cutoff <= local_dt → empty
    assert body["count"] == 0
    assert body["rows"] == []


def test_download_missing_param(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    r = client.get(_URL_DOWNLOAD, headers=superuser_token_headers)
    assert r.status_code == 422


def test_download_unauthenticated(client: TestClient) -> None:
    r = client.get(_URL_DOWNLOAD, params={"newest_local_ts": 0})
    assert r.status_code == 401


def test_download_not_enough_permissions(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    r = client.get(
        _URL_DOWNLOAD,
        headers=normal_user_token_headers,
        params={"newest_local_ts": 0},
    )
    assert r.status_code == 403


# ── Request endpoint ──────────────────────────────────────────────


def test_create_training_job_request(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    _cleanup(db)
    r = client.post(_URL_REQUEST, headers=superuser_token_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["is_pending"] is True
    assert body["id"] is not None
    assert body["requested_by"] is not None


def test_create_training_job_request_unauthenticated(
    client: TestClient,
) -> None:
    r = client.post(_URL_REQUEST)
    assert r.status_code == 401


def test_create_training_job_request_not_enough_permissions(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    r = client.post(_URL_REQUEST, headers=normal_user_token_headers)
    assert r.status_code == 403


def test_download_response_contains_all_telemetry_fields(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    """Every telemetry field should be present in the download response."""
    _cleanup(db)

    now = datetime.now(tz=timezone.utc)
    old_ts = now - timedelta(days=20)

    row = PacemakerTelemetry(
        patient_id=99,
        timestamp=old_ts,
        lead_impedance_ohms=510.0,
        capture_threshold_v=1.1,
        r_wave_sensing_mv=8.7,
        battery_voltage_v=2.9,
        target_fail_next_7d=1,
        lead_impedance_ohms_rolling_mean_3d=505.0,
        lead_impedance_ohms_rolling_mean_7d=508.0,
        capture_threshold_v_rolling_mean_3d=1.05,
        capture_threshold_v_rolling_mean_7d=1.08,
        lead_impedance_ohms_delta_per_day_3d=0.5,
        lead_impedance_ohms_delta_per_day_7d=0.3,
        capture_threshold_v_delta_per_day_3d=0.02,
        capture_threshold_v_delta_per_day_7d=0.01,
    )
    db.add(row)
    db.commit()

    # Add recent anchor so server_max is now
    _seed_telemetry(db, patient_id=100, ts=now)

    r = client.get(
        _URL_DOWNLOAD,
        headers=superuser_token_headers,
        params={"newest_local_ts": 0},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 1
    data = body["rows"][0]
    assert data["patient_id"] == 99
    assert data["target_fail_next_7d"] == 1
    assert data["lead_impedance_ohms_rolling_mean_3d"] == 505.0
    assert data["capture_threshold_v_delta_per_day_7d"] == 0.01
