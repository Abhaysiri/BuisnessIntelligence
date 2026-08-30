# Research Report: Orchestrator Completion & STL Decomposition (R2)

**Author**: Explorer 2 (Orchestrator & Time-Series Algorithm Specialist)  
**Date**: 2026-08-30  
**Scope**: Requirement R2 — Orchestrator Completion (specifically STL Decomposition - Seasonal and Trend decomposition using Loess, excluding contextual debouncing)  
**Target Repository**: `BuisnessIntelligence.ai` / `kpi-engine`

---

## 1. Executive Summary & High-Level Findings

The current `kpi-engine` implementation possesses an agent swarm orchestration pipeline built using **LangGraph** (`kpi-engine/app/orchestrator/graph.py`), deterministic analytics modules (`app/analytics/`), and a **ZenEngine / GoRules** decision table (`app/governance/`). However, the engine currently begins execution *downstream* of an already synthesized `KPIMovementEvent`.

There is currently **zero automated time-series decomposition or statistical baseline detection** in the repository:
1. **Missing Upstream Baseline & Anomaly Detection**: The orchestrator expects pre-computed `observed_value`, `expected_value`, `percentage_change`, and `statistical_score`, but has no statistical time-series engine to derive expected values or evaluate whether an observed movement is statistically significant.
2. **Missing Time-Series Mathematics Dependencies**: `requirements.txt` lacks `statsmodels`, `scipy`, `numpy`, `pandas`, and `polars`.
3. **Empty Time-Series Stubs**: `app/tools/kpi.py` is an empty 0-byte file.
4. **Visualizer Trend Gap**: `frontend/Visualizers/api/main.py` requires `metadata.trend_data` containing `[timestamp, actual_value, expected_value, lower_bound, upper_bound]`, which is currently provided only via synthetic hardcoded mocks in tests.

To complete the orchestrator per Requirement R2, an **STL (Seasonal and Trend decomposition using Loess)** statistical pipeline must be designed and integrated into the orchestrator workflow prior to multi-agent investigation dispatch.

---

## 2. Current Codebase Inventory & Gap Analysis

### 2.1 Existing Orchestration & Pipeline Components

| Component | File Path | Current Status | Description |
|---|---|---|---|
| **Investigation Graph** | `app/orchestrator/graph.py` | Implemented | LangGraph `StateGraph(InvestigationState)` fanning out across 4 domain agents (`product`, `customer`, `geography`, `channel`), fanning in to `analysis`, followed by `contradictions`, `orchestrator`, and `governance`. |
| **Persona Graph** | `app/orchestrator/persona_graph.py` | Implemented | LangGraph `StateGraph(PersonaState)` generating role-tailored narratives grounded in `DiagnosticPayload`. |
| **Orchestrator Nodes** | `app/orchestrator/nodes.py` | Implemented | Dispatches agent execution, calls analytics verification functions, invokes LLM structured synthesis with deterministic fallback. |
| **Investigation State** | `app/orchestrator/state.py` | Implemented | `TypedDict` containing `movement`, `findings`, `analytical_results`, `contradictions`, `diagnostic_payload`. |
| **Analytics Modules** | `app/analytics/` | Partial | Deterministic heuristic functions: `contribution.py` (arithmetic deltas), `dependency.py` (NetworkX DAG path check), `temporal.py` (timestamp bounds), `evidence.py` (scoring weights), `contradictions.py` (pairwise conflicts). |
| **Governance Engine** | `app/governance/engine.py` | Implemented | ZenEngine runner executing 30 policy rules in `decision_table.json`. |
| **KPI Tools** | `app/tools/kpi.py` | **Missing (0 bytes)** | Placeholder for KPI metric extraction and time-series aggregation. |
| **Visualizers API** | `frontend/Visualizers/api/main.py` | Implemented | Vega-Lite specification generator expecting `metadata.trend_data`. |

### 2.2 Critical Gaps Identified for R2

