from typing import Tuple, Union
import numpy as np


def compute_dynamic_baseline(
    trend: Union[np.ndarray, list],
    seasonal: Union[np.ndarray, list],
) -> np.ndarray:
    """
    Phase-Aligned Dynamic Expected Baseline (§3.5):
    Ŷ_t = T_t + S_t
    """
    t_arr = np.asarray(trend, dtype=float)
    s_arr = np.asarray(seasonal, dtype=float)
    return t_arr + s_arr


def compute_robust_residual_uncertainty(
    residuals: Union[np.ndarray, list],
    min_floor: float = 1e-6,
) -> float:
    """
    Robust Residual Uncertainty (σ_R) via Median Absolute Deviation (MAD) (§3.5):
    σ_R = 1.4826 * MAD(R_t) = 1.4826 * median(|R_t - median(R_t)|)
    Prevents variance inflation from extreme isolated anomaly excursions.
    """
    r_arr = np.asarray(residuals, dtype=float)
    if len(r_arr) == 0:
        return min_floor

    # Filter out NaNs/Infs
    valid_r = r_arr[np.isfinite(r_arr)]
    if len(valid_r) == 0:
        return min_floor

    med = np.median(valid_r)
    mad = np.median(np.abs(valid_r - med))
    sigma_r = 1.4826 * mad

    # Fallback to standard deviation if MAD collapses to zero
    if sigma_r < min_floor:
        std_val = float(np.std(valid_r))
        sigma_r = max(std_val, min_floor)

    return float(sigma_r)


def compute_confidence_bands(
    expected: Union[np.ndarray, list],
    sigma_r: float,
    z_value: float = 2.576,  # 99% confidence level (alpha = 0.01)
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Dynamic Confidence Interval Bands (§3.5):
    [Lower_t, Upper_t] = [Ŷ_t - z * σ_R, Ŷ_t + z * σ_R]
    """
    exp_arr = np.asarray(expected, dtype=float)
    margin = z_value * sigma_r
    lower_bound = exp_arr - margin
    upper_bound = exp_arr + margin
    return lower_bound, upper_bound
