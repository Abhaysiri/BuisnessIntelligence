# Handoff Report: KPI Scenarios, Telemetry & Golden Datasets (Requirements R3 & R4)

**Agent:** Explorer 3 (`explorer_survey_3`)  
**Parent:** `orchestrator_1` (Conv ID: `e16fd076-8d94-4a97-a7c1-2a4c07e7f050`)  
**Mission:** Codebase survey and architectural research for R3 (KPI Scenario Testing Strategy) and R4 (Golden Datasets & Runtime Telemetry)  
**Deliverable Path:** `c:\Users\Abhay\Desktop\CODING\BuisnessIntelligence.ai\.agents\explorer_survey_3\survey_report.md`

---

## 1. Observation

Direct observations from examining the codebase:

1. **Testing Infrastructure:**
   - `kpi-engine/tests/`: Directory is completely empty (0 files).
   - `kpi-engine/run_test.py` (lines 14-87): Executes a single hardcoded synthetic event (`INC-2026-001`, monthly revenue drop of 30%) through `run_investigation(event)` and generates sample Engineering and Executive persona stories.
   - `test_visualizers_api.py` (lines 8-106): Sends a mock `DiagnosticPayload` to `http://localhost:8001/visualizations` to verify Vega-Lite specification generation.

2. **Analytical Layer & Attribution:**
   - `app/analytics/contribution.py` (lines 5-24): Implements a single 1D dimension slice calculation (`calculate_contribution`) dividing finding delta by total KPI delta (`dim_delta / movement.absolute_change`). Lacks multi-factor interaction terms, Shapley values, or joint covariance modeling.
   - `app/analytics/dependency.py` (lines 5-54): Defines a static 17-node `NetworkX` graph with basic relationship semantics (`influences`, `mathematical`, `transforms`, `decomposes`).
   - `app/analytics/contradictions.py` (lines 4-46): Only flags contradictions when two findings have identical dimension slices with different observed values or opposite directional signs.

3. **Governance & Decision Rules:**
   - `app/governance/decision_table.json`: Contains 30 GoRules decision table rules including Rule 20 (`confidence >= 0.85 -> ALLOWED`), Rule 21 (`confidence [0.70..0.84] -> HUMAN_REVIEW`), Rule 22 (`confidence < 0.70 -> ABSTAIN`), Rule 23 (`dataQualityStatus != 'VALID' -> PROHIBITED`), and role authorization rules (Rules 13-16).
   - `app/orchestrator/nodes.py` (lines 148-171): `governance_node` invokes `evaluate_recommendation()` and attaches `decision_right` to recommendations.

4. **Persona & Entitlement State:**
   - `app/schemas/persona.py` (lines 7-13): Defines `PersonaRole` enum (`ANALYST`, `FINANCE`, `EXECUTIVE`, `SALES`, `ENGINEERING`).
   - `app/orchestrator/persona.py` (lines 8-31): Enforces strict negative constraints in prompt ("Never invent evidence", "Never change numerical values"), but lacks data masking, role-based metric filtering, or tenant isolation.
   - `app/tools/product.py`, `customer.py`, `geography.py`, `channel.py`: SQL queries filter on `observed_at` and `kpi_id`, but omit `tenant_id`, user context, or Row-Level Security (RLS) enforcement.

5. **Frontend Telemetry Expectations:**
   - `frontend/Dashboard/src/App.jsx` (lines 89-95): Hardcodes UI telemetry preview elements: `Latency: 450ms`, `Model Calls: 12`, `Token Usage: 4.2k`, `Est. Cost: $0.012`.
   - `kpi-engine/requirements.txt`: Lacks explicit telemetry packages (e.g. `opentelemetry-api`, `prometheus-client`), though `langsmith` is referenced in `public-architecture-dia/Complete technology architecture.md`.

---

## 2. Logic Chain

1. **Premise (from Observation 1):** The absence of test files in `kpi-engine/tests/` means the engine cannot verify behavioral regression, edge case handling, or governance enforcement automatically.
   - *Inference:* An automated scenario testing runner and a versioned Golden Dataset evaluation harness are critical prerequisites before production deployment.

2. **Premise (from Observation 2):** Real-world KPI drops involve concurrent multiple root causes acting in combination.
   - *Inference:* The 1D attribution in `contribution.py` is insufficient for Scenario 1 (Multi-factor movement). It must be upgraded to multi-factor Shapley value or Logarithmic Mean Divisia Index (LMDI) decomposition, validated against synthetic ground-truth driver datasets.