```
[Missing Upstream Pipeline]
Raw Database Measurements (canonical_measurements)
   ↓
[GAP 1: Time-Series Regularizer & Imputer]
   ↓
[GAP 2: STL Decomposition Engine (Loess)]
   ├── Trend Component T_t
   ├── Seasonal Component S_t
   └── Remainder Component R_t
   ↓
[GAP 3: Dynamic Baseline & Anomaly Evaluator]
   ├── Expected Baseline: Ŷ_t = T_t + S_t
   ├── Residual Uncertainty: σ_R
   ├── Confidence Bounds: [Ŷ_t - z·σ_R, Ŷ_t + z·σ_R]
   └── Anomaly Score: Z_t = (Y_t - Ŷ_t) / σ_R
   ↓
[Automated Trigger: KPIMovementEvent] ──► [Existing LangGraph Swarm Orchestrator]
```

---

## 3. Mathematical & Algorithmic Foundation of STL Decomposition with Loess

STL is a versatile, robust time-series decomposition method developed by Robert B. Cleveland, William S. Cleveland, Jean E. McRae, and Irma Terpenning (1990). It decomposes a continuous time-series $Y_t$ into three additive components:

$$Y_t = T_t + S_t + R_t \quad \text{for } t = 1, \dots, N$$

Where:
- $T_t$ is the **Trend** component (long-term low-frequency progression).
- $S_t$ is the **Seasonal** component (repeating cyclic pattern with period $n_{(p)}$).
- $R_t$ is the **Remainder / Residual** component (irregular noise and unexplained anomalies).

For multiplicative series (e.g. revenue, traffic scaling exponentially or proportionally with season):
$$\ln(Y_t) = T_t + S_t + R_t \iff Y_t = \exp(T_t) \cdot \exp(S_t) \cdot \exp(R_t)$$

---

### 3.1 Mathematical Formulation of LOESS (Locally Estimated Scatterplot Smoothing)

LOESS fits local polynomials to localized subsets of data using weighted least squares. For any evaluation point $x_0$ given sample points $(x_i, y_i)_{i=1}^N$:

#### 1. Neighborhood Selection & Bandwidth
Choose neighborhood window span $q = \max(n_w, \text{int}(\text{span} \cdot N))$. Let $\Delta(x_0)$ be the distance from $x_0$ to the $q$-th nearest neighbor among $\{x_i\}$:
$$\Delta(x_0) = \max_{i \in \mathcal{N}_q(x_0)} |x_i - x_0|$$

#### 2. Tricube Distance Weight Function
The neighborhood proximity weight $W(u)$ is defined by the tricube function:
$$W(u) = \begin{cases} (1 - |u|^3)^3 & \text{for } 0 \le |u| < 1 \\ 0 & \text{for } |u| \ge 1 \end{cases}$$

For each observation point $x_i$:
$$w_i(x_0) = W\left( \frac{|x_i - x_0|}{\Delta(x_0)} \right)$$

#### 3. Combining with Robustness Weights
When outer robustness iteration produces robustness weight $\rho_i \in [0, 1]$:
$$\tilde{w}_i(x_0) = \rho_i \cdot w_i(x_0)$$

#### 4. Local Weighted Polynomial Regression
Fit a polynomial of degree $d \in \{0, 1, 2\}$ (locally linear $d=1$ or locally quadratic $d=2$) minimizing:
$$\min_{\beta_0, \dots, \beta_d} \sum_{i=1}^N \tilde{w}_i(x_0) \left( y_i - \sum_{j=0}^d \beta_j (x_i - x_0)^j \right)^2$$

In matrix form:
$$\mathbf{X}_{x_0} = \begin{bmatrix} 1 & (x_1 - x_0) & \dots & (x_1 - x_0)^d \\ \vdots & \vdots & \ddots & \vdots \\ 1 & (x_N - x_0) & \dots & (x_N - x_0)^d \end{bmatrix}, \quad \mathbf{W}_{x_0} = \text{diag}(\tilde{w}_1(x_0), \dots, \tilde{w}_N(x_0))$$

