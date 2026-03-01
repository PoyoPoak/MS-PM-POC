# MLEngine Guide

This document explains how `MLEngine` in `backend/util/ml_engine.py` works, what it expects, and how to use it for the early-stage flow:

`generate_data.py` → model training → evaluation → prediction.

## Purpose and Scope

`MLEngine` is a focused utility class for:
- Loading telemetry data from a CSV path or pandas DataFrame
- Preparing model features and labels
- Training a Random Forest classifier
- Evaluating with OOB, K-Fold CV, and hold-out test metrics
- Running batch predictions
- Saving and loading model artifacts locally

Current scope intentionally excludes API wiring, DB incremental sync, and model registry activation workflows.

## Class Configuration

Constructor (`MLEngine(...)`) accepts:
- `n_estimators` (default `100`): number of trees in the Random Forest
- `max_depth` (default `None`): max depth of each tree
- `random_state` (default `42`): deterministic randomness for reproducibility
- `n_folds` (default `5`): K-Fold count for CV
- `test_size` (default `0.2`): hold-out fraction for test split
- `target_column` (default `Target_Fail_Next_7d`)
- `excluded_columns` (default `["Patient_ID", "Timestamp"]`)
- `artifact_dir` (default `backend/util/artifacts`)

## Method-by-Method Behavior

### `load_data(source)`

Input:
- CSV file path (`str`/`Path`) or
- `pd.DataFrame`

Behavior:
- Reads CSV with `pandas.read_csv()` when path is provided
- Copies DataFrame when DataFrame input is provided
- Raises if path is missing or dataset is empty

Returns:
- Loaded `pd.DataFrame`

### `prepare_features(df, inference_mode=False)`

Behavior in both modes:
- Drops non-predictive columns from `excluded_columns`

Training mode (`inference_mode=False`):
- Requires `target_column`
- Separates `X` (features) and `y` (target)
- Drops rows where feature columns (or target) contain `NaN`
  - This is mainly for rolling-window warm-up rows from generated telemetry features

Inference mode (`inference_mode=True`):
- Requires trained feature schema (`self._feature_names`)
- Drops target column if present
- Validates that all trained feature columns exist
- Reorders columns to training-time feature order

Returns:
- `(X, y)` for training mode
- `(X, None)` for inference mode

### `train(source)`

Pipeline:
1. `load_data(source)`
2. `prepare_features(..., inference_mode=False)`
3. Stratified train/test split with `train_test_split`
4. Fit `RandomForestClassifier` with:
   - configured hyperparameters
   - `oob_score=True`
   - `n_jobs=-1`
5. Store training metadata and feature schema for later evaluation/prediction

Returns:
- `self` (for chaining)

### `evaluate()`

Prerequisite:
- `train()` must be completed first

Metrics produced:
- `oob_score`: out-of-bag score from training model
- `kfold_cv_scores`: fold accuracy list on training partition
- `kfold_cv_mean`, `kfold_cv_std`
- `test_accuracy`: hold-out test set accuracy
- `classification_report`: sklearn `classification_report(..., output_dict=True)`
- `hyperparameters` and dataset summary (`dataset_info`)

Returns:
- JSON-serializable `dict[str, Any]`

### `predict(source)`

Prerequisite:
- Trained model exists (`train()`) or loaded model exists (`load_artifact()`)

Behavior:
- Loads input
- Prepares inference features aligned to training schema
- Generates `risk_probability` (probability of class `1`)
- Returns original input columns plus prediction columns

Returns:
- `pd.DataFrame`

### `save_artifact(version_id=None)`

Behavior:
- Creates `artifact_dir/version_id/`
- Saves:
  - `model.joblib`
  - `run_metadata.json`
- If no `version_id` is provided, uses UTC timestamp format `YYYYMMDD_HHMMSS`

Returns:
- Path to artifact directory

### `load_artifact(path)`

Accepts:
- Artifact directory path, or
- Direct `model.joblib` path

Behavior:
- Loads model via `joblib`
- Loads metadata (if present) and restores:
  - feature schema
  - target/excluded column configuration
  - training metadata

Returns:
- `self`

## Data Contracts

Expected training columns from generated telemetry:
- Core telemetry + engineered features
- `Target_Fail_Next_7d` as binary target
- `Patient_ID`, `Timestamp` may be present but are excluded from model features by default

Notes:
- If inference data misses any trained feature columns, prediction raises a `ValueError`
- Additional unused columns are allowed and passed through in prediction output
- Generated training data is ordered by `Timestamp` then `Patient_ID` to simulate parallel telemetry arrival across active patients
- See `docs/data-generator.md` for generator behavior details

## Typical Usage

## Train from DataFrame

```python
from backend.util.generate_data import generate_predictive_telemetry
from backend.util.ml_engine import MLEngine

df = generate_predictive_telemetry(
    num_patients=500,
    pings_per_day=1,
    num_days=365,
    failure_rate=0.05,
    save_csv=False,
)

engine = MLEngine(n_estimators=200, max_depth=20)
engine.train(df)
metrics = engine.evaluate()
artifact_dir = engine.save_artifact()
```

## Train from CSV

```python
from backend.util.ml_engine import MLEngine

engine = MLEngine()
engine.train("backend/util/data/pacemaker_data_seed.csv")
metrics = engine.evaluate()
```

## Predict with trained or loaded model

```python
from backend.util.ml_engine import MLEngine

engine = MLEngine().load_artifact("backend/util/artifacts/20260227_120000")
pred_df = engine.predict("backend/util/data/new_telemetry.csv")
```

## CLI smoke runner options

Run with retraining (default):

```bash
python backend/util/ml_engine.py
```

Run smoke mode using the latest existing artifact (skip retraining):

```bash
python backend/util/ml_engine.py --lastmodel
```

Use a custom CSV with either mode:

```bash
python backend/util/ml_engine.py path/to/telemetry.csv --lastmodel
```

## Troubleshooting

- **`Target column ... not found`**
  - Ensure training input includes `Target_Fail_Next_7d` (or set custom `target_column`)

- **`No trained feature schema found`**
  - Call `train()` or `load_artifact()` before `predict()`

- **`Inference data is missing trained feature columns`**
  - Ensure incoming telemetry has all features used during training

- **Very high accuracy with low positive class prevalence**
  - Inspect class distribution (`positive_rate_train`)
  - Focus on recall/F1 from `classification_report`, not only accuracy

## Current Limitations (Intentional for Early Stage)

- No threshold tuning for alert policy
- No probability calibration
- No temporal split strategy yet (current split is stratified random)
- No incremental DB + Parquet sync inside this class yet

## Next Integration Steps

When integrating with later stages:
- Add API endpoints that call `train/evaluate/predict`
- Upload trained artifacts and metrics to backend via `POST /api/v1/models/upload`
- Persist run metadata and model binary in PostgreSQL model registry tables
- Add promotion gate checks using recall/F1 thresholds
- Add scheduled retraining and telemetry ingestion orchestration
