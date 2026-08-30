# Specialist Research & Survey Report: Requirements R3 & R4
## KPI Scenario Testing Strategy, Golden Datasets & Runtime Telemetry Architecture

**Author:** Explorer 3 (KPI Scenarios, Telemetry & Golden Datasets Specialist)  
**Date:** 2026-08-30  
**Scope:** Business Intelligence Engine (`kpi-engine`, `frontend`, data schemas, governance layer)  
**Reference Document:** `.agents/ORIGINAL_REQUEST.md`

---

## 1. Executive Summary

The Business Intelligence engine aims to autonomously ingest raw business metrics, detect statistically material KPI movements, mobilize specialized diagnostic agents, apply causal and econometric validation, synthesize governed diagnostic payloads, and generate persona-tailored storytelling with actionable recommendations.

This survey provides a technical investigation into **Requirement R3 (KPI Scenario Testing Strategy)** and **Requirement R4 (Golden Datasets & Runtime Telemetry)**.

### Core Survey Findings:
1. **Testing Infrastructure Gap:** The current repository possesses only single-incident ad-hoc test scripts (`kpi-engine/run_test.py` and `test_visualizers_api.py`). The `kpi-engine/tests` directory is completely empty. There are no automated scenario harnesses, statistical simulators, property-based tests, or continuous benchmarking suites.
2. **Analytical Layer Extension Needed for Scenarios:**
   - **Multi-Factor Attribution (Scenario 1):** The current `calculate_contribution` implementation uses single 1D dimension slices without multi-factor interaction terms, joint covariance, or Shapley value attribution.
   - **Uncertainty & Abstention (Scenario 2):** Current contradiction detection is limited to exact dimensional identity conflicts. A formalized composite confidence index combining evidence, temporal precedence, and dependency graph validity is required to trigger deterministic abstention and clarification protocols.
   - **Cold Start / Sparse History (Scenario 3):** The engine assumes complete historical series in `canonical_measurements`. Missing is a minimum-sample gating threshold ($N_{min} = 14$), hierarchical Bayesian prior borrowing, and surrogate indicator mapping.
   - **Entitlements & Masking (Scenario 4):** While `PersonaRole` exists in `app/schemas/persona.py`, queries in `app/tools/` lack multi-tenant scoping (`tenant_id`), row-level security (RLS), metric-level entitlement filtering, and PII/financial data masking.
3. **Golden Datasets Strategy:** An immutable, version-controlled repository of synthetic and sanitized historical KPI incidents with strict Pydantic contracts is needed for automated regression benchmarking (driver precision/recall, attribution MAE, abstention accuracy).
4. **Runtime Telemetry Strategy:** The UI mockup in `frontend/Dashboard/src/App.jsx` already expects four key telemetry dimensions (`Latency`, `Model Calls`, `Token Usage`, `Est. Cost`). We detail seven exact hook placement points throughout the orchestrator and data pipeline using OpenTelemetry and LangChain callbacks.

---

## 2. Current State of Testing Harnesses & Simulation in the Codebase

### 2.1 Inventory of Existing Testing Assets
| Asset Path | Type | Current Capabilities | Limitations / Missing Elements |
|---|---|---|---|
| `kpi-engine/run_test.py` | Script | Runs a single synthetic 30% revenue drop event (`INC-2026-001`) through `investigation_graph.invoke()` and tests Engineering/Executive persona generation. | Hardcoded single scenario; no assertion framework; does not test edge cases, abstention, cold start, or permissions. |
| `test_visualizers_api.py` | Script | Dispatches mock `DiagnosticPayload` via HTTP POST to FastAPI `/visualizations` on port 8001 and dumps Vega-Lite specs. | Only validates frontend chart schema generation; does not test engine intelligence or causal reasoning. |
| `kpi-engine/tests/` | Directory | Empty (0 files). | No unit test suite, pytest fixtures, mocking harnesses, or automated regression tests. |

