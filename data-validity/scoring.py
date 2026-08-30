"""
Composite Data Quality ($DQ$) Scoring & Governance Coupling (§2.4)
Calculates continuous DQ in [0.0, 1.0]:
DQ = w_struct*S_struct + w_range*S_range + w_temp*S_temp + w_reconcile*S_reconcile + w_completeness*S_completeness
Weights:
- w_struct = 0.25 (Structural and type compliance)
- w_range = 0.20 (Range and boundary validity)
- w_temp = 0.20 (Temporal grid alignment and continuity)
- w_reconcile = 0.20 (Dimensional sum reconciliation)
- w_completeness = 0.15 (Absence of missing/imputed records)

Couples directly to GoRules Rule 23:
- DQ >= 0.95 -> VALID
- 0.80 <= DQ < 0.95 -> DEGRADED
- DQ < 0.80 -> INVALID (Blocks automated actions, Decision Right: PROHIBITED)
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DQWeights(BaseModel):
    w_struct: float = 0.25
    w_range: float = 0.20
    w_temp: float = 0.20
    w_reconcile: float = 0.20
    w_completeness: float = 0.15


class DQScoreResult(BaseModel):
    dq_score: float = Field(..., ge=0.0, le=1.0)
    data_quality_status: str  # "VALID", "DEGRADED", "INVALID"
    component_scores: Dict[str, float]
    weights: Dict[str, float]
    governance_action: Dict[str, Any]


class DQScorer:
    """
    Computes composite data quality scores and governance status.
    """

    def __init__(self, weights: Optional[DQWeights] = None):
        self.weights = weights or DQWeights()

    def compute_dq_score(
        self,
        s_struct: float = 1.0,
        s_range: float = 1.0,
        s_temp: float = 1.0,
        s_reconcile: float = 1.0,
        s_completeness: float = 1.0,
    ) -> DQScoreResult:
        # Clamp inputs to [0.0, 1.0]
        s_struct = max(0.0, min(1.0, float(s_struct)))
        s_range = max(0.0, min(1.0, float(s_range)))
        s_temp = max(0.0, min(1.0, float(s_temp)))
        s_reconcile = max(0.0, min(1.0, float(s_reconcile)))
        s_completeness = max(0.0, min(1.0, float(s_completeness)))

        w = self.weights
        total_dq = (
            w.w_struct * s_struct
            + w.w_range * s_range
            + w.w_temp * s_temp
            + w.w_reconcile * s_reconcile
            + w.w_completeness * s_completeness
        )
        total_dq = round(max(0.0, min(1.0, total_dq)), 4)

        if total_dq >= 0.95:
            status = "VALID"
            gov_action = {
                "rule_id": 23,
                "decision_right": "ALLOWED",
                "action": "PROCEED",
                "reason": "Data quality score meets certified threshold (>= 0.95).",
            }
        elif total_dq >= 0.80:
            status = "DEGRADED"
            gov_action = {
                "rule_id": 23,
                "decision_right": "HUMAN_REVIEW",
                "action": "FLAG_DEGRADED",
                "reason": "Data quality is degraded (0.80 <= DQ < 0.95). Caution advised.",
            }
        else:
            status = "INVALID"
            gov_action = {
                "rule_id": 23,
                "condition": "dataQualityStatus != 'VALID'",
                "decision_right": "PROHIBITED",
                "action": "BLOCK_AUTOMATION",
                "reason": "Data quality score below certified threshold (< 0.80). Automated actions prohibited.",
            }

        return DQScoreResult(
            dq_score=total_dq,
            data_quality_status=status,
            component_scores={
                "s_struct": s_struct,
                "s_range": s_range,
                "s_temp": s_temp,
                "s_reconcile": s_reconcile,
                "s_completeness": s_completeness,
            },
            weights={
                "w_struct": w.w_struct,
                "w_range": w.w_range,
                "w_temp": w.w_temp,
                "w_reconcile": w.w_reconcile,
                "w_completeness": w.w_completeness,
            },
            governance_action=gov_action,
        )

    def score_from_pipeline_metrics(
        self,
        valid_struct_ratio: float = 1.0,
        valid_range_ratio: float = 1.0,
        temporal_continuity_ratio: float = 1.0,
        reconciliation_ratio: float = 1.0,
        missing_ratio: float = 0.0,
    ) -> DQScoreResult:
        """
        Convenience method to compute DQ from pipeline metrics.
        """
        s_completeness = 1.0 - missing_ratio
        return self.compute_dq_score(
            s_struct=valid_struct_ratio,
            s_range=valid_range_ratio,
            s_temp=temporal_continuity_ratio,
            s_reconcile=reconciliation_ratio,
            s_completeness=s_completeness,
        )
