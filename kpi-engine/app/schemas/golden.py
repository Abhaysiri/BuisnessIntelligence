from datetime import datetime
from typing import Any, Dict, List, Literal
from pydantic import BaseModel, Field


class GroundTruthDriver(BaseModel):
    """
    Synthetically defined or empirically verified ground-truth root cause driver (§5.1).
    """
    driver_name: str
    dimension_key: str
    dimension_value: str
    true_contribution_pct: float = Field(..., description="Exact theoretical or observed percentage attribution")
    causal_path: List[str] = Field(default_factory=list, description="Topological path through causal DAG")
    onset_timestamp: datetime


class ExpectedGovernanceAction(BaseModel):
    """
    Expected GoRules decision right and automated lever execution (§5.1).
    """
    rule_id: int
    decision_right: str = Field(..., description="ALLOWED, HUMAN_REVIEW, PROHIBITED, ABSTAIN")
    expected_action: str


class GoldenDatasetSpec(BaseModel):
    """
    Authoritative benchmark test specification for CI/CD regression verification (§5.1).
    """
    benchmark_id: str
    tier: Literal["Tier1_Unit", "Tier2_Boundary", "Tier3_Interaction", "Tier4_RealWorld"]
    description: str
    kpi_id: str
    cadence: str
    input_time_series: List[Dict[str, Any]]
    ground_truth_movement: Dict[str, Any]
    ground_truth_drivers: List[GroundTruthDriver] = Field(default_factory=list)
    expected_governance: ExpectedGovernanceAction
    expected_persona_facts: Dict[str, List[str]] = Field(default_factory=dict)
    dataset_version: str = "1.0.0"
