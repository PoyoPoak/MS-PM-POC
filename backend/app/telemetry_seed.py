import csv
import io
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.exc import ProgrammingError
from sqlmodel import Session, func, select

from app.models import PacemakerTelemetry

logger = logging.getLogger(__name__)

SEED_PACEMAKER_DATA_ENV = "SEED_PACEMAKER_DATA"

DEFAULT_PACEMAKER_DATA_CSV = (
    Path(__file__).resolve().parents[1] / "util" / "data" / "pacemaker_data_seed.csv"
)

_CSV_COLUMN_MAP: dict[str, str] = {
    "Patient_ID": "patient_id",
    "Timestamp": "timestamp",
    "Lead_Impedance_Ohms": "lead_impedance_ohms",
    "Capture_Threshold_V": "capture_threshold_v",
    "R_Wave_Sensing_mV": "r_wave_sensing_mv",
    "Battery_Voltage_V": "battery_voltage_v",
    "Target_Fail_Next_7d": "target_fail_next_7d",
    "Lead_Impedance_Ohms_RollingMean_3d": "lead_impedance_ohms_rolling_mean_3d",
    "Lead_Impedance_Ohms_RollingMean_7d": "lead_impedance_ohms_rolling_mean_7d",
    "Capture_Threshold_V_RollingMean_3d": "capture_threshold_v_rolling_mean_3d",
    "Capture_Threshold_V_RollingMean_7d": "capture_threshold_v_rolling_mean_7d",
    "Lead_Impedance_Ohms_DeltaPerDay_3d": "lead_impedance_ohms_delta_per_day_3d",
    "Lead_Impedance_Ohms_DeltaPerDay_7d": "lead_impedance_ohms_delta_per_day_7d",
    "Capture_Threshold_V_DeltaPerDay_3d": "capture_threshold_v_delta_per_day_3d",
    "Capture_Threshold_V_DeltaPerDay_7d": "capture_threshold_v_delta_per_day_7d",
}

_COPY_COLUMNS: tuple[str, ...] = (
    "patient_id",
    "timestamp",
    "lead_impedance_ohms",
    "capture_threshold_v",
    "r_wave_sensing_mv",
    "battery_voltage_v",
    "target_fail_next_7d",
    "lead_impedance_ohms_rolling_mean_3d",
    "lead_impedance_ohms_rolling_mean_7d",
    "capture_threshold_v_rolling_mean_3d",
    "capture_threshold_v_rolling_mean_7d",
    "lead_impedance_ohms_delta_per_day_3d",
    "lead_impedance_ohms_delta_per_day_7d",
    "capture_threshold_v_delta_per_day_3d",
    "capture_threshold_v_delta_per_day_7d",
    "id",
    "created_at",
)


def _normalize_row(row: dict[str, str]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for key, value in row.items():
        normalized_key = key.strip()
        normalized_value = value.strip() if isinstance(value, str) else ""
        normalized[normalized_key] = normalized_value
    return normalized


def _candidate_keys(field_name: str) -> tuple[str, ...]:
    mapped = [
        csv_key
        for csv_key, model_key in _CSV_COLUMN_MAP.items()
        if model_key == field_name
    ]
    return (field_name, *mapped)


def _read_field(row: dict[str, str], field_name: str) -> str | None:
    for key in _candidate_keys(field_name):
        value = row.get(key)
        if value is not None and value != "":
            return value
    return None


def _parse_timestamp(value: str) -> datetime:
    try:
        timestamp_value = float(value)
        return datetime.fromtimestamp(timestamp_value, tz=timezone.utc)
    except ValueError:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)


