import logging
import time
import uuid
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def generate_predictive_telemetry(
    num_patients=1000,
    pings_per_day=1,
    num_days=1825,
    failure_rate=0.2,
    filename="pacemaker_data.csv",
    save_csv=True,
):
    """
    Generate synthetic pacemaker telemetry time-series data for predictive maintenance modeling.

    The function creates a chronological baseline of healthy device metrics for each patient, injects
    realistic multi-day degradation curves for a subset of failing devices, labels the 7-day pre-failure
    warning window (`Target_Fail_Next_7d`), applies an explant rule to remove all failure-time and
    post-failure records,
    and engineers temporal rolling/trend features.

    Data Map:
    - Patient_ID: Integer identifier for each patient/device (0..num_patients-1).
    - Timestamp: Unix timestamp of each telemetry ping.
    - Lead_Impedance_Ohms: Electrical impedance of the lead, which can indicate lead integrity issues.
    - Capture_Threshold_V: Voltage required to capture the heart, which can rise as the device degrades.
    - R_Wave_Sensing_mV: Quality of R-wave sensing, which can drop as the device fails.
    - Battery_Voltage_V: Voltage of the device battery, which can drop rapidly before failure.
    - Target_Fail_Next_7d: Binary target variable indicating if the device will fail within the next 7 days (1) or not (0).
    - Lead_Impedance_Ohms_RollingMean_3d: Trailing 3-day rolling mean of lead impedance.
    - Lead_Impedance_Ohms_RollingMean_7d: Trailing 7-day rolling mean of lead impedance.
    - Capture_Threshold_V_RollingMean_3d: Trailing 3-day rolling mean of capture threshold.
    - Capture_Threshold_V_RollingMean_7d: Trailing 7-day rolling mean of capture threshold.
    - Lead_Impedance_Ohms_DeltaPerDay_3d: Average per-day change in impedance over trailing 3 days.
    - Lead_Impedance_Ohms_DeltaPerDay_7d: Average per-day change in impedance over trailing 7 days.
    - Capture_Threshold_V_DeltaPerDay_3d: Average per-day change in threshold over trailing 3 days.
    - Capture_Threshold_V_DeltaPerDay_7d: Average per-day change in threshold over trailing 7 days.

        Row ordering:
        - Rows are ordered by Timestamp first, then Patient_ID, so all patients are represented in parallel
            for each telemetry interval.

    Args:
        num_patients (int, optional): Number of patients to simulate data from. Defaults to 1000.
        pings_per_day (int, optional): Number of telemetry pings per day. Defaults to 1.
        num_days (int, optional): Number of days of data to generate. Defaults to 1825.
        failure_rate (float, optional): Proportion of patients that will experience device failure. Defaults to 0.2.
        filename (str, optional): Name of the output CSV file. Relative paths are saved under ./backend/util/data. Defaults to "pacemaker_data_seed.csv".
        save_csv (bool, optional): Whether to save the generated data to a CSV file. Defaults to True.

    Returns:
        pd.DataFrame: A synthetic telemetry dataset with baseline signals, failure labels,
        and engineered rolling/trend features.
    """
    logger.info(
        "Generating predictive data for %d patients over %d days...",
        num_patients,
        num_days,
    )

    # Validate input parameters
    if not (0 <= failure_rate <= 1):
        raise ValueError("Failure rate must be between 0 and 1.")
    if not all(
        isinstance(value, int) for value in (num_patients, pings_per_day, num_days)
    ):
        raise TypeError(
            "num_patients, pings_per_day, and num_days must all be integers."
        )
    if num_patients <= 0 or pings_per_day <= 0 or num_days <= 0:
        raise ValueError(
            "Number of patients, pings per day, and number of days must all be positive integers."
        )
    if not filename:
        filename = f"{uuid.uuid4()}.csv"
    if save_csv and not filename:
        raise ValueError("Filename must be provided if save_csv is True.")
    if save_csv and not filename.endswith(".csv"):
        raise ValueError("Filename must end with '.csv'.")

    # Handle output path
    output_path = Path(filename)
    if save_csv and not output_path.is_absolute() and output_path.parent == Path("."):
        output_path = Path(__file__).resolve().parent / "data" / output_path

    # Ensure we have enough data points to support failure injection and the predictive target window
    total_points_per_patient = num_days * pings_per_day
    normal_data_points = 100 * pings_per_day
    post_failure_buffer_points = 10 * pings_per_day
    min_points_required_for_failure_injection = (
        normal_data_points + post_failure_buffer_points + 1
    )
    if (
        total_points_per_patient < min_points_required_for_failure_injection
        and failure_rate > 0
    ):
        raise ValueError(
            "num_days * pings_per_day must be at least "
            f"{min_points_required_for_failure_injection} when failure_rate > 0 "
            "to support baseline, degradation, and target windows."
        )

    np.random.seed(42)

    # 1. Base Setup: IDs and Timestamps
    patient_ids = np.arange(num_patients, dtype=int)
    interval_seconds = int((24 * 60 * 60) / pings_per_day)
    current_time = int(time.time())
    timestamps = [
        current_time - (i * interval_seconds) for i in range(num_days * pings_per_day)
    ]
    timestamps.reverse()

    idx = pd.MultiIndex.from_product(
        [timestamps, patient_ids], names=["Timestamp", "Patient_ID"]
    )
    df = pd.DataFrame(index=idx).reset_index()[["Patient_ID", "Timestamp"]]

    # 2. Generate Healthy Baseline Metrics
    df["Lead_Impedance_Ohms"] = np.random.normal(500.0, 30.0, size=len(df))
    df["Capture_Threshold_V"] = np.random.normal(0.70, 0.10, size=len(df))
    df["R_Wave_Sensing_mV"] = np.random.normal(12.00, 1.50, size=len(df))
    df["Battery_Voltage_V"] = np.random.normal(2.95, 0.05, size=len(df))

    # Initialize the predictive target
    df["Target_Fail_Next_7d"] = 0

    # 3. Inject Degradation and Failures
    num_failing_patients = int(num_patients * failure_rate)
    failing_patient_ids = np.random.choice(
        patient_ids, num_failing_patients, replace=False
    )

    failure_types = ["impedance", "threshold", "sensing", "battery"]
    rows_to_drop = []  # Track rows to drop after device explant

    logger.info(
        "Injecting degradation curves into %d patients...", num_failing_patients
    )

    for pid in failing_patient_ids:
        patient_mask = df["Patient_ID"] == pid
        patient_indices = df.index[patient_mask].to_numpy()

        # Pick a failure point (ensure they have at least 100 days of normal data first)
        fail_pos = np.random.randint(
            normal_data_points,
            len(patient_indices) - post_failure_buffer_points,
        )

        # Define the warning window (e.g., the device degrades over 14 days)
        degradation_days = 14 * pings_per_day
        start_deg_pos = fail_pos - degradation_days
        degradation_indices = patient_indices[start_deg_pos:fail_pos]

        # Label the 7 days prior to failure as our predictive target (The Danger Zone)
        target_start_pos = fail_pos - (7 * pings_per_day)
        target_end_pos = fail_pos
        target_indices = patient_indices[target_start_pos:target_end_pos]
        df.loc[target_indices, "Target_Fail_Next_7d"] = 1

        # Apply the gradual drift based on failure type
        fail_type = np.random.choice(failure_types)
        if fail_type == "impedance":
            # Impedance slowly climbs from ~500 to ~2500
            drift = np.linspace(0, 2000, degradation_days) + np.random.normal(
                0, 50, degradation_days
            )
            df.loc[degradation_indices, "Lead_Impedance_Ohms"] += drift

        elif fail_type == "battery":
            # Battery drops rapidly to 2.4V
            drift = np.linspace(0, 0.55, degradation_days) + np.random.normal(
                0, 0.02, degradation_days
            )
            df.loc[degradation_indices, "Battery_Voltage_V"] -= drift

        elif fail_type == "threshold":
            # Voltage needed to capture heart rises
            drift = np.linspace(0, 2.0, degradation_days) + np.random.normal(
                0, 0.1, degradation_days
            )
            df.loc[degradation_indices, "Capture_Threshold_V"] += drift

        elif fail_type == "sensing":
            # R-wave sensing quality degrades approaching failure
            drift = np.linspace(0, 8.5, degradation_days) + np.random.normal(
                0, 0.4, degradation_days
            )
            df.loc[degradation_indices, "R_Wave_Sensing_mV"] -= drift

        # The "Explant Rule": no telemetry at or after failure (device replaced immediately)
        rows_to_drop.extend(patient_indices[fail_pos:].tolist())

    # 4. Cleanup and Formatting
    logger.info("Applying Explant Rule (dropping post-failure data)...")
    df = df.drop(index=rows_to_drop).reset_index(drop=True)
    df = df.sort_values(["Timestamp", "Patient_ID"], kind="stable").reset_index(
        drop=True
    )

    df["Lead_Impedance_Ohms"] = np.round(df["Lead_Impedance_Ohms"], 2)
    df["Capture_Threshold_V"] = np.round(df["Capture_Threshold_V"], 2)
    df["R_Wave_Sensing_mV"] = np.round(df["R_Wave_Sensing_mV"], 2)
    df["Battery_Voltage_V"] = np.round(df["Battery_Voltage_V"], 2)

    # 5. Temporal Feature Engineering (patient-level rolling windows)
    window_3d = 3 * pings_per_day
    window_7d = 7 * pings_per_day

    grouped = df.groupby("Patient_ID", sort=False)

    df["Lead_Impedance_Ohms_RollingMean_3d"] = grouped["Lead_Impedance_Ohms"].transform(
        lambda series: series.rolling(window=window_3d, min_periods=1).mean()
    )
    df["Lead_Impedance_Ohms_RollingMean_7d"] = grouped["Lead_Impedance_Ohms"].transform(
        lambda series: series.rolling(window=window_7d, min_periods=1).mean()
    )
    df["Capture_Threshold_V_RollingMean_3d"] = grouped["Capture_Threshold_V"].transform(
        lambda series: series.rolling(window=window_3d, min_periods=1).mean()
    )
    df["Capture_Threshold_V_RollingMean_7d"] = grouped["Capture_Threshold_V"].transform(
        lambda series: series.rolling(window=window_7d, min_periods=1).mean()
    )
    df["Lead_Impedance_Ohms_DeltaPerDay_3d"] = grouped["Lead_Impedance_Ohms"].transform(
        lambda series: series.diff(periods=window_3d) / 3
    )
    df["Lead_Impedance_Ohms_DeltaPerDay_7d"] = grouped["Lead_Impedance_Ohms"].transform(
        lambda series: series.diff(periods=window_7d) / 7
    )
    df["Capture_Threshold_V_DeltaPerDay_3d"] = grouped["Capture_Threshold_V"].transform(
        lambda series: series.diff(periods=window_3d) / 3
    )
    df["Capture_Threshold_V_DeltaPerDay_7d"] = grouped["Capture_Threshold_V"].transform(
        lambda series: series.diff(periods=window_7d) / 7
    )

    # Round engineered features for cleaner output
    feature_columns = [
        "Lead_Impedance_Ohms_RollingMean_3d",
        "Lead_Impedance_Ohms_RollingMean_7d",
        "Capture_Threshold_V_RollingMean_3d",
        "Capture_Threshold_V_RollingMean_7d",
        "Lead_Impedance_Ohms_DeltaPerDay_3d",
        "Lead_Impedance_Ohms_DeltaPerDay_7d",
        "Capture_Threshold_V_DeltaPerDay_3d",
        "Capture_Threshold_V_DeltaPerDay_7d",
    ]
    df[feature_columns] = df[feature_columns].round(4)

    # 6. Export
    if save_csv:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info("Dataset saved to '%s'. Total rows: %d", output_path, len(df))

    return df


# Run the generator
if __name__ == "__main__":
    df_predictive = generate_predictive_telemetry()
