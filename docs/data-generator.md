# Data Generator (`backend/util/generate_data.py`)

This document describes how synthetic telemetry is generated for the pacemaker monitoring workflow.

## Entry Point

Function: `generate_predictive_telemetry(...)` in `backend/util/generate_data.py`.

Primary purpose:
- Generate synthetic telemetry for all patients over a shared timeline.
- Inject realistic pre-failure degradation for a subset of patients.
- Produce `Target_Fail_Next_7d` labels for supervised training.
- Engineer temporal rolling/trend features used by `MLEngine`.

## Timeline and Row Ordering

The generated dataset simulates **all patients coexisting at the same time**.

- Every telemetry interval includes one row per active patient.
- Rows are sorted by `Timestamp` first, then `Patient_ID`.
- This creates a parallel timeline view, for example:
  - `t1`: patient 0, patient 1, patient 2, ...
  - `t2`: patient 0, patient 1, patient 2, ...

It does **not** generate all time points for patient 0, then all time points for patient 1.

## Failure Simulation

For a configurable percentage of patients (`failure_rate`):

- A failure point is sampled after sufficient baseline history.
- A degradation window is injected before failure (failure type randomly selected from impedance, threshold, sensing, battery).
- The 7-day pre-failure window is labeled with `Target_Fail_Next_7d = 1`.
- Explant rule is applied: all telemetry at/after failure time is removed for that patient.

Failure and labeling logic is applied using patient-local time indexing to remain correct even when rows are globally interleaved by timestamp.

## Feature Engineering

Computed per patient (time-ordered):

- Rolling means (3d, 7d)
  - `Lead_Impedance_Ohms_RollingMean_3d`
  - `Lead_Impedance_Ohms_RollingMean_7d`
  - `Capture_Threshold_V_RollingMean_3d`
  - `Capture_Threshold_V_RollingMean_7d`
- Delta-per-day trends (3d, 7d)
  - `Lead_Impedance_Ohms_DeltaPerDay_3d`
  - `Lead_Impedance_Ohms_DeltaPerDay_7d`
  - `Capture_Threshold_V_DeltaPerDay_3d`
  - `Capture_Threshold_V_DeltaPerDay_7d`

## Output

- Returns a pandas DataFrame.
- Optionally writes CSV under `backend/util/data/` when `save_csv=True` and a relative filename is used.
- Default filename: `pacemaker_data_seed.csv`.

## Example

```python
from backend.util.generate_data import generate_predictive_telemetry

df = generate_predictive_telemetry(
    num_patients=1000,
    pings_per_day=1,
    num_days=1825,
    failure_rate=0.2,
    filename="pacemaker_data_seed.csv",
    save_csv=True,
)
```
