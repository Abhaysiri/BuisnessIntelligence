from typing import Any, Dict, List
from pydantic import BaseModel, Field
from app.schemas.persona import PersonaRole


class SecurityContext(BaseModel):
    """
    Multi-tenant role-based access control and data entitlement context (§4.4).
    """
    user_id: str = Field(..., description="Unique authenticated user identity")
    tenant_id: str = Field(..., description="Multi-tenant organization boundary")
    roles: List[PersonaRole] = Field(..., description="Active user persona roles")
    permitted_metrics: List[str] = Field(default_factory=list, description="Whitelisted KPI IDs")
    permitted_dimensions: List[str] = Field(default_factory=list, description="Whitelisted dimensions")
    can_view_margins: bool = Field(default=False, description="Entitlement for gross margin/COGS")
    can_view_pii: bool = Field(default=False, description="Entitlement for customer PII")
    max_approval_limit: float = Field(default=0.0, description="Financial authority threshold ($USD)")


class ConfidenceBreakdown(BaseModel):
    """
    Decomposition of composite confidence score across multi-factor evidence layers (§4.2).
    """
    evidence_score: float = Field(..., ge=0.0, le=1.0, description="Statistical significance & r^2 of findings (w=0.35)")
    temporal_score: float = Field(..., ge=0.0, le=1.0, description="Temporal precedence fraction of driver shifts (w=0.35)")
    dag_validity_score: float = Field(..., ge=0.0, le=1.0, description="Causal graph path reachability ratio (w=0.30)")
    contradiction_penalty: float = Field(default=0.0, ge=0.0, description="Penalty for directional contradictions (0.20 per conflict)")
    sample_penalty: float = Field(default=0.0, ge=0.0, description="Penalty for small sample sizes")


class ClarificationPayload(BaseModel):
    """
    Structured clarification request generated under low-confidence conditions (§4.2) invoking Rule 22.
    """
    request_type: str = Field(default="CLARIFICATION_REQUIRED")
    kpi_id: str
    composite_confidence: float = Field(..., ge=0.0, le=1.0)
    confidence_breakdown: ConfidenceBreakdown
    conflicting_hypotheses: List[Dict[str, Any]] = Field(default_factory=list)
    missing_dimensions: List[str] = Field(default_factory=list)
    suggested_operator_queries: List[str] = Field(default_factory=list)
    governance_verdict: Dict[str, Any] = Field(default_factory=dict)