### 2.2 Existing Orchestrator & Analytical Execution Flow
The orchestrator graph (`app/orchestrator/graph.py`) is structured as follows:
```
              ┌───> product_agent ────┐
              ├───> customer_agent ───┤
START ────────┼───> geography_agent ──┼───> analysis ───> contradictions ───> orchestrator ───> governance ───> END
              └───> channel_agent ────┘
```
- **Fan-out:** 4 domain agents run concurrently against SQL tools in `app/tools/`.
- **Fan-in:** `analysis_node` runs `calculate_contribution`, `validate_dependency`, `validate_temporal_precedence`, and `calculate_evidence_score`.
- **Contradictions:** `contradiction_node` runs pairwise checks.
- **Synthesis:** `orchestrator_node` invokes `ChatOpenAI(gpt-4o-mini)` or falls back to deterministic rule-based synthesis.
- **Governance:** `governance_node` invokes `ZenEngine` with `app/governance/decision_table.json`.

---

## 3. Architecture for the 4 Key KPI Testing Scenarios (Requirement R3)

### 3.1 Scenario 1: Multi-Factor KPI Movement with Known Drivers

#### A. Problem Formulation
In real-world business environments, a high-level KPI (such as `Total Net Revenue`) rarely drops due to a single isolated root cause. Instead, multiple independent or interacting factors simultaneously push and pull the metric.
*Example Benchmark Incident:*
- **Overall Revenue Impact:** -$100,000 (-20%)
- **Driver A (Technical Failure):** EMEA Checkout Gateway latency spike causing conversion drop (Impact: -$60,000, 60% attribution).
- **Driver B (Marketing Strategy):** Paid search budget cut in North America (Impact: -$50,000, 50% attribution).
- **Driver C (Pricing Tail-wind):** Price increase on Enterprise Tier in APAC (Impact: +$10,000, -10% attribution).
- **Net Simulated Total:** -$60,000 - $50,000 + $10,000 = -$100,000.

#### B. Architectural Design & Enhancements
1. **Mathematical Attribution (Shapley & Additive Decomposition):**
   - Enhance `app/analytics/contribution.py` with multi-dimensional Shapley value decomposition:
     $$\phi_i = \sum_{S \subseteq N \setminus \{i\}} \frac{|S|!(|N| - |S| - 1)!}{|N|!} (v(S \cup \{i\}) - v(S))$$
   - For non-linear multiplicative KPIs ($Revenue = Traffic \times CVR \times AOV$), use logarithmic mean Divisia index (LMDI) or first-order Taylor expansion to ensure exact sum-to-total attribution without unexplained residuals.
2. **Causal Graph & Collinearity Separation:**
   - Expand `app/analytics/dependency.py` (`DEPENDENCY_GRAPH`) to compute partial correlation matrices and structural causal paths using `NetworkX`.
   - Distinguish between **direct root causes** (e.g. checkout outage) and **downstream collateral metrics** (e.g. cart abandonment increase) to prevent double counting.
3. **Simulation Harness:**
   - A deterministic synthetic data generator (`MultiFactorScenarioGenerator`) that populates `canonical_measurements` with ground-truth mathematical formulas.
   - Outputs an evaluation manifest with exact target driver rankings and percentage contributions.

#### C. Evaluation Criteria & Verification Metrics
- **Top-K Driver Recall ($K=3$):** $\ge 1.0$ (all 3 drivers correctly identified).
- **Attribution Mean Absolute Error (MAE):** $\frac{1}{M}\sum |\hat{p}_i - p_i^*| \le 3.5\%$.
- **Causal Ordering Accuracy:** 100% of validated drivers must possess valid directed paths in `DEPENDENCY_GRAPH`.

---

### 3.2 Scenario 2: Low-Confidence Scenario (Clarification & Abstention Protocols)

#### A. Problem Formulation
When incoming data is noisy, contradictory, unaligned temporally, or missing statistical significance, the engine must **not** hallucinate root causes or recommend irreversible operational actions. It must quantify uncertainty, gate execution, and either generate structured clarification requests or abstain entirely.
*Example Benchmark Incident:*
- Marketing agent claims +40% revenue boost from Campaign X.
- Product agent claims -50% drop from SKU stockouts.
- Temporal timestamps show Campaign X started *after* the KPI drop occurred.
- Sample size is statistically insignificant ($p > 0.20, z < 1.5$).

#### B. Architectural Design & Enhancements
1. **Composite Confidence Index ($C_{composite}$):**
   Formulate a standardized scoring function in `app/analytics/evidence.py`:
   $$C_{composite} = w_{ev} \cdot S_{evidence} + w_{temp} \cdot S_{temporal} + w_{dep} \cdot S_{dependency} - \text{Penalty}_{contradictions}$$
   where:
   - $S_{evidence} \in [0, 1]$ (sample volume, source diversity, metric directness).
   - $S_{temporal} = 1.0$ if strictly preceding, else $0.0$.
   - $S_{dependency} = 1.0$ if connected via directed path in DAG, else $0.2$.
   - $\text{Penalty}_{contradictions} = 0.35 \times N_{conflicts}$.