def _parse_optional_float(value: str | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _parse_optional_int(value: str | None) -> int | None:
    if value is None:
        return None
    return int(float(value))


def _build_payload(row: dict[str, str]) -> dict[str, object]:
    patient_id_raw = _read_field(row, "patient_id")
    timestamp_raw = _read_field(row, "timestamp")
    lead_impedance_raw = _read_field(row, "lead_impedance_ohms")
    capture_threshold_raw = _read_field(row, "capture_threshold_v")
    r_wave_sensing_raw = _read_field(row, "r_wave_sensing_mv")
    battery_voltage_raw = _read_field(row, "battery_voltage_v")

    required = [
        patient_id_raw,
        timestamp_raw,
        lead_impedance_raw,
        capture_threshold_raw,
        r_wave_sensing_raw,
        battery_voltage_raw,
    ]
    if any(value is None for value in required):
        raise ValueError("Missing required telemetry fields in row")

    target_value = _parse_optional_int(_read_field(row, "target_fail_next_7d"))
    if target_value is not None and target_value not in (0, 1):
        raise ValueError("target_fail_next_7d must be 0 or 1 when present")

    return {
        "patient_id": int(float(patient_id_raw)),
        "timestamp": _parse_timestamp(timestamp_raw),
        "lead_impedance_ohms": float(lead_impedance_raw),
        "capture_threshold_v": float(capture_threshold_raw),
        "r_wave_sensing_mv": float(r_wave_sensing_raw),
        "battery_voltage_v": float(battery_voltage_raw),
        "target_fail_next_7d": target_value,
        "lead_impedance_ohms_rolling_mean_3d": _parse_optional_float(
            _read_field(row, "lead_impedance_ohms_rolling_mean_3d")
        ),
        "lead_impedance_ohms_rolling_mean_7d": _parse_optional_float(
            _read_field(row, "lead_impedance_ohms_rolling_mean_7d")
        ),
        "capture_threshold_v_rolling_mean_3d": _parse_optional_float(
            _read_field(row, "capture_threshold_v_rolling_mean_3d")
        ),
        "capture_threshold_v_rolling_mean_7d": _parse_optional_float(
            _read_field(row, "capture_threshold_v_rolling_mean_7d")
        ),
        "lead_impedance_ohms_delta_per_day_3d": _parse_optional_float(
            _read_field(row, "lead_impedance_ohms_delta_per_day_3d")
        ),
        "lead_impedance_ohms_delta_per_day_7d": _parse_optional_float(
            _read_field(row, "lead_impedance_ohms_delta_per_day_7d")
        ),
        "capture_threshold_v_delta_per_day_3d": _parse_optional_float(
            _read_field(row, "capture_threshold_v_delta_per_day_3d")
        ),
        "capture_threshold_v_delta_per_day_7d": _parse_optional_float(
            _read_field(row, "capture_threshold_v_delta_per_day_7d")
        ),
        "id": uuid.uuid4(),
        "created_at": datetime.now(timezone.utc),
    }


def _serialize_copy_value(value: object | None) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _copy_batch(session: Session, rows: list[dict[str, object]]) -> None:
    if not rows:
        return

    copy_sql = (
        "COPY pacemaker_telemetry "
        f"({', '.join(_COPY_COLUMNS)}) "
        "FROM STDIN WITH (FORMAT csv, HEADER false, NULL '')"
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    for row in rows:
        writer.writerow(
            [_serialize_copy_value(row.get(column)) for column in _COPY_COLUMNS]
        )
    buffer.seek(0)

    dbapi_connection = session.connection().connection
    with dbapi_connection.cursor() as cursor:
        with cursor.copy(copy_sql) as copy:
            copy.write(buffer.getvalue())


def _is_seed_enabled() -> bool:
    value = os.getenv(SEED_PACEMAKER_DATA_ENV, "false").strip().lower()
    return value in {"1", "true", "yes", "on"}


def seed_pacemaker_telemetry_if_empty(
    session: Session,
    *,
    csv_path: Path | None = None,
    batch_size: int = 5_000,
) -> None:
    if not _is_seed_enabled():
        logger.info(
            "Skipping pacemaker telemetry seed because %s is not enabled.",
            SEED_PACEMAKER_DATA_ENV,
        )
        return

    count_query = select(func.count()).select_from(PacemakerTelemetry)
    try:
        _ = int(session.exec(count_query).one())
    except ProgrammingError:
        logger.info(
            "Skipping pacemaker telemetry seed because telemetry table is not available yet."
        )
        session.rollback()
        return

    source_path = csv_path or DEFAULT_PACEMAKER_DATA_CSV
    if not source_path.exists():
        logger.info(
            "Skipping pacemaker telemetry seed because CSV file was not found at %s.",
            source_path,
        )
        return

    logger.info("Seeding pacemaker telemetry data from %s", source_path)

    inserted_rows = 0
    skipped_rows = 0
    batch: list[dict[str, object]] = []

    with source_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row_number, row in enumerate(reader, start=2):
            normalized = _normalize_row(row)
            try:
                payload = _build_payload(normalized)
                batch.append(payload)
            except ValueError as error:
                skipped_rows += 1
                logger.warning(
                    "Skipping pacemaker telemetry row %d due to parse/validation error: %s",
                    row_number,
                    error,
                )
                continue

            if len(batch) >= batch_size:
                _copy_batch(session, batch)
                session.commit()
                inserted_rows += len(batch)
                batch = []

    if batch:
        _copy_batch(session, batch)
        session.commit()
        inserted_rows += len(batch)

    logger.info(
        "Pacemaker telemetry seed completed. Inserted=%d, skipped=%d.",
        inserted_rows,
        skipped_rows,
    )
