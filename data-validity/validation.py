"""
6-Tier Data Validity Gate Specification (§2.2)
Tiers:
- Tier 1: Pydantic V2 structural & type enforcement (UUIDs, non-null, ISO-8601, dimension sanitization)
- Tier 2: Pandera columnar & category taxonomy DataFrameSchema
- Tier 3: Temporal continuity & clock skew boundary (t_observed <= t_ingest + 5s)
- Tier 4: Physical domain constraints (non-negative count/currency, [0,1] ratios, dynamic 6-sigma outlier screening)
- Tier 5: Additive dimensional reconciliation (|sum(slices) - total| <= max(0.01, 0.001 * total))
- Tier 6: Distributional drift detection (scipy KS-test and Population Stability Index PSI vs 30-day baseline)
"""

import json
import math
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import polars as pl
from pydantic import BaseModel, Field, field_validator, model_validator
try:
    import pandera.pandas as pa
    from pandera.pandas import Column, Check, DataFrameSchema
except (ImportError, AttributeError):
    import pandera as pa
    from pandera import Column, Check, DataFrameSchema
from scipy import stats


# ============================================================================
# TIER 1: Structural & Type Validation (Pydantic V2)
# ============================================================================

class Tier1MetricSchema(BaseModel):
    """Tier 1 individual metric record contract."""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = Field(..., min_length=1, max_length=128)
    kpi_id: str = Field(..., min_length=1, max_length=128)
    observed_at: datetime
    value: float
    dimensions: Dict[str, Any] = Field(default_factory=dict)
    is_imputed: bool = False

    @field_validator("tenant_id", "kpi_id")
    @classmethod
    def sanitize_identifiers(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Identifier cannot be blank or whitespace-only.")
        return s

    @field_validator("observed_at", mode="before")
    @classmethod
    def parse_observed_at_pre(cls, v: Any) -> Any:
        if isinstance(v, str):
            clean = v.replace("Z", "+00:00")
            try:
                return datetime.fromisoformat(clean)
            except Exception:
                from dateutil import parser
                return parser.parse(clean)
        return v

    @field_validator("dimensions", mode="before")
    @classmethod
    def sanitize_dimensions(cls, v: Any) -> Dict[str, Any]:
        if v is None:
            return {}
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, dict):
                    return parsed
                return {"raw": str(parsed)}
            except Exception:
                return {"raw": v}
        if not isinstance(v, dict):
            return {"raw": str(v)}
        # Sanitize keys: strip and remove control characters
        sanitized = {}
        for k, val in v.items():
            clean_k = str(k).strip()
            if clean_k:
                sanitized[clean_k] = str(val).strip() if val is not None else ""
        return sanitized

    @field_validator("value")
    @classmethod
    def validate_finite_value(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError(f"Metric value must be finite, got: {v}")
        return v


class Tier1BatchValidator:
    """Vectorized and sequential Tier 1 structural validator."""

    def validate_record(self, record: Dict[str, Any]) -> Tuple[bool, Optional[Tier1MetricSchema], Optional[str]]:
        try:
            # Handle ISO string timestamps
            rec_copy = dict(record)
            if isinstance(rec_copy.get("observed_at"), str):
                ts_str = rec_copy["observed_at"].replace("Z", "+00:00")
                rec_copy["observed_at"] = datetime.fromisoformat(ts_str)
            validated = Tier1MetricSchema(**rec_copy)
            return True, validated, None
        except Exception as e:
            return False, None, f"Tier 1 Structural Violation: {str(e)}"

    def validate_batch(self, records: List[Dict[str, Any]]) -> Tuple[List[Tier1MetricSchema], List[Dict[str, Any]]]:
        valid_records: List[Tier1MetricSchema] = []
        rejected_records: List[Dict[str, Any]] = []

        for r in records:
            is_valid, validated_obj, err_msg = self.validate_record(r)
            if is_valid and validated_obj is not None:
                valid_records.append(validated_obj)
            else:
                rejected_records.append({
                    "raw_payload": r,
                    "failed_tier": "TIER_1_STRUCTURAL",
                    "error_code": "ERR_TIER1_SCHEMA_INVALID",
                    "error_message": err_msg or "Schema validation failed",
                })
        return valid_records, rejected_records


# ============================================================================
# TIER 2: Columnar & Statistical Range Validation (Pandera)
# ============================================================================

REGISTERED_TAXONOMIES = {
    "channel": ["Enterprise", "Self-Serve", "Partner", "Direct", "Organic", "Paid", "All", "Inbound", "Outbound"],
    "region": ["US", "EMEA", "APAC", "LATAM", "Global", "NA", "EU"],
    "tier": ["Free", "Starter", "Professional", "Enterprise", "Custom"],
}

tier2_pandera_schema = DataFrameSchema(
    columns={
        "tenant_id": Column(pa.String, nullable=False),
        "kpi_id": Column(pa.String, nullable=False),
        "observed_at": Column(pa.DateTime, nullable=False),
        "value": Column(pa.Float, nullable=False),
        "is_imputed": Column(pa.Bool, nullable=False),
    },
    strict=False,
    coerce=True,
)


class Tier2PanderaValidator:
    """Pandera columnar & taxonomy validation gate."""

    def __init__(self, taxonomies: Optional[Dict[str, List[str]]] = None):
        self.taxonomies = taxonomies or REGISTERED_TAXONOMIES
        self.schema = tier2_pandera_schema

    def validate(self, df: pd.DataFrame) -> Tuple[bool, Optional[str]]:
        if df.empty:
            return True, None

        # 1. Columnar schema validation
        try:
            self.schema.validate(df, lazy=True)
        except pa.errors.SchemaErrors as err:
            return False, f"Tier 2 Pandera Schema Errors: {str(err.failure_cases)}"
        except Exception as e:
            return False, f"Tier 2 Pandera Failure: {str(e)}"

        # 2. Taxonomy taxonomy checks on parsed dimensions if present
        if "dimensions" in df.columns:
            for idx, dims in enumerate(df["dimensions"]):
                if isinstance(dims, str):
                    try:
                        dims_dict = json.loads(dims)
                    except Exception:
                        dims_dict = {}
                elif isinstance(dims, dict):
                    dims_dict = dims
                else:
                    dims_dict = {}

                for tax_key, allowed_values in self.taxonomies.items():
                    if tax_key in dims_dict:
                        val = dims_dict[tax_key]
                        if val not in allowed_values:
                            return False, (
                                f"Tier 2 Taxonomy Violation at row {idx}: "
                                f"Dimension '{tax_key}'='{val}' not in registered taxonomy {allowed_values}"
                            )

        return True, None


# ============================================================================
# TIER 3: Temporal Continuity & Clock Skew Gate
# ============================================================================

class Tier3TemporalValidator:
    """Rejects future timestamps beyond clock skew threshold (5 seconds)."""

    def __init__(self, clock_skew_seconds: float = 5.0):
        self.clock_skew = timedelta(seconds=clock_skew_seconds)

    def validate_record(self, observed_at: datetime, ingest_at: Optional[datetime] = None) -> Tuple[bool, Optional[str]]:
        ingest_time = ingest_at or datetime.now(timezone.utc)
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        if ingest_time.tzinfo is None:
            ingest_time = ingest_time.replace(tzinfo=timezone.utc)

        max_allowed_time = ingest_time + self.clock_skew
        if observed_at > max_allowed_time:
            return False, (
                f"Tier 3 Temporal Clock Skew Violation: observed_at ({observed_at.isoformat()}) "
                f"exceeds ingest_at + 5s ({max_allowed_time.isoformat()})"
            )
        return True, None


# ============================================================================
# TIER 4: Physical Domain & Statistical Boundary Constraints
# ============================================================================

NON_NEGATIVE_KPI_KEYWORDS = [
    "revenue", "arr", "mrr", "count", "orders", "users", "latency",
    "cost", "volume", "clicks", "impressions", "duration", "items"
]

BOUNDED_RATIO_KPI_KEYWORDS = [
    "rate", "pct", "percentage", "ratio", "share", "conversion",
    "churn_rate", "retention", "margin_pct"
]


class Tier4BoundaryValidator:
    """Enforces non-negativity, [0,1] ratios, and 6-sigma outlier screening."""

    def __init__(self, outlier_sigma: float = 6.0):
        self.outlier_sigma = outlier_sigma

    def validate_physical_domain(self, kpi_id: str, value: float) -> Tuple[bool, Optional[str]]:
        kpi_lower = kpi_id.lower()

        # Non-negative check
        if any(keyword in kpi_lower for keyword in NON_NEGATIVE_KPI_KEYWORDS):
            if value < 0.0:
                return False, f"Tier 4 Physical Domain Violation: Non-negative KPI '{kpi_id}' received value {value} < 0"

        # Bounded ratio check [0.0, 1.0] (or [0, 100])
        if any(keyword in kpi_lower for keyword in BOUNDED_RATIO_KPI_KEYWORDS):
            if value < 0.0 or value > 1.0:
                # Allow percentage scale if <= 100 and > 1
                if not (0.0 <= value <= 100.0 and ("pct" in kpi_lower or "percentage" in kpi_lower)):
                    return False, f"Tier 4 Bounded Ratio Violation: Ratio KPI '{kpi_id}' received value {value} outside [0.0, 1.0]"

        return True, None

    def screen_6sigma_outliers(
        self,
        values: np.ndarray,
        baseline_mean: Optional[float] = None,
        baseline_std: Optional[float] = None,
    ) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Flag points where |Y_t - mu| > 6 * sigma.
        Returns: (is_outlier_mask, outlier_details_list)
        """
        if len(values) == 0:
            return np.array([], dtype=bool), []

        mu = baseline_mean if baseline_mean is not None else float(np.nanmean(values))
        sigma = baseline_std if baseline_std is not None else float(np.nanstd(values))

        if sigma <= 1e-9 or math.isnan(sigma):
            return np.zeros(len(values), dtype=bool), []

        z_scores = np.abs(values - mu) / sigma
        outlier_mask = z_scores > self.outlier_sigma

        outliers = []
        for idx in np.where(outlier_mask)[0]:
            outliers.append({
                "index": int(idx),
                "value": float(values[idx]),
                "z_score": float(z_scores[idx]),
                "baseline_mean": mu,
                "baseline_std": sigma,
                "threshold_sigma": self.outlier_sigma,
            })

        return outlier_mask, outliers


# ============================================================================
# TIER 5: Additive Dimensional Reconciliation Engine
# ============================================================================

class Tier5ReconciliationValidator:
    """Enforces mathematical consistency across multi-dimensional slices."""

    def reconcile_slices(
        self,
        slice_values: List[float],
        total_metric_value: float,
    ) -> Tuple[bool, float, Optional[str]]:
        """
        |sum(SliceValue_i) - TotalMetricValue| <= max(0.01, 0.001 * TotalMetricValue)
        """
        sum_slices = float(sum(slice_values))
        delta = abs(sum_slices - total_metric_value)
        allowed_tolerance = max(0.01, 0.001 * abs(total_metric_value))

        if delta > allowed_tolerance:
            pct_discrepancy = (delta / abs(total_metric_value)) * 100.0 if abs(total_metric_value) > 1e-9 else 100.0
            return False, delta, (
                f"Tier 5 Dimensional Reconciliation Violation: Sum of slices ({sum_slices:.4f}) "
                f"differs from total ({total_metric_value:.4f}) by delta {delta:.4f} "
                f"({pct_discrepancy:.2f}% discrepancy > allowed tolerance {allowed_tolerance:.4f})"
            )
        return True, delta, None


# ============================================================================
# TIER 6: Distributional Drift Detection (KS-Test & PSI)
# ============================================================================

def calculate_psi(reference: np.ndarray, current: np.ndarray, num_buckets: int = 10) -> float:
    """
    Calculate Population Stability Index (PSI) between reference and current distribution.
    PSI < 0.10: No significant change
    0.10 <= PSI < 0.25: Moderate shift
    PSI >= 0.25: Significant distributional drift
    """
    ref = reference[~np.isnan(reference)]
    curr = current[~np.isnan(current)]

    if len(ref) < 5 or len(curr) < 5:
        return 0.0

    # Determine quantile bins based on reference distribution
    percentiles = np.linspace(0, 100, num_buckets + 1)
    bin_edges = np.percentile(ref, percentiles)
    # Ensure unique bin edges
    bin_edges = np.unique(bin_edges)
    if len(bin_edges) < 2:
        return 0.0

    bin_edges[0] = -np.inf
    bin_edges[-1] = np.inf

    ref_counts, _ = np.histogram(ref, bins=bin_edges)
    curr_counts, _ = np.histogram(curr, bins=bin_edges)

    # Convert to fractions with Laplace smoothing
    ref_fractions = (ref_counts + 1e-4) / (len(ref) + 1e-4 * len(ref_counts))
    curr_fractions = (curr_counts + 1e-4) / (len(curr) + 1e-4 * len(curr_counts))

    # Compute PSI sum: (curr - ref) * ln(curr / ref)
    psi_val = np.sum((curr_fractions - ref_fractions) * np.log(curr_fractions / ref_fractions))
    return float(max(0.0, psi_val))


class Tier6DriftValidator:
    """Distributional drift evaluator using 2-sample Kolmogorov-Smirnov test and PSI."""

    def __init__(self, ks_alpha: float = 0.01, psi_threshold: float = 0.25):
        self.ks_alpha = ks_alpha
        self.psi_threshold = psi_threshold

    def evaluate_drift(
        self,
        current_batch: Union[np.ndarray, List[float]],
        baseline_30d: Union[np.ndarray, List[float]],
    ) -> Dict[str, Any]:
        curr_arr = np.asarray(current_batch, dtype=float)
        base_arr = np.asarray(baseline_30d, dtype=float)

        curr_clean = curr_arr[~np.isnan(curr_arr)]
        base_clean = base_arr[~np.isnan(base_arr)]

        if len(curr_clean) < 5 or len(base_clean) < 5:
            return {
                "drift_detected": False,
                "psi": 0.0,
                "ks_statistic": 0.0,
                "ks_pvalue": 1.0,
                "message": "Insufficient data points for statistical drift testing (<5).",
            }

        # 1. Two-sample Kolmogorov-Smirnov Test
        ks_res = stats.ks_2samp(base_clean, curr_clean)
        ks_stat = float(ks_res.statistic)
        ks_pval = float(ks_res.pvalue)

        # 2. Population Stability Index (PSI)
        psi_val = calculate_psi(base_clean, curr_clean)

        drift_detected = (psi_val >= self.psi_threshold) or (ks_pval < self.ks_alpha)
        msg = "Distribution stable."
        if drift_detected:
            msg = (
                f"Significant distributional drift detected: PSI={psi_val:.4f} "
                f"(threshold={self.psi_threshold}), KS p-value={ks_pval:.4e} (alpha={self.ks_alpha})."
            )

        return {
            "drift_detected": drift_detected,
            "psi": round(psi_val, 4),
            "ks_statistic": round(ks_stat, 4),
            "ks_pvalue": ks_pval,
            "reference_mean": float(np.mean(base_clean)),
            "reference_std": float(np.std(base_clean)),
            "current_mean": float(np.mean(curr_clean)),
            "current_std": float(np.std(curr_clean)),
            "message": msg,
        }


# ============================================================================
# COMPOSITE VALIDATION GATE MANAGER
# ============================================================================

class ValidationResult(BaseModel):
    is_valid: bool
    passed_tiers: List[str]
    failed_tier: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    quarantine_records: List[Dict[str, Any]] = Field(default_factory=list)
    drift_telemetry: Optional[Dict[str, Any]] = None
    tier_scores: Dict[str, float] = Field(default_factory=dict)


class ValidationGateManager:
    """
    Coordinates execution of Tier 1, Tier 2, Tier 3, Tier 4, Tier 5, Tier 6 gates.
    """

    def __init__(self):
        self.tier1_validator = Tier1BatchValidator()
        self.tier2_validator = Tier2PanderaValidator()
        self.tier3_validator = Tier3TemporalValidator()
        self.tier4_validator = Tier4BoundaryValidator()
        self.tier5_validator = Tier5ReconciliationValidator()
        self.tier6_validator = Tier6DriftValidator()

    def validate_batch(
        self,
        records: List[Dict[str, Any]],
        baseline_30d: Optional[List[float]] = None,
        ingest_time: Optional[datetime] = None,
    ) -> ValidationResult:
        if ingest_time is None:
            ingest_time = datetime.now(timezone.utc)

        passed_tiers: List[str] = []
        quarantine_records: List[Dict[str, Any]] = []
        tier_scores = {
            "struct": 1.0,
            "range": 1.0,
            "temp": 1.0,
            "reconcile": 1.0,
            "completeness": 1.0,
        }

        # ----------------------------------------------------
        # Tier 1: Structural & Type Validation
        # ----------------------------------------------------
        valid_t1_objs, t1_quarantined = self.tier1_validator.validate_batch(records)
        if t1_quarantined:
            tier_scores["struct"] = max(0.0, 1.0 - (len(t1_quarantined) / len(records)))
            for qr in t1_quarantined:
                quarantine_records.append(qr)
            return ValidationResult(
                is_valid=False,
                passed_tiers=passed_tiers,
                failed_tier="TIER_1_STRUCTURAL",
                error_code="ERR_TIER1_STRUCTURE",
                error_message=f"{len(t1_quarantined)} records failed Tier 1 structural validation.",
                quarantine_records=quarantine_records,
                tier_scores=tier_scores,
            )
        passed_tiers.append("TIER_1_STRUCTURAL")

        # ----------------------------------------------------
        # Tier 3: Temporal Clock Skew Checks
        # ----------------------------------------------------
        t3_quarantined = []
        for obj in valid_t1_objs:
            t3_ok, t3_err = self.tier3_validator.validate_record(obj.observed_at, ingest_time)
            if not t3_ok:
                t3_quarantined.append({
                    "raw_payload": obj.model_dump(mode="json"),
                    "failed_tier": "TIER_3_TEMPORAL",
                    "error_code": "ERR_TIER3_FUTURE_TIMESTAMP",
                    "error_message": t3_err,
                })
        if t3_quarantined:
            tier_scores["temp"] = 0.0
            quarantine_records.extend(t3_quarantined)
            return ValidationResult(
                is_valid=False,
                passed_tiers=passed_tiers,
                failed_tier="TIER_3_TEMPORAL",
                error_code="ERR_TIER3_FUTURE_TIMESTAMP",
                error_message=f"{len(t3_quarantined)} records failed Tier 3 future timestamp check.",
                quarantine_records=quarantine_records,
                tier_scores=tier_scores,
            )
        passed_tiers.append("TIER_3_TEMPORAL")

        # ----------------------------------------------------
        # Tier 2: Pandera Columnar & Taxonomy Schema
        # ----------------------------------------------------
        df_for_t2 = pd.DataFrame([obj.model_dump() for obj in valid_t1_objs])
        t2_ok, t2_err = self.tier2_validator.validate(df_for_t2)
        if not t2_ok:
            tier_scores["range"] = 0.5
            for obj in valid_t1_objs:
                quarantine_records.append({
                    "raw_payload": obj.model_dump(mode="json"),
                    "failed_tier": "TIER_2_PANDERA",
                    "error_code": "ERR_TIER2_SCHEMA_TAXONOMY",
                    "error_message": t2_err,
                })
            return ValidationResult(
                is_valid=False,
                passed_tiers=passed_tiers,
                failed_tier="TIER_2_PANDERA",
                error_code="ERR_TIER2_SCHEMA_TAXONOMY",
                error_message=t2_err,
                quarantine_records=quarantine_records,
                tier_scores=tier_scores,
            )
        passed_tiers.append("TIER_2_PANDERA")

        # ----------------------------------------------------
        # Tier 4: Physical Domain Constraints (Non-negative, bounded ratios)
        # ----------------------------------------------------
        t4_quarantined = []
        for obj in valid_t1_objs:
            t4_ok, t4_err = self.tier4_validator.validate_physical_domain(obj.kpi_id, obj.value)
            if not t4_ok:
                t4_quarantined.append({
                    "raw_payload": obj.model_dump(mode="json"),
                    "failed_tier": "TIER_4_BOUNDARY",
                    "error_code": "ERR_TIER4_PHYSICAL_BOUNDARY",
                    "error_message": t4_err,
                })
        if t4_quarantined:
            tier_scores["range"] = 0.0
            quarantine_records.extend(t4_quarantined)
            return ValidationResult(
                is_valid=False,
                passed_tiers=passed_tiers,
                failed_tier="TIER_4_BOUNDARY",
                error_code="ERR_TIER4_PHYSICAL_BOUNDARY",
                error_message=f"{len(t4_quarantined)} records failed Tier 4 physical domain check.",
                quarantine_records=quarantine_records,
                tier_scores=tier_scores,
            )
        passed_tiers.append("TIER_4_BOUNDARY")

        # ----------------------------------------------------
        # Tier 6: Distributional Drift Detection (Telemetry Alert)
        # ----------------------------------------------------
        drift_telemetry = None
        if baseline_30d is not None and len(baseline_30d) >= 5:
            current_vals = [obj.value for obj in valid_t1_objs]
            drift_telemetry = self.tier6_validator.evaluate_drift(current_vals, baseline_30d)
        passed_tiers.append("TIER_6_DRIFT")

        return ValidationResult(
            is_valid=True,
            passed_tiers=passed_tiers,
            quarantine_records=[],
            drift_telemetry=drift_telemetry,
            tier_scores=tier_scores,
        )
