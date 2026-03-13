---
description: Guidance for maintaining the telemetry replay flow documentation. Use when editing replay architecture, ingest behavior, or replay script usage docs.
applyTo: "docs/telemetry-live-replay.md"
---

# Telemetry Replay Documentation Instructions

Use these instructions whenever editing `docs/telemetry-live-replay.md`.

## Intent

Keep this document focused on the end-to-end replay ingestion path from generated CSV to API ingestion and PostgreSQL persistence.

## Content Requirements

- Keep architecture references aligned with:
  - `backend/util/replay_telemetry.py`
  - `backend/app/api/routes/telemetry.py`
  - `backend/app/models.py`
- Keep command examples runnable from repository root and include platform-safe shell examples when relevant.
- Keep required ingest payload fields and batch-size limits synchronized with backend validation.
- Keep duplicate-handling behavior explicit (payload-level and database-level dedupe).

## Boundaries

- Do not duplicate full setup steps that belong in `docs/telemetry-live-replay-setup.md`.
- Do not describe model-training internals here; link to `docs/training_loop.md` or `docs/local-training-listener.md` when needed.

## Style

- Prefer concise step-based structure.
- Prefer concrete endpoint/module links over abstract wording.
- Keep troubleshooting focused on actionable checks.

## Documentation Sync Rule

When replay behavior changes in `backend/util/replay_telemetry.py` or ingest contract behavior changes in `backend/app/api/routes/telemetry.py`, update this document in the same change set.
