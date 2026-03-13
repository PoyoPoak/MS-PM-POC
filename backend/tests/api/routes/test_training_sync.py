"""Tests for training-sync endpoints.

* ``GET  /training/poll``
* ``GET  /training/download``
* ``POST /training/request``
* ``POST /training/claim``
* ``POST /training/{job_id}/complete``
"""

import uuid
from datetime import datetime, timedelta, timezone
from io import BytesIO

import joblib
import pandas as pd
from fastapi.testclient import TestClient
from sklearn.ensemble import RandomForestClassifier
from sqlmodel import Session, delete, select

from app.core.config import settings
from app.models import (
    ModelArtifact,
    PacemakerTelemetry,
    PatientLatestTelemetry,
    TrainingJobRequest,
)

_URL_POLL = f"{settings.API_V1_STR}/training/poll"
_URL_DOWNLOAD = f"{settings.API_V1_STR}/training/download"
_URL_REQUEST = f"{settings.API_V1_STR}/training/request"
_URL_CLAIM = f"{settings.API_V1_STR}/training/claim"
_URL_PREDICT = f"{settings.API_V1_STR}/training/predict"


def _url_complete(job_id: uuid.UUID | str) -> str:
    return f"{settings.API_V1_STR}/training/{job_id}/complete"


def _cleanup(db: Session) -> None:
    """Remove all training job requests and telemetry rows."""
    db.exec(delete(TrainingJobRequest))  # type: ignore[call-overload]
    db.exec(delete(ModelArtifact))  # type: ignore[call-overload]
    db.exec(delete(PatientLatestTelemetry))  # type: ignore[call-overload]
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


