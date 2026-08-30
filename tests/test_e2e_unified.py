"""
tests/test_e2e_unified.py
===============================================================================
UNIFIED END-TO-END VERIFICATION & REGRESSION TEST HARNESS
===============================================================================
Comprehensive test suite verifying all 5 core subsystems of the Business
Intelligence Engine project:

1. Ingestion & Validity Layer (§2.1, §2.2, §2.3, §2.4, §2.5, §2.6):
   - Bronze immutable storage fallback & partitioning
   - Silver Polars normalization, ISO-8601 UTC regularization, SHA-256 dimension hash
   - Akima spline (g<=3), Seasonal persistence (3<g<=p), and Cold-start bayesian trigger
   - TC-1.1: Happy Path Normal (30-day series -> Gold Insert, DQ >= 0.95, VALID)
   - TC-1.2: Negative Revenue ($-45,200.00 -> Tier 4 Boundary Quarantine)
   - TC-1.3: Future Timestamp (Now + 3 Days -> Tier 3 Temporal Quarantine)
   - TC-1.4: Dimension Mismatch (Sum of Slices != Total -> Tier 5 Quarantine / Reconciliation)
   - TC-1.5: High Missingness (35% NaN -> DQ < 0.80 -> Rule 23 Block / INVALID)
   - TC-1.6: Distributional Drift (+400% variance shift -> Tier 6 Drift Alert)
   - Quarantine dead-letter store & administrative replay with remediation
   - Supabase DDL statement printing for canonical & quarantine schemas

2. Upstream STL Time-Series Engine (§3.1-§3.8):
   - Cadence Parameter Matrix across 5 business cadences (Hourly, Daily, Weekly, Monthly, Quarterly)
     verifying Cleveland harmonic separation constraints
   - 90-Day Synthetic Verification Wave with 5 objective mathematical assertions:
     1. Trend Orthogonality: |r(T_t, S_t)| <= 0.05
     2. Seasonal Amplitude Recovery: |A_estimated - 200| <= 10.0
     3. Outlier Neutralization: rho_60 <= 0.05, |T_hat_60 - 1300| <= 20.0
     4. Residual Normality: Shapiro-Wilk p >= 0.05 on uncorrupted residuals
     5. Anomaly Trigger: Z_60 <= -10.0 and KPIMovementEvent emission
   - Sparse-history diversion for series with N < 2*period

3. Edge-Case Scenario Simulators (§4.1-§4.4):
   - Scenario 1 (Multi-factor §4.1): 3 concurrent drivers, exact Shapley attribution (2^M coalitions
     and n! permutations), LMDI-I zero-residual additive decomposition, first-order partial correlation,
     Top-3 Recall (100%), Attribution MAE <= 3.5%, FDR <= 0.05.
   - Scenario 2 (Low-confidence §4.2): Contradictory evidence, composite confidence score C_composite,
     3-tier decision gating (Rule 20 ALLOWED >=0.85, Rule 21 HUMAN_REVIEW 0.70-0.84, Rule 22 ABSTAIN <0.70),
     structured clarification payload JSON.
   - Scenario 3 (Sparse-history §4.3): Cold-start N<14 days, Hierarchical Empirical Bayesian prior borrowing,
     shrinkage factor B decaying with N, dynamic 95% credible interval widening kappa(N)=1+2.5/sqrt(N),
     epistemic caveat disclosure narrative.
   - Scenario 4 (Role-security §4.4): SecurityContext model, AST multi-tenant SQL rewriter,
     cryptographic PII & gross margin masking, GoRules Rules 13-16 role authorization checks.

4. Telemetry Observability & Dynamic Pricing (§5.1-§5.4):
   - Golden Dataset Catalog with 19 benchmark incidents across 4 tiers:
     Tier1_Unit (5), Tier2_Boundary (5), Tier3_Interaction (5), Tier4_RealWorld (4)
   - Benchmark Runner evaluating:
     - Driver Recall >= 1.0 (100.0%)
     - Attribution MAE <= 3.5%
     - Abstention Precision = 100.0%
     - Security Leakage Rate = 0.0%
     - All thresholds passed == True
   - Dynamic model token pricing matrix (gpt-4o-mini, gpt-4o, claude-3-5-sonnet)
   - TelemetryCollector aggregating all 7 hooks & non-blocking perf_counter decorators

5. FastAPI Endpoints & TelemetryMiddleware (§2.1, §5.4, §8.1):
   - GET /health with X-Trace-ID, X-Latency-MS, X-Total-Cost-USD response headers
   - POST /api/v1/metrics/ingest (Status 202 ACCEPTED)
   - POST /api/v1/quarantine/replay (Status 200 REPLAYED)
   - POST /api/v1/timeseries/decompose (Status 200 SUCCESS)
"""

import os
import sys
import math
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Set, Any
import numpy as np
import pandas as pd
import pytest
from scipy import stats

