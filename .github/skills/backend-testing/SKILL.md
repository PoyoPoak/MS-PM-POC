---
name: backend-testing
description: Backend testing guide for writing and maintaining pytest coverage in this repository. Use when adding or changing FastAPI routes, SQLModel CRUD behavior, telemetry ingestion, training-sync lifecycle endpoints, model-artifact upload flows, or backend scripts.
---

# Backend Testing Skill

## Goal

Ship backend changes with reliable pytest coverage that matches this repository's real architecture (auth, telemetry, training sync, model artifacts) and keeps CI at >=90% coverage.

## Use This Skill When

- Adding or changing backend API routes under backend/app/api/routes
- Changing behavior in backend/app/crud.py or backend/app/models.py
- Adding telemetry ingestion, training workflow, or model artifact logic
- Fixing flaky/failing pytest cases
- Increasing coverage for CI

## Primary References

- .github/copilot-instructions.md
- backend/tests/conftest.py
- backend/tests/api/routes/test_items.py
- backend/tests/api/routes/test_telemetry.py
- backend/tests/api/routes/test_training_sync.py
- backend/tests/api/routes/test_model_artifacts.py
- docs/training-sync-endpoints.md
- docs/pacemaker-telemetry.md

## Test Environment Baseline

1. Start required services:

```bash
docker compose up -d db mailcatcher
```

2. Ensure migrations and seed/prestart tasks ran:

```bash
cd backend && uv run bash scripts/prestart.sh && cd ..
```

3. Run tests:

```bash
cd backend && uv run bash scripts/tests-start.sh && cd ..
```

4. Verify coverage gate:

```bash
cd backend && uv run coverage report --fail-under=90 && cd ..
```

## Repository Test Layout

- backend/tests/conftest.py: shared fixtures and auth headers
- backend/tests/api/routes/: endpoint-level contract tests
- backend/tests/crud/: CRUD unit/integration tests
- backend/tests/scripts/: startup and initialization script tests
- backend/tests/test_telemetry_seed.py: telemetry seed behavior tests

## Required Test Design Rules

- Always annotate test function return types with -> None.
- Use settings.API_V1_STR for API prefixes instead of hardcoded /api/v1.
- Prefer existing fixtures from conftest.py before adding new fixtures.
- Avoid print; rely on assertions and pytest output.
- Assert both status code and response body contract.
- Cover both auth and permission boundaries on protected endpoints.

## Auth and Permission Matrix

For protected routes, cover these paths unless the endpoint contract states otherwise:

1. Superuser happy path (200-level expected)
2. Normal-user forbidden path (typically 403)
3. Unauthenticated path (typically 401)

Reuse:

- superuser_token_headers
- normal_user_token_headers

## Endpoint Category Playbooks

### CRUD-style Endpoints (items/users-like)

Minimum coverage set:

1. create success
2. read single success
3. read single not found
4. read permission denied
5. list success
6. update success
7. update not found
8. update permission denied
9. delete success
10. delete not found
11. delete permission denied

Reference pattern: backend/tests/api/routes/test_items.py

### Telemetry Ingest Endpoints

In addition to happy/permission paths, cover:

- invalid timestamp or payload shape validation (422)
- non-list body rejection when list is required
- empty batch rejection
- oversized batch rejection
- duplicate handling summary fields where applicable
- target label validation (0/1/null semantics)

Reference pattern: backend/tests/api/routes/test_telemetry.py and backend/tests/api/routes/test_telemetry_route.py

### Training Sync Endpoints

Treat these as a state-machine API, not simple CRUD. Cover:

- poll when no jobs vs pending jobs
- claim newest pending job
- cancellation of older pending jobs on claim
- conflict when an in-progress job already exists
- complete transitions and invalid transition conflicts
- maturity-window behavior for download endpoint
- predict behavior when model exists and when model is missing

Reference pattern: backend/tests/api/routes/test_training_sync.py

### Model Artifact Upload Endpoints

Cover multipart and metadata contract details:

- successful upload with valid model_file + metadata_json
- invalid JSON metadata handling
- required metadata field validation
- empty file rejection
- permission and unauthenticated behavior

Reference pattern: backend/tests/api/routes/test_model_artifacts.py

## Creating New Tests for a Backend Change

1. Locate the closest existing test module by endpoint type.
2. Mirror naming and fixture usage from that module.
3. Add the smallest set of tests that proves behavior and guards regressions.
4. If model fields changed, update related utilities in backend/tests/utils.
5. Run targeted tests first, then full backend test command.

## Useful Commands

Run one test module:

```bash
cd backend && uv run pytest tests/api/routes/test_training_sync.py -v && cd ..
```

Run one test function:

```bash
cd backend && uv run pytest tests/api/routes/test_telemetry.py::test_bulk_ingest_telemetry -v && cd ..
```

Run backend lint after test changes:

```bash
cd backend && uv run bash scripts/lint.sh && cd ..
```

## Coverage and Regression Checklist

- [ ] New/changed behavior has direct tests in backend/tests/**
- [ ] Permission and unauthenticated paths are covered for protected endpoints
- [ ] State transitions are covered for workflow endpoints (training)
- [ ] Validation failures are covered for input contracts
- [ ] Backend tests pass via scripts/tests-start.sh
- [ ] Coverage remains >=90%

## Common Pitfalls

- Writing tests against outdated template-only assumptions instead of telemetry/training contracts
- Forgetting to run prestart.sh before tests when schema changed
- Adding duplicate fixtures rather than using conftest.py fixtures
- Asserting only status codes without checking contract fields
- Ignoring permission paths for superuser-protected endpoints
