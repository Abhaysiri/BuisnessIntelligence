from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4
import numpy as np
import pandas as pd

from app.schemas.movement import KPIMovementEvent
from app.schemas.timeseries import STLDecompositionResult, STLParameters, TrendDataPoint
from app.timeseries.baseline import compute_confidence_bands, compute_dynamic_baseline, compute_robust_residual_uncertainty
from app.timeseries.stl import STLDecomposer


def compute_z_scores(
    actual: Union[np.ndarray, list],
    expected: Union[np.ndarray, list],
    sigma_r: float,
) -> np.ndarray:
    """
    Statistical Anomaly Z-Score (§3.5):
    Z_t = (Y_t - Ŷ_t) / σ_R
    """
    y_arr = np.asarray(actual, dtype=float)
    y_hat_arr = np.asarray(expected, dtype=float)
    denom = max(sigma_r, 1e-6)
    return (y_arr - y_hat_arr) / denom


def evaluate_anomaly_condition(
    actual: float,
    expected: float,
    z_score: float,
    z_threshold: float = 2.576,
    materiality_threshold: float = 0.05,
) -> Tuple[bool, str]:
    """
    Evaluate Investigation Triggering Condition (§3.5):
    Emits anomaly if and only if |Z_t| >= 2.576 AND |(Y_t - Ŷ_t) / Ŷ_t| >= 0.05.
    Returns (is_anomaly, materiality_status).
    """
    stat_sig = abs(z_score) >= z_threshold

    denom = abs(expected) if abs(expected) > 1e-9 else 1.0
    pct_delta = abs(actual - expected) / denom
    material = pct_delta >= materiality_threshold

    if stat_sig and material:
        status = "MATERIAL_ANOMALY"
        is_anomaly = True
    elif stat_sig and not material:
        status = "STAT_SIG_IMMATERIAL"
        is_anomaly = False
    elif not stat_sig and material:
        status = "SUB_CRITICAL_DEVIATION"
        is_anomaly = False
    else:
        status = "WITHIN_NORMAL_BOUNDS"
        is_anomaly = False

    return is_anomaly, status


def create_kpi_movement_event(
    kpi_id: str,
    analysis_start: datetime,
    analysis_end: datetime,
    observed_value: float,
    expected_value: float,
    z_score: float,
    dimensions: Optional[List[str]] = None,
    event_id: Optional[str] = None,
) -> KPIMovementEvent:
    """
    Constructs a validated KPIMovementEvent instance (§3.1, §3.5) for LangGraph swarm ingestion.
    """
    abs_change = float(observed_value - expected_value)
    denom = abs(expected_value) if abs(expected_value) > 1e-9 else 1.0
    pct_change = float((observed_value - expected_value) / denom)

    _, status = evaluate_anomaly_condition(
        actual=observed_value,
        expected=expected_value,
        z_score=z_score,
    )

    return KPIMovementEvent(
        event_id=event_id or f"evt_{uuid4().hex[:12]}",
        kpi_id=kpi_id,
        analysis_start=analysis_start,
        analysis_end=analysis_end,
        observed_value=observed_value,
        expected_value=expected_value,
        absolute_change=abs_change,
        percentage_change=pct_change,
        statistical_score=float(z_score),
        materiality_status=status,
        dimensions=dimensions or [],
    )


def run_stl_pipeline(
    data: Union[pd.Series, pd.DataFrame, List[float], List[Dict[str, Any]], np.ndarray, Any],
    cadence: str = "daily",
    tenant_id: str = "default_tenant",
    kpi_id: str = "default_kpi",
    custom_params: Optional[STLParameters] = None,
    use_log_transform: bool = False,
    z_threshold: float = 2.576,
    materiality_threshold: float = 0.05,
    timestamp_col: str = "timestamp",
    value_col: str = "value",
) -> STLDecompositionResult:
    """
    End-to-end STL pipeline execution:
    1. STL decomposition (Cleveland LOESS)
    2. Dynamic expected baseline (Ŷ_t = T_t + S_t)
    3. Robust residual uncertainty (MAD σ_R)
    4. 99% confidence interval bands
    5. Z-scores and anomaly trigger evaluations
    Returns STLDecompositionResult.
    """
    decomposer = STLDecomposer(
        cadence=cadence,
        custom_params=custom_params,
        use_log_transform=use_log_transform,
    )

    decomp = decomposer.decompose(
        data=data,
        timestamp_col=timestamp_col,
        value_col=value_col,
    )

    actuals = decomp["actual"]
    trends = decomp["trend"]
    seasonals = decomp["seasonal"]
    residuals = decomp["residual"]
    timestamps = decomp["timestamps"]
    n_points = decomp["observed_points"]

    # Compute baseline and uncertainty
    expected = compute_dynamic_baseline(trends, seasonals)
    sigma_r = compute_robust_residual_uncertainty(residuals)
    lower_bounds, upper_bounds = compute_confidence_bands(expected, sigma_r, z_threshold)
    z_scores = compute_z_scores(actuals, expected, sigma_r)

    # Build trend data points
    trend_points: List[TrendDataPoint] = []
    any_anomaly = False

    for i in range(n_points):
        ts = timestamps[i] if i < len(timestamps) else datetime.now(timezone.utc)
        act = float(actuals[i])
        tr = float(trends[i])
        sea = float(seasonals[i])
        res = float(residuals[i])
        exp = float(expected[i])
        lb = float(lower_bounds[i])
        ub = float(upper_bounds[i])
        z = float(z_scores[i])

        is_anom, _ = evaluate_anomaly_condition(
            actual=act,
            expected=exp,
            z_score=z,
            z_threshold=z_threshold,
            materiality_threshold=materiality_threshold,
        )
        if is_anom:
            any_anomaly = True

        trend_points.append(
            TrendDataPoint(
                timestamp=ts,
                actual_value=act,
                trend_value=tr,
                seasonal_value=sea,
                residual_value=res,
                expected_value=exp,
                lower_bound=lb,
                upper_bound=ub,
                is_anomaly=is_anom,
                z_score=z,
            )
        )

    latest_act = float(actuals[-1]) if n_points > 0 else 0.0
    latest_exp = float(expected[-1]) if n_points > 0 else 0.0
    latest_z = float(z_scores[-1]) if n_points > 0 else 0.0

    return STLDecompositionResult(
        tenant_id=tenant_id,
        kpi_id=kpi_id,
        cadence=cadence,
        observed_points=n_points,
        residual_std=sigma_r,
        trend_data=trend_points,
        latest_expected=latest_exp,
        latest_actual=latest_act,
        latest_z_score=latest_z,
        anomaly_detected=any_anomaly,
        diverted_to_bayesian=decomp.get("diverted_to_bayesian", False),
        status=decomp.get("status", "SUCCESS"),
        message=decomp.get("message"),
    )
