import hashlib
import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlmodel import select

from app.api.deps import SessionDep, get_current_active_superuser
from app.models import (
    Message,
    ModelArtifact,
    ModelArtifactPublic,
    ModelArtifactsPublic,
    ModelArtifactUploadMetadata,
    ModelArtifactUploadResponse,
    User,
)

_MAX_UPLOAD_BYTES = 64 * 1024 * 1024

router = APIRouter(prefix="/models", tags=["models"])


def _is_active_model(model: ModelArtifact) -> bool:
    return bool(model.dataset_info.get("is_active", False))


def _to_model_public(model: ModelArtifact, *, is_active: bool) -> ModelArtifactPublic:
    return ModelArtifactPublic(
        id=model.id,
        created_at=model.created_at,
        client_version_id=model.client_version_id,
        source_run_id=model.source_run_id,
        trained_at_utc=model.trained_at_utc,
        algorithm=model.algorithm,
        metrics=model.metrics,
        dataset_info=model.dataset_info,
        is_active=is_active,
    )


def _resolve_active_model_id(models: list[ModelArtifact]) -> uuid.UUID | None:
    active_model = next((model for model in models if _is_active_model(model)), None)
    if active_model is not None:
        return active_model.id
    if not models:
        return None
    return models[0].id


@router.post("/upload", response_model=ModelArtifactUploadResponse)
def upload_model_artifact(
    *,
    session: SessionDep,
    current_superuser: User = Depends(get_current_active_superuser),
    model_file: UploadFile = File(...),
    metadata_json: str = Form(...),
) -> Any:
    """
    Upload a trained model artifact with metrics and persist to PostgreSQL.

    - `model_file`: binary model payload (for example `.joblib`)
    - `metadata_json`: JSON string containing algorithm, metrics, and run metadata
    """
    _ = current_superuser.id

    try:
        metadata_dict = json.loads(metadata_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="metadata_json must be valid JSON.",
        ) from exc

    try:
        metadata = ModelArtifactUploadMetadata.model_validate(metadata_dict)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(),
        ) from exc

    model_bytes = model_file.file.read()
    if not model_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="model_file must not be empty.",
        )

    model_size_bytes = len(model_bytes)
    if model_size_bytes > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"model_file exceeds {_MAX_UPLOAD_BYTES} bytes.",
        )

    model_sha256 = hashlib.sha256(model_bytes).hexdigest()

    db_model_artifact = ModelArtifact(
        client_version_id=metadata.client_version_id,
        source_run_id=metadata.source_run_id,
        trained_at_utc=metadata.trained_at_utc,
        algorithm=metadata.algorithm,
        hyperparameters=metadata.hyperparameters,
        metrics=metadata.metrics,
        dataset_info=metadata.dataset_info,
        notes=metadata.notes,
        content_type=model_file.content_type,
        model_size_bytes=model_size_bytes,
        model_sha256=model_sha256,
        model_blob=model_bytes,
    )

    session.add(db_model_artifact)
    session.commit()
    session.refresh(db_model_artifact)

    return ModelArtifactUploadResponse(
        id=db_model_artifact.id,
        created_at=db_model_artifact.created_at,
        client_version_id=db_model_artifact.client_version_id,
        source_run_id=db_model_artifact.source_run_id,
        algorithm=db_model_artifact.algorithm,
        model_size_bytes=db_model_artifact.model_size_bytes,
        model_sha256=db_model_artifact.model_sha256,
        content_type=db_model_artifact.content_type,
    )


@router.get("/", response_model=ModelArtifactsPublic)
def read_model_artifacts(
    *,
    session: SessionDep,
    _current_superuser: User = Depends(get_current_active_superuser),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    ordered_models = list(
        session.exec(
            select(ModelArtifact).order_by(ModelArtifact.created_at.desc())  # type: ignore[union-attr]
        ).all()
    )
    active_model_id = _resolve_active_model_id(ordered_models)
    sliced_models = ordered_models[skip : skip + limit]

    return ModelArtifactsPublic(
        data=[
            _to_model_public(model, is_active=model.id == active_model_id)
            for model in sliced_models
        ],
        count=len(ordered_models),
    )


@router.get("/active", response_model=ModelArtifactPublic)
def read_active_model_artifact(
    *,
    session: SessionDep,
    _current_superuser: User = Depends(get_current_active_superuser),
) -> Any:
    ordered_models = list(
        session.exec(
            select(ModelArtifact).order_by(ModelArtifact.created_at.desc())  # type: ignore[union-attr]
        ).all()
    )
    active_model_id = _resolve_active_model_id(ordered_models)
    if active_model_id is None:
        raise HTTPException(status_code=404, detail="No model artifacts found.")

    active_model = next(
        model for model in ordered_models if model.id == active_model_id
    )
    return _to_model_public(active_model, is_active=True)


@router.post("/{model_id}/activate", response_model=ModelArtifactPublic)
def activate_model_artifact(
    *,
    session: SessionDep,
    model_id: uuid.UUID,
    _current_superuser: User = Depends(get_current_active_superuser),
) -> Any:
    ordered_models = list(session.exec(select(ModelArtifact)).all())
    target_model = next(
        (model for model in ordered_models if model.id == model_id), None
    )
    if target_model is None:
        raise HTTPException(status_code=404, detail="Model artifact not found.")

    for model in ordered_models:
        dataset_info = dict(model.dataset_info)
        if model.id == model_id:
            dataset_info["is_active"] = True
        else:
            dataset_info.pop("is_active", None)
        model.dataset_info = dataset_info
        session.add(model)

    session.commit()
    session.refresh(target_model)
    return _to_model_public(target_model, is_active=True)


@router.delete("/{model_id}", response_model=Message)
def delete_model_artifact(
    *,
    session: SessionDep,
    model_id: uuid.UUID,
    _current_superuser: User = Depends(get_current_active_superuser),
) -> Any:
    model = session.get(ModelArtifact, model_id)
    if model is None:
        raise HTTPException(status_code=404, detail="Model artifact not found.")

    session.delete(model)
    session.commit()
    return Message(message="Model artifact deleted successfully")
