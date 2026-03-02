# Training Sync Endpoints

Backend routes that let the local compute server (or any authorized client) check for pending training jobs, download mature telemetry data, manage job lifecycle (claim/complete), and create new job requests.

- **Route module:** [backend/app/api/routes/training.py](../backend/app/api/routes/training.py)
- **Table model:** `TrainingJobRequest` in [backend/app/models.py](../backend/app/models.py)
- **Auth:** all endpoints require a **superuser JWT** (`Authorization: Bearer <TOKEN>`)

Related docs:

- [local-training-listener.md](local-training-listener.md) — the listener that consumes these endpoints
- [training_loop.md](training_loop.md) — delayed-label lifecycle and maturity rules
- [model-upload-endpoint.md](model-upload-endpoint.md) — how the listener uploads artifacts after training

---

## How to Get a Superuser Token

```bash
curl -X POST "http://localhost:8000/api/v1/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=<FIRST_SUPERUSER_EMAIL>" \
  -d "password=<FIRST_SUPERUSER_PASSWORD>"
```

Use the `access_token` value from the JSON response:

```text
Authorization: Bearer <TOKEN>
```

Superuser credentials are configured in the repo-root `.env` file (`FIRST_SUPERUSER` / `FIRST_SUPERUSER_PASSWORD`).

---

## Endpoint Reference

### 1. `GET /api/v1/training/poll`

Check whether there is at least one pending training-job request.

#### Request

| Part | Detail |
|---|---|
| **Method** | `GET` |
| **Path** | `/api/v1/training/poll` |
| **Auth** | Bearer superuser token |
| **Body** | _none_ |

#### Response

Returns a bare JSON boolean.

| Scenario | Response body |
|---|---|
| One or more `is_pending=true` rows exist | `true` |
| No pending rows | `false` |

#### Example

```bash
curl -s "http://localhost:8000/api/v1/training/poll" \
  -H "Authorization: Bearer <TOKEN>"
# → true
```

---

### 2. `GET /api/v1/training/download`

Fetch telemetry rows that the local compute has not yet seen **and** that satisfy the 7-day maturity window. This is the primary data-transfer mechanism for incremental training.

#### Request

| Part | Detail |
|---|---|
| **Method** | `GET` |
| **Path** | `/api/v1/training/download` |
| **Auth** | Bearer superuser token |
| **Query param** | `newest_local_ts` — **required**, Unix epoch seconds (int) of the newest `timestamp` the local compute already has |

#### Boundary Rules

```
local_dt    = datetime(newest_local_ts, UTC)
server_max  = MAX(pacemaker_telemetry.timestamp)
cutoff      = server_max − 7 days
result set  = rows WHERE  timestamp > local_dt  AND  timestamp <= cutoff
```

The 7-day gap ensures only rows with matured label windows are sent for training. See [training_loop.md → §5 "What matured data means"](training_loop.md) for rationale.

#### Response Schema — `TrainingDataDownloadResult`

```json
{
  "rows": [
    {
      "id": "uuid",
      "patient_id": 42,
      "timestamp": "2026-02-19T00:00:00Z",
      "lead_impedance_ohms": 510.0,
      "capture_threshold_v": 1.1,
      "r_wave_sensing_mv": 8.7,
      "battery_voltage_v": 2.9,
      "target_fail_next_7d": 0,
      "lead_impedance_ohms_rolling_mean_3d": 505.0,
      "lead_impedance_ohms_rolling_mean_7d": 508.0,
      "capture_threshold_v_rolling_mean_3d": 1.05,
      "capture_threshold_v_rolling_mean_7d": 1.08,
      "lead_impedance_ohms_delta_per_day_3d": 0.5,
      "lead_impedance_ohms_delta_per_day_7d": 0.3,
      "capture_threshold_v_delta_per_day_3d": 0.02,
      "capture_threshold_v_delta_per_day_7d": 0.01
    }
  ],
  "count": 1,
  "server_newest_ts": 1740700800,
  "maturity_cutoff_ts": 1740096000
}
```

| Field | Type | Description |
|---|---|---|
| `rows` | `list[PacemakerTelemetryPublic]` | Telemetry rows matching the window |
| `count` | `int` | Length of `rows` |
| `server_newest_ts` | `int \| null` | Epoch seconds of `MAX(timestamp)` on server; `null` when table is empty |
| `maturity_cutoff_ts` | `int \| null` | Epoch seconds of the maturity boundary (`server_newest_ts − 7d`); `null` when table is empty |

