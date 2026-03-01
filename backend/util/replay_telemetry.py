from __future__ import annotations

import argparse
import logging
import math
import os
import time
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import pandas as pd  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)

_DEFAULT_ENDPOINT_URL = "http://localhost:8000/api/v1/telemetry/ingest"
_DEFAULT_CSV_PATH = Path(__file__).resolve().parent / "data" / "pacemaker_data.csv"
_DEFAULT_TIMEOUT_SECONDS = 30.0
_DEFAULT_MAX_REQUEST_ROWS = 2000
_REQUIRED_PAYLOAD_FIELDS = [
    "patient_id",
    "timestamp",
    "lead_impedance_ohms",
    "capture_threshold_v",
    "r_wave_sensing_mv",
    "battery_voltage_v",
]
_OPTIONAL_PAYLOAD_FIELDS = [
    "target_fail_next_7d",
    "lead_impedance_ohms_rolling_mean_3d",
    "lead_impedance_ohms_rolling_mean_7d",
    "capture_threshold_v_rolling_mean_3d",
    "capture_threshold_v_rolling_mean_7d",
    "lead_impedance_ohms_delta_per_day_3d",
    "lead_impedance_ohms_delta_per_day_7d",
    "capture_threshold_v_delta_per_day_3d",
    "capture_threshold_v_delta_per_day_7d",
]

_COLUMN_ALIASES = {
    "Patient_ID": "patient_id",
    "Timestamp": "timestamp",
    "Lead_Impedance_Ohms": "lead_impedance_ohms",
    "Capture_Threshold_V": "capture_threshold_v",
    "R_Wave_Sensing_mV": "r_wave_sensing_mv",
    "Battery_Voltage_V": "battery_voltage_v",
    "Target_Fail_Next_7d": "target_fail_next_7d",
    "Lead_Impedance_Ohms_RollingMean_3d": "lead_impedance_ohms_rolling_mean_3d",
    "Lead_Impedance_Ohms_RollingMean_7d": "lead_impedance_ohms_rolling_mean_7d",
    "Capture_Threshold_V_RollingMean_3d": "capture_threshold_v_rolling_mean_3d",
    "Capture_Threshold_V_RollingMean_7d": "capture_threshold_v_rolling_mean_7d",
    "Lead_Impedance_Ohms_DeltaPerDay_3d": "lead_impedance_ohms_delta_per_day_3d",
    "Lead_Impedance_Ohms_DeltaPerDay_7d": "lead_impedance_ohms_delta_per_day_7d",
    "Capture_Threshold_V_DeltaPerDay_3d": "capture_threshold_v_delta_per_day_3d",
    "Capture_Threshold_V_DeltaPerDay_7d": "capture_threshold_v_delta_per_day_7d",
}


@dataclass
class ReplayConfig:
    csv_path: Path
    endpoint_url: str
    interval_ms: int
    timeout_seconds: float
    max_request_rows: int
    token: str | None
    dry_run: bool
    verbose: bool
    stop_on_error: bool


def configure_logging(*, verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def parse_args() -> ReplayConfig:
    parser = argparse.ArgumentParser(
        description=(
            "Replay generated pacemaker telemetry CSV data to "
            "POST /api/v1/telemetry/ingest in daily batches."
        )
    )
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=_DEFAULT_CSV_PATH,
        help="Path to generated telemetry CSV file.",
    )
    parser.add_argument(
        "--endpoint-url",
        default=_DEFAULT_ENDPOINT_URL,
        help="Telemetry ingest endpoint URL.",
    )
    parser.add_argument(
        "--interval-ms",
        type=int,
        default=1000,
        help="Delay between each POST request in milliseconds.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=_DEFAULT_TIMEOUT_SECONDS,
        help="HTTP timeout in seconds.",
    )
    parser.add_argument(
        "--max-request-rows",
        type=int,
        default=_DEFAULT_MAX_REQUEST_ROWS,
        help="Maximum rows in each request payload (ingest API max is 2000).",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("TELEMETRY_INGEST_TOKEN"),
        help="Bearer token for auth. Defaults to TELEMETRY_INGEST_TOKEN env var.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Prepare and log batches but do not send requests.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable detailed per-batch logs.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue replaying remaining batches if a request fails.",
    )

    args = parser.parse_args()

    if args.interval_ms < 0:
        raise ValueError("--interval-ms must be >= 0")
    if args.timeout_seconds <= 0:
        raise ValueError("--timeout-seconds must be > 0")
    if args.max_request_rows <= 0:
        raise ValueError("--max-request-rows must be > 0")

    return ReplayConfig(
        csv_path=args.csv_path,
        endpoint_url=args.endpoint_url,
        interval_ms=args.interval_ms,
        timeout_seconds=args.timeout_seconds,
        max_request_rows=args.max_request_rows,
        token=args.token,
        dry_run=args.dry_run,
        verbose=args.verbose,
        stop_on_error=not args.continue_on_error,
    )


