import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import math
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from scipy import stats

from app.schemas.movement import KPIMovementEvent
from app.timeseries.parameters import get_cadence_parameters, calculate_cleveland_parameters
from app.timeseries.stl import STLDecomposer
from app.timeseries.baseline import (
    compute_dynamic_baseline,
    compute_robust_residual_uncertainty,
    compute_confidence_bands,
)
from app.timeseries.anomaly import (
    compute_z_scores,
    evaluate_anomaly_condition,
    create_kpi_movement_event,
    run_stl_pipeline,
)


def generate_90day_synthetic_wave(seed: int = 42) -> pd.DataFrame:
    """
    Generate the deterministic 90-day synthetic benchmark dataset from §3.8:
    Y_t = (1000 + 5t) + 200*sin(2*pi*t/7) + eps_t + A_t
    where A_60 = -600.0, eps_t ~ N(0, 15^2)
    """
    print("[MOCK DATA] This output uses synthetic/simulated data. Replace with real ingested data.")
    np.random.seed(seed)
    n = 90
    t = np.arange(n)

    # Base components
    trend_true = 1000.0 + 5.0 * t
    seasonal_true = 200.0 * np.sin(2.0 * np.pi * t / 7.0)
    noise = np.random.normal(0.0, 15.0, n)

    # Anomaly injection at day 60
    anomaly = np.zeros(n)
    anomaly[60] = -600.0

    y = trend_true + seasonal_true + noise + anomaly

    base_time = datetime(2026, 1, 1, 0, 0, 0)
    timestamps = [base_time + timedelta(days=int(i)) for i in range(n)]

    return pd.DataFrame({
        "timestamp": timestamps,
        "value": y,
        "true_trend": trend_true,
        "true_seasonal": seasonal_true,
        "true_noise": noise,
        "anomaly": anomaly,
    })


