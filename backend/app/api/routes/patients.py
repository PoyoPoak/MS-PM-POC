from typing import Any, Literal

from fastapi import APIRouter, Query
from sqlmodel import and_, func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    PacemakerTelemetry,
    PatientLatestTelemetry,
    PatientLatestTelemetryPublic,
    PatientLatestTelemetryPublicList,
)

router = APIRouter(prefix="/patients", tags=["patients"])

SortBy = Literal[
    "patient_id",
    "risk_score",
    "lead_impedance",
    "capture_threshold",
    "battery_voltage",
    "last_update",
]
SortOrder = Literal["asc", "desc"]
RiskFilter = Literal["all", "high", "medium", "low"]
AlertFilter = Literal["all", "sent", "none"]


@router.get("/latest", response_model=PatientLatestTelemetryPublicList)
def list_latest_patient_telemetry(
    *,
    session: SessionDep,
    _current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    sort_by: SortBy = "risk_score",
    sort_order: SortOrder = "desc",
    patient_search: str | None = Query(default=None),
    risk_filter: RiskFilter = "all",
    alert_filter: AlertFilter = "all",
) -> Any:
    latest_ts_subquery = (
        select(
            PacemakerTelemetry.patient_id.label("patient_id"),  # type: ignore[attr-defined]
            func.max(PacemakerTelemetry.timestamp).label("max_timestamp"),
        )
        .group_by(PacemakerTelemetry.patient_id)  # type: ignore[arg-type]
        .subquery()
    )

    latest_rows_statement = (
        select(PacemakerTelemetry)
        .join(
            latest_ts_subquery,
            and_(
                PacemakerTelemetry.patient_id == latest_ts_subquery.c.patient_id,
                PacemakerTelemetry.timestamp == latest_ts_subquery.c.max_timestamp,
            ),
        )
        .order_by(
            PacemakerTelemetry.patient_id,  # type: ignore[arg-type]
            PacemakerTelemetry.created_at.desc(),  # type: ignore[union-attr]
        )
    )
    latest_rows = session.exec(latest_rows_statement).all()

    newest_by_patient: dict[int, PacemakerTelemetry] = {}
    for row in latest_rows:
        if row.patient_id not in newest_by_patient:
            newest_by_patient[row.patient_id] = row

    latest_patient_ids = list(newest_by_patient)
    probability_map: dict[int, float | None] = {}
    if latest_patient_ids:
        snapshot_statement = select(PatientLatestTelemetry).where(
            PatientLatestTelemetry.patient_id.in_(latest_patient_ids)
        )
        snapshots = session.exec(snapshot_statement).all()
        probability_map = {
            snapshot.patient_id: snapshot.fail_probability for snapshot in snapshots
        }

    rows = [
        PatientLatestTelemetryPublic(
            patient_id=row.patient_id,
            timestamp=row.timestamp,
            lead_impedance_ohms=row.lead_impedance_ohms,
            capture_threshold_v=row.capture_threshold_v,
            r_wave_sensing_mv=row.r_wave_sensing_mv,
            battery_voltage_v=row.battery_voltage_v,
            lead_impedance_ohms_rolling_mean_3d=row.lead_impedance_ohms_rolling_mean_3d,
            lead_impedance_ohms_rolling_mean_7d=row.lead_impedance_ohms_rolling_mean_7d,
            capture_threshold_v_rolling_mean_3d=row.capture_threshold_v_rolling_mean_3d,
            capture_threshold_v_rolling_mean_7d=row.capture_threshold_v_rolling_mean_7d,
            lead_impedance_ohms_delta_per_day_3d=row.lead_impedance_ohms_delta_per_day_3d,
            lead_impedance_ohms_delta_per_day_7d=row.lead_impedance_ohms_delta_per_day_7d,
            capture_threshold_v_delta_per_day_3d=row.capture_threshold_v_delta_per_day_3d,
            capture_threshold_v_delta_per_day_7d=row.capture_threshold_v_delta_per_day_7d,
            fail_probability=probability_map.get(row.patient_id),
            created_at=row.created_at,
        )
        for row in newest_by_patient.values()
    ]

    if patient_search:
        rows = [row for row in rows if patient_search in str(row.patient_id)]

    if risk_filter == "high":
        rows = [
            row
            for row in rows
            if row.fail_probability is not None and row.fail_probability >= 0.7
        ]
    elif risk_filter == "medium":
        rows = [
            row
            for row in rows
            if row.fail_probability is not None and 0.4 <= row.fail_probability < 0.7
        ]
    elif risk_filter == "low":
        rows = [
            row
            for row in rows
            if row.fail_probability is None or row.fail_probability < 0.4
        ]

    if alert_filter == "sent":
        rows = [
            row
            for row in rows
            if row.fail_probability is not None and row.fail_probability >= 0.75
        ]
    elif alert_filter == "none":
        rows = [
            row
            for row in rows
            if row.fail_probability is None or row.fail_probability < 0.75
        ]

    sort_key_map: dict[SortBy, Any] = {
        "patient_id": lambda row: row.patient_id,
        "risk_score": lambda row: row.fail_probability
        if row.fail_probability is not None
        else -1.0,
        "lead_impedance": lambda row: row.lead_impedance_ohms,
        "capture_threshold": lambda row: row.capture_threshold_v,
        "battery_voltage": lambda row: row.battery_voltage_v,
        "last_update": lambda row: row.timestamp,
    }
    rows = sorted(rows, key=sort_key_map[sort_by], reverse=sort_order == "desc")

    count = len(rows)
    paginated_rows = rows[skip : skip + limit]

    return PatientLatestTelemetryPublicList(data=paginated_rows, count=count)
