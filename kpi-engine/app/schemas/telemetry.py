from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class TelemetryBreakdown(BaseModel):
    """
    Fine-grained latency breakdown across engine pipeline execution stages (§5.4).
    """
    db_latency_ms: float = Field(default=0.0, description="Hook 2: Database query execution latency")
    agent_swarm_latency_ms: float = Field(default=0.0, description="Hook 3: LangGraph agent swarm fan-out latency")
    analytical_math_latency_ms: float = Field(default=0.0, description="Hook 4: STL / Shapley CPU execution time")
    orchestrator_llm_latency_ms: float = Field(default=0.0, description="Hook 5: Diagnostic Orchestrator LLM latency")
    governance_latency_ms: float = Field(default=0.0, description="Hook 6: GoRules Decision Table evaluation latency")
    persona_story_llm_latency_ms: float = Field(default=0.0, description="Hook 7: Persona Storytelling LLM generation latency")
    total_latency_ms: float = Field(default=0.0, description="Hook 1: Total end-to-end request latency")


class ModelUsage(BaseModel):
    """
    Aggregate LLM model invocation counts, token counters, and calculated costs (§5.3).
    """
    total_calls: int = Field(default=0)
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    estimated_cost_usd: float = Field(default=0.0)
    models: Dict[str, int] = Field(default_factory=dict, description="Model name to call count map")


class TelemetryRecord(BaseModel):
    """
    Single unit of telemetry observation recorded by collectors or hooks.
    """
    hook_id: str
    component_name: str
    duration_ms: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TelemetryPayload(BaseModel):
    """
    Aggregated telemetry payload attached to DiagnosticPayload and HTTP response headers (§5.3, §8.1).
    """
    trace_id: str = Field(..., description="Unique correlation ID for request / investigation")
    total_latency_ms: float = Field(..., description="Wall-clock execution duration in milliseconds")
    tenant_id: Optional[str] = None
    endpoint: Optional[str] = None
    status_code: int = Field(default=200)
    breakdown: TelemetryBreakdown = Field(default_factory=TelemetryBreakdown)
    model_calls: Dict[str, int] = Field(default_factory=dict)
    tokens: Dict[str, int] = Field(default_factory=dict)
    estimated_cost_usd: float = Field(default=0.0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