#### Edge Cases

| Condition | Behavior |
|---|---|
| Telemetry table is empty | `rows=[], count=0, server_newest_ts=null, maturity_cutoff_ts=null` |
| No qualifying rows (cutoff ≤ local_dt) | `rows=[], count=0` — timestamps are still populated |
| `newest_local_ts=0` (first sync) | All rows up to the maturity cutoff are returned |

#### Example

```bash
# First sync — local compute has no data yet
curl -s "http://localhost:8000/api/v1/training/download?newest_local_ts=0" \
  -H "Authorization: Bearer <TOKEN>" | python -m json.tool

# Incremental sync — only rows newer than local max
curl -s "http://localhost:8000/api/v1/training/download?newest_local_ts=1740096000" \
  -H "Authorization: Bearer <TOKEN>" | python -m json.tool
```

---

### 3. `POST /api/v1/training/request`

Create a new pending training-job request. This is the backend action behind the frontend "Request Training" button. The local compute server polls for these via `GET /training/poll`.

#### Request

| Part | Detail |
|---|---|
| **Method** | `POST` |
| **Path** | `/api/v1/training/request` |
| **Auth** | Bearer superuser token |
| **Body** | _none_ |

#### Response Schema — `TrainingJobRequestPublic`

```json
{
  "id": "a1b2c3d4-...",
  "created_at": "2026-03-01T12:00:00Z",
  "is_pending": true,
  "requested_by": "user-uuid-..."
}
```

#### Example

```bash
curl -s -X POST "http://localhost:8000/api/v1/training/request" \
  -H "Authorization: Bearer <TOKEN>" | python -m json.tool
```

---

### 4. `POST /api/v1/training/claim`

Atomically claim the **newest** pending training-job request. Any older pending jobs are cancelled. Only one job may be in-progress at a time.

#### Request

| Part | Detail |
|---|---|
| **Method** | `POST` |
| **Path** | `/api/v1/training/claim` |
| **Auth** | Bearer superuser token |
| **Body** | _none_ |

#### Behaviour

1. **In-progress guard** — if any job is already claimed but not yet completed or cancelled, returns `409`.
2. Fetches all pending jobs newest-first (`ORDER BY created_at DESC`).
3. Claims the first (newest) — sets `is_pending = false`.
4. Cancels all older pending jobs — sets `is_pending = false`, `cancelled_at = now()`.
5. Returns the claimed job.

#### Response Schema — `TrainingJobRequestPublic`

```json
{
  "id": "a1b2c3d4-...",
  "created_at": "2026-03-01T12:00:00Z",
  "is_pending": false,
  "requested_by": "user-uuid-...",
  "consumed_at": null,
  "cancelled_at": null
}
```

#### Error Responses

| Status | Condition |
|---|---|
| `404 Not Found` | No pending training jobs |
| `409 Conflict` | A training job is already in progress (claimed, not completed/cancelled) |

#### Example

```bash
# Claim the newest pending job
curl -s -X POST "http://localhost:8000/api/v1/training/claim" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

---

### 5. `POST /api/v1/training/{job_id}/complete`

Mark a claimed training-job request as complete. Sets `consumed_at` to now-UTC.

#### Request

| Part | Detail |
|---|---|
| **Method** | `POST` |
| **Path** | `/api/v1/training/{job_id}/complete` |
| **Auth** | Bearer superuser token |
| **Path param** | `job_id` — UUID of the claimed job |
| **Body** | _none_ |

#### Response Schema — `TrainingJobRequestPublic`

```json
{
  "id": "a1b2c3d4-...",
  "created_at": "2026-03-01T12:00:00Z",
  "is_pending": false,
  "requested_by": "user-uuid-...",
  "consumed_at": "2026-03-01T12:05:00Z",
  "cancelled_at": null
}
```

#### Error Responses

| Status | Condition |
|---|---|
| `404 Not Found` | Job ID does not exist |
| `409 Conflict` | Job has not been claimed yet (still pending) |
| `409 Conflict` | Job has already been completed |
| `409 Conflict` | Job was cancelled |

#### Example

```bash
# Complete a claimed job (use the job ID from the claim response)
curl -s -X POST "http://localhost:8000/api/v1/training/a1b2c3d4-.../complete" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

---

## Job Lifecycle

A training job transitions through these states:

