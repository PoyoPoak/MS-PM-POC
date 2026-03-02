from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import uvicorn
from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

try:
    from backend.util.ml_engine import MLEngine
except ModuleNotFoundError:
    from ml_engine import MLEngine

logger = logging.getLogger(__name__)

_DEFAULT_TRAINING_CSV_PATH = (
    Path(__file__).resolve().parent / "data" / "pacemaker_data_seed.csv"
)
_DEFAULT_BACKEND_UPLOAD_URL = "http://localhost:8000/api/v1/models/upload"
_DEFAULT_TIMEOUT_SECONDS = 60.0


@dataclass
class ListenerSettings:
    api_key: str | None
    backend_upload_url: str
    request_timeout_seconds: float


class TrainJobRequest(BaseModel):
    training_csv_path: str = str(_DEFAULT_TRAINING_CSV_PATH)
    artifact_version_id: str | None = Field(default=None, max_length=255)
    client_version_id: str | None = Field(default=None, max_length=255)
    source_run_id: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=2000)
    upload_to_backend: bool = True
    backend_upload_url: str | None = None
    backend_token: str | None = None

    n_estimators: int = Field(default=100, ge=1)
    max_depth: int | None = Field(default=20, ge=1)
    random_state: int = 42
    n_folds: int = Field(default=5, ge=2)
    test_size: float = Field(default=0.2, gt=0, lt=1)


class TrainJobResponse(BaseModel):
    status: str
    artifact_dir: str
    model_path: str
    metrics: dict[str, Any]
    upload_response: dict[str, Any] | None = None


def _resolve_training_csv_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def _build_metadata_payload(
    request: TrainJobRequest,
    metrics: dict[str, Any],
    *,
    fallback_version_id: str,
) -> dict[str, Any]:
    return {
        "client_version_id": request.client_version_id or fallback_version_id,
        "source_run_id": request.source_run_id,
        "algorithm": "RandomForestClassifier",
        "hyperparameters": metrics.get("hyperparameters", {}),
        "metrics": {
            "oob_score": metrics.get("oob_score"),
            "kfold_cv_mean": metrics.get("kfold_cv_mean"),
            "kfold_cv_std": metrics.get("kfold_cv_std"),
            "test_accuracy": metrics.get("test_accuracy"),
            "classification_report": metrics.get("classification_report"),
            "kfold_cv_scores": metrics.get("kfold_cv_scores"),
        },
        "dataset_info": metrics.get("dataset_info", {}),
        "notes": request.notes,
    }


def _upload_model_artifact(
    *,
    upload_url: str,
    token: str,
    model_path: Path,
    metadata_payload: dict[str, Any],
    timeout_seconds: float,
) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}"}

    with model_path.open("rb") as model_file:
        files = {
            "model_file": (
                model_path.name,
                model_file,
                "application/octet-stream",
            )
        }
        data = {"metadata_json": json.dumps(metadata_payload)}
        response = httpx.post(
            upload_url,
            headers=headers,
            files=files,
            data=data,
            timeout=timeout_seconds,
        )

    response.raise_for_status()

    try:
        return response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Backend upload endpoint returned a non-JSON response.",
        ) from exc


def _train_model(
    request: TrainJobRequest, training_csv_path: Path
) -> tuple[Path, dict[str, Any]]:
    engine = MLEngine(
        n_estimators=request.n_estimators,
        max_depth=request.max_depth,
        random_state=request.random_state,
        n_folds=request.n_folds,
        test_size=request.test_size,
    )
    engine.train(training_csv_path)
    metrics = engine.evaluate()
    artifact_dir = engine.save_artifact(version_id=request.artifact_version_id)
    return artifact_dir, metrics


def create_app(settings: ListenerSettings) -> FastAPI:
    app = FastAPI(title="Pacemaker Local Training Listener", version="0.1.0")

    @app.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/train", response_model=TrainJobResponse)
    def run_training_job(
        request: TrainJobRequest,
        x_listener_key: str | None = Header(default=None),
    ) -> TrainJobResponse:
        if settings.api_key and x_listener_key != settings.api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing X-Listener-Key.",
            )

        training_csv_path = _resolve_training_csv_path(request.training_csv_path)
        if not training_csv_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Training CSV not found: {training_csv_path}",
            )

        try:
            artifact_dir, metrics = _train_model(request, training_csv_path)
        except Exception as exc:
            logger.exception("Training job failed.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Training failed: {exc}",
            ) from exc

        model_path = artifact_dir / "model.joblib"
        metadata_payload = _build_metadata_payload(
            request,
            metrics,
            fallback_version_id=artifact_dir.name,
        )

        upload_response: dict[str, Any] | None = None
        if request.upload_to_backend:
            token = request.backend_token or os.getenv("BACKEND_SUPERUSER_TOKEN")
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        "backend_token is required when upload_to_backend=true "
                        "(or set BACKEND_SUPERUSER_TOKEN)."
                    ),
                )

            upload_url = request.backend_upload_url or settings.backend_upload_url
            try:
                upload_response = _upload_model_artifact(
                    upload_url=upload_url,
                    token=token,
                    model_path=model_path,
                    metadata_payload=metadata_payload,
                    timeout_seconds=settings.request_timeout_seconds,
                )
            except httpx.HTTPStatusError as exc:
                backend_status = exc.response.status_code
                backend_detail = exc.response.text
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=(
                        "Backend upload failed with status "
                        f"{backend_status}: {backend_detail}"
                    ),
                ) from exc
            except httpx.HTTPError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Backend upload request failed: {exc}",
                ) from exc

        return TrainJobResponse(
            status="completed",
            artifact_dir=str(artifact_dir),
            model_path=str(model_path),
            metrics=metrics,
            upload_response=upload_response,
        )

    return app


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the local training listener service. "
            "POST /train to trigger MLEngine training and artifact upload."
        )
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Host to bind the listener."
    )
    parser.add_argument(
        "--port", type=int, default=8081, help="Port to bind the listener."
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("TRAINING_LISTENER_API_KEY"),
        help="Optional shared key expected in X-Listener-Key.",
    )
    parser.add_argument(
        "--backend-upload-url",
        default=os.getenv("BACKEND_MODEL_UPLOAD_URL", _DEFAULT_BACKEND_UPLOAD_URL),
        help="Default backend model upload endpoint.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=_DEFAULT_TIMEOUT_SECONDS,
        help="Timeout for backend upload requests.",
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["critical", "error", "warning", "info", "debug"],
        help="Listener log verbosity.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    settings = ListenerSettings(
        api_key=args.api_key,
        backend_upload_url=args.backend_upload_url,
        request_timeout_seconds=args.timeout_seconds,
    )

    app = create_app(settings)
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
