# Local Training Listener (Self-Hosted Compute Receiver)

This document describes the standalone listener used as the local compute receiving end for model training jobs.

- Script: `backend/util/training_listener.py`
- Health check: `GET /health`
- Job trigger: `POST /train`

The listener runs `MLEngine` locally, saves artifacts under `backend/util/artifacts/<version_id>/`, and can upload `model.joblib` + metadata to `POST /api/v1/models/upload`.

For the backend endpoints that feed data to the listener (poll for jobs, download training data, create job requests), see [training-sync-endpoints.md](training-sync-endpoints.md).

## Run the listener

From repository root:

```bash
uv run python backend/util/training_listener.py --host 127.0.0.1 --port 8081
```

Optional security and upload defaults:

```bash
export TRAINING_LISTENER_API_KEY="<shared-key>"
export BACKEND_SUPERUSER_TOKEN="<backend-superuser-jwt>"
export BACKEND_MODEL_UPLOAD_URL="http://localhost:8000/api/v1/models/upload"
uv run python backend/util/training_listener.py --port 8081
```

## Trigger a training job

`POST /train` accepts JSON with training config and upload options.

### Minimal request (local training only)

```json
{
  "training_csv_path": "backend/util/data/pacemaker_data_seed.csv",
  "upload_to_backend": false
}
```

### Full request (train + upload)

```json
{
  "training_csv_path": "backend/util/data/pacemaker_data_seed.csv",
  "artifact_version_id": "20260301_120000",
  "client_version_id": "20260301_120000",
  "source_run_id": "ado-run-1842",
  "notes": "Nightly retrain run",
  "upload_to_backend": true,
  "backend_upload_url": "http://localhost:8000/api/v1/models/upload",
  "backend_token": "<SUPERUSER_TOKEN>",
  "n_estimators": 200,
  "max_depth": 20,
  "random_state": 42,
  "n_folds": 5,
  "test_size": 0.2
}
```

If `TRAINING_LISTENER_API_KEY` is configured, include header:

- `X-Listener-Key: <shared-key>`

## Example `curl`

```bash
curl -X POST "http://127.0.0.1:8081/train" \
  -H "Content-Type: application/json" \
  -H "X-Listener-Key: <shared-key>" \
  -d '{
    "training_csv_path":"backend/util/data/pacemaker_data_seed.csv",
    "upload_to_backend":true,
    "backend_token":"<SUPERUSER_TOKEN>",
    "source_run_id":"ado-run-1842"
  }'
```

## Response shape

Successful runs return:

- `status` (`"completed"`)
- `artifact_dir`
- `model_path`
- `metrics` (OOB, CV, accuracy, report, dataset info)
- `upload_response` (present when upload succeeds)

## Failure behavior

- `401` invalid/missing `X-Listener-Key` when listener key is enabled
- `404` training CSV path not found
- `422` backend token missing while `upload_to_backend=true`
- `500` local training/evaluation failure
- `502` backend model upload failure
