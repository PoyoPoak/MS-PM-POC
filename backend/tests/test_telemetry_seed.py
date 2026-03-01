from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlmodel import Session, delete, func, select

from app.models import PacemakerTelemetry
from app.telemetry_seed import seed_pacemaker_telemetry_if_empty

CSV_HEADER = (
    "Patient_ID,Timestamp,Lead_Impedance_Ohms,Capture_Threshold_V,"
    "R_Wave_Sensing_mV,Battery_Voltage_V,Target_Fail_Next_7d,"
    "Lead_Impedance_Ohms_RollingMean_3d,Lead_Impedance_Ohms_RollingMean_7d,"
    "Capture_Threshold_V_RollingMean_3d,Capture_Threshold_V_RollingMean_7d,"
    "Lead_Impedance_Ohms_DeltaPerDay_3d,Lead_Impedance_Ohms_DeltaPerDay_7d,"
    "Capture_Threshold_V_DeltaPerDay_3d,Capture_Threshold_V_DeltaPerDay_7d"
)


def _count_rows(session: Session) -> int:
    query = select(func.count()).select_from(PacemakerTelemetry)
    return int(session.exec(query).one())


def _write_csv(path: Path, rows: list[str]) -> None:
    content = "\n".join([CSV_HEADER, *rows])
    path.write_text(content, encoding="utf-8")


def test_seed_pacemaker_telemetry_inserts_when_empty(
    db: Session,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SEED_PACEMAKER_DATA", "true")

    db.exec(delete(PacemakerTelemetry))
    db.commit()

    csv_path = tmp_path / "pacemaker_data.csv"
    _write_csv(
        csv_path,
        [
            "1,1700000000,540,1.1,8.2,2.8,1,535,530,1.05,1.0,2.1,1.8,0.1,0.07",
            "2,1700003600,500,0.9,9.1,2.9,0,501,500,0.95,0.93,0.2,0.1,0.03,0.02",
        ],
    )

    seed_pacemaker_telemetry_if_empty(db, csv_path=csv_path, batch_size=1)

    assert _count_rows(db) == 2


def test_seed_pacemaker_telemetry_appends_when_table_has_rows(
    db: Session,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SEED_PACEMAKER_DATA", "true")

    db.exec(delete(PacemakerTelemetry))
    db.commit()

    existing = PacemakerTelemetry(
        patient_id=99,
        timestamp=datetime.now(timezone.utc),
        lead_impedance_ohms=500,
        capture_threshold_v=1.0,
        r_wave_sensing_mv=8.0,
        battery_voltage_v=2.7,
        target_fail_next_7d=0,
    )
    db.add(existing)
    db.commit()

    csv_path = tmp_path / "pacemaker_data.csv"
    _write_csv(
        csv_path,
        [
            "10,1700000000,550,1.2,7.8,2.6,1,540,538,1.1,1.0,3.2,2.3,0.2,0.11",
        ],
    )

    seed_pacemaker_telemetry_if_empty(db, csv_path=csv_path)

    assert _count_rows(db) == 2


def test_seed_pacemaker_telemetry_skips_when_flag_disabled(
    db: Session,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SEED_PACEMAKER_DATA", "false")

    db.exec(delete(PacemakerTelemetry))
    db.commit()

    csv_path = tmp_path / "pacemaker_data.csv"
    _write_csv(
        csv_path,
        [
            "10,1700000000,550,1.2,7.8,2.6,1,540,538,1.1,1.0,3.2,2.3,0.2,0.11",
        ],
    )

    seed_pacemaker_telemetry_if_empty(db, csv_path=csv_path)

    assert _count_rows(db) == 0


def test_seed_pacemaker_telemetry_skips_when_csv_missing(
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SEED_PACEMAKER_DATA", "true")

    db.exec(delete(PacemakerTelemetry))
    db.commit()

    seed_pacemaker_telemetry_if_empty(
        db,
        csv_path=Path("./backend/util/data/this_file_does_not_exist.csv"),
    )

    assert _count_rows(db) == 0


def test_seed_pacemaker_telemetry_inserts_same_number_of_rows_as_csv(
    db: Session,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SEED_PACEMAKER_DATA", "true")

    db.exec(delete(PacemakerTelemetry))
    db.commit()

    csv_rows = [
        "101,1700000000,540,1.1,8.2,2.8,1,535,530,1.05,1.0,2.1,1.8,0.1,0.07",
        "102,1700003600,500,0.9,9.1,2.9,0,501,500,0.95,0.93,0.2,0.1,0.03,0.02",
        "103,1700007200,525,1.0,8.7,2.7,1,520,518,0.98,0.97,0.6,0.4,0.05,0.03",
    ]

    csv_path = tmp_path / "pacemaker_data.csv"
    _write_csv(csv_path, csv_rows)

    seed_pacemaker_telemetry_if_empty(db, csv_path=csv_path, batch_size=2)

    assert _count_rows(db) == len(csv_rows)
