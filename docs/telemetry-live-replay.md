# Telemetry Live Replay: End-to-End Data Ingestion Flow

This document explains the full ingestion path in this repository:

1. synthetic pacemaker telemetry is generated,
2. your local machine replays that data as if 1000 pacemakers are reporting,
3. the backend validates and stores those records in PostgreSQL.

It complements setup-oriented steps in [telemetry-live-replay-setup.md](telemetry-live-replay-setup.md).

## 1) Architecture at a glance

- **Data generator**: [backend/util/generate_data.py](../backend/util/generate_data.py)
- **Replay client**: [backend/util/replay_telemetry.py](../backend/util/replay_telemetry.py)
- **Ingest endpoint**: [backend/app/api/routes/telemetry.py](../backend/app/api/routes/telemetry.py)
- **Ingest schema + table model**: [backend/app/models.py](../backend/app/models.py)
- **Storage table**: `pacemaker_telemetry` in PostgreSQL

## 2) Step A — Generate synthetic telemetry data

Use [backend/util/generate_data.py](../backend/util/generate_data.py) to produce a CSV.

- Default simulation is **1000 patients** (`num_patients=1000`).
- Rows are ordered by timestamp, then patient, so each telemetry interval contains all active devices.
- The generator writes to `backend/util/data/pacemaker_data.csv` by default.

Run from repository root:

```bash
uv run python backend/util/generate_data.py
```

Output columns include the required ingest fields:

- `Patient_ID`
- `Timestamp` (Unix seconds)
- `Lead_Impedance_Ohms`
- `Capture_Threshold_V`
- `R_Wave_Sensing_mV`
- `Battery_Voltage_V`

Plus optional labels/engineered features used by training.

## 3) Step B — Replay from local machine as live device traffic

Your local machine acts as a telemetry source by reading the generated CSV and sending **daily batches** to the backend.

Replay script: [backend/util/replay_telemetry.py](../backend/util/replay_telemetry.py)

What it does:

1. Loads CSV (`backend/util/data/pacemaker_data.csv` by default).
2. Normalizes column names from generator format (for example `Patient_ID` -> `patient_id`).
3. Validates required fields.
4. Sorts by `timestamp`, `patient_id`.
5. Groups rows by UTC day.
6. Sends each day as one or more POST requests to `/api/v1/telemetry/ingest`.
   - Request size is capped (`--max-request-rows`, default `2000`, matching API limit).
7. Waits between requests (`--interval-ms`) to simulate ongoing arrival.

Example (Git Bash):

```bash
export TELEMETRY_INGEST_TOKEN="<access_token>"
uv run python backend/util/replay_telemetry.py \
  --endpoint-url http://localhost:8000/api/v1/telemetry/ingest \
  --interval-ms 1000 \
  --verbose
```

Example (PowerShell):

```powershell
$env:TELEMETRY_INGEST_TOKEN="<access_token>"
uv run python backend\util\replay_telemetry.py --endpoint-url http://localhost:8000/api/v1/telemetry/ingest --interval-ms 1000 --verbose
```

## 4) Step C — Backend ingest endpoint behavior

Endpoint: `POST /api/v1/telemetry/ingest`

Implementation: [backend/app/api/routes/telemetry.py](../backend/app/api/routes/telemetry.py)

### Auth and payload limits

- Superuser auth is required (Bearer token).
- Request body is an array of telemetry rows.
- Minimum rows per request: `1`
- Maximum rows per request: `2000`

### Required per-row fields

- `patient_id` (integer, >= 0)
- `timestamp` (Unix seconds, UTC)
- `lead_impedance_ohms` (float)
- `capture_threshold_v` (float)
- `r_wave_sensing_mv` (float)
- `battery_voltage_v` (float)

Optional fields (when available) are also accepted and persisted, including:

- `target_fail_next_7d`
- rolling means
- delta-per-day engineered features

### Duplicate handling

The route removes duplicates in two stages:

1. **Within request payload**: duplicate `(patient_id, timestamp)` pairs in the same POST are counted and dropped.
2. **Against database**: existing `(patient_id, timestamp)` pairs already stored are looked up and skipped.

The API response includes:

- `received_count`
- `inserted_count`
- `duplicate_count`
- `duplicate_in_payload_count`
- `duplicate_existing_count`

## 5) Step D — Database persistence details

Model: `PacemakerTelemetry` in [backend/app/models.py](../backend/app/models.py)

- Table name: `pacemaker_telemetry`
- Each inserted row gets:
  - `id` (UUID primary key)
  - `created_at` (UTC timestamp)
  - telemetry fields from payload

Insert path in [backend/app/api/routes/telemetry.py](../backend/app/api/routes/telemetry.py):

- Request rows are converted to SQLModel `PacemakerTelemetry` objects.
- Backend runs `session.add_all(records_to_insert)`.
- Backend commits with `session.commit()`.

Result: valid, non-duplicate rows are durably stored in PostgreSQL and become available for downstream prediction/training workflows.

## 6) Practical local workflow (recommended)

1. Start backend + DB containers.
2. Initialize backend data and superuser.
3. Generate or refresh telemetry CSV.
4. Acquire superuser token.
5. Run replay script (optionally `--dry-run` first).
6. Verify ingest response counts and backend logs.

For command-by-command setup, use [telemetry-live-replay-setup.md](telemetry-live-replay-setup.md).

## 7) Troubleshooting quick checks

- **401/403 on ingest**: token missing/expired or not superuser.
- **422 validation errors**: CSV missing required fields or wrong types.
- **High duplicate counts**: replaying the same day/range again is expected to skip existing pairs.
- **No data inserted**: confirm endpoint URL and backend container are reachable.
