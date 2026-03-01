import hashlib
import json
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError

from app.api.deps import SessionDep, get_current_active_superuser
from app.models import (
    ModelArtifact,
    ModelArtifactUploadMetadata,
    ModelArtifactUploadResponse,
    User,
)

_MAX_UPLOAD_BYTES = 64 * 1024 * 1024

router = APIRouter(prefix="/models", tags=["models"])


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
