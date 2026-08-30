from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class STLParameters(BaseModel):
    """
    Parameter specification for Cleveland LOESS & 2-Loop STL Decomposition (§3.4).
    """
    period: int = Field(..., ge=2, description="Seasonal cycle period n_(p)")
    seasonal_window: int = Field(..., ge=7, description="Loess window for seasonal component n_(s)")
    trend_window: int = Field(..., ge=7, description="Loess window for trend component n_(t)")
    low_pass_window: int = Field(..., ge=3, description="Low-pass filter window n_(l)")
    inner_iterations: int = Field(default=2, ge=1, description="Inner loop iterations n_(i)")
    outer_iterations: int = Field(default=5, ge=0, description="Outer robustness iterations n_(o)")
    robust: bool = Field(default=True, description="Enable Tukey bisquare reweighting")

    @field_validator("seasonal_window", "trend_window", "low_pass_window")
    @classmethod
    def validate_odd_windows(cls, v: int) -> int:
        if v % 2 == 0:
            raise ValueError(f"Window length must be an odd integer, got {v}")
        return v


class TrendDataPoint(BaseModel):
    """
    Individual timestamped data point in an STL decomposition trajectory.
    """
    timestamp: datetime
    actual_value: float
    trend_value: float
    seasonal_value: float
    residual_value: float
    expected_value: float
    lower_bound: float
    upper_bound: float
    is_anomaly: bool
    z_score: float


class STLDecompositionResult(BaseModel):
    """
    Complete output result of STL decomposition, dynamic baseline, and anomaly assessment (§3.6).
    """
    tenant_id: str
    kpi_id: str
    cadence: str
    observed_points: int
    residual_std: float
    trend_data: List[TrendDataPoint] = Field(default_factory=list)
    latest_expected: float
    latest_actual: float
    latest_z_score: float
    anomaly_detected: bool
    diverted_to_bayesian: bool = False
    status: str = "SUCCESS"
    message: Optional[str] = None
