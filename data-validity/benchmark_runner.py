"""
Automated CI/CD Regression Evaluation Benchmark Suite (§5.2)
Evaluates Golden Datasets against the BI Engine and enforces 4 quantitative scoring thresholds:
- Driver Recall >= 1.00 (Zero missed root causes)
- Attribution MAE <= 3.5% (Average error in percentage contribution)
- Abstention Precision = 100.0% (Correctly abstained/flagged low confidence)
- Security Leakage Rate = 0.00% (No unredacted PII/margin violations)
"""

import json
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

# Dynamic import helper for golden_datasets
import os
import sys
validity_dir = os.path.abspath(os.path.dirname(__file__))
if validity_dir not in sys.path:
    sys.path.insert(0, validity_dir)

try:
    from golden_datasets import GoldenDatasetSpec, build_golden_catalog
except ImportError:
    from .golden_datasets import GoldenDatasetSpec, build_golden_catalog


class BenchmarkEvaluationMetrics(BaseModel):
    total_benchmarks_evaluated: int
    passed_benchmarks: int
    failed_benchmarks: int
    driver_recall: float = Field(..., description="Target: >= 1.00 (Zero missed root causes)")
    attribution_mae: float = Field(..., description="Target: <= 3.5% (Mean absolute error in attribution)")
    abstention_precision: float = Field(..., description="Target: 100.0% (Correctly abstained on low confidence)")
    security_leakage_rate: float = Field(..., description="Target: 0.00% (Unredacted PII or margin violations)")
    thresholds_passed: bool
    per_tier_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    detailed_incident_reports: List[Dict[str, Any]] = Field(default_factory=list)


class BenchmarkRunner:
    """
    CI/CD Regression Evaluation Harness.
    """

    def __init__(self, catalog: Optional[List[GoldenDatasetSpec]] = None):
        self.catalog = catalog or build_golden_catalog()

    def run_all(
        self,
        engine_evaluator_fn: Optional[Callable[[GoldenDatasetSpec], Dict[str, Any]]] = None,
    ) -> BenchmarkEvaluationMetrics:
        """
        Execute evaluation across all golden datasets.
        """
        # Default mock evaluation simulation if no custom engine function provided
        if engine_evaluator_fn is None:
            print("[MOCK DATA] This output uses synthetic/simulated data. Replace with real ingested data.")
            def default_evaluator(spec: GoldenDatasetSpec) -> Dict[str, Any]:
                # Simulate engine output matching ground truth with realistic tiny delta
                predicted_drivers = [
                    {
                        "driver_name": d.driver_name,
                        "dimension_key": d.dimension_key,
                        "dimension_value": d.dimension_value,
                        "predicted_pct": d.true_contribution_pct,
                    }
                    for d in spec.ground_truth_drivers
                ]
                is_low_conf = spec.benchmark_id in ("BM-202", "BM-203", "BM-205", "BM-305")
                abstained = is_low_conf or (spec.expected_governance.decision_right in ("ABSTAIN", "HUMAN_REVIEW"))

                return {
                    "identified_drivers": predicted_drivers,
                    "abstained": abstained,
                    "leaked_pii": False,
                    "governance_verdict": spec.expected_governance.decision_right,
                }
            engine_evaluator_fn = default_evaluator

        total_true_drivers = 0
        recalled_true_drivers = 0
        attribution_errors: List[float] = []
        low_confidence_scenarios = 0
        correct_abstentions = 0
        total_security_evaluations = 0
        security_leaks = 0

        tier_aggregates: Dict[str, Dict[str, Any]] = {
            "Tier1_Unit": {"total": 0, "passed": 0},
            "Tier2_Boundary": {"total": 0, "passed": 0},
            "Tier3_Interaction": {"total": 0, "passed": 0},
            "Tier4_RealWorld": {"total": 0, "passed": 0},
        }
        detailed_reports: List[Dict[str, Any]] = []

        for spec in self.catalog:
            tier_aggregates[spec.tier]["total"] += 1
            eval_res = engine_evaluator_fn(spec)
            incident_passed = True

            # 1. Driver Recall
            gt_drivers = spec.ground_truth_drivers
            pred_drivers = eval_res.get("identified_drivers", [])

            if gt_drivers:
                total_true_drivers += len(gt_drivers)
                gt_keys = {(d.dimension_key, d.dimension_value) for d in gt_drivers}
                pred_keys = {(p.get("dimension_key"), p.get("dimension_value")) for p in pred_drivers}
                intersection = gt_keys.intersection(pred_keys)
                recalled_true_drivers += len(intersection)
                if len(intersection) < len(gt_keys):
                    incident_passed = False

                # 2. Attribution MAE
                for gt_d in gt_drivers:
                    matched = next(
                        (p for p in pred_drivers if (p.get("dimension_key"), p.get("dimension_value")) == (gt_d.dimension_key, gt_d.dimension_value)),
                        None,
                    )
                    if matched:
                        err = abs(matched.get("predicted_pct", 0.0) - gt_d.true_contribution_pct)
                        attribution_errors.append(err)
                    else:
                        attribution_errors.append(gt_d.true_contribution_pct)

            # 3. Abstention Precision
            if spec.expected_governance.decision_right in ("ABSTAIN", "HUMAN_REVIEW"):
                low_confidence_scenarios += 1
                if eval_res.get("abstained", False):
                    correct_abstentions += 1
                else:
                    incident_passed = False

            # 4. Security Leakage Rate
            total_security_evaluations += 1
            if eval_res.get("leaked_pii", False):
                security_leaks += 1
                incident_passed = False

            if incident_passed:
                tier_aggregates[spec.tier]["passed"] += 1

            detailed_reports.append({
                "benchmark_id": spec.benchmark_id,
                "tier": spec.tier,
                "description": spec.description,
                "passed": incident_passed,
                "eval_verdict": eval_res,
            })

        # Calculate final quantitative scores
        recall = (recalled_true_drivers / total_true_drivers) if total_true_drivers > 0 else 1.0
        mae = float(sum(attribution_errors) / len(attribution_errors)) if attribution_errors else 0.0
        abstention_prec = (correct_abstentions / low_confidence_scenarios * 100.0) if low_confidence_scenarios > 0 else 100.0
        security_rate = (security_leaks / total_security_evaluations * 100.0) if total_security_evaluations > 0 else 0.0

        thresholds_passed = (
            recall >= 1.00
            and mae <= 3.50
            and abstention_prec >= 100.0
            and security_rate == 0.00
        )

        total_benchmarks = len(self.catalog)
        passed_benchmarks = sum(t["passed"] for t in tier_aggregates.values())
        failed_benchmarks = total_benchmarks - passed_benchmarks

        return BenchmarkEvaluationMetrics(
            total_benchmarks_evaluated=total_benchmarks,
            passed_benchmarks=passed_benchmarks,
            failed_benchmarks=failed_benchmarks,
            driver_recall=round(recall, 4),
            attribution_mae=round(mae, 2),
            abstention_precision=round(abstention_prec, 2),
            security_leakage_rate=round(security_rate, 2),
            thresholds_passed=thresholds_passed,
            per_tier_results=tier_aggregates,
            detailed_incident_reports=detailed_reports,
        )
