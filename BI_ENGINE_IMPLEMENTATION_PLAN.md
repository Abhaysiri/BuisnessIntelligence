# Business Intelligence Engine: Comprehensive Research & Implementation Plan

**Document Version:** 1.0.0-PROD-PLAN  
**Status:** Authoritative Architectural Specification & Implementation Roadmap  
**Target Systems:** Data Ingestion Pipeline, Time-Series Statistical Engine, LangGraph Orchestration Swarm, Causal Analytics, GoRules Governance, Telemetry Observability, and Frontend Visualizers  
**Constraint Verification:** Contains no executable application source code. All algorithms, schemas, and hook points are fully specified as rigorous technical architecture.

---

## Table of Contents
1. [Executive Summary & System Architecture Blueprint](#1-executive-summary--system-architecture-blueprint)
2. [Requirement R1: Data Ingestion & Validity Layer Architecture](#2-requirement-r1-data-ingestion--validity-layer-architecture)
   - [2.1 End-to-End Medallion Ingestion Pipeline](#21-end-to-end-medallion-ingestion-pipeline)
   - [2.2 6-Tier Data Validity Gate Specification](#22-6-tier-data-validity-gate-specification)
   - [2.3 Dead-Letter Quarantine & Replay Architecture](#23-dead-letter-quarantine--replay-architecture)
   - [2.4 Composite Data Quality ($DQ$) Scoring & Governance Coupling](#24-composite-data-quality-dq-scoring--governance-coupling)
   - [2.5 Time-Series Regularization & Imputation Hierarchy](#25-time-series-regularization--imputation-hierarchy)
   - [2.6 Objective Verification Steps with Mock Data & Fault Injection](#26-objective-verification-steps-with-mock-data--fault-injection)
3. [Requirement R2: Orchestrator Completion — STL Decomposition Engine](#3-requirement-r2-orchestrator-completion--stl-decomposition-engine)
   - [3.1 Upstream Orchestrator Integration Architecture](#31-upstream-orchestrator-integration-architecture)
   - [3.2 Mathematical Foundations of LOESS & STL Decomposition](#32-mathematical-foundations-of-loess--stl-decomposition)
   - [3.3 Cleveland et al. (1990) Two-Loop Iterative Algorithm](#33-cleveland-et-al-1990-two-loop-iterative-algorithm)
   - [3.4 Cadence-Specific Parameter Tuning Framework](#34-cadence-specific-parameter-tuning-framework)
   - [3.5 Dynamic Expected Baseline, Uncertainty & Anomaly Scoring](#35-dynamic-expected-baseline-uncertainty--anomaly-scoring)
   - [3.6 Interface Contracts & Schemas](#36-interface-contracts--schemas)
   - [3.7 Explicit Exclusion of Contextual Debouncing & Edge-Case Protocols](#37-explicit-exclusion-of-contextual-debouncing--edge-case-protocols)
   - [3.8 Objective Synthetic Verification Assertions](#38-objective-synthetic-verification-assertions)
4. [Requirement R3: KPI Scenario Testing Strategy Plan](#4-requirement-r3-kpi-scenario-testing-strategy-plan)
   - [4.1 Scenario 1: Multi-Factor KPI Movement with Known/Simulated Drivers](#41-scenario-1-multi-factor-kpi-movement-with-knownsimulated-drivers)
   - [4.2 Scenario 2: Low-Confidence Scenario with Clarification & Abstention](#42-scenario-2-low-confidence-scenario-with-clarification--abstention)
   - [4.3 Scenario 3: Sparse-History / Cold-Start KPI Scenario](#43-scenario-3-sparse-history--cold-start-kpi-scenario)
   - [4.4 Scenario 4: Role-Based Security & Entitlements Scenario](#44-scenario-4-role-based-security--entitlements-scenario)
5. [Requirement R4: Golden Datasets & Runtime Telemetry Integration](#5-requirement-r4-golden-datasets--runtime-telemetry-integration)
   - [5.1 Golden Datasets Generation & 4-Tier Catalog](#51-golden-datasets-generation--4-tier-catalog)
   - [5.2 Automated CI/CD Regression Evaluation Benchmark Suite](#52-automated-cicd-regression-evaluation-benchmark-suite)
   - [5.3 Runtime Telemetry Observability Framework & Cost Engine](#53-runtime-telemetry-observability-framework--cost-engine)
   - [5.4 All 7 Exact Runtime Telemetry Hook Placements](#54-all-7-exact-runtime-telemetry-hook-placements)
6. [Target Code Layout & Implementation Roadmap](#6-target-code-layout--implementation-roadmap)

---

## 1. Executive Summary & System Architecture Blueprint

### 1.1 Mission & Architectural Gap
The Business Intelligence (BI) Engine is an enterprise-grade agentic diagnostic platform that autonomously detects anomalous movements in corporate key performance indicators (KPIs), investigates underlying multidimensional root causes across distributed business entities (Product, Customer, Geography, Channel), enforces automated governance policies, and presents role-tailored narratives with interactive Vega-Lite visualizers.

Prior codebase exploration revealed critical structural gaps:
1. **Ingestion & Data Quality Void (R1)**: Metric data was queried directly from raw tables with zero validation gates, schema contracts, dimensional reconciliation, or dead-letter quarantine, directly conflicting with GoRules Rule 23 (`dataQualityStatus != 'VALID' -> PROHIBITED`).
2. **Missing Time-Series Baseline Engine (R2)**: The orchestrator operated strictly downstream of an assumed pre-existing `KPIMovementEvent`, lacking statistical time-series decomposition (STL/LOESS) to autonomously establish dynamic baselines ($\hat{Y}_t$), isolate seasonal cycles ($S_t$), calculate residual variance ($\sigma_R$), and trigger statistically grounded investigations.
3. **Scenario Gaps in Multi-Factor & Security Layers (R3)**: Root-cause attribution was limited to simple 1D slicing (`app/analytics/contribution.py`), unable to decouple concurrent interacting drivers, while database queries and persona narratives lacked multi-tenant isolation and role-based data masking.
4. **Observability & Benchmark Deficit (R4)**: The test suite was completely empty (`kpi-engine/tests`), and runtime telemetry was hardcoded on the frontend without backend instrumentation for latency, model calls, token usage, and cost tracking.

### 1.2 Unified System Architecture Blueprint

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       1. DATA INGESTION & VALIDITY LAYER                                │
│   [Bronze Object Store] ──► [Silver Polars Normalize] ──► [6-Tier Validity Gate] ──► [Gold PostgreSQL]  │
│   (S3 / MinIO WORM)          (Vectorized Cleanse)          (Pydantic/Pandera/Drift)   (Partitioned DB) │
│                                                                   │ (Corrupted)                        │
│                                                                   ▼                                    │
│                                                       [Quarantine Dead-Letter]                         │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │
                                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              2. ORCHESTRATOR & TIME-SERIES ENGINE (STL)                                │
│   [kpi_extractor_node] ──► [stl_evaluator_node (Cleveland LOESS)] ──► [Dynamic Baseline & Bounds]       │
│   (Regularized Grid)       (Inner/Outer Iteration Decomposition)      (Anomalous |Z| >= 2.5 Trigger)   │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │ (KPIMovementEvent)
                                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 3. LANGGRAPH MULTI-AGENT DIAGNOSTIC SWARM                              │
│   Parallel Swarm Execution:                                                                            │
│   ├── [Product Agent]     ├── [Customer Agent]                                                         │
│   ├── [Geography Agent]   └── [Channel Agent]                                                          │
│   └── (All scoped by SecurityContext ABAC & Multi-Tenant Parameterized SQL)                            │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │
                                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                4. CAUSAL ANALYTICS & GOVERNANCE PIPELINE                               │
│   ├── [Shapley / LMDI Attribution] ──► Decouples concurrent multi-factor drivers                       │
│   ├── [NetworkX Causal DAG]        ──► Validates dependency paths & partial correlations               │
│   ├── [Composite Confidence Engine]──► Evaluates C_composite (Gating Rule 20/21/22)                    │
│   └── [GoRules ZenEngine]          ──► Evaluates 30 Decision Table Governance Rules                    │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │
                                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 5. PRESENTATION & OBSERVABILITY LAYER                                  │
│   ├── [Persona Synthesis Node]     ──► Generates stories (Executive, Finance, Engineering, Sales)      │
│   ├── [Dynamic Data Masking]       ──► Redacts PII & Financial Margins per role                        │
│   ├── [Vega-Lite Visualizer API]   ──► Renders Trend Errorbands, Breakdowns, & Timelines               │
│   └── [OpenTelemetry & Hooks]      ──► Captures Latency, Model Calls, Tokens, & Cost across 7 Hooks    │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Requirement R1: Data Ingestion & Validity Layer Architecture

### 2.1 End-to-End Medallion Ingestion Pipeline
To ensure high-throughput, low-latency, and strictly validated metric ingestion, the ingestion engine adopts a Medallion Architecture across Bronze, Silver, and Gold storage tiers:

1. **Bronze Layer (Raw Immutable Ingestion)**:
   - **Ingestion Entrypoints**: FastAPI micro-batch endpoint (`POST /api/v1/metrics/ingest`) and async object storage batch uploads.
   - **Storage**: Amazon S3 / MinIO Write-Once-Read-Many (WORM) storage partitioned by `tenant_id/metric_id/YYYY/MM/DD/hh_raw_payload.json.zst`.
   - **Characteristics**: Preserves unmodified source payloads with complete metadata (ingest timestamp, source IP, client certificate fingerprint).

2. **Silver Layer (Normalized In-Memory Cleansing)**:
   - **Engine**: Polars vectorized execution engine.
   - **Processing**: Type casting, ISO-8601 UTC timestamp regularization, dimension hash standardization (`dim_hash = SHA256(dim_key + dim_value)`), and schema conformity.

3. **Gold Layer (Canonical High-Performance Storage)**:
   - **Storage**: PostgreSQL `canonical_measurements` partitioned table.
   - **Indexes**: Composite B-Tree index on `(tenant_id, kpi_id, observed_at DESC)` and GIN index on `dimensions` JSONB column.

```sql
-- Gold Canonical Storage DDL
CREATE TABLE canonical_measurements (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(64) NOT NULL,
    kpi_id VARCHAR(64) NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    value NUMERIC(18, 6) NOT NULL,
    dimensions JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_imputed BOOLEAN NOT NULL DEFAULT FALSE,
    dq_score NUMERIC(5, 4) NOT NULL DEFAULT 1.0000,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (tenant_id, kpi_id, observed_at, id)
) PARTITION BY RANGE (observed_at);
```

### 2.2 6-Tier Data Validity Gate Specification

Every incoming metric batch must pass sequentially through six independent validation tiers before admission to the Gold layer:

```
[Raw Ingest] ──► [Tier 1: Pydantic V2] ──► [Tier 2: Pandera Schema] ──► [Tier 3: Temporal Grid]
                         │ (Fail)                   │ (Fail)                   │ (Fail)
                         ▼                          ▼                          ▼
                 [Quarantine]               [Quarantine]               [Quarantine]
                         ▲                          ▲                          ▲
                         │ (Fail)                   │ (Fail)                   │ (Fail)
[Admit to Gold] ◄── [Tier 6: Drift] ◄── [Tier 5: Reconciliation] ◄── [Tier 4: Boundary/Stats]
```

1. **Tier 1: Structural & Type Validation (Pydantic V2)**
   - Schema enforcement: Validates UUIDs, non-empty metric names, ISO-8601 temporal parsing, and dimension key sanitization.
   - Nullability constraints: Rejects null `tenant_id`, `kpi_id`, `observed_at`, or `value`.

2. **Tier 2: Columnar & Statistical Range Validation (Pandera)**
   - High-throughput vectorized dataframe validation.
   - Verifies categorical dimension values match registered taxonomies (e.g. `channel IN ['Enterprise', 'Self-Serve', 'Partner', 'Direct']`).

3. **Tier 3: Temporal Continuity & Cadence Grid Validation**
   - Future-timestamp rejection: $t_{\text{observed}} \le t_{\text{ingest}} + \Delta_{\text{clock\_skew}}$ (where $\Delta_{\text{clock\_skew}} = 5 \text{ seconds}$).
   - Monotonicity checks: Ingested batches must be strictly ordered or automatically sort-reordered.
   - Cadence alignment: Timestamps are floored to registered cadence boundaries (e.g. `00:00:00Z` for Daily, `hh:00:00Z` for Hourly).

4. **Tier 4: Physical Domain & Statistical Boundary Constraints**
   - Hard physical boundaries: Non-negative checks for count/currency metrics ($\text{Revenue} \ge 0$, $\text{Latency} \ge 0$), bounded ratios ($\text{ConversionRate} \in [0.0, 1.0]$).
   - Dynamic 6-Sigma outlier screening: Flag values where $|Y_t - \mu_{30d}| > 6 \cdot \sigma_{30d}$ for secondary review.

5. **Tier 5: Additive Dimensional Reconciliation Engine**
   - Enforces mathematical consistency across multi-dimensional slices:
     $$\left| \sum_{i=1}^{K} \text{SliceValue}_i - \text{TotalMetricValue} \right| \le \max(0.01, 0.001 \times \text{TotalMetricValue})$$
   - If sum-to-total discrepancies exceed $0.1\%$, the reconciliation tier flags a dimensional mismatch violation.

6. **Tier 6: Distributional Drift Detection (Evidently AI / KS-Test)**
   - Evaluates reference distribution $P_{\text{ref}}$ (rolling 30-day baseline) against current batch $P_{\text{curr}}$.
   - Uses two-sample Kolmogorov-Smirnov test ($\alpha = 0.01$) and Population Stability Index (PSI).
   - PSI $\ge 0.25$ indicates significant distributional drift, generating a telemetry alert.

### 2.3 Dead-Letter Quarantine & Replay Architecture
Any record failing any validation tier is immediately diverted from the processing pipeline into the quarantine store:

```sql
-- Quarantine Dead-Letter Store DDL
CREATE TABLE quarantine_measurements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(64) NOT NULL,
    kpi_id VARCHAR(64) NOT NULL,
    raw_payload JSONB NOT NULL,
    failed_tier VARCHAR(32) NOT NULL,
    error_code VARCHAR(64) NOT NULL,
    error_message TEXT NOT NULL,
    validation_trace JSONB NOT NULL,
    quarantined_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    replayed_by VARCHAR(64)
);
```

- **Administrative Replay API**: `POST /api/v1/quarantine/replay` allows operators to re-inject remediated records back into Tier 1 after upstream schema updates or upstream data source fixes.

### 2.4 Composite Data Quality ($DQ$) Scoring & Governance Coupling
To bridge data validity with agentic decision-making, each ingested metric batch receives a continuous Data Quality score $DQ \in [0.0, 1.0]$:

$$DQ = w_{\text{struct}} S_{\text{struct}} + w_{\text{range}} S_{\text{range}} + w_{\text{temp}} S_{\text{temp}} + w_{\text{reconcile}} S_{\text{reconcile}} + w_{\text{completeness}} S_{\text{completeness}}$$

Where weights are calibrated as:
- $w_{\text{struct}} = 0.25$ (Structural and type compliance)
- $w_{\text{range}} = 0.20$ (Range and boundary validity)
- $w_{\text{temp}} = 0.20$ (Temporal grid alignment and continuity)
- $w_{\text{reconcile}} = 0.20$ (Dimensional sum reconciliation)
- $w_{\text{completeness}} = 0.15$ (Absence of missing/imputed records)

#### Direct Coupling to GoRules Rule 23
The computed $DQ$ score maps directly to categorical `dataQualityStatus`:
- $DQ \ge 0.95 \implies \text{dataQualityStatus} = \text{"VALID"}$
- $0.80 \le DQ < 0.95 \implies \text{dataQualityStatus} = \text{"DEGRADED"}$
- $DQ < 0.80 \implies \text{dataQualityStatus} = \text{"INVALID"}$

In `app/governance/decision_table.json`, Rule 23 enforces:
```json
{
  "rule_id": 23,
  "condition": "dataQualityStatus != 'VALID'",
  "decision_right": "PROHIBITED",
  "action": "BLOCK_AUTOMATION",
  "reason": "Data quality score below certified threshold. Automated actions prohibited."
}
```

### 2.5 Time-Series Regularization & Imputation Hierarchy
To prevent downstream algorithmic crashes in STL decomposition:
1. **Regularization Grid**: Missing timestamps are filled with a complete `pandas.date_range` or Polars temporal grid.
2. **Missingness Imputation Strategy**:
   - Gap length $g \le 3$ intervals: Vectorized Akima cubic spline interpolation.
   - Gap length $3 < g \le n_{(p)}$ intervals: Seasonal persistence ($Y_t = Y_{t - n_{(p)}}$).
   - Gap length $g > 0.20 \times N$: Series rejected from automated STL analysis; triggers cold-start Bayesian prior mode.
3. **Audit Immutability**: All imputed records have `is_imputed = TRUE` permanently set in `canonical_measurements` to maintain complete audit transparency.

### 2.6 Objective Verification Steps with Mock Data & Fault Injection
To verify the ingestion and validity layer without running application code, the test harness defines a deterministic synthetic test suite executing 6 objective assertions:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                      INGESTION & VALIDITY VERIFICATION TEST SUITE                       │
├────────────────────────────────┬───────────────────────────┬────────────────────────────┤
│ Test Case Category             │ Injected Fault / Mutation │ Expected System Verdict    │
├────────────────────────────────┼───────────────────────────┼────────────────────────────┤
│ TC-1.1: Happy Path Normal      │ Perfect 30-day series     │ Gold DB Insert, DQ = 1.00  │
│ TC-1.2: Negative Revenue       │ Revenue = -$45,200.00     │ Tier 4 Quarantine Block    │
│ TC-1.3: Future Timestamp       │ Timestamp = Now + 3 Days  │ Tier 3 Quarantine Block    │
│ TC-1.4: Dimension Mismatch     │ Sum(Slices) != Total (5%) │ Tier 5 Quarantine Block    │
│ TC-1.5: High Missingness (35%) │ 35% NaN values injected   │ DQ = 0.65 -> Rule 23 Block │
│ TC-1.6: Distributional Drift   │ +400% variance shift      │ Tier 6 Alert -> Telemetry  │
└────────────────────────────────┴───────────────────────────┴────────────────────────────┘
```

---

## 3. Requirement R2: Orchestrator Completion — STL Decomposition Engine

### 3.1 Upstream Orchestrator Integration Architecture
The time-series statistical engine is positioned strictly **upstream** of the LangGraph diagnostic swarm. This architecture solves the foundational gap where investigations previously assumed an already diagnosed anomaly event:

```
[Periodic Trigger / API] ──► [kpi_extractor_node] ──► [stl_evaluator_node] ──► [Anomaly Decision]
                                                                                      │
                                                 ┌────────────────────────────────────┴────────────────────────────────────┐
                                                 │ No Significant Deviation (|Z| < 2.5)                                    │ Significant Anomaly (|Z| >= 2.5)
                                                 ▼                                                                         ▼
                                     [Persist Baseline to Gold]                                               [Emit KPIMovementEvent]
                                     [Telemetry Healthy Status]                                                            │
                                     [Execution Completes]                                                                 ▼
                                                                                                              [LangGraph Agent Swarm]
```

### 3.2 Mathematical Foundations of LOESS & STL Decomposition
STL (Seasonal and Trend decomposition using Loess, Cleveland et al., 1990) decomposes an observed continuous time series $Y_t$ into additive orthogonal components:

$$Y_t = T_t + S_t + R_t \quad \text{for } t = 1, 2, \dots, N$$

Where:
- $T_t$: **Trend component**, capturing low-frequency secular movements and multi-period drift.
- $S_t$: **Seasonal component**, capturing deterministic recurring periodic cycles of length $n_{(p)}$.
- $R_t$: **Remainder (residual) component**, capturing stationary stochastic noise and anomalous excursions.

#### LOESS (Locally Estimated Scatterplot Smoothing) Mathematics
LOESS estimates the smoothed value $\hat{y}$ at target point $x_0$ using locally weighted linear polynomial regression ($d=1$).
For each point $x_i$ in the neighborhood of $x_0$:

1. **Neighborhood Distance**: Let $q$ be the smoothing window parameter ($n_{(s)}, n_{(t)}$, or $n_{(l)}$). The distance to the $q$-th nearest neighbor is:
   $$\Delta(x_0) = |x_q - x_0|$$

2. **Tricube Weight Function**:
   $$u_i = \frac{|x_i - x_0|}{\Delta(x_0)}$$
   $$W(u_i) = \begin{cases} (1 - u_i^3)^3 & \text{for } 0 \le u_i < 1 \\ 0 & \text{for } u_i \ge 1 \end{cases}$$

3. **Weighted Least Squares Optimization**:
   Find $(\hat{\beta}_0, \hat{\beta}_1)$ minimizing:
   $$\sum_{i=1}^{N} \rho_i W\left(\frac{|x_i - x_0|}{\Delta(x_0)}\right) \left( y_i - \beta_0 - \beta_1(x_i - x_0) \right)^2$$
   Where $\rho_i$ is the outer-loop robustness weight ($\rho_i = 1.0$ in initial pass). The fitted value is $\hat{y}(x_0) = \hat{\beta}_0$.

### 3.3 Cleveland et al. (1990) Two-Loop Iterative Algorithm

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 OUTER LOOP (k = 1 to n_(o))                             │
│   Computes Robustness Weights ρ_t based on Remainder R_t                                │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                              INNER LOOP (m = 1 to n_(i))                       │   │
│   │   Step 1: Detrending ─────────────► Y_t - T_t^(k-1)                            │   │
│   │   Step 2: Subseries Smoothing ────► Loess on each seasonal phase (window n_(s))│   │
│   │   Step 3: Low-Pass Filter ────────► Moving Avg [n_(p), n_(p), 3] + Loess n_(l) │   │
│   │   Step 4: Subseries Subtraction ──► S_t^(k) = Subseries - LowPass              │   │
│   │   Step 5: Deseasonalizing ────────► Y_t - S_t^(k)                              │   │
│   │   Step 6: Trend Smoothing ────────► Loess on Deseasonalized (window n_(t))     │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                        │
│   Compute Remainder: R_t^(k) = Y_t - T_t^(k) - S_t^(k)                                 │
│   Compute Tukey Bisquare Weights: ρ_t = B(|R_t| / (6 * median(|R|)))                   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Step-by-Step Inner Loop Procedure:
1. **Detrending**: Compute detrended series $D_t^{(k)} = Y_t - T_t^{(k-1)}$ (with $T_t^{(0)} = 0$).
2. **Cycle-Subseries Smoothing**: Break $D_t^{(k)}$ into $n_{(p)}$ distinct subseries corresponding to each seasonal position (e.g. all Mondays, all Tuesdays). Smooth each subseries independently using LOESS ($d=1, q=n_{(s)}$). Collect into temporary series $C_t^{(k)}$.
3. **Low-Pass Filter of Smoothed Subseries**: Pass $C_t^{(k)}$ sequentially through:
   - Moving average of length $n_{(p)}$
   - Moving average of length $n_{(p)}$
   - Moving average of length $3$
   - LOESS smoothing with window $n_{(l)}$ and degree $d=1$
   Yielding low-pass series $L_t^{(k)}$.
4. **Subseries Low-Pass Subtraction (Seasonal Extraction)**:
   $$S_t^{(k)} = C_t^{(k)} - L_t^{(k)}$$
5. **Deseasonalizing**: Compute deseasonalized series $V_t^{(k)} = Y_t - S_t^{(k)}$.
6. **Trend Smoothing**: Smooth $V_t^{(k)}$ using LOESS with degree $d=1$ and window $n_{(t)}$ to yield $T_t^{(k)}$.

#### Outer Loop Robustness Iteration:
Compute residual $R_t^{(k)} = Y_t - T_t^{(k)} - S_t^{(k)}$.  
Compute median absolute residual $h = 6 \cdot \text{median}(|R_t^{(k)}|)$.  
Compute Tukey's Bisquare Robustness Weight $\rho_t$:

$$B(u) = \begin{cases} (1 - u^2)^2 & \text{for } 0 \le u < 1 \\ 0 & \text{for } u \ge 1 \end{cases}$$
$$\rho_t = B\left( \frac{|R_t^{(k)}|}{h} \right)$$

Weights $\rho_t$ scale the LOESS neighborhood weights in the subsequent inner loop iteration, completely neutralizing extreme outlier spikes.

### 3.4 Cadence-Specific Parameter Tuning Framework
To ensure statistical orthogonality and prevent leakage between trend and seasonality, parameters must strictly satisfy the Cleveland harmonic separation equations:

$$n_{(l)} = \text{Smallest odd integer } \ge n_{(p)}$$
$$n_{(t)} \ge \frac{1.5 \cdot n_{(p)}}{1 - 1.5 / n_{(s)}} \quad (\text{rounded up to next odd integer})$$

#### Parameter Mapping Matrix Across 5 Business Cadences:
```
┌───────────┬──────────────┬───────────┬──────────────┬─────────────┬─────────────┬───────────┬───────────┐
│ Cadence   │ Period n_(p) │ n_(s) Win │ n_(t) Trend  │ n_(l) Pass  │ Inner n_(i) │ Outer n_(o)│ Min Hist N│
├───────────┼──────────────┼───────────┼──────────────┼─────────────┼─────────────┼───────────┼───────────┤
│ Hourly    │ 24 (Diurnal) │ 35 (odd)  │ 39 (odd)     │ 25 (odd)    │ 2           │ 5 (robust)│ 168 (7d)  │
│ Daily     │ 7 (Weekly)   │ 13 (odd)  │ 15 (odd)     │ 7 (odd)     │ 2           │ 5 (robust)│ 60 (2mo)  │
│ Weekly    │ 52 (Annual)  │ 35 (odd)  │ 83 (odd)     │ 53 (odd)    │ 2           │ 5 (robust)│ 104 (2yr) │
│ Monthly   │ 12 (Annual)  │ 19 (odd)  │ 21 (odd)     │ 13 (odd)    │ 2           │ 5 (robust)│ 36 (3yr)  │
│ Quarterly │ 4 (Annual)   │ 7 (odd)   │ 9 (odd)      │ 5 (odd)     │ 2           │ 5 (robust)│ 16 (4yr)  │
└───────────┴──────────────┴───────────┴──────────────┴─────────────┴─────────────┴───────────┴───────────┘
```

### 3.5 Dynamic Expected Baseline, Uncertainty & Anomaly Scoring

1. **Phase-Aligned Dynamic Expected Baseline**:
   $$\hat{Y}_t = T_t + S_t$$

2. **Robust Residual Uncertainty ($\sigma_R$)**:
   To avoid variance inflation from single anomalous spikes:
   $$\sigma_R = 1.4826 \cdot \text{MAD}(R_t) = 1.4826 \cdot \text{median}\left( \left| R_t - \text{median}(R_t) \right| \right)$$

3. **Dynamic Confidence Interval Bands**:
   $$[\text{Lower}_t, \text{Upper}_t] = \left[ \hat{Y}_t - z_{\alpha/2} \cdot \sigma_R, \; \hat{Y}_t + z_{\alpha/2} \cdot \sigma_R \right]$$
   For $99\%$ confidence ($\alpha=0.01$), $z_{\alpha/2} = 2.576$.

4. **Statistical Anomaly $Z$-Score**:
   $$Z_t = \frac{Y_t - \hat{Y}_t}{\sigma_R}$$

5. **Investigation Triggering Condition**:
   A `KPIMovementEvent` is emitted to the LangGraph swarm if and only if:
   $$|Z_t| \ge 2.576 \quad \text{AND} \quad \left| \frac{Y_t - \hat{Y}_t}{\hat{Y}_t} \right| \ge \Delta_{\text{materiality}} \quad (\text{default } 5.0\%)$$

### 3.6 Interface Contracts & Schemas

```python
# app/schemas/timeseries.py (Pydantic V2 Contract Specification)

class STLParameters(BaseModel):
    period: int = Field(..., ge=2, description="Seasonal cycle period n_(p)")
    seasonal_window: int = Field(..., ge=7, description="Loess window for seasonal component n_(s)")
    trend_window: int = Field(..., ge=7, description="Loess window for trend component n_(t)")
    low_pass_window: int = Field(..., ge=3, description="Low-pass filter window n_(l)")
    inner_iterations: int = Field(default=2, ge=1, description="Inner loop iterations n_(i)")
    outer_iterations: int = Field(default=5, ge=0, description="Outer robustness iterations n_(o)")
    robust: bool = Field(default=True, description="Enable Tukey bisquare reweighting")

class TrendDataPoint(BaseModel):
    timestamp: datetime
    actual_value: float
    trend_value: float
    seasonal_value: float
    residual_value: float
    expected_value: float
    lower_bound: float
    upper_bound: float
    is_anomaly: bool
    z_score: float

class STLDecompositionResult(BaseModel):
    tenant_id: str
    kpi_id: str
    cadence: str
    observed_points: int
    residual_std: float
    trend_data: List[TrendDataPoint]
    latest_expected: float
    latest_actual: float
    latest_z_score: float
    anomaly_detected: bool
```

### 3.7 Explicit Exclusion of Contextual Debouncing & Edge-Case Protocols
- **Contextual Debouncing Exclusion**: In strict adherence to Requirement R2, **contextual debouncing is excluded**. The engine evaluates every timestamped observation purely on its mathematical $Z$-score and percentage delta.
- **Sparse History ($N < 2 n_{(p)}$)**: Automatically diverted to Scenario 3 Cold-Start Bayesian prior borrowing.
- **Missing Data**: Interpolated linearly ($g \le 3$) or via seasonal lag ($3 < g \le n_{(p)}$) before STL execution.
- **Multiplicative Metrics**: Modeled via Box-Cox logarithmic transformation $\ln(Y_t + \delta)$ to enforce additive decomposition on strictly positive series.

### 3.8 Objective Synthetic Verification Assertions
The STL engine's accuracy is objectively validated using a deterministic 90-day synthetic benchmark:

$$Y_t = (1000 + 5t) + 200 \sin\left(\frac{2\pi t}{7}\right) + \epsilon_t + A_t$$

Where:
- Linear Trend: $T_t = 1000 + 5t$
- Weekly Seasonality: $S_t = 200 \sin(2\pi t / 7)$
- White Noise: $\epsilon_t \sim \mathcal{N}(0, 15^2)$
- Injected Anomaly: $A_{60} = -600.0$ (Day 60 flash crash)

#### Mathematical Pass/Fail Assertions:
1. **Trend Orthogonality**: Pearson correlation $r(T_t, S_t) \le 0.05$.
2. **Seasonal Recovery**: Seasonal amplitude recovery $|A_{\text{estimated}} - 200| \le 10.0$.
3. **Outlier Neutralization**: Outer robustness weight $\rho_{60} \le 0.05$, preventing trend distortion ($|\hat{T}_{60} - (1000 + 5 \times 60)| \le 20.0$).
4. **Residual Normality**: Shapiro-Wilk test on uncorrupted residuals $p \ge 0.05$.
5. **Anomaly Trigger**: $Z_{60} \le -10.0 \implies \text{Emits } KPIMovementEvent$.

---

## 4. Requirement R3: KPI Scenario Testing Strategy Plan

### 4.1 Scenario 1: Multi-Factor KPI Movement with Known/Simulated Drivers

#### Problem Formulation
Real-world enterprise KPI shifts rarely stem from single isolated causes. In Scenario 1, an overall KPI drop (e.g. $-30\%$ Monthly Net Revenue) results from multiple concurrent drivers acting simultaneously across different dimensions:
- Factor A: A $-40\%$ conversion rate drop in Enterprise Self-Serve (Product release bug).
- Factor B: A $-25\%$ ad spend reduction in Paid Social (Marketing budget cut).
- Factor C: A $+10\%$ compensatory surge in Direct Sales (Organic expansion).

#### Mathematical Multi-Factor Attribution: Exact Shapley Values
To fairly distribute total KPI deviation $\Delta Y$ across $M$ concurrent contributing factors without order bias, the engine computes exact cooperative game-theoretic Shapley Values:

$$\phi_i(v) = \sum_{S \subseteq N \setminus \{i\}} \frac{|S|! (|N| - |S| - 1)!}{|N|!} \left[ v(S \cup \{i\}) - v(S) \right]$$

Where:
- $N$: Set of all candidate driver factors $\{1, 2, \dots, M\}$.
- $S$: Subset coalition of active factors.
- $v(S)$: Characteristic function evaluating expected KPI change given active subset $S$.

#### Axiomatic Guarantees:
1. **Efficiency**: $\sum_{i=1}^M \phi_i = \Delta Y$ (Attributed drivers sum exactly to total observed delta).
2. **Symmetry**: If $v(S \cup \{i\}) = v(S \cup \{j\})$ for all $S$, then $\phi_i = \phi_j$.
3. **Dummy Player**: If $v(S \cup \{i\}) = v(S)$ for all $S$, then $\phi_i = 0$.

#### Logarithmic Mean Divisia Index (LMDI-I) for Multiplicative Trees
For multiplicative KPI trees (e.g. $\text{Revenue} = \text{Traffic} \times \text{Conversion} \times \text{AOV}$), LMDI-I provides exact zero-residual decomposition:

$$\Delta \text{Revenue} = \Delta \text{Rev}_{\text{Traffic}} + \Delta \text{Rev}_{\text{Conversion}} + \Delta \text{Rev}_{\text{AOV}}$$
$$\Delta \text{Rev}_k = L(\text{Rev}_t, \text{Rev}_0) \cdot \ln\left( \frac{x_{k,t}}{x_{k,0}} \right) \quad \text{where } L(a, b) = \frac{a - b}{\ln(a) - \ln(b)}$$

#### Causal DAG Path Validation & Partial Correlation
Using the 17-node NetworkX causal graph (`DEPENDENCY_GRAPH`), the engine calculates first-order partial correlation $\rho_{XY \cdot Z}$ to isolate true root causes from downstream collateral symptoms:

$$\rho_{XY \cdot Z} = \frac{\rho_{XY} - \rho_{XZ} \rho_{YZ}}{\sqrt{(1 - \rho_{XZ}^2)(1 - \rho_{YZ}^2)}}$$

#### Pass/Fail Quantitative Benchmark Metrics:
- **Attribution Mean Absolute Error**: $\text{MAE} = \frac{1}{M} \sum_{i=1}^M |\hat{\phi}_i - \phi_i^{\text{ground\_truth}}| \le 3.5\%$.
- **Driver Top-3 Recall**: $100\%$ (All 3 simulated root drivers identified).
- **False Discovery Rate**: $\text{FDR} \le 0.05$.

---

### 4.2 Scenario 2: Low-Confidence Scenario with Clarification & Abstention

#### Problem Formulation
When diagnostic evidence is contradictory, telemetry data is noisy, or sample sizes are inadequate, the engine must not hallucinate confident root causes. Instead, it must compute a rigorous uncertainty metric, generate structured clarification prompts, and invoke GoRules Rule 22 to abstain from automated actions.

#### Multi-Layer Composite Confidence Score ($C_{\text{composite}}$)

$$C_{\text{composite}} = w_e C_{\text{evidence}} + w_t C_{\text{temporal}} + w_d C_{\text{dag}} - P_{\text{contradictions}} - P_{\text{sample}}$$

Where:
- $C_{\text{evidence}} = \min\left(1.0, \frac{\text{StatSigFindings}}{K}\right) \times \bar{r}^2$: Finding consistency and statistical significance ($w_e = 0.35$).
- $C_{\text{temporal}}$: Fraction of driver shifts preceding the KPI drop ($w_t = 0.35$).
- $C_{\text{dag}}$: Proportion of identified drivers reachable along valid causal paths in NetworkX DAG ($w_d = 0.30$).
- $P_{\text{contradictions}} = 0.20 \times N_{\text{contradictions}}$: Penalty for directional/value contradictions.
- $P_{\text{sample}}$: Small sample size penalty.

#### Three-Tier Decision Gating Architecture

```
                               ┌─────────────────────────────────────────┐
                               │     Composite Confidence C_composite    │
                               └────────────────────┬────────────────────┘
                                                    │
                   ┌────────────────────────────────┼────────────────────────────────┐
                   │                                │                                │
                   ▼                                ▼                                ▼
         C_composite >= 0.85             0.70 <= C_composite < 0.85          C_composite < 0.70
       ┌─────────────────────┐          ┌────────────────────────┐         ┌─────────────────────┐
       │   GoRules Rule 20   │          │    GoRules Rule 21     │         │   GoRules Rule 22   │
       │       ALLOWED       │          │      HUMAN_REVIEW      │         │       ABSTAIN       │
       │ Full Auto-Execution │          │  Clarification Prompt  │         │ Block All Levers    │
       └─────────────────────┘          └────────────────────────┘         └─────────────────────┘
```

#### Structured Clarification Request Payload

```json
{
  "request_type": "CLARIFICATION_REQUIRED",
  "kpi_id": "checkout_conversion_rate",
  "composite_confidence": 0.62,
  "confidence_breakdown": {
    "evidence_score": 0.58,
    "temporal_score": 0.70,
    "dag_validity_score": 0.60,
    "contradiction_penalty": 0.20
  },
  "conflicting_hypotheses": [
    {"hypothesis_id": "H1", "driver": "Payment Gateway Timeout", "support": "Customer Agent"},
    {"hypothesis_id": "H2", "driver": "Promotional Discount Expired", "support": "Channel Agent"}
  ],
  "missing_dimensions": ["payment_processor_type", "user_subscription_tier"],
  "suggested_operator_queries": [
    "SELECT payment_method, COUNT(*) FROM checkout_errors WHERE status_code = 504 GROUP BY 1",
    "SELECT promo_code, SUM(discount_amount) FROM redemptions WHERE date >= '2026-08-20'"
  ],
  "governance_verdict": {
    "rule_applied": 22,
    "decision_right": "ABSTAIN",
    "automation_blocked": true
  }
}
```

---

### 4.3 Scenario 3: Sparse-History / Newly Launched KPI Scenario (Cold Start)

#### Problem Formulation
Newly launched KPIs or emerging regional markets have sparse historical time series ($N < 14$ days), making standard STL decomposition and asymptotic normal models statistically invalid ($N < 2 n_{(p)}$).

#### Hierarchical Empirical Bayesian Prior Borrowing
The engine resolves cold starts by borrowing statistical parameters from parent product categories, global benchmarks, or related metric cohorts:

$$\theta_{\text{new}} \sim \mathcal{N}(\mu_0, \sigma_0^2) \quad \text{where } (\mu_0, \sigma_0^2) \text{ are estimated from the parent cohort}$$

Given $N$ observed points with sample mean $\bar{y}$ and sample variance $s^2$:

$$\mu_N = (1 - B) \bar{y} + B \mu_0 \quad \text{where shrinkage factor } B = \frac{\sigma^2 / N}{\sigma_0^2 + \sigma^2 / N} = \frac{\kappa_0}{\kappa_0 + N}$$
$$\sigma_N^2 = \frac{1}{\frac{N}{\sigma^2} + \frac{1}{\sigma_0^2}}$$

- When $N \to 0$, $\mu_N \to \mu_0$ (Baseline defaults safely to parent category expectation).
- As $N \to \infty$, $\mu_N \to \bar{y}$ (Baseline converges smoothly to the new KPI's empirical reality).

#### Surrogate Proxy Indicator Mapping
When the primary KPI (e.g. *Enterprise LTV*) has insufficient history, the engine dynamically binds to fast-moving upstream funnel proxies:
$$\text{Surrogate Precursor Funnel}: \quad \text{Ad Clicks} \longrightarrow \text{Trial Starts} \longrightarrow \text{Product Activations} \longrightarrow \text{Paid Conversions}$$

#### Dynamic 95% Bayesian Credible Interval Widening
To visually communicate sparse-history uncertainty on the frontend visualizer, confidence bands expand inversely with $\sqrt{N}$:

$$\kappa(N) = 1.0 + \frac{2.5}{\sqrt{N}}$$
$$[\text{Lower}_t, \text{Upper}_t] = \left[ \mu_N - 1.96 \cdot \kappa(N) \cdot \sigma_N, \; \mu_N + 1.96 \cdot \kappa(N) \cdot \sigma_N \right]$$

#### Mandatory Persona Narrative Disclosure:
Every story generated under cold-start gating includes mandatory epistemic caveats:
> *"Notice: This metric was launched 6 days ago (N=6 < 14). Baselines are synthesized via Bayesian prior borrowing from [SaaS Enterprise Tier]. Confidence intervals are widened by 202% to account for sample variance."*

---

### 4.4 Scenario 4: Role-Based Security & Entitlements Scenario

#### Problem Formulation
The BI engine serves diverse enterprise personas (Executive, Finance, Engineering, Sales) across multi-tenant deployments. Diagnostic investigations, raw SQL queries, and generated stories must strictly enforce tenant isolation, metric entitlements, and dynamic PII/margin data masking.

#### Comprehensive `SecurityContext` Model

```python
# app/schemas/security.py (Contract Specification)

class SecurityContext(BaseModel):
    user_id: str = Field(..., description="Unique authenticated user identity")
    tenant_id: str = Field(..., description="Multi-tenant organization boundary")
    roles: List[PersonaRole] = Field(..., description="Active user roles")
    permitted_metrics: List[str] = Field(default_factory=list, description="Whitelisted KPI IDs")
    permitted_dimensions: List[str] = Field(default_factory=list, description="Whitelisted dimensions")
    can_view_margins: bool = Field(default=False, description="Entitlement for gross margin/COGS")
    can_view_pii: bool = Field(default=False, description="Entitlement for customer PII")
    max_approval_limit: float = Field(default=0.0, description="Financial authority threshold ($USD)")
```

#### Multi-Tenant AST Parameterized Query Rewriting
All domain agent SQL queries (`app/tools/*`) are intercepted by a secure SQL AST parser that automatically injects tenant and regional scoping:

```sql
-- Original Agent Query:
SELECT customer_id, gross_margin, lifetime_value FROM customer_metrics WHERE kpi_id = 'net_revenue';

-- Intercepted & Rewritten Multi-Tenant Query:
SELECT customer_id, gross_margin, lifetime_value 
FROM customer_measurements 
WHERE tenant_id = :tenant_id 
  AND kpi_id = :kpi_id 
  AND region IN (:permitted_regions)
LIMIT 1000;
```

#### Pre-Synthesis ABAC Metric & Dimension Filtering
Before agent findings enter `analysis_node` and `contradiction_node`:
- Findings associated with metrics not present in `SecurityContext.permitted_metrics` are completely pruned from the graph state.
- Unauthorized dimension slices (e.g. `Executive_Salary_Band`) are removed before LLM prompt assembly.

#### Dynamic Cryptographic Data Masking & Redaction

```
┌──────────────────────────────────────┬───────────────────────────────────┬───────────────────────────────────┐
│ Sensitive Field                      │ User With Privilege (Finance/Exec)│ User Without Privilege (Eng/Sales)│
├──────────────────────────────────────┼───────────────────────────────────┼───────────────────────────────────┤
│ Customer Email                       │ john.doe@enterprise.com           │ CUST-***-SHA256:7f8a              │
│ Customer Phone                       │ +1 (415) 555-0199                 │ [REDACTED - PII]                  │
│ Gross Margin %                       │ 74.2%                             │ [REDACTED - CONFIDENTIAL]         │
│ Unit COGS ($)                        │ $142.50                           │ [REDACTED - FINANCIAL]            │
└──────────────────────────────────────┴───────────────────────────────────┴───────────────────────────────────┘
```

#### GoRules Role Authorization Enforcement (Rules 13-16)
- **Rule 13**: `PersonaRole == 'ENGINEERING'` $\implies$ Restricts recommendations to infrastructure/code rollbacks; financial discount levers are `PROHIBITED`.
- **Rule 14**: `PersonaRole == 'SALES'` $\implies$ Restricts recommendations to pricing quotes; infrastructure restarts are `PROHIBITED`.
- **Rule 15**: `PersonaRole == 'EXECUTIVE'` $\implies$ Authorizes strategic pricing and budget reallocation levers up to `max_approval_limit`.
- **Rule 16**: `ActionCost > SecurityContext.max_approval_limit` $\implies$ Decision right downgraded to `HUMAN_REVIEW` with required CFO sign-off.

---

## 5. Requirement R4: Golden Datasets & Runtime Telemetry Integration

### 5.1 Golden Datasets Generation & 4-Tier Catalog

#### `GoldenDatasetSpec` Pydantic V2 Contract Schema

```python
# app/schemas/golden.py (Contract Specification)

class GroundTruthDriver(BaseModel):
    driver_name: str
    dimension_key: str
    dimension_value: str
    true_contribution_pct: float
    causal_path: List[str]
    onset_timestamp: datetime

class ExpectedGovernanceAction(BaseModel):
    rule_id: int
    decision_right: str  # ALLOWED, HUMAN_REVIEW, PROHIBITED, ABSTAIN
    expected_action: str

class GoldenDatasetSpec(BaseModel):
    benchmark_id: str
    tier: Literal["Tier1_Unit", "Tier2_Boundary", "Tier3_Interaction", "Tier4_RealWorld"]
    description: str
    kpi_id: str
    cadence: str
    input_time_series: List[Dict[str, Any]]
    ground_truth_movement: Dict[str, Any]
    ground_truth_drivers: List[GroundTruthDriver]
    expected_governance: ExpectedGovernanceAction
    expected_persona_facts: Dict[str, List[str]]
    dataset_version: str = "1.0.0"
```

#### 4-Tier Golden Dataset Catalog (19 Benchmark Incidents)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                             4-TIER GOLDEN DATASET BENCHMARK CATALOG                     │
├───────┬───────────────────────┬───────┬─────────────────────────────────────────────────┤
│ Tier  │ Benchmark Category    │ Count │ Core Verification Focus                         │
├───────┼───────────────────────┼───────┼─────────────────────────────────────────────────┤
│ 1     │ Feature Unit Coverage │ 5     │ Single-factor drops across Product, Customer,   │
│       │                       │       │ Geography, Channel, and Operational Latency.    │
├───────┼───────────────────────┼───────┼─────────────────────────────────────────────────┤
│ 2     │ Boundary & Noise      │ 5     │ Flash crashes (1-point drop), high noise        │
│       │ Stress Testing        │       │ (SNR = 1.0), sparse cold-starts (N=7), missing  │
│       │                       │       │ values (20%), and zero-inflated time series.    │
├───────┼───────────────────────┼───────┼─────────────────────────────────────────────────┤
│ 3     │ Cross-Factor &        │ 5     │ Multi-factor drivers (3 concurrent), competing  │
│       │ Contradiction Stress  │       │ agent contradictions, non-stationary trends,    │
│       │                       │       │ and DAG feedback loops.                         │
├───────┼───────────────────────┼───────┼─────────────────────────────────────────────────┤
│ 4     │ Enterprise Incident   │ 4     │ Sanitized real-world enterprise outages:        │
│       │ Scenarios             │       │ Black Friday payment gateway outage, Cloudflare │
│       │                       │       │ CDN regional routing failure, enterprise price  │
│       │                       │       │ tier migration churn, multi-tenant data leak.   │
└───────┴───────────────────────┴───────┴─────────────────────────────────────────────────┘
```

#### Storage & Semantic Versioning
- **Directory Structure**:
  ```
  kpi-engine/tests/golden/
  ├── v1.0.0/
  │   ├── manifests/ (JSON manifests conforming to GoldenDatasetSpec)
  │   └── data/ (Snappy-compressed Parquet time-series vectors)
  ```
- **DVC / Git LFS Tracking**: Dataset binaries are tracked via Data Version Control (DVC) backed by S3, ensuring 100% reproducible benchmark evaluation.

### 5.2 Automated CI/CD Regression Evaluation Benchmark Suite
In CI/CD pipelines, the benchmark harness runs all 19 Golden Datasets against the engine and enforces 4 quantitative scoring thresholds:

$$\text{Driver Recall} = \frac{|\text{Identified True Drivers} \cap \text{Ground Truth Drivers}|}{|\text{Ground Truth Drivers}|} \ge 1.00 \quad (\text{Zero missed root causes})$$
$$\text{Attribution MAE} = \frac{1}{M} \sum_{i=1}^M |\hat{\phi}_i - \phi_i^{\text{ground\_truth}}| \le 3.5\%$$
$$\text{Abstention Precision} = \frac{\text{Correctly Executed Abstentions}}{\text{Total Low-Confidence Scenarios}} = 100.0\%$$
$$\text{Security Leakage Rate} = \frac{\text{Unredacted PII or Margin Violations}}{\text{Total Evaluated Outputs}} = 0.00\%$$

---

### 5.3 Runtime Telemetry Observability Framework & Cost Engine
The telemetry framework satisfies the frontend UI contract (`Latency`, `Model Calls`, `Token Usage`, `Est. Cost`) using OpenTelemetry (OTel) distributed tracing and custom LangChain callback handlers.

#### Dynamic Cost Estimation Pricing Matrix

$$\text{Cost} = \sum_{\text{models}} \left( \frac{\text{PromptTokens}}{1,000,000} \cdot P_{\text{prompt}} + \frac{\text{CompletionTokens}}{1,000,000} \cdot P_{\text{completion}} + \frac{\text{CachedTokens}}{1,000,000} \cdot P_{\text{cached}} \right)$$

```
┌───────────────────────────┬──────────────────────┬──────────────────────────┬────────────────────────┐
│ Model Name                │ Prompt Price / 1M    │ Completion Price / 1M    │ Cached Prompt / 1M     │
├───────────────────────────┼──────────────────────┼──────────────────────────┼────────────────────────┤
│ gpt-4o-mini (Default)     │ $0.150               │ $0.600                   │ $0.075                 │
│ gpt-4o (Executive Persona)│ $2.500               │ $10.000                  │ $1.250                 │
│ claude-3-5-sonnet         │ $3.000               │ $15.000                  │ $0.300                 │
└───────────────────────────┴──────────────────────┴──────────────────────────┴────────────────────────┘
```

---

### 5.4 All 7 Exact Runtime Telemetry Hook Placements

The observability architecture instruments seven exact hook placements across the backend pipeline. Each hook operates inside a non-blocking `try/except` wrapper, ensuring telemetry failures never interrupt business investigations.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              RUNTIME TELEMETRY HOOK ARCHITECTURE                       │
│                                                                                        │
│   [Client Request]                                                                     │
│          │                                                                             │
│          ▼                                                                             │
│   ┌──────────────┐  HOOK 1: FastAPI Request Lifecycle Middleware                       │
│   │ Middleware   │  Path: `kpi-engine/app/api/middleware.py` :: TelemetryMiddleware    │
│   └──────┬───────┘  Captures: Total Request Latency, HTTP Status, Tenant ID            │
│          │                                                                             │
│          ▼                                                                             │
│   ┌──────────────┐  HOOK 2: Database Query Execution Interceptor                       │
│   │ Database SQL │  Path: `kpi-engine/app/database.py` :: execute_monitored_query      │
│   └──────┬───────┘  Captures: DB Query Duration, Rows Returned, Query Hash             │
│          │                                                                             │
│          ▼                                                                             │
│   ┌──────────────┐  HOOK 3: LangGraph Agent Swarm Fan-Out Execution                    │
│   │ Agent Swarm  │  Path: `kpi-engine/app/orchestrator/nodes.py` :: BaseAgentNode      │
│   └──────┬───────┘  Captures: Per-Agent Latency, Concurrency Fan-Out, Findings Count   │
│          │                                                                             │
│          ▼                                                                             │
│   ┌──────────────┐  HOOK 4: Analytical Computation & Attribution Algorithms            │
│   │ Analytics    │  Path: `kpi-engine/app/orchestrator/nodes.py` :: analysis_node      │
│   └──────┬───────┘  Captures: STL / Shapley CPU Execution Time, Vector Sizes           │
│          │                                                                             │
│          ▼                                                                             │
│   ┌──────────────┐  HOOK 5: Diagnostic Orchestrator LLM Invocation                     │
│   │ Orch LLM     │  Path: `kpi-engine/app/orchestrator/llm.py` :: invoke_diagnostic_llm│
│   └──────┬───────┘  Captures: LLM Latency, Model Name, Prompt/Completion Tokens, Cost  │
│          │                                                                             │
│          ▼                                                                             │
│   ┌──────────────┐  HOOK 6: GoRules Decision Table Governance Evaluation               │
│   │ GoRules      │  Path: `kpi-engine/app/governance/engine.py` :: evaluate_governance │
│   └──────┬───────┘  Captures: ZenEngine Evaluation Latency, Rules Fired, Verdict       │
│          │                                                                             │
│          ▼                                                                             │
│   ┌──────────────┐  HOOK 7: Persona Storytelling LLM Generation                        │
│   │ Persona LLM  │  Path: `kpi-engine/app/orchestrator/persona.py` :: generate_story   │
│   └──────┬───────┘  Captures: Story Gen Latency, Persona Role, Token Counts, Cost      │
│          │                                                                             │
│          ▼                                                                             │
│   [Aggregate TelemetryPayload] ──► Inject into DiagnosticPayload & HTTP Headers        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Detailed Hook Specifications:

1. **Hook 1: FastAPI Request Lifecycle Middleware**
   - **Target File**: `kpi-engine/app/api/middleware.py`
   - **Target Class/Function**: `TelemetryMiddleware.dispatch(request, call_next)`
   - **Captured Metrics**: `total_latency_ms`, HTTP status code, endpoint route, `tenant_id`, `trace_id`.
   - **Propagation**: Initializes `contextvars.ContextVar("request_telemetry")` and injects `X-Trace-ID`, `X-Latency-MS`, `X-Total-Cost-USD` response headers.

2. **Hook 2: Database Query Execution Interceptor**
   - **Target File**: `kpi-engine/app/database.py` (and `app/tools/*`)
   - **Target Class/Function**: `execute_monitored_query(session, sql_query, params)`
   - **Captured Metrics**: `db_latency_ms`, table name, query operation type (SELECT/INSERT), row count.

3. **Hook 3: LangGraph Agent Swarm Fan-Out Execution**
   - **Target File**: `kpi-engine/app/orchestrator/nodes.py`
   - **Target Functions**: `product_agent`, `customer_agent`, `geography_agent`, `channel_agent` wrappers.
   - **Captured Metrics**: Individual agent execution duration, number of emitted findings, SQL queries executed per agent.

4. **Hook 4: Analytical Computation & Attribution Algorithms**
   - **Target File**: `kpi-engine/app/orchestrator/nodes.py` (invoking `app/analytics/`)
   - **Target Function**: `analysis_node(state)`
   - **Captured Metrics**: Algorithm computation duration (STL decomposition ms, Shapley attribution ms, Causal DAG validation ms).

5. **Hook 5: Diagnostic Orchestrator LLM Invocation**
   - **Target File**: `kpi-engine/app/orchestrator/llm.py`
   - **Target Class/Function**: `invoke_diagnostic_llm(messages)` / `TelemetryCallbackHandler.on_llm_end()`
   - **Captured Metrics**: `llm_latency_ms`, `model_name`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `estimated_cost_usd`.

6. **Hook 6: GoRules Decision Table Governance Evaluation**
   - **Target File**: `kpi-engine/app/governance/engine.py`
   - **Target Function**: `evaluate_recommendation(finding, recommendation)`
   - **Captured Metrics**: `governance_latency_ms`, `rules_evaluated_count`, `rule_ids_fired` (e.g. `[20, 23]`), `decision_right`.

7. **Hook 7: Persona Storytelling LLM Generation**
   - **Target File**: `kpi-engine/app/orchestrator/persona.py`
   - **Target Function**: `generate_persona_story(diagnostic_payload, persona_role)`
   - **Captured Metrics**: Persona story generation duration, persona role (`EXECUTIVE`, `FINANCE`, `ENGINEERING`, `SALES`), prompt/completion tokens, model cost.

#### Frontend Telemetry JSON Schema Injection Contract:
The combined telemetry metrics are attached directly to the `DiagnosticPayload` returned to the frontend dashboard:

```json
{
  "telemetry": {
    "trace_id": "tr-7f8a9e01-2026-0830",
    "total_latency_ms": 462.4,
    "breakdown": {
      "db_latency_ms": 38.2,
      "agent_swarm_latency_ms": 142.6,
      "analytical_math_latency_ms": 24.1,
      "orchestrator_llm_latency_ms": 118.5,
      "governance_latency_ms": 4.2,
      "persona_story_llm_latency_ms": 134.8
    },
    "model_calls": {
      "total_calls": 2,
      "gpt-4o-mini": 1,
      "gpt-4o": 1
    },
    "tokens": {
      "prompt_tokens": 3420,
      "completion_tokens": 820,
      "total_tokens": 4240
    },
    "estimated_cost_usd": 0.01248
  }
}
```

---

## 6. Target Code Layout & Implementation Roadmap

### 6.1 Complete Code Layout

```
kpi-engine/
├── app/
│   ├── api/
│   │   ├── routes.py                # FastAPI routes (/ingest, /investigations, /persona, /telemetry)
│   │   └── middleware.py            # Hook 1: TelemetryMiddleware & SecurityContext propagation
│   ├── ingestion/
│   │   ├── pipeline.py              # Bronze -> Silver -> Gold Medallion ingestion pipeline
│   │   ├── validation.py            # 6-tier Pydantic, Pandera, Temporal, Reconciliation gate
│   │   ├── quarantine.py            # Dead-letter quarantine storage and replay API
│   │   ├── scoring.py               # Continuous DQ scoring algorithm
│   │   └── imputation.py            # Time-series regularization and Akima/lag imputation
│   ├── timeseries/
│   │   ├── stl.py                   # Cleveland et al. (1990) LOESS & 2-Loop STL decomposition
│   │   ├── baseline.py              # Dynamic expected baseline Ŷ_t and MAD uncertainty σ_R
│   │   ├── anomaly.py               # Statistical Z-score calculation & KPIMovementEvent trigger
│   │   └── parameters.py            # Cadence parameter matrix (Hourly, Daily, Weekly, Monthly)
│   ├── analytics/
│   │   ├── contribution.py          # Exact Shapley value and LMDI-I multi-factor attribution
│   │   ├── dependency.py            # NetworkX causal DAG and partial correlation validation
│   │   └── contradictions.py        # Dimensional and directional contradiction detection
│   ├── scenarios/
│   │   ├── multifactor.py           # Scenario 1: Multi-driver evaluation & attribution
│   │   ├── confidence.py            # Scenario 2: Composite confidence score & clarification payload
│   │   ├── coldstart.py             # Scenario 3: Hierarchical Bayesian prior borrowing (N < 14)
│   │   └── security.py              # Scenario 4: Multi-tenant SQL rewriter & dynamic PII masking
│   ├── telemetry/
│   │   ├── collector.py             # OpenTelemetry tracer & LangChain callback handlers
│   │   ├── pricing.py               # Dynamic model token pricing tables & cost calculator
│   │   └── hooks.py                 # Telemetry decorators and non-blocking hook interceptors
│   ├── governance/
│   │   ├── engine.py                # Hook 6: GoRules ZenEngine decision evaluator
│   │   └── decision_table.json      # 30 Business Rules (Rules 1-30, including Rules 20-23)
│   ├── orchestrator/
│   │   ├── graph.py                 # LangGraph StateGraph (Upstream STL + Swarm + Synthesis)
│   │   ├── nodes.py                 # Swarm agent nodes, analysis, orchestrator, governance nodes
│   │   ├── llm.py                   # Hook 5: Diagnostic Orchestrator LLM caller
│   │   └── persona.py               # Hook 7: Multi-Persona storytelling generator with masking
│   └── schemas/
│       ├── ingestion.py             # Pydantic schemas for Ingestion, Validity, Quarantine, DQ
│       ├── timeseries.py            # Pydantic schemas for STLParameters, TrendDataPoint, STLResult
│       ├── scenarios.py             # Schemas for SecurityContext, Confidence, Clarification
│       ├── telemetry.py             # Schemas for TelemetryRecord and TelemetryBreakdown
│       └── golden.py                # Schemas for GoldenDatasetSpec and EvaluationMetrics
└── tests/
    ├── conftest.py                  # Pytest fixtures and mock database/S3 containers
    ├── test_ingestion_validity.py   # R1: 6-Tier validity gate & mock verification tests
    ├── test_timeseries_stl.py       # R2: Cleveland STL orthogonality & bisquare wave tests
    ├── test_kpi_scenarios.py        # R3: Scenarios 1-4 deterministic test harness
    ├── test_telemetry_hooks.py      # R4: 7 Telemetry hooks latency & cost tracking tests
    └── golden/
        └── v1.0.0/                  # 19 Standardized Golden Benchmark Incidents (JSON + Parquet)
```

### 6.2 Step-by-Step Implementation Roadmap

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          PHASED ENGINEERING IMPLEMENTATION ROADMAP                     │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Phase 1: Ingestion & Validity Infrastructure (M1 / R1)                                  │
│ - Implement PostgreSQL DDL partitions and quarantine tables.                          │
│ - Build Polars Silver normalization and 6-Tier Pandera/Pydantic validity gates.        │
│ - Integrate composite DQ scoring and bind to GoRules Rule 23.                          │
│ - Execute mock data verification test suite (TC-1.1 through TC-1.6).                   │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Phase 2: Upstream STL Time-Series Engine (M2 / R2)                                     │
│ - Implement `kpi-engine/app/timeseries/stl.py` with Cleveland LOESS & 2-loop STL.     │
│ - Build `kpi_extractor_node` and `stl_evaluator_node` upstream of LangGraph swarm.     │
│ - Connect dynamic baseline and uncertainty bounds to Vega-Lite `metadata.trend_data`.  │
│ - Verify orthogonality and outlier robustness using the 90-day synthetic wave test.    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Phase 3: Advanced Scenario Engines & Security (M3 / R3)                                │
│ - Upgrade `app/analytics/contribution.py` to exact Shapley and LMDI-I attribution.     │
│ - Implement Composite Confidence index $C_{\text{composite}}$ & clarification prompts. │
│ - Build Hierarchical Bayesian prior borrowing for Cold-Start ($N < 14$) metrics.       │
│ - Deploy `SecurityContext`, parameterized SQL rewriter, and dynamic PII/margin masking.│
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Phase 4: Telemetry Instrumentation & Golden Dataset Harness (M4 / R4)                  │
│ - Deploy all 7 telemetry hooks across middleware, DB, swarm, math, LLMs, & GoRules.   │
│ - Build dynamic cost calculator supporting OpenAI and Anthropic token pricing.         │
│ - Ingest 19 Golden Datasets (`v1.0.0`) into `tests/golden/`.                           │
│ - Integrate automated benchmark evaluation into CI/CD pipeline.                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```