def load_and_normalize_csv(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError("CSV file is empty.")

    df = df.rename(columns=_COLUMN_ALIASES)

    missing_required = [
        column for column in _REQUIRED_PAYLOAD_FIELDS if column not in df
    ]
    if missing_required:
        raise ValueError(
            f"CSV is missing required telemetry columns: {', '.join(missing_required)}"
        )

    payload_columns = [
        *_REQUIRED_PAYLOAD_FIELDS,
        *[field for field in _OPTIONAL_PAYLOAD_FIELDS if field in df.columns],
    ]
    df = df[payload_columns].copy()

    df["patient_id"] = pd.to_numeric(df["patient_id"], errors="raise").astype(int)
    df["timestamp"] = pd.to_numeric(df["timestamp"], errors="raise").astype(int)

    for field in _REQUIRED_PAYLOAD_FIELDS[2:]:
        df[field] = pd.to_numeric(df[field], errors="raise").astype(float)

    if "target_fail_next_7d" in df.columns:
        df["target_fail_next_7d"] = (
            pd.to_numeric(df["target_fail_next_7d"], errors="coerce")
            .round()
            .astype("Int64")
        )

    return df.sort_values(["timestamp", "patient_id"], kind="stable").reset_index(
        drop=True
    )


def iter_daily_batches(
    df: pd.DataFrame, *, max_request_rows: int
) -> Iterator[tuple[str, list[dict[str, Any]]]]:
    day_keys = pd.to_datetime(df["timestamp"], unit="s", utc=True).dt.strftime(
        "%Y-%m-%d"
    )

    grouped = df.groupby(day_keys, sort=False)
    for day_key, day_frame in grouped:
        rows = dataframe_to_payload_rows(day_frame)
        if len(rows) <= max_request_rows:
            yield day_key, rows
            continue

        chunks = math.ceil(len(rows) / max_request_rows)
        for chunk_idx in range(chunks):
            start = chunk_idx * max_request_rows
            end = start + max_request_rows
            yield f"{day_key} (chunk {chunk_idx + 1}/{chunks})", rows[start:end]


def dataframe_to_payload_rows(df: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw_row in df.to_dict(orient="records"):
        payload_row: dict[str, Any] = {}
        for key, value in raw_row.items():
            if value is None:
                payload_row[key] = None
                continue
            if isinstance(value, float) and math.isnan(value):
                payload_row[key] = None
                continue
            if pd.isna(value):
                payload_row[key] = None
                continue
            payload_row[key] = (
                int(value) if key in {"patient_id", "timestamp"} else value
            )
        rows.append(payload_row)
    return rows


def build_headers(token: str | None) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def replay_batches(
    config: ReplayConfig, batches: Iterable[tuple[str, list[dict[str, Any]]]]
) -> None:
    total_batches = 0
    total_rows = 0
    sent_batches = 0
    sent_rows = 0

    headers = build_headers(config.token)
    client_timeout = httpx.Timeout(config.timeout_seconds)

    if not config.dry_run and not config.token:
        logger.warning(
            "No bearer token provided. The ingest endpoint requires superuser auth and may reject requests."
        )

    with httpx.Client(timeout=client_timeout) as client:
        for batch_index, (batch_label, batch_rows) in enumerate(batches, start=1):
            total_batches += 1
            total_rows += len(batch_rows)

            if config.verbose or batch_index == 1 or batch_index % 100 == 0:
                logger.info(
                    "Batch %d | %s | rows=%d",
                    batch_index,
                    batch_label,
                    len(batch_rows),
                )

            if config.dry_run:
                sent_batches += 1
                sent_rows += len(batch_rows)
                continue

            try:
                response = client.post(
                    config.endpoint_url,
                    headers=headers,
                    json=batch_rows,
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                logger.error("Request failed for batch '%s': %s", batch_label, exc)
                if config.stop_on_error:
                    raise
                continue

            sent_batches += 1
            sent_rows += len(batch_rows)

            if config.verbose:
                try:
                    logger.debug(
                        "Batch %d response: %s",
                        batch_index,
                        response.json(),
                    )
                except ValueError:
                    logger.debug(
                        "Batch %d response (non-JSON): %s",
                        batch_index,
                        response.text,
                    )

            if config.interval_ms > 0:
                time.sleep(config.interval_ms / 1000)

    logger.info(
        "Replay complete | prepared_batches=%d prepared_rows=%d sent_batches=%d sent_rows=%d",
        total_batches,
        total_rows,
        sent_batches,
        sent_rows,
    )


def main() -> None:
    config = parse_args()
    configure_logging(verbose=config.verbose)

    logger.info("Loading telemetry CSV from %s", config.csv_path)
    telemetry_df = load_and_normalize_csv(config.csv_path)
    if telemetry_df.empty:
        logger.warning("No telemetry batches found in CSV. Nothing to send.")
        return

    logger.info(
        "Prepared telemetry rows=%d for daily replay batching.", len(telemetry_df)
    )

    replay_batches(
        config,
        iter_daily_batches(
            telemetry_df,
            max_request_rows=config.max_request_rows,
        ),
    )


if __name__ == "__main__":
    main()