3. **Premise (from Observations 2 & 3):** When data is conflicting or weak, GoRules specifies `ABSTAIN` (Rule 22), but `orchestrator_node` currently only falls back to a basic string reason.
   - *Inference:* For Scenario 2 (Low confidence), a composite confidence scoring function ($C_{composite}$) combining evidence, temporal precedence, and DAG validity must be formalized to trigger structured clarification requests and GoRules abstention blocking.

4. **Premise (from Observations 1 & 2):** In sparse-history or cold-start scenarios ($N < 14$), moving averages and standard queries return empty sets or fail.
   - *Inference:* For Scenario 3 (Cold start), a minimum data threshold ($N_{min} = 14$) gating protocol, hierarchical Bayesian prior borrowing, and surrogate proxy indicator mappings must be architected.

5. **Premise (from Observation 4):** Database queries and persona story generation currently execute without multi-tenant scoping or column-level permissions.
   - *Inference:* For Scenario 4 (Security & Entitlements), a `SecurityContext` model, multi-tenant SQL scoping (`tenant_id`), ABAC metric filtering, dynamic PII/margin data masking, and GoRules role authorization must be enforced.

6. **Premise (from Observation 5):** The frontend expects four specific runtime telemetry metrics (`Latency`, `Model Calls`, `Token Usage`, `Est. Cost`), but no hooks currently capture these in the backend.
   - *Inference:* Seven exact hook points (FastAPI middleware, DB queries, agent fan-out, analytical computation, orchestrator LLM, GoRules governance, and persona storytelling LLM) must be instrumented using OpenTelemetry and LangChain callback handlers.

---

## 3. Caveats

1. **Read-Only Investigation Scope:** In accordance with the system constraints, this survey is purely research, architectural planning, and gap analysis; no production application code or test implementation code has been written to the repository.
2. **Database Connectivity:** Live PostgreSQL / Supabase connection was not executed during this survey (mock environment mode in `run_test.py`); database latency benchmarks were estimated based on typical pooling performance.
3. **LLM Cost Pricing:** Cost estimates assume standard OpenAI API pricing for `gpt-4o-mini` (\$0.15/1M input tokens, \$0.60/1M output tokens); alternative models (e.g. `gpt-4o`, Anthropic Claude, self-hosted LLMs) will require dynamic pricing lookup tables.

---

## 4. Conclusion

1. **Scenario Testing Strategy (R3):** The four target scenarios are fully mapped with concrete mathematical algorithms, Pydantic schemas, and simulation blueprints:
   - *Scenario 1 (Multi-factor):* Shapley decomposition + partial correlation in DAG.
   - *Scenario 2 (Low confidence):* Multi-layer composite confidence index ($C_{composite}$) + structured clarification & abstention protocol.
   - *Scenario 3 (Cold start):* Minimum-sample gating ($N_{min}=14$) + Hierarchical Bayesian priors + surrogate indicator funnel mapping.
   - *Scenario 4 (Entitlements):* `SecurityContext` + multi-tenant SQL scoping + ABAC metric filtering + dynamic PII/margin data masking.
2. **Golden Datasets & Benchmarking (R4):** Designed `GoldenDatasetSpec` schema, semantic versioning pipeline (`v1.0.0`), and automated CI/CD evaluation matrix measuring driver recall, attribution MAE, abstention precision, and zero security leakage.
3. **Runtime Telemetry & Exact Hooks (R4):** Designed full OpenTelemetry and LangChain callback architecture mapping exactly 7 hook placement points across `main.py`, `database.py`, `nodes.py`, `llm.py`, `governance/engine.py`, and `persona.py`, directly satisfying the frontend dashboard telemetry contract.

---

## 5. Verification Method

To independently verify these survey findings and architecture:

1. **Verify Existing Codebase State:**
   - Inspect empty tests folder: `fd -p "kpi-engine/tests"` (returns 0 results).
   - Inspect attribution logic: `view_file` at `kpi-engine/app/analytics/contribution.py:5-24`.
   - Inspect governance table: `view_file` at `kpi-engine/app/governance/decision_table.json:555-635` (Rules 20-23).
   - Inspect persona constraints: `view_file` at `kpi-engine/app/orchestrator/persona.py:8-31`.
   - Inspect frontend telemetry contract: `view_file` at `frontend/Dashboard/src/App.jsx:89-95`.

2. **Verify Specialist Report:**
   - Read full deliverable report: `view_file` at `c:\Users\Abhay\Desktop\CODING\BuisnessIntelligence.ai\.agents\explorer_survey_3\survey_report.md`.