2. **Multi-Threshold Decision Gating:**
   - **$C_{composite} \ge 0.85$ (High Confidence):** Proceed with automated synthesis and standard governed recommendations.
   - **$0.70 \le C_{composite} < 0.85$ (Moderate Confidence):** Trigger `HUMAN_REVIEW` recommendation tier in GoRules (Rule 21).
   - **$C_{composite} < 0.70$ (Low Confidence / Contradiction):** Set `Uncertainty(status="HIGH", abstain=True)`. Halt automated lever generation (GoRules Rule 22).
3. **Structured Disambiguation & Clarification Protocol:**
   - When abstaining, populate `Uncertainty.alternatives` and generate structured clarification prompts for the user/operator:
     - Clarification Type: `TEMPORAL_MISALIGNMENT`, `DIMENSION_CONFLICT`, or `INSUFFICIENT_SAMPLE_SIZE`.
     - Specific Prompt: "Data source A reports EMEA drop of $40k while telemetry stream B reports $0 change. Please verify the authoritative measurement pipeline."

#### C. Evaluation Criteria & Verification Metrics
- **Abstention Precision & Recall:** 100% on synthetic contradiction and noise datasets.
- **GoRules Governance Adherence:** 0 automated levers issued when $C_{composite} < 0.70$.
- **Clarification Payload Completeness:** 100% of abstentions must provide non-null `reason` and structured `alternatives`.

---

### 3.3 Scenario 3: Sparse-History & Newly Launched KPI Scenario (Cold Start)

#### A. Problem Formulation
When a new product line, regional territory, or experimental feature is launched, historical time series data is severely limited ($N < 14$ daily observations). Standard time-series STL decomposition, seasonal moving averages, and 3-sigma anomaly bands fail due to insufficient degrees of freedom.
*Example Benchmark Incident:*
- New SaaS product tier launched 4 days ago.
- Observed revenue on Day 4 is $1,200.
- No 30-day baseline or seasonal indices exist in `canonical_measurements`.

#### B. Architectural Design & Enhancements
1. **Minimum Sample Size Gating ($N_{min}$):**
   - Enforce an ingestion/orchestration guardrail:
     - If $N \ge 14$ days $\rightarrow$ Normal Mode (STL decomposition + statistical scoring).
     - If $N < 14$ days $\rightarrow$ Sparse / Cold-Start Mode.
2. **Hierarchical Bayesian Priors:**
   - In Cold-Start Mode, initialize baseline distributions using empirical Bayesian priors borrowed from parent categories or historical cohort analogs:
     $$\theta_{new} \sim \text{Prior}(\mu_{parent}, \sigma_{parent}^2)$$
   - Conversion rates initialized with Beta priors $\text{Beta}(\alpha_0, \beta_0)$ parameterized from overall category conversion rates.
3. **Surrogate & Leading Proxy Indicators:**
   - Map sparse target KPIs to dense upstream proxy signals in `DEPENDENCY_GRAPH`:
     - Target KPI: `new_tier_monthly_revenue` (sparse).
     - Surrogates: `landing_page_visits`, `pricing_modal_clicks`, `checkout_initiation_rate` (dense).
   - Compute expected values dynamically based on surrogate funnel velocity.
4. **Epistemic Uncertainty Representation:**
   - Generate wide 95% Bayesian Credible Intervals ($[\hat{y}_{lower}, \hat{y}_{upper}]$) rather than narrow deterministic bounds to prevent false-alarm anomaly triggers.
   - Tag `DiagnosticPayload.metadata["cold_start"] = True`.

#### C. Evaluation Criteria & Verification Metrics
- **False-Positive Anomaly Suppression:** Zero false anomaly alerts triggered during initial $N \in [1, 7]$ days of synthetic noise.
- **Prior Shrinkage Metric:** Posterior distributions smoothly converge to empirical data as $N \to 14$.
- **Surrogate Correlation Fidelity:** Surrogate-predicted expected values must achieve $R^2 \ge 0.75$ against true simulated trajectories.

