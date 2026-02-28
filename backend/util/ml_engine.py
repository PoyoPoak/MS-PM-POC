"""
ml_engine.py
============
``MLEngine`` — Random Forest training, evaluation, and prediction engine for
pacemaker telemetry risk monitoring.

Standalone scope (early-stage)
-------------------------------
Load data → prepare features → train RF → evaluate (OOB + K-Fold CV +
classification report) → predict on new data → persist/reload artifacts.

Typical usage
-------------
::

    from backend.util.ml_engine import MLEngine

    # --- Train & evaluate ---
    engine = MLEngine(n_estimators=200, max_depth=20)
    engine.train("backend/util/data/pacemaker_data.csv")
    metrics = engine.evaluate()
    artifact_dir = engine.save_artifact()

    # --- Predict on new telemetry ---
    predictions = engine.predict("backend/util/data/new_telemetry.csv")

    # --- Reload a saved model ---
    engine2 = MLEngine().load_artifact(artifact_dir)
    predictions2 = engine2.predict(new_df)
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import KFold, cross_val_score, train_test_split

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

# Columns that carry identity/time context but are not predictive model inputs.
_DEFAULT_EXCLUDED_COLUMNS: list[str] = ["Patient_ID", "Timestamp"]

# Target column produced by the data generation pipeline.
_DEFAULT_TARGET_COLUMN: str = "Target_Fail_Next_7d"

# Default artifact output directory (relative to this file's location).
_DEFAULT_ARTIFACT_DIR: Path = Path(__file__).parent / "artifacts"


# ---------------------------------------------------------------------------
# MLEngine
# ---------------------------------------------------------------------------


class MLEngine:
    """Training, evaluation, and prediction engine for pacemaker telemetry.

    The class encapsulates the full ML lifecycle for the Random Forest baseline
    model used to predict near-term pacemaker device failure.

    Attributes:
        n_estimators: Trees in the Random Forest.
        max_depth: Maximum tree depth; ``None`` means no limit.
        random_state: Global seed for reproducibility.
        n_folds: Folds used in K-Fold cross-validation.
        test_size: Fraction of data reserved for the hold-out test set.
        target_column: Name of the binary classification target column.
        excluded_columns: Columns removed before feature preparation.
        artifact_dir: Root directory for persisted model artifacts.
    """

    def __init__(
        self,
        *,
        n_estimators: int = 100,
        max_depth: int | None = None,
        random_state: int = 42,
        n_folds: int = 5,
        test_size: float = 0.2,
        target_column: str = _DEFAULT_TARGET_COLUMN,
        excluded_columns: list[str] | None = None,
        artifact_dir: str | Path = _DEFAULT_ARTIFACT_DIR,
    ) -> None:
        """Initialise the engine with Random Forest hyperparameters and config.

        Args:
            n_estimators: Number of trees in the Random Forest.
            max_depth: Maximum depth of each tree; ``None`` grows fully.
            random_state: Seed for the RF and train/test split.
            n_folds: Number of folds for K-Fold cross-validation in
                :meth:`evaluate`.
            test_size: Proportion of labelled data held out as a test set.
            target_column: Column name of the binary classification target.
            excluded_columns: Columns dropped prior to feature preparation;
                defaults to ``["Patient_ID", "Timestamp"]``.
            artifact_dir: Root directory written by :meth:`save_artifact` and
                read by :meth:`load_artifact`.
        """
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self.n_folds = n_folds
        self.test_size = test_size
        self.target_column = target_column
        self.excluded_columns: list[str] = (
            excluded_columns
            if excluded_columns is not None
            else list(_DEFAULT_EXCLUDED_COLUMNS)
        )
        self.artifact_dir = Path(artifact_dir)

        # Internal state — populated by train() / load_artifact()
        self._model: RandomForestClassifier | None = None
        self._feature_names: list[str] = []
        self._X_train: pd.DataFrame | None = None
        self._y_train: pd.Series | None = None
        self._X_test: pd.DataFrame | None = None
        self._y_test: pd.Series | None = None
        self._train_metadata: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def load_data(self, source: str | Path | pd.DataFrame) -> pd.DataFrame:
        """Load telemetry data from a CSV file path or an existing DataFrame.

        Args:
            source: Absolute or relative path to a CSV file, or a DataFrame
                that is used directly (a copy is taken; the original is not
                mutated).

        Returns:
            A pandas DataFrame ready for feature preparation.

        Raises:
            FileNotFoundError: If ``source`` is a path and the file does not
                exist.
            ValueError: If the resulting DataFrame is empty.
        """
        if isinstance(source, pd.DataFrame):
            df = source.copy()
        else:
            csv_path = Path(source)
            if not csv_path.exists():
                raise FileNotFoundError(f"Data file not found: {csv_path}")
            logger.info("Loading data from %s", csv_path)
            df = pd.read_csv(csv_path)

        if df.empty:
            raise ValueError("Loaded dataset is empty.")

        logger.info("Loaded %d rows × %d columns.", len(df), len(df.columns))
        return df

    # ------------------------------------------------------------------
    # Feature preparation
    # ------------------------------------------------------------------

    def prepare_features(
        self,
        df: pd.DataFrame,
        *,
        inference_mode: bool = False,
    ) -> tuple[pd.DataFrame, pd.Series | None]:
        """Isolate the feature matrix and (optionally) the target vector.

        Steps:

        1. Drop excluded identity/time columns (e.g. ``Patient_ID``,
           ``Timestamp``).
        2. **Training mode**: separate the target column, then remove rows
           whose rolling-window feature columns contain ``NaN`` values
           introduced during the warm-up period of the rolling calculations.
        3. **Inference mode**: enforce the training-time feature schema
           (column list and order) so predictions are consistent with the
           fitted model; the target column is *not* required.

        Args:
            df: Raw telemetry DataFrame (may still include excluded and/or
                target columns).
            inference_mode: ``True`` when scoring new data — the target column
                is not expected and feature alignment uses the schema captured
                during :meth:`train`.

        Returns:
            ``(X, y)`` where *y* is ``None`` in inference mode.

        Raises:
            RuntimeError: If ``inference_mode=True`` but :meth:`train` or
                :meth:`load_artifact` has not yet been called.
            ValueError: If required feature columns are absent in inference
                mode, or if the target column is missing in training mode.
        """
        df = df.copy()

        # Step 1: drop non-predictive identity/time columns
        cols_to_drop = [c for c in self.excluded_columns if c in df.columns]
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)

        # --- Inference mode ---
        if inference_mode:
            if not self._feature_names:
                raise RuntimeError(
                    "No trained feature schema found. "
                    "Call train() or load_artifact() before predict()."
                )
            # Remove the target column if it happens to be present
            df = df.drop(columns=[self.target_column], errors="ignore")

            missing = set(self._feature_names) - set(df.columns)
            if missing:
                raise ValueError(
                    "Inference data is missing trained feature columns: "
                    f"{sorted(missing)}"
                )
            return df[self._feature_names], None

        # --- Training mode ---
        if self.target_column not in df.columns:
            raise ValueError(
                f"Target column '{self.target_column}' not found in the dataset."
            )

        y: pd.Series = df[self.target_column]
        X: pd.DataFrame = df.drop(columns=[self.target_column])

        # Remove NaN rows produced by rolling-feature warm-up
        original_len = len(X)
        valid_mask: pd.Series = X.notna().all(axis=1) & y.notna()
        X = X.loc[valid_mask]
        y = y.loc[valid_mask]

        dropped = original_len - len(X)
        if dropped:
            logger.info(
                "Removed %d NaN rows (rolling-window warm-up artefacts).",
                dropped,
            )

        positive_rate = float(y.mean())
        logger.info(
            "Feature matrix: %d rows × %d features | "
            "Positive-class rate (Target=1): %.3f",
            len(X),
            len(X.columns),
            positive_rate,
        )
        return X, y

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(self, source: str | Path | pd.DataFrame) -> MLEngine:
        """Run the full training pipeline: load → prepare → split → fit.

        A stratified train/test split is applied before fitting.  The Random
        Forest is created with ``oob_score=True`` so that the out-of-bag
        accuracy estimate is always available immediately after training.

        Args:
            source: CSV path or labelled DataFrame containing telemetry data
                with the target column.

        Returns:
            ``self`` — supports method chaining.
        """
        df = self.load_data(source)
        X, y_or_none = self.prepare_features(df)

        # y is always present in training mode; explicit check for type safety
        if y_or_none is None:
            raise RuntimeError(
                "prepare_features returned no target vector in training mode."
            )
        y: pd.Series = y_or_none

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=self.test_size,
            random_state=self.random_state,
            stratify=y,
        )

        self._feature_names = list(X_train.columns)
        self._X_train = X_train
        self._y_train = y_train
        self._X_test = X_test
        self._y_test = y_test

        self._model = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            oob_score=True,
            random_state=self.random_state,
            n_jobs=-1,
        )

        train_start = time.perf_counter()
        self._model.fit(X_train, y_train)
        train_duration = time.perf_counter() - train_start

        oob: float = float(self._model.oob_score_)
        logger.info(
            "Training complete in %.2fs | OOB score: %.4f | "
            "Train rows: %d | Test rows: %d",
            train_duration,
            oob,
            len(X_train),
            len(X_test),
        )

        self._train_metadata = {
            "train_rows": int(len(X_train)),
            "test_rows": int(len(X_test)),
            "n_features": int(len(self._feature_names)),
            "positive_rate_train": round(float(y_train.mean()), 4),
            "oob_score": round(oob, 4),
            "training_duration_seconds": round(train_duration, 3),
            "hyperparameters": {
                "n_estimators": self.n_estimators,
                "max_depth": self.max_depth,
                "random_state": self.random_state,
                "oob_score": True,
                "n_jobs": -1,
            },
        }

        return self

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def evaluate(self) -> dict[str, Any]:
        """Produce a comprehensive model evaluation report.

        Metrics computed:

        - **OOB score** — out-of-bag accuracy estimate captured during
          training.
        - **K-Fold CV** — ``n_folds``-fold cross-validation accuracy run on
          the training partition, refitting the estimator for each fold to give
          an honest generalisation estimate.
        - **Hold-out test metrics** — accuracy, and a full
          ``classification_report`` (precision, recall, F1, support per class)
          evaluated on the test set reserved during :meth:`train`.

        Returns:
            Structured metrics dictionary that is JSON-serialisable and ready
            for downstream run-history logging.

        Raises:
            RuntimeError: If :meth:`train` has not been called.
        """
        if (
            self._model is None
            or self._X_train is None
            or self._y_train is None
            or self._X_test is None
            or self._y_test is None
        ):
            raise RuntimeError(
                "No trained model found. Call train() before evaluate()."
            )

        # K-Fold cross-validation on the *training* partition
        kf = KFold(n_splits=self.n_folds, shuffle=True, random_state=self.random_state)
        cv_scores = cross_val_score(
            RandomForestClassifier(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                oob_score=False,
                random_state=self.random_state,
                n_jobs=-1,
            ),
            self._X_train,
            self._y_train,
            cv=kf,
            scoring="accuracy",
        )

        # Hold-out test evaluation
        y_pred = self._model.predict(self._X_test)
        test_accuracy = float(
            np.sum(np.asarray(y_pred) == np.asarray(self._y_test)) / len(self._y_test)
        )

        report: dict[str, Any] = classification_report(
            self._y_test, y_pred, output_dict=True
        )

        metrics: dict[str, Any] = {
            "oob_score": self._train_metadata.get("oob_score"),
            "kfold_cv_scores": [round(float(s), 4) for s in cv_scores],
            "kfold_cv_mean": round(float(cv_scores.mean()), 4),
            "kfold_cv_std": round(float(cv_scores.std()), 4),
            "test_accuracy": round(test_accuracy, 4),
            "classification_report": report,
            "hyperparameters": self._train_metadata.get("hyperparameters", {}),
            "dataset_info": {
                "train_rows": self._train_metadata.get("train_rows"),
                "test_rows": self._train_metadata.get("test_rows"),
                "n_features": self._train_metadata.get("n_features"),
                "positive_rate_train": self._train_metadata.get("positive_rate_train"),
            },
        }

        logger.info(
            "Evaluation | OOB: %.4f | KFold mean: %.4f ± %.4f | Test accuracy: %.4f",
            metrics["oob_score"],
            metrics["kfold_cv_mean"],
            metrics["kfold_cv_std"],
            metrics["test_accuracy"],
        )
        return metrics

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self, source: str | Path | pd.DataFrame) -> pd.DataFrame:
        """Run batch risk predictions on new or unseen telemetry data.

        Non-feature context columns present in the input (e.g. ``Patient_ID``,
        ``Timestamp``) are **preserved** in the output alongside the model
        outputs for traceability.  They are not passed to the model.

        Args:
            source: CSV path or DataFrame of telemetry records to score.  Must
                contain at least the columns used during training; any
                additional columns are passed through unchanged.

        Returns:
                        A copy of the input DataFrame with one additional column appended:

                        - ``risk_probability`` — model's predicted probability for
                            class ``1`` (failure), rounded to 4 decimal places.

        Raises:
            RuntimeError: If :meth:`train` or :meth:`load_artifact` has not
                been called.
        """
        if self._model is None:
            raise RuntimeError(
                "No fitted model available. Call train() or load_artifact() first."
            )

        raw_df = self.load_data(source)
        X, _ = self.prepare_features(raw_df, inference_mode=True)

        probabilities: np.ndarray = self._model.predict_proba(X)[:, 1]

        result = raw_df.copy()
        result["risk_probability"] = np.round(probabilities, 4)

        total = len(result)
        logger.info(
            "Prediction complete: %d records scored. Max risk probability: %.4f",
            total,
            float(result["risk_probability"].max()) if total > 0 else 0.0,
        )
        return result

    # ------------------------------------------------------------------
    # Artifact persistence
    # ------------------------------------------------------------------

    def save_artifact(self, version_id: str | None = None) -> Path:
        """Persist the fitted model and run metadata to disk.

        Creates ``{artifact_dir}/{version_id}/`` containing:

        - ``model.joblib`` — serialised ``RandomForestClassifier``.
        - ``run_metadata.json`` — version ID, hyperparameters, dataset info,
          training metrics, and the feature schema required to reload and run
          predictions.

        Args:
            version_id: Sortable identifier for this run.  Defaults to the
                current UTC time formatted as ``YYYYMMDD_HHMMSS``.

        Returns:
            :class:`~pathlib.Path` to the artifact directory.

        Raises:
            RuntimeError: If :meth:`train` has not been called.
        """
        if self._model is None:
            raise RuntimeError("No trained model to save. Call train() first.")

        if version_id is None:
            version_id = time.strftime("%Y%m%d_%H%M%S", time.gmtime())

        save_dir = self.artifact_dir / version_id
        save_dir.mkdir(parents=True, exist_ok=True)

        model_path = save_dir / "model.joblib"
        joblib.dump(self._model, model_path)

        metadata: dict[str, Any] = {
            "version_id": version_id,
            "saved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "feature_names": self._feature_names,
            "target_column": self.target_column,
            "excluded_columns": self.excluded_columns,
            **self._train_metadata,
        }

        metadata_path = save_dir / "run_metadata.json"
        with metadata_path.open("w") as fh:
            json.dump(metadata, fh, indent=2)

        logger.info("Artifact saved → %s  (version: %s)", save_dir, version_id)
        return save_dir

    def load_artifact(self, path: str | Path) -> MLEngine:
        """Reload a previously saved model and its metadata.

        Accepts either:

        - The **directory** path created by :meth:`save_artifact`
          (containing ``model.joblib`` + ``run_metadata.json``), or
        - A direct path to a ``model.joblib`` file (metadata is read from the
          same directory if present).

        After loading, :meth:`predict` is immediately available using the
        restored feature schema.

        Args:
            path: Directory or ``model.joblib`` file path.

        Returns:
            ``self`` — supports method chaining.

        Raises:
            FileNotFoundError: If the model file does not exist.
        """
        artifact_path = Path(path)

        if artifact_path.is_dir():
            model_file = artifact_path / "model.joblib"
            metadata_file = artifact_path / "run_metadata.json"
        else:
            model_file = artifact_path
            metadata_file = artifact_path.parent / "run_metadata.json"

        if not model_file.exists():
            raise FileNotFoundError(f"Model file not found: {model_file}")

        self._model = joblib.load(model_file)

        if metadata_file.exists():
            with metadata_file.open() as fh:
                meta: dict[str, Any] = json.load(fh)

            self._feature_names = meta.get("feature_names", [])
            self.target_column = meta.get("target_column", self.target_column)
            self.excluded_columns = meta.get("excluded_columns", self.excluded_columns)
            # Restore available training metadata (skip version/path keys)
            _skip = {
                "version_id",
                "saved_at_utc",
                "feature_names",
                "target_column",
                "excluded_columns",
            }
            self._train_metadata = {k: v for k, v in meta.items() if k not in _skip}
            logger.info(
                "Loaded artifact version '%s' from %s",
                meta.get("version_id"),
                artifact_path,
            )
        else:
            logger.warning(
                "run_metadata.json not found alongside model at %s. "
                "Feature schema must be set manually via _feature_names.",
                artifact_path,
            )

        return self


# ---------------------------------------------------------------------------
# CLI smoke runner (not imported in production)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Run MLEngine smoke test (train/eval/predict or load latest model)."
    )
    parser.add_argument(
        "csv_path",
        nargs="?",
        default=str(Path(__file__).parent / "data" / "pacemaker_data.csv"),
        help="CSV path used for training and smoke predictions.",
    )
    parser.add_argument(
        "--lastmodel",
        action="store_true",
        help="Load the latest saved artifact from backend/util/artifacts and skip retraining.",
    )
    args = parser.parse_args(sys.argv[1:])

    csv_arg = args.csv_path

    if args.lastmodel:
        artifacts_root = Path(__file__).parent / "artifacts"
        artifact_dirs = [
            path
            for path in artifacts_root.glob("*")
            if path.is_dir() and (path / "model.joblib").exists()
        ]
        if not artifact_dirs:
            raise FileNotFoundError(
                "No existing model artifacts found. Run smoke test without "
                "--lastmodel first to create one."
            )

        artifact_dir = max(artifact_dirs, key=lambda path: path.stat().st_mtime)
        engine2 = MLEngine().load_artifact(artifact_dir)
        logger.info("Using latest existing artifact: %s", artifact_dir)
    else:
        engine = MLEngine(n_estimators=100, max_depth=20)
        engine.train(csv_arg)
        metrics = engine.evaluate()
        artifact_dir = engine.save_artifact()

        logger.info("--- Evaluation Summary ---")
        logger.info("OOB score      : %.4f", metrics["oob_score"])
        logger.info(
            "KFold CV mean  : %.4f ± %.4f",
            metrics["kfold_cv_mean"],
            metrics["kfold_cv_std"],
        )
        logger.info("Test accuracy  : %.4f", metrics["test_accuracy"])
        logger.info("Artifacts at   : %s", artifact_dir)

        engine2 = MLEngine().load_artifact(artifact_dir)

    # Quick predict smoke check on a random sample from the same CSV.
    full_df = pd.read_csv(csv_arg)
    sample_size = min(100, len(full_df))
    sample_df = full_df.sample(n=sample_size, random_state=42)
    preds = engine2.predict(sample_df)
    smoke_predictions_path = artifact_dir / "smoke_predictions_sample.csv"

    preds.to_csv(smoke_predictions_path, index=False)
    logger.info("Smoke prediction CSV: %s", smoke_predictions_path)
    top_risk_preds = preds.sort_values("risk_probability", ascending=False).head(5)
    logger.info(
        "Top 5 most likely risk predictions:\n%s",
        top_risk_preds[["Patient_ID", "Timestamp", "risk_probability"]],
    )