$$\hat{\boldsymbol{\beta}} = \left( \mathbf{X}_{x_0}^T \mathbf{W}_{x_0} \mathbf{X}_{x_0} \right)^{-1} \mathbf{X}_{x_0}^T \mathbf{W}_{x_0} \mathbf{y}$$

The smoothed estimate at $x_0$ is the intercept:
$$\hat{y}(x_0) = \hat{\beta}_0$$

---

### 3.2 The STL Iterative Two-Loop Procedure

STL operates via two nested loops: an **Outer Loop** that adjusts robustness weights to mitigate outliers, and an **Inner Loop** that iteratively refines the seasonal and trend components.

```
┌─────────────────────────────────────────────────────────────┐
│ Outer Loop (k = 0 to n_(o)): Robustness Weights ρ_t        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Inner Loop (j = 1 to n_(i)):                          │  │
│  │  1. Detrend: Y_t - T_t^(j-1)                          │  │
│  │  2. Cycle-Subseries Loess Smoothing (span n_(s))       │  │
│  │  3. Low-Pass Filter (MA(p) -> MA(p) -> MA(3) -> Loess)│  │
│  │  4. Detrend Seasonal: S_t^(j) = C_t^(j) - L_t^(j)     │  │
│  │  5. Deseasonalize: D_t^(j) = Y_t - S_t^(j)            │  │
│  │  6. Trend Loess Smoothing (span n_(t)) -> T_t^(j)     │  │
│  └───────────────────────────────────────────────────────┘  │
│  7. Compute Residuals: R_t = Y_t - T_t - S_t                │
│  8. Update Robustness Weights ρ_t using Bisquare Function   │
└─────────────────────────────────────────────────────────────┘
```

#### Detailed Step-by-Step Execution:

1. **Initialization**:
   - Set robustness weights $\rho_t = 1$ for all $t = 1, \dots, N$.
   - Set initial trend $T_t^{(0)} = 0$ for all $t = 1, \dots, N$.

2. **Outer Loop** (runs $n_{(o)}$ iterations; on initial pass $k=0$):
   
3. **Inner Loop** (runs $n_{(i)}$ iterations, indexed by $j = 1, \dots, n_{(i)}$):
   - **Step 1: Detrending**:
     $$Y_t - T_t^{(j-1)}$$
   - **Step 2: Cycle-Subseries Smoothing**:
     - Split the detrended series into $n_{(p)}$ subseries (e.g. for weekly period $n_{(p)}=7$, subseries for Mondays, Tuesdays, etc.).
     - Apply LOESS smoothing to each cycle-subseries independently with window length $n_{(s)}$ (degree $d=1$) and weights $\rho_t$.
     - Extrapolate by one period before the start and one period after the end.
     - Concatenate the smoothed subseries in temporal order to form the temporary seasonal series $C_t^{(j)}$ of length $N + 2 n_{(p)}$.
   - **Step 3: Low-Pass Filtering of Smoothed Cycle-Subseries**:
     - Apply a linear 3-stage moving average filter followed by LOESS smoothing to extract any low-frequency trend leaked into the seasonal subseries:
       1. Moving Average of length $n_{(p)}$: $A_t^{(1)} = \frac{1}{n_{(p)}} \sum_{m=-n_{(p)}/2}^{n_{(p)}/2} C_{t+m}^{(j)}$
       2. Moving Average of length $n_{(p)}$: $A_t^{(2)} = \frac{1}{n_{(p)}} \sum_{m=-n_{(p)}/2}^{n_{(p)}/2} A_{t+m}^{(1)}$
       3. Moving Average of length 3: $A_t^{(3)} = \frac{1}{3} (A_{t-1}^{(2)} + A_t^{(2)} + A_{t+1}^{(2)})$
       4. LOESS smoothing on $A_t^{(3)}$ with window length $n_{(l)}$ (degree $d=1$) and weights $\rho_t$.
     - Result is the low-pass filtered series $L_t^{(j)}$ for $t = 1, \dots, N$.
   - **Step 4: Detrending of Smoothed Cycle-Subseries**:
     - Subtract low-frequency leakage to isolate pure seasonality:
       $$S_t^{(j)} = C_t^{(j)} - L_t^{(j)}$$
   - **Step 5: Deseasonalizing**:
     - Subtract seasonal component from original raw series:
       $$D_t^{(j)} = Y_t - S_t^{(j)}$$
   - **Step 6: Trend Smoothing**:
     - Smooth deseasonalized series $D_t^{(j)}$ using LOESS with window length $n_{(t)}$ (degree $d=1$) and weights $\rho_t$.
     - Result is the updated trend component $T_t^{(j)}$.

