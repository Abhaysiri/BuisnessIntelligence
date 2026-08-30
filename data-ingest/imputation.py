"""
Time-Series Regularization & Imputation Hierarchy (§2.5)
Enforces a continuous temporal grid and fills missing observations:
- Gap length g <= 3: Vectorized Akima cubic spline interpolation (scipy.interpolate.Akima1DInterpolator) or linear fallback.
- Gap length 3 < g <= period: Seasonal persistence (Y_t = Y_{t - period}).
- Gap length g > 0.20 * N (or >20% missingness): Series rejected from automated STL, triggers cold-start Bayesian prior mode.
- All imputed records permanently marked with is_imputed = True.
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import polars as pl
from scipy.interpolate import Akima1DInterpolator


CADENCE_PERIOD_MAP = {
    "hourly": 24,    # 24 hours in a day
    "1h": 24,
    "daily": 7,      # 7 days in a week
    "1d": 7,
    "weekly": 52,    # 52 weeks in a year (or 4 for monthly cycle)
    "1w": 52,
    "monthly": 12,   # 12 months in a year
    "1m": 12,
    "quarterly": 4,  # 4 quarters in a year
    "1q": 4,
}

CADENCE_FREQ_STR = {
    "hourly": "1h",
    "1h": "1h",
    "daily": "1D",
    "1d": "1D",
    "weekly": "7D",
    "1w": "7D",
    "monthly": "MS",
    "1m": "MS",
    "quarterly": "QS",
    "1q": "QS",
}


class TimeSeriesImputer:
    """
    Time-series regularizer and hierarchical imputer.
    """

    def __init__(self, cadence: str = "daily", seasonal_period: Optional[int] = None):
        self.cadence = cadence.lower()
        self.seasonal_period = seasonal_period or CADENCE_PERIOD_MAP.get(self.cadence, 7)
        self.freq_str = CADENCE_FREQ_STR.get(self.cadence, "1D")

    def regularize_and_impute(
        self,
        df_or_records: Union[pl.DataFrame, pd.DataFrame, List[Dict[str, Any]]],
        tenant_id: Optional[str] = None,
        kpi_id: Optional[str] = None,
    ) -> Tuple[pl.DataFrame, Dict[str, Any]]:
        """
        Regularize time series onto a complete temporal grid and execute hierarchical imputation.
        Returns:
            (imputed_df, imputation_summary_dict)
        """
        # Convert input to pandas for flexible temporal indexing & interpolation math
        if isinstance(df_or_records, pl.DataFrame):
            pdf = pd.DataFrame(df_or_records.to_dicts())
        elif isinstance(df_or_records, list):
            pdf = pd.DataFrame(df_or_records)
        elif isinstance(df_or_records, pd.DataFrame):
            pdf = df_or_records.copy()
        else:
            raise TypeError(f"Unsupported type: {type(df_or_records)}")

        if pdf.empty:
            empty_pl = pl.DataFrame(
                schema={
                    "tenant_id": pl.Utf8,
                    "kpi_id": pl.Utf8,
                    "observed_at": pl.Datetime("ms", "UTC"),
                    "observed_at_str": pl.Utf8,
                    "value": pl.Float64,
                    "dimensions": pl.Utf8,
                    "dim_hash": pl.Utf8,
                    "is_imputed": pl.Boolean,
                }
            )
            return empty_pl, {
                "total_points": 0,
                "missing_count": 0,
                "missing_ratio": 0.0,
                "max_gap": 0,
                "stl_eligible": False,
                "cold_start_bayesian_trigger": True,
                "imputation_method": "none",
            }

        # Ensure observed_at is datetime
        pdf["observed_at"] = pd.to_datetime(pdf["observed_at"], utc=True)
        pdf = pdf.sort_values("observed_at").drop_duplicates(subset=["observed_at"])

        # Extract tenant and kpi ids
        t_id = tenant_id or (pdf["tenant_id"].iloc[0] if "tenant_id" in pdf.columns and pd.notna(pdf["tenant_id"].iloc[0]) else "unknown_tenant")
        k_id = kpi_id or (pdf["kpi_id"].iloc[0] if "kpi_id" in pdf.columns and pd.notna(pdf["kpi_id"].iloc[0]) else "unknown_kpi")

        min_time = pdf["observed_at"].min()
        max_time = pdf["observed_at"].max()

        # Build full temporal grid
        full_grid = pd.date_range(start=min_time, end=max_time, freq=self.freq_str, tz="UTC")
        if len(full_grid) == 0:
            full_grid = pdf["observed_at"].values

        grid_df = pd.DataFrame({"observed_at": full_grid})
        merged = pd.merge(grid_df, pdf, on="observed_at", how="left")

        merged["tenant_id"] = t_id
        merged["kpi_id"] = k_id
        if "dimensions" not in merged.columns or merged["dimensions"].isna().all():
            merged["dimensions"] = "{}"
        else:
            merged["dimensions"] = merged["dimensions"].fillna("{}")

        if "dim_hash" not in merged.columns:
            merged["dim_hash"] = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        else:
            merged["dim_hash"] = merged["dim_hash"].fillna("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")

        if "is_imputed" not in merged.columns:
            merged["is_imputed"] = False
        else:
            merged["is_imputed"] = merged["is_imputed"].fillna(False).astype(bool)

        # Identify missingness
        values = merged["value"].to_numpy(dtype=float)
        n_total = len(values)
        is_missing = np.isnan(values)
        missing_count = int(np.sum(is_missing))
        missing_ratio = float(missing_count / n_total) if n_total > 0 else 0.0

        # Compute contiguous gap runs
        gaps: List[Tuple[int, int]] = []  # (start_idx, end_idx) inclusive
        in_gap = False
        gap_start = 0
        max_gap = 0

        for i, m in enumerate(is_missing):
            if m and not in_gap:
                in_gap = True
                gap_start = i
            elif not m and in_gap:
                in_gap = False
                gap_len = i - gap_start
                gaps.append((gap_start, i - 1))
                if gap_len > max_gap:
                    max_gap = gap_len
        if in_gap:
            gap_len = n_total - gap_start
            gaps.append((gap_start, n_total - 1))
            if gap_len > max_gap:
                max_gap = gap_len

        # Check STL eligibility (§2.5: g > 0.20 * N or missing_ratio > 0.20 triggers cold-start Bayesian prior mode)
        stl_eligible = True
        cold_start_bayesian_trigger = False

        if n_total < 7:
            stl_eligible = False
            cold_start_bayesian_trigger = True
        elif max_gap > (0.20 * n_total) or missing_ratio > 0.20:
            stl_eligible = False
            cold_start_bayesian_trigger = True

        # Perform hierarchical imputation
        imputed_values = values.copy()
        valid_indices = np.where(~is_missing)[0]

        if missing_count > 0 and len(valid_indices) >= 2:
            # Check each gap individually according to hierarchy
            for start_idx, end_idx in gaps:
                gap_len = end_idx - start_idx + 1

                if gap_len <= 3:
                    # Strategy 1: Akima cubic spline interpolation (or linear fallback if insufficient points)
                    if len(valid_indices) >= 5:
                        try:
                            akima = Akima1DInterpolator(valid_indices, values[valid_indices])
                            gap_range = np.arange(start_idx, end_idx + 1)
                            interp_vals = akima(gap_range)
                            # Guard against extrapolation NaNs
                            if np.any(np.isnan(interp_vals)):
                                s = pd.Series(imputed_values)
                                interp_vals = s.interpolate(method="linear").iloc[gap_range].to_numpy()
                            imputed_values[gap_range] = interp_vals
                        except Exception:
                            s = pd.Series(imputed_values)
                            imputed_values[start_idx : end_idx + 1] = s.interpolate(method="linear").iloc[start_idx : end_idx + 1].to_numpy()
                    else:
                        s = pd.Series(imputed_values)
                        imputed_values[start_idx : end_idx + 1] = s.interpolate(method="linear").iloc[start_idx : end_idx + 1].to_numpy()

                elif 3 < gap_len <= self.seasonal_period:
                    # Strategy 2: Seasonal persistence Y_t = Y_{t - period}
                    for g_i in range(start_idx, end_idx + 1):
                        lookback_idx = g_i - self.seasonal_period
                        if lookback_idx >= 0 and not np.isnan(imputed_values[lookback_idx]):
                            imputed_values[g_i] = imputed_values[lookback_idx]
                        else:
                            # Forward persistence fallback or linear
                            if g_i > 0 and not np.isnan(imputed_values[g_i - 1]):
                                imputed_values[g_i] = imputed_values[g_i - 1]
                            elif len(valid_indices) > 0:
                                imputed_values[g_i] = values[valid_indices[0]]

                else:
                    # Strategy 3: Large gap (> period or > 0.20*N). Use rolling baseline or linear fill to avoid crashing
                    s = pd.Series(imputed_values)
                    imputed_values[start_idx : end_idx + 1] = s.interpolate(method="linear").bfill().ffill().iloc[start_idx : end_idx + 1].to_numpy()

            # Any residual NaNs bfill/ffill
            s = pd.Series(imputed_values).bfill().ffill()
            imputed_values = s.to_numpy()

        elif missing_count > 0 and len(valid_indices) == 1:
            # Single point: constant fill
            imputed_values[:] = values[valid_indices[0]]

        # Update values and is_imputed flags
        merged["value"] = imputed_values
        merged["is_imputed"] = merged["is_imputed"] | is_missing
        merged["observed_at_str"] = merged["observed_at"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Convert back to Polars
        pl_df = pl.from_pandas(merged[[
            "tenant_id",
            "kpi_id",
            "observed_at",
            "observed_at_str",
            "value",
            "dimensions",
            "dim_hash",
            "is_imputed",
        ]])

        summary = {
            "total_points": n_total,
            "missing_count": missing_count,
            "missing_ratio": round(missing_ratio, 4),
            "max_gap": max_gap,
            "stl_eligible": stl_eligible,
            "cold_start_bayesian_trigger": cold_start_bayesian_trigger,
            "cadence": self.cadence,
            "seasonal_period": self.seasonal_period,
        }

        return pl_df, summary
