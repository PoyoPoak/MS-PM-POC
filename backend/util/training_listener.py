"""
training_listener.py
====================
Polling-based local compute worker for pacemaker model training.

Flow
----
1. **Poll** ``GET /api/v1/training/poll`` every *N* seconds.
2. If ``true``, **download** new data via
   ``GET /api/v1/training/download?newest_local_ts=<ts>``.
3. Append rows to a local CSV cache, **train** the model with
   ``MLEngine``, then **upload** the artifact + metrics via
   ``POST /api/v1/models/upload``.
4. Resume polling.

All backend communication uses a superuser JWT
(``Authorization: Bearer <TOKEN>``).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

import httpx
import pandas as pd

try:
    from backend.util.ml_engine import MLEngine
except ModuleNotFoundError:
    from ml_engine import MLEngine

logger = logging.getLogger("training_listener")

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
_DEFAULT_BACKEND_URL = "http://localhost:8000"
_DEFAULT_POLL_INTERVAL_SECONDS = 5
_DEFAULT_TIMEOUT_SECONDS = 120.0
_DEFAULT_CSV_PATH = Path(__file__).resolve().parent / "data" / "local_training_data.csv"
_MIN_ROWS_FOR_TRAINING = 10

# ---------------------------------------------------------------------------
# Field mapping: PacemakerTelemetryPublic JSON key → CSV column header
# ---------------------------------------------------------------------------
_FIELD_TO_CSV: dict[str, str] = {
    "patient_id": "Patient_ID",
    "timestamp": "Timestamp",
    "lead_impedance_ohms": "Lead_Impedance_Ohms",
    "capture_threshold_v": "Capture_Threshold_V",
    "r_wave_sensing_mv": "R_Wave_Sensing_mV",
    "battery_voltage_v": "Battery_Voltage_V",
    "target_fail_next_7d": "Target_Fail_Next_7d",
    "lead_impedance_ohms_rolling_mean_3d": "Lead_Impedance_Ohms_RollingMean_3d",
    "lead_impedance_ohms_rolling_mean_7d": "Lead_Impedance_Ohms_RollingMean_7d",
    "capture_threshold_v_rolling_mean_3d": "Capture_Threshold_V_RollingMean_3d",
    "capture_threshold_v_rolling_mean_7d": "Capture_Threshold_V_RollingMean_7d",
    "lead_impedance_ohms_delta_per_day_3d": "Lead_Impedance_Ohms_DeltaPerDay_3d",
    "lead_impedance_ohms_delta_per_day_7d": "Lead_Impedance_Ohms_DeltaPerDay_7d",
    "capture_threshold_v_delta_per_day_3d": "Capture_Threshold_V_DeltaPerDay_3d",
    "capture_threshold_v_delta_per_day_7d": "Capture_Threshold_V_DeltaPerDay_7d",
}

# The CSV columns in canonical order (matches pacemaker_data_seed.csv).
_CSV_COLUMNS: list[str] = list(_FIELD_TO_CSV.values())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _newest_local_ts(csv_path: Path) -> int:
    """Return the newest ``Timestamp`` epoch-seconds from the local CSV.

    Returns ``0`` when the file is missing, empty, or has no data rows.
    """
    if not csv_path.exists():
        return 0
    try:
        df = pd.read_csv(csv_path, usecols=["Timestamp"])
    except (pd.errors.EmptyDataError, ValueError):
        return 0
    if df.empty:
        return 0
    # Timestamp stored as ISO string in CSV — parse then convert.
    ts_series = pd.to_datetime(df["Timestamp"], utc=True)
    return int(ts_series.max().timestamp())


def _rows_to_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Convert JSON rows from ``/training/download`` into a CSV-shaped DataFrame."""
    records: list[dict[str, Any]] = []
    for row in rows:
        record: dict[str, Any] = {}
        for json_key, csv_col in _FIELD_TO_CSV.items():
            record[csv_col] = row.get(json_key)
        records.append(record)
    return pd.DataFrame(records, columns=_CSV_COLUMNS)


def _append_to_csv(df: pd.DataFrame, csv_path: Path) -> None:
    """Append rows to the local CSV cache, creating the file if needed."""
    write_header = not csv_path.exists() or csv_path.stat().st_size == 0
    df.to_csv(csv_path, mode="a", header=write_header, index=False)
    logger.info("Appended %d rows to %s", len(df), csv_path)


def _build_metadata_payload(
    metrics: dict[str, Any],
    *,
    artifact_dir_name: str,
) -> dict[str, Any]:
    """Build the ``metadata_json`` dict for the upload endpoint."""
    return {
        "client_version_id": artifact_dir_name,
        "algorithm": "RandomForestClassifier",
        "hyperparameters": metrics.get("hyperparameters", {}),
        "metrics": {
            "oob_score": metrics.get("oob_score"),
            "kfold_cv_mean": metrics.get("kfold_cv_mean"),
            "kfold_cv_std": metrics.get("kfold_cv_std"),
            "test_accuracy": metrics.get("test_accuracy"),
            "classification_report": metrics.get("classification_report"),
            "kfold_cv_scores": metrics.get("kfold_cv_scores"),
        },
        "dataset_info": metrics.get("dataset_info", {}),
        "notes": "Automated training via polling worker",
    }


