# Pacemaker Failure Prediction Feature Reference

This document defines only the features used for pacemaker failure prediction context.

## Core Telemetry Features

### lead_impedance_ohms
- Electrical impedance of the pacing lead in Ohms.
- Used to detect lead integrity issues (e.g., insulation breach, conductor fracture, connection faults).

### capture_threshold_v
- Minimum pacing voltage required to capture (depolarize) myocardium.
- Rising values can indicate worsening lead-tissue interface performance and increased risk of failure.

### r_wave_sensing_mv
- Measured ventricular intrinsic signal amplitude (R-wave) in mV.
- Falling values can indicate degraded sensing quality and progression toward device/lead failure states.

### battery_voltage_v
- Measured pulse generator battery voltage.
- Accelerated decline can precede near-term device failure.

## Prediction Target

### target_fail_next_7d
- Binary target label for supervised learning.
- `1` = device fails within the next 7 days.
- `0` = device does not fail within the next 7 days.

## Engineered Rolling Mean Features

### lead_impedance_ohms_rolling_mean_3d
- Trailing 3-day rolling mean of `lead_impedance_ohms`.
- Smooths short-term noise to capture recent local trend.

### lead_impedance_ohms_rolling_mean_7d
- Trailing 7-day rolling mean of `lead_impedance_ohms`.
- Captures broader weekly trend in lead impedance behavior.

### capture_threshold_v_rolling_mean_3d
- Trailing 3-day rolling mean of `capture_threshold_v`.
- Highlights short-horizon upward threshold drift.

### capture_threshold_v_rolling_mean_7d
- Trailing 7-day rolling mean of `capture_threshold_v`.
- Captures medium-horizon threshold trajectory.

## Engineered Delta-Per-Day Features

### lead_impedance_ohms_delta_per_day_3d
- Average per-day change in `lead_impedance_ohms` over trailing 3 days.
- Positive values indicate increasing impedance; negative values indicate decreasing impedance.

### lead_impedance_ohms_delta_per_day_7d
- Average per-day change in `lead_impedance_ohms` over trailing 7 days.
- Quantifies weekly direction and slope of impedance change.

### capture_threshold_v_delta_per_day_3d
- Average per-day change in `capture_threshold_v` over trailing 3 days.
- Positive values indicate short-term threshold rise.

### capture_threshold_v_delta_per_day_7d
- Average per-day change in `capture_threshold_v` over trailing 7 days.
- Quantifies weekly threshold progression.

## Telemetry Ingestion API Contract (Demo V1)

- Endpoint: `POST /api/v1/telemetry/ingest`
- Authentication: superuser token required.
- Request body: JSON array of telemetry rows (variable daily batch size; typical upper target ~1000 rows/day, maximum 2000 rows/request).

### Required fields per row

- `patient_id` (integer, >= 0)
- `timestamp` (Unix epoch seconds, UTC)
- `lead_impedance_ohms` (number)
- `capture_threshold_v` (number)
- `r_wave_sensing_mv` (number)
- `battery_voltage_v` (number)

### Optional fields per row

- `target_fail_next_7d` (`0`, `1`, or `null`)
- All engineered rolling/delta feature fields listed above.

### Duplicate behavior

- Rows are considered duplicates when `patient_id` and `timestamp` match.
- Duplicates are not inserted and are reported in the response summary (`duplicate_count`, `duplicate_in_payload_count`, `duplicate_existing_count`).

## Standalone Telemetry Replay Script

- Script: `backend/util/replay_telemetry.py`
- Purpose: replay generated CSV telemetry to the ingest endpoint in day-level batches at a configurable millisecond interval.
- Batch behavior: requests are grouped by UTC day. Because simulated failed devices stop reporting, later days naturally contain fewer rows than earlier days.

### Default behavior

- Input CSV: `backend/util/data/pacemaker_data.csv`
- Endpoint: `http://localhost:8000/api/v1/telemetry/ingest`
- Request pacing: `--interval-ms 1000`
- Auth token: optional `--token` argument, or `TELEMETRY_INGEST_TOKEN` environment variable.

### Example

```bash
cd backend
uv run python util/replay_telemetry.py --interval-ms 500 --token "$TELEMETRY_INGEST_TOKEN"
```

### Dry run

```bash
cd backend
uv run python util/replay_telemetry.py --dry-run --interval-ms 0 --verbose
```

## Telemetry Ingestion API Contract (Demo V1)

- Endpoint: `POST /api/v1/telemetry/ingest`
- Authentication: superuser token required.
- Request body: JSON array of telemetry rows (variable daily batch size; typical upper target ~1000 rows/day, maximum 2000 rows/request).

### Required fields per row

- `patient_id` (integer, >= 0)
- `timestamp` (Unix epoch seconds, UTC)
- `lead_impedance_ohms` (number)
- `capture_threshold_v` (number)
- `r_wave_sensing_mv` (number)
- `battery_voltage_v` (number)

### Optional fields per row

- `target_fail_next_7d` (`0`, `1`, or `null`)
- All engineered rolling/delta feature fields listed above.

### Duplicate behavior

- Rows are considered duplicates when `patient_id` and `timestamp` match.
- Duplicates are not inserted and are reported in the response summary (`duplicate_count`, `duplicate_in_payload_count`, `duplicate_existing_count`).
