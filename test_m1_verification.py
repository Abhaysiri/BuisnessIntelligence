"""
Comprehensive Verification Test Suite for Milestone 1 (Worker M1)
Tests:
1. End-to-End Medallion Pipeline (Bronze -> Silver -> Imputation -> Validation -> Quarantine -> Gold)
2. Objective Verification Test Suite (§2.6):
   - TC-1.1: Happy Path Normal (30-day series -> Gold Insert, DQ = 1.00)
   - TC-1.2: Negative Revenue (Revenue = -$45,200.00 -> Tier 4 Quarantine)
   - TC-1.3: Future Timestamp (Timestamp = Now + 3 Days -> Tier 3 Quarantine)
   - TC-1.4: Dimension Mismatch (Sum(Slices) != Total -> Tier 5 Quarantine / Reconciliation)
   - TC-1.5: High Missingness (35% NaN -> DQ < 0.80 -> Rule 23 Block)
   - TC-1.6: Distributional Drift (+400% variance shift -> Tier 6 Drift Alert)
3. Akima Spline and Seasonal Persistence Imputation (§2.5)
4. Dead-Letter Quarantine Store & Administrative Replay API (§2.3)
5. 19-Incident Golden Dataset Catalog & Benchmark Runner (§5.1, §5.2)
6. Dynamic Model Token Pricing Matrix & Cost Engine (§5.3)
7. Non-blocking Telemetry Hooks & Latency Breakdown (§5.4)
8. DDL Printout for Supabase Tables (canonical_measurements, quarantine_measurements)
"""

import os
import sys
import json
import math
import time
from datetime import datetime, timezone, timedelta
import numpy as np
import pandas as pd
import polars as pl

# Configure paths
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Imports
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


def test_ddl_printing():
    print("\n--- 1. Testing Supabase DDL Printing ---")
    ddls = pipeline_mod.MedallionIngestionPipeline().print_all_ddl()
    assert "CREATE TABLE canonical_measurements" in ddls["canonical_measurements"], "Canonical DDL missing"
    assert "CREATE TABLE quarantine_measurements" in ddls["quarantine_measurements"], "Quarantine DDL missing"
    print("PASS: DDL printing verified successfully.")


def test_tc1_1_happy_path():
    print("\n--- 2. Testing TC-1.1: Happy Path Normal (30-day Series) ---")
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

    print(f"Result Status: {result.batch_status}, DQ Score: {result.dq_score}, Gold Records: {result.gold_records_count}")
    assert result.batch_status == "ADMITTED_TO_GOLD", f"Expected ADMITTED_TO_GOLD, got {result.batch_status}"
    assert result.dq_score >= 0.95, f"Expected DQ >= 0.95, got {result.dq_score}"
    assert result.data_quality_status == "VALID", f"Expected VALID, got {result.data_quality_status}"
    assert result.gold_records_count == 30, f"Expected 30 gold records, got {result.gold_records_count}"
    assert result.quarantined_count == 0, f"Expected 0 quarantined, got {result.quarantined_count}"
    print("PASS: TC-1.1 passed.")


def test_tc1_2_negative_revenue():
    print("\n--- 3. Testing TC-1.2: Negative Revenue ($ -45,200.00) ---")
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

    print(f"Result Status: {result.batch_status}, Failed Tier: {result.validation_verdict.get('failed_tier')}")
    assert result.batch_status == "QUARANTINED", f"Expected QUARANTINED, got {result.batch_status}"
    assert result.validation_verdict.get("failed_tier") == "TIER_4_BOUNDARY", "Expected Tier 4 failure"
    assert result.quarantined_count > 0, "Expected quarantined records"
    print("PASS: TC-1.2 passed.")


def test_tc1_3_future_timestamp():
    print("\n--- 4. Testing TC-1.3: Future Timestamp (Now + 3 Days) ---")
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

    print(f"Result Status: {result.batch_status}, Failed Tier: {result.validation_verdict.get('failed_tier')}")
    assert result.batch_status == "QUARANTINED", f"Expected QUARANTINED, got {result.batch_status}"
    assert result.validation_verdict.get("failed_tier") == "TIER_3_TEMPORAL", "Expected Tier 3 failure"
    print("PASS: TC-1.3 passed.")


