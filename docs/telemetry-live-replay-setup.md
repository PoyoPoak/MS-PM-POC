# Local telemetry live replay

This guide shows how to run the live telemetry replay script against a local backend.

## Prerequisites

- Docker services are up (for example with `docker compose watch` or `docker compose up`).
- Dependencies are installed from repo root:
  - `uv sync --all-packages`
  - `bun install`

## 1) Initialize backend data (required when preseeding is off)

```bash
docker compose exec backend bash -lc "python app/backend_pre_start.py && alembic upgrade head && python app/initial_data.py"
```

This runs DB readiness checks, migrations, and creates the first superuser.

## 2) Get an access token

```bash
curl -s -X POST http://localhost:8000/api/v1/login/access-token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changethis"
```

Copy the `access_token` value from the JSON response.

## 3) Run telemetry replay

### Git Bash

```bash
export TELEMETRY_INGEST_TOKEN="<paste_access_token_here>"
uv run python backend/util/replay_telemetry.py \
  --endpoint-url http://localhost:8000/api/v1/telemetry/ingest \
  --interval-ms 1000 \
  --verbose
```

### PowerShell

```powershell
$env:TELEMETRY_INGEST_TOKEN="<paste_access_token_here>"
uv run python backend\util\replay_telemetry.py --endpoint-url http://localhost:8000/api/v1/telemetry/ingest --interval-ms 1000 --verbose
```

## Optional: dry run first

```bash
uv run python backend/util/replay_telemetry.py --dry-run --interval-ms 0 --verbose
```

Dry run validates CSV loading and batching without POSTing to the backend.
