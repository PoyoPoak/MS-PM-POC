# Model Upload Endpoint and PostgreSQL BYTEA Storage

This document defines how trained model artifacts and evaluation metrics are uploaded from local training compute to the backend API and persisted in PostgreSQL.

## Endpoint Summary

- **Method:** `POST`
- **Path:** `/api/v1/models/upload`
- **Auth:** superuser token required
- **Content-Type:** `multipart/form-data`
- **Purpose:** persist a trained model artifact (`model_file`) and model run metadata/metrics (`metadata_json`) as one atomic backend write

## How to Get a Superuser Token

The upload route requires a bearer token for a superuser account.

1. Use the superuser credentials configured in the repo root `.env`:
   - `FIRST_SUPERUSER`
   - `FIRST_SUPERUSER_PASSWORD`
2. Request a token from the login endpoint:

```bash
curl -X POST "http://localhost:8000/api/v1/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=<FIRST_SUPERUSER_EMAIL>" \
  -d "password=<FIRST_SUPERUSER_PASSWORD>"
```

3. Copy `access_token` from the JSON response and use it as:

```text
Authorization: Bearer <SUPERUSER_TOKEN>
```

Example response:

```json
{
  "access_token": "<JWT_TOKEN>",
  "token_type": "bearer"
}
```

## Request Contract

The endpoint expects exactly two multipart fields:

1. `model_file` (file)
   - Binary model artifact (for example `.joblib`)
   - Must be non-empty
   - Max size currently enforced in backend route: 64 MB

2. `metadata_json` (text)
   - JSON string with training run metadata and evaluation metrics
   - Validated against backend schema

### `metadata_json` schema

- `client_version_id` (optional string, max 255)
- `source_run_id` (optional string, max 255)
- `trained_at_utc` (optional datetime)
- `algorithm` (required string, max 255)
- `hyperparameters` (required object)
- `metrics` (required object)
- `dataset_info` (required object)
- `notes` (optional string, max 2000)

## Example Request Body

### Multipart form fields

- `model_file`: `rf_model.joblib` (binary)
- `metadata_json`:

```json
{
  "client_version_id": "20260301_120000",
  "source_run_id": "ado-run-1842",
  "trained_at_utc": "2026-03-01T12:00:00Z",
  "algorithm": "RandomForestClassifier",
  "hyperparameters": {
    "n_estimators": 200,
    "max_depth": 20,
    "random_state": 42
  },
  "metrics": {
    "oob_score": 0.9312,
    "kfold_cv_mean": 0.9244,
    "kfold_cv_std": 0.0081,
    "test_accuracy": 0.9287,
    "classification_report": {
      "0": {
        "precision": 0.95,
        "recall": 0.96,
        "f1-score": 0.95,
        "support": 1820
      },
      "1": {
        "precision": 0.81,
        "recall": 0.76,
        "f1-score": 0.78,
        "support": 280
      }
    }
  },
  "dataset_info": {
    "train_rows": 8400,
    "test_rows": 2100,
    "n_features": 12,
    "positive_rate_train": 0.132
  },
  "notes": "Nightly retrain run"
}
```

### Example `curl`

```bash
curl -X POST "http://localhost:8000/api/v1/models/upload" \
  -H "Authorization: Bearer <SUPERUSER_TOKEN>" \
  -F "model_file=@backend/util/artifacts/20260301_210304/model.joblib;type=application/octet-stream" \
  -F 'metadata_json={"client_version_id":"20260301_210304","source_run_id":"ado-run-1842","trained_at_utc":"2026-03-01T12:00:00Z","algorithm":"RandomForestClassifier","hyperparameters":{"n_estimators":200,"max_depth":20,"random_state":42},"metrics":{"oob_score":0.9312,"kfold_cv_mean":0.9244,"kfold_cv_std":0.0081,"test_accuracy":0.9287},"dataset_info":{"train_rows":8400,"test_rows":2100,"n_features":12,"positive_rate_train":0.132},"notes":"Nightly retrain run"}'
```

## Response Contract

Successful response returns metadata summary and does not return the binary model payload:

```json
{
  "id": "5dd3e277-5b86-4423-8cc3-0e476fb0bf0c",
  "created_at": "2026-03-01T12:03:21.218949Z",
  "client_version_id": "20260301_120000",
  "source_run_id": "ado-run-1842",
  "algorithm": "RandomForestClassifier",
  "model_size_bytes": 24518733,
  "model_sha256": "e5f9b0b0f594bcf8f5939e89995c8239f399f745f4efd9e7a2f4d0f5ca6ecf07",
  "content_type": "application/octet-stream"
}
```

## Error Behavior

- `401` unauthenticated
- `403` authenticated user lacks superuser privileges
- `400` empty `model_file`
- `413` `model_file` exceeds route max upload size
- `422` invalid `metadata_json` or schema validation failure

## Database Persistence Details

Models are persisted to `model_artifact` table with:

- `id` (UUID, server-generated primary key)
- `created_at`
- optional traceability fields (`client_version_id`, `source_run_id`, `trained_at_utc`)
- `algorithm`
- `hyperparameters` (`JSON`)
- `metrics` (`JSON`)
- `dataset_info` (`JSON`)
- `notes`
- `content_type`
- `model_size_bytes`
- `model_sha256`
- `model_blob` (`BYTEA`/`LargeBinary`)

## Operational Notes

- Average artifact size target (~20-30 MB) is supported by current route limits.
- For larger future models, revisit API/proxy request-size limits and consider object storage offload with DB metadata pointers.
- The route is designed for local self-hosted training agent handoff and supports end-to-end auditability through run IDs and hash metadata.
