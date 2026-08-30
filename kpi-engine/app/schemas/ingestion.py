from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator


class RawPayload(BaseModel):
    """
    Incoming raw data payload prior to Tier 1 validation and bronze storage (§2.1).
    """
    payload_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str = Field(..., min_length=1, description="Multi-tenant organization identifier")
    kpi_id: str = Field(..., min_length=1, description="Target KPI / metric identifier")
    observed_at: datetime = Field(..., description="Timestamp of metric observation in ISO-8601 UTC")
    value: float = Field(..., description="Numeric measurement value")
    dimensions: Dict[str, Any] = Field(default_factory=dict, description="Slicing dimensional attributes")
    source_metadata: Dict[str, Any] = Field(default_factory=dict, description="Ingest metadata e.g. source IP, agent")


class CanonicalMeasurement(BaseModel):
    """
    Validated Gold-tier canonical measurement record (§2.1).
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    kpi_id: str
    observed_at: datetime
    value: float
    dimensions: Dict[str, Any] = Field(default_factory=dict)
    is_imputed: bool = Field(default=False, description="Flag indicating if value was synthesized via imputation")
    dq_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Data quality score at admission")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class QuarantineRecord(BaseModel):
    """
    Dead-letter quarantine record for records failing any validation tier (§2.3).
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    kpi_id: str
    raw_payload: Dict[str, Any]
    failed_tier: str = Field(..., description="Validation tier that rejected the record (e.g. TIER_1_STRUCTURAL)")
    error_code: str = Field(..., description="Machine-readable error identifier")
    error_message: str = Field(..., description="Human-readable root cause explanation")
    validation_trace: Dict[str, Any] = Field(default_factory=dict)
    quarantined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = Field(default=False)
    resolved_at: Optional[datetime] = None
    replayed_by: Optional[str] = None


class DQScoreResult(BaseModel):
    """
    Composite Data Quality score result (§2.4) mapping directly to GoRules Rule 23.
    """
    overall_score: float = Field(..., ge=0.0, le=1.0)
    status: str = Field(..., description="VALID (>=0.95), DEGRADED (0.80-0.95), INVALID (<0.80)")
    structural_score: float = Field(default=1.0, ge=0.0, le=1.0)
    range_score: float = Field(default=1.0, ge=0.0, le=1.0)
    temporal_score: float = Field(default=1.0, ge=0.0, le=1.0)
    reconciliation_score: float = Field(default=1.0, ge=0.0, le=1.0)
    completeness_score: float = Field(default=1.0, ge=0.0, le=1.0)
    passed: bool = Field(default=True)
    details: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_statuses = {"VALID", "DEGRADED", "INVALID"}
        if v.upper() not in valid_statuses:
            raise ValueError(f"Invalid DQ status: {v}. Must be one of {valid_statuses}")
        return v.upper()
