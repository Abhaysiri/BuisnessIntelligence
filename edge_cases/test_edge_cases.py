"""
test_edge_cases.py
Automated deterministic test harness for all 4 edge-case scenario modules (§4.1-§4.4).
"""

import math
import os
import sys
import numpy as np

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from edge_cases.multifactor import (
    MultiFactorSimulator,
    compute_shapley_values,
    compute_shapley_permutations,
    compute_lmdi_additive,
    calculate_first_order_partial_correlation
)
from edge_cases.low_confidence import (
    ConfidenceEngine,
    LowConfidenceScenarioRunner,
    GovernanceDecisionRight
)
from edge_cases.sparse_history import (
    PriorCohortSpec,
    ColdStartBayesianEngine,
    SparseHistoryScenarioRunner
)
from edge_cases.role_security import (
    PersonaRole,
    SecurityContext,
    SQLRewriter,
    DataMasker,
    ABACFilter,
    GovernanceRoleAuthorizer,
    RoleSecurityScenarioRunner
)


# ============================================================================
# Scenario 1 Tests (§4.1)
# ============================================================================

def test_scenario1_efficiency_axiom():
    """Verify that sum of Shapley values exactly equals total observed delta."""
    sim = MultiFactorSimulator()
    res = sim.run_simulation()
    assert res.efficiency_axiom_holds is True
    assert res.efficiency_residual < 1e-5
    assert abs(sum(res.shapley_attribution.values()) - res.total_delta) < 1e-5


def test_scenario1_combinatorial_vs_permutations():
    """Verify combinatorial subset Shapley formulation matches full permutation enumeration."""
    sim = MultiFactorSimulator()
    factor_ids = [d.driver_id for d in sim.drivers]
    v_comb = compute_shapley_values(factor_ids, sim.characteristic_function)
    v_perm = compute_shapley_permutations(factor_ids, sim.characteristic_function)
    for fid in factor_ids:
        assert math.isclose(v_comb[fid], v_perm[fid], rel_tol=1e-5, abs_tol=1e-5)


def test_scenario1_lmdi_zero_residual():
    """Verify LMDI-I decomposition sums exactly to total delta."""
    sim = MultiFactorSimulator()
    res = sim.run_simulation()
    lmdi_sum = sum(res.lmdi_attribution.values())
    expected_delta = res.details["lmdi_components"]["delta_revenue"]
    assert math.isclose(lmdi_sum, expected_delta, rel_tol=1e-5, abs_tol=1e-5)


def test_scenario1_partial_correlation():
    """Verify partial correlation isolates direct vs mediated influence."""
    sim = MultiFactorSimulator()
    res = sim.run_simulation()
    # Product Bug and Revenue controlling for Conversion should be near zero (< 0.15)
    partial_r = abs(res.partial_correlations["r_bug_revenue_given_conversion"])
    assert partial_r < 0.15


def test_scenario1_benchmarks():
    """Verify MAE <= 3.5%, Top-3 Recall == 100%, FDR <= 0.05."""
    sim = MultiFactorSimulator()
    res = sim.run_simulation()
    assert res.top_3_recall == 1.0
    assert res.attribution_mae <= 3.5
    assert res.false_discovery_rate <= 0.05


# ============================================================================
# Scenario 2 Tests (§4.2)
# ============================================================================

def test_scenario2_decision_gating_tiers():
    """Verify 3-tier decision gating for GoRules Rules 20, 21, and 22."""
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


# ============================================================================
# Scenario 3 Tests (§4.3)
# ============================================================================

def test_scenario3_bayesian_shrinkage_convergence():
    """Verify Bayesian shrinkage factor B decays as N grows and mean converges to sample."""
    prior = PriorCohortSpec(
        cohort_name="Enterprise Baseline",
        mu_0=10000.0,
        sigma_0=2000.0,
        observation_sigma=2000.0
    )
    engine = ColdStartBayesianEngine(prior)

    # When N=1, B = kappa_0 / (kappa_0 + 1) = 1 / 2 = 0.5
    res_1 = engine.estimate_posterior([8000.0])
    assert math.isclose(res_1.shrinkage_factor_B, 0.5, abs_tol=1e-3)
    assert res_1.is_cold_start is True
    assert res_1.widening_multiplier_kappa > 1.0

    # When N=100, B = 1 / 101 ~= 0.0099
    res_100 = engine.estimate_posterior([8000.0] * 100)
    assert res_100.shrinkage_factor_B < 0.02
    assert res_100.is_cold_start is False
    assert math.isclose(res_100.posterior_mean_muN, 8000.0, rel_tol=1e-2)


def test_scenario3_epistemic_caveat():
    """Verify epistemic caveat persona narrative format."""
    runner = SparseHistoryScenarioRunner()
    results = runner.run_cold_start_simulation()
    primary = results["cold_start_primary_n6"]
    assert primary["is_cold_start"] is True
    assert "Notice: This metric" in primary["epistemic_caveat_disclosure"]
    assert "widened by" in primary["epistemic_caveat_disclosure"]


# ============================================================================
# Scenario 4 Tests (§4.4)
# ============================================================================

def test_scenario4_sql_rewriter_tenant_isolation():
    """Verify SQL rewriter injects WHERE tenant_id and region."""
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


def test_scenario4_pii_and_margin_masking():
    """Verify dynamic cryptographic masking of emails, phones, and gross margins."""
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
    assert unmasked["customer_phone"] == "+1 (555) 123-4567"
    assert unmasked["gross_margin_pct"] == "75.0%"
    assert unmasked["unit_cogs"] == "$120.00"


def test_scenario4_gorules_authorization():
    """Verify Rules 13-16 role authorization checks."""
    eng_ctx = SecurityContext(
        user_id="usr_eng",
        tenant_id="tenant_alpha",
        roles=[PersonaRole.ENGINEERING],
        max_approval_limit=5000.0
    )
    # Engineering rollback within limit -> AUTHORIZED (Rule 13)
    dec1 = GovernanceRoleAuthorizer.authorize_action("Rollback code", 1000.0, eng_ctx)
    assert dec1["rule_applied"] == 13
    assert dec1["authorized"] is True

    # Engineering discount -> PROHIBITED (Rule 13)
    dec2 = GovernanceRoleAuthorizer.authorize_action("Offer discount", 500.0, eng_ctx)
    assert dec2["rule_applied"] == 13
    assert dec2["decision_right"] == "PROHIBITED"

    # Action cost > limit -> Rule 16 HUMAN_REVIEW
    dec3 = GovernanceRoleAuthorizer.authorize_action("Rollback cluster", 10000.0, eng_ctx)
    assert dec3["rule_applied"] == 16
    assert dec3["decision_right"] == "HUMAN_REVIEW"


if __name__ == "__main__":
    test_functions = [
        test_scenario1_efficiency_axiom,
        test_scenario1_combinatorial_vs_permutations,
        test_scenario1_lmdi_zero_residual,
        test_scenario1_partial_correlation,
        test_scenario1_benchmarks,
        test_scenario2_decision_gating_tiers,
        test_scenario3_bayesian_shrinkage_convergence,
        test_scenario3_epistemic_caveat,
        test_scenario4_sql_rewriter_tenant_isolation,
        test_scenario4_pii_and_margin_masking,
        test_scenario4_gorules_authorization,
    ]
    print(f"Running {len(test_functions)} automated test cases...")
    for fn in test_functions:
        fn()
        print(f"  [PASS] {fn.__name__}")
    print("\nALL TEST CASES PASSED SUCCESSFULLY!")
