---
name: create-endpoint
description: Full-stack endpoint implementation guide for this repository. Use when adding or changing backend routes, SQLModel schemas, migrations, API contracts, generated frontend client usage, and related docs for telemetry, training, model artifacts, or standard CRUD resources.
---

# Create Endpoint Skill

## Goal

Implement endpoint changes as a complete vertical slice for this codebase: model/schema, route logic, tests, migration/client sync, and documentation updates.

## Use This Skill When

- Adding a new route under backend/app/api/routes
- Extending an existing endpoint contract
- Introducing new SQLModel API schemas or table models
- Building telemetry, training-sync, or model-artifact APIs
- Adding full-stack features that depend on backend OpenAPI changes

## Primary References

- .github/copilot-instructions.md
- backend/app/api/main.py
- backend/app/api/deps.py
- backend/app/models.py
- backend/app/api/routes/items.py
- backend/app/api/routes/telemetry.py
- backend/app/api/routes/training.py
- backend/app/api/routes/model_artifacts.py
- docs/project.md
- docs/pacemaker-telemetry.md
- docs/training-sync-endpoints.md

## Core Conventions

- Route handlers in this codebase are synchronous: use def, not async def, unless an existing module in the same area clearly uses async.
- All API routes are under /api/v1 via backend/app/api/main.py.
- Use shared dependencies from backend/app/api/deps.py for DB and auth.
- Protect operational endpoints with superuser authorization when they affect data ingestion, training orchestration, or model management.
- Never edit generated frontend files directly:
  - frontend/src/client/**
  - frontend/src/routeTree.gen.ts

## Implementation Workflow

### 1. Classify the Endpoint Type

Pick the closest existing pattern first:

- CRUD resource: items/users pattern
- Telemetry ingest: telemetry route pattern
- Training workflow/state transitions: training route pattern
- Artifact upload/download metadata: model_artifacts route pattern

### 2. Define or Update Schemas in backend/app/models.py

Use existing schema style and naming conventions:

- Request models for input payloads
- Public response models for API output
- Public list wrappers when returning paginated/list results
- Table models only when persistence changes are required

If persistence schema changes, immediately plan a migration using the database-migration skill.

### 3. Implement Route Logic

- Add/modify route module under backend/app/api/routes.
- Reuse dependency aliases (SessionDep, CurrentUser, etc.) from deps.py.
- Enforce ownership/permission checks where applicable.
- Return explicit error messages and HTTP codes matching nearby modules.

### 4. Register Router

Update backend/app/api/main.py to include the router if it is new.

### 5. Add or Update Tests Before Finalizing

Create or update tests in backend/tests/api/routes following the nearest existing module.

Minimum matrix for protected endpoints:

1. success path
2. normal user forbidden path (if superuser-only)
3. unauthenticated path
4. input validation errors
5. state/conflict errors for workflow endpoints

For workflow APIs (training claim/complete/poll/download/predict), test lifecycle transitions and conflict handling, not only CRUD semantics.

### 6. Run Backend Verification

```bash
docker compose up -d db mailcatcher
cd backend && uv run bash scripts/prestart.sh && cd ..
cd backend && uv run bash scripts/tests-start.sh && cd ..
cd backend && uv run coverage report --fail-under=90 && cd ..
cd backend && uv run bash scripts/lint.sh && cd ..
```

### 7. OpenAPI Client Synchronization Barrier

If any backend API/model contract changed, regenerate the frontend client:

```bash
bash ./scripts/generate-client.sh
```

Then fix any TypeScript fallout in frontend/src.

### 8. Frontend Integration (When Requested)

If the user asks for full-stack delivery, wire new client calls from frontend/src using existing hooks/query patterns.

Do not edit generated client code manually; consume generated service/types instead.

### 9. Documentation Sync

Apply the documentation-governance rules:

- Update docs/project.md for feature-level behavior changes.
- Update docs/pacemaker-telemetry.md for telemetry schema/contract changes.
- Update docs/training-sync-endpoints.md for training endpoint contract changes.
- Update docs/model-upload-endpoint.md for artifact upload contract changes.
- Use docs/development.md and docs/deployment.md as baseline operational references when relevant; do not duplicate long prose into skill files.

If no doc update is needed, explicitly state why.

## Endpoint Checklist

- [ ] Endpoint type mapped to an existing module pattern
- [ ] Models/schemas updated in backend/app/models.py as needed
- [ ] Router implemented/updated in backend/app/api/routes
- [ ] Router included in backend/app/api/main.py (if new)
- [ ] Auth/permission checks implemented and tested
- [ ] Backend tests updated and passing
- [ ] Coverage remains >=90%
- [ ] Lint passes
- [ ] scripts/generate-client.sh run after API/schema changes
- [ ] Relevant docs updated (or explicit no-doc rationale provided)

## Common Pitfalls

- Implementing generic template CRUD guidance for training lifecycle endpoints
- Forgetting superuser enforcement on operational endpoints
- Skipping generate-client after backend contract changes
- Updating docs partially, causing drift between docs and behavior
- Editing generated frontend client files directly
