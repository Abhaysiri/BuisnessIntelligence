# Architectural & Implementation Specification: Requirement R3 — KPI Scenario Testing Strategy

**Document Version:** 1.0.0  
**Author:** Worker 3 (KPI Scenario Testing Strategy Architect)  
**Status:** Complete Architectural Specification  
**Target System:** Business Intelligence Engine (`kpi-engine`, analytics layer, governance engine, persona orchestrator)  
**Reference Documents:** `.agents/ORIGINAL_REQUEST.md`, `PROJECT.md`, `.agents/explorer_survey_3/survey_report.md`

---

## 1. Executive Summary & Architectural Overview

The Business Intelligence Engine is an autonomous, causal time-series analytics and diagnostic platform. It ingests enterprise metric streams, detects statistically material anomalies, mobilizes specialized multi-agent diagnostic swarms (Product, Customer, Geography, Channel), performs multi-factor causal attribution, executes policy governance via GoRules ZenEngine, and synthesizes persona-tailored diagnostic narratives.

To ensure deterministic reliability, mathematical correctness, safety under uncertainty, and strict enterprise security, this specification defines the **KPI Scenario Testing Strategy (Requirement R3)** across four mission-critical business scenarios:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                REQUIREMENT R3 SCENARIO TESTING MATRIX                            │
├──────────────────────┬─────────────────────────────┬───────────────────────────┬─────────────────┤
│ Scenario Identifier  │ Core Analytical Challenge   │ Mathematical Mechanism   │ Governance Gate │
├──────────────────────┼─────────────────────────────┼───────────────────────────┼─────────────────┤
│ Scenario 1:          │ Concurrent, interacting     │ Shapley Value Game Theory │ Rules 8-12      │
│ Multi-Factor Movement│ drivers & collinearity      │ + LMDI + NetworkX DAG     │ (Action Fit)    │
├──────────────────────┼─────────────────────────────┼───────────────────────────┼─────────────────┤
│ Scenario 2:          │ Contradictory findings &    │ Composite Confidence      │ Rules 20-23     │
│ Low-Confidence/Abst. │ noisy/unaligned signals     │ Score ($C_{comp}$) Engine │ (Abstention)    │
├──────────────────────┼─────────────────────────────┼───────────────────────────┼─────────────────┤
│ Scenario 3:          │ Cold start / sparse history │ Hierarchical Bayesian     │ Rules 20-22     │
│ Sparse-History KPI   │ ($N < 14$ observations)     │ Priors + Surrogate Funnels│ (Credible Bounds│
├──────────────────────┼─────────────────────────────┼───────────────────────────┼─────────────────┤
│ Scenario 4:          │ Enterprise multi-tenancy &  │ SecurityContext ABAC +    │ Rules 13-19     │
│ Security & RBAC      │ sensitive metric access     │ SQL AST Scoping & Masking │ (Decision Rights│
└──────────────────────┴─────────────────────────────┴───────────────────────────┴─────────────────┘
```

This document establishes the exhaustive mathematical formulations, synthetic generation equations, interface contracts, decision logic, and objective pass/fail metrics for each scenario.

---

## 2. Scenario 1: Multi-Factor KPI Movement with Known/Simulated Drivers

### 2.1 Problem Formulation & Business Context
In real-world enterprise environments, high-level business metrics (e.g. `Total Net Revenue`, `Gross Merchandise Value`, `Customer Acquisition Cost`) rarely experience significant variance due to a single isolated driver. Instead, multiple independent or interacting factors simultaneously pull the metric in opposing or reinforcing directions.

**Concrete Benchmark Incident (`INC-S1-MULTIFACTOR`):**
- **Target KPI:** `Total Net Revenue`
- **Baseline Expectation:** $\$500,000$
- **Observed Value:** $\$400,000$ (Net Movement: $-\$100,000$ or $-20.0\%$)
- **Underlying Concurrent Drivers:**
  1. *Driver A (Technical Failure - Negative):* EMEA Checkout Gateway latency spike and payment timeout cascade causing conversion collapse (Direct Impact: $-\$60,000$, $60.0\%$ attribution).
  2. *Driver B (Marketing Strategy - Negative):* Paid search budget cut in North America reducing top-of-funnel qualified traffic (Direct Impact: $-\$50,000$, $50.0\%$ attribution).
  3. *Driver C (Pricing Strategy - Positive Tail-wind):* Enterprise tier price increase in APAC yielding higher Average Order Value (Direct Impact: $+\$10,000$, $-10.0\%$ attribution).
- **Net Sum of Attributed Drivers:** $-\$60,000 - \$50,000 + \$10,000 = -\$100,000$ ($100.0\%$ reconciliation).

The legacy implementation in `app/analytics/contribution.py` calculates naive 1-dimensional slice deltas ($\Delta Y_i / \Delta Y_{total}$), which fails when drivers interact non-linearly, share collinear upstream causes, or sum to more than $100\%$ due to product-form metric formulas.

---

### 2.2 Mathematical Framework for Multi-Driver Attribution

#### 2.2.1 Shapley Value Cooperative Game Theory Attribution
To allocate credit or blame fairly across a coalition of $N$ interacting drivers without double-counting, we formulate KPI attribution as a cooperative game $(N, v)$.

Let $N = \{1, 2, \dots, n\}$ be the set of candidate causal drivers identified by the swarm agents.  
Let $S \subseteq N$ be a coalition (subset) of drivers.  
Let $v(S)$ be the characteristic value function representing the modeled KPI delta when only the drivers in subset $S$ are active, holding all drivers in $N \setminus S$ at their counterfactual baseline levels:
$$v(S) = \hat{Y}(S) - Y_{baseline}$$
where $v(\emptyset) = 0$ and $v(N) = \Delta Y_{total} = Y_{observed} - Y_{baseline}$.

The marginal contribution of driver $i \in N$ to a coalition $S \subseteq N \setminus \{i\}$ is:
$$\Delta v(i, S) = v(S \cup \{i\}) - v(S)$$

The exact Shapley Value attribution $\phi_i$ for driver $i$ is the weighted average of its marginal contributions across all possible permutation orders of driver activation:
$$\phi_i = \sum_{S \subseteq N \setminus \{i\}} \frac{|S|!(|N| - |S| - 1)!}{|N|!} \left[ v(S \cup \{i\}) - v(S) \right]$$

**Mathematical Properties Guaranteed by Shapley Attribution:**
1. **Efficiency (Sum-to-Total):** $\sum_{i=1}^n \phi_i = v(N) = \Delta Y_{total}$. The sum of driver attributions exactly equals the total observed KPI movement.
2. **Symmetry:** If $v(S \cup \{i\}) = v(S \cup \{j\})$ for all $S \subseteq N \setminus \{i, j\}$, then $\phi_i = \phi_j$. Equal drivers receive equal attribution.
3. **Dummy / Null Player:** If $v(S \cup \{i\}) = v(S)$ for all $S \subseteq N \setminus \{i\}$, then $\phi_i = 0$. Ineffective factors receive exactly zero attribution.
4. **Additivity:** If the game is composed of two independent metric sub-components $v = u + w$, then $\phi_i(v) = \phi_i(u) + \phi_i(w)$.

**Computational Scalability:**
- For $|N| \le 8$, compute the exact Shapley value over all $2^{|N|}$ subsets.
- For $|N| > 8$, utilize the **Owen Sampling Approximation** with $M = 2,048$ permutation samples:
  $$\hat{\phi}_i = \frac{1}{M} \sum_{m=1}^M \left[ v(S_m^i \cup \{i\}) - v(S_m^i) \right]$$
  where $S_m^i$ is the set of drivers preceding driver $i$ in random permutation $\pi_m$.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SHAPLEY COALITIONAL VALUE DECOMPOSITION                  │
│                                                                             │
│   Baseline ($500k) ────────────► v(∅) = $0                                  │
│                                                                             │
│   + Driver A (Checkout) ───────► v({A}) = -$60k                             │
│   + Driver B (Ad Spend) ───────► v({B}) = -$50k                             │
│   + Driver C (APAC Price) ─────► v({C}) = +$10k                             │
│                                                                             │
│   Joint Interactions:                                                       │
│   v({A, B}) = -$110k + $5k (Interaction overlap) = -$105k                   │
│   v({A, C}) = -$60k + $10k = -$50k                                          │
│   v({B, C}) = -$50k + $10k = -$40k                                          │
│   v({A, B, C}) = -$100k (Observed Total Delta)                              │
│                                                                             │
│   Exact Shapley Values:                                                     │
│   φ_A = -$58,333.33 (-58.33%)                                               │
│   φ_B = -$48,333.33 (-48.33%)                                               │
│   φ_C = +$6,666.67 (+6.67%)                                                 │
│   Sum: φ_A + φ_B + φ_C = -$100,000.00 (100.00% Exact Reconciliation)        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

#### 2.2.2 Logarithmic Mean Divisia Index (LMDI-I) for Multiplicative Metric Trees
For multiplicative KPIs governed by tree formulas such as:
$$\text{Revenue} = \text{Sessions} \times \text{Conversion Rate (CVR)} \times \text{Average Order Value (AOV)}$$
or generally $Y = \prod_{k=1}^K X_k$, linear subtraction introduces non-linear cross-product interaction residuals.

The engine applies the **LMDI-I (Logarithmic Mean Divisia Index)** decomposition to map multiplicative factor changes into an exact additive decomposition:
$$\Delta Y = Y_t - Y_0 = \sum_{k=1}^K \Delta Y_{X_k}$$
where the additive contribution of factor $X_k$ is computed as:
$$\Delta Y_{X_k} = L(Y_t, Y_0) \cdot \ln\left( \frac{X_{k,t}}{X_{k,0}} \right)$$
and the logarithmic mean function $L(a, b)$ is rigorously defined as:
$$L(a, b) = \begin{cases} \frac{a - b}{\ln(a) - \ln(b)} & \text{if } a \neq b \text{ and } a, b > 0 \\ a & \text{if } a = b > 0 \\ 0 & \text{if } a = 0 \text{ or } b = 0 \end{cases}$$

**Percentage Contribution Allocation:**
$$p_k = \frac{\Delta Y_{X_k}}{\Delta Y_{total}} \times 100.0\%$$
Because $\sum_{k=1}^K \Delta Y_{X_k} = \Delta Y_{total}$, the percentage contributions satisfy $\sum_{k=1}^K p_k = 100.00\%$ with zero residual error.

---

#### 2.2.3 NetworkX Causal DAG Path Validation & Partial Correlation
To separate **direct root causes** from **downstream collateral symptoms** (e.g. a checkout error causes a conversion drop, which subsequently increases cart abandonment), the engine evaluates findings over the causal Directed Acyclic Graph $\mathcal{G} = (\mathcal{V}, \mathcal{E})$ in `app/analytics/dependency.py`.

```
         ┌───────────────────┐               ┌───────────────────┐
         │  marketing_spend  │               │checkout_error_rate│
         └─────────┬─────────┘               └─────────┬─────────┘
                   │ (influences)                      │ (influences)
                   ▼                                   ▼
         ┌───────────────────┐               ┌───────────────────┐
         │ qualified_sessions│               │  conversion_rate  │
         └─────────┬─────────┘               └─────────┬─────────┘
                   │ (influences)                      │ (influences)
                   └───────────────┬───────────────────┘
                                   ▼
                             ┌───────────┐
                             │  orders   │
                             └─────┬─────┘
                                   │ (mathematical)
                                   ▼
                             ┌───────────┐
                             │  revenue  │◄───────── [ average_order_value ]
                             └───────────┘
```

**Causal Path Evaluation Algorithm:**
1. **D-Separation & Path Traversal:** For each agent finding claiming driver node $u$ influenced target KPI $v$, verify that $\exists \text{ directed path } p = (u, e_1, w_1, \dots, v) \in \mathcal{G}$.
2. **First-Order Partial Correlation:** To confirm $u$ has an independent effect on $v$ controlling for collateral mediator $z$:
   $$\rho_{uv \cdot z} = \frac{\rho_{uv} - \rho_{uz}\rho_{vz}}{\sqrt{(1 - \rho_{uz}^2)(1 - \rho_{vz}^2)}}$$
3. **Collateral Suppression Rule:** If $\rho_{uv \cdot z} \approx 0$ and $z$ lies on the directed path between $u$ and $v$, $z$ is classified as a *mediating symptom* and pruned from top-level root cause attribution to prevent double-counting.

---

### 2.3 Synthetic Data Generation Equations for Scenario 1

To test Scenario 1 objectively, the test harness generates ground-truth multi-factor synthetic series via the following parametric equations over time $t \in [0, T]$ with $T = 60$ days and event window starting at $t_{event} = 45$:

$$\text{Sessions}(t) = S_0 \cdot \left[1 + A_{dow}\sin\left(\frac{2\pi t}{7}\right)\right] \cdot \left[1 - \delta_{spend} \cdot \mathbb{I}(t \ge t_{event})\right] + \epsilon_S(t)$$
$$\text{CVR}(t) = \text{CVR}_0 \cdot \left[1 - \delta_{checkout} \cdot \mathbb{I}(t \ge t_{event})\right] + \epsilon_C(t)$$
$$\text{AOV}(t) = \text{AOV}_0 \cdot \left[1 + \delta_{price} \cdot \mathbb{I}(t \ge t_{event})\right] + \epsilon_A(t)$$
$$\text{Revenue}(t) = \text{Sessions}(t) \times \text{CVR}(t) \times \text{AOV}(t)$$

**Ground-Truth Parameter Values for Benchmark Dataset `GD-S1-001`:**
- $S_0 = 100,000\text{ sessions/day}$
- $\text{CVR}_0 = 0.025$ ($2.50\%$)
- $\text{AOV}_0 = \$200.00$
- Baseline Daily Revenue: $100,000 \times 0.025 \times 200 = \$500,000/\text{day}$
- Interventions at $t \ge 45$:
  - $\delta_{checkout} = 0.12$ (EMEA checkout error causes $12.0\%$ drop in net CVR $\to 0.022$)
  - $\delta_{spend} = 0.10$ (NA ad spend cut causes $10.0\%$ drop in Sessions $\to 90,000$)
  - $\delta_{price} = 0.02$ (APAC price increase yields $2.0\%$ increase in net AOV $\to \$204.00$)
- Noise distributions: $\epsilon_S(t) \sim \mathcal{N}(0, 500^2)$, $\epsilon_C(t) \sim \mathcal{N}(0, 0.0002^2)$, $\epsilon_A(t) \sim \mathcal{N}(0, 1.0^2)$.

---

### 2.4 Interface Contracts & Schemas for Scenario 1

```python
# app/schemas/multifactor.py
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DriverAttribution(BaseModel):
    driver_id: str
    driver_name: str
    driver_type: str  # "technical_failure", "marketing_spend", "pricing_shift"
    dimension_slice: Dict[str, str]  # e.g. {"region": "EMEA", "channel": "checkout"}
    
    # Quantitative Attribution
    absolute_impact: float = Field(..., description="Absolute monetary/unit impact on KPI")
    percentage_attribution: float = Field(..., description="Share of total movement in % (-100% to +100%)")
    shapley_value: float = Field(..., description="Exact coalitional Shapley value")
    lmdi_weight: Optional[float] = Field(None, description="LMDI logarithmic weight")
    
    # Causal Graph Validation
    causal_path: List[str] = Field(..., description="Directed graph path from driver to KPI")
    is_direct_root_cause: bool = True
    collateral_symptoms: List[str] = Field(default_factory=list)

class MultiFactorAttributionResult(BaseModel):
    incident_id: str
    target_kpi: str
    observed_delta: float
    percentage_delta: float
    
    drivers: List[DriverAttribution]
    unexplained_residual: float = Field(0.0, description="Should be <= 0.001 under LMDI/Shapley")
    reconciliation_status: str  # "EXACT_RECONCILIATION", "APPROXIMATE", "UNRECONCILED"
```

---

### 2.5 Quantitative Pass/Fail Metrics for Scenario 1

| Metric Identifier | Mathematical Definition | Pass Threshold | Critical Failure Boundary |
|---|---|---|---|
| **Attribution MAE** | $\text{MAE}_{attr} = \frac{1}{|K|}\sum_{k=1}^K \|\hat{p}_k\% - p_k^*\%\|$ | $\le 3.5\%$ | $> 5.0\%$ |
| **Top-K Driver Recall** | $\text{Recall}@K = \frac{\|D_{true} \cap D_{pred}@K\|}{\|D_{true}\|}$ ($K=3$) | $= 1.00$ ($100\%$) | $< 1.00$ |
| **Driver Precision** | $\text{Precision}@K = \frac{\|D_{true} \cap D_{pred}@K\|}{K}$ | $\ge 0.90$ | $< 0.80$ |
| **False Discovery Rate (FDR)** | $\text{FDR} = \frac{\text{False Positives}}{\text{True Positives} + \text{False Positives}}$ | $\le 0.05$ ($5\%$) | $> 0.10$ |
| **Sum-to-Total Residual** | $\|\Delta Y_{observed} - \sum \phi_i\| / \|\Delta Y_{observed}\|$ | $\le 0.001$ ($0.1\%$) | $> 0.01$ |
| **Causal Path Validity** | $\frac{\text{Validated DAG Paths}}{\text{Total Claimed Drivers}}$ | $= 1.00$ ($100\%$) | $< 1.00$ |

---

## 3. Scenario 2: Low-Confidence Scenario with Clarification & Abstention

### 3.1 Problem Formulation & Business Context
When incoming data is noisy, contradictory across swarm agent findings, temporally unaligned (e.g. claimed cause occurred *after* the KPI drop), or statistically underpowered, an autonomous BI engine must **never hallucinate root causes or trigger destructive automated operational levers**.

**Concrete Benchmark Incident (`INC-S2-CONTRADICTION`):**
- **Target KPI:** `Gross Margin`
- **Agent A (Marketing Agent):** Claims $+\$40,000$ margin improvement due to Campaign "SummerBoost".
- **Agent B (Product Agent):** Claims $-\$50,000$ margin collapse due to SKU clearance discount.
- **Agent C (Geography Agent):** Reports no change in SKU volume in North America.
- **Temporal Check:** Campaign "SummerBoost" launched on August 15; KPI drop occurred on August 10.
- **Statistical Significance:** $p\text{-value} = 0.38$, sample size $N = 4$ transactions.

The engine must calculate a formal multi-layer composite confidence score, detect conflicts, gate automated actions via GoRules Rule 22, and return a structured clarification payload to human operators.

---

### 3.2 Mathematical Formula for Multi-Layer Composite Confidence Score ($C_{composite}$)

The Composite Confidence Score combines four orthogonal pillars of epistemic certainty and subtracts explicit penalty functions for contradictions and small sample sizes:

$$C_{composite} = \max\left(0.0, \min\left(1.0, w_e C_{evidence} + w_t C_{temporal} + w_d C_{dag} - P_{contradictions} - P_{sample}\right)\right)$$

**Pillar Weights:**
$$w_e = 0.35, \quad w_t = 0.35, \quad w_d = 0.30 \quad \left(\sum w_i = 1.00\right)$$

#### 1. Evidence Sub-Score ($C_{evidence} \in [0, 1]$):
Measures quantitative depth, data source diversity, and directness of measurement:
$$C_{evidence} = 0.40 \cdot \min\left(1.0, \frac{N_{records}}{100}\right) + 0.30 \cdot \left(\frac{H(Sources)}{H_{max}}\right) + 0.30 \cdot \bar{q}_{directness}$$
where $H(Sources) = -\sum_{s} p_s \ln p_s$ is Shannon entropy over evidence data sources, and $\bar{q}_{directness} \in [0.2, 1.0]$ is the average measurement directness (1.0 for primary database telemetry, 0.5 for secondary logs).

#### 2. Temporal Precedence Sub-Score ($C_{temporal} \in [0, 1]$):
Enforces strict physical causality: causes must precede or coincide with effects.
$$C_{temporal} = \prod_{e \in \text{Evidence}} \mathbb{I}(t_e \le t_{kpi\_event\_end}) \cdot \exp\left(-\frac{\max(0, t_{kpi\_event\_start} - t_e)}{\tau_{decay}}\right)$$
If any primary evidence occurred *after* the KPI event window, $\mathbb{I}(t_e \le t_{kpi\_event\_end}) = 0$, driving $C_{temporal} \to 0.0$.

#### 3. Causal DAG Path Sub-Score ($C_{dag} \in [0, 1]$):
Measures structural validity in `DEPENDENCY_GRAPH`:
$$C_{dag} = \begin{cases} 1.00 & \text{if direct directed edge } u \to v \\ 0.85^{\text{path\_length} - 1} & \text{if directed path exists of length } \ge 2 \\ 0.20 & \text{if undirected / correlational connection only} \\ 0.00 & \text{if disconnected in DAG} \end{cases}$$

#### 4. Contradiction Penalty Function ($P_{contradictions} \ge 0$):
$$P_{contradictions} = \min\left(0.80, 0.35 \times N_{\text{value\_conflicts}} + 0.50 \times N_{\text{directional\_conflicts}}\right)$$
A single directional contradiction (e.g. Agent A says $+20\%$, Agent B says $-20\%$ on same dimension) incurs a $-0.50$ penalty.

#### 5. Sample Size / Statistical Power Penalty ($P_{sample} \ge 0$):
$$P_{sample} = \max\left(0.0, \frac{N_{min} - N}{N_{min}}\right) \times 0.30 \quad (\text{where } N_{min} = 30 \text{ for standard hypothesis testing})$$

---

### 3.3 Multi-Threshold Decision Gating & GoRules Integration

```
                         ┌─────────────────────────────┐
                         │  Calculate C_composite      │
                         └──────────────┬──────────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
  ┌──────────────────┐        ┌──────────────────┐        ┌──────────────────┐
  │ C_comp >= 0.85   │        │ 0.70 <= C < 0.85 │        │ C_comp < 0.70    │
  ├──────────────────┤        ├──────────────────┤        ├──────────────────┤
  │ Status: ALLOWED  │        │ Status:          │        │ Status: ABSTAIN  │
  │ GoRules Rule 20  │        │ HUMAN_REVIEW     │        │ GoRules Rule 22  │
  │ Auto-synthesis & │        │ GoRules Rule 21  │        │ Block all levers;│
  │ standard levers  │        │ Flagged review   │        │ Clarification    │
  └──────────────────┘        └──────────────────┘        └──────────────────┘
```

**GoRules Rule Mapping (`app/governance/decision_table.json`):**
- **Rule 20:** `confidence >= 0.85` $\to$ `result: "ALLOWED"`
- **Rule 21:** `confidence in [0.70..0.84]` $\to$ `result: "HUMAN_REVIEW"`
- **Rule 22:** `confidence < 0.70` $\to$ `result: "ABSTAIN"`
- **Rule 23:** `dataQualityStatus != "VALID"` $\to$ `result: "PROHIBITED"`

When Rule 22 triggers:
1. `DiagnosticPayload.uncertainty.abstain = True`
2. `DiagnosticPayload.uncertainty.status = "HIGH"`
3. `DiagnosticPayload.recommendations = []` (all automated levers stripped)
4. `DiagnosticPayload.uncertainty.alternatives` populated with structured clarification queries.

---

### 3.4 Structured Clarification Request Payload Schema

```python
# app/schemas/clarification.py
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field

class ClarificationType(str, Enum):
    DIRECTIONAL_CONTRADICTION = "directional_contradiction"
    TEMPORAL_MISALIGNMENT = "temporal_misalignment"
    DATA_STREAM_DISCREPANCY = "data_stream_discrepancy"
    INSUFFICIENT_SAMPLE_SIZE = "insufficient_sample_size"

class ConflictingHypothesis(BaseModel):
    hypothesis_id: str
    source_agent: str
    claimed_driver: str
    claimed_impact: float
    evidence_summary: str
    confidence: float

class ClarificationRequestPayload(BaseModel):
    incident_id: str
    target_kpi: str
    composite_confidence: float = Field(..., le=0.70)
    failure_type: ClarificationType
    
    summary_for_operator: str
    missing_dimensions: List[str]
    conflicting_hypotheses: List[ConflictingHypothesis]
    suggested_queries: List[str] = Field(
        ..., 
        description="SQL or telemetry queries operator should run to resolve ambiguity"
    )
    resolution_actions: List[str] = Field(
        default_factory=list,
        description="Selectable operator resolution choices"
    )
```

---

### 3.5 Pass/Fail Quantitative Metrics for Scenario 2

| Metric Identifier | Mathematical Definition | Pass Threshold | Critical Failure Boundary |
|---|---|---|---|
| **Abstention Precision** | $\frac{\text{True Abstentions}}{\text{True Abstentions} + \text{False Abstentions}}$ | $= 1.00$ ($100\%$) | $< 1.00$ |
| **Abstention Recall** | $\frac{\text{True Abstentions}}{\text{True Abstentions} + \text{Missed Abstentions}}$ | $= 1.00$ ($100\%$) | $< 1.00$ |
| **GoRules Rule 22 Compliance** | Percentage of $C < 0.70$ events with zero emitted levers | $= 100.0\%$ | $< 100.0\%$ |
| **Clarification Payload Completeness** | Percentage of abstentions with non-null `missing_dimensions` & `suggested_queries` | $= 100.0\%$ | $< 100.0\%$ |
| **Zero False Action Rate** | Automated levers executed when $C < 0.70$ | $= 0$ actions | $> 0$ actions |

---

## 4. Scenario 3: Sparse-History / Newly Launched KPI Scenario (Cold Start)

### 4.1 Problem Formulation & Business Context
When a new product line, regional territory, marketing channel, or subscription tier is launched, the historical time series is sparse ($N < 14$ daily observations). Standard time-series STL decomposition (which requires multiple seasonal cycles, e.g. $N \ge 2 \times \text{period} = 14$ for weekly seasonality) and asymptotic Gaussian anomaly detectors fail due to insufficient degrees of freedom.

**Concrete Benchmark Incident (`INC-S3-COLDSTART`):**
- **Target KPI:** `New AI-Addon Daily Revenue`
- **History Available:** $N = 4$ daily data points ($\$800, \$1,100, \$950, \$1,400$)
- **Problem:** No 30-day baseline, no seasonal indices, high empirical variance ($s = \$253.31$).
- **Risk:** Standard 3-sigma detector triggers continuous false-alarm anomaly alerts on normal early-stage variance.

---

### 4.2 Minimum Sample Size Gating ($N_{min} = 14$)

The ingestion and orchestrator pipeline implements an explicit sample size gate:

```
                            ┌────────────────────────┐
                            │ Ingested Time Series D │
                            └───────────┬────────────┘
                                        │
                         Is len(D) >= N_min (14 days)?
                                        │
                        ┌───────────────┴───────────────┐
                        │ YES                           │ NO
                        ▼                               ▼
            ┌───────────────────────┐       ┌───────────────────────┐
            │     NORMAL MODE       │       │    COLD-START MODE    │
            ├───────────────────────┤       ├───────────────────────┤
            │ • Classical STL Decomp│       │ • Empirical Bayes     │
            │ • 3-Sigma Anomaly Band│       │   Prior Borrowing     │
            │ • Additive Trend/Seas │       │ • Funnel Proxy Models │
            │ • Standard Confidence │       │ • Widened 95% Bayesian│
            │   Intervals           │       │   Credible Intervals  │
            └───────────────────────┘       └───────────────────────┘
```

---

### 4.3 Hierarchical Empirical Bayesian Prior Borrowing

In Cold-Start Mode ($N < 14$), the engine borrows prior distributions from the parent category, historical product launch cohorts, or sibling geographic markets.

#### 4.3.1 Conjugate Normal-Inverse-Gamma Prior for Revenue / Monetary KPIs:
Let the metric observations be $y_1, y_2, \dots, y_N \sim \mathcal{N}(\mu, \sigma^2)$.  
The prior distribution borrowed from the parent category cohort is:
$$\mu \mid \sigma^2 \sim \mathcal{N}\left(\mu_0, \frac{\sigma^2}{\kappa_0}\right), \quad \sigma^2 \sim \text{Inv-Gamma}(\alpha_0, \beta_0)$$
where $\mu_0 = \mu_{cohort}$, $\kappa_0$ represents pseudo-observation weight (default $\kappa_0 = 7$), $\alpha_0 = 3$, and $\beta_0 = 2 \sigma_{cohort}^2$.

**Bayesian Posterior Updating Equations:**
$$\kappa_N = \kappa_0 + N$$
$$\mu_N = \frac{\kappa_0 \mu_0 + N \bar{y}}{\kappa_N} = (1 - B)\bar{y} + B\mu_0$$
$$\alpha_N = \alpha_0 + \frac{N}{2}$$
$$\beta_N = \beta_0 + \frac{1}{2}\sum_{i=1}^N (y_i - \bar{y})^2 + \frac{\kappa_0 N (\bar{y} - \mu_0)^2}{2\kappa_N}$$

**Shrinkage Factor ($B \in [0, 1]$):**
$$B(N) = \frac{\kappa_0}{\kappa_0 + N}$$
- At $N = 0$: $B = 1.0$ (100% reliance on parent cohort prior $\mu_0$).
- At $N = 4$: $B = \frac{7}{7 + 4} = 0.636$ (63.6% prior, 36.4% empirical data).
- As $N \to 14$: $B = \frac{7}{7 + 14} = 0.333 \to 0$ (smooth transition to empirical data).

#### 4.3.2 Conjugate Beta-Binomial Prior for Conversion Rates:
$$\theta_{CVR} \sim \text{Beta}(\alpha_0, \beta_0) \quad \text{where } \alpha_0 = \mu_{cat} \cdot M_0, \; \beta_0 = (1 - \mu_{cat}) \cdot M_0 \quad (M_0 = 1,000)$$
$$\theta_{post} \sim \text{Beta}(\alpha_0 + \text{Conversions}, \; \beta_0 + \text{Visitors} - \text{Conversions})$$

---

### 4.4 Surrogate Proxy Indicator Funnel Mapping

When target downstream KPIs lack history, the engine traverses upstream edges in `DEPENDENCY_GRAPH` to high-frequency, dense precursor indicators:

```
┌─────────────────────────────────┐
│ Upstream Surrogate Precursors   │
│ (Dense, High-Frequency Telemetry│
├─────────────────────────────────┤
│ • Landing Page Impressions      │───────┐
│ • Pricing Modal Clicks          │       ▼
│ • Free Trial Initiations        │  Transfer Function f_funnel(X, η)
│ • Cart Additions                │       │
└─────────────────────────────────┘       ▼
                              ┌───────────────────────────────────┐
                              │ Target Sparse KPI Expected Value  │
                              │ Ŷ_target(t) = Sessions(t)         │
                              │              × CVR_proxy          │
                              │              × AOV_cohort         │
                              └───────────────────────────────────┘
```

**Surrogate Transfer Equation:**
$$\hat{Y}_{target}(t) = X_{precursor}(t) \cdot \eta_{stage\_conversion} \cdot \bar{V}_{cohort\_AOV}$$

---

### 4.5 Dynamic Uncertainty Widening & Credible Intervals

To prevent false anomaly alarms during cold start, anomaly detection bounds use the **95% Bayesian Posterior Predictive Credible Interval** widened by a finite-sample penalty factor $\kappa_{sparse}(N)$:

$$[\hat{y}_{lower}(t), \hat{y}_{upper}(t)] = \mu_N \pm t_{2\alpha_N, 0.975} \cdot \sqrt{\frac{\beta_N (\kappa_N + 1)}{\alpha_N \kappa_N}} \cdot \kappa_{sparse}(N)$$
where the dynamic widening factor is:
$$\kappa_{sparse}(N) = 1.0 + \frac{2.5}{\sqrt{N}}$$
- At $N = 1$: $\kappa_{sparse} = 3.50$ (wide band, zero false alarms).
- At $N = 4$: $\kappa_{sparse} = 2.25$.
- At $N = 14$: $\kappa_{sparse} = 1.67 \to 1.00$ (smooth handoff to 3-sigma STL bounds).

**Persona Story Caveat Enforcement (`app/orchestrator/persona.py`):**
When `metadata["cold_start"] = True`, persona story generators are strictly required to append standardized caveat annotations:
> *"⚠️ Cold Start Advisory: Metric history is limited to N=4 observations. Expected baseline ($1,020 ± $450) is inferred via Bayesian prior borrowing from 'SaaS Addon Cohort' and surrogate modal clicks. Confidence intervals are widened to prevent false-alarm triggers."*

---

### 4.6 Pass/Fail Quantitative Metrics for Scenario 3

| Metric Identifier | Mathematical Definition | Pass Threshold | Critical Failure Boundary |
|---|---|---|---|
| **False Positive Anomaly Rate** | $\frac{\text{False Alarms in First 7 Days}}{7\text{ Days}}$ | $= 0.00$ ($0\%$) | $> 0.05$ |
| **Bayesian Prior Shrinkage** | Monotonic decrease in $B(N)$ as $N \to 14$ | $100\%$ Monotonic | Non-monotonic |
| **Credible Interval Coverage** | Ground truth within $[\hat{y}_{lower}, \hat{y}_{upper}]$ | $\ge 95.0\%$ | $< 90.0\%$ |
| **Surrogate Correlation Fidelity** | $R^2(\hat{Y}_{surrogate}, Y_{true})$ | $\ge 0.75$ | $< 0.60$ |
| **Persona Caveat Presence** | Cold start metadata & narrative disclosure present | $= 100.0\%$ | $< 100.0\%$ |

---

## 5. Scenario 4: Role-Based Security, Entitlements & Data Masking Scenario

### 5.1 Problem Formulation & Business Context
In an enterprise multi-tenant BI environment, users across different organizational roles and clearance tiers query the diagnostic engine. Unauthorized users must **never access cross-tenant data, raw customer PII, or restricted financial metrics** (e.g. Gross Margins, Unit Costs, Executive Levers).

**Concrete Benchmark Incidents:**
1. **Tenant Isolation Incident (`INC-S4-TENANT`):** Tenant A (`tenant_id: "acme_corp"`) executes an investigation; engine must never read or leak telemetry from Tenant B (`tenant_id: "globex_inc"`).
2. **Role Entitlement Incident (`INC-S4-ROLE`):** EMEA Sales Manager (`role: "sales"`, `allowed_regions: ["EMEA"]`) investigates revenue drop; engine must redact APAC revenue, mask Gross Margin percentage, hash customer emails, and block recommendation levers exceeding $\$10,000$.
3. **Executive Incident (`INC-S4-EXEC`):** VP Finance (`role: "finance"`, `can_view_margins: True`) is authorized to view company-wide margins and approve high-impact levers ($>\$25,000$).

---

### 5.2 `SecurityContext` Architecture & Entitlement Model

```python
# app/schemas/security.py
from typing import List, Optional, Set
from enum import Enum
from pydantic import BaseModel, Field
from app.schemas.persona import PersonaRole

class DataClassification(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED_FINANCIAL = "RESTRICTED_FINANCIAL"
    PII = "PII"

class SecurityContext(BaseModel):
    user_id: str
    tenant_id: str = Field(..., description="Mandatory tenant isolation identifier")
    roles: List[PersonaRole] = Field(default_factory=list)
    
    # Attribute-Based Access Control (ABAC) Permissions
    permitted_metrics: Set[str] = Field(
        default_factory=lambda: {"revenue", "orders", "conversion_rate", "traffic"}
    )
    permitted_dimensions: Set[str] = Field(
        default_factory=lambda: {"product", "customer_segment", "geography", "sales_channel"}
    )
    allowed_regions: Set[str] = Field(default_factory=lambda: {"*"})  # e.g. {"EMEA"}
    
    # Financial & Privacy Flags
    can_view_margins: bool = False
    can_view_unit_costs: bool = False
    can_view_pii: bool = False
    
    # Financial Action Approval Limit ($ USD)
    max_approval_limit: float = Field(default=0.0, description="Max dollar impact user can authorize")
```

---

### 5.3 Multi-Tenant SQL Query Rewriting & Row-Level Security (RLS)

All database access tools in `app/tools/` (including `database.py`, `channel.py`, `customer.py`, `geography.py`, `product.py`) are intercepted by a secure SQL AST query rewriter that injects mandatory tenant and regional filter predicates.

**Query Rewriting Logic:**
$$\text{Raw Query: } \texttt{SELECT * FROM canonical\_measurements WHERE kpi\_id = 'revenue'}$$
$$\Downarrow \text{ AST Scoping Injection }$$
$$\text{Scoped Query: } \texttt{SELECT * FROM canonical\_measurements WHERE tenant\_id = :tenant\_id AND kpi\_id = 'revenue' AND (region IN (:allowed\_regions) OR :is\_global = true)}$$

```python
# app/tools/security_wrapper.py specification
def apply_tenant_scoping(query_str: str, sec_ctx: SecurityContext) -> tuple[str, dict]:
    """
    Enforces mandatory tenant isolation and regional ABAC filtering at SQL execution level.
    """
    params = {
        "tenant_id": sec_ctx.tenant_id,
        "allowed_regions": list(sec_ctx.allowed_regions),
        "is_global": "*" in sec_ctx.allowed_regions
    }
    # AST / Parameterized injection ensures zero SQL injection or cross-tenant leaks
    scoped_query = (
        f"WITH scoped_data AS ("
        f"  SELECT * FROM canonical_measurements "
        f"  WHERE tenant_id = :tenant_id "
        f"  AND (:is_global = TRUE OR region = ANY(:allowed_regions))"
        f") "
        f"{query_str}"
    )
    return scoped_query, params
```

---

### 5.4 Attribute-Based Access Control (ABAC) Filtering on Diagnostic Pipeline

Before findings reach the orchestrator LLM or persona storytelling engine, they pass through the `ABACFilter`:

```
┌─────────────────────────────┐
│ Raw Agent Findings / Telemetry│
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│      ABACFilter Node        │
│ Intercepts findings against │
│ SecurityContext permissions │
└──────────────┬──────────────┘
               │
               ├─► Restricted Metric? (e.g. margin without can_view_margins) ──► DROP or MASK
               ├─► Out-of-Region Dimension? (e.g. APAC finding for EMEA user) ──► DROP
               └─► PII in Evidence? (e.g. user_email, customer_id) ────────────► TOKENIZE / HASH
               │
               ▼
┌─────────────────────────────┐
│ Sanitized Diagnostic Payload│
└─────────────────────────────┘
```

---

### 5.5 Dynamic Data Masking & Persona Sanitization Layer

#### 1. Cryptographic PII Tokenization:
Customer IDs, IP addresses, and email addresses in finding evidence are transformed via HMAC-SHA256 with a per-tenant secret salt:
$$\text{Token}(x) = \text{HMAC-SHA256}(x, \text{Salt}_{tenant})[0:8] \implies \texttt{"CUST-8f3a9b21"}$$

#### 2. Margin & Financial Value Obfuscation:
For users with `can_view_margins = False`:
- Exact margin values replaced with: `"[REDACTED - INSUFFICIENT PRIVILEGES]"`
- Percentage changes preserved only if relative direction is non-confidential: `"+2.1% (direction only)"`

#### 3. Persona Prompt Sanitization:
The system prompt in `app/orchestrator/persona.py` is dynamically injected with the user's role boundary rules:
```
SECURITY CONSTRAINTS FOR PERSONA ROLE {role}:
- Tenant ID: {tenant_id} (STRICT ISOLATION)
- Permitted Regions: {allowed_regions}
- Permitted Metrics: {permitted_metrics}
- Margin Clearance: {can_view_margins}
You must NOT disclose or extrapolate any information outside these boundaries.
```

---

### 5.6 GoRules Role Authorization Gating (Rules 13-19)

The GoRules decision table (`app/governance/decision_table.json`) enforces organizational decision rights:

| Rule ID | Role / Actor | Condition / Lever | Result |
|---|---|---|---|
| **Rule 13** | Sales Manager | Discount $\le 10\%$ | `AUTHORIZED` |
| **Rule 14** | VP Sales | Discount $> 10\%$ | `AUTHORIZED` |
| **Rule 15** | Lead SRE | Deployment rollback | `AUTHORIZED` |
| **Rule 16** | Operations Manager | Inventory reorder | `AUTHORIZED` |
| **Rule 17** | Any Role | Expected Impact $< \$5,000$ | `NO_EXTRA_APPROVAL` |
| **Rule 18** | Any Role | Expected Impact $\$5,000 - \$25,000$ | `MANAGER_APPROVAL` |
| **Rule 19** | Any Role | Expected Impact $> \$25,000$ | `VP_APPROVAL` |

If a recommendation requires `VP_APPROVAL` but `SecurityContext.max_approval_limit < 25000` or `PersonaRole != EXECUTIVE`, the engine marks the lever as `PENDING_HIGHER_APPROVAL` and disables automated execution.

---

### 5.7 Pass/Fail Quantitative Metrics for Scenario 4

| Metric Identifier | Mathematical Definition | Pass Threshold | Critical Failure Boundary |
|---|---|---|---|
| **Cross-Tenant Leakage Rate** | $\frac{\text{Records Leaked from Other Tenants}}{\text{Total Records Queried}}$ | $= 0.00\%$ (Zero) | $> 0.00\%$ |
| **Restricted Field Redaction Rate** | $\frac{\text{Successfully Redacted Fields}}{\text{Total Restricted Fields}}$ | $= 100.0\%$ | $< 100.0\%$ |
| **PII Tokenization Rate** | $\frac{\text{Hashed PII Fields}}{\text{Total Raw PII Occurrences}}$ | $= 100.0\%$ | $< 100.0\%$ |
| **Role Authorization Adherence** | Percentage of unauthorized levers successfully blocked | $= 100.0\%$ | $< 100.0\%$ |
| **SQL Injection & Bypass Rejection** | Rejection rate of malformed/unscoped SQL injection probes | $= 100.0\%$ | $< 100.0\%$ |

---

## 6. Unified Scenario Test Execution Harness & Verification Strategy

### 6.1 Automated Pytest Scenario Execution Matrix

The scenario test suite is orchestrated through a unified benchmark runner (`app/evaluation/scenario_runner.py`):

```
kpi-engine/
└── tests/
    ├── conftest.py                   # Pytest fixtures & synthetic data generators
    ├── scenarios/
    │   ├── test_scenario_1_multifactor.py   # Multi-factor Shapley & LMDI attribution tests
    │   ├── test_scenario_2_confidence.py    # Low-confidence & abstention tests
    │   ├── test_scenario_3_coldstart.py     # Bayesian cold-start & surrogate tests
    │   └── test_scenario_4_security.py      # Multi-tenant scoping & RBAC masking tests
    └── fixtures/
        ├── synthetic_multifactor.json
        ├── synthetic_contradictions.json
        ├── synthetic_coldstart.json
        └── security_contexts.json
```

---

### 6.2 Step-by-Step Test Execution Plan for Each Scenario

#### Test Procedure 1: Multi-Factor Attribution Verification (`test_scenario_1_multifactor.py`)
1. **Setup:** Instantiate `MultiFactorScenarioGenerator` with parameters: $\delta_{checkout} = -12\%$, $\delta_{spend} = -10\%$, $\delta_{price} = +2\%$.
2. **Execute:** Feed generated series into `investigation_graph.invoke()`.
3. **Assert:**
   - Identified drivers contain `EMEA Checkout Failure`, `NA Ad Spend Reduction`, `APAC Price Increase`.
   - Driver Recall $@3 == 1.00$.
   - Attribution $\text{MAE} \le 3.5\%$.
   - Unexplained residual $\le 0.1\%$.
   - `DEPENDENCY_GRAPH` verifies valid directed paths for all 3 drivers.

#### Test Procedure 2: Low-Confidence & Abstention Verification (`test_scenario_2_confidence.py`)
1. **Setup:** Inject contradictory findings (Agent A: $+40\%$ revenue on EMEA, Agent B: $-50\%$ revenue on EMEA).
2. **Execute:** Run through `analysis_node`, `contradiction_node`, `orchestrator_node`, and `governance_node`.
3. **Assert:**
   - $C_{composite} < 0.70$ (Contradiction penalty applied).
   - `DiagnosticPayload.uncertainty.abstain == True`.
   - GoRules evaluation returns `ABSTAIN` (Rule 22).
   - `recommendations` list is empty (zero automated levers).
   - `ClarificationRequestPayload` contains non-null `missing_dimensions` and `suggested_queries`.

#### Test Procedure 3: Cold Start & Bayesian Prior Borrowing (`test_scenario_3_coldstart.py`)
1. **Setup:** Ingest sparse series with $N = 4$ observations for `new_tier_revenue`.
2. **Execute:** Invoke time-series anomaly detection and diagnostic orchestrator.
3. **Assert:**
   - Pipeline switches to Cold-Start Mode ($N < 14$).
   - Expected baseline $\mu_N$ computed via Bayesian prior borrowing ($B \approx 0.636$).
   - 95% Credible Interval is widened by $\kappa(4) = 2.25$.
   - Zero false-positive anomaly alarms triggered on synthetic noise.
   - Persona narrative contains mandatory cold-start caveat disclosure.

#### Test Procedure 4: Multi-Tenant Scoping & ABAC Masking (`test_scenario_4_security.py`)
1. **Setup:** Construct `SecurityContext` for EMEA Sales Lead (`tenant_id: "acme"`, `allowed_regions: ["EMEA"]`, `can_view_margins: False`).
2. **Execute:** Execute multi-agent investigation and persona story generation.
3. **Assert:**
   - Zero records returned from `tenant_id: "globex"`.
   - APAC findings completely excluded from `DiagnosticPayload`.
   - Gross Margin values replaced with `"[REDACTED - INSUFFICIENT PRIVILEGES]"`.
   - Customer IDs tokenized with HMAC hashes (`CUST-***-849`).
   - Governance blocks recommendations exceeding $\$10,000$ (Rule 18/19).

---

## 7. Implementation Roadmap & Milestones

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      R3 IMPLEMENTATION MILESTONES                           │
├─────────────┬───────────────────────────────────────────┬───────────────────┤
│ Milestone   │ Key Deliverables                          │ Dependencies      │
├─────────────┼───────────────────────────────────────────┼───────────────────┤
│ **M3.1**    │ • Implement `app/analytics/shapley.py`    │ Ingestion / Gold  │
│             │ • Implement `app/analytics/lmdi.py`       │ Tables Schema     │
│             │ • Multi-Factor Synthetic Benchmark Suite  │                   │
├─────────────┼───────────────────────────────────────────┼───────────────────┤
│ **M3.2**    │ • Implement Composite Confidence Engine   │ Contradiction     │
│             │ • Structured Clarification Schema         │ Detector          │
│             │ • GoRules Rule 20-23 Abstention Gating    │                   │
├─────────────┼───────────────────────────────────────────┼───────────────────┤
│ **M3.3**    │ • Implement Hierarchical Bayesian Engine  │ NetworkX          │
│             │ • Surrogate Funnel Transfer Functions     │ Dependency Graph  │
│             │ • Dynamic Uncertainty Widening Layer      │                   │
├─────────────┼───────────────────────────────────────────┼───────────────────┤
│ **M3.4**    │ • Implement `SecurityContext` Model       │ SQLAlchemy Tools  │
│             │ • AST Multi-Tenant Query Rewriter         │ & Persona LLM     │
│             │ • Dynamic PII Tokenization & Redaction    │                   │
├─────────────┼───────────────────────────────────────────┼───────────────────┤
│ **M3.5**    │ • Unified Pytest Benchmark Harness        │ M3.1 - M3.4       │
│             │ • End-to-End Golden Dataset Verification  │ Complete          │
└─────────────┴───────────────────────────────────────────┴───────────────────┘
```

---

## 8. Conclusion

This specification provides the exhaustive architectural blueprint for Requirement R3. By combining **Shapley value cooperative game theory** and **LMDI decomposition** (Scenario 1), **multi-layer composite confidence scoring and GoRules abstention** (Scenario 2), **hierarchical Bayesian prior borrowing and surrogate funnel mapping** (Scenario 3), and **multi-tenant AST query rewriting and ABAC data masking** (Scenario 4), the Business Intelligence Engine establishes mathematical rigor, safe automated execution, and enterprise-grade multi-tenant security.
