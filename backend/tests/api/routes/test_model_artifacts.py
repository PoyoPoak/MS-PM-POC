import hashlib
import json
import uuid
from datetime import datetime, timezone

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


def _create_model_artifact(
    db: Session,
    *,
    client_version_id: str,
    is_active: bool = False,
) -> ModelArtifact:
    artifact = ModelArtifact(
        client_version_id=client_version_id,
        source_run_id=f"run-{client_version_id}",
        trained_at_utc=datetime.now(tz=timezone.utc),
        algorithm="RandomForestClassifier",
        hyperparameters={"n_estimators": 20},
        metrics={"recall": 0.91, "f1": 0.88},
        dataset_info={"rows": 1000, "is_active": is_active},
        notes="created for endpoint testing",
        content_type="application/octet-stream",
        model_size_bytes=4,
        model_sha256=("a" * 63) + str(uuid.uuid4().int % 10),
        model_blob=b"test",
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact


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


def test_read_model_artifacts_returns_active_and_count(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    db.exec(delete(ModelArtifact))
    db.commit()
    first = _create_model_artifact(db, client_version_id="v1", is_active=False)
    second = _create_model_artifact(db, client_version_id="v2", is_active=True)

    response = client.get(
        f"{settings.API_V1_STR}/models/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["count"] == 2
    assert len(content["data"]) == 2
    active_models = [row for row in content["data"] if row["is_active"] is True]
    assert len(active_models) == 1
    assert active_models[0]["id"] == str(second.id)
    assert {row["id"] for row in content["data"]} == {str(first.id), str(second.id)}


def test_read_active_model_falls_back_to_newest(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    db.exec(delete(ModelArtifact))
    db.commit()
    _create_model_artifact(db, client_version_id="v1", is_active=False)
    newest = _create_model_artifact(db, client_version_id="v2", is_active=False)

    response = client.get(
        f"{settings.API_V1_STR}/models/active",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(newest.id)
    assert content["is_active"] is True


def test_activate_model_artifact_sets_single_active(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    db.exec(delete(ModelArtifact))
    db.commit()
    first = _create_model_artifact(db, client_version_id="v1", is_active=True)
    second = _create_model_artifact(db, client_version_id="v2", is_active=False)

    activate_response = client.post(
        f"{settings.API_V1_STR}/models/{second.id}/activate",
        headers=superuser_token_headers,
    )
    assert activate_response.status_code == 200
    assert activate_response.json()["id"] == str(second.id)
    assert activate_response.json()["is_active"] is True

    list_response = client.get(
        f"{settings.API_V1_STR}/models/",
        headers=superuser_token_headers,
    )
    assert list_response.status_code == 200
    rows = list_response.json()["data"]
    active_rows = [row for row in rows if row["is_active"] is True]
    assert len(active_rows) == 1
    assert active_rows[0]["id"] == str(second.id)
    first_row = next(row for row in rows if row["id"] == str(first.id))
    assert first_row["is_active"] is False


def test_delete_model_artifact(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    db.exec(delete(ModelArtifact))
    db.commit()
    artifact = _create_model_artifact(db, client_version_id="v1", is_active=False)

    response = client.delete(
        f"{settings.API_V1_STR}/models/{artifact.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Model artifact deleted successfully"}
    assert _count_model_artifacts(db) == 0


def test_model_management_endpoints_not_enough_permissions(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    db.exec(delete(ModelArtifact))
    db.commit()
    artifact = _create_model_artifact(db, client_version_id="v1", is_active=False)

    list_response = client.get(
        f"{settings.API_V1_STR}/models/",
        headers=normal_user_token_headers,
    )
    active_response = client.get(
        f"{settings.API_V1_STR}/models/active",
        headers=normal_user_token_headers,
    )
    activate_response = client.post(
        f"{settings.API_V1_STR}/models/{artifact.id}/activate",
        headers=normal_user_token_headers,
    )
    delete_response = client.delete(
        f"{settings.API_V1_STR}/models/{artifact.id}",
        headers=normal_user_token_headers,
    )

    assert list_response.status_code == 403
    assert active_response.status_code == 403
    assert activate_response.status_code == 403
    assert delete_response.status_code == 403