def _seed_model_artifact(db: Session) -> ModelArtifact:
    """Insert a tiny trained RF model artifact for inference tests."""
    X_train = pd.DataFrame(
        [
            {
                "lead_impedance_ohms": 490.0,
                "capture_threshold_v": 0.9,
                "r_wave_sensing_mv": 9.2,
                "battery_voltage_v": 3.0,
                "lead_impedance_ohms_rolling_mean_3d": 488.0,
                "lead_impedance_ohms_rolling_mean_7d": 486.0,
                "capture_threshold_v_rolling_mean_3d": 0.88,
                "capture_threshold_v_rolling_mean_7d": 0.87,
                "lead_impedance_ohms_delta_per_day_3d": 0.2,
                "lead_impedance_ohms_delta_per_day_7d": 0.1,
                "capture_threshold_v_delta_per_day_3d": 0.01,
                "capture_threshold_v_delta_per_day_7d": 0.005,
            },
            {
                "lead_impedance_ohms": 610.0,
                "capture_threshold_v": 1.6,
                "r_wave_sensing_mv": 6.0,
                "battery_voltage_v": 2.5,
                "lead_impedance_ohms_rolling_mean_3d": 608.0,
                "lead_impedance_ohms_rolling_mean_7d": 605.0,
                "capture_threshold_v_rolling_mean_3d": 1.58,
                "capture_threshold_v_rolling_mean_7d": 1.55,
                "lead_impedance_ohms_delta_per_day_3d": 0.9,
                "lead_impedance_ohms_delta_per_day_7d": 0.7,
                "capture_threshold_v_delta_per_day_3d": 0.04,
                "capture_threshold_v_delta_per_day_7d": 0.03,
            },
        ]
    )
    y_train = [0, 1]
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)

    buffer = BytesIO()
    joblib.dump(model, buffer)

    artifact = ModelArtifact(
        algorithm="RandomForestClassifier",
        hyperparameters={"n_estimators": 10, "random_state": 42},
        metrics={"test_accuracy": 1.0},
        dataset_info={"train_rows": 2, "test_rows": 0, "n_features": 12},
        is_active=True,
        content_type="application/octet-stream",
        model_size_bytes=len(buffer.getvalue()),
        model_sha256="a" * 64,
        model_blob=buffer.getvalue(),
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact


def _seed_single_class_model_artifact(db: Session, *, klass: int) -> ModelArtifact:
    """Insert a trained RF model artifact with a single class in training labels."""
    X_train = pd.DataFrame(
        [
            {
                "lead_impedance_ohms": 490.0,
                "capture_threshold_v": 0.9,
                "r_wave_sensing_mv": 9.2,
                "battery_voltage_v": 3.0,
                "lead_impedance_ohms_rolling_mean_3d": 488.0,
                "lead_impedance_ohms_rolling_mean_7d": 486.0,
                "capture_threshold_v_rolling_mean_3d": 0.88,
                "capture_threshold_v_rolling_mean_7d": 0.87,
                "lead_impedance_ohms_delta_per_day_3d": 0.2,
                "lead_impedance_ohms_delta_per_day_7d": 0.1,
                "capture_threshold_v_delta_per_day_3d": 0.01,
                "capture_threshold_v_delta_per_day_7d": 0.005,
            },
            {
                "lead_impedance_ohms": 500.0,
                "capture_threshold_v": 1.0,
                "r_wave_sensing_mv": 8.5,
                "battery_voltage_v": 2.9,
                "lead_impedance_ohms_rolling_mean_3d": 499.0,
                "lead_impedance_ohms_rolling_mean_7d": 498.0,
                "capture_threshold_v_rolling_mean_3d": 0.98,
                "capture_threshold_v_rolling_mean_7d": 0.97,
                "lead_impedance_ohms_delta_per_day_3d": 0.25,
                "lead_impedance_ohms_delta_per_day_7d": 0.15,
                "capture_threshold_v_delta_per_day_3d": 0.02,
                "capture_threshold_v_delta_per_day_7d": 0.01,
            },
        ]
    )
    y_train = [klass, klass]
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)

    buffer = BytesIO()
    joblib.dump(model, buffer)

    artifact = ModelArtifact(
        algorithm="RandomForestClassifier",
        hyperparameters={"n_estimators": 10, "random_state": 42},
        metrics={"test_accuracy": 1.0},
        dataset_info={"train_rows": 2, "test_rows": 0, "n_features": 12},
        is_active=True,
        content_type="application/octet-stream",
        model_size_bytes=len(buffer.getvalue()),
        model_sha256="c" * 64,
        model_blob=buffer.getvalue(),
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact


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


def test_predict_latest_snapshot_scores_rows(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    _cleanup(db)

    now = datetime.now(tz=timezone.utc)
    db.add_all(
        [
            PacemakerTelemetry(
                patient_id=1,
                timestamp=now - timedelta(hours=2),
                lead_impedance_ohms=500.0,
                capture_threshold_v=1.0,
                r_wave_sensing_mv=8.9,
                battery_voltage_v=2.9,
                lead_impedance_ohms_rolling_mean_3d=499.0,
                lead_impedance_ohms_rolling_mean_7d=498.0,
                capture_threshold_v_rolling_mean_3d=0.99,
                capture_threshold_v_rolling_mean_7d=0.98,
                lead_impedance_ohms_delta_per_day_3d=0.25,
                lead_impedance_ohms_delta_per_day_7d=0.2,
                capture_threshold_v_delta_per_day_3d=0.01,
                capture_threshold_v_delta_per_day_7d=0.01,
            ),
            PacemakerTelemetry(
                patient_id=1,
                timestamp=now - timedelta(hours=1),
                lead_impedance_ohms=503.0,
                capture_threshold_v=1.1,
                r_wave_sensing_mv=8.7,
                battery_voltage_v=2.85,
                lead_impedance_ohms_rolling_mean_3d=501.0,
                lead_impedance_ohms_rolling_mean_7d=500.0,
                capture_threshold_v_rolling_mean_3d=1.05,
                capture_threshold_v_rolling_mean_7d=1.03,
                lead_impedance_ohms_delta_per_day_3d=0.31,
                lead_impedance_ohms_delta_per_day_7d=0.25,
                capture_threshold_v_delta_per_day_3d=0.02,
                capture_threshold_v_delta_per_day_7d=0.015,
            ),
            PacemakerTelemetry(
                patient_id=2,
                timestamp=now - timedelta(hours=1),
                lead_impedance_ohms=607.0,
                capture_threshold_v=1.6,
                r_wave_sensing_mv=6.1,
                battery_voltage_v=2.55,
                lead_impedance_ohms_rolling_mean_3d=605.0,
                lead_impedance_ohms_rolling_mean_7d=603.0,
                capture_threshold_v_rolling_mean_3d=1.58,
                capture_threshold_v_rolling_mean_7d=1.56,
                lead_impedance_ohms_delta_per_day_3d=0.88,
                lead_impedance_ohms_delta_per_day_7d=0.7,
                capture_threshold_v_delta_per_day_3d=0.04,
                capture_threshold_v_delta_per_day_7d=0.03,
            ),
        ]
    )
    db.commit()

    artifact = _seed_model_artifact(db)

    r = client.post(_URL_PREDICT, headers=superuser_token_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["rows_upserted"] == 2
    assert body["rows_scored"] == 2
    assert body["model_id"] == str(artifact.id)
    assert body["queued_job_id"] is None

    rows = db.exec(
        select(PatientLatestTelemetry).order_by(PatientLatestTelemetry.patient_id)
    ).all()
    assert len(rows) == 2
    assert rows[0].timestamp == now - timedelta(hours=1)
    assert rows[0].fail_probability is not None
    assert rows[1].fail_probability is not None


def test_predict_handles_single_class_model_probabilities(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    _cleanup(db)

    now = datetime.now(tz=timezone.utc)
    db.add(
        PacemakerTelemetry(
            patient_id=55,
            timestamp=now,
            lead_impedance_ohms=501.0,
            capture_threshold_v=1.1,
            r_wave_sensing_mv=8.1,
            battery_voltage_v=2.88,
            lead_impedance_ohms_rolling_mean_3d=500.0,
            lead_impedance_ohms_rolling_mean_7d=499.0,
            capture_threshold_v_rolling_mean_3d=1.05,
            capture_threshold_v_rolling_mean_7d=1.03,
            lead_impedance_ohms_delta_per_day_3d=0.3,
            lead_impedance_ohms_delta_per_day_7d=0.2,
            capture_threshold_v_delta_per_day_3d=0.02,
            capture_threshold_v_delta_per_day_7d=0.01,
        )
    )
    db.commit()

    _seed_single_class_model_artifact(db, klass=0)

    response = client.post(_URL_PREDICT, headers=superuser_token_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["rows_scored"] == 1

    snapshot = db.get(PatientLatestTelemetry, 55)
    assert snapshot is not None
    assert snapshot.fail_probability == 0.0


def test_predict_returns_404_when_active_model_missing_but_still_upserts(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    _cleanup(db)

    now = datetime.now(tz=timezone.utc)
    db.add(
        PacemakerTelemetry(
            patient_id=7,
            timestamp=now,
            lead_impedance_ohms=501.0,
            capture_threshold_v=1.1,
            r_wave_sensing_mv=8.1,
            battery_voltage_v=2.88,
            lead_impedance_ohms_rolling_mean_3d=500.0,
            lead_impedance_ohms_rolling_mean_7d=499.0,
            capture_threshold_v_rolling_mean_3d=1.05,
            capture_threshold_v_rolling_mean_7d=1.03,
            lead_impedance_ohms_delta_per_day_3d=0.3,
            lead_impedance_ohms_delta_per_day_7d=0.2,
            capture_threshold_v_delta_per_day_3d=0.02,
            capture_threshold_v_delta_per_day_7d=0.01,
        )
    )
    db.commit()

    r = client.post(_URL_PREDICT, headers=superuser_token_headers)
    assert r.status_code == 404
    detail = r.json()["detail"]
    assert detail["message"] == "No active model artifact available for inference."
    assert detail["rows_upserted"] == 1
    assert detail["rows_scored"] == 0
    assert detail["model_id"] is None

    snapshot = db.get(PatientLatestTelemetry, 7)
    assert snapshot is not None
    assert snapshot.fail_probability is None


def test_predict_unauthenticated(client: TestClient) -> None:
    r = client.post(_URL_PREDICT)
    assert r.status_code == 401


def test_predict_not_enough_permissions(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    r = client.post(_URL_PREDICT, headers=normal_user_token_headers)
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


# ── Claim endpoint ────────────────────────────────────────────────


def test_claim_returns_newest_pending_job(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    """Claim should return the newest pending job, not the oldest."""
    _cleanup(db)

    now = datetime.now(tz=timezone.utc)
    old_job = TrainingJobRequest(is_pending=True, created_at=now - timedelta(hours=2))
    new_job = TrainingJobRequest(is_pending=True, created_at=now)
    db.add(old_job)
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    r = client.post(_URL_CLAIM, headers=superuser_token_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == str(new_job.id)
    assert body["is_pending"] is False


def test_claim_cancels_older_pending_jobs(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    """Older pending jobs must be cancelled when the newest is claimed."""
    _cleanup(db)

    now = datetime.now(tz=timezone.utc)
    old_job = TrainingJobRequest(is_pending=True, created_at=now - timedelta(hours=2))
    mid_job = TrainingJobRequest(is_pending=True, created_at=now - timedelta(hours=1))
    new_job = TrainingJobRequest(is_pending=True, created_at=now)
    db.add_all([old_job, mid_job, new_job])
    db.commit()
    db.refresh(old_job)
    db.refresh(mid_job)

    r = client.post(_URL_CLAIM, headers=superuser_token_headers)
    assert r.status_code == 200

    # Refresh stale ORM instances
    db.refresh(old_job)
    db.refresh(mid_job)

    # Both older jobs should be cancelled
    assert old_job.is_pending is False
    assert old_job.cancelled_at is not None
    assert mid_job.is_pending is False
    assert mid_job.cancelled_at is not None


def test_claim_returns_404_when_no_pending(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    _cleanup(db)
    r = client.post(_URL_CLAIM, headers=superuser_token_headers)
    assert r.status_code == 404
    assert "No pending" in r.json()["detail"]


def test_claim_returns_409_when_job_already_in_progress(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    """If a job is claimed but not yet completed, a new claim must fail."""
    _cleanup(db)

    # Create a job that is already in-progress (claimed, not completed)
    in_progress = TrainingJobRequest(
        is_pending=False, consumed_at=None, cancelled_at=None
    )
    # And a new pending one
    pending = TrainingJobRequest(is_pending=True)
    db.add_all([in_progress, pending])
    db.commit()

    r = client.post(_URL_CLAIM, headers=superuser_token_headers)
    assert r.status_code == 409
    assert "already in progress" in r.json()["detail"]


def test_claim_succeeds_when_previous_completed(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    """A completed job should not block a new claim."""
    _cleanup(db)

    now = datetime.now(tz=timezone.utc)
    completed = TrainingJobRequest(
        is_pending=False, consumed_at=now - timedelta(hours=1)
    )
    pending = TrainingJobRequest(is_pending=True, created_at=now)
    db.add_all([completed, pending])
    db.commit()

    r = client.post(_URL_CLAIM, headers=superuser_token_headers)
    assert r.status_code == 200


def test_claim_succeeds_when_previous_cancelled(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    """A cancelled job should not block a new claim."""
    _cleanup(db)

    now = datetime.now(tz=timezone.utc)
    cancelled = TrainingJobRequest(
        is_pending=False, cancelled_at=now - timedelta(hours=1)
    )
    pending = TrainingJobRequest(is_pending=True, created_at=now)
    db.add_all([cancelled, pending])
    db.commit()

    r = client.post(_URL_CLAIM, headers=superuser_token_headers)
    assert r.status_code == 200


def test_claim_response_includes_cancelled_at_field(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    _cleanup(db)
    db.add(TrainingJobRequest(is_pending=True))
    db.commit()

    r = client.post(_URL_CLAIM, headers=superuser_token_headers)
    assert r.status_code == 200
    body = r.json()
    assert "cancelled_at" in body
    assert body["cancelled_at"] is None


def test_claim_unauthenticated(client: TestClient) -> None:
    r = client.post(_URL_CLAIM)
    assert r.status_code == 401


def test_claim_not_enough_permissions(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    r = client.post(_URL_CLAIM, headers=normal_user_token_headers)
    assert r.status_code == 403


# ── Complete endpoint ─────────────────────────────────────────────


def test_complete_marks_claimed_job_done(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    _cleanup(db)

    job = TrainingJobRequest(is_pending=False, consumed_at=None, cancelled_at=None)
    db.add(job)
    db.commit()
    db.refresh(job)

    r = client.post(_url_complete(job.id), headers=superuser_token_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["consumed_at"] is not None
    assert body["is_pending"] is False


def test_complete_returns_404_for_nonexistent_job(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    _cleanup(db)
    fake_id = uuid.uuid4()
    r = client.post(_url_complete(fake_id), headers=superuser_token_headers)
    assert r.status_code == 404


def test_complete_returns_409_for_pending_job(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    _cleanup(db)

    job = TrainingJobRequest(is_pending=True)
    db.add(job)
    db.commit()
    db.refresh(job)

    r = client.post(_url_complete(job.id), headers=superuser_token_headers)
    assert r.status_code == 409
    assert "not been claimed" in r.json()["detail"]


def test_complete_returns_409_for_already_completed_job(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    _cleanup(db)

    now = datetime.now(tz=timezone.utc)
    job = TrainingJobRequest(is_pending=False, consumed_at=now)
    db.add(job)
    db.commit()
    db.refresh(job)

    r = client.post(_url_complete(job.id), headers=superuser_token_headers)
    assert r.status_code == 409
    assert "already been completed" in r.json()["detail"]


def test_complete_returns_409_for_cancelled_job(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    _cleanup(db)

    now = datetime.now(tz=timezone.utc)
    job = TrainingJobRequest(is_pending=False, cancelled_at=now)
    db.add(job)
    db.commit()
    db.refresh(job)

    r = client.post(_url_complete(job.id), headers=superuser_token_headers)
    assert r.status_code == 409
    assert "cancelled" in r.json()["detail"]


def test_complete_unauthenticated(client: TestClient) -> None:
    fake_id = uuid.uuid4()
    r = client.post(_url_complete(fake_id))
    assert r.status_code == 401


def test_complete_not_enough_permissions(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    fake_id = uuid.uuid4()
    r = client.post(_url_complete(fake_id), headers=normal_user_token_headers)
    assert r.status_code == 403
