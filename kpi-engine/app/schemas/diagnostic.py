from typing import Any
from pydantic import BaseModel, Field


class Driver(BaseModel):
    driver_id: str
    name: str
    driver_type: str

    contribution_absolute: float | None = None
    contribution_percentage: float | None = None

    temporal_valid: bool | None = None
    dependency_valid: bool | None = None

    evidence_score: float | None = None
    diagnostic_confidence: float | None = None

    supporting_findings: list[str] = Field(default_factory=list)


class Uncertainty(BaseModel):
    status: str
    abstain: bool = False
    reason: str | None = None
    alternatives: list[str] = Field(default_factory=list)


class Recommendation(BaseModel):
    lever_id: str
    action: str

    target: dict[str, Any] = Field(default_factory=dict)

    expected_impact: dict[str, Any] = Field(default_factory=dict)

    owner_role: str | None = None
    decision_right: str | None = None


class DiagnosticPayload(BaseModel):
    incident_id: str
    kpi_id: str

    observed_value: float
    expected_value: float

    percentage_change: float

    drivers: list[Driver]

    uncertainty: Uncertainty

    recommendations: list[Recommendation]

    lineage: list[dict[str, Any]] = Field(default_factory=list)

    metadata: dict[str, Any] = Field(default_factory=dict)