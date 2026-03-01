from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Body, Depends
from sqlalchemy import tuple_
from sqlmodel import select

from app.api.deps import SessionDep, get_current_active_superuser
from app.models import (
    PacemakerTelemetry,
    PacemakerTelemetryIngest,
    PacemakerTelemetryIngestResult,
    User,
)

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post("/ingest", response_model=PacemakerTelemetryIngestResult)
def ingest_telemetry_bulk(
    *,
    session: SessionDep,
    current_superuser: User = Depends(get_current_active_superuser),
    telemetry_rows: list[PacemakerTelemetryIngest] = Body(
        ..., min_length=1, max_length=2000
    ),
) -> Any:
    """
    Ingest telemetry rows in bulk.

    Daily simulation batches can vary in size and are accepted as long as
    they contain between 1 and 2000 rows.
    """
    _ = current_superuser.id

    unique_rows: dict[tuple[int, datetime], PacemakerTelemetryIngest] = {}
    duplicate_in_payload_count = 0

    for row in telemetry_rows:
        timestamp = datetime.fromtimestamp(row.timestamp, tz=timezone.utc)
        key = (row.patient_id, timestamp)
        if key in unique_rows:
            duplicate_in_payload_count += 1
            continue
        unique_rows[key] = row

    existing_pairs: set[tuple[int, datetime]] = set()
    if unique_rows:
        key_pairs = list(unique_rows.keys())
        existing_statement = select(
            PacemakerTelemetry.patient_id,
            PacemakerTelemetry.timestamp,
        ).where(
            tuple_(
                PacemakerTelemetry.patient_id,
                PacemakerTelemetry.timestamp,
            ).in_(key_pairs)
        )
        existing_pairs = set(session.exec(existing_statement).all())

    records_to_insert: list[PacemakerTelemetry] = []
    for key, row in unique_rows.items():
        if key in existing_pairs:
            continue
        records_to_insert.append(
            PacemakerTelemetry(
                patient_id=row.patient_id,
                timestamp=key[1],
                lead_impedance_ohms=row.lead_impedance_ohms,
                capture_threshold_v=row.capture_threshold_v,
                r_wave_sensing_mv=row.r_wave_sensing_mv,
                battery_voltage_v=row.battery_voltage_v,
                target_fail_next_7d=row.target_fail_next_7d,
                lead_impedance_ohms_rolling_mean_3d=row.lead_impedance_ohms_rolling_mean_3d,
                lead_impedance_ohms_rolling_mean_7d=row.lead_impedance_ohms_rolling_mean_7d,
                capture_threshold_v_rolling_mean_3d=row.capture_threshold_v_rolling_mean_3d,
                capture_threshold_v_rolling_mean_7d=row.capture_threshold_v_rolling_mean_7d,
                lead_impedance_ohms_delta_per_day_3d=row.lead_impedance_ohms_delta_per_day_3d,
                lead_impedance_ohms_delta_per_day_7d=row.lead_impedance_ohms_delta_per_day_7d,
                capture_threshold_v_delta_per_day_3d=row.capture_threshold_v_delta_per_day_3d,
                capture_threshold_v_delta_per_day_7d=row.capture_threshold_v_delta_per_day_7d,
            )
        )

    if records_to_insert:
        session.add_all(records_to_insert)
        session.commit()

    duplicate_existing_count = len(existing_pairs)
    duplicate_count = duplicate_in_payload_count + duplicate_existing_count
    return PacemakerTelemetryIngestResult(
        received_count=len(telemetry_rows),
        inserted_count=len(records_to_insert),
        duplicate_count=duplicate_count,
        duplicate_in_payload_count=duplicate_in_payload_count,
        duplicate_existing_count=duplicate_existing_count,
    )
