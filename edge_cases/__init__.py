"""
edge_cases package
Simulated KPI scenario data & runners for the Business Intelligence Engine.

Scenarios:
  - multifactor: Scenario 1 (§4.1) Multi-factor KPI movement with Shapley attribution & LMDI-I
  - low_confidence: Scenario 2 (§4.2) Low-confidence with multi-layer C_composite & GoRules Rules 20-22
  - sparse_history: Scenario 3 (§4.3) Cold-start Bayesian prior borrowing & widened credible intervals
  - role_security: Scenario 4 (§4.4) Role-based security, SQL rewriting, PII masking & GoRules Rules 13-16
"""

from edge_cases.multifactor import (
    MultiFactorSimulator,
    MultiFactorScenarioResult,
    compute_shapley_values,
    compute_lmdi_additive,
    run_scenario as run_multifactor_scenario,
)
from edge_cases.low_confidence import (
    ConfidenceEngine,
    ConfidenceBreakdown,
    ClarificationPayload,
    LowConfidenceScenarioRunner,
    run_scenario as run_low_confidence_scenario,
)
from edge_cases.sparse_history import (
    PriorCohortSpec,
    BayesianEstimateResult,
    ColdStartBayesianEngine,
    SparseHistoryScenarioRunner,
    run_scenario as run_sparse_history_scenario,
)
from edge_cases.role_security import (
    PersonaRole,
    SecurityContext,
    SQLRewriter,
    DataMasker,
    ABACFilter,
    GovernanceRoleAuthorizer,
    RoleSecurityScenarioRunner,
    run_scenario as run_role_security_scenario,
)

__all__ = [
    "MultiFactorSimulator",
    "MultiFactorScenarioResult",
    "compute_shapley_values",
    "compute_lmdi_additive",
    "run_multifactor_scenario",
    "ConfidenceEngine",
    "ConfidenceBreakdown",
    "ClarificationPayload",
    "LowConfidenceScenarioRunner",
    "run_low_confidence_scenario",
    "PriorCohortSpec",
    "BayesianEstimateResult",
    "ColdStartBayesianEngine",
    "SparseHistoryScenarioRunner",
    "run_sparse_history_scenario",
    "PersonaRole",
    "SecurityContext",
    "SQLRewriter",
    "DataMasker",
    "ABACFilter",
    "GovernanceRoleAuthorizer",
    "RoleSecurityScenarioRunner",
    "run_role_security_scenario",
]
