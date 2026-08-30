from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import STL

from app.schemas.timeseries import STLParameters
from app.timeseries.parameters import CadenceConfig, get_cadence_parameters, smallest_odd_gt, smallest_odd_ge


class STLDecomposer:
    """
    Production STL Decomposition Engine wrapping statsmodels.tsa.seasonal.STL (§3.1-3.5).
    Handles cadence tuning, log transformations, missing value imputation, and sparse history detection.
    """

    def __init__(
        self,
        cadence: str = "daily",
        custom_params: Optional[STLParameters] = None,
        use_log_transform: bool = False,
        robust: Optional[bool] = None,
    ):
        self.cadence = cadence.lower()
        self.use_log_transform = use_log_transform

        if custom_params is not None:
            self.params = custom_params.model_copy() if hasattr(custom_params, 'model_copy') else custom_params.copy()
            if robust is not None:
                self.params.robust = robust
            self.cadence_config = CadenceConfig(
                cadence_name="custom",
                period=custom_params.period,
                seasonal_window=custom_params.seasonal_window,
                trend_window=custom_params.trend_window,
                low_pass_window=custom_params.low_pass_window,
                inner_iterations=custom_params.inner_iterations,
                outer_iterations=custom_params.outer_iterations if self.params.robust else 0,
                min_history=max(14, 2 * custom_params.period),
                robust=self.params.robust,
            )
        else:
            base_config = get_cadence_parameters(self.cadence)
            self.cadence_config = base_config.model_copy() if hasattr(base_config, 'model_copy') else base_config.copy()
            if robust is not None:
                self.cadence_config.robust = robust
            self.params = self.cadence_config.to_stl_parameters()

    def _prepare_series(
        self,
        data: Union[pd.Series, pd.DataFrame, List[float], List[Dict[str, Any]], np.ndarray, Any],
        timestamp_col: str = "timestamp",
        value_col: str = "value",
    ) -> Tuple[pd.Series, List[datetime], bool]:
        """
        Normalize incoming data structures into a clean pd.Series with DatetimeIndex.
        Returns (series, timestamps_list, is_sparse_flag).
        """
        # Handle Polars DataFrame / Series by converting to Pandas
        if hasattr(data, "to_pandas"):
            data = data.to_pandas()

        if isinstance(data, pd.DataFrame):
            if timestamp_col in data.columns and value_col in data.columns:
                df = data[[timestamp_col, value_col]].copy()
                df[timestamp_col] = pd.to_datetime(df[timestamp_col])
                df = df.sort_values(by=timestamp_col).reset_index(drop=True)
                timestamps = df[timestamp_col].tolist()
                series = pd.Series(df[value_col].values, index=df[timestamp_col], dtype=float)
            else:
                numeric_cols = data.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    val_col = numeric_cols[0]
                    series = pd.Series(data[val_col].values, dtype=float)
                    timestamps = [datetime.now(timezone.utc) for _ in range(len(series))]
                else:
                    raise ValueError("Provided DataFrame contains no numeric measurement column")
        elif isinstance(data, pd.Series):
            series = data.astype(float)
            if isinstance(series.index, pd.DatetimeIndex):
                timestamps = series.index.to_pydatetime().tolist()
            else:
                timestamps = [datetime.now(timezone.utc) for _ in range(len(series))]
        elif isinstance(data, list):
            if len(data) == 0:
                raise ValueError("Input time series data list is empty")
            if isinstance(data[0], dict):
                ts_list = []
                val_list = []
                for item in data:
                    t_val = item.get(timestamp_col) or item.get("observed_at") or item.get("date")
                    v_val = item.get(value_col) or item.get("val") or item.get("y")
                    if t_val is not None:
                        ts_list.append(pd.to_datetime(t_val))
                    else:
                        ts_list.append(datetime.now(timezone.utc))
                    val_list.append(float(v_val) if v_val is not None else np.nan)
                timestamps = ts_list
                series = pd.Series(val_list, dtype=float)
            else:
                val_list = [float(v) if v is not None else np.nan for v in data]
                timestamps = [datetime.now(timezone.utc) for _ in range(len(val_list))]
                series = pd.Series(val_list, dtype=float)
        elif isinstance(data, np.ndarray):
            series = pd.Series(data.flatten(), dtype=float)
            timestamps = [datetime.now(timezone.utc) for _ in range(len(series))]
        else:
            raise TypeError(f"Unsupported data type for STL decomposition: {type(data)}")

        n_points = len(series)
        min_required = max(14, 2 * self.params.period)
        is_sparse = (n_points < min_required)

        return series, timestamps, is_sparse

    def _impute_missing_values(self, series: pd.Series, period: int) -> Tuple[pd.Series, bool]:
        """
        Missingness imputation hierarchy (§2.5, §3.7):
        - Gap length g <= 3: Akima / linear interpolation
        - Gap length 3 < g <= n_(p): Seasonal persistence lag (Y_t = Y_{t - n_(p)})
        - Gap ratio > 20%: Flag as sparse/diverted to Bayesian prior.
        """
        nan_count = series.isna().sum()
        total_count = len(series)

        if total_count == 0:
            return series, True

        nan_ratio = nan_count / total_count
        if nan_ratio > 0.20:
            # Series rejected from standard STL; divert to Bayesian prior
            return series.bfill().ffill().fillna(0.0), True

        if nan_count == 0:
            return series, False

        filled = series.copy()
        
        # Step 1: Seasonal lag persistence for larger interior missing blocks
        if period > 0 and len(filled) >= period:
            seasonal_lag = filled.shift(period)
            filled = filled.fillna(seasonal_lag)

        # Step 2: Linear/Akima interpolation for small gaps (g <= 3) and remaining NaNs
        try:
            filled = filled.interpolate(method="akima", limit_direction="both")
        except Exception:
            filled = filled.interpolate(method="linear", limit_direction="both")

        # Step 3: Edge boundary fills
        filled = filled.bfill().ffill().fillna(0.0)

        return filled, False

    def decompose(
        self,
        data: Union[pd.Series, pd.DataFrame, List[float], List[Dict[str, Any]], np.ndarray, Any],
        timestamp_col: str = "timestamp",
        value_col: str = "value",
    ) -> Dict[str, Any]:
        """
        Execute robust STL decomposition returning trend, seasonal, residual, weights, and metadata.
        """
        raw_series, timestamps, is_sparse = self._prepare_series(data, timestamp_col, value_col)
        n_points = len(raw_series)

        # Check for sparse history or extreme missingness
        clean_series, missing_reject = self._impute_missing_values(raw_series, self.params.period)
        diverted = is_sparse or missing_reject

        if diverted:
            # Fallback baseline when series is too sparse for STL
            mean_val = float(clean_series.mean()) if n_points > 0 else 0.0
            std_val = float(clean_series.std()) if n_points > 1 else 1.0
            actual_vals = clean_series.values.astype(float)
            trend_vals = np.full(n_points, mean_val, dtype=float)
            seasonal_vals = np.zeros(n_points, dtype=float)
            residual_vals = actual_vals - mean_val
            weights_vals = np.ones(n_points, dtype=float)

            return {
                "timestamps": timestamps,
                "actual": actual_vals,
                "trend": trend_vals,
                "seasonal": seasonal_vals,
                "residual": residual_vals,
                "weights": weights_vals,
                "diverted_to_bayesian": True,
                "status": "SPARSE_HISTORY_DIVERTED",
                "message": f"Time series contains insufficient history (N={n_points} < {2 * self.params.period}) or >20% missingness. Diverted to Bayesian prior borrowing (§4.3).",
                "observed_points": n_points,
            }

        # Multiplicative log transform if requested
        log_shift = 0.0
        work_values = clean_series.values.copy()
        if self.use_log_transform:
            min_val = np.min(work_values)
            if min_val <= 0:
                log_shift = abs(min_val) + 1.0
            work_values = np.log(work_values + log_shift)

        # Ensure low_pass > period for statsmodels requirement
        low_pass = self.params.low_pass_window
        if low_pass <= self.params.period:
            low_pass = smallest_odd_gt(self.params.period)

        # Configure and execute statsmodels STL
        outer_iter_val = self.params.outer_iterations if self.params.robust else 0
        stl_model = STL(
            endog=pd.Series(work_values),
            period=self.params.period,
            seasonal=self.params.seasonal_window,
            trend=self.params.trend_window,
            low_pass=low_pass,
            robust=self.params.robust,
        )

        res = stl_model.fit(
            inner_iter=self.params.inner_iterations,
            outer_iter=outer_iter_val,
        )

        trend_arr = np.array(res.trend, dtype=float)
        seasonal_arr = np.array(res.seasonal, dtype=float)
        residual_arr = np.array(res.resid, dtype=float)

        weights_attr = getattr(res, "weights", None)
        if weights_attr is not None:
            weights_arr = np.array(weights_attr, dtype=float)
        else:
            weights_arr = np.ones(n_points, dtype=float)

        # Invert log transform if applied
        if self.use_log_transform:
            actual_arr = clean_series.values.astype(float)
            exp_trend = np.exp(trend_arr) - log_shift
            exp_expected = np.exp(trend_arr + seasonal_arr) - log_shift
            seasonal_arr = exp_expected - exp_trend
            trend_arr = exp_trend
            residual_arr = actual_arr - (trend_arr + seasonal_arr)
        else:
            actual_arr = clean_series.values.astype(float)

        return {
            "timestamps": timestamps,
            "actual": actual_arr,
            "trend": trend_arr,
            "seasonal": seasonal_arr,
            "residual": residual_arr,
            "weights": weights_arr,
            "diverted_to_bayesian": False,
            "status": "SUCCESS",
            "message": "STL decomposition completed successfully",
            "observed_points": n_points,
        }