4. **Outer Loop Residuals & Robustness Weights**:
   - Compute remainder:
     $$R_t = Y_t - T_t^{(n_{(i)})} - S_t^{(n_{(i)})}$$
   - Compute residual scale parameter $h$:
     $$h = 6 \cdot \text{median}(|R_1|, |R_2|, \dots, |R_N|)$$
   - If $h = 0$, set $\rho_t = 1$. Otherwise, compute bisquare robustness weights:
     $$B(u) = \begin{cases} (1 - u^2)^2 & \text{for } 0 \le u < 1 \\ 0 & \text{for } u \ge 1 \end{cases}$$
     $$\rho_t = B\left( \frac{|R_t|}{h} \right)$$
   - Points with extreme residuals ($|R_t| \ge h$) receive $\rho_t = 0$, completely nullifying their distortion on subsequent Loess smoothing iterations.

---

## 4. Parameter Selection & Heuristic Tuning Framework

The behavior and spectral separation of STL depend on 7 key hyper-parameters. Below are the recommended formulas, constraints, and defaults:

### 4.1 Parameter Specification Table

| Parameter | Symbol | Constraints | Recommended Formula / Value | Semantic Purpose |
|---|---|---|---|---|
| **Period** | $n_{(p)}$ | Integer $\ge 2$ | Domain cadence (e.g. 7 for daily/weekly, 12 for monthly/annual) | Number of observations in one complete seasonal cycle. |
| **Seasonal Window** | $n_{(s)}$ | Odd integer $\ge 7$ | Default: 7 (fast adaptation) or 13 (smooth seasonal pattern) | Span for cycle-subseries Loess. Controls how rapidly seasonal pattern evolves over years/cycles. |
| **Trend Window** | $n_{(t)}$ | Odd integer $> n_{(p)}$ | $n_{(t)} = \left\lceil \frac{1.5 \cdot n_{(p)}}{1 - 1.5 / n_{(s)}} \right\rceil_{\text{odd}}$ | Span for trend Loess. Prevents seasonal variation from contaminating the trend. |
| **Low-Pass Window** | $n_{(l)}$ | Odd integer $\ge n_{(p)}$ | Smallest odd integer $\ge n_{(p)}$ (e.g., $n_{(p)}$ if odd, $n_{(p)}+1$ if even) | Span for low-pass filter Loess. Ensures complete removal of seasonal frequencies. |
| **Inner Iterations** | $n_{(i)}$ | Integer $\ge 1$ | 2 (if robust $n_{(o)} > 0$), 5 (if non-robust $n_{(o)} = 0$) | Number of inner refinement passes per outer loop. |
| **Robust Iterations**| $n_{(o)}$ | Integer $\ge 0$ | 0 (clean data), 1-5 (standard), 15 (heavy outliers/spikes) | Outer robustness passes using bisquare weighting. |
| **Polynomial Degree**| $d$ | $d \in \{0, 1, 2\}$ | $d=1$ (locally linear for seasonal, trend, low-pass) | Degree of local polynomial in Loess regressions. |

### 4.2 Cadence Mapping Matrix for Business Intelligence KPIs