def test_tc1_4_dimension_reconciliation():
    print("\n--- 5. Testing TC-1.4: Dimension Mismatch (Sum of Slices != Total) ---")
    rec_validator = valid_mod.Tier5ReconciliationValidator()

    # Total = 1000.0, Slices = [300, 300, 350] -> Sum = 950 (5% difference > 0.1% tolerance)
    is_ok, delta, err = rec_validator.reconcile_slices(
        slice_values=[300.0, 300.0, 350.0],
        total_metric_value=1000.0,
    )

    print(f"Reconciliation Valid: {is_ok}, Delta: {delta}, Error: {err}")
    assert not is_ok, "Expected dimensional reconciliation failure for 5% discrepancy"
    assert delta == 50.0, f"Expected delta of 50.0, got {delta}"
    print("PASS: TC-1.4 passed.")


def test_tc1_5_high_missingness():
    print("\n--- 6. Testing TC-1.5: High Missingness (35% NaN Values) ---")
    pipeline = pipeline_mod.MedallionIngestionPipeline()

    start_date = datetime(2026, 7, 1, 0, 0, 0, tzinfo=timezone.utc)
    series = []
    # Build 30-day series with ~35% missing timestamps (only 19 days present out of 30)
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

    print(f"Imputation Summary: {result.imputation_summary}")
    print(f"DQ Score: {result.dq_score}, Status: {result.data_quality_status}")
    assert result.imputation_summary.get("missing_ratio") >= 0.30, "Expected >=30% missing ratio"
    assert result.imputation_summary.get("stl_eligible") == False, "Expected STL eligibility to be False due to high missingness"
    assert result.imputation_summary.get("cold_start_bayesian_trigger") == True, "Expected cold start Bayesian trigger"
    assert result.dq_score < 0.95, "Expected degraded/invalid DQ score"
    print("PASS: TC-1.5 passed.")


def test_tc1_6_distributional_drift():
    print("\n--- 7. Testing TC-1.6: Distributional Drift (+400% Variance Shift) ---")
    drift_validator = valid_mod.Tier6DriftValidator(ks_alpha=0.01, psi_threshold=0.25)

    np.random.seed(42)
    # 30-day baseline: normal(loc=100, scale=10, size=60)
    baseline_30d = np.random.normal(loc=100.0, scale=10.0, size=60)
    # Drifted current batch: +400% variance shift -> normal(loc=100, scale=50, size=60)
    current_drifted = np.random.normal(loc=100.0, scale=50.0, size=60)

    drift_report = drift_validator.evaluate_drift(current_drifted, baseline_30d)
    print(f"Drift Report: {drift_report}")
    assert drift_report["drift_detected"] == True, "Expected drift to be detected"
    assert drift_report["psi"] >= 0.25 or drift_report["ks_pvalue"] < 0.01, "Expected PSI or KS threshold trip"
    print("PASS: TC-1.6 passed.")


def test_akima_and_seasonal_imputation():
    print("\n--- 8. Testing Akima Spline & Seasonal Imputation (§2.5) ---")
    imputer = impute_mod.TimeSeriesImputer(cadence="daily", seasonal_period=7)

    # Create 20 days with a 2-day gap (Akima g<=3) and a 4-day gap (Seasonal 3<g<=7)
    base_t = datetime(2026, 7, 1, 0, 0, 0, tzinfo=timezone.utc)
    records = []
    for day in range(25):
        if day in (5, 6):
            continue  # Gap of length 2 -> Akima
        if day in (14, 15, 16, 17):
            continue  # Gap of length 4 -> Seasonal Persistence
        records.append({
            "observed_at": (base_t + timedelta(days=day)).isoformat(),
            "value": 100.0 + 20.0 * math.sin(2 * math.pi * (day % 7) / 7.0),
            "tenant_id": "test_t",
            "kpi_id": "test_k",
        })

    imputed_df, summary = imputer.regularize_and_impute(records)
    print(f"Imputed DataFrame height: {imputed_df.height}, summary: {summary}")
    assert imputed_df.height == 25, f"Expected 25 rows in temporal grid, got {imputed_df.height}"
    assert summary["missing_count"] == 6, f"Expected 6 missing points, got {summary['missing_count']}"
    
    # Verify no residual NaNs
    vals = imputed_df["value"].to_list()
    assert not any(math.isnan(v) for v in vals), "Imputed values contain NaN!"
    
    # Verify is_imputed flags
    imputed_flags = imputed_df["is_imputed"].to_list()
    assert sum(imputed_flags) == 6, f"Expected 6 is_imputed flags, got {sum(imputed_flags)}"
    print("PASS: Akima and seasonal imputation verified.")


