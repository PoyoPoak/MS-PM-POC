import hashlib
import json

from fastapi.testclient import TestClient
from sqlmodel import Session, delete, func, select

from app.core.config import settings
from app.models import ModelArtifact


def _base_metadata() -> dict[str, object]:
    return {
        "client_version_id": "20260301_120000",
        "source_run_id": "ado-run-1842",
        "trained_at_utc": "2026-03-01T12:00:00Z",
        "algorithm": "RandomForestClassifier",
        "hyperparameters": {
            "n_estimators": 200,
            "max_depth": 20,
            "random_state": 42,
        },
        "metrics": {
            "oob_score": 0.9312,
            "kfold_cv_mean": 0.9244,
            "kfold_cv_std": 0.0081,
            "test_accuracy": 0.9287,
        },
        "dataset_info": {
            "train_rows": 8400,
            "test_rows": 2100,
            "n_features": 12,
            "positive_rate_train": 0.132,
        },
        "notes": "Nightly retrain run",
    }


def _count_model_artifacts(db: Session) -> int:
    statement = select(func.count()).select_from(ModelArtifact)
    return int(db.exec(statement).one())


def test_upload_model_artifact(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    db.exec(delete(ModelArtifact))
    db.commit()

    model_bytes = b"random-forest-model-bytes"
    metadata = _base_metadata()

    response = client.post(
        f"{settings.API_V1_STR}/models/upload",
        headers=superuser_token_headers,
        data={"metadata_json": json.dumps(metadata)},
        files={
            "model_file": (
                "rf_model.joblib",
                model_bytes,
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 200
    content = response.json()
    assert content["algorithm"] == "RandomForestClassifier"
    assert content["client_version_id"] == metadata["client_version_id"]
    assert content["source_run_id"] == metadata["source_run_id"]
    assert content["model_size_bytes"] == len(model_bytes)
    assert content["model_sha256"] == hashlib.sha256(model_bytes).hexdigest()
    assert _count_model_artifacts(db) == 1


def test_upload_model_artifact_not_enough_permissions(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/models/upload",
        headers=normal_user_token_headers,
        data={"metadata_json": json.dumps(_base_metadata())},
        files={
            "model_file": (
                "rf_model.joblib",
                b"model",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "The user doesn't have enough privileges"}


def test_upload_model_artifact_unauthenticated(client: TestClient) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/models/upload",
        data={"metadata_json": json.dumps(_base_metadata())},
        files={
            "model_file": (
                "rf_model.joblib",
                b"model",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 401


def test_upload_model_artifact_invalid_metadata_json(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/models/upload",
        headers=superuser_token_headers,
        data={"metadata_json": "not-json"},
        files={
            "model_file": (
                "rf_model.joblib",
                b"model",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "metadata_json must be valid JSON."}


def test_upload_model_artifact_missing_required_metadata_field(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    metadata = _base_metadata()
    metadata.pop("algorithm")

    response = client.post(
        f"{settings.API_V1_STR}/models/upload",
        headers=superuser_token_headers,
        data={"metadata_json": json.dumps(metadata)},
        files={
            "model_file": (
                "rf_model.joblib",
                b"model",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 422


def test_upload_model_artifact_rejects_empty_file(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/models/upload",
        headers=superuser_token_headers,
        data={"metadata_json": json.dumps(_base_metadata())},
        files={
            "model_file": (
                "rf_model.joblib",
                b"",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "model_file must not be empty."}