def _upload_artifact(
    *,
    upload_url: str,
    token: str,
    model_path: Path,
    metadata_payload: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    """POST the model binary + metadata to the backend upload endpoint."""
    with model_path.open("rb") as f:
        files = {
            "model_file": (model_path.name, f, "application/octet-stream"),
        }
        data = {"metadata_json": json.dumps(metadata_payload)}
        resp = httpx.post(
            upload_url,
            headers=_auth_headers(token),
            files=files,
            data=data,
            timeout=timeout,
        )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Core loop actions
# ---------------------------------------------------------------------------


def poll(*, backend_url: str, token: str, timeout: float) -> bool:
    """Check whether the backend has a pending training job."""
    url = f"{backend_url}/api/v1/training/poll"
    resp = httpx.get(url, headers=_auth_headers(token), timeout=timeout)
    resp.raise_for_status()
    result: bool = resp.json() is True
    return result


def download(
    *,
    backend_url: str,
    token: str,
    newest_ts: int,
    timeout: float,
) -> dict[str, Any]:
    """Download mature telemetry rows newer than *newest_ts*."""
    url = f"{backend_url}/api/v1/training/download"
    resp = httpx.get(
        url,
        headers=_auth_headers(token),
        params={"newest_local_ts": newest_ts},
        timeout=timeout,
    )
    resp.raise_for_status()
    result: dict[str, Any] = resp.json()
    return result


def train_and_upload(
    *,
    csv_path: Path,
    backend_url: str,
    token: str,
    timeout: float,
) -> None:
    """Train a model on the local CSV and upload the artifact to the backend."""
    row_count = sum(1 for _ in csv_path.open()) - 1  # minus header
    if row_count < _MIN_ROWS_FOR_TRAINING:
        logger.warning(
            "Only %d data rows in %s (minimum %d). Skipping training.",
            row_count,
            csv_path,
            _MIN_ROWS_FOR_TRAINING,
        )
        return

    logger.info("Starting training on %s (%d rows)…", csv_path, row_count)

    engine = MLEngine(n_estimators=200, max_depth=20)
    engine.train(csv_path)
    metrics = engine.evaluate()
    artifact_dir = engine.save_artifact()

    model_path = artifact_dir / "model.joblib"
    metadata = _build_metadata_payload(metrics, artifact_dir_name=artifact_dir.name)

    upload_url = f"{backend_url}/api/v1/models/upload"
    logger.info("Uploading artifact %s to %s …", model_path, upload_url)

    result = _upload_artifact(
        upload_url=upload_url,
        token=token,
        model_path=model_path,
        metadata_payload=metadata,
        timeout=timeout,
    )
    logger.info("Upload complete. id=%s", result.get("id"))


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def run_loop(
    *,
    backend_url: str,
    token: str,
    csv_path: Path,
    poll_interval: int,
    timeout: float,
) -> None:  # pragma: no cover — long-running loop
    """Poll → download → train → upload, repeating indefinitely."""
    logger.info(
        "Worker started. backend=%s  csv=%s  interval=%ds",
        backend_url,
        csv_path,
        poll_interval,
    )

    while True:
        try:
            has_job = poll(backend_url=backend_url, token=token, timeout=timeout)
            if not has_job:
                logger.debug("No pending job. Sleeping %ds …", poll_interval)
                time.sleep(poll_interval)
                continue

            logger.info("Pending job detected — downloading data …")
            newest_ts = _newest_local_ts(csv_path)
            data = download(
                backend_url=backend_url,
                token=token,
                newest_ts=newest_ts,
                timeout=timeout,
            )

            if data["count"] > 0:
                df = _rows_to_dataframe(data["rows"])
                _append_to_csv(df, csv_path)
            else:
                logger.info("Download returned 0 new rows.")

            train_and_upload(
                csv_path=csv_path,
                backend_url=backend_url,
                token=token,
                timeout=timeout,
            )

        except httpx.HTTPStatusError as exc:
            logger.error(
                "HTTP %d from %s: %s",
                exc.response.status_code,
                exc.request.url,
                exc.response.text[:300],
            )
        except httpx.HTTPError as exc:
            logger.error("HTTP error: %s", exc)
        except Exception:
            logger.exception("Unexpected error in polling loop")

        time.sleep(poll_interval)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Polling worker that checks the backend for pending training "
            "jobs, downloads new telemetry data, trains a model with "
            "MLEngine, and uploads the artifact back to the backend."
        ),
    )
    parser.add_argument(
        "--backend-url",
        default=os.getenv("BACKEND_URL", _DEFAULT_BACKEND_URL),
        help="Base URL of the backend API (default: %(default)s).",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("BACKEND_SUPERUSER_TOKEN"),
        help="Superuser JWT for backend auth (or set BACKEND_SUPERUSER_TOKEN).",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path(os.getenv("LOCAL_TRAINING_CSV", str(_DEFAULT_CSV_PATH))),
        help="Path to the local training-data CSV cache.",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=int(
            os.getenv("POLL_INTERVAL_SECONDS", str(_DEFAULT_POLL_INTERVAL_SECONDS))
        ),
        help="Seconds between poll requests (default: %(default)s).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=_DEFAULT_TIMEOUT_SECONDS,
        help="HTTP request timeout in seconds (default: %(default)s).",
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["critical", "error", "warning", "info", "debug"],
        help="Log verbosity (default: %(default)s).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )

    if not args.token:
        logger.error(
            "No superuser token provided. Use --token or set BACKEND_SUPERUSER_TOKEN."
        )
        sys.exit(1)

    run_loop(
        backend_url=args.backend_url.rstrip("/"),
        token=args.token,
        csv_path=args.csv,
        poll_interval=args.poll_interval,
        timeout=args.timeout,
    )


if __name__ == "__main__":
    main()
