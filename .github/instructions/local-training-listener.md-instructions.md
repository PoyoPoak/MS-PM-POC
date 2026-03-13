---
description: Guidance for maintaining local training worker documentation. Use when editing polling flow, worker runtime behavior, or listener CLI docs.
applyTo: "docs/local-training-listener.md"
---

# Local Training Listener Documentation Instructions

Use these instructions whenever editing `docs/local-training-listener.md`.

## Intent

Keep this document as the canonical operational guide for the polling worker in `backend/util/training_listener.py`.

## Content Requirements

- Keep lifecycle flow accurate: `poll` -> `claim` -> `download` -> `train` -> `upload` -> `complete`.
- Keep endpoint references synchronized with:
  - `docs/training-sync-endpoints.md`
  - `docs/model-upload-endpoint.md`
- Keep CLI flags and environment variable mappings aligned with the script.
- Keep default values accurate for backend URL, polling interval, timeout, and local CSV path.
- Keep minimum-row training guard behavior (`_MIN_ROWS_FOR_TRAINING`) documented.

## Boundaries

- Do not duplicate full endpoint contracts from `docs/training-sync-endpoints.md`; summarize and link.
- Do not document core ML implementation details beyond what the worker invokes; link to `docs/ml-engine.md`.

## Style

- Prefer operational clarity over architecture prose.
- Keep troubleshooting and manual-test sections task-oriented.
- Ensure examples match current auth requirements (superuser bearer token).

## Documentation Sync Rule

When worker behavior changes in `backend/util/training_listener.py`, update this document in the same change set.
