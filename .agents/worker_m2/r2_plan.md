# Technical Implementation Plan: Orchestrator Completion via STL Decomposition (Requirement R2)

**Author**: Worker 2 (Orchestrator & Time-Series / STL Decomposition Architect)  
**Milestone**: M2 (Requirement R2)  
**Status**: Authoritative Architectural Plan  
**Target Subsystems**: `kpi-engine/app/timeseries/`, `kpi-engine/app/orchestrator/`, `kpi-engine/app/schemas/timeseries.py`, `frontend/Visualizers/`  
**Explicit Constraint**: Contextual debouncing is **strictly excluded** from this architecture.

---

## Table of Contents
1. [Executive Summary & Upstream Orchestrator Integration](#1-executive-summary--upstream-orchestrator-integration)
2. [Mathematical Foundations of LOESS & STL Decomposition](#2-mathematical-foundations-of-loess--stl-decomposition)
   - [2.1 The Additive and Multiplicative STL Framework](#21-the-additive-and-multiplicative-stl-framework)
   - [2.2 LOESS Smoothing Mathematics](#22-loess-smoothing-mathematics)
   - [2.3 The STL Inner Loop (6-Step Procedure)](#23-the-stl-inner-loop-6-step-procedure)
   - [2.4 The STL Outer Loop (Robustness Iteration)](#24-the-stl-outer-loop-robustness-iteration)
3. [Cadence-Specific Parameter Tuning & Selection Framework](#3-cadence-specific-parameter-tuning--selection-framework)
   - [3.1 Parameter Definitions and Mathematical Constraints](#31-parameter-definitions-and-mathematical-constraints)
   - [3.2 The 5 Core Business Cadences Mapping Matrix](#32-the-5-core-business-cadences-mapping-matrix)
4. [Dynamic Baseline, Confidence Bounds & Anomaly Triggering](#4-dynamic-baseline-confidence-bounds--anomaly-triggering)
   - [4.1 Dynamic Expected Baseline Formulation](#41-dynamic-expected-baseline-formulation)
   - [4.2 Robust Residual Uncertainty Estimation](#42-robust-residual-uncertainty-estimation)
   - [4.3 Dynamic Confidence Interval Bands](#43-dynamic-confidence-interval-bands)
   - [4.4 Statistical Score & KPIMovementEvent Triggering](#44-statistical-score--kpimovementevent-triggering)
5. [Interface Contracts & Pydantic Data Models](#5-interface-contracts--pydantic-data-models)
   - [5.1 `app/schemas/timeseries.py`](#51-appschemastimeseriespy)
   - [5.2 Updated `app/orchestrator/state.py`](#52-updated-apporchestratorstatepy)
   - [5.3 Frontend Vega-Lite Visualizer Integration](#53-frontend-vega-lite-visualizer-integration)
6. [Edge Case Handling & Statistical Failure Recovery](#6-edge-case-handling--statistical-failure-recovery)
   - [6.1 Sparse History ($N < 2 n_{(p)}$) & Cold Starts](#61-sparse-history-n--2-n_p--cold-starts)
   - [6.2 Missing Data Imputation & Grid Regularization](#62-missing-data-imputation--grid-regularization)
   - [6.3 Multiplicative Transformation & Zero-Inflation](#63-multiplicative-transformation--zero-inflation)
   - [6.4 Structural Breaks & Level Shifts](#64-structural-breaks--level-shifts)
   - [6.5 Multiple Seasonalities (MSTL Extension)](#65-multiple-seasonalities-mstl-extension)
7. [Objective Synthetic Verification & Mock Testing Suite](#7-objective-synthetic-verification--mock-testing-suite)
   - [7.1 Synthetic Test Wave Generator Equation](#71-synthetic-test-wave-generator-equation)
   - [7.2 Mathematical Verification Assertions](#72-mathematical-verification-assertions)
8. [Module-by-Module Code Layout & Step-by-Step Implementation Roadmap](#8-module-by-module-code-layout--step-by-step-implementation-roadmap)

---

## 1. Executive Summary & Upstream Orchestrator Integration

### 1.1 Architectural Context & Gap
The current `kpi-engine` implementation executes multi-agent causal investigations using LangGraph (`kpi-engine/app/orchestrator/graph.py`), deterministic analytics (`app/analytics/`), and a ZenEngine governance decision table (`app/governance/`). However, the existing graph starts downstream of an already synthesized `KPIMovementEvent`. There is currently no statistical time-series decomposition engine to generate dynamic baseline expectations ($\hat{Y}_t$), isolate cyclical seasonal noise ($S_t$), calculate residual variance ($\sigma_R$), or objectively determine whether an observed movement is statistically significant.

Furthermore, the frontend visualization engine (`frontend/Visualizers/api/main.py`) exposes an `errorband` and `line` chart expecting `metadata.trend_data` containing `[timestamp, actual_value, expected_value, lower_bound, upper_bound]`, which is currently unpopulated in real runs.

### 1.2 Upstream Orchestrator Integration Architecture
To complete Requirement R2, a statistical time-series processing pipeline is introduced **upstream** of the LangGraph agent swarm. The orchestrator workflow is augmented with two upstream nodes:
1. `kpi_extractor_node`: Queries historical metric measurements from PostgreSQL `canonical_measurements`, validates sample size, regularizes the temporal grid, and applies necessary data imputation.
2. `stl_evaluator_node`: Executes Cleveland et al. (1990) STL decomposition using Loess, separates Trend ($T_t$), Seasonality ($S_t$), and Remainder ($R_t$), computes dynamic confidence bounds, calculates the anomaly $Z$-score, and determines if a statistically significant, material movement occurred.

### 1.3 Exclusion of Contextual Debouncing
Per strict architectural requirements, **contextual debouncing is explicitly excluded**. Anomaly triggering is evaluated purely on mathematical deviations ($|Z_t| \ge Z_{\text{threshold}}$) and business materiality ($|\Delta \%_t| \ge \text{Threshold}$), without suppressing alerts via sliding temporal windows, cooldown timers, or debouncing heuristics.

### 1.4 End-to-End Orchestrator Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                 PERIODIC CRON / API TRIGGER                             │
│                  Executes on cadence (Hourly, Daily, Weekly, Monthly)                   │
└────────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                     UPSTREAM NODE 1: `kpi_extractor_node`                                │
│  - Query PostgreSQL canonical_measurements for target KPI and history [t - N, t]        │
│  - Construct strict continuous DateTime index (pandas.date_range / Polars)              │
│  - Regularize grid: interpolate missing values (linear for gap <= 3, lag for gap > 3)   │
│  - Gate check: Verify N >= 2 * n_(p) (Minimum 2 full seasonal cycles)                   │
└────────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                     UPSTREAM NODE 2: `stl_evaluator_node`                               │
│  - Configure Cadence-Specific STL Parameters (n_(p), n_(s), n_(t), n_(l), n_(i), n_(o)) │
│  - Execute 2-Loop Cleveland STL Decomposition with Loess degree d=1                     │
│  - Decompose series: Y_t = T_t + S_t + R_t                                              │
│  - Compute Dynamic Expected Baseline: Ŷ_t = T_t + S_t                                   │
│  - Compute Robust Residual Standard Deviation: σ_R = 1.4826 * MAD(R_t)                  │
│  - Calculate Dynamic Confidence Bands: [Ŷ_t - z * σ_R, Ŷ_t + z * σ_R]                   │
│  - Calculate Anomaly Metric: Z_t = |Y_t - Ŷ_t| / σ_R and Δ%_t                           │
└────────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
                                ┌─────────────────────────┐
                                │ Is Anomaly Material?    │
                                │ |Z_t| >= 2.5 & |Δ%|>=5% │
                                └────────────┬────────────┘
                                             │
                      ┌──────────────────────┴──────────────────────┐
                   NO │                                             │ YES
                      ▼                                             ▼
┌───────────────────────────────────────────┐ ┌───────────────────────────────────────────┐
│           NO ACTION / RECORD TELEMETRY    │ │   CONSTRUCT KPIMovementEvent              │
│  - Persist baseline & trend_data to Gold  │ │   - Observed: Y_t, Expected: Ŷ_t          │
│  - Emit OpenTelemetry healthy metric      │ │   - Z-score: Z_t, Deviation: Δ%           │
│  - Graph execution completes at END       │ │   - Attach STLDecompositionResult         │
└───────────────────────────────────────────┘ └─────────────────────┬─────────────────────┘
                                                                    │
                                                                    ▼
                                              ┌───────────────────────────────────────────┐
                                              │   LANGGRAPH INVESTIGATION SWARM (PARALLEL)│
                                              │   ├── product_agent                       │
                                              │   ├── customer_agent                      │
                                              │   ├── geography_agent                     │
                                              │   └── channel_agent                       │
                                              └─────────────────────┬─────────────────────┘
                                                                    │
                                                                    ▼
                                              ┌───────────────────────────────────────────┐
                                              │   ANALYSIS & CONTRADICTIONS NODES         │
                                              │   - Shapley contribution vs baseline      │
                                              │   - Causal DAG path validation            │
                                              │   - Evidence scoring & pairwise conflicts │
                                              └─────────────────────┬─────────────────────┘
                                                                    │
                                                                    ▼
                                              ┌───────────────────────────────────────────┐
                                              │   ORCHESTRATOR & GOVERNANCE NODES         │
                                              │   - Synthesize DiagnosticPayload          │
                                              │   - Embed metadata.trend_data             │
                                              │   - ZenEngine GoRules validation          │
                                              └─────────────────────┬─────────────────────┘
                                                                    │
                                                                    ▼
                                              ┌───────────────────────────────────────────┐
                                              │   FRONTEND VEGA-LITE VISUALIZER API       │
                                              │   - Render Errorband + Expected + Actual  │
                                              │   - Persona narrative presentation        │
                                              └───────────────────────────────────────────┘
```

---

## 2. Mathematical Foundations of LOESS & STL Decomposition

### 2.1 The Additive and Multiplicative STL Framework
STL (Seasonal and Trend decomposition using Loess), formulated by Robert B. Cleveland, William S. Cleveland, Jean E. McRae, and Irma Terpenning (1990), decomposes a time series into three components:

$$Y_t = T_t + S_t + R_t \quad \text{for } t = 1, 2, \dots, N$$

Where:
- $Y_t$: Observed continuous metric value at index $t$.
- $T_t$: **Trend component**, capturing macro, low-frequency deterministic shifts and multi-cycle drift.
- $S_t$: **Seasonal component**, capturing deterministic or slowly evolving periodic oscillations of fixed cadence $n_{(p)}$.
- $R_t$: **Remainder (residual) component**, capturing stationary stochastic noise and anomalous transient excursions.

For multiplicative time-series (e.g. e-commerce revenue, web traffic, where seasonal amplitude scales proportionally with the baseline level):

$$\ln(Y_t) = T_t + S_t + R_t \iff Y_t = \exp(T_t) \cdot \exp(S_t) \cdot \exp(R_t)$$

The additive STL algorithm is applied directly to the log-transformed series $Z_t = \ln(Y_t)$, and components are exponentiated back to the natural domain:

$$\hat{Y}_t = \exp(T_t + S_t), \quad \text{Bounds} = \left[\exp(\hat{Z}_t - z \cdot \sigma_{R_Z}), \, \exp(\hat{Z}_t + z \cdot \sigma_{R_Z})\right]$$

---

### 2.2 LOESS Smoothing Mathematics

LOESS (Locally Estimated Scatterplot Smoothing) is the foundational non-parametric smoothing engine used within STL. At any query point $x_0 \in \mathbb{R}$, LOESS fits a local polynomial of degree $d \in \{0, 1, 2\}$ using weighted least squares (WLS). In STL, degree $d=1$ (locally linear regression) is standard to prevent overfitting and boundary bias.

#### Step 1: Local Neighborhood Selection & Bandwidth
Given $N$ observation points $(x_i, y_i)_{i=1}^N$ and a smoothing window parameter $q \in \mathbb{Z}^+$ ($q \ge 3$):
Let $\mathcal{N}_q(x_0)$ be the set of the $q$ nearest observations to $x_0$. The maximum neighborhood distance $\Delta(x_0)$ is defined as:

$$\Delta(x_0) = \begin{cases} 
\max_{i \in \mathcal{N}_q(x_0)} |x_i - x_0| & \text{if } q \le N \\ 
\Delta(x_N) \cdot \frac{q}{N} & \text{if } q > N 
\end{cases}$$

#### Step 2: Neighborhood Tricube Weight Function
The spatial proximity of observation $x_i$ relative to $x_0$ is scaled into normalized distance $u_i(x_0)$:

$$u_i(x_0) = \frac{|x_i - x_0|}{\Delta(x_0)}$$

The distance weight $w_i(x_0)$ is evaluated using the **Tricube Weight Function** $W(u)$:

$$W(u) = \begin{cases} 
(1 - |u|^3)^3 & \text{for } 0 \le |u| < 1 \\ 
0 & \text{for } |u| \ge 1 
\end{cases}$$

The tricube function possesses continuous first and second derivatives at both $u=0$ and the boundary $|u|=1$, ensuring smooth spatial transitions without gradient discontinuities.

#### Step 3: Integration with Outer Robustness Weights
When LOESS is executed during an outer robustness loop, each observation $i$ carries an associated robustness weight $\rho_i \in [0, 1]$ (derived from bisquare weighting of residuals). The composite regression weight $\tilde{w}_i(x_0)$ is:

$$\tilde{w}_i(x_0) = \rho_i \cdot W\left( \frac{|x_i - x_0|}{\Delta(x_0)} \right)$$

#### Step 4: Locally Weighted Linear Regression (WLS)
For degree $d=1$, we find polynomial coefficients $\hat{\boldsymbol{\beta}} = [\hat{\beta}_0, \hat{\beta}_1]^T$ that minimize the weighted sum of squared residuals:

$$\min_{\beta_0, \beta_1} \sum_{i=1}^N \tilde{w}_i(x_0) \left( y_i - \beta_0 - \beta_1 (x_i - x_0) \right)^2$$

In matrix notation:
Let the design matrix centered at $x_0$ be:

$$\mathbf{X}_{x_0} = \begin{bmatrix} 
1 & (x_1 - x_0) \\ 
1 & (x_2 - x_0) \\ 
\vdots & \vdots \\ 
1 & (x_N - x_0) 
\end{bmatrix}_{N \times 2}, \quad 
\mathbf{W}_{x_0} = \operatorname{diag}\left(\tilde{w}_1(x_0), \tilde{w}_2(x_0), \dots, \tilde{w}_N(x_0)\right)_{N \times N}, \quad 
\mathbf{y} = \begin{bmatrix} y_1 \\ y_2 \\ \vdots \\ y_N \end{bmatrix}$$

The normal equations yield:

$$\left( \mathbf{X}_{x_0}^T \mathbf{W}_{x_0} \mathbf{X}_{x_0} \right) \hat{\boldsymbol{\beta}} = \mathbf{X}_{x_0}^T \mathbf{W}_{x_0} \mathbf{y} \implies \hat{\boldsymbol{\beta}} = \left( \mathbf{X}_{x_0}^T \mathbf{W}_{x_0} \mathbf{X}_{x_0} \right)^{-1} \mathbf{X}_{x_0}^T \mathbf{W}_{x_0} \mathbf{y}$$

Because the coordinates are centered at $x_0$, $(x_0 - x_0) = 0$. The smoothed estimate $\hat{y}(x_0)$ is directly the intercept:

$$\hat{y}(x_0) = \hat{\beta}_0 = [1, 0] \left( \mathbf{X}_{x_0}^T \mathbf{W}_{x_0} \mathbf{X}_{x_0} \right)^{-1} \mathbf{X}_{x_0}^T \mathbf{W}_{x_0} \mathbf{y}$$

---

### 2.3 The STL Inner Loop (6-Step Procedure)

The inner loop executes $n_{(i)}$ iterations (indexed by $j = 1, \dots, n_{(i)}$) to iteratively isolate and separate the seasonal component $S_t^{(j)}$ and the trend component $T_t^{(j)}$.

```
                         INNER LOOP ITERATION (j)
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Detrend:                                                                 │
│    D_t = Y_t - T_t^(j-1)                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. Cycle-Subseries LOESS Smoothing:                                         │
│    Split D_t into n_(p) subseries; smooth each with LOESS(n_(s), d=1)       │
│    Extrapolate forward/backward by 1 period -> C_t^(j) of length N + 2*n_(p)│
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. Low-Pass Filter:                                                         │
│    MA(n_(p)) -> MA(n_(p)) -> MA(3) -> LOESS(n_(l), d=1) -> L_t^(j)          │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. Seasonal Detrending:                                                     │
│    S_t^(j) = C_t^(j) - L_t^(j)                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ 5. Deseasonalizing:                                                         │
│    V_t^(j) = Y_t - S_t^(j)                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ 6. Trend LOESS Smoothing:                                                   │
│    LOESS(V_t^(j), n_(t), d=1) -> T_t^(j)                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Step 1: Detrending
Subtract the prior trend estimate $T_t^{(j-1)}$ (with initial $T_t^{(0)} = 0$) from the raw time series:

$$D_t^{(j)} = Y_t - T_t^{(j-1)} \quad \text{for } t = 1, \dots, N$$

#### Step 2: Cycle-Subseries Smoothing
The detrended series $D_t^{(j)}$ is partitioned into $n_{(p)}$ disjoint cycle-subseries based on temporal phase $\gamma \in \{1, 2, \dots, n_{(p)}\}$:

$$D_{\gamma}^{(j)} = \left\{ D_{\gamma + m \cdot n_{(p)}}^{(j)} \;\middle|\; m = 0, 1, \dots, \left\lfloor \frac{N - \gamma}{n_{(p)}} \right\rfloor \right\}$$

- Each cycle-subseries $D_{\gamma}^{(j)}$ is smoothed independently using LOESS with window span $n_{(s)}$ and polynomial degree $d=1$, utilizing robustness weights $\rho_{\gamma + m \cdot n_{(p)}}$.
- Each smoothed subseries is extrapolated forward by 1 period ($m = \lfloor (N - \gamma)/n_{(p)} \rfloor + 1$) and backward by 1 period ($m = -1$).
- The smoothed and extrapolated subseries are recombined into chronological order, creating the temporary seasonal cycle series $C_t^{(j)}$ for $t = 1 - n_{(p)}, \dots, N + n_{(p)}$ (length $N + 2 n_{(p)}$).

#### Step 3: Low-Pass Filtering of Smoothed Cycle-Subseries
To ensure no low-frequency trend remains trapped within the seasonal estimates, $C_t^{(j)}$ is passed through a 4-stage cascaded low-pass filter:
1. **Moving Average 1**: Symmetrical moving average of length $n_{(p)}$:
   $$A_t^{(1)} = \frac{1}{n_{(p)}} \sum_{k = -\lfloor n_{(p)}/2 \rfloor}^{\lfloor (n_{(p)}-1)/2 \rfloor} C_{t+k}^{(j)}$$
2. **Moving Average 2**: Second symmetrical moving average of length $n_{(p)}$:
   $$A_t^{(2)} = \frac{1}{n_{(p)}} \sum_{k = -\lfloor n_{(p)}/2 \rfloor}^{\lfloor (n_{(p)}-1)/2 \rfloor} A_{t+k}^{(1)}$$
3. **Moving Average 3**: Moving average of length 3:
   $$A_t^{(3)} = \frac{1}{3} \left( A_{t-1}^{(2)} + A_t^{(2)} + A_{t+1}^{(2)} \right)$$
4. **LOESS Smoothing**: LOESS smoothing on $A_t^{(3)}$ with window length $n_{(l)}$ and degree $d=1$, using weights $\rho_t$.

The resulting low-pass output $L_t^{(j)}$ is defined for $t = 1, \dots, N$.

#### Step 4: Seasonal Subseries Low-Pass Subtraction
The pure seasonal component $S_t^{(j)}$ is obtained by subtracting the low-pass trend leakage $L_t^{(j)}$ from the smoothed cycle series $C_t^{(j)}$:

$$S_t^{(j)} = C_t^{(j)} - L_t^{(j)} \quad \text{for } t = 1, \dots, N$$

This step guarantees that $\sum_{k=0}^{n_{(p)}-1} S_{t+k}^{(j)} \approx 0$, preserving zero-mean seasonal oscillations over any full period.

#### Step 5: Deseasonalizing
Subtract the updated seasonal component from the original raw time series:

$$V_t^{(j)} = Y_t - S_t^{(j)} \quad \text{for } t = 1, \dots, N$$

#### Step 6: Trend Smoothing
Smooth the deseasonalized series $V_t^{(j)}$ using LOESS with window span $n_{(t)}$, polynomial degree $d=1$, and robustness weights $\rho_t$:

$$T_t^{(j)} = \operatorname{LOESS}\left(V_t^{(j)}; \, n_{(t)}, \, d=1, \, \boldsymbol{\rho}\right) \quad \text{for } t = 1, \dots, N$$

---

### 2.4 The STL Outer Loop (Robustness Iteration)

The outer loop executes $n_{(o)}$ iterations (indexed by $k = 1, \dots, n_{(o)}$) to dynamically downweight transient spikes and structural outliers.

#### Step 1: Remainder Computation
At the conclusion of the $n_{(i)}$ inner loop passes, the residual/remainder series $R_t$ is computed:

$$R_t = Y_t - T_t - S_t \quad \text{for } t = 1, \dots, N$$

#### Step 2: Residual Scale Parameter $h$
The median absolute residual is computed:

$$M = \operatorname{median}\left( |R_1|, |R_2|, \dots, |R_N| \right)$$

The cutoff threshold $h$ is defined as 6 times the median absolute residual:

$$h = 6 \cdot M$$

If $h = 0$ (e.g. in perfectly synthetic zero-noise series), set $\rho_t = 1.0$ for all $t$ to avoid division by zero.

#### Step 3: Bisquare Robustness Weighting
The Tukey Bisquare function $B(u)$ is defined as:

$$B(u) = \begin{cases} 
\left(1 - u^2\right)^2 & \text{for } 0 \le u < 1 \\ 
0 & \text{for } u \ge 1 
\end{cases}$$

For each time point $t = 1, \dots, N$, the robustness weight $\rho_t$ is updated:

$$\rho_t = B\left( \frac{|R_t|}{h} \right) = \begin{cases} 
\left( 1 - \left(\frac{|R_t|}{6 M}\right)^2 \right)^2 & \text{if } |R_t| < 6 M \\ 
0 & \text{if } |R_t| \ge 6 M 
\end{cases}$$

```
                TUKEY BISQUARE ROBUSTNESS WEIGHT ρ_t
   1.0 ┼─────────╮
       │          ╲
   0.8 ┼           ╲
       │            ╲
   0.6 ┼             ╲
       │              ╲
   0.4 ┼               ╲
       │                ╲
   0.2 ┼                 ╲
       │                  ╲
   0.0 ┼───────────────────┴───────────────────────────────►
       0                  3M                       6M = h   |R_t|
                        (50% Weight)             (0 Weight: Nullified)
```

Observations with residuals exceeding $6M$ are assigned $\rho_t = 0$, completely eliminating their biasing influence on both local trend and seasonal subseries fits during subsequent iterations.

---

## 3. Cadence-Specific Parameter Tuning & Selection Framework

### 3.1 Parameter Definitions and Mathematical Constraints

STL behavior is governed by 7 parameters. To ensure mathematical stability and prevent harmonic leakage, parameters must satisfy strict mathematical relations:

1. **Period ($n_{(p)}$)**: Number of discrete time steps in one full seasonal cycle. $n_{(p)} \in \mathbb{Z}_{\ge 2}$.
2. **Seasonal Window ($n_{(s)}$)**: Smoothing span for cycle-subseries LOESS.
   - **Constraint**: $n_{(s)}$ must be an **odd integer** $\ge 7$.
   - **Tuning rule**: Small $n_{(s)}$ (e.g. 7) allows the seasonal pattern to evolve rapidly across years. Large $n_{(s)}$ (e.g. 13 to 21) forces a rigid, stationary seasonal pattern.
3. **Low-Pass Filter Window ($n_{(l)}$)**: Smoothing span for the low-pass filter.
   - **Constraint**: Smallest **odd integer** $\ge n_{(p)}$.
   - **Formula**:
     $$n_{(l)} = \begin{cases} n_{(p)} & \text{if } n_{(p)} \text{ is odd} \\ n_{(p)} + 1 & \text{if } n_{(p)} \text{ is even} \end{cases}$$
4. **Trend Window ($n_{(t)}$)**: Smoothing span for deseasonalized trend LOESS.
   - **Constraint**: $n_{(t)}$ must be an **odd integer** $> n_{(p)}$.
   - **Cleveland et al. (1990) Harmonic Separation Formula**:
     $$n_{(t)} = \left\lceil \frac{1.5 \cdot n_{(p)}}{1 - 1.5 / n_{(s)}} \right\rceil_{\text{odd}}$$
     Where $\lceil x \rceil_{\text{odd}}$ denotes rounding up to the nearest odd integer if the ceiling is even. This condition guarantees that trend estimation does not absorb seasonal power spectrum frequencies.
5. **Inner Iterations ($n_{(i)}$)**: Number of inner loop iterations.
   - Standard: $n_{(i)} = 2$ when robust outer loop is enabled ($n_{(o)} > 0$); $n_{(i)} = 5$ for non-robust fast passes.
6. **Outer Robustness Iterations ($n_{(o)}$)**: Number of outer bisquare robustness iterations.
   - Standard: $n_{(o)} = 5$ for production metric analysis; $n_{(o)} = 15$ for highly volatile or spike-prone telemetry metrics.
7. **Polynomial Degrees**:
   - $d_{(s)} = 1$ (locally linear for seasonal subseries)
   - $d_{(t)} = 1$ (locally linear for trend)
   - $d_{(l)} = 1$ (locally linear for low-pass filter)

---

### 3.2 The 5 Core Business Cadences Mapping Matrix

The table below specifies the exact mathematical parameterization across the 5 primary business rhythms:

| Business Cadence | Temporal Unit | Period ($n_{(p)}$) | Seasonal Window ($n_{(s)}$) | Computed Trend Window ($n_{(t)}$) | Computed Low-Pass ($n_{(l)}$) | Inner Iter ($n_{(i)}$) | Outer Iter ($n_{(o)}$) | Minimum History Required ($N_{\min} = 2 n_{(p)}$) | Recommended Baseline ($N = 6 n_{(p)}$) |
|---|---|---|---|---|---|---|---|---|---|
| **Hourly** | Intraday (1 hr) | **24** | **13** | **41** | **25** | 2 | 5 | 48 hours | 144 hours (6 days) |
| **Daily** | Day of week (1 day) | **7** | **7** | **15** | **7** | 2 | 5 | 14 days | 42 days (6 weeks) |
| **Weekly** | Week of year (1 week)| **52** | **13** | **89** | **53** | 2 | 5 | 104 weeks (2 yrs) | 156 weeks (3 yrs) |
| **Monthly**| Month of year (1 mo) | **12** | **13** | **21** | **13** | 2 | 5 | 24 months (2 yrs) | 72 months (6 yrs) |
| **Quarterly**| Quarter (1 quarter)| **4** | **7** | **9** | **5** | 2 | 5 | 8 quarters (2 yrs)| 24 quarters (6 yrs) |

#### Mathematical Verification of Cadence Calculations:
- **Hourly**: $n_{(p)} = 24, n_{(s)} = 13 \implies n_{(t)} = \left\lceil \frac{1.5 \times 24}{1 - 1.5/13} \right\rceil = \left\lceil \frac{36}{1 - 0.11538} \right\rceil = \left\lceil 40.697 \right\rceil = 41$ (odd). Low-pass $n_{(l)} = 24 + 1 = 25$ (odd).
- **Daily**: $n_{(p)} = 7, n_{(s)} = 7 \implies n_{(t)} = \left\lceil \frac{1.5 \times 7}{1 - 1.5/7} \right\rceil = \left\lceil \frac{10.5}{0.7857} \right\rceil = \left\lceil 13.36 \right\rceil = 15$ (odd). Low-pass $n_{(l)} = 7$ (odd).
- **Weekly**: $n_{(p)} = 52, n_{(s)} = 13 \implies n_{(t)} = \left\lceil \frac{1.5 \times 52}{1 - 1.5/13} \right\rceil = \left\lceil \frac{78}{0.8846} \right\rceil = \left\lceil 88.17 \right\rceil = 89$ (odd). Low-pass $n_{(l)} = 52 + 1 = 53$ (odd).
- **Monthly**: $n_{(p)} = 12, n_{(s)} = 13 \implies n_{(t)} = \left\lceil \frac{1.5 \times 12}{1 - 1.5/13} \right\rceil = \left\lceil \frac{18}{0.8846} \right\rceil = \left\lceil 20.348 \right\rceil = 21$ (odd). Low-pass $n_{(l)} = 12 + 1 = 13$ (odd).
- **Quarterly**: $n_{(p)} = 4, n_{(s)} = 7 \implies n_{(t)} = \left\lceil \frac{1.5 \times 4}{1 - 1.5/7} \right\rceil = \left\lceil \frac{6}{0.7857} \right\rceil = \left\lceil 7.636 \right\rceil = 9$ (odd). Low-pass $n_{(l)} = 4 + 1 = 5$ (odd).

---

## 4. Dynamic Baseline, Confidence Bounds & Anomaly Triggering

```
                               DYNAMIC CONFIDENCE BAND
   Metric Value
       ▲
       │                                         ● Observed Y_t (ANOMALY TRIGGER!)
       │                                     ▲  /
       │                              ───────│─/────────────────── Upper Bound: Ŷ_t + z·σ_R
       │                       - - - - - - - │- - - - - - - - - -  Expected Baseline Ŷ_t = T_t + S_t
       │                              ───────│──────────────────── Lower Bound: Ŷ_t - z·σ_R
       │                 ●            ●      │
       │          ●     / \          / \     ▼ Residual Width: 2·z·σ_R
       │         / \   /   \   ●    /   \
       │  ●     /   \ /     \ / \  /     \
       │───\───/─────●───────●───\/───────●───────────────────────►
       0                                                    Time t
```

### 4.1 Dynamic Expected Baseline Formulation
At any point $t$ (including the latest evaluation period $t=N$), the dynamic expected baseline $\hat{Y}_t$ accounts for both macro trend drift and the cyclic seasonal expectation:

$$\hat{Y}_t = T_t + S_t$$

Unlike a naive trailing moving average (which suffers from phase lag during trends and is blind to day-of-week/month-of-year seasonality), $\hat{Y}_t$ provides a phase-aligned, season-adjusted counterfactual expected value.

---

### 4.2 Robust Residual Uncertainty Estimation
Standard sample standard deviation $s_R = \sqrt{\frac{1}{N-1}\sum (R_t - \bar{R})^2}$ is vulnerable to leverage contamination from anomalies, which inflates the variance estimate and leads to false negative masking.

To ensure resilience, the residual uncertainty $\sigma_R$ is estimated using the **Median Absolute Deviation (MAD)** scaled for asymptotic normal consistency:

$$\operatorname{MAD}(R) = \operatorname{median}\left( \left| R_t - \operatorname{median}(R) \right| \right)$$

$$\sigma_R = 1.4826022185 \cdot \operatorname{MAD}(R)$$

Where $1.4826 \approx \frac{1}{\Phi^{-1}(0.75)}$ ensures that $\mathbb{E}[\sigma_R] = \sigma$ when residuals are identically and independently distributed Gaussian noise $\mathcal{N}(0, \sigma^2)$.

---

### 4.3 Dynamic Confidence Interval Bands
For a designated confidence level $(1 - \alpha)$ (default $95\%$, corresponding to two-tailed significance $\alpha = 0.05$ and standard normal critical value $z_{\alpha/2} = \Phi^{-1}(1 - \alpha/2) = 1.95996 \approx 1.96$):

$$\text{Lower Bound}_t = \hat{Y}_t - z_{\alpha/2} \cdot \sigma_R = (T_t + S_t) - z_{\alpha/2} \cdot \sigma_R$$

$$\text{Upper Bound}_t = \hat{Y}_t + z_{\alpha/2} \cdot \sigma_R = (T_t + S_t) + z_{\alpha/2} \cdot \sigma_R$$

For high-criticality metrics requiring $99\%$ confidence bounds ($\alpha = 0.01$), $z_{0.005} = 2.576$.

---

### 4.4 Statistical Score & KPIMovementEvent Triggering

#### Step 1: Statistical Deviation $Z$-Score
At the latest observation index $t=N$:

$$Z_N = \frac{Y_N - \hat{Y}_N}{\sigma_R} = \frac{Y_N - (T_N + S_N)}{\sigma_R}$$

#### Step 2: Percentage Movement
The relative percentage deviation against the seasonal-trend expectation is:

$$\Delta \%_N = \left( \frac{Y_N - \hat{Y}_N}{\hat{Y}_N} \right) \times 100$$

#### Step 3: Materiality and Anomaly Evaluation
An investigation is triggered if and only if both the statistical threshold and business materiality criteria are met:

$$\operatorname{IsAnomaly}(Y_N) = \left( |Z_N| \ge Z_{\text{threshold}} \right) \land \left( |\Delta \%_N| \ge \text{MaterialityPctThreshold} \right)$$

Where default system configurations are:
- $Z_{\text{threshold}} = 2.50$ (corresponding to $p < 0.0124$ rarity under Gaussian remainder)
- $\text{MaterialityPctThreshold} = 5.0\%$ (prevents triggering on high-precision low-variance metrics with negligible economic impact)

#### Step 4: Upstream Event Construction
When $\operatorname{IsAnomaly}(Y_N) = \text{True}$, the `stl_evaluator_node` constructs a formal `KPIMovementEvent`:

```python
KPIMovementEvent(
    event_id=f"EVT-{kpi_id}-{analysis_end.strftime('%Y%m%d%H%M')}",
    kpi_id=kpi_id,
    analysis_start=analysis_start,
    analysis_end=analysis_end,
    observed_value=float(Y_N),
    expected_value=float(hat_Y_N),
    absolute_change=float(Y_N - hat_Y_N),
    percentage_change=float(delta_pct_N),
    statistical_score=float(abs(Z_N)),
    materiality_status="CRITICAL" if abs(Z_N) >= 3.5 else "SIGNIFICANT",
    dimensions=dimension_list
)
```

---

## 5. Interface Contracts & Pydantic Data Models

### 5.1 `app/schemas/timeseries.py`
The following schemas define the time-series decomposition inputs, data points, and outputs:

```python
from datetime import datetime
from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator


class STLParameters(BaseModel):
    """Configuration hyper-parameters for Cleveland STL Decomposition."""
    period: int = Field(..., ge=2, description="Number of observations per seasonal cycle n_(p)")
    seasonal: int = Field(default=7, ge=7, description="Seasonal Loess window span n_(s) (must be odd)")
    trend: Optional[int] = Field(default=None, description="Trend Loess window span n_(t) (must be odd)")
    low_pass: Optional[int] = Field(default=None, description="Low-pass filter window span n_(l) (must be odd)")
    seasonal_deg: int = Field(default=1, ge=0, le=2, description="Degree of seasonal Loess polynomial")
    trend_deg: int = Field(default=1, ge=0, le=2, description="Degree of trend Loess polynomial")
    low_pass_deg: int = Field(default=1, ge=0, le=2, description="Degree of low-pass Loess polynomial")
    robust: bool = Field(default=True, description="Enable outer loop Tukey bisquare robustness iterations")
    inner_iter: int = Field(default=2, ge=1, description="Number of inner loop iterations n_(i)")
    outer_iter: int = Field(default=5, ge=0, description="Number of outer loop robustness iterations n_(o)")
    transform: Literal["additive", "multiplicative"] = Field(
        default="additive", description="Decomposition type (additive or log-transformed multiplicative)"
    )
    confidence_level: float = Field(default=0.95, ge=0.50, le=0.999, description="Confidence interval coverage (1 - alpha)")
    z_threshold: float = Field(default=2.5, ge=1.0, description="Z-score critical threshold for anomaly trigger")
    materiality_pct_threshold: float = Field(default=5.0, ge=0.0, description="Minimum absolute % deviation required")

    @model_validator(mode="after")
    def validate_odd_windows(self):
        if self.seasonal % 2 == 0:
            raise ValueError(f"seasonal window must be an odd integer, got {self.seasonal}")
        if self.trend is not None and self.trend % 2 == 0:
            raise ValueError(f"trend window must be an odd integer, got {self.trend}")
        if self.low_pass is not None and self.low_pass % 2 == 0:
            raise ValueError(f"low_pass window must be an odd integer, got {self.low_pass}")
        return self


class TrendDataPoint(BaseModel):
    """Single timestamp point containing full decomposed vectors and dynamic bounds."""
    timestamp: datetime
    actual_value: float = Field(..., description="Observed raw KPI value Y_t")
    expected_value: float = Field(..., description="Expected baseline Ŷ_t = T_t + S_t")
    trend_value: float = Field(..., description="Smoothed low-frequency trend T_t")
    seasonal_value: float = Field(..., description="Cyclic seasonal component S_t")
    residual_value: float = Field(..., description="Residual noise R_t = Y_t - T_t - S_t")
    lower_bound: float = Field(..., description="Dynamic lower confidence bound Ŷ_t - z * sigma_R")
    upper_bound: float = Field(..., description="Dynamic upper confidence bound Ŷ_t + z * sigma_R")
    robustness_weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Outer loop bisquare weight rho_t")
    is_imputed: bool = Field(default=False, description="True if timestamp value was interpolated prior to STL")
    is_anomaly: bool = Field(default=False, description="True if actual_value falls outside confidence bounds")
    z_score: float = Field(default=0.0, description="Statistical Z-score (Y_t - Ŷ_t) / sigma_R")


class STLDecompositionResult(BaseModel):
    """Complete container for STL decomposition output, diagnostics, and anomaly state."""
    kpi_id: str
    cadence: str = Field(..., description="Business cadence: hourly, daily, weekly, monthly, quarterly")
    period: int = Field(..., description="Period n_(p) used in decomposition")
    series_length: int = Field(..., description="Total observation count N")
    parameters_used: STLParameters
    residual_std: float = Field(..., description="Robust residual scale estimate sigma_R (MAD-based)")
    residual_mad: float = Field(..., description="Raw Median Absolute Deviation of residuals")
    trend_data: List[TrendDataPoint] = Field(..., description="Chronological list of decomposed trend points")
    latest_observed: float
    latest_expected: float
    latest_z_score: float
    latest_percentage_change: float
    is_anomaly_detected: bool
    anomaly_direction: Optional[Literal["SPIKE", "DROP"]] = None
```

---

### 5.2 Updated `app/orchestrator/state.py`

The LangGraph `InvestigationState` is updated to incorporate upstream time-series measurements and decomposition results:

```python
import operator
from typing import Annotated, TypedDict, List, Dict, Any, Optional
from datetime import datetime

from app.schemas.findings import AgentFinding
from app.schemas.movement import KPIMovementEvent
from app.schemas.diagnostic import DiagnosticPayload
from app.schemas.timeseries import STLDecompositionResult, TrendDataPoint


class RawMeasurement(TypedDict):
    timestamp: datetime
    value: float
    dimensions: Dict[str, str]


class InvestigationState(TypedDict, total=False):
    # Upstream Ingestion & Time-Series State
    kpi_id: str
    analysis_timestamp: datetime
    cadence: str
    raw_measurements: List[RawMeasurement]
    stl_result: Optional[STLDecompositionResult]
    
    # Anomaly Event & Multi-Agent Swarm State
    movement: Optional[KPIMovementEvent]
    findings: Annotated[List[AgentFinding], operator.add]
    analytical_results: List[Dict[str, Any]]
    contradictions: List[Dict[str, Any]]
    
    # Final Synthesized Diagnostic & Governance Payload
    diagnostic_payload: Optional[DiagnosticPayload]
```

---

### 5.3 Frontend Vega-Lite Visualizer Integration

The visualizer API in `frontend/Visualizers/api/main.py` utilizes `metadata.trend_data` from `DiagnosticPayload`. The `stl_evaluator_node` outputs serialized `TrendDataPoint` dictionaries directly matching this schema:

```json
{
  "incident_id": "EVT-REVENUE-202608301400",
  "kpi_id": "REVENUE",
  "observed_value": 18500.0,
  "expected_value": 24200.0,
  "percentage_change": -23.55,
  "drivers": [...],
  "uncertainty": {"status": "LOW", "abstain": false},
  "recommendations": [...],
  "metadata": {
    "cadence": "daily",
    "residual_std": 642.5,
    "trend_data": [
      {
        "timestamp": "2026-08-01T00:00:00Z",
        "actual_value": 22100.0,
        "expected_value": 22050.0,
        "trend_value": 21800.0,
        "seasonal_value": 250.0,
        "residual_value": 50.0,
        "lower_bound": 20790.7,
        "upper_bound": 23309.3,
        "is_imputed": false,
        "is_anomaly": false,
        "z_score": 0.078
      },
      {
        "timestamp": "2026-08-30T00:00:00Z",
        "actual_value": 18500.0,
        "expected_value": 24200.0,
        "trend_value": 23900.0,
        "seasonal_value": 300.0,
        "residual_value": -5700.0,
        "lower_bound": 22940.7,
        "upper_bound": 25459.3,
        "is_imputed": false,
        "is_anomaly": true,
        "z_score": -8.87
      }
    ]
  }
}
```

This data is rendered by the Vega-Lite specification in `frontend/Visualizers/api/main.py`:
- `layer[0]`: `errorband` between `lower_bound` and `upper_bound` with opacity `0.2`.
- `layer[1]`: `line` (dashed gray `#888`) for `expected_value`.
- `layer[2]`: `line` with points (blue `#1f77b4`) for `actual_value`.

---

## 6. Edge Case Handling & Statistical Failure Recovery

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           EDGE CASE DECISION & RECOVERY TREE                            │
└────────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                      ┌──────────────────────┴──────────────────────┐
                      ▼                                             ▼
          Series Length N < 2 * n_(p)?                   Gaps / Missing Timestamps?
              ├── YES: Gating / Holt-Winters Fallback       ├── Gap <= 3: Linear Interp
              │        Flag SPARSE_HISTORY in payload       ├── Gap > 3: Seasonal Lag Interp
              └── NO:  Proceed to STL                       └── Gap > 20%: Abort & DQ Alert
                                             │
                      ┌──────────────────────┴──────────────────────┐
                      ▼                                             ▼
          Zero / Negative Values in Multi?               Structural Break / Level Shift?
              ├── YES: Fallback to Additive Mode            ├── CUSUM / Persistent Run > 5
              └── NO:  Apply ln(Y_t) Log-STL                └── Tighten n_(t) / Trigger Alert
```

### 6.1 Sparse History ($N < 2 n_{(p)}$) & Cold Starts
- **Statistical Failure Mode**: When available history $N$ is less than two full seasonal cycles ($N < 2 n_{(p)}$), LOESS cycle-subseries smoothing cannot separate intra-cycle seasonality from macro trend drift due to rank deficiency in local design matrices.
- **Orchestrator Fallback Protocol**:
  1. If $N < n_{(p)}$: Abort STL. Fallback to Simple Exponential Smoothing (SES) or 3-period Rolling Moving Average ($\hat{Y}_t = \frac{1}{k}\sum_{i=1}^k Y_{t-i}$).
  2. If $n_{(p)} \le N < 2 n_{(p)}$: Execute **Holt-Winters additive exponential smoothing** with fixed seasonal indices.
  3. Mark state with `uncertainty.status = "SPARSE_HISTORY"`, `diagnostic_confidence = 0.50`, and append explanation to `DiagnosticPayload.uncertainty.reason`.

### 6.2 Missing Data Imputation & Grid Regularization
- **Statistical Failure Mode**: LOESS assumes strictly equidistant spatial sampling $\Delta t = \text{const}$. Missing records or temporal jitter introduce local distortion in polynomial kernel weights.
- **Pre-Processing Protocol**:
  1. Resample raw PostgreSQL measurements onto a strict monotonic grid using `pandas.date_range(start, end, freq=cadence_freq)`.
  2. For missing intervals of gap length $g \le 3$: Apply linear interpolation:
     $$\hat{Y}_{t+k} = Y_t + \frac{k}{g+1}(Y_{t+g+1} - Y_t) \quad \text{for } k=1,\dots,g$$
  3. For missing intervals of gap length $g > 3$: Apply **Seasonal-Lag Imputation**:
     $$\hat{Y}_t = Y_{t - n_{(p)}}$$
  4. Flag all interpolated records with `is_imputed = True` in `TrendDataPoint`.
  5. If total missing records exceed **$20\%$** of the time window: Abort STL decomposition, flag `DATA_QUALITY_ERROR`, quarantine the evaluation run, and dispatch an engineering alert.

### 6.3 Multiplicative Transformation & Zero-Inflation
- **Statistical Failure Mode**: Multiplicative decomposition requires $\ln(Y_t)$, which is undefined for $Y_t \le 0$.
- **Mitigation Protocol**:
  1. Inspect series minimum: $Y_{\min} = \min_{t=1}^N Y_t$.
  2. If $Y_{\min} \le 0$ and user requested `transform="multiplicative"`:
     - If series contains isolated zeros (e.g. daily new signups = 0 on holiday): Apply constant positive offset shift:
       $$Y'_t = Y_t + (|Y_{\min}| + 1.0)$$
     - If series is heavily zero-inflated ($>10\%$ zero values): Automatically fall back to **Additive STL** (`transform="additive"`), and append a transformation note to `DiagnosticPayload.lineage`.

### 6.4 Structural Breaks & Level Shifts
- **Statistical Failure Mode**: A permanent step-function level shift (e.g. server migration, pricing tier doubling) causes standard STL trend LOESS (with large window $n_{(t)}$) to smooth across the break, producing a persistent run of large residuals over multiple periods.
- **Mitigation Protocol**:
  1. Implement **CUSUM (Cumulative Sum)** residual monitoring:
     $$S_k = \sum_{t=1}^k (R_t - \bar{R})$$
  2. If a consecutive sequence of $m \ge 5$ residuals satisfies $\operatorname{sign}(R_t) = \text{const}$ and $|R_t| \ge 2.0 \cdot \sigma_R$:
     - Flag structural regime shift `STRUCTURAL_BREAK_DETECTED`.
     - Automatically re-estimate trend using an **Adaptive Trend Window** $n_{(t)}' = \max(n_{(p)}+1, \, \lfloor n_{(t)}/2 \rfloor_{\text{odd}})$.
     - Reset baseline reference to post-break mean.

### 6.5 Multiple Seasonalities (MSTL Extension)
- For sub-daily cadences exhibiting multiple nested seasonalities (e.g., hourly e-commerce with both intraday diurnal $n_{(p_1)}=24$ and weekly $n_{(p_2)}=168$ cycles):
- Execute **MSTL (Multiple Seasonal-Trend decomposition using LOESS)**:
  1. Iterate sequentially over seasonal period vectors $\mathbf{p} = [n_{(p_1)}, n_{(p_2)}]$.
  2. Step 1: Detrend and decompose for $n_{(p_1)}=24 \implies S_t^{(1)}$.
  3. Step 2: Subtract $S_t^{(1)}$ and decompose for $n_{(p_2)}=168 \implies S_t^{(2)}$.
  4. Composite baseline: $\hat{Y}_t = T_t + S_t^{(1)} + S_t^{(2)}$.

---

## 7. Objective Synthetic Verification & Mock Testing Suite

To ensure absolute mathematical integrity and verify the implementation objectively, a synthetic test suite is defined.

### 7.1 Synthetic Test Wave Generator Equation

We construct a 90-day daily synthetic time-series ($N = 90$, cadence = Daily, $n_{(p)} = 7$) with known deterministic ground-truth parameters:

$$Y_t = \underbrace{(1000 + 5.0 \cdot t)}_{\text{Ground Truth Trend } T_t^*} + \underbrace{200.0 \cdot \sin\left(\frac{2\pi t}{7}\right)}_{\text{Ground Truth Seasonality } S_t^*} + \underbrace{\epsilon_t}_{\text{Gaussian Noise } \mathcal{N}(0, 25^2)} + \underbrace{A_t}_{\text{Injected Anomaly}}$$

Where:
- $t = 1, 2, \dots, 90$.
- Injected Gaussian noise: $\epsilon_t \sim \text{i.i.d. } \mathcal{N}(0, \sigma_\epsilon^2)$ with known $\sigma_\epsilon = 25.0$ ($\sigma_\epsilon^2 = 625.0$).
- Injected Anomaly at index $t=85$: $A_{85} = -600.0$ (representing a severe $-41.8\%$ drop). For all $t \ne 85$, $A_t = 0.0$.

```
Synthetic Values at t=85:
- Ground Truth Trend:        T_85* = 1000 + 5(85) = 1425.0
- Ground Truth Seasonality:  S_85* = 200 * sin(2*pi*85/7) = 200 * sin(24.2857 * pi) = 200 * sin(0.2857 * pi) ≈ +156.4
- Expected Baseline:         Ŷ_85* = 1425.0 + 156.4 = 1581.4
- Injected Actual Value:     Y_85  = 1581.4 + (-600.0) + epsilon_85 ≈ 981.4
```

---

### 7.2 Mathematical Verification Assertions

The verification test harness validates 5 strict mathematical properties:

#### Assertion 1: Additive Orthogonality & Variance Preservation
Over the non-anomalous subset $\mathcal{T}_{\text{clean}} = \{t \in [1, 90] \mid t \ne 85\}$:
The residual variance $\operatorname{Var}(R_t)$ must closely track the known injected noise variance $\sigma_\epsilon^2 = 625.0$:

$$\left| \frac{\operatorname{Var}_{t \in \mathcal{T}_{\text{clean}}}(R_t) - 625.0}{625.0} \right| \le 0.15$$

And the sum of reconstructed components must satisfy exact arithmetic closure:

$$\max_{t=1}^{90} \left| Y_t - (T_t + S_t + R_t) \right| < 10^{-6}$$

#### Assertion 2: Outer Loop Bisquare Attenuation of Outlier
At the anomalous index $t=85$:
1. The estimated outer loop robustness weight must be fully nullified:
   $$\rho_{85} = 0.0$$
2. The estimated trend $T_{85}$ must resist corruption from the $-600.0$ shock, remaining within $5\%$ of the true linear progression $T_{85}^* = 1425.0$:
   $$\left| \frac{T_{85} - 1425.0}{1425.0} \right| \le 0.05 \iff 1353.75 \le T_{85} \le 1496.25$$

#### Assertion 3: Residual Residual White-Noise Properties
The remainder series on clean data $R_{\text{clean}}$ must be free of residual seasonal or trend autocorrelation.
- **Ljung-Box Autocorrelation Test**: For lag $k = 7$ (the seasonal period):
  $$Q(7) = N(N+2) \sum_{k=1}^7 \frac{r_k^2}{N-k} < \chi_{0.95}^2(7) = 14.067 \implies p\text{-value} > 0.05$$

#### Assertion 4: Anomaly Detection Trigger & Z-Score Magnitude
At index $t=85$:
1. The calculated robust scale $\sigma_R = 1.4826 \cdot \operatorname{MAD}(R)$ must satisfy $20.0 \le \sigma_R \le 30.0$.
2. The calculated anomaly score must satisfy:
   $$|Z_{85}| = \frac{|Y_{85} - \hat{Y}_{85}|}{\sigma_R} \ge 15.0 \gg 2.50$$
3. `is_anomaly_detected` must evaluate to `True`, triggering a `KPIMovementEvent` with `materiality_status = "CRITICAL"`.

#### Assertion 5: Visualizer Contract Schema Compliance
1. Output `trend_data` must contain exactly 90 serialized `TrendDataPoint` objects.
2. For all $t=1, \dots, 90$, $\text{lower\_bound}_t < \text{expected\_value}_t < \text{upper\_bound}_t$.
3. Exactly one point ($t=85$) has `is_anomaly = True`.
4. Schema validation against `frontend/Visualizers/api/main.py` succeeds without error.

---

## 8. Module-by-Module Code Layout & Step-by-Step Implementation Roadmap

### 8.1 File Structure Inventory

```
kpi-engine/
├── app/
│   ├── schemas/
│   │   ├── timeseries.py             # STLParameters, TrendDataPoint, STLDecompositionResult
│   │   ├── movement.py               # KPIMovementEvent schema
│   │   └── diagnostic.py             # DiagnosticPayload with metadata.trend_data
│   ├── timeseries/
│   │   ├── __init__.py
│   │   ├── stl.py                    # Pure Cleveland 1990 STL + statsmodels wrapper
│   │   ├── baseline.py               # Dynamic baseline, MAD sigma_R, confidence bounds
│   │   ├── regularizer.py            # Strict grid resampling & missing value imputation
│   │   └── anomaly.py                # Anomaly Z-scoring & KPIMovementEvent factory
│   ├── tools/
│   │   └── kpi.py                    # DB extraction tools for canonical_measurements
│   └── orchestrator/
│       ├── state.py                  # InvestigationState updated with stl_result
│       ├── nodes.py                  # kpi_extractor_node, stl_evaluator_node, agent nodes
│       └── graph.py                  # Upstream STL nodes wired before swarm fan-out
```

---

### 8.2 Step-by-Step Implementation Sequence

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: Dependencies & Base Schemas                                         │
│ - Add statsmodels>=0.14.0, scipy>=1.11.0, numpy>=1.24.0, pandas>=2.0.0       │
│ - Create app/schemas/timeseries.py with Pydantic contracts                  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: Time-Series Engine Core                                             │
│ - Implement app/timeseries/regularizer.py (grid alignment & imputation)     │
│ - Implement app/timeseries/stl.py (Cleveland STL with cadence mapping)      │
│ - Implement app/timeseries/baseline.py (MAD residual scale & bounds)        │
│ - Implement app/timeseries/anomaly.py (Z-score & KPIMovementEvent trigger)  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: Database Extraction Tools                                           │
│ - Implement app/tools/kpi.py querying PostgreSQL canonical_measurements     │
│ - Add fallback mock generator for isolated local testing                    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: Orchestrator Graph Upstream Wiring                                  │
│ - Add kpi_extractor_node and stl_evaluator_node to app/orchestrator/nodes.py │
│ - Update app/orchestrator/state.py with stl_result field                    │
│ - Wire START -> kpi_extractor -> stl_evaluator in app/orchestrator/graph.py  │
│ - Add conditional routing: trigger swarm if anomaly, end if baseline normal │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 5: Visualizer & Persona Delivery                                       │
│ - Populate DiagnosticPayload.metadata["trend_data"] from stl_result         │
│ - Validate Vega-Lite errorband chart rendering in Visualizers API           │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 6: Verification & Test Harness                                         │
│ - Implement tests/test_stl_decomposition.py executing synthetic 90-day wave│
│ - Assert variance recovery, outlier attenuation, and Z-score >= 15.0        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Conclusion & Deliverable Summary

This implementation plan establishes the complete, rigorous mathematical and architectural blueprint for **Requirement R2 (Orchestrator Completion via STL Decomposition using Loess)**:
1. **Upstream Integration**: Time-series extraction, grid regularizing, and STL anomaly scoring precede the LangGraph swarm.
2. **Mathematical Precision**: Full formulation of Cleveland et al. (1990) LOESS linear regression ($d=1$), tricube weights $W(u)$, 6-step inner loop, and Tukey bisquare robustness outer loop.
3. **5-Cadence Parameter Tuning**: Formal odd-integer window spans ($n_{(s)}, n_{(t)}, n_{(l)}$) derived for Hourly ($n_{(p)}=24$), Daily ($n_{(p)}=7$), Weekly ($n_{(p)}=52$), Monthly ($n_{(p)}=12$), and Quarterly ($n_{(p)}=4$) rhythms.
4. **Dynamic Bounds & Anomaly Triggering**: Expected baseline $\hat{Y}_t = T_t + S_t$ with robust $1.4826 \cdot \text{MAD}$ residual scale $\sigma_R$, dynamic confidence bands $[\hat{Y}_t \pm z \cdot \sigma_R]$, and dual Z-score/materiality event triggering.
5. **Contract Consistency**: Pydantic schemas seamlessly bridging the database, LangGraph state, and frontend Vega-Lite visualizers.
6. **No Contextual Debouncing**: Pure statistical and business materiality gating without heuristic alert suppression.
7. **Synthetic Verification Suite**: Objective mathematical assertions proving orthogonality, outlier bisquare attenuation, residual white-noise, and anomaly detection.