---

### 3.4 Scenario 4: Role-Based Security, Entitlement & Data Masking Scenario

#### A. Problem Formulation
In an enterprise multi-tenant BI platform, users possess different organizational roles, geographic jurisdictions, and data sensitivity clearances. Unauthorized users must never access raw PII, restricted financial metrics (e.g. Gross Margin, Executive Bonus Levers), or cross-tenant data.
*Example Benchmark Incident:*
- **Tenant A vs Tenant B:** Strict isolation; tenant A must never view tenant B's telemetry.
- **Regional Sales Lead (EMEA):** Authorized to view EMEA revenue and conversion; prohibited from viewing APAC data or executive gross margin.
- **Executive Persona:** Authorized to view company-wide financial margins, root causes, and high-impact levers ($>\$25\text{k}$).

#### B. Architectural Design & Enhancements
1. **Security Context & Entitlement Model:**
   ```python
   # Proposed Architectural Schema (app/schemas/security.py)
   class SecurityContext(BaseModel):
       user_id: str
       tenant_id: str
       role: PersonaRole
       allowed_regions: list[str]  # e.g. ["EMEA"] or ["*"]
       allowed_metrics: list[str]  # e.g. ["revenue", "conversion_rate"]
       restricted_attributes: list[str]  # e.g. ["margin_percentage", "user_email"]
       max_approval_limit: float
   ```
2. **Multi-Tenant Isolation at Data Layer:**
   - Update SQL query builders in `app/tools/` to enforce mandatory tenant scoping:
     `WHERE tenant_id = :tenant_id AND observed_at BETWEEN :start AND :end`
   - Leverage PostgreSQL Row-Level Security (RLS) policies.
3. **Metric & Dimension Level ABAC Filtering:**
   - Intercept findings before synthesis: filter out `AgentFinding` records that reference dimensions or metrics outside `SecurityContext.allowed_regions` and `allowed_metrics`.
4. **Dynamic Data Masking & Redaction Layer:**
   - Implement redaction on `DiagnosticPayload` and `PersonaStoryPayload`:
     - PII masking: Mask IP addresses, email addresses, and customer IDs with salted cryptographic hashes (`CUST-***-849`).
     - Value redaction: Obscure restricted numerical fields (e.g. `margin: "[REDACTED - INSUFFICIENT PRIVILEGES]"`).
5. **Governance Entitlement Enforcement:**
   - Integrate GoRules decision table rules (Rules 13, 14, 15, 16) to verify that recommendation decision rights match user role authorization before presenting executable actions.

#### C. Evaluation Criteria & Verification Metrics
- **Cross-Tenant Leakage Rate:** 0.00% (absolute zero tolerance).
- **Metric Redaction Verification:** 100% of restricted fields redacted across unauthorized persona runs.
- **Governance Entitlement Enforcement:** 100% rejection/blocking of recommendations exceeding the user's role authorization limit.

---

## 4. Golden Datasets Architecture (Requirement R4)

### 4.1 Purpose & Role in Continuous Evaluation
Golden Datasets serve as the authoritative ground-truth benchmark for the BI Engine. They enable automated regression testing, CI/CD validation, and quantitative model evaluation whenever prompt templates, LLM models, analytical algorithms, or governance rules are modified.

### 4.2 Standardized Golden Dataset Schema Standard
Each Golden Dataset scenario is formalized as a versioned JSON/Parquet artifact adhering to the following Pydantic specification:

```python
# Specification for Golden Dataset Definition
class GoldenDriverBenchmark(BaseModel):
    driver_id: str
    name: str
    driver_type: str
    expected_absolute_contribution: float
    expected_percentage_contribution: float
    is_causal: bool
    ground_truth_rank: int

class GoldenDatasetSpec(BaseModel):
    benchmark_id: str
    version: str  # Semantic versioning, e.g. "v1.2.0"
    scenario_category: str  # "MULTI_FACTOR", "ABSTENTION", "COLD_START", "SECURITY"
    description: str
    
    # Input Conditions
    movement_event: KPIMovementEvent
    synthetic_telemetry_series: list[dict[str, Any]]
    security_context: SecurityContext | None = None
    
    # Ground Truth Expectations
    expected_drivers: list[GoldenDriverBenchmark]
    expected_uncertainty_status: str  # "LOW", "MODERATE", "HIGH"
    expected_abstain: bool
    expected_governance_outcomes: list[str]  # e.g. ["APPROVED", "VP_APPROVAL"]
    
    # Validation Tolerances
    attribution_mae_tolerance: float = 5.0  # max acceptable MAE in %
    min_driver_recall: float = 1.0
```

