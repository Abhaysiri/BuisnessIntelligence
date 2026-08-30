"""
edge_cases/low_confidence.py
Scenario 2 (§4.2): Low-Confidence Scenario with Clarification & Abstention

Simulates contradictory diagnostic evidence, noisy telemetry, and inadequate sample size:
  - Customer Agent observes: Payment gateway timeout (+450% 504 errors on Stripe endpoint)
  - Channel Agent observes: Promotional discount expired (FALL2026 promo code lapsed)

Implements:
  1. Multi-layer composite confidence score C_composite:
     C_composite = w_e * C_evidence + w_t * C_temporal + w_d * C_dag - P_contradictions - P_sample
     with weights: w_e=0.35, w_t=0.35, w_d=0.30.
  2. Three-Tier Decision Gating Architecture:
     - C_composite >= 0.85 -> GoRules Rule 20 (ALLOWED, Full Auto-Execution)
     - 0.70 <= C_composite < 0.85 -> GoRules Rule 21 (HUMAN_REVIEW, Clarification Prompt)
     - C_composite < 0.70 -> GoRules Rule 22 (ABSTAIN, Block Automated Levers)
  3. Structured Clarification Request Payload JSON with conflicting hypotheses,
     missing dimensions, suggested SQL queries, and governance verdict.
  4. Runtime [MOCK DATA] notification.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import networkx as nx
from pydantic import BaseModel, Field


MOCK_NOTICE = "[MOCK DATA] This output uses synthetic/simulated data. Replace with real ingested data."


class GovernanceDecisionRight(str, Enum):
    ALLOWED = "ALLOWED"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    ABSTAIN = "ABSTAIN"
    PROHIBITED = "PROHIBITED"


class ConfidenceBreakdown(BaseModel):
    evidence_score: float = Field(..., ge=0.0, le=1.0)
    temporal_score: float = Field(..., ge=0.0, le=1.0)
    dag_validity_score: float = Field(..., ge=0.0, le=1.0)
    contradiction_penalty: float = Field(default=0.0, ge=0.0)
    sample_size_penalty: float = Field(default=0.0, ge=0.0)


class ConflictingHypothesis(BaseModel):
    hypothesis_id: str
    driver: str
    support: str
    confidence: float
    evidence_snippet: str


class GovernanceVerdict(BaseModel):
    rule_applied: int
    decision_right: GovernanceDecisionRight
    automation_blocked: bool
    summary: str


class ClarificationPayload(BaseModel):
    request_type: str = "CLARIFICATION_REQUIRED"
    kpi_id: str
    composite_confidence: float
    confidence_breakdown: ConfidenceBreakdown
    conflicting_hypotheses: List[ConflictingHypothesis]
    missing_dimensions: List[str]
    suggested_operator_queries: List[str]
    governance_verdict: GovernanceVerdict
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class FindingEvidence:
    source_agent: str
    driver_name: str
    r_squared: float
    is_stat_sig: bool
    precedes_kpi_drop: bool
    dag_path_valid: bool
    description: str


class ConfidenceEngine:
    """
    Computes multi-layer composite confidence score C_composite and implements
    3-tier decision gating aligned with GoRules Rules 20, 21, 22.
    """

    def __init__(
        self,
        w_evidence: float = 0.35,
        w_temporal: float = 0.35,
        w_dag: float = 0.30,
        contradiction_weight: float = 0.20,
        min_sample_threshold: int = 30
    ):
        self.w_e = w_evidence
        self.w_t = w_temporal
        self.w_d = w_dag
        self.p_contra_weight = contradiction_weight
        self.min_sample_threshold = min_sample_threshold

    def calculate_composite_confidence(
        self,
        findings: List[FindingEvidence],
        n_contradictions: int = 0,
        sample_size: int = 30
    ) -> Tuple[float, ConfidenceBreakdown]:
        """
        Calculates C_composite = w_e * C_evidence + w_t * C_temporal + w_d * C_dag - P_contradictions - P_sample
        """
        k = len(findings)
        if k == 0:
            return 0.0, ConfidenceBreakdown(
                evidence_score=0.0,
                temporal_score=0.0,
                dag_validity_score=0.0,
                contradiction_penalty=0.0,
                sample_size_penalty=0.0
            )

        # 1. Evidence score: C_evidence = min(1.0, StatSigFindings / K) * mean(r^2)
        stat_sig_count = sum(1 for f in findings if f.is_stat_sig)
        mean_r2 = sum(f.r_squared for f in findings) / k
        c_evidence = min(1.0, stat_sig_count / k) * mean_r2

        # 2. Temporal score: C_temporal = fraction of driver shifts preceding the KPI drop
        temporal_count = sum(1 for f in findings if f.precedes_kpi_drop)
        c_temporal = temporal_count / k

        # 3. DAG validity score: C_dag = proportion of drivers with valid causal paths
        dag_count = sum(1 for f in findings if f.dag_path_valid)
        c_dag = dag_count / k

        # 4. Penalties
        p_contradictions = self.p_contra_weight * n_contradictions
        p_sample = 0.0
        if sample_size < self.min_sample_threshold:
            p_sample = ((self.min_sample_threshold - sample_size) / self.min_sample_threshold) * 0.15

        # Weighted raw composite
        raw_composite = (
            (self.w_e * c_evidence) +
            (self.w_t * c_temporal) +
            (self.w_d * c_dag) -
            p_contradictions -
            p_sample
        )
        composite_confidence = max(0.0, min(1.0, raw_composite))

        breakdown = ConfidenceBreakdown(
            evidence_score=round(c_evidence, 4),
            temporal_score=round(c_temporal, 4),
            dag_validity_score=round(c_dag, 4),
            contradiction_penalty=round(p_contradictions, 4),
            sample_size_penalty=round(p_sample, 4)
        )

        return round(composite_confidence, 4), breakdown

    def evaluate_governance_rule(self, composite_confidence: float) -> GovernanceVerdict:
        """
        Applies 3-Tier Decision Gating:
          C_composite >= 0.85 -> GoRules Rule 20 (ALLOWED)
          0.70 <= C_composite < 0.85 -> GoRules Rule 21 (HUMAN_REVIEW)
          C_composite < 0.70 -> GoRules Rule 22 (ABSTAIN)
        """
        if composite_confidence >= 0.85:
            return GovernanceVerdict(
                rule_applied=20,
                decision_right=GovernanceDecisionRight.ALLOWED,
                automation_blocked=False,
                summary="Rule 20 triggered: Diagnostic confidence >= 0.85. Automated lever execution is ALLOWED."
            )
        elif composite_confidence >= 0.70:
            return GovernanceVerdict(
                rule_applied=21,
                decision_right=GovernanceDecisionRight.HUMAN_REVIEW,
                automation_blocked=True,
                summary="Rule 21 triggered: Moderate confidence (0.70-0.84). Automated levers paused; HUMAN_REVIEW and operator clarification required."
            )
        else:
            return GovernanceVerdict(
                rule_applied=22,
                decision_right=GovernanceDecisionRight.ABSTAIN,
                automation_blocked=True,
                summary="Rule 22 triggered: Low confidence (< 0.70) or unresolvable contradiction. Automated levers BLOCKED; system ABSTAINS from execution."
            )


class LowConfidenceScenarioRunner:
    """
    Simulates Scenario 2 (§4.2) with contradictory multi-agent findings.
    """

    def __init__(self):
        self.engine = ConfidenceEngine()

    def simulate_low_confidence_contradiction(self) -> ClarificationPayload:
        """
        Simulates contradictory findings between Customer Agent and Channel Agent,
        yielding low confidence and triggering Rule 22 (ABSTAIN).
        """
        findings = [
            FindingEvidence(
                source_agent="Customer Agent",
                driver_name="Payment Gateway Timeout",
                r_squared=0.62,
                is_stat_sig=True,
                precedes_kpi_drop=True,
                dag_path_valid=True,
                description="450% spike in 504 Gateway Timeout errors detected on /v1/checkout/process Stripe endpoint"
            ),
            FindingEvidence(
                source_agent="Channel Agent",
                driver_name="Promotional Discount Expired",
                r_squared=0.54,
                is_stat_sig=False,
                precedes_kpi_drop=False,
                dag_path_valid=True,
                description="FALL2026 promotional coupon code expired at 00:00 UTC, reducing organic conversions"
            )
        ]

        conf, breakdown = self.engine.calculate_composite_confidence(
            findings=findings,
            n_contradictions=1,  # Direct contradiction between gateway bug vs promo expiration
            sample_size=12       # Sparse sample size (12 hours of telemetry)
        )

        verdict = self.engine.evaluate_governance_rule(conf)

        conflicting_hypotheses = [
            ConflictingHypothesis(
                hypothesis_id="H1",
                driver="Payment Gateway Timeout",
                support="Customer Agent",
                confidence=0.65,
                evidence_snippet="Stripe HTTP 504 error volume surged 450% coincident with conversion dip."
            ),
            ConflictingHypothesis(
                hypothesis_id="H2",
                driver="Promotional Discount Expired",
                support="Channel Agent",
                confidence=0.52,
                evidence_snippet="FALL2026 promo code lapsed, causing cart abandonment surge."
            )
        ]

        missing_dimensions = [
            "payment_processor_type",
            "user_subscription_tier",
            "checkout_error_subcode"
        ]

        suggested_queries = [
            "SELECT payment_method, COUNT(*) AS error_count FROM checkout_errors WHERE status_code = 504 GROUP BY 1;",
            "SELECT promo_code, SUM(discount_amount) FROM redemptions WHERE date >= '2026-08-20' GROUP BY 1;",
            "SELECT payment_processor_type, status_code, COUNT(*) FROM transaction_logs WHERE created_at >= NOW() - INTERVAL '6 HOURS' GROUP BY 1, 2;"
        ]

        return ClarificationPayload(
            request_type="CLARIFICATION_REQUIRED",
            kpi_id="checkout_conversion_rate",
            composite_confidence=conf,
            confidence_breakdown=breakdown,
            conflicting_hypotheses=conflicting_hypotheses,
            missing_dimensions=missing_dimensions,
            suggested_operator_queries=suggested_queries,
            governance_verdict=verdict
        )

    def simulate_medium_confidence_human_review(self) -> ClarificationPayload:
        """
        Simulates moderate confidence (0.70 <= C < 0.85), triggering Rule 21 (HUMAN_REVIEW).
        """
        findings = [
            FindingEvidence(
                source_agent="Customer Agent",
                driver_name="CDN Cache Invalidation Latency",
                r_squared=0.82,
                is_stat_sig=True,
                precedes_kpi_drop=True,
                dag_path_valid=True,
                description="Elevated TTFB (+320ms) observed in EU-Central region"
            ),
            FindingEvidence(
                source_agent="Geography Agent",
                driver_name="EU ISP Routing Degradation",
                r_squared=0.74,
                is_stat_sig=True,
                precedes_kpi_drop=False,
                dag_path_valid=True,
                description="Frankfurt POP packet loss correlated with regional latency"
            )
        ]

        conf, breakdown = self.engine.calculate_composite_confidence(
            findings=findings,
            n_contradictions=0,
            sample_size=24
        )

        verdict = self.engine.evaluate_governance_rule(conf)

        return ClarificationPayload(
            request_type="OPERATOR_CONFIRMATION_REQUIRED",
            kpi_id="checkout_latency_ms",
            composite_confidence=conf,
            confidence_breakdown=breakdown,
            conflicting_hypotheses=[
                ConflictingHypothesis(
                    hypothesis_id="H1",
                    driver="CDN Cache Invalidation Latency",
                    support="Customer Agent",
                    confidence=conf,
                    evidence_snippet="EU-Central TTFB degradation matches regional latency anomaly."
                )
            ],
            missing_dimensions=["origin_pop_identifier"],
            suggested_operator_queries=[
                "SELECT edge_location, AVG(ttfb_ms) FROM edge_access_logs WHERE timestamp >= NOW() - INTERVAL '4 HOURS' GROUP BY 1;"
            ],
            governance_verdict=verdict
        )

    def simulate_high_confidence_allowed(self) -> ClarificationPayload:
        """
        Simulates high confidence (C >= 0.85), triggering Rule 20 (ALLOWED).
        """
        findings = [
            FindingEvidence(
                source_agent="Product Agent",
                driver_name="Database Connection Pool Exhaustion",
                r_squared=0.96,
                is_stat_sig=True,
                precedes_kpi_drop=True,
                dag_path_valid=True,
                description="Max connections reached on primary Postgres replica leading to 500 errors"
            ),
            FindingEvidence(
                source_agent="Customer Agent",
                driver_name="API Gateway 500 Responses",
                r_squared=0.94,
                is_stat_sig=True,
                precedes_kpi_drop=True,
                dag_path_valid=True,
                description="Upstream 500 error count perfectly matches checkout failures"
            )
        ]

        conf, breakdown = self.engine.calculate_composite_confidence(
            findings=findings,
            n_contradictions=0,
            sample_size=100
        )

        verdict = self.engine.evaluate_governance_rule(conf)

        return ClarificationPayload(
            request_type="EXECUTION_AUTHORIZED",
            kpi_id="checkout_error_rate",
            composite_confidence=conf,
            confidence_breakdown=breakdown,
            conflicting_hypotheses=[],
            missing_dimensions=[],
            suggested_operator_queries=[],
            governance_verdict=verdict
        )


def run_scenario() -> Dict[str, Any]:
    """Entrypoint to run all 3 tiers of Scenario 2 and print results."""
    print(MOCK_NOTICE)
    print("=" * 80)
    print("SCENARIO 2: LOW-CONFIDENCE SCENARIO WITH CLARIFICATION & ABSTENTION (§4.2)")
    print("=" * 80)

    runner = LowConfidenceScenarioRunner()

    print("\n[TIER 1: HIGH CONFIDENCE - RULE 20 ALLOWED]")
    p1 = runner.simulate_high_confidence_allowed()
    print(f"Composite Confidence: {p1.composite_confidence:.4f}")
    print(f"Governance Verdict:   Rule {p1.governance_verdict.rule_applied} -> {p1.governance_verdict.decision_right.value}")
    print(f"Automation Blocked:   {p1.governance_verdict.automation_blocked}")

    print("\n[TIER 2: MEDIUM CONFIDENCE - RULE 21 HUMAN_REVIEW]")
    p2 = runner.simulate_medium_confidence_human_review()
    print(f"Composite Confidence: {p2.composite_confidence:.4f}")
    print(f"Governance Verdict:   Rule {p2.governance_verdict.rule_applied} -> {p2.governance_verdict.decision_right.value}")
    print(f"Automation Blocked:   {p2.governance_verdict.automation_blocked}")

    print("\n[TIER 3: LOW CONFIDENCE CONTRADICTION - RULE 22 ABSTAIN]")
    p3 = runner.simulate_low_confidence_contradiction()
    print(f"Composite Confidence: {p3.composite_confidence:.4f}")
    print(f"Confidence Breakdown: Evidence={p3.confidence_breakdown.evidence_score}, Temporal={p3.confidence_breakdown.temporal_score}, DAG={p3.confidence_breakdown.dag_validity_score}")
    print(f"Penalties:            Contradiction=-{p3.confidence_breakdown.contradiction_penalty}, SampleSize=-{p3.confidence_breakdown.sample_size_penalty}")
    print(f"Governance Verdict:   Rule {p3.governance_verdict.rule_applied} -> {p3.governance_verdict.decision_right.value}")
    print(f"Automation Blocked:   {p3.governance_verdict.automation_blocked}")
    print("-" * 80)
    print("STRUCTURED CLARIFICATION PAYLOAD JSON (Rule 22 Output):")
    print(json.dumps(p3.model_dump(), indent=2))
    print("=" * 80 + "\n")

    return {
        "tier1_allowed": p1.model_dump(),
        "tier2_human_review": p2.model_dump(),
        "tier3_abstain": p3.model_dump()
    }


if __name__ == "__main__":
    run_scenario()
