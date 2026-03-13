from typing import Any

from fastapi import APIRouter
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    DashboardSummary,
    ModelArtifact,
    ModelArtifactPublic,
    PacemakerTelemetry,
    PatientLatestTelemetry,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _to_model_artifact_public(model: ModelArtifact) -> ModelArtifactPublic:
    return ModelArtifactPublic(
        id=model.id,
        created_at=model.created_at,
        client_version_id=model.client_version_id,
        source_run_id=model.source_run_id,
        trained_at_utc=model.trained_at_utc,
        algorithm=model.algorithm,
        hyperparameters=model.hyperparameters,
        metrics=model.metrics,
        dataset_info=model.dataset_info,
        notes=model.notes,
        is_active=model.is_active,
        content_type=model.content_type,
        model_size_bytes=model.model_size_bytes,
        model_sha256=model.model_sha256,
    )


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    *,
    session: SessionDep,
    _current_user: CurrentUser,
) -> Any:
    total_patients = int(
        session.exec(
            select(
                func.count(func.distinct(PacemakerTelemetry.patient_id))
            ).select_from(PacemakerTelemetry)
        ).one()
    )

    high_risk_patients = int(
        session.exec(
            select(func.count())
            .select_from(PatientLatestTelemetry)
            .where(func.coalesce(PatientLatestTelemetry.fail_probability, 0.0) >= 0.7)
        ).one()
    )

    alerts_sent = int(
        session.exec(
            select(func.count())
            .select_from(PatientLatestTelemetry)
            .where(func.coalesce(PatientLatestTelemetry.fail_probability, 0.0) >= 0.75)
        ).one()
    )

    last_update = session.exec(select(func.max(PacemakerTelemetry.timestamp))).one()

    active_model = session.exec(
        select(ModelArtifact)
        .where(ModelArtifact.is_active == True)  # noqa: E712
        .order_by(ModelArtifact.created_at.desc())  # type: ignore[union-attr]
    ).first()

    return DashboardSummary(
        total_patients=total_patients,
        high_risk_patients=high_risk_patients,
        alerts_sent=alerts_sent,
        last_update=last_update,
        active_model=None
        if active_model is None
        else _to_model_artifact_public(active_model),
    )
