import math
from typing import Dict, Optional
from pydantic import BaseModel, Field
from app.schemas.timeseries import STLParameters


class CadenceConfig(BaseModel):
    """
    Configuration specification for a business cadence including minimum history requirements (§3.4).
    """
    cadence_name: str
    period: int = Field(..., description="Seasonal cycle period n_(p)")
    seasonal_window: int = Field(..., description="Loess window for seasonal component n_(s)")
    trend_window: int = Field(..., description="Loess window for trend component n_(t)")
    low_pass_window: int = Field(..., description="Low-pass filter window n_(l)")
    inner_iterations: int = Field(default=2, description="Inner loop iterations n_(i)")
    outer_iterations: int = Field(default=5, description="Outer robustness iterations n_(o)")
    min_history: int = Field(..., description="Minimum observations required for statistical stability N")
    robust: bool = Field(default=True, description="Enable Tukey bisquare reweighting")

    def to_stl_parameters(self) -> STLParameters:
        return STLParameters(
            period=self.period,
            seasonal_window=self.seasonal_window,
            trend_window=self.trend_window,
            low_pass_window=self.low_pass_window,
            inner_iterations=self.inner_iterations,
            outer_iterations=self.outer_iterations,
            robust=self.robust,
        )


def smallest_odd_ge(n: float) -> int:
    """Return smallest odd integer >= n."""
    n_int = int(math.ceil(n))
    return n_int if n_int % 2 != 0 else n_int + 1


def smallest_odd_gt(n: int) -> int:
    """Return smallest odd integer strictly > n (required for statsmodels low_pass filter)."""
    next_int = n + 1
    return next_int if next_int % 2 != 0 else next_int + 1


def calculate_cleveland_parameters(
    period: int,
    seasonal_window: Optional[int] = None,
    inner_iterations: int = 2,
    outer_iterations: int = 5,
    min_history: Optional[int] = None,
    cadence_name: str = "custom",
) -> CadenceConfig:
    """
    Dynamically compute Cleveland et al. (1990) harmonic separation parameters:
    - n_(l) = Smallest odd integer > n_(p) (statsmodels requirement for low-pass filter)
    - n_(t) >= (1.5 * n_(p)) / (1 - 1.5 / n_(s)), rounded up to next odd integer.
    """
    if period < 2:
        raise ValueError(f"Period n_(p) must be >= 2, got {period}")

    # Default seasonal window if not provided: smallest odd integer >= max(7, period)
    if seasonal_window is None:
        s_win = smallest_odd_ge(max(7, period + 1 if period % 2 == 0 else period))
    else:
        s_win = smallest_odd_ge(seasonal_window)

    if s_win <= 1.5:
        raise ValueError(f"Seasonal window n_(s) must be > 1.5, got {s_win}")

    # n_(l) = smallest odd integer > n_(p)
    low_pass = smallest_odd_gt(period)

    # n_(t) >= (1.5 * n_(p)) / (1 - 1.5 / n_(s)) rounded up to next odd integer
    raw_nt = (1.5 * period) / (1.0 - (1.5 / s_win))
    trend_win = smallest_odd_ge(raw_nt)

    # Min history default: at least 2 full seasonal cycles or 14 points
    if min_history is None:
        min_hist = max(14, 2 * period)
    else:
        min_hist = min_history

    return CadenceConfig(
        cadence_name=cadence_name.lower(),
        period=period,
        seasonal_window=s_win,
        trend_window=trend_win,
        low_pass_window=low_pass,
        inner_iterations=inner_iterations,
        outer_iterations=outer_iterations,
        min_history=min_hist,
        robust=True,
    )


# Authoritative Cadence Parameter Matrix Across 5 Business Cadences (§3.4)
CADENCE_REGISTRY: Dict[str, CadenceConfig] = {
    "hourly": CadenceConfig(
        cadence_name="hourly",
        period=24,
        seasonal_window=35,
        trend_window=39,
        low_pass_window=25,
        inner_iterations=2,
        outer_iterations=5,
        min_history=168,  # 7 days
        robust=True,
    ),
    "daily": CadenceConfig(
        cadence_name="daily",
        period=7,
        seasonal_window=13,
        trend_window=15,
        low_pass_window=9,  # Smallest odd integer > 7 (Cleveland/statsmodels requirement)
        inner_iterations=2,
        outer_iterations=5,
        min_history=60,  # 2 months
        robust=True,
    ),
    "weekly": CadenceConfig(
        cadence_name="weekly",
        period=52,
        seasonal_window=35,
        trend_window=83,
        low_pass_window=53,
        inner_iterations=2,
        outer_iterations=5,
        min_history=104,  # 2 years
        robust=True,
    ),
    "monthly": CadenceConfig(
        cadence_name="monthly",
        period=12,
        seasonal_window=19,
        trend_window=21,
        low_pass_window=13,
        inner_iterations=2,
        outer_iterations=5,
        min_history=36,  # 3 years
        robust=True,
    ),
    "quarterly": CadenceConfig(
        cadence_name="quarterly",
        period=4,
        seasonal_window=7,
        trend_window=9,
        low_pass_window=5,
        inner_iterations=2,
        outer_iterations=5,
        min_history=16,  # 4 years
        robust=True,
    ),
}

# Aliases for flexible cadence resolution
CADENCE_ALIASES: Dict[str, str] = {
    "hour": "hourly",
    "1h": "hourly",
    "h": "hourly",
    "day": "daily",
    "1d": "daily",
    "d": "daily",
    "week": "weekly",
    "1w": "weekly",
    "w": "weekly",
    "month": "monthly",
    "1m": "monthly",
    "m": "monthly",
    "quarter": "quarterly",
    "1q": "quarterly",
    "q": "quarterly",
}


def get_cadence_parameters(cadence: str) -> CadenceConfig:
    """
    Retrieve authoritative CadenceConfig for a given business cadence string.
    Supports case-insensitive lookups and standard cadence aliases.
    """
    normalized = cadence.strip().lower()
    canonical = CADENCE_ALIASES.get(normalized, normalized)

    if canonical in CADENCE_REGISTRY:
        return CADENCE_REGISTRY[canonical]

    raise ValueError(
        f"Unknown cadence '{cadence}'. Supported cadences: {list(CADENCE_REGISTRY.keys())}"
    )
