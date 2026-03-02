"""Training-sync endpoints consumed by the local compute server.

* ``GET /training/poll``     – is there a pending training job?
* ``GET /training/download`` – fetch mature telemetry rows for training.
* ``POST /training/request`` – create a new pending training job request.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlmodel import func, select

from app.api.deps import SessionDep, get_current_active_superuser
from app.models import (
    PacemakerTelemetry,
    PacemakerTelemetryPublic,
    TrainingDataDownloadResult,
    TrainingJobRequest,
    TrainingJobRequestPublic,
    User,
)

router = APIRouter(prefix="/training", tags=["training"])

_MATURITY_DAYS = 7


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
