# Pacemaker Failure Prediction Feature Reference

This document defines only the features used for pacemaker failure prediction context.

## Core Telemetry Features

### Lead_Impedance_Ohms
- Electrical impedance of the pacing lead in Ohms.
- Used to detect lead integrity issues (e.g., insulation breach, conductor fracture, connection faults).

### Capture_Threshold_V
- Minimum pacing voltage required to capture (depolarize) myocardium.
- Rising values can indicate worsening lead-tissue interface performance and increased risk of failure.

### R_Wave_Sensing_mV
- Measured ventricular intrinsic signal amplitude (R-wave) in mV.
- Falling values can indicate degraded sensing quality and progression toward device/lead failure states.

### Battery_Voltage_V
- Measured pulse generator battery voltage.
- Accelerated decline can precede near-term device failure.

## Prediction Target

### Target_Fail_Next_7d
- Binary target label for supervised learning.
- `1` = device fails within the next 7 days.
- `0` = device does not fail within the next 7 days.

## Engineered Rolling Mean Features

### Lead_Impedance_Ohms_RollingMean_3d
- Trailing 3-day rolling mean of `Lead_Impedance_Ohms`.
- Smooths short-term noise to capture recent local trend.

### Lead_Impedance_Ohms_RollingMean_7d
- Trailing 7-day rolling mean of `Lead_Impedance_Ohms`.
- Captures broader weekly trend in lead impedance behavior.

### Capture_Threshold_V_RollingMean_3d
- Trailing 3-day rolling mean of `Capture_Threshold_V`.
- Highlights short-horizon upward threshold drift.

### Capture_Threshold_V_RollingMean_7d
- Trailing 7-day rolling mean of `Capture_Threshold_V`.
- Captures medium-horizon threshold trajectory.

## Engineered Delta-Per-Day Features

### Lead_Impedance_Ohms_DeltaPerDay_3d
- Average per-day change in `Lead_Impedance_Ohms` over trailing 3 days.
- Positive values indicate increasing impedance; negative values indicate decreasing impedance.

### Lead_Impedance_Ohms_DeltaPerDay_7d
- Average per-day change in `Lead_Impedance_Ohms` over trailing 7 days.
- Quantifies weekly direction and slope of impedance change.

### Capture_Threshold_V_DeltaPerDay_3d
- Average per-day change in `Capture_Threshold_V` over trailing 3 days.
- Positive values indicate short-term threshold rise.

### Capture_Threshold_V_DeltaPerDay_7d
- Average per-day change in `Capture_Threshold_V` over trailing 7 days.
- Quantifies weekly threshold progression.