### 4.3 Generation, Versioning & Storage Pipeline

```
┌────────────────────────────────┐       ┌─────────────────────────────────┐
│ Synthetic Scenario Generator   │       │ Sanitized Historical Incidents  │
│ (Mathematical Ground Truth)    │       │ (De-identified Real Data)       │
└───────────────┬────────────────┘       └────────────────┬────────────────┘
                │                                         │
                └───────────────────┬─────────────────────┘
                                    ▼
                     ┌──────────────────────────────┐
                     │ Pydantic Validation & Lint   │
                     │ (GoldenDatasetSpec)          │
                     └──────────────┬───────────────┘
                                    ▼
                     ┌──────────────────────────────┐
                     │ Storage & Version Control    │
                     │ S3 / MinIO / Git LFS / DVC   │
                     │ /golden_datasets/v1.0.0/     │
                     └──────────────┬───────────────┘
                                    ▼
                     ┌──────────────────────────────┐
                     │ CI/CD Benchmarking Suite     │
                     │ (Pytest Regression Harness)  │
                     └──────────────────────────────┘
```

1. **Generation Modes:**
   - **Synthetic Blueprint Generator:** Parametric scripts creating mathematical multi-factor movements, noise injections, seasonal disruptions, and cold-start series.
   - **Sanitized Real-World Incident Importer:** Real enterprise KPI anomalies stripped of PII and normalized into canonical format.
2. **Versioning & Immutability:**
   - Managed via Semantic Versioning (`v1.0.0`, `v1.1.0`) stored in `/golden_datasets/` or an S3/MinIO bucket.
   - Any modification to an existing dataset requires bumping the minor/patch version; historical versions remain immutable.
3. **Automated CI/CD Benchmarking Matrix:**
   - Automated test runner executes the entire engine across all golden datasets on every Git Pull Request.
   - Generates an evaluation scorecard:

| Benchmark Scenario | Driver Recall | Attribution MAE | Abstention Accuracy | Governance Pass Rate | Status |
|---|---|---|---|---|---|
| `GD-001: MultiFactor-EMEA-Outage` | 100% | 2.1% | N/A (Resolved) | 100% | PASS |
| `GD-002: Contradictory-Signals` | N/A | N/A | 100% (Abstained) | 100% | PASS |
| `GD-003: ColdStart-SaaS-Launch` | 100% | 4.2% | 100% (Wide Bounds) | 100% | PASS |
| `GD-004: RBAC-Sales-Restricted` | 100% | 1.8% | N/A (Masked) | 100% (Zero Leakage) | PASS |

---

## 5. Runtime Telemetry Architecture (Requirement R4)

### 5.1 Telemetry Objectives & Metrics Specification
The runtime telemetry system provides full-lifecycle observability into engine performance, computational cost, token efficiency, and execution reliability.

#### Core Telemetry Metrics:
1. **Latency Breakdown:**
   - $T_{total}$: Total end-to-end request latency (FastAPI request to response).
   - $T_{agents}$: Wall-clock parallel agent execution time vs individual agent times ($T_{prod}, T_{cust}, T_{geo}, T_{chan}$).
   - $T_{analytics}$: Matrix decomposition, dependency graph traversal, and contradiction detection latency.
   - $T_{llm\_orch}$: Orchestrator synthesis LLM invocation latency.
   - $T_{governance}$: GoRules decision table evaluation latency.
   - $T_{persona}$: Persona storytelling LLM generation latency.
2. **Model Call Tracking & Token Accounting:**
   - Model Identifier (`gpt-4o-mini`, `gpt-4o`, etc.).
   - Prompt (Input) Tokens ($N_{in}$).
   - Completion (Output) Tokens ($N_{out}$).
   - Total Tokens ($N_{total} = N_{in} + N_{out}$).
   - Cached Tokens ($N_{cached}$).