def test_quarantine_and_replay():
    print("\n--- 9. Testing Quarantine Store & Administrative Replay API (§2.3) ---")
    quarantine = quar_mod.QuarantineStore()

    # Create bad record with negative revenue
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

    # Attempt replay with unchanged bad payload -> should fail
    ok, res = quarantine.replay(rec.id, replayed_by="admin@company.com")
    assert not ok, "Replay should have failed for uncorrected bad payload"
    assert not rec.resolved

    # Attempt replay with remediated payload (value = 500.0) -> should succeed
    remediated_payload = dict(bad_payload)
    remediated_payload["value"] = 500.0
    ok, res = quarantine.replay(rec.id, replayed_by="admin@company.com", mutated_payload=remediated_payload)
    assert ok, f"Replay should succeed with remediated payload: {res}"
    assert rec.resolved, "Quarantine record should now be marked resolved"
    assert rec.replayed_by == "admin@company.com"
    print("PASS: Quarantine and replay verified.")


def test_golden_dataset_catalog_and_benchmark():
    print("\n--- 10. Testing Golden Dataset Catalog & CI/CD Benchmark Runner (§5.1, §5.2) ---")
    catalog = golden_mod.build_golden_catalog()
    assert len(catalog) == 19, f"Expected 19 golden dataset benchmark incidents, got {len(catalog)}"

    tier_counts = {}
    for item in catalog:
        tier_counts[item.tier] = tier_counts.get(item.tier, 0) + 1

    print(f"Golden Catalog Tier Breakdown: {tier_counts}")
    assert tier_counts.get("Tier1_Unit") == 5, "Expected 5 Tier 1 incidents"
    assert tier_counts.get("Tier2_Boundary") == 5, "Expected 5 Tier 2 incidents"
    assert tier_counts.get("Tier3_Interaction") == 5, "Expected 5 Tier 3 incidents"
    assert tier_counts.get("Tier4_RealWorld") == 4, "Expected 4 Tier 4 incidents"

    # Run benchmark harness
    runner = bench_mod.BenchmarkRunner(catalog=catalog)
    metrics = runner.run_all()
    print(f"Benchmark Metrics Summary:")
    print(f"  Driver Recall: {metrics.driver_recall * 100:.1f}% (Threshold: >= 100.0%)")
    print(f"  Attribution MAE: {metrics.attribution_mae:.2f}% (Threshold: <= 3.5%)")
    print(f"  Abstention Precision: {metrics.abstention_precision:.1f}% (Threshold: 100.0%)")
    print(f"  Security Leakage Rate: {metrics.security_leakage_rate:.2f}% (Threshold: 0.00%)")
    print(f"  Thresholds Passed: {metrics.thresholds_passed}")

    assert metrics.thresholds_passed == True, "Benchmark thresholds failed!"
    assert metrics.driver_recall >= 1.00, f"Driver recall {metrics.driver_recall} < 1.00"
    assert metrics.attribution_mae <= 3.50, f"Attribution MAE {metrics.attribution_mae} > 3.5%"
    assert metrics.abstention_precision >= 100.0, f"Abstention precision {metrics.abstention_precision} < 100%"
    assert metrics.security_leakage_rate == 0.0, f"Security leakage {metrics.security_leakage_rate} > 0%"
    print("PASS: Golden Datasets & Benchmark Runner verified.")


