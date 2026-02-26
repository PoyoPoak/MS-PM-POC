
# MSOA — MLOps for Pacemaker Telemetry (Interview Project)

This repository is an interview-focused demonstration of a simple end-to-end MLOps workflow built on FastAPI full-stack template. It contains a backend (FastAPI + SQLModel), a React + TypeScript frontend, data generation and ML training utilities, and Docker Compose orchestration for local development.

**Purpose**: Showcase skills in data engineering, AI/ML, CI/CD, and automation by generating synthetic pacemaker telemetry, training a predictive model (random forest) to detect imminent device failure, and demonstrating an automated pipeline to retrain and publish model updates.

**Disclaimer**: This project uses the FastAPI full-stack template as its starting point. Template files are intentionally present; the repository is a work-in-progress and not a final product.

## Highlights
- Synthetic telemetry generator for pacemaker signals
- Simple ML training pipeline (Random Forest) and model persistence
- FastAPI backend with endpoints and migration scripts
- React + TypeScript frontend dashboard (Vite + Bun)
- Docker Compose for local full-stack development

## Tech stack
- Backend: Python 3.10+, FastAPI, SQLModel, Alembic
- Frontend: React 19, TypeScript, Vite, Tailwind CSS
- Tooling: `uv` (Python workspace), `bun` (frontend), Docker Compose, Playwright (E2E)

## Quick start (local)

Prerequisites

- Docker & Docker Compose
- `uv` available for Python workspace management
- `bun` for frontend package management

Start required dev services (database + mailcatcher):

```bash
docker compose up -d db mailcatcher
```

Backend setup

```bash
# From repo root
uv sync --all-packages
cd backend
uv run bash scripts/prestart.sh   # runs migrations + seeds as needed
uv run bash scripts/tests-start.sh   # runs backend tests (requires DB)
```

Frontend setup

```bash
bun install
cd frontend
bun run dev   # or use your preferred bun/vite dev command
```

Regenerate frontend OpenAPI client (when backend API/models change)

```bash
bash ./scripts/generate-client.sh
```

## Tests & CI

- Backend tests: `cd backend && uv run bash scripts/tests-start.sh` (requires DB + prestart)
- Playwright E2E: bring up backend services and run `bunx playwright test` from `frontend/`.
- Coverage requirement (for CI): backend coverage must remain >= 90%.

## Important repo notes

- Do NOT manually edit generated files under `frontend/src/client/` or `frontend/src/components/ui/`.
- Use `uv` for Python package commands and `bun` for JavaScript/TypeScript per repository conventions.
- Follow scripts in `backend/scripts/` for consistent local setup.

## Where to look next
- Backend entrypoint: [backend/app/main.py](backend/app/main.py#L1)
- Models and CRUD: [backend/app/models.py](backend/app/models.py#L1) and [backend/app/crud.py](backend/app/crud.py#L1)
- Data generation helper: [util/generate_data.py](util/generate_data.py#L1)
- Client generation script: [scripts/generate-client.sh](scripts/generate-client.sh#L1)
