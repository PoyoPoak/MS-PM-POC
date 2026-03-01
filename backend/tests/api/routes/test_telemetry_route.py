from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session, delete, func, select

from app.core.config import settings
from app.models import PacemakerTelemetry


def _base_payload(*, patient_id: int, timestamp: int) -> dict[str, object]:
    return {
        "patient_id": patient_id,
        "timestamp": timestamp,
        "lead_impedance_ohms": 510.0,
        "capture_threshold_v": 1.1,
        "r_wave_sensing_mv": 8.7,
        "battery_voltage_v": 2.9,
    }


def _count_rows(db: Session) -> int:
    statement = select(func.count()).select_from(PacemakerTelemetry)
    return int(db.exec(statement).one())


def test_bulk_ingest_telemetry(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    db.exec(delete(PacemakerTelemetry))
    db.commit()

    existing = PacemakerTelemetry(
        patient_id=1,
        timestamp=datetime.fromtimestamp(1_700_000_000, tz=timezone.utc),
        lead_impedance_ohms=500.0,
        capture_threshold_v=1.0,
        r_wave_sensing_mv=8.0,
        battery_voltage_v=2.8,
        target_fail_next_7d=0,
    )
    db.add(existing)
    db.commit()

    payload = [
        _base_payload(patient_id=1, timestamp=1_700_000_000),
        _base_payload(patient_id=2, timestamp=1_700_000_600),
        _base_payload(patient_id=2, timestamp=1_700_000_600),
    ]

    response = client.post(
        f"{settings.API_V1_STR}/telemetry/ingest",
        headers=superuser_token_headers,
        json=payload,
    )

    assert response.status_code == 200
    content = response.json()
    assert content["received_count"] == 3
    assert content["inserted_count"] == 1
    assert content["duplicate_count"] == 2
    assert content["duplicate_in_payload_count"] == 1
    assert content["duplicate_existing_count"] == 1
    assert _count_rows(db) == 2


def test_bulk_ingest_telemetry_not_enough_permissions(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    payload = [_base_payload(patient_id=11, timestamp=1_700_010_000)]
    response = client.post(
        f"{settings.API_V1_STR}/telemetry/ingest",
        headers=normal_user_token_headers,
        json=payload,
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "The user doesn't have enough privileges"}


def test_bulk_ingest_telemetry_invalid_timestamp(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    payload = [_base_payload(patient_id=21, timestamp=1_700_010_000)]
    payload[0]["timestamp"] = "2024-01-01T00:00:00Z"

    response = client.post(
        f"{settings.API_V1_STR}/telemetry/ingest",
        headers=superuser_token_headers,
        json=payload,
    )
    assert response.status_code == 422


def test_bulk_ingest_telemetry_requires_list(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/telemetry/ingest",
        headers=superuser_token_headers,
        json=_base_payload(patient_id=31, timestamp=1_700_010_000),
    )
    assert response.status_code == 422


def test_bulk_ingest_telemetry_unauthenticated(client: TestClient) -> None:
    payload = [_base_payload(patient_id=41, timestamp=1_700_020_000)]
    response = client.post(
        f"{settings.API_V1_STR}/telemetry/ingest",
        json=payload,
    )
    assert response.status_code == 401


def test_bulk_ingest_telemetry_rejects_empty_batch(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/telemetry/ingest",
        headers=superuser_token_headers,
        json=[],
    )
    assert response.status_code == 422


def test_bulk_ingest_telemetry_rejects_oversized_batch(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    payload = [
        _base_payload(patient_id=1000 + index, timestamp=1_700_030_000 + index)
        for index in range(2001)
    ]
    response = client.post(
        f"{settings.API_V1_STR}/telemetry/ingest",
        headers=superuser_token_headers,
        json=payload,
    )
    assert response.status_code == 422


def test_bulk_ingest_telemetry_invalid_target_fail_value(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    payload = [_base_payload(patient_id=51, timestamp=1_700_040_000)]
    payload[0]["target_fail_next_7d"] = 2

    response = client.post(
        f"{settings.API_V1_STR}/telemetry/ingest",
        headers=superuser_token_headers,
        json=payload,
    )
    assert response.status_code == 422
