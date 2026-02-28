---
description: Guidance for implementing and updating the MLEngine training utility.
applyTo: "backend/util/ml_engine.py"
---

# MLEngine Implementation Instructions

Use these instructions whenever editing `backend/util/ml_engine.py`.

## Purpose

`MLEngine` is a focused, early-stage ML utility for the pacemaker telemetry workflow. Its scope is intentionally limited to:

1. Loading telemetry data from CSV or DataFrame
2. Preparing/pruning feature columns
3. Training a Random Forest baseline
4. Evaluating trained models
5. Running batch predictions
6. Saving/loading local artifacts

Do not expand this file into API routing, database ingestion orchestration, or frontend concerns.

## Contract and Behavioral Rules

- Keep baseline model as `RandomForestClassifier`.
- Keep `oob_score=True` enabled during training.
- Preserve support for both CSV path and `pd.DataFrame` inputs.
- Preserve feature-pruning behavior:
	- Exclude identity/time columns by default (`Patient_ID`, `Timestamp`).
	- Require target column during training mode.
	- Remove rows with `NaN` in features/target during training preparation.
- Preserve inference schema enforcement:
	- Predictions must align to training-time feature names/order.
	- Missing required inference features must raise a clear `ValueError`.
- Keep prediction output additive:
	- Return original input columns plus `predicted_label` and `risk_probability`.

## Evaluation Requirements

`evaluate()` should continue returning structured, JSON-serializable metrics containing at least:

- OOB score
- K-Fold CV scores and summary
- Hold-out test accuracy
- `classification_report` output
- Training hyperparameters and dataset summary metadata

Avoid returning metrics in a text-only format.

## Persistence Requirements

- Artifact persistence remains local filesystem based.
- `save_artifact()` must write:
	- `model.joblib`
	- `run_metadata.json`
- `load_artifact()` must restore model and, when metadata exists, restore feature schema and relevant training metadata.

## Quality and Style Constraints

- Follow backend lint/type standards (Ruff + mypy strict compatibility).
- Use `logging` (not `print`).
- Keep methods cohesive and single-purpose.
- Prefer explicit type hints for public method signatures.
- Keep changes backward-compatible unless explicitly requested otherwise.

## Out-of-Scope (Until Explicitly Requested)

- DB incremental pull and Parquet cache orchestration
- Model registry table writes/reads
- Alerting threshold policy logic
- API endpoint integration
- Cloud deployment or CI pipeline wiring

## Documentation Sync Rule

When changing behavior in `ml_engine.py`, update the usage/behavior documentation in `docs/ml-engine.md` in the same change set so docs and implementation remain aligned.