| Business Cadence | Observed Frequency | Typical Period ($n_{(p)}$) | Recommended $n_{(s)}$ | Computed $n_{(t)}$ | Computed $n_{(l)}$ | Typical Use Cases |
|---|---|---|---|---|---|---|
| **Hourly** | Intraday (24/7) | 24 | 13 | 41 | 25 | API throughput, server errors, checkout latency |
| **Daily** | Day of week | 7 | 7 | 15 | 7 | E-commerce orders, GMV, daily active users |
| **Weekly** | Week of year | 52 | 13 | 89 | 53 | High-level sales revenue, enterprise pipeline |
| **Monthly** | Month of year | 12 | 13 | 21 | 13 | Financial GAAP revenue, churn, ARR, COGS |
| **Quarterly** | Quarter of year | 4 | 7 | 9 | 5 | Board-level financial reporting, headcount costs |

---

## 5. Orchestrator Architecture & Pipeline Integration Plan

### 5.1 End-to-End Orchestrator Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DAGSTER / API TRIGGER                             │
│                  Periodic Cron (Hourly/Daily) or Webhook                    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      STAGE 1: CANONICAL EXTRACTION                          │
│  - Query canonical_measurements table for KPI key & target time window      │
│  - Retrieve N periods of historical baseline (minimum 2 * n_(p))            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      STAGE 2: TIME-SERIES REGULARIZATION                    │
│  - Resample into continuous strict-frequency grid (pandas.date_range)       │
│  - Handle missing data / imputation (linear / seasonal-lag)                 │
│  - Multiplicative check: check for zero/negative values; apply log(Y)       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      STAGE 3: STL DECOMPOSITION ENGINE                      │
│  - Execute statsmodels.tsa.seasonal.STL(Y, period, seasonal, robust=True)   │
│  - Decompose into Trend T_t, Seasonal S_t, Remainder R_t                    │
│  - Calculate Expected Baseline: Ŷ_t = T_t + S_t                             │
│  - Calculate Robust Residual Std: σ_R = 1.4826 * MAD(R_t)                   │
│  - Calculate Dynamic Confidence Bands: [Ŷ_t ± z_alpha/2 * σ_R]              │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      STAGE 4: MOVEMENT & ANOMALY DETECTION                  │
│  - Calculate Statistical Score: Z_t = |Y_t - Ŷ_t| / σ_R                     │
│  - Calculate Percentage Change: Δ% = ((Y_t - Ŷ_t) / Ŷ_t) * 100               │
│  - Materiality Filter: Is |Z_t| >= 2.5 AND |Δ%| >= threshold?               │
│      ├── NO  ──► Record baseline in telemetry, END (no anomaly)             │
│      └── YES ──► Construct KPIMovementEvent with metadata.trend_data        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                  STAGE 5: LANGGRAPH INVESTIGATION SWARM                     │
│  - Fan-out to Product, Customer, Geography, Channel Diagnostic Agents       │
│  - Multi-dimensional slicing of anomaly window vs STL expected baseline    │
│  - Analytics Verification (Contribution %, DAG Dependency, Evidence Score)  │
│  - Contradiction Detection & Uncertainty Evaluation                         │
│  - ZenEngine / GoRules Deterministic Governance Gate                        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      STAGE 6: DIAGNOSTIC PAYLOAD & STORY                    │
│  - DiagnosticPayload output with full drivers, lineage, and metadata        │
│  - Direct feeding of metadata.trend_data to Vega-Lite Visualizers API       │
│  - Persona-specific narrative generation (Executive, Engineering, Ops)      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Interface Contracts & Pydantic Data Structures

To guarantee modularity, type safety, and clean integration between the time-series engine, orchestrator, and visualizers, the following Pydantic schemas must be added to `kpi-engine/app/schemas/`:

### 6.1 Time-Series & STL Schemas (`app/schemas/timeseries.py`)