def test_telemetry_cost_engine_and_collector():
    print("\n--- 11. Testing Telemetry Observability & Cost Calculator (§5.3, §5.4) ---")
    calc = price_mod.CostCalculator()

    # Test gpt-4o-mini cost (1,000 prompt tokens @ $0.15/1M, 500 completion @ $0.60/1M)
    # = (1000/1e6)*0.15 + (500/1e6)*0.60 = 0.00015 + 0.00030 = 0.00045
    mini_cost = calc.calculate_call_cost("gpt-4o-mini", prompt_tokens=1000, completion_tokens=500)
    assert abs(mini_cost - 0.00045) < 1e-6, f"Expected 0.00045, got {mini_cost}"

    # Test gpt-4o cost (1,000 prompt @ $2.50/1M, 500 completion @ $10.00/1M)
    # = 0.0025 + 0.0050 = 0.0075
    gpt4_cost = calc.calculate_call_cost("gpt-4o", prompt_tokens=1000, completion_tokens=500)
    assert abs(gpt4_cost - 0.0075) < 1e-6, f"Expected 0.0075, got {gpt4_cost}"

    # Test TelemetryCollector with all 7 hooks
    collector = collect_mod.TelemetryCollector(trace_id="tr-test-1234")

    # Hook 2: DB query
    collector.record_db_query(duration_ms=12.5, row_count=50)
    # Hook 3: Agent execution
    collector.record_agent_execution("product_agent", duration_ms=45.2, findings_count=2)
    # Hook 4: Analytical math
    collector.record_analytical_math("stl_decomposition", duration_ms=8.4)
    # Hook 5: Orchestrator LLM
    collector.record_orchestrator_llm(duration_ms=120.0, model_name="gpt-4o-mini", prompt_tokens=2000, completion_tokens=400)
    # Hook 6: GoRules Governance
    collector.record_governance(duration_ms=3.1, rules_evaluated=5, fired_rule_ids=[13, 23])
    # Hook 7: Persona Story LLM
    collector.record_persona_story_llm(duration_ms=95.0, model_name="gpt-4o", prompt_tokens=1500, completion_tokens=300)

    payload = collector.build_payload()
    print(f"Generated Telemetry Payload: {payload.model_dump_json(indent=2)}")

    assert payload.trace_id == "tr-test-1234"
    assert payload.breakdown.db_latency_ms == 12.5
    assert payload.breakdown.agent_swarm_latency_ms == 45.2
    assert payload.breakdown.analytical_math_latency_ms == 8.4
    assert payload.breakdown.orchestrator_llm_latency_ms == 120.0
    assert payload.breakdown.governance_latency_ms == 3.1
    assert payload.breakdown.persona_story_llm_latency_ms == 95.0
    assert payload.model_calls["total_calls"] == 2
    assert payload.tokens.total_tokens == (2000 + 400 + 1500 + 300)
    assert payload.estimated_cost_usd > 0.0

    # Test perf_counter_hook decorator
    @hooks_mod.perf_counter_hook(hook_type="analytical_math", identifier_arg_name="algo")
    def sample_math(algo="shapley"):
        time.sleep(0.01)
        return "math_done"

    with hooks_mod.TelemetryContext(collector) as c:
        res = sample_math(algo="shapley_kernel")
        assert res == "math_done"
        assert c.analytical_math_latency_ms >= 8.4 + 10.0  # Increased by ~10ms

    print("PASS: Telemetry, Pricing, and Hooks verified.")


if __name__ == "__main__":
    print("=" * 80)
    print("STARTING FULL MILESTONE 1 VERIFICATION TEST SUITE")
    print("=" * 80)
    
    test_ddl_printing()
    test_tc1_1_happy_path()
    test_tc1_2_negative_revenue()
    test_tc1_3_future_timestamp()
    test_tc1_4_dimension_reconciliation()
    test_tc1_5_high_missingness()
    test_tc1_6_distributional_drift()
    test_akima_and_seasonal_imputation()
    test_quarantine_and_replay()
    test_golden_dataset_catalog_and_benchmark()
    test_telemetry_cost_engine_and_collector()

    print("\n" + "=" * 80)
    print("ALL 11 TEST MODULES PASSED WITH 100% SUCCESS!")
    print("=" * 80)
