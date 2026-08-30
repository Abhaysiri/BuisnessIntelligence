## 2026-08-30T17:00:24Z
You are Worker M3 for the Business Intelligence Engine project.

Your assigned working directory for metadata/progress is: c:\Users\Abhay\Desktop\CODING\BuisnessIntelligence.ai\.agents\worker_m3\
The project root is: c:\Users\Abhay\Desktop\CODING\BuisnessIntelligence.ai

Read the authoritative requirements and architectural specifications:
- `c:\Users\Abhay\Desktop\CODING\BuisnessIntelligence.ai\.agents\ORIGINAL_REQUEST.md` (Read thoroughly!)
- `c:\Users\Abhay\Desktop\CODING\BuisnessIntelligence.ai\PROJECT.md`
- `c:\Users\Abhay\Desktop\CODING\BuisnessIntelligence.ai\BI_ENGINE_IMPLEMENTATION_PLAN.md` (Specifically §4.1-4.4, §6. Do NOT edit this plan file!)

CRITICAL CONSTRAINTS:
1. Do NOT push, commit, or interact with git.
2. Do NOT edit BI_ENGINE_IMPLEMENTATION_PLAN.md.
3. Do NOT modify any existing files under kpi-engine/ unless explicitly required for integration.
4. DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
5. All outputs from edge-case simulators MUST print at runtime: `[MOCK DATA] This output uses synthetic/simulated data. Replace with real ingested data.`
6. Frontend styling: Use existing Tailwind CSS styling (slate palette, blue-600 accents, clean flat design, no glassmorphism).

YOUR SCOPE & CODE OWNERSHIP:
Build the following directories and files:
`edge_cases/`
- `multifactor.py` (Scenario 1 §4.1): Simulate multi-factor KPI movement with 3 concurrent drivers acting simultaneously across dimensions (e.g. Factor A: -40% conversion rate in Self-Serve, Factor B: -25% ad spend in Paid Social, Factor C: +10% compensatory surge in Direct Sales). Implement exact cooperative game-theoretic Shapley value attribution using `itertools` for all 2^M coalition permutations. Implement LMDI-I (Logarithmic Mean Divisia Index) for multiplicative metric trees. Validate that sum of Shapley values equals total observed delta (Efficiency axiom). Validate Top-3 driver recall and MAE <= 3.5%. Print `[MOCK DATA]` notice at runtime.
- `low_confidence.py` (Scenario 2 §4.2): Simulate contradictory evidence (e.g. Customer Agent finds payment gateway timeout vs Channel Agent finds promotional discount expired). Compute multi-layer composite confidence score C_composite = w_e*C_evidence + w_t*C_temporal + w_d*C_dag - P_contradictions - P_sample (weights: 0.35, 0.35, 0.30). Implement 3-tier decision gating: C_composite >= 0.85 -> Rule 20 (ALLOWED), 0.70 <= C_composite < 0.85 -> Rule 21 (HUMAN_REVIEW with clarification prompt), C_composite < 0.70 -> Rule 22 (ABSTAIN, block automation). Generate structured clarification payload JSON with conflicting hypotheses and suggested queries. Print `[MOCK DATA]` notice at runtime.
- `sparse_history.py` (Scenario 3 §4.3): Simulate cold-start newly launched KPI with N < 14 days. Implement Hierarchical Empirical Bayesian prior borrowing: theta_new ~ N(mu_0, sigma_0^2) from parent cohort, compute posterior mean mu_N = (1-B)*y_bar + B*mu_0 with shrinkage factor B = kappa_0 / (kappa_0 + N), posterior variance sigma_N^2. Implement dynamic 95% Bayesian credible interval widening: kappa(N) = 1.0 + 2.5/sqrt(N), bounds = [mu_N - 1.96*kappa(N)*sigma_N, mu_N + 1.96*kappa(N)*sigma_N]. Generate mandatory epistemic caveat persona narrative disclosure. Print `[MOCK DATA]` notice at runtime.
- `role_security.py` (Scenario 4 §4.4): Implement SecurityContext model (user_id, tenant_id, roles: EXECUTIVE/FINANCE/ENGINEERING/SALES, permitted_metrics, permitted_dimensions, can_view_margins, can_view_pii, max_approval_limit). Implement multi-tenant AST/regex parameterized SQL rewriter (injects WHERE tenant_id=:tenant_id AND region IN (:permitted_regions)). Implement dynamic cryptographic PII & margin masking (e.g. email -> CUST-***-SHA256:..., phone -> [REDACTED - PII], gross_margin -> [REDACTED - CONFIDENTIAL]). Implement GoRules Rules 13-16 role authorization checks. Print `[MOCK DATA]` notice at runtime.

`frontend/Dashboard/src/`
- Explore existing `frontend/Dashboard/` structure to understand the React setup, components, router, and styling.
- Create the Upload Documents page (e.g. `frontend/Dashboard/src/pages/UploadDocuments.jsx`) with:
  * 2-column layout:
    - Column 1: Unstructured Data (PDFs, Word docs, emails, images)
    - Column 2: Structured Data (CSV, Excel, JSON, Parquet)
  * Drag-and-drop upload zone in each column with file type hints and file picker fallback.
  * Upload simulation posting to `/api/v1/metrics/ingest` with progress indicator and success/error toast notifications.
  * Tailwind CSS styling matching existing Dashboard (slate palette, blue-600 accents, clean flat design).
- Register the route in `frontend/Dashboard/src/App.jsx` under the existing React Router setup (e.g. path `/upload` or `/upload-documents`) and ensure the sidebar "Upload Documents" link navigates to this page.