def test_90day_synthetic_verification_wave():
    """
    Execute and verify all 5 objective mathematical pass/fail assertions from §3.8.
    """
    df = generate_90day_synthetic_wave(seed=42)
    decomposer = STLDecomposer(cadence="daily")
    result = decomposer.decompose(df)

    assert result["status"] == "SUCCESS", f"Expected SUCCESS but got {result['status']}"
    assert not result["diverted_to_bayesian"], "Should not divert 90-day series to Bayesian"

    trend_est = result["trend"]
    seasonal_est = result["seasonal"]
    resid_est = result["residual"]
    weights = result["weights"]

    # Assertion 1: Trend Orthogonality r(T_t, S_t) <= 0.05
    corr_ts, _ = stats.pearsonr(trend_est, seasonal_est)
    print(f"Assertion 1: Pearson r(T_t, S_t) = {corr_ts:.4f} (<= 0.05)")
    assert abs(corr_ts) <= 0.05, f"Trend orthogonality failed: r = {corr_ts}"

    # Assertion 2: Seasonal Amplitude Recovery |A_estimated - 200| <= 10.0
    # Amplitude is half the peak-to-trough range of the estimated seasonal component
    seasonal_amplitude = (np.max(seasonal_est) - np.min(seasonal_est)) / 2.0
    amp_diff = abs(seasonal_amplitude - 200.0)
    print(f"Assertion 2: Seasonal amplitude = {seasonal_amplitude:.2f}, diff = {amp_diff:.2f} (<= 10.0)")
    assert amp_diff <= 10.0, f"Seasonal amplitude recovery failed: diff = {amp_diff}"

    # Assertion 3: Outlier Neutralization (Tukey bisquare weight rho_60 <= 0.05, |T_hat_60 - 1300| <= 20.0)
    weight_60 = weights[60]
    trend_60 = trend_est[60]
    true_trend_60 = 1000.0 + 5.0 * 60.0  # 1300.0
    trend_diff_60 = abs(trend_60 - true_trend_60)
    print(f"Assertion 3: rho_60 = {weight_60:.4f} (<= 0.05), T_hat_60 = {trend_60:.2f}, diff = {trend_diff_60:.2f} (<= 20.0)")
    assert weight_60 <= 0.05, f"Outlier weight neutralization failed: rho_60 = {weight_60}"
    assert trend_diff_60 <= 20.0, f"Trend distortion at outlier failed: diff = {trend_diff_60}"

    # Assertion 4: Residual Normality (Shapiro-Wilk test on uncorrupted series residuals p >= 0.05)
    clean_series = df["true_trend"] + df["true_seasonal"] + df["true_noise"]
    clean_decomposer = STLDecomposer(cadence="daily", robust=False)
    clean_res = clean_decomposer.decompose(pd.DataFrame({"timestamp": df["timestamp"], "value": clean_series}))
    clean_residuals = clean_res["residual"]
    shapiro_stat, shapiro_p = stats.shapiro(clean_residuals)
    print(f"Assertion 4: Shapiro-Wilk p-value on uncorrupted residuals = {shapiro_p:.4f} (>= 0.05)")
    assert shapiro_p >= 0.05, f"Residual normality failed: p = {shapiro_p}"

    # Assertion 5: Anomaly Trigger (Z_60 <= -10.0 and emits KPIMovementEvent)
    pipeline_res = run_stl_pipeline(
        data=df,
        cadence="daily",
        tenant_id="tenant_alpha",
        kpi_id="daily_revenue",
    )

    dp_60 = pipeline_res.trend_data[60]
    print(f"Assertion 5: Z_60 = {dp_60.z_score:.2f} (<= -10.0), is_anomaly = {dp_60.is_anomaly}")
    assert dp_60.z_score <= -10.0, f"Z-score at Day 60 was not sufficiently extreme: Z = {dp_60.z_score}"
    assert dp_60.is_anomaly, "Day 60 should be flagged as an anomaly"

    # Verify KPIMovementEvent creation
    event = create_kpi_movement_event(
        kpi_id="daily_revenue",
        analysis_start=df["timestamp"].iloc[0],
        analysis_end=df["timestamp"].iloc[-1],
        observed_value=dp_60.actual_value,
        expected_value=dp_60.expected_value,
        z_score=dp_60.z_score,
        dimensions=["channel:Enterprise"],
    )
    assert isinstance(event, KPIMovementEvent)
    assert event.materiality_status == "MATERIAL_ANOMALY"
    assert event.observed_value < event.expected_value
    print("All 5 §3.8 assertions passed perfectly!")


def test_cadence_parameters_matrix():
    """Verify all 5 business cadences satisfy Cleveland harmonic separation formulas."""
    cadences = ["hourly", "daily", "weekly", "monthly", "quarterly"]
    for cad in cadences:
        config = get_cadence_parameters(cad)
        assert config.period >= 2
        assert config.seasonal_window % 2 == 1
        assert config.trend_window % 2 == 1
        assert config.low_pass_window % 2 == 1
        # Cleveland constraint: n_(t) >= 1.5 * n_(p) / (1 - 1.5 / n_(s))
        cleveland_min_nt = (1.5 * config.period) / (1.0 - 1.5 / config.seasonal_window)
        assert config.trend_window >= math.floor(cleveland_min_nt)


def test_sparse_history_bayesian_diversion():
    """Verify series with N < 2*period diverts to Bayesian prior."""
    short_data = [100.0, 105.0, 98.0, 102.0, 99.0]
    pipeline_res = run_stl_pipeline(
        data=short_data,
        cadence="daily",  # period = 7 -> min required 14
        kpi_id="new_kpi",
    )
    assert pipeline_res.diverted_to_bayesian
    assert pipeline_res.status == "SPARSE_HISTORY_DIVERTED"


if __name__ == "__main__":
    print("Running STL Timeseries Test Suite...")
    test_cadence_parameters_matrix()
    test_sparse_history_bayesian_diversion()
    test_90day_synthetic_verification_wave()
    print("Test Suite Completed Successfully!")