```
                              ┌──────────┐
  POST /request ─────────────→│ pending  │
                              └────┬─────┘
                                   │
                        POST /claim│
                     ┌─────────────┼─────────────┐
                     │             │              │
                     ▼             ▼              │
              ┌───────────┐ ┌───────────┐         │
              │ cancelled │ │  claimed  │         │
              │           │ │(in-prog.) │         │
              └───────────┘ └─────┬─────┘         │
                                  │               │
                   POST /{id}/    │               │
                   complete       │               │
                                  ▼               │
                           ┌───────────┐          │
                           │ completed │          │
                           └───────────┘          │
```

**Rules:**
- Only one job may be in the **claimed** state at a time.
- Claiming always picks the **newest** pending job.
- All older pending jobs are automatically **cancelled**.
- The listener must complete (or the backend must receive a complete call for) the current job before another can be claimed.

---

## Database Table: `training_job_request`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key, auto-generated |
| `created_at` | `timestamptz` | Auto-set on creation |
| `is_pending` | `boolean` | `true` until claimed or cancelled; indexed for fast polling |
| `requested_by` | UUID (FK → `user.id`) | Nullable, ON DELETE SET NULL |
| `consumed_at` | `timestamptz` | Set when the local compute marks the job complete |
| `cancelled_at` | `timestamptz` | Set when the job is cancelled (e.g., superseded by a newer job) |

### State Matrix

| State | `is_pending` | `consumed_at` | `cancelled_at` |
|---|---|---|---|
| **Pending** | `true` | `null` | `null` |
| **Claimed** (in-progress) | `false` | `null` | `null` |
| **Completed** | `false` | set | `null` |
| **Cancelled** | `false` | `null` | set |

---

## Manual Testing

### Prerequisites

1. Backend + PostgreSQL running:

   ```bash
   docker compose up -d db mailcatcher
   cd backend && uv run bash scripts/prestart.sh && cd ..
   # In another terminal:
   cd backend && uv run fastapi dev app/main.py
   ```

