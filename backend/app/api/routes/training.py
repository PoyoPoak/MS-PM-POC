"""Training-sync endpoints consumed by the local compute server.

* ``GET  /training/poll``            – is there a pending training job?
* ``GET  /training/download``        – fetch mature telemetry rows for training.
* ``POST /training/request``         – create a new pending training job request.
* ``POST /training/claim``           – atomically claim the newest pending job.
* ``POST /training/{job_id}/complete`` – mark a claimed job as complete.
"""

import uuid
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import Any

import joblib  # type: ignore[import-untyped]
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import and_, func, select

from app.api.deps import SessionDep, get_current_active_superuser
from app.models import (
    ModelArtifact,
    PacemakerTelemetry,
    PacemakerTelemetryPublic,
    PatientLatestTelemetry,
    PatientRiskRowPublic,
    PatientRiskRowsPublic,
    TrainingDataDownloadResult,
    TrainingJobRequest,
    TrainingJobRequestPublic,
    TrainingPredictSummary,
    User,
)

router = APIRouter(prefix="/training", tags=["training"])

_MATURITY_DAYS = 7
_PREDICT_FEATURE_COLUMNS: list[str] = [
    "lead_impedance_ohms",
    "capture_threshold_v",
    "r_wave_sensing_mv",
    "battery_voltage_v",
    "lead_impedance_ohms_rolling_mean_3d",
    "lead_impedance_ohms_rolling_mean_7d",
    "capture_threshold_v_rolling_mean_3d",
    "capture_threshold_v_rolling_mean_7d",
    "lead_impedance_ohms_delta_per_day_3d",
    "lead_impedance_ohms_delta_per_day_7d",
    "capture_threshold_v_delta_per_day_3d",
    "capture_threshold_v_delta_per_day_7d",
]


def _risk_level(score: float) -> str:
    if score >= 0.8:
        return "HIGH"
    if score >= 0.6:
        return "MED"
    return "LOW"


@router.get("/poll")
def poll_training_job(
    *,
    session: SessionDep,
    _current_superuser: User = Depends(get_current_active_superuser),
) -> bool:
    """Return ``true`` when at least one pending training-job request exists."""
    statement = select(TrainingJobRequest.id).where(
        TrainingJobRequest.is_pending == True  # noqa: E712
    )
    row = session.exec(statement).first()
    return row is not None


@router.get("/download", response_model=TrainingDataDownloadResult)
def download_training_data(
    *,
    session: SessionDep,
    _current_superuser: User = Depends(get_current_active_superuser),
    newest_local_ts: int = Query(
        ...,
        description=(
            "Unix epoch seconds of the newest telemetry row "
            "the local compute already has."
        ),
    ),
) -> Any:
    """Return mature telemetry rows the local compute has not yet seen.

    **Boundary rules**

    * ``local_dt``   = ``datetime(newest_local_ts, UTC)``
    * ``server_max`` = ``MAX(pacemaker_telemetry.timestamp)``
    * ``cutoff``     = ``server_max − 7 days``
    * Result set:  ``timestamp > local_dt  AND  timestamp <= cutoff``

    If the table is empty **or** no rows satisfy the window, an empty
    ``rows`` list is returned with ``count = 0``.
    """
    local_dt = datetime.fromtimestamp(newest_local_ts, tz=timezone.utc)

    # Determine server-side newest timestamp
    server_max_row = session.exec(select(func.max(PacemakerTelemetry.timestamp))).one()
    server_max: datetime | None = server_max_row

    if server_max is None:
        return TrainingDataDownloadResult(
            rows=[], count=0, server_newest_ts=None, maturity_cutoff_ts=None
        )

    cutoff = server_max - timedelta(days=_MATURITY_DAYS)

    # Nothing qualifies if the cutoff is at or before the local timestamp
    if cutoff <= local_dt:
        return TrainingDataDownloadResult(
            rows=[],
            count=0,
            server_newest_ts=int(server_max.timestamp()),
            maturity_cutoff_ts=int(cutoff.timestamp()),
        )

    statement = (
        select(PacemakerTelemetry)
        .where(PacemakerTelemetry.timestamp > local_dt)
        .where(PacemakerTelemetry.timestamp <= cutoff)
        .order_by(PacemakerTelemetry.timestamp)  # type: ignore[arg-type]
    )
    rows = session.exec(statement).all()

    telemetry_out = [PacemakerTelemetryPublic.model_validate(r) for r in rows]

    return TrainingDataDownloadResult(
        rows=telemetry_out,
        count=len(telemetry_out),
        server_newest_ts=int(server_max.timestamp()),
        maturity_cutoff_ts=int(cutoff.timestamp()),
    )