```python
from datetime import datetime
from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator


class STLParameters(BaseModel):
    period: int = Field(..., ge=2, description="Seasonality period n_(p)")
    seasonal: int = Field(default=7, ge=7, description="Seasonal Loess window n_(s) (must be odd)")
    trend: Optional[int] = Field(default=None, description="Trend Loess window n_(t) (must be odd)")
    low_pass: Optional[int] = Field(default=None, description="Low-pass filter window n_(l)")
    seasonal_deg: int = Field(default=1, ge=0, le=2)
    trend_deg: int = Field(default=1, ge=0, le=2)
    low_pass_deg: int = Field(default=1, ge=0, le=2)
    robust: bool = Field(default=True, description="Enable outer loop robustness weights")
    inner_iter: int = Field(default=2, ge=1)
    outer_iter: int = Field(default=5, ge=0)
    transform: Literal["additive", "multiplicative"] = Field(default="additive")
    confidence_level: float = Field(default=0.95, ge=0.5, le=0.999)
    z_threshold: float = Field(default=2.5, description="Z-score threshold for anomaly detection")
    materiality_pct_threshold: float = Field(default=5.0, description="Minimum % deviation to trigger investigation")

    @model_validator(mode="after")
    def validate_odd_windows(self):
        if self.seasonal % 2 == 0:
            raise ValueError(f"seasonal window must be odd, got {self.seasonal}")
        if self.trend is not None and self.trend % 2 == 0:
            raise ValueError(f"trend window must be odd, got {self.trend}")
        if self.low_pass is not None and self.low_pass % 2 == 0:
            raise ValueError(f"low_pass window must be odd, got {self.low_pass}")
        return self


class TrendDataPoint(BaseModel):
    timestamp: datetime
    actual_value: float
    expected_value: float
    trend: float
    seasonal: float
    remainder: float
    lower_bound: float
    upper_bound: float
    is_imputed: bool = False
    is_anomaly: bool = False
    z_score: float = 0.0


class STLDecompositionResult(BaseModel):
    kpi_id: str
    period: int
    cadence: str
    series_length: int
    residual_std: float
    residual_mad: float
    trend_data: List[TrendDataPoint]
    latest_observed: float
    latest_expected: float
    latest_z_score: float
    is_anomaly_detected: bool
    anomaly_direction: Optional[Literal["SPIKE", "DROP"]] = None
```

### 6.2 Updated Orchestrator Investigation State (`app/orchestrator/state.py`)

```python
import operator
from typing import Annotated, TypedDict, List, Dict, Any, Optional

from app.schemas.findings import AgentFinding
from app.schemas.movement import KPIMovementEvent
from app.schemas.diagnostic import DiagnosticPayload
from app.schemas.timeseries import STLDecompositionResult


class InvestigationState(TypedDict, total=False):
    kpi_id: str
    raw_time_series: List[Dict[str, Any]]
    stl_result: Optional[STLDecompositionResult]
    movement: KPIMovementEvent
    findings: Annotated[List[AgentFinding], operator.add]
    analytical_results: List[Dict[str, Any]]
    contradictions: List[Dict[str, Any]]
    diagnostic_payload: Optional[DiagnosticPayload]
```

---

## 7. Edge Cases & Failure Recovery Protocols