2. Obtain a superuser token (see [above](#how-to-get-a-superuser-token)).

3. Seed some telemetry data so the download has rows to return:

   ```bash
   # Generate data + replay a few batches
   uv run python backend/util/generate_data.py
   uv run python backend/util/replay_telemetry.py \
     --url http://localhost:8000/api/v1/telemetry/ingest \
     --token "<TOKEN>" \
     --batches 20
   ```

### Walk-Through

```bash
TOKEN="<paste-your-superuser-token>"

# Step 1 — Poll: no jobs yet
curl -s "http://localhost:8000/api/v1/training/poll" \
  -H "Authorization: Bearer $TOKEN"
# → false

# Step 2 — Create a training job request
curl -s -X POST "http://localhost:8000/api/v1/training/request" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

# Step 3 — Poll: should now be true
curl -s "http://localhost:8000/api/v1/training/poll" \
  -H "Authorization: Bearer $TOKEN"
# → true

# Step 4 — Claim the newest pending job
curl -s -X POST "http://localhost:8000/api/v1/training/claim" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
# → returns the claimed job with is_pending=false, note the "id" field

# Step 5 — Download mature telemetry data (first sync)
curl -s "http://localhost:8000/api/v1/training/download?newest_local_ts=0" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

# Step 6 — (train and upload model locally)

# Step 7 — Mark the job as complete (use the id from step 4)
JOB_ID="<paste-job-id-from-step-4>"
curl -s -X POST "http://localhost:8000/api/v1/training/$JOB_ID/complete" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
# → returns the job with consumed_at set
```

### Auth Error Cases

```bash
# No token → 401
curl -s "http://localhost:8000/api/v1/training/poll"

# Normal user token → 403
curl -s "http://localhost:8000/api/v1/training/poll" \
  -H "Authorization: Bearer <NORMAL_USER_TOKEN>"

# Missing query param → 422
curl -s "http://localhost:8000/api/v1/training/download" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Integrating with the Local Training Listener

The [training_listener.py](../backend/util/training_listener.py) script is the self-hosted compute server that runs `MLEngine` locally. These sync endpoints are designed to be called **from** the listener (or a wrapper script around it) so that training jobs are driven by the backend's job queue.

### Recommended Integration Flow

```
┌────────────────────────────┐      ┌──────────────────────────────┐
│   Local Compute (Listener) │      │   Backend (FastAPI)          │
│                            │      │                              │
│  1. Poll for jobs ─────────┼──GET─┼→ /api/v1/training/poll       │
│     (on a timer / cron)    │      │   returns true/false         │
│                            │      │                              │
│  2. Claim newest job ──────┼─POST─┼→ /api/v1/training/claim      │
│     (cancels older ones)   │      │   returns claimed job or 409 │
│                            │      │                              │
│  3. Download data ─────────┼──GET─┼→ /api/v1/training/download   │
│     newest_local_ts=<ts>   │      │   returns telemetry rows     │
│                            │      │                              │
│  4. Train model locally    │      │                              │
│     (MLEngine)             │      │                              │
│                            │      │                              │
│  5. Upload artifact ───────┼─POST─┼→ /api/v1/models/upload       │
│                            │      │   (multipart model + meta)   │
│                            │      │                              │
│  6. Mark complete ─────────┼─POST─┼→ /api/v1/training/{id}/      │
│                            │      │   complete                   │
└────────────────────────────┘      └──────────────────────────────┘
```

### Step-by-Step

1. **Poll on a schedule** — add a loop or cron job that calls `GET /api/v1/training/poll` every _N_ minutes. When it returns `true`, proceed to step 2.

2. **Claim the newest job** — call `POST /api/v1/training/claim`. This atomically claims the newest pending job and cancels any older pending ones. If `409` is returned, a job is already in-progress — wait and retry later. If `404`, no pending jobs exist.

3. **Download training data** — call `GET /api/v1/training/download?newest_local_ts=<ts>` where `<ts>` is the Unix epoch seconds of the newest row in your local data cache. On first run, use `0`. Save the returned rows to your local data store (CSV, Parquet, or DataFrame).

4. **Train** — invoke `MLEngine.train()` with the updated local dataset.

5. **Upload** — post the resulting `model.joblib` + metadata to `POST /api/v1/models/upload` (see [model-upload-endpoint.md](model-upload-endpoint.md)).

6. **Mark complete** — call `POST /api/v1/training/{job_id}/complete` with the job ID returned from the claim step. This sets `consumed_at` and frees the system for a new claim.

### Example: Minimal Python Polling Loop

This snippet can be added to `training_listener.py` or run as a standalone wrapper:

```python
import time
import httpx

BACKEND_BASE = "http://localhost:8000/api/v1"
TOKEN = "<SUPERUSER_TOKEN>"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
POLL_INTERVAL_SECONDS = 300  # 5 minutes
local_newest_ts = 0  # start from epoch 0

while True:
    # 1. Poll
    poll = httpx.get(f"{BACKEND_BASE}/training/poll", headers=HEADERS)
    if poll.json() is True:
        # 2. Claim the newest pending job
        claim = httpx.post(f"{BACKEND_BASE}/training/claim", headers=HEADERS)
        if claim.status_code == 200:
            job = claim.json()
            job_id = job["id"]

            # 3. Download
            resp = httpx.get(
                f"{BACKEND_BASE}/training/download",
                headers=HEADERS,
                params={"newest_local_ts": local_newest_ts},
            )
            data = resp.json()
            if data["count"] > 0:
                rows = data["rows"]
                # → append rows to local CSV or Parquet
                # → update local_newest_ts to max timestamp in rows
                local_newest_ts = data["maturity_cutoff_ts"]

                # 4. Train (invoke MLEngine)
                # 5. Upload artifact to /api/v1/models/upload

            # 6. Mark job complete
            httpx.post(
                f"{BACKEND_BASE}/training/{job_id}/complete",
                headers=HEADERS,
            )
        # 409 = job already in progress, 404 = no pending — just wait

    time.sleep(POLL_INTERVAL_SECONDS)
```

### Environment Variables for the Listener

| Variable | Purpose |
|---|---|
| `BACKEND_SUPERUSER_TOKEN` | JWT used by the listener to auth against the backend |
| `BACKEND_MODEL_UPLOAD_URL` | Override for the model upload endpoint (default `http://localhost:8000/api/v1/models/upload`) |
| `TRAINING_LISTENER_API_KEY` | Optional shared key protecting the listener's own `POST /train` |

---

## Error Responses

All three endpoints share the same auth error behavior:

| Status | Condition |
|---|---|
| `401 Unauthorized` | Missing or invalid token |
| `403 Forbidden` | Token belongs to a non-superuser account |
| `422 Unprocessable Entity` | Missing required query parameter (`newest_local_ts` on download) |