3. **Financial Cost Estimation:**
   - Computed in real time using official model pricing matrices:
     $$\text{Estimated Cost} = \sum_{m \in \text{Calls}} \left( N_{in, m} \times P_{in, m} + N_{out, m} \times P_{out, m} \right)$$
     *(e.g. for `gpt-4o-mini`: \$0.15 / 1M input tokens, \$0.60 / 1M output tokens).*

---

### 5.2 Exact Hook Placement Map Across the Backend Pipeline

The following diagram and table detail the **7 exact hook placement points** throughout the orchestrator and data pipeline:

```
[ FastAPI HTTP Request ]
       │  [HOOK 1: Request & Context Middleware]
       ▼
[ Investigation Service: run_investigation() ]
       │
       ├─► [ Agent Swarm Fan-Out (Parallel) ]
       │        ├─► product_agent    ──┐
       │        ├─► customer_agent   ──┼─► [HOOK 2: Database Query Telemetry]
       │        ├─► geography_agent  ──┤   [HOOK 3: Agent Execution & LLM Hook]
       │        └─► channel_agent    ──┘
       │
       ├─► [ Analytical Layer (analysis_node + contradictions) ]
       │        └─► [HOOK 4: Analytical Computation Hook]
       │
       ├─► [ Orchestrator LLM Synthesis (orchestrator_node) ]
       │        └─► [HOOK 5: Orchestrator LLM Callback Hook]
       │
       ├─► [ Governance Engine (governance_node) ]
       │        └─► [HOOK 6: Governance Engine Hook]
       │
       ▼
[ Persona Story Service: generate_persona_story() ]
       │
       └─► [HOOK 7: Persona Story LLM Callback Hook]
       │
       ▼
[ FastAPI HTTP Response with Telemetry Headers / Payload ]
```

#### Detailed Hook Placement Specification Table:

| Hook ID | File & Function Target | Instrumentation Technique | Exact Captured Telemetry | Downstream Destination |
|---|---|---|---|---|
| **Hook 1** | `app/main.py`<br>`@api.middleware("http")` | FastAPI ASGI Middleware / Starlette BaseHTTPMiddleware | Correlation ID (`X-Correlation-ID`), Request/Response timestamp, total HTTP latency ($T_{total}$), HTTP status code, client IP. | OpenTelemetry Span / Prometheus / Telemetry Context |
| **Hook 2** | `app/tools/database.py`<br>`execute_query()` / SQLAlchemy Event Listener | SQLAlchemy `before_cursor_execute` & `after_cursor_execute` events | SQL query text hash, execution duration ($T_{db}$), row count returned, connection pool wait time, tenant filter validation status. | Trace Span Attributes / Slow Query Log |
| **Hook 3** | `app/orchestrator/nodes.py`<br>`product_node`, `customer_node`, `geography_node`, `channel_node` | Python decorator `@trace_agent_span` / LangGraph node wrapper | Agent name, start/end timestamps, wall-clock latency ($T_{agent}$), error status, tool invocations count, agent-level LLM tokens (if invoked). | LangSmith Run / Telemetry Collector |
| **Hook 4** | `app/orchestrator/nodes.py`<br>`analysis_node`, `contradiction_node` | High-precision timer (`time.perf_counter()`) block wrapper | Mathematical computation latency ($T_{analytics}$), graph traversal time in NetworkX, number of contradictions detected, matrix size. | Span Events / Analytics Metrics |
| **Hook 5** | `app/orchestrator/llm.py` & `app/orchestrator/nodes.py`<br>`orchestrator_node` | LangChain Callback Handler (`TelemetryCallbackHandler`) attached to `orchestrator_llm` | Prompt tokens, completion tokens, model name, temperature, LLM latency ($T_{llm\_orch}$), cost calculation (\$USD), fallback invocation flag. | LangSmith / Prometheus Counter / Diagnostic Metadata |
| **Hook 6** | `app/governance/engine.py`<br>`evaluate_recommendation()` | Execution timer & result interceptor around `decision.evaluate()` | ZenEngine evaluation time ($T_{gov}$), matched Rule ID (e.g. `rule_21`), policy decision outcome (`APPROVED`, `HUMAN_REVIEW`, `ABSTAIN`). | Audit Log / Governance Metric Stream |
| **Hook 7** | `app/orchestrator/persona.py`<br>`generate_persona_story()` | LangChain Callback Handler attached to Persona `ChatOpenAI` | Persona role (`analyst`, `finance`, `executive`), user prompt token length, story completion tokens, LLM latency ($T_{persona}$), cost (\$USD). | Telemetry Summary Payload / LangSmith |