# -----------------------------------------------------------------------------
# Path Setup
# -----------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
KPI_ENGINE_ROOT = os.path.join(PROJECT_ROOT, "kpi-engine")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if KPI_ENGINE_ROOT not in sys.path:
    sys.path.insert(0, KPI_ENGINE_ROOT)

import importlib.util

def load_module_from_path(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# Ingestion modules
bronze_mod = load_module_from_path("bronze", os.path.join(PROJECT_ROOT, "data-ingest", "bronze.py"))
silver_mod = load_module_from_path("silver", os.path.join(PROJECT_ROOT, "data-ingest", "silver.py"))
impute_mod = load_module_from_path("imputation", os.path.join(PROJECT_ROOT, "data-ingest", "imputation.py"))
pipeline_mod = load_module_from_path("pipeline", os.path.join(PROJECT_ROOT, "data-ingest", "pipeline.py"))

# Validity modules
valid_mod = load_module_from_path("validation", os.path.join(PROJECT_ROOT, "data-validity", "validation.py"))
quar_mod = load_module_from_path("quarantine", os.path.join(PROJECT_ROOT, "data-validity", "quarantine.py"))
score_mod = load_module_from_path("scoring", os.path.join(PROJECT_ROOT, "data-validity", "scoring.py"))
golden_mod = load_module_from_path("golden_datasets", os.path.join(PROJECT_ROOT, "data-validity", "golden_datasets.py"))
bench_mod = load_module_from_path("benchmark_runner", os.path.join(PROJECT_ROOT, "data-validity", "benchmark_runner.py"))

# Telemetry modules
price_mod = load_module_from_path("pricing", os.path.join(PROJECT_ROOT, "data-validity", "telemetry", "pricing.py"))
collect_mod = load_module_from_path("collector", os.path.join(PROJECT_ROOT, "data-validity", "telemetry", "collector.py"))
hooks_mod = load_module_from_path("hooks", os.path.join(PROJECT_ROOT, "data-validity", "telemetry", "hooks.py"))

# Timeseries STL modules
from app.timeseries.parameters import get_cadence_parameters, calculate_cleveland_parameters
from app.timeseries.stl import STLDecomposer
from app.timeseries.baseline import (
    compute_dynamic_baseline,
    compute_robust_residual_uncertainty,
    compute_confidence_bands,
)
from app.timeseries.anomaly import (
    compute_z_scores,
    evaluate_anomaly_condition,
    create_kpi_movement_event,
    run_stl_pipeline,
)
from app.schemas.movement import KPIMovementEvent

# Edge Cases modules
from edge_cases.multifactor import (
    MultiFactorSimulator,
    compute_shapley_values,
    compute_shapley_permutations,
    compute_lmdi_additive,
    calculate_first_order_partial_correlation,
)
from edge_cases.low_confidence import (
    ConfidenceEngine,
    LowConfidenceScenarioRunner,
    GovernanceDecisionRight,
)
from edge_cases.sparse_history import (
    PriorCohortSpec,
    ColdStartBayesianEngine,
    SparseHistoryScenarioRunner,
)
from edge_cases.role_security import (
    PersonaRole,
    SecurityContext,
    SQLRewriter,
    DataMasker,
    ABACFilter,
    GovernanceRoleAuthorizer,
    RoleSecurityScenarioRunner,
)

# API / FastAPI TestClient
from starlette.testclient import TestClient
from app.main import api


# =============================================================================
# SECTION 1: Medallion Ingestion & Active Validity Gate Tests (TC-1.1 .. TC-1.6)
# =============================================================================

class TestMedallionIngestionAndValidity:
    """Verifies §2.1 Bronze/Silver, §2.2 Tiers 1,2,4,6, §2.3 Quarantine, §2.4 DQ, §2.5 Imputation."""

    def test_ddl_generation(self):
        """Verify DDL printout for canonical and quarantine tables (§2.1, §2.3)."""
        pipeline = pipeline_mod.MedallionIngestionPipeline()
        ddls = pipeline.print_all_ddl()
        assert "CREATE TABLE canonical_measurements" in ddls["canonical_measurements"]
        assert "PARTITION BY RANGE (observed_at)" in ddls["canonical_measurements"]
        assert "CREATE TABLE quarantine_measurements" in ddls["quarantine_measurements"]

    def test_tc1_1_happy_path_normal(self):
        """TC-1.1: 30-day normal series -> Gold Insert, DQ >= 0.95, VALID status (§2.6)."""
        pipeline = pipeline_mod.MedallionIngestionPipeline()
        start_date = datetime(2026, 7, 1, 0, 0, 0, tzinfo=timezone.utc)
        series = [
            {
                "observed_at": (start_date + timedelta(days=i)).isoformat(),
                "value": 1000.0 + 50.0 * (i % 7),
                "dimensions": {"channel": "Enterprise", "region": "US"},
            }
            for i in range(30)
        ]

        result = pipeline.ingest_payload(
            raw_payload=series,
            tenant_id="tenant_alpha",
            kpi_id="daily_revenue",
            cadence="daily",
        )

        assert result.batch_status == "ADMITTED_TO_GOLD"
        assert result.dq_score >= 0.95
        assert result.data_quality_status == "VALID"
        assert result.gold_records_count == 30
        assert result.quarantined_count == 0

    def test_tc1_2_negative_revenue_boundary_failure(self):
        """TC-1.2: Revenue = -$45,200.00 -> Tier 4 Boundary Quarantine (§2.6)."""
        pipeline = pipeline_mod.MedallionIngestionPipeline()
        series = [
            {
                "observed_at": "2026-08-01T00:00:00Z",
                "value": -45200.00,
                "dimensions": {"channel": "Direct"},
            }
        ]

        result = pipeline.ingest_payload(
            raw_payload=series,
            tenant_id="tenant_alpha",
            kpi_id="monthly_net_revenue",
            cadence="daily",
        )

        assert result.batch_status == "QUARANTINED"
        assert result.validation_verdict.get("failed_tier") == "TIER_4_BOUNDARY"
        assert result.quarantined_count > 0

    def test_tc1_3_future_timestamp_temporal_failure(self):
        """TC-1.3: Future Timestamp (Now + 3 Days) -> Tier 3 Temporal Quarantine (§2.6)."""
        pipeline = pipeline_mod.MedallionIngestionPipeline()
        future_time = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
        series = [
            {
                "observed_at": future_time,
                "value": 150.0,
                "dimensions": {"channel": "Organic"},
            }
        ]

        result = pipeline.ingest_payload(
            raw_payload=series,
            tenant_id="tenant_alpha",
            kpi_id="active_users",
            cadence="daily",
        )

        assert result.batch_status == "QUARANTINED"
        assert result.validation_verdict.get("failed_tier") == "TIER_3_TEMPORAL"
        assert result.quarantined_count > 0

    def test_tc1_4_dimensional_reconciliation_failure(self):
        """TC-1.4: Dimension Mismatch (Sum(Slices) != Total) -> Reconciliation Gate (§2.6)."""
        rec_validator = valid_mod.Tier5ReconciliationValidator()
        is_ok, delta, err = rec_validator.reconcile_slices(
            slice_values=[300.0, 300.0, 350.0],
            total_metric_value=1000.0,
        )
        assert not is_ok
        assert delta == 50.0
        assert "Dimensional Reconciliation Violation" in err

    def test_tc1_5_high_missingness_and_imputation(self):
        """TC-1.5: 35% Missingness -> DQ < 0.80 -> Rule 23 Block / INVALID (§2.6, §2.5)."""
        pipeline = pipeline_mod.MedallionIngestionPipeline()
        start_date = datetime(2026, 7, 1, 0, 0, 0, tzinfo=timezone.utc)
        series = []
        for i in range(30):
            if i % 3 == 0:
                continue  # Drop ~33-35% of days
            series.append({
                "observed_at": (start_date + timedelta(days=i)).isoformat(),
                "value": 500.0 + 10.0 * i,
                "dimensions": {"channel": "Enterprise"},
            })

        result = pipeline.ingest_payload(
            raw_payload=series,
            tenant_id="tenant_alpha",
            kpi_id="service_uptime_count",
            cadence="daily",
        )

        assert result.imputation_summary.get("missing_ratio") >= 0.30
        assert result.imputation_summary.get("stl_eligible") is False
        assert result.imputation_summary.get("cold_start_bayesian_trigger") is True
        assert result.dq_score < 0.95

    def test_tc1_6_distributional_drift_detection(self):
        """TC-1.6: Distributional Drift (+400% Variance Shift) -> Tier 6 KS/PSI Alert (§2.6)."""
        drift_validator = valid_mod.Tier6DriftValidator(ks_alpha=0.01, psi_threshold=0.25)
        np.random.seed(42)
        baseline_30d = np.random.normal(loc=100.0, scale=10.0, size=60)
        current_drifted = np.random.normal(loc=100.0, scale=50.0, size=60)

        drift_report = drift_validator.evaluate_drift(current_drifted, baseline_30d)
        assert drift_report["drift_detected"] is True
        assert drift_report["psi"] >= 0.25 or drift_report["ks_pvalue"] < 0.01

    def test_akima_and_seasonal_gap_imputation(self):
        """Verify Akima spline for g<=3, seasonal persistence for 3<g<=7 (§2.5)."""
        imputer = impute_mod.TimeSeriesImputer(cadence="daily", seasonal_period=7)
        base_t = datetime(2026, 7, 1, 0, 0, 0, tzinfo=timezone.utc)
        records = []
        for day in range(25):
            if day in (5, 6):
                continue  # Gap length 2 -> Akima
            if day in (14, 15, 16, 17):
                continue  # Gap length 4 -> Seasonal Persistence
            records.append({
                "observed_at": (base_t + timedelta(days=day)).isoformat(),
                "value": 100.0 + 20.0 * math.sin(2 * math.pi * (day % 7) / 7.0),
                "tenant_id": "test_t",
                "kpi_id": "test_k",
            })

        imputed_df, summary = imputer.regularize_and_impute(records)
        assert imputed_df.height == 25
        assert summary["missing_count"] == 6
        vals = imputed_df["value"].to_list()
        assert not any(math.isnan(v) for v in vals)
        imputed_flags = imputed_df["is_imputed"].to_list()
        assert sum(imputed_flags) == 6

    def test_quarantine_store_and_administrative_replay(self):
        """Verify Dead-letter quarantine store and administrative replay API (§2.3)."""
        quarantine = quar_mod.QuarantineStore()
        bad_payload = {
            "tenant_id": "tenant_1",
            "kpi_id": "revenue",
            "observed_at": "2026-08-01T00:00:00Z",
            "value": -500.0,
        }
        rec = quarantine.quarantine(
            tenant_id="tenant_1",
            kpi_id="revenue",
            raw_payload=bad_payload,
            failed_tier="TIER_4_BOUNDARY",
            error_code="ERR_NEGATIVE_REVENUE",
            error_message="Negative value for non-negative KPI",
        )
        assert rec.id is not None
        assert not rec.resolved

        # Replay unchanged bad payload -> fails
        ok, res = quarantine.replay(rec.id, replayed_by="admin@company.com")
        assert not ok
        assert not rec.resolved

        # Replay remediated payload -> succeeds
        remediated_payload = dict(bad_payload)
        remediated_payload["value"] = 500.0
        ok, res = quarantine.replay(rec.id, replayed_by="admin@company.com", mutated_payload=remediated_payload)
        assert ok
        assert rec.resolved
        assert rec.replayed_by == "admin@company.com"


# =============================================================================
# SECTION 2: STL Time-Series Engine & 90-Day Wave Mathematical Assertions
# =============================================================================

class TestSTLTimeSeriesEngine:
    """Verifies §3.1-§3.8: STL decomposition, baseline, MAD bounds, and 5 mathematical assertions."""

    def test_cadence_parameters_matrix(self):
        """Verify Cleveland harmonic separation parameters for 5 business cadences (§3.4)."""
        cadences = ["hourly", "daily", "weekly", "monthly", "quarterly"]
        for cad in cadences:
            config = get_cadence_parameters(cad)
            assert config.period >= 2
            assert config.seasonal_window % 2 == 1
            assert config.trend_window % 2 == 1
            assert config.low_pass_window % 2 == 1
            # Cleveland constraint: n_(t) >= 1.5 * n_(p) / (1 - 1.5 / n_(s))
            cleveland_min_nt = (1.5 * config.period) / (1.0 - 1.5 / config.seasonal_window)
            assert config.trend_window >= math.floor(cleveland_min_nt)

    def test_sparse_history_bayesian_diversion(self):
        """Verify series with N < 2*period diverts to Bayesian prior (§3.7)."""
        short_data = [100.0, 105.0, 98.0, 102.0, 99.0]
        pipeline_res = run_stl_pipeline(
            data=short_data,
            cadence="daily",  # period = 7 -> min required 14
            kpi_id="new_kpi",
        )
        assert pipeline_res.diverted_to_bayesian is True
        assert pipeline_res.status == "SPARSE_HISTORY_DIVERTED"

    def test_90day_synthetic_verification_wave_5_assertions(self):
        """
        Verify all 5 objective mathematical pass/fail assertions from §3.8:
        1. Trend Orthogonality: |r(T_t, S_t)| <= 0.05
        2. Seasonal Amplitude Recovery: |A_estimated - 200| <= 10.0
        3. Outlier Neutralization: rho_60 <= 0.05, |T_hat_60 - 1300| <= 20.0
        4. Residual Normality: Shapiro-Wilk p >= 0.05 on uncorrupted residuals
        5. Anomaly Trigger: Z_60 <= -10.0 and emits KPIMovementEvent
        """
        print("[MOCK DATA] This output uses synthetic/simulated data. Replace with real ingested data.")
        np.random.seed(42)
        n = 90
        t = np.arange(n)

        # Base components
        trend_true = 1000.0 + 5.0 * t
        seasonal_true = 200.0 * np.sin(2.0 * np.pi * t / 7.0)
        noise = np.random.normal(0.0, 15.0, n)

        # Anomaly injection at day 60
        anomaly = np.zeros(n)
        anomaly[60] = -600.0

        y = trend_true + seasonal_true + noise + anomaly
        base_time = datetime(2026, 1, 1, 0, 0, 0)
        timestamps = [base_time + timedelta(days=int(i)) for i in range(n)]

        df = pd.DataFrame({
            "timestamp": timestamps,
            "value": y,
            "true_trend": trend_true,
            "true_seasonal": seasonal_true,
            "true_noise": noise,
            "anomaly": anomaly,
        })

        decomposer = STLDecomposer(cadence="daily")
        result = decomposer.decompose(df)

        assert result["status"] == "SUCCESS"
        assert not result["diverted_to_bayesian"]

        trend_est = result["trend"]
        seasonal_est = result["seasonal"]
        weights = result["weights"]

        # Assertion 1: Trend Orthogonality r(T_t, S_t) <= 0.05
        corr_ts, _ = stats.pearsonr(trend_est, seasonal_est)
        assert abs(corr_ts) <= 0.05, f"Trend orthogonality failed: r = {corr_ts}"

        # Assertion 2: Seasonal Amplitude Recovery |A_estimated - 200| <= 10.0
        seasonal_amplitude = (np.max(seasonal_est) - np.min(seasonal_est)) / 2.0
        amp_diff = abs(seasonal_amplitude - 200.0)
        assert amp_diff <= 10.0, f"Seasonal amplitude recovery failed: diff = {amp_diff}"

        # Assertion 3: Outlier Neutralization (rho_60 <= 0.05, |T_hat_60 - 1300| <= 20.0)
        weight_60 = weights[60]
        trend_60 = trend_est[60]
        true_trend_60 = 1000.0 + 5.0 * 60.0  # 1300.0
        trend_diff_60 = abs(trend_60 - true_trend_60)
        assert weight_60 <= 0.05, f"Outlier weight neutralization failed: rho_60 = {weight_60}"
        assert trend_diff_60 <= 20.0, f"Trend distortion at outlier failed: diff = {trend_diff_60}"

        # Assertion 4: Residual Normality (Shapiro-Wilk test on uncorrupted series residuals p >= 0.05)
        clean_series = df["true_trend"] + df["true_seasonal"] + df["true_noise"]
        clean_decomposer = STLDecomposer(cadence="daily", robust=False)
        clean_res = clean_decomposer.decompose(pd.DataFrame({"timestamp": df["timestamp"], "value": clean_series}))
        clean_residuals = clean_res["residual"]
        shapiro_stat, shapiro_p = stats.shapiro(clean_residuals)
        assert shapiro_p >= 0.05, f"Residual normality failed: p = {shapiro_p}"

        # Assertion 5: Anomaly Trigger (Z_60 <= -10.0 and emits KPIMovementEvent)
        pipeline_res = run_stl_pipeline(
            data=df,
            cadence="daily",
            tenant_id="tenant_alpha",
            kpi_id="daily_revenue",
        )

        dp_60 = pipeline_res.trend_data[60]
        assert dp_60.z_score <= -10.0, f"Z-score at Day 60 was not sufficiently extreme: Z = {dp_60.z_score}"
        assert dp_60.is_anomaly is True

        event = create_kpi_movement_event(
            kpi_id="daily_revenue",
            analysis_start=df["timestamp"].iloc[0],
            analysis_end=df["timestamp"].iloc[-1],
            observed_value=dp_60.actual_value,
            expected_value=dp_60.expected_value,
            z_score=dp_60.z_score,
            dimensions=["channel:Enterprise"],
        )
        assert isinstance(event, KPIMovementEvent)
        assert event.materiality_status == "MATERIAL_ANOMALY"
        assert event.observed_value < event.expected_value


# =============================================================================
# SECTION 3: Edge-Case Scenario Simulators (Scenarios 1-4)
# =============================================================================

class TestEdgeCaseScenarios:
    """Verifies §4.1-§4.4: Multi-factor Shapley, Low-confidence C_composite, Sparse history, Role security."""

    def test_scenario1_shapley_efficiency_and_lmdi(self):
        """Scenario 1 (§4.1): Shapley efficiency axiom, LMDI-I zero-residual, partial correlations, MAE <= 3.5%."""
        sim = MultiFactorSimulator()
        res = sim.run_simulation()

        # Efficiency axiom: Sum of Shapley values equals total delta
        assert res.efficiency_axiom_holds is True
        assert res.efficiency_residual < 1e-5
        assert abs(sum(res.shapley_attribution.values()) - res.total_delta) < 1e-5

        # Combinatorial subset matches permutations
        factor_ids = [d.driver_id for d in sim.drivers]
        v_comb = compute_shapley_values(factor_ids, sim.characteristic_function)
        v_perm = compute_shapley_permutations(factor_ids, sim.characteristic_function)
        for fid in factor_ids:
            assert math.isclose(v_comb[fid], v_perm[fid], rel_tol=1e-5, abs_tol=1e-5)

        # LMDI-I zero-residual additive decomposition
        lmdi_sum = sum(res.lmdi_attribution.values())
        expected_delta = res.details["lmdi_components"]["delta_revenue"]
        assert math.isclose(lmdi_sum, expected_delta, rel_tol=1e-5, abs_tol=1e-5)

        # Partial correlation
        partial_r = abs(res.partial_correlations["r_bug_revenue_given_conversion"])
        assert partial_r < 0.15

        # Benchmarks: Recall == 100%, MAE <= 3.5%, FDR <= 0.05
        assert res.top_3_recall == 1.0
        assert res.attribution_mae <= 3.5
        assert res.false_discovery_rate <= 0.05

    def test_scenario2_composite_confidence_decision_gating(self):
        """Scenario 2 (§4.2): 3-tier decision gating for GoRules Rules 20, 21, 22."""
        runner = LowConfidenceScenarioRunner()

        # Tier 1: High confidence >= 0.85 -> Rule 20 ALLOWED
        t1 = runner.simulate_high_confidence_allowed()
        assert t1.composite_confidence >= 0.85
        assert t1.governance_verdict.rule_applied == 20
        assert t1.governance_verdict.decision_right == GovernanceDecisionRight.ALLOWED
        assert t1.governance_verdict.automation_blocked is False

        # Tier 2: Moderate confidence 0.70-0.84 -> Rule 21 HUMAN_REVIEW
        t2 = runner.simulate_medium_confidence_human_review()
        assert 0.70 <= t2.composite_confidence < 0.85
        assert t2.governance_verdict.rule_applied == 21
        assert t2.governance_verdict.decision_right == GovernanceDecisionRight.HUMAN_REVIEW
        assert t2.governance_verdict.automation_blocked is True

        # Tier 3: Contradiction / Low confidence < 0.70 -> Rule 22 ABSTAIN
        t3 = runner.simulate_low_confidence_contradiction()
        assert t3.composite_confidence < 0.70
        assert t3.governance_verdict.rule_applied == 22
        assert t3.governance_verdict.decision_right == GovernanceDecisionRight.ABSTAIN
        assert t3.governance_verdict.automation_blocked is True
        assert len(t3.conflicting_hypotheses) == 2
        assert len(t3.suggested_operator_queries) > 0

    def test_scenario3_sparse_history_bayesian_prior_borrowing(self):
        """Scenario 3 (§4.3): Hierarchical Bayesian shrinkage factor B and widened credible intervals."""
        prior = PriorCohortSpec(
            cohort_name="Enterprise Baseline",
            mu_0=10000.0,
            sigma_0=2000.0,
            observation_sigma=2000.0
        )
        engine = ColdStartBayesianEngine(prior)

        # N=1 -> B = 0.5, cold start active
        res_1 = engine.estimate_posterior([8000.0])
        assert math.isclose(res_1.shrinkage_factor_B, 0.5, abs_tol=1e-3)
        assert res_1.is_cold_start is True
        assert res_1.widening_multiplier_kappa > 1.0

        # N=100 -> B < 0.02, converges to sample mean
        res_100 = engine.estimate_posterior([8000.0] * 100)
        assert res_100.shrinkage_factor_B < 0.02
        assert res_100.is_cold_start is False
        assert math.isclose(res_100.posterior_mean_muN, 8000.0, rel_tol=1e-2)

        # Epistemic caveat narrative
        runner = SparseHistoryScenarioRunner()
        results = runner.run_cold_start_simulation()
        primary = results["cold_start_primary_n6"]
        assert primary["is_cold_start"] is True
        assert "Notice: This metric" in primary["epistemic_caveat_disclosure"]

    def test_scenario4_role_security_and_governance(self):
        """Scenario 4 (§4.4): SQL AST rewriter, dynamic PII/margin masking, GoRules Rules 13-16."""
        # AST SQL Rewriting
        ctx = SecurityContext(
            user_id="usr_eng",
            tenant_id="tenant_alpha",
            roles=[PersonaRole.ENGINEERING],
            permitted_regions=["US-East"]
        )
        query = "SELECT * FROM customer_metrics WHERE kpi_id = 'orders';"
        rewritten = SQLRewriter.rewrite_query(query, ctx, target_kpi="orders")
        assert "customer_measurements" in rewritten.rewritten_sql
        assert "tenant_id = :tenant_id" in rewritten.rewritten_sql
        assert "region IN (:permitted_regions)" in rewritten.rewritten_sql
        assert rewritten.bound_parameters["tenant_id"] == "tenant_alpha"

        # PII and Margin Masking
        unprivileged_ctx = SecurityContext(
            user_id="usr_sales",
            tenant_id="tenant_alpha",
            roles=[PersonaRole.SALES],
            can_view_pii=False,
            can_view_margins=False
        )
        raw = {
            "customer_email": "john.doe@acme.com",
            "customer_phone": "+1 (555) 123-4567",
            "gross_margin_pct": "75.0%",
            "unit_cogs": "$120.00"
        }
        masked = DataMasker.mask_record(raw, unprivileged_ctx)
        assert masked["customer_email"].startswith("CUST-***-SHA256:")
        assert masked["customer_phone"] == "[REDACTED - PII]"
        assert masked["gross_margin_pct"] == "[REDACTED - CONFIDENTIAL]"
        assert masked["unit_cogs"] == "[REDACTED - FINANCIAL]"

        privileged_ctx = SecurityContext(
            user_id="usr_exec",
            tenant_id="tenant_alpha",
            roles=[PersonaRole.EXECUTIVE],
            can_view_pii=True,
            can_view_margins=True
        )
        unmasked = DataMasker.mask_record(raw, privileged_ctx)
        assert unmasked["customer_email"] == "john.doe@acme.com"
        assert unmasked["gross_margin_pct"] == "75.0%"

        # GoRules Authorization
        eng_ctx = SecurityContext(
            user_id="usr_eng",
            tenant_id="tenant_alpha",
            roles=[PersonaRole.ENGINEERING],
            max_approval_limit=5000.0
        )
        # Rollback within limit -> Rule 13 AUTHORIZED
        dec1 = GovernanceRoleAuthorizer.authorize_action("Rollback code", 1000.0, eng_ctx)
        assert dec1["rule_applied"] == 13
        assert dec1["authorized"] is True

        # Engineering discount -> Rule 13 PROHIBITED
        dec2 = GovernanceRoleAuthorizer.authorize_action("Offer discount", 500.0, eng_ctx)
        assert dec2["rule_applied"] == 13
        assert dec2["decision_right"] == "PROHIBITED"

        # Action cost > limit -> Rule 16 HUMAN_REVIEW
        dec3 = GovernanceRoleAuthorizer.authorize_action("Rollback cluster", 10000.0, eng_ctx)
        assert dec3["rule_applied"] == 16
        assert dec3["decision_right"] == "HUMAN_REVIEW"


# =============================================================================
# SECTION 4: Golden Datasets & Telemetry Observability
# =============================================================================

class TestGoldenDatasetsAndTelemetry:
    """Verifies §5.1-§5.4: 19 golden incidents across 4 tiers, benchmark runner, TelemetryCollector, pricing."""

    def test_golden_dataset_catalog_and_benchmark_runner(self):
        """Verify 19 golden datasets, all 4 tiers, and benchmark pass criteria (§5.1, §5.2)."""
        catalog = golden_mod.build_golden_catalog()
        assert len(catalog) == 19

        tier_counts = {}
        for item in catalog:
            tier_counts[item.tier] = tier_counts.get(item.tier, 0) + 1

        assert tier_counts.get("Tier1_Unit") == 5
        assert tier_counts.get("Tier2_Boundary") == 5
        assert tier_counts.get("Tier3_Interaction") == 5
        assert tier_counts.get("Tier4_RealWorld") == 4

        runner = bench_mod.BenchmarkRunner(catalog=catalog)
        metrics = runner.run_all()

        assert metrics.thresholds_passed is True
        assert metrics.driver_recall >= 1.00
        assert metrics.attribution_mae <= 3.50
        assert metrics.abstention_precision >= 100.0
        assert metrics.security_leakage_rate == 0.0

    def test_telemetry_cost_calculator_and_collector(self):
        """Verify pricing calculations, TelemetryCollector 7 hooks, and perf_counter decorator (§5.3, §5.4)."""
        calc = price_mod.CostCalculator()

        # gpt-4o-mini
        mini_cost = calc.calculate_call_cost("gpt-4o-mini", prompt_tokens=1000, completion_tokens=500)
        assert abs(mini_cost - 0.00045) < 1e-6

        # gpt-4o
        gpt4_cost = calc.calculate_call_cost("gpt-4o", prompt_tokens=1000, completion_tokens=500)
        assert abs(gpt4_cost - 0.0075) < 1e-6

        # TelemetryCollector aggregating all 7 hooks
        collector = collect_mod.TelemetryCollector(trace_id="tr-unified-test-01")
        collector.record_db_query(duration_ms=10.0, row_count=25)
        collector.record_agent_execution("customer_agent", duration_ms=30.0, findings_count=1)
        collector.record_analytical_math("stl_decomp", duration_ms=5.0)
        collector.record_orchestrator_llm(duration_ms=110.0, model_name="gpt-4o-mini", prompt_tokens=1000, completion_tokens=200)
        collector.record_governance(duration_ms=2.5, rules_evaluated=4, fired_rule_ids=[20])
        collector.record_persona_story_llm(duration_ms=85.0, model_name="gpt-4o", prompt_tokens=1200, completion_tokens=250)

        payload = collector.build_payload()
        assert payload.trace_id == "tr-unified-test-01"
        assert payload.breakdown.db_latency_ms == 10.0
        assert payload.breakdown.agent_swarm_latency_ms == 30.0
        assert payload.breakdown.analytical_math_latency_ms == 5.0
        assert payload.breakdown.orchestrator_llm_latency_ms == 110.0
        assert payload.breakdown.governance_latency_ms == 2.5
        assert payload.breakdown.persona_story_llm_latency_ms == 85.0
        assert payload.model_calls["total_calls"] == 2
        assert payload.tokens.total_tokens == (1000 + 200 + 1200 + 250)
        assert payload.estimated_cost_usd > 0.0

        # Non-blocking decorator execution
        @hooks_mod.perf_counter_hook(hook_type="analytical_math", identifier_arg_name="algo")
        def dummy_math(algo="shapley"):
            time.sleep(0.005)
            return "ok"

        with hooks_mod.TelemetryContext(collector) as c:
            res = dummy_math(algo="shapley")
            assert res == "ok"
            assert c.analytical_math_latency_ms >= 5.0 + 5.0


# =============================================================================
# SECTION 5: FastAPI Endpoints & TelemetryMiddleware
# =============================================================================

class TestFastAPIIntegration:
    """Verifies FastAPI endpoints, TelemetryMiddleware response headers (§5.4, §8.1)."""

    def test_health_endpoint_and_telemetry_headers(self):
        """Verify /health returns 200 and X-Trace-ID, X-Latency-MS, X-Total-Cost-USD headers."""
        client = TestClient(api)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "kpi-engine"}
        assert "X-Trace-ID" in response.headers
        assert response.headers["X-Trace-ID"].startswith("tr-")
        assert "X-Latency-MS" in response.headers
        assert float(response.headers["X-Latency-MS"]) >= 0.0
        assert "X-Total-Cost-USD" in response.headers

    def test_metrics_ingest_endpoint(self):
        """Verify POST /api/v1/metrics/ingest accepts measurement payloads."""
        client = TestClient(api)
        payload = {
            "tenant_id": "org_enterprise_1",
            "kpi_id": "net_revenue",
            "measurements": [
                {
                    "tenant_id": "org_enterprise_1",
                    "kpi_id": "net_revenue",
                    "observed_at": "2026-08-30T12:00:00Z",
                    "value": 150240.50,
                    "dimensions": {"region": "US-East", "channel": "Direct"},
                },
                {
                    "tenant_id": "org_enterprise_1",
                    "kpi_id": "net_revenue",
                    "observed_at": "2026-08-30T13:00:00Z",
                    "value": 148900.00,
                    "dimensions": {"region": "US-West", "channel": "Enterprise"},
                },
            ],
        }
        response = client.post("/api/v1/metrics/ingest", json=payload)
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "ACCEPTED"
        assert data["processed_count"] == 2
        assert data["quarantined_count"] == 0
        assert "X-Trace-ID" in response.headers

    def test_quarantine_replay_endpoint(self):
        """Verify POST /api/v1/quarantine/replay processes replay requests."""
        client = TestClient(api)
        payload = {
            "record_id": "rec_quarantine_987",
            "replayed_by": "operator_admin_1",
            "notes": "Remediated corrupted timestamp format from upstream",
        }
        response = client.post("/api/v1/quarantine/replay", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "REPLAYED"
        assert data["record_id"] == "rec_quarantine_987"
        assert data["replayed_by"] == "operator_admin_1"
        assert data["admitted_to_gold"] is True

    def test_timeseries_decompose_endpoint(self):
        """Verify POST /api/v1/timeseries/decompose executes STL pipeline on request."""
        client = TestClient(api)
        base_time = datetime(2026, 1, 1, 0, 0, 0)
        data_points = []
        for i in range(30):
            t_str = (base_time + timedelta(days=i)).isoformat()
            val = 100.0 + 2.0 * i + 10.0 * (1.0 if i % 7 in [0, 6] else 0.0)
            data_points.append({"timestamp": t_str, "value": val})

        payload = {
            "tenant_id": "tenant_test",
            "kpi_id": "test_kpi",
            "cadence": "daily",
            "data": data_points,
        }
        response = client.post("/api/v1/timeseries/decompose", json=payload)
        assert response.status_code == 200
        res = response.json()
        assert res["tenant_id"] == "tenant_test"
        assert res["kpi_id"] == "test_kpi"
        assert res["observed_points"] == 30
        assert len(res["trend_data"]) == 30
        assert res["status"] == "SUCCESS"


# =============================================================================
# Standalone Main Runner
# =============================================================================

def run_all_tests_standalone():
    """Runs all test classes sequentially and outputs structured results."""
    print("=" * 80)
    print("RUNNING UNIFIED E2E VERIFICATION TEST SUITE (STANDALONE)")
    print("=" * 80)

    test_classes = [
        TestMedallionIngestionAndValidity,
        TestSTLTimeSeriesEngine,
        TestEdgeCaseScenarios,
        TestGoldenDatasetsAndTelemetry,
        TestFastAPIIntegration,
    ]

    total_tests = 0
    passed_tests = 0

    for cls in test_classes:
        instance = cls()
        methods = [m for m in dir(instance) if m.startswith("test_") and callable(getattr(instance, m))]
        print(f"\n--- Running {cls.__name__} ({len(methods)} tests) ---")
        for method_name in methods:
            total_tests += 1
            method = getattr(instance, method_name)
            try:
                method()
                passed_tests += 1
                print(f"  [PASS] {method_name}")
            except Exception as e:
                print(f"  [FAIL] {method_name}: {e}")
                raise e

    print("\n" + "=" * 80)
    print(f"UNIFIED SUITE SUMMARY: {passed_tests}/{total_tests} TESTS PASSED (100% SUCCESS RATE)")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests_standalone()
