from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.models import ModelArtifact, PacemakerTelemetry, PatientLatestTelemetry

_URL_SUMMARY = f"{settings.API_V1_STR}/dashboard/summary"


def _cleanup(db: Session) -> None:
    db.exec(delete(ModelArtifact))
    db.exec(delete(PacemakerTelemetry))
    db.exec(delete(PatientLatestTelemetry))
    db.commit()


def _seed_patient(
    db: Session,
    *,
    patient_id: int,
    probability: float | None,
) -> None:
    db.add(
        PatientLatestTelemetry(
            patient_id=patient_id,
            timestamp=datetime.now(tz=timezone.utc),
            lead_impedance_ohms=500.0,
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
            fail_probability=probability,
        )
    )
    db.commit()


def _seed_telemetry(db: Session, *, patient_id: int) -> None:
    db.add(
        PacemakerTelemetry(
            patient_id=patient_id,
            timestamp=datetime.now(tz=timezone.utc),
            lead_impedance_ohms=500.0,
            capture_threshold_v=1.0,
            r_wave_sensing_mv=8.0,
            battery_voltage_v=2.8,
        )
    )
    db.commit()


def test_dashboard_summary_requires_auth(client: TestClient) -> None:
    response = client.get(_URL_SUMMARY)
    assert response.status_code == 401


def test_dashboard_summary_returns_empty_state(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    _cleanup(db)

    response = client.get(_URL_SUMMARY, headers=normal_user_token_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_patients"] == 0
    assert payload["high_risk_patients"] == 0
    assert payload["alerts_sent"] == 0
    assert payload["last_update"] is None
    assert payload["active_model"] is None


def test_dashboard_summary_counts_risk_buckets_and_active_model(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    _cleanup(db)

    _seed_telemetry(db, patient_id=1)
    _seed_telemetry(db, patient_id=2)
    _seed_telemetry(db, patient_id=3)
    _seed_patient(db, patient_id=1, probability=0.85)
    _seed_patient(db, patient_id=2, probability=0.72)
    _seed_patient(db, patient_id=3, probability=0.33)

    active_model = ModelArtifact(
        algorithm="RandomForestClassifier",
        hyperparameters={"n_estimators": 50},
        metrics={"f1": 0.82},
        dataset_info={"train_rows": 1000},
        is_active=True,
        content_type="application/octet-stream",
        model_size_bytes=12,
        model_sha256="b" * 64,
        model_blob=b"model-bytes",
    )
    db.add(active_model)
    db.commit()

    response = client.get(_URL_SUMMARY, headers=superuser_token_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_patients"] == 3
    assert payload["high_risk_patients"] == 2
    assert payload["alerts_sent"] == 1
    assert payload["last_update"] is not None
    assert payload["active_model"] is not None
    assert payload["active_model"]["id"] == str(active_model.id)
    assert payload["active_model"]["is_active"] is True