---

### 5.3 Telemetry Data Structure & Frontend Contract
Telemetry gathered across all 7 hooks is compiled into a standardized `RuntimeTelemetry` object attached to the API response metadata:

```python
# Specification for Runtime Telemetry Payload
class LLMCallTelemetry(BaseModel):
    stage: str  # "orchestrator" | "persona" | "agent_product"
    model: str  # "gpt-4o-mini"
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    cost_usd: float

class RuntimeTelemetry(BaseModel):
    trace_id: str
    incident_id: str
    total_latency_ms: float
    stage_latencies_ms: dict[str, float]  # {"agents_fanout": 120, "analytics": 15, "orchestrator_llm": 350, "governance": 4, "persona_llm": 310}
    model_calls_count: int
    total_tokens: int
    total_estimated_cost_usd: float
    llm_calls: list[LLMCallTelemetry]
    governance_rules_evaluated: int
```

This directly feeds the `frontend/Dashboard/src/App.jsx` sidebar telemetry preview:
- `Latency:` `450ms`
- `Model Calls:` `12`
- `Token Usage:` `4.2k`
- `Est. Cost:` `$0.012`

---

## 6. Gap Analysis & Architecture Comparison

| Area | Current Codebase State | Target Architecture Requirement | Gap Severity | Resolution Plan |
|---|---|---|---|---|
| **Multi-Factor Attribution** | 1D single-dimension percentage formula in `calculate_contribution()`. | Shapley value / LMDI multi-factor additive decomposition handling joint interactions. | High | Implement Shapley decomposition and multi-factor synthetic test suite in R3. |
| **Abstention Protocol** | Basic contradiction check causing binary string fallback. | Standardized $C_{composite}$ scoring engine with structured clarification generation and GoRules blocking. | High | Formalize confidence equation and clarification schema in R3. |
| **Cold Start / Sparse KPI** | Fails or returns empty rows if history $< 14$ days. | $N_{min} = 14$ gating, Hierarchical Bayesian priors, surrogate indicator funnel mapping. | High | Architect Bayesian prior borrowing and surrogate graph edges in R3. |
| **Security & Entitlements** | Unscoped SQL queries; no tenant, metric, or column masking. | `SecurityContext` model, multi-tenant SQL scoping, ABAC metric filtering, PII redaction layer. | Critical | Implement security context filtering across tools and persona storytelling in R3. |
| **Golden Datasets** | 0 golden dataset files or benchmark runners. | Versioned `GoldenDatasetSpec` suite covering all 4 scenario categories with automated CI/CD scoring. | High | Construct golden dataset generator and automated evaluation runner in R4. |
| **Runtime Telemetry** | Uninstrumented backend; frontend hardcodes mock telemetry. | OpenTelemetry + LangChain callback handler instrumented at 7 specific pipeline hooks. | Medium | Integrate telemetry middleware, callback handlers, and cost computation in R4. |

---

## 7. Recommended Implementation Milestones for Subsequent Work

1. **Milestone R3-A: Scenario 1 & 2 Testing Framework**
   - Implement `MultiFactorScenarioGenerator` and Shapley attribution module.
   - Implement $C_{composite}$ confidence scoring engine, contradiction penalty, and structured clarification response generator.
2. **Milestone R3-B: Scenario 3 & 4 Testing Framework**
   - Implement Sparse KPI / Cold-Start Bayesian prior engine and surrogate indicator resolver.
   - Implement `SecurityContext`, tenant isolation in `app/tools/`, ABAC metric filtering, and PII masking layer.
3. **Milestone R4-A: Golden Dataset Repository & CI/CD Benchmark Runner**
   - Generate initial suite of 20 versioned golden dataset JSON files across the 4 scenario types.
   - Implement Pytest evaluation runner verifying driver recall, attribution MAE, abstention accuracy, and zero-leakage security.
4. **Milestone R4-B: Runtime Telemetry Engine & Exact Hook Integration**
   - Implement `TelemetryCallbackHandler` and FastAPI context middleware.
   - Wire all 7 hooks across `main.py`, `database.py`, `nodes.py`, `llm.py`, `governance/engine.py`, and `persona.py`.
   - Expose live telemetry payload to frontend visualizers and dashboard.
