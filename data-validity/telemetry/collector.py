"""
Runtime Telemetry Observability Collector (§5.3)
Aggregates latency, model calls, token usage, and cost across all 7 runtime hooks
into the unified Frontend Telemetry JSON Schema contract.
"""

import os
import sys
import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

current_dir = os.path.abspath(os.path.dirname(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from .pricing import CostCalculator, ModelPricingMatrix
except (ImportError, ValueError):
    from pricing import CostCalculator, ModelPricingMatrix


class LatencyBreakdown(BaseModel):
    db_latency_ms: float = 0.0
    agent_swarm_latency_ms: float = 0.0
    analytical_math_latency_ms: float = 0.0
    orchestrator_llm_latency_ms: float = 0.0
    governance_latency_ms: float = 0.0
    persona_story_llm_latency_ms: float = 0.0


class TokenUsageBreakdown(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ModelCallsBreakdown(BaseModel):
    total_calls: int = 0
    counts: Dict[str, int] = Field(default_factory=dict)


class TelemetryPayload(BaseModel):
    trace_id: str
    total_latency_ms: float
    breakdown: LatencyBreakdown
    model_calls: Dict[str, Any]
    tokens: TokenUsageBreakdown
    estimated_cost_usd: float


class TelemetryCollector:
    """
    Thread-safe / Async-safe runtime telemetry accumulator for a single request lifecycle.
    """

    def __init__(self, trace_id: Optional[str] = None, cost_calculator: Optional[CostCalculator] = None):
        self.trace_id = trace_id or f"tr-{uuid.uuid4().hex[:8]}-{time.strftime('%Y%m%d')}"
        self.cost_calculator = cost_calculator or CostCalculator()
        self.start_time = time.perf_counter()

        self.db_latency_ms: float = 0.0
        self.agent_swarm_latency_ms: float = 0.0
        self.analytical_math_latency_ms: float = 0.0
        self.orchestrator_llm_latency_ms: float = 0.0
        self.governance_latency_ms: float = 0.0
        self.persona_story_llm_latency_ms: float = 0.0

        self.model_calls_by_name: Dict[str, int] = {}
        self.total_prompt_tokens: int = 0
        self.total_completion_tokens: int = 0
        self.total_cached_tokens: int = 0
        self.model_token_map: Dict[str, Dict[str, int]] = {}

        self.db_queries_count: int = 0
        self.rules_evaluated_count: int = 0
        self.fired_rule_ids: List[int] = []

    # ------------------------------------------------------------------------
    # Hook 1: Request Lifecycle
    # ------------------------------------------------------------------------
    def set_total_latency(self, latency_ms: float) -> None:
        self._override_total_latency = latency_ms

    # ------------------------------------------------------------------------
    # Hook 2: Database Query Execution
    # ------------------------------------------------------------------------
    def record_db_query(self, duration_ms: float, row_count: int = 0, query_hash: Optional[str] = None) -> None:
        self.db_latency_ms += duration_ms
        self.db_queries_count += 1

    # ------------------------------------------------------------------------
    # Hook 3: Agent Swarm Fan-Out
    # ------------------------------------------------------------------------
    def record_agent_execution(self, agent_name: str, duration_ms: float, findings_count: int = 0) -> None:
        self.agent_swarm_latency_ms += duration_ms

    # ------------------------------------------------------------------------
    # Hook 4: Analytical Computation (STL / Shapley / Causal)
    # ------------------------------------------------------------------------
    def record_analytical_math(self, algorithm_name: str, duration_ms: float) -> None:
        self.analytical_math_latency_ms += duration_ms

    # ------------------------------------------------------------------------
    # Hook 5: Diagnostic Orchestrator LLM Invocation
    # ------------------------------------------------------------------------
    def record_orchestrator_llm(
        self,
        duration_ms: float,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        cached_tokens: int = 0,
    ) -> None:
        self.orchestrator_llm_latency_ms += duration_ms
        self._record_llm_usage(model_name, prompt_tokens, completion_tokens, cached_tokens)

    # ------------------------------------------------------------------------
    # Hook 6: GoRules Governance Evaluation
    # ------------------------------------------------------------------------
    def record_governance(self, duration_ms: float, rules_evaluated: int, fired_rule_ids: List[int]) -> None:
        self.governance_latency_ms += duration_ms
        self.rules_evaluated_count += rules_evaluated
        self.fired_rule_ids.extend(fired_rule_ids)

    # ------------------------------------------------------------------------
    # Hook 7: Persona Storytelling LLM Generation
    # ------------------------------------------------------------------------
    def record_persona_story_llm(
        self,
        duration_ms: float,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        cached_tokens: int = 0,
    ) -> None:
        self.persona_story_llm_latency_ms += duration_ms
        self._record_llm_usage(model_name, prompt_tokens, completion_tokens, cached_tokens)

    def _record_llm_usage(
        self,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        cached_tokens: int = 0,
    ) -> None:
        self.model_calls_by_name[model_name] = self.model_calls_by_name.get(model_name, 0) + 1
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_cached_tokens += cached_tokens

        if model_name not in self.model_token_map:
            self.model_token_map[model_name] = {"prompt_tokens": 0, "completion_tokens": 0, "cached_tokens": 0}
        self.model_token_map[model_name]["prompt_tokens"] += prompt_tokens
        self.model_token_map[model_name]["completion_tokens"] += completion_tokens
        self.model_token_map[model_name]["cached_tokens"] += cached_tokens

    def build_payload(self) -> TelemetryPayload:
        """
        Compile all collected metrics into the frontend TelemetryPayload.
        """
        total_latency = (
            getattr(self, "_override_total_latency", None)
            if hasattr(self, "_override_total_latency")
            else (time.perf_counter() - self.start_time) * 1000.0
        )

        estimated_cost = self.cost_calculator.calculate_aggregate_cost(self.model_token_map)

        model_calls_dict: Dict[str, Any] = {
            "total_calls": sum(self.model_calls_by_name.values()),
        }
        for k, v in self.model_calls_by_name.items():
            model_calls_dict[k] = v

        return TelemetryPayload(
            trace_id=self.trace_id,
            total_latency_ms=round(total_latency, 2),
            breakdown=LatencyBreakdown(
                db_latency_ms=round(self.db_latency_ms, 2),
                agent_swarm_latency_ms=round(self.agent_swarm_latency_ms, 2),
                analytical_math_latency_ms=round(self.analytical_math_latency_ms, 2),
                orchestrator_llm_latency_ms=round(self.orchestrator_llm_latency_ms, 2),
                governance_latency_ms=round(self.governance_latency_ms, 2),
                persona_story_llm_latency_ms=round(self.persona_story_llm_latency_ms, 2),
            ),
            model_calls=model_calls_dict,
            tokens=TokenUsageBreakdown(
                prompt_tokens=self.total_prompt_tokens,
                completion_tokens=self.total_completion_tokens,
                total_tokens=self.total_prompt_tokens + self.total_completion_tokens,
            ),
            estimated_cost_usd=estimated_cost,
        )