@router.post("/request", response_model=TrainingJobRequestPublic)
def create_training_job_request(
    *,
    session: SessionDep,
    current_superuser: User = Depends(get_current_active_superuser),
) -> Any:
    """Create a pending training-job request.

    Called by the frontend when a user clicks the "Request Training" button.
    """
    job = TrainingJobRequest(requested_by=current_superuser.id)
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


@router.post("/predict", response_model=TrainingPredictSummary)
def refresh_patient_latest_predictions(
    *,
    session: SessionDep,
    _current_superuser: User = Depends(get_current_active_superuser),
) -> Any:
    """Refresh latest-per-patient telemetry snapshot and fail probabilities."""
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

    rows_upserted = 0
    for source in newest_by_patient.values():
        target = session.get(PatientLatestTelemetry, source.patient_id)
        if target is None:
            target = PatientLatestTelemetry(patient_id=source.patient_id)
        target.timestamp = source.timestamp
        target.lead_impedance_ohms = source.lead_impedance_ohms
        target.capture_threshold_v = source.capture_threshold_v
        target.r_wave_sensing_mv = source.r_wave_sensing_mv
        target.battery_voltage_v = source.battery_voltage_v
        target.lead_impedance_ohms_rolling_mean_3d = (
            source.lead_impedance_ohms_rolling_mean_3d
        )
        target.lead_impedance_ohms_rolling_mean_7d = (
            source.lead_impedance_ohms_rolling_mean_7d
        )
        target.capture_threshold_v_rolling_mean_3d = (
            source.capture_threshold_v_rolling_mean_3d
        )
        target.capture_threshold_v_rolling_mean_7d = (
            source.capture_threshold_v_rolling_mean_7d
        )
        target.lead_impedance_ohms_delta_per_day_3d = (
            source.lead_impedance_ohms_delta_per_day_3d
        )
        target.lead_impedance_ohms_delta_per_day_7d = (
            source.lead_impedance_ohms_delta_per_day_7d
        )
        target.capture_threshold_v_delta_per_day_3d = (
            source.capture_threshold_v_delta_per_day_3d
        )
        target.capture_threshold_v_delta_per_day_7d = (
            source.capture_threshold_v_delta_per_day_7d
        )
        session.add(target)
        rows_upserted += 1

    session.commit()

    if rows_upserted == 0:
        return TrainingPredictSummary(
            rows_upserted=0,
            rows_scored=0,
            model_id=None,
            queued_job_id=None,
        )

    newest_model_statement = select(ModelArtifact).order_by(
        ModelArtifact.created_at.desc()  # type: ignore[union-attr]
    )
    newest_model = session.exec(newest_model_statement).first()

    if newest_model is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "No model artifacts available for inference.",
                "rows_upserted": rows_upserted,
                "rows_scored": 0,
                "model_id": None,
                "queued_job_id": None,
            },
        )

    snapshots = session.exec(
        select(PatientLatestTelemetry).order_by(PatientLatestTelemetry.patient_id)  # type: ignore[arg-type]
    ).all()

    if not snapshots:
        return TrainingPredictSummary(
            rows_upserted=rows_upserted,
            rows_scored=0,
            model_id=newest_model.id,
            queued_job_id=None,
        )

    rows_for_matrix: list[list[float]] = []
    for snapshot in snapshots:
        feature_values: list[float | None] = [
            snapshot.lead_impedance_ohms,
            snapshot.capture_threshold_v,
            snapshot.r_wave_sensing_mv,
            snapshot.battery_voltage_v,
            snapshot.lead_impedance_ohms_rolling_mean_3d,
            snapshot.lead_impedance_ohms_rolling_mean_7d,
            snapshot.capture_threshold_v_rolling_mean_3d,
            snapshot.capture_threshold_v_rolling_mean_7d,
            snapshot.lead_impedance_ohms_delta_per_day_3d,
            snapshot.lead_impedance_ohms_delta_per_day_7d,
            snapshot.capture_threshold_v_delta_per_day_3d,
            snapshot.capture_threshold_v_delta_per_day_7d,
        ]

        normalized_feature_values: list[float] = []
        for value in feature_values:
            if value is None:
                raise HTTPException(
                    status_code=422,
                    detail="Latest patient telemetry snapshot has missing feature values.",
                )
            normalized_feature_values.append(float(value))

        rows_for_matrix.append(normalized_feature_values)

    model = joblib.load(BytesIO(newest_model.model_blob))
    feature_matrix = np.asarray(rows_for_matrix, dtype=np.float64)
    probabilities = model.predict_proba(feature_matrix)[:, 1]

    for snapshot, probability in zip(snapshots, probabilities, strict=True):
        snapshot.fail_probability = float(probability)
        session.add(snapshot)

    session.commit()

    return TrainingPredictSummary(
        rows_upserted=rows_upserted,
        rows_scored=len(snapshots),
        model_id=newest_model.id,
        queued_job_id=None,
    )


