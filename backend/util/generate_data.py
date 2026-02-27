import time
import uuid
from pathlib import Path

import numpy as np
import pandas as pd


def generate_predictive_telemetry(
    num_patients=1000,
    pings_per_day=1,
    num_days=1825,
    failure_rate=0.05,
    filename="pacemaker_data.csv",
    save_csv=True,
):
    """
    Generate synthetic pacemaker telemetry time-series data for predictive maintenance modeling.

    The function creates a chronological baseline of healthy device metrics for each patient, injects
    realistic multi-day degradation curves for a subset of failing devices, labels the 7-day pre-failure
    warning window (`Target_Fail_Next_7d`), applies an explant rule to remove post-failure records,
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

    Args:
        num_patients (int, optional): Number of patients to simulate data from. Defaults to 1000.
        pings_per_day (int, optional): Number of telemetry pings per day. Defaults to 1.
        num_days (int, optional): Number of days of data to generate. Defaults to 1825.
        failure_rate (float, optional): Proportion of patients that will experience device failure. Defaults to 0.05.
        filename (str, optional): Name of the output CSV file. Relative paths are saved under ./data. Defaults to "pacemaker_data.csv".
        save_csv (bool, optional): Whether to save the generated data to a CSV file. Defaults to True.

    Returns:
        pd.DataFrame: A synthetic telemetry dataset with baseline signals, failure labels,
        and engineered rolling/trend features.
    """
    print( 
        f"Generating predictive data for {num_patients} patients over {num_days} days..."
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
        output_path = Path("data") / output_path

    # Ensure we have enough data points to support failure injection and the predictive target window
    total_points_per_patient = num_days * pings_per_day
    min_points_required_for_failure_injection = 111
    if (
        total_points_per_patient < min_points_required_for_failure_injection
        and failure_rate > 0
    ):
        raise ValueError(
            "num_days * pings_per_day must be at least 111 when failure_rate > 0 "
            "to support degradation and target windows."
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
        [patient_ids, timestamps], names=["Patient_ID", "Timestamp"]
    )
    df = pd.DataFrame(index=idx).reset_index()

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

    print(f"Injecting degradation curves into {num_failing_patients} patients...")

    for pid in failing_patient_ids:
        patient_mask = df["Patient_ID"] == pid
        patient_indices = df[patient_mask].index

        # Pick a failure day (ensure they have at least 100 days of normal data first)
        fail_idx = np.random.choice(patient_indices[100:-10])

        # Define the warning window (e.g., the device degrades over 14 days)
        degradation_days = 14 * pings_per_day
        start_deg_idx = fail_idx - degradation_days

        # Label the 7 days prior to failure as our predictive target (The Danger Zone)
        target_start_idx = fail_idx - (7 * pings_per_day)
        df.loc[target_start_idx:fail_idx, "Target_Fail_Next_7d"] = 1

        # Apply the gradual drift based on failure type
        fail_type = np.random.choice(failure_types)
        if fail_type == "impedance":
            # Impedance slowly climbs from ~500 to ~2500
            drift = np.linspace(0, 2000, degradation_days) + np.random.normal(
                0, 50, degradation_days
            )
            df.loc[start_deg_idx : fail_idx - 1, "Lead_Impedance_Ohms"] += drift
            # Hard failure
            df.loc[fail_idx:, "Lead_Impedance_Ohms"] = np.random.uniform(
                2500.0, 3000.0, size=len(df.loc[fail_idx:])
            )

        elif fail_type == "battery":
            # Battery drops rapidly to 2.4V
            drift = np.linspace(0, 0.55, degradation_days) + np.random.normal(
                0, 0.02, degradation_days
            )
            df.loc[start_deg_idx : fail_idx - 1, "Battery_Voltage_V"] -= drift
            df.loc[fail_idx:, "Battery_Voltage_V"] = np.random.uniform(
                2.20, 2.40, size=len(df.loc[fail_idx:])
            )

        elif fail_type == "threshold":
            # Voltage needed to capture heart rises
            drift = np.linspace(0, 2.0, degradation_days) + np.random.normal(
                0, 0.1, degradation_days
            )
            df.loc[start_deg_idx : fail_idx - 1, "Capture_Threshold_V"] += drift
            df.loc[fail_idx:, "Capture_Threshold_V"] = np.random.uniform(
                2.50, 3.50, size=len(df.loc[fail_idx:])
            )

        elif fail_type == "sensing":
            # R-wave sensing quality degrades and then collapses after failure
            drift = np.linspace(0, 8.5, degradation_days) + np.random.normal(
                0, 0.4, degradation_days
            )
            df.loc[start_deg_idx : fail_idx - 1, "R_Wave_Sensing_mV"] -= drift
            df.loc[fail_idx:, "R_Wave_Sensing_mV"] = np.random.uniform(
                0.2, 2.0, size=len(df.loc[fail_idx:])
            )

        # The "Explant Rule": Mark data 3 days after failure to be dropped (device was replaced)
        drop_start_idx = fail_idx + (3 * pings_per_day)
        rows_to_drop.extend(range(drop_start_idx, patient_indices[-1] + 1))

    # 4. Cleanup and Formatting
    print("Applying Explant Rule (dropping post-failure data)...")
    df = df.drop(index=rows_to_drop).reset_index(drop=True)

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
        print(f"Dataset saved to '{output_path}'. Total rows: {len(df):,}")

    return df


# Run the generator
if __name__ == "__main__":
    df_predictive = generate_predictive_telemetry()
