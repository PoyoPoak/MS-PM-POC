from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.models import PacemakerTelemetry, PatientLatestTelemetry

_URL_LATEST = f"{settings.API_V1_STR}/patients/latest"


def _cleanup(db: Session) -> None:
    db.exec(delete(PacemakerTelemetry))
    db.exec(delete(PatientLatestTelemetry))
    db.commit()


def _seed_telemetry(
    db: Session,
    *,
    patient_id: int,
    ts: datetime,
) -> None:
    db.add(
        PacemakerTelemetry(
            patient_id=patient_id,
            timestamp=ts,
            lead_impedance_ohms=500.0 + patient_id,
            capture_threshold_v=1.0,
            r_wave_sensing_mv=8.0,
            battery_voltage_v=2.8,
            lead_impedance_ohms_rolling_mean_3d=500.0,
            lead_impedance_ohms_rolling_mean_7d=499.0,
            capture_threshold_v_rolling_mean_3d=1.0,
            capture_threshold_v_rolling_mean_7d=0.99,
            lead_impedance_ohms_delta_per_day_3d=0.2,
            lead_impedance_ohms_delta_per_day_7d=0.1,
            capture_threshold_v_delta_per_day_3d=0.01,
            capture_threshold_v_delta_per_day_7d=0.005,
        )
    )
    db.commit()


def _seed_snapshot(
    db: Session,
    *,
    patient_id: int,
    risk: float | None,
    ts: datetime,
) -> None:
    db.add(
        PatientLatestTelemetry(
            patient_id=patient_id,
            timestamp=ts,
            lead_impedance_ohms=500.0 + patient_id,
            capture_threshold_v=1.0,
            r_wave_sensing_mv=8.0,
            battery_voltage_v=2.8,
            lead_impedance_ohms_rolling_mean_3d=500.0,
            lead_impedance_ohms_rolling_mean_7d=499.0,
            capture_threshold_v_rolling_mean_3d=1.0,
            capture_threshold_v_rolling_mean_7d=0.99,
            lead_impedance_ohms_delta_per_day_3d=0.2,
            lead_impedance_ohms_delta_per_day_7d=0.1,
            capture_threshold_v_delta_per_day_3d=0.01,
            capture_threshold_v_delta_per_day_7d=0.005,
            fail_probability=risk,
        )
    )
    db.commit()


def test_latest_patients_requires_auth(client: TestClient) -> None:
    response = client.get(_URL_LATEST)
    assert response.status_code == 401


def test_latest_patients_returns_data_for_authenticated_user(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    _cleanup(db)
    now = datetime.now(tz=timezone.utc)
    _seed_telemetry(db, patient_id=1, ts=now - timedelta(minutes=5))
    _seed_telemetry(db, patient_id=2, ts=now)
    _seed_snapshot(db, patient_id=1, risk=0.8, ts=now - timedelta(minutes=5))
    _seed_snapshot(db, patient_id=2, risk=0.3, ts=now)

    response = client.get(_URL_LATEST, headers=normal_user_token_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 2
    assert len(payload["data"]) == 2


def test_latest_patients_filters_by_risk_and_alerts(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    _cleanup(db)
    now = datetime.now(tz=timezone.utc)
    _seed_telemetry(db, patient_id=10, ts=now)
    _seed_telemetry(db, patient_id=11, ts=now)
    _seed_telemetry(db, patient_id=12, ts=now)
    _seed_snapshot(db, patient_id=10, risk=0.9, ts=now)
    _seed_snapshot(db, patient_id=11, risk=0.5, ts=now)
    _seed_snapshot(db, patient_id=12, risk=0.2, ts=now)

    high_risk = client.get(
        _URL_LATEST,
        headers=superuser_token_headers,
        params={"risk_filter": "high"},
    )
    alert_sent = client.get(
        _URL_LATEST,
        headers=superuser_token_headers,
        params={"alert_filter": "sent"},
    )

    assert high_risk.status_code == 200
    assert high_risk.json()["count"] == 1
    assert high_risk.json()["data"][0]["patient_id"] == 10

    assert alert_sent.status_code == 200
    assert alert_sent.json()["count"] == 1
    assert alert_sent.json()["data"][0]["patient_id"] == 10


def test_latest_patients_supports_search_sort_and_pagination(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    _cleanup(db)
    now = datetime.now(tz=timezone.utc)
    _seed_telemetry(db, patient_id=101, ts=now)
    _seed_telemetry(db, patient_id=202, ts=now)
    _seed_snapshot(db, patient_id=101, risk=0.1, ts=now)
    _seed_snapshot(db, patient_id=202, risk=0.8, ts=now)

    response = client.get(
        _URL_LATEST,
        headers=superuser_token_headers,
        params={
            "patient_search": "02",
            "sort_by": "patient_id",
            "sort_order": "asc",
            "skip": 0,
            "limit": 10,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["data"][0]["patient_id"] == 202


def test_latest_patients_uses_telemetry_when_snapshots_missing(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    _cleanup(db)
    now = datetime.now(tz=timezone.utc)
    _seed_telemetry(db, patient_id=301, ts=now - timedelta(minutes=1))
    _seed_telemetry(db, patient_id=302, ts=now)

    response = client.get(_URL_LATEST, headers=normal_user_token_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 2
    assert payload["data"][0]["fail_probability"] is None