@router.get("/risk", response_model=PatientRiskRowsPublic)
def read_at_risk_patients(
    *,
    session: SessionDep,
    _current_superuser: User = Depends(get_current_active_superuser),
    skip: int = 0,
    limit: int = 50,
    search: str | None = Query(default=None),
    min_risk: float = Query(default=0.0, ge=0.0, le=1.0),
) -> Any:
    statement = (
        select(PatientLatestTelemetry)
        .where(PatientLatestTelemetry.fail_probability.is_not(None))  # type: ignore[union-attr]
        .order_by(PatientLatestTelemetry.fail_probability.desc())  # type: ignore[union-attr]
    )
    snapshots = list(session.exec(statement).all())

    filtered_rows: list[PatientLatestTelemetry] = []
    normalized_search = search.lower().strip() if search else None
    for snapshot in snapshots:
        score = float(snapshot.fail_probability or 0.0)
        if score < min_risk:
            continue

        if normalized_search is not None:
            patient_label = f"pat-{snapshot.patient_id}".lower()
            if normalized_search not in patient_label and normalized_search not in str(
                snapshot.patient_id
            ):
                continue

        filtered_rows.append(snapshot)

    paginated_rows = filtered_rows[skip : skip + limit]
    payload_rows = [
        PatientRiskRowPublic(
            patient_id=row.patient_id,
            timestamp=row.timestamp,
            fail_probability=float(row.fail_probability or 0.0),
            risk_level=_risk_level(float(row.fail_probability or 0.0)),
            battery_voltage_v=row.battery_voltage_v,
            lead_impedance_ohms=row.lead_impedance_ohms,
            capture_threshold_v=row.capture_threshold_v,
        )
        for row in paginated_rows
    ]

    latest_timestamp = max((row.timestamp for row in filtered_rows), default=None)

    return PatientRiskRowsPublic(
        data=payload_rows,
        count=len(filtered_rows),
        refreshed_at=latest_timestamp,
    )


@router.post("/claim", response_model=TrainingJobRequestPublic)
def claim_training_job(
    *,
    session: SessionDep,
    _current_superuser: User = Depends(get_current_active_superuser),
) -> Any:
    """Atomically claim the **newest** pending training-job request.

    * Any *older* pending jobs are cancelled (``cancelled_at`` set to
      now-UTC, ``is_pending`` set to ``False``).
    * Returns **404** when no pending job exists.
    * Returns **409** when a job is already in-progress (claimed but
      not yet completed/cancelled).  Only one job may run at a time.
    """
    # Guard: reject if another job is already in-progress
    in_progress_stmt = select(TrainingJobRequest.id).where(
        TrainingJobRequest.is_pending == False,  # noqa: E712
        TrainingJobRequest.consumed_at.is_(None),  # type: ignore[union-attr]
        TrainingJobRequest.cancelled_at.is_(None),  # type: ignore[union-attr]
    )
    if session.exec(in_progress_stmt).first() is not None:
        raise HTTPException(
            status_code=409,
            detail="A training job is already in progress.",
        )

    # Fetch all pending jobs newest-first
    pending_stmt = (
        select(TrainingJobRequest)
        .where(TrainingJobRequest.is_pending == True)  # noqa: E712
        .order_by(TrainingJobRequest.created_at.desc())  # type: ignore[union-attr]
    )
    pending_jobs = list(session.exec(pending_stmt).all())
    if not pending_jobs:
        raise HTTPException(status_code=404, detail="No pending training job.")

    # Claim the newest (first in list)
    newest = pending_jobs[0]
    newest.is_pending = False
    session.add(newest)

    # Cancel all older pending jobs
    now = datetime.now(timezone.utc)
    for older in pending_jobs[1:]:
        older.is_pending = False
        older.cancelled_at = now
        session.add(older)

    session.commit()
    session.refresh(newest)
    return newest


@router.post("/{job_id}/complete", response_model=TrainingJobRequestPublic)
def complete_training_job(
    *,
    session: SessionDep,
    job_id: uuid.UUID,
    _current_superuser: User = Depends(get_current_active_superuser),
) -> Any:
    """Mark a claimed training-job request as complete.

    Sets ``consumed_at`` to now-UTC.  Returns **404** when the job does
    not exist and **409** when the job is still pending (not yet claimed)
    or has already been completed.
    """
    job = session.get(TrainingJobRequest, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Training job not found.")
    if job.is_pending:
        raise HTTPException(
            status_code=409,
            detail="Job has not been claimed yet.",
        )
    if job.consumed_at is not None:
        raise HTTPException(
            status_code=409,
            detail="Job has already been completed.",
        )
    if job.cancelled_at is not None:
        raise HTTPException(
            status_code=409,
            detail="Job was cancelled.",
        )
    job.consumed_at = datetime.now(timezone.utc)
    session.add(job)
    session.commit()
    session.refresh(job)
    return job
