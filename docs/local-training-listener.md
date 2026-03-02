# Local Training Worker (Polling Compute Script)

The training worker is a standalone Python script that runs on your local machine (or any self-hosted compute environment). It polls the backend for pending training jobs, downloads new telemetry data, trains a model with `MLEngine`, and uploads the artifact + metrics back to the backend.

- **Script:** `backend/util/training_listener.py`
- **Auth:** Superuser JWT (`Authorization: Bearer <TOKEN>`)
- **Data cache:** `backend/util/data/local_training_data.csv`

For the backend endpoints the worker calls (poll, download, request), see [training-sync-endpoints.md](training-sync-endpoints.md). For the upload contract, see [model-upload-endpoint.md](model-upload-endpoint.md).

## How It Works

```
┌────────────────────────────┐      ┌──────────────────────────────┐
│   Local Compute (Worker)   │      │   Backend (FastAPI)          │
│                            │      │                              │
│  1. Poll for jobs ─────────┼──GET─┼→ /api/v1/training/poll       │
│     (every 5 seconds)      │      │   returns true / false       │
│                            │      │                              │
│  2. Download data ─────────┼──GET─┼→ /api/v1/training/download   │
│     newest_local_ts=<ts>   │      │   ?newest_local_ts=...       │
│                            │      │   returns telemetry rows     │
│                            │      │                              │
│  3. Append to local CSV    │      │                              │
│     Train model (MLEngine) │      │                              │
│                            │      │                              │
│  4. Upload artifact ───────┼─POST─┼→ /api/v1/models/upload       │
│                            │      │   (multipart model + meta)   │
│                            │      │                              │
│  5. Resume polling ────────┼──────┼→ back to step 1              │
└────────────────────────────┘      └──────────────────────────────┘
```

## Prerequisites

1. **Backend running** — the backend API must be reachable at the configured URL.
2. **Superuser token** — obtain a JWT from `POST /api/v1/login/access-token` using the superuser credentials in `.env` (`FIRST_SUPERUSER` / `FIRST_SUPERUSER_PASSWORD`).
3. **Python dependencies** — `uv sync --all-packages` from the repo root installs all required packages (`httpx`, `pandas`, `scikit-learn`, etc.).

## Run the Worker

From the repository root:

```bash
uv run python backend/util/training_listener.py \
  --token "<SUPERUSER_JWT>"
```

With all options:

```bash
uv run python backend/util/training_listener.py \
  --backend-url http://localhost:8000 \
  --token "<SUPERUSER_JWT>" \
  --csv backend/util/data/local_training_data.csv \
  --poll-interval 5 \
  --timeout 120 \
  --log-level info
```

### Environment Variables

Instead of CLI flags, you can set environment variables:

| Variable | CLI Flag | Default |
|---|---|---|
| `BACKEND_URL` | `--backend-url` | `http://localhost:8000` |
| `BACKEND_SUPERUSER_TOKEN` | `--token` | *(required)* |
| `LOCAL_TRAINING_CSV` | `--csv` | `backend/util/data/local_training_data.csv` |
| `POLL_INTERVAL_SECONDS` | `--poll-interval` | `5` |

Example with environment variables:

```bash
export BACKEND_SUPERUSER_TOKEN="<jwt>"
uv run python backend/util/training_listener.py
```

## CLI Reference

| Flag | Description | Default |
|---|---|---|
| `--backend-url` | Base URL of the backend API | `http://localhost:8000` |
| `--token` | Superuser JWT for backend auth | `BACKEND_SUPERUSER_TOKEN` env var |
| `--csv` | Path to local training-data CSV cache | `backend/util/data/local_training_data.csv` |
| `--poll-interval` | Seconds between poll requests | `5` |
| `--timeout` | HTTP request timeout (seconds) | `120` |
| `--log-level` | Log verbosity: debug, info, warning, error, critical | `info` |

## Data Flow Details

### Polling

The worker calls `GET /api/v1/training/poll` every `--poll-interval` seconds.

- Returns `true` → a pending training job exists; proceed to download.
- Returns `false` → sleep and poll again.

### Downloading

When a job is pending, the worker calls `GET /api/v1/training/download?newest_local_ts=<ts>` where `<ts>` is the Unix epoch of the newest row in the local CSV (or `0` on first run).

The backend applies a 7-day maturity window and returns only rows with `timestamp > local_ts AND timestamp <= server_max - 7d`.

Downloaded rows are field-mapped from JSON snake_case to the CSV's PascalCase column names and appended to the local cache file.

### Training

If the local CSV has at least 10 data rows, `MLEngine` trains a Random Forest model:

- `n_estimators=200`, `max_depth=20`
- Evaluates OOB score, K-Fold CV, test accuracy, classification report
- Saves artifact to `backend/util/artifacts/<version_id>/`

### Uploading

The worker `POST`s to `/api/v1/models/upload` with:

- `model_file`: the `model.joblib` binary
- `metadata_json`: algorithm, hyperparameters, metrics, dataset_info

## Error Handling

The worker catches and logs all errors without crashing:

| Error | Behavior |
|---|---|
| HTTP 401/403 | Logged; likely expired or invalid token |
| HTTP 4xx/5xx | Logged with status code and response body |
| Connection error | Logged; retries on next poll cycle |
| Training failure | Logged; resumes polling |

The worker always returns to polling after an error, making it resilient for long-running unattended operation.

## Stopping the Worker

Press `Ctrl+C` to stop the polling loop.