| Edge Case / Condition | Statistical Failure Mode | Orchestrator Mitigation & Fallback Strategy |
|---|---|---|
| **Sparse History ($N < 2 \cdot n_{(p)}$)** | STL cannot separate cycle-subseries due to insufficient full periods. | Fallback to **Holt-Winters exponential smoothing** or simple moving average (SMA). Flag `uncertainty.status = "SPARSE_HISTORY"` and set `diagnostic_confidence = 0.5`. |
| **Missing Observations / Irregular Gaps** | Loess requires strictly regular time-step spacing $\Delta t$. | Pre-processing interpolation: Linear interpolation for gaps $\le 3$ intervals; seasonal-lag interpolation ($Y_{t - n_{(p)}}$) for gaps $> 3$ intervals. Mark points with `is_imputed = True`. If missing $> 20\%$ of series, abort STL and request data repair. |
| **Zero or Negative Values in Multiplicative Mode** | $\ln(Y_t)$ is undefined for $Y_t \le 0$. | Automatic mode switch: If $\min(Y) \le 0$, automatically revert from `multiplicative` to `additive` STL, or apply constant shift $Y'_t = Y_t + |\min(Y)| + 1$. Log warning in lineage. |
| **Structural Breaks / Level Shifts** | Trend Loess with large $n_{(t)}$ lags behind sudden permanent level shifts, producing persistent large residuals. | Implement adaptive windowing or changepoint detection (e.g. CUSUM / Pelt). If persistent run of $> 5$ consecutive residuals exceeds $2\sigma$, shorten $n_{(t)}$ to allow trend to track the shift. |
| **Sudden Extreme Outliers (Spikes)** | Single extreme anomaly distorts trend and seasonal subseries. | Robust outer loop ($n_{(o)} \ge 5$) with bisquare weights $\rho_t = B(|R_t|/h)$. Points with $|R_t| \ge 6 \cdot \text{MAD}$ receive $\rho_t = 0$, completely isolating outlier impact. |
| **High Frequency Noise / Multiple Seasonalities** | Intra-day + weekly patterns combined (e.g. hourly data with 24-hr and 168-hr cycles). | Extend STL to **MSTL (Multiple Seasonal-Trend decomposition using LOESS)**, executing sequential Loess filtering passes across multiple period vectors $[24, 168]$. |

---

## 8. Verification Strategy & Mock Data Validation

To objectively verify the STL implementation without writing application code, a verification test suite using synthetic data generators must test the following 5 verification criteria:

### 8.1 Synthetic Test Wave Generator Equation
$$Y_t = \underbrace{(1000 + 5t)}_{\text{Trend } T_t} + \underbrace{200 \sin\left(\frac{2\pi t}{7}\right)}_{\text{Seasonality } S_t} + \underbrace{\epsilon_t}_{\mathcal{N}(0, 25)} + \underbrace{A_t}_{\text{Injected Anomaly}}$$

Where:
- $t = 1, \dots, 90$ (90 daily data points, period $n_{(p)} = 7$).
- At $t=85$, inject a sharp synthetic drop: $A_{85} = -600$.

### 8.2 Objective Verification Assertions

1. **Orthogonality / Variance Explained Verification**:
   $$\text{Var}(Y_t - (T_t + S_t)) \le 1.1 \cdot \text{Var}(\epsilon_t)$$
   The residual variance must match known injected Gaussian noise $\sigma^2 = 25^2 = 625$.

2. **Robustness Against Outliers Assertion**:
   At $t=85$, the outer bisquare weight $\rho_{85}$ must evaluate to $0.0$, and the estimated trend $T_{85}$ must not deviate by more than $5\%$ from the ground-truth line $1000 + 5(85) = 1425$.

3. **Anomaly Detection Trigger Assertion**:
   At $t=85$, the calculated $Z$-score must satisfy $|Z_{85}| \ge 15.0$, successfully triggering `KPIMovementEvent` with `observed_value = 825.0` and `expected_value = 1425.0`.

4. **Visualizer Contract Compliance Assertion**:
   The generated `metadata.trend_data` must contain 90 elements matching `TrendDataPoint` schema, with non-null `lower_bound`, `upper_bound`, and `expected_value`, matching the exact format consumed by `frontend/Visualizers/api/main.py`.

---

## 9. Next Steps for Implementation Team

1. Add `statsmodels>=0.14.0`, `scipy>=1.11.0`, `numpy>=1.24.0`, and `pandas>=2.0.0` to `kpi-engine/requirements.txt`.
2. Implement `app/schemas/timeseries.py` defining `STLParameters`, `TrendDataPoint`, and `STLDecompositionResult`.
3. Implement `app/services/timeseries.py` with `decompose_kpi_series()` and `evaluate_kpi_anomaly()`.
4. Update `app/orchestrator/graph.py` to include the upstream `kpi_extractor` and `stl_evaluator` nodes prior to agent swarm dispatch.
5. Populate `metadata.trend_data` in `DiagnosticPayload` to complete end-to-end rendering in the frontend Vega-Lite visualizers.
