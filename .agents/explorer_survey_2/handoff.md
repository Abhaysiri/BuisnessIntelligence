# Handoff Report: Orchestrator Survey & Time-Series / STL Specification (R2)

**Sender**: Explorer 2 (`explorer_survey_2`)  
**Recipient**: Parent Orchestrator (`orchestrator_1` / `e16fd076-8d94-4a97-a7c1-2a4c07e7f050`)  
**Mission**: Requirement R2 — Orchestrator Completion (STL Decomposition using Loess) & Time-Series Algorithmic Specification  
**Type**: Hard Handoff (Task Complete)

---

## 1. Observation

Direct observations made during codebase inspection:
1. **Existing LangGraph Orchestration**:
   - `kpi-engine/app/orchestrator/graph.py` (lines 16-48) implements a fan-out / fan-in `StateGraph` running 4 domain agents (`product_agent`, `customer_agent`, `geography_agent`, `channel_agent`) in parallel from `START`, feeding findings into `analysis`, `contradictions`, `orchestrator`, `governance`, and `END`.
   - `kpi-engine/app/orchestrator/nodes.py` (lines 69-145) receives a pre-existing `KPIMovementEvent` from `state["movement"]` and synthesizes a `DiagnosticPayload`.
2. **Missing Time-Series Mathematics & Libraries**:
   - `kpi-engine/requirements.txt` (lines 1-12) includes `fastapi`, `uvicorn`, `pydantic`, `sqlalchemy`, `psycopg2-binary`, `langchain-openai`, `langchain-core`, `langgraph`, `zen-engine`, `networkx`. It does **not** contain `statsmodels`, `scipy`, `numpy`, `pandas`, or `polars`.
   - `kpi-engine/app/tools/kpi.py` is an empty 0-byte file.
   - Time-series decomposition (STL / Loess) is completely absent across the entire repository.
3. **Frontend Visualizer Expectations**:
   - `frontend/Visualizers/api/main.py` (lines 31-74, `build_kpi_trend`) expects `metadata.trend_data` containing `timestamp`, `actual_value`, `expected_value`, `lower_bound`, and `upper_bound`.
   - `frontend/Visualizers/web/src/App.jsx` (lines 37-43) demonstrates the frontend expectation for 30 days of time-series trend and bounds.
4. **Architecture Documentation**:
   - `public-architecture-dia/Complete technology architecture — backend + AI + data + monitoring.md` (lines 15, 38) explicitly specifies `statsmodels` for time-series mathematics and `Dagster` for data pipeline orchestration.

---

## 2. Logic Chain

1. **Premise**: The current system starts at the point where a `KPIMovementEvent` (with expected value, observed value, and statistical score) is already assumed to exist.
2. **Inference**: Without an upstream statistical baseline generator, the orchestrator cannot autonomously detect when a KPI has deviated, cannot quantify seasonality vs trend, and cannot supply `trend_data` bounds to the visualizer.
3. **Mathematical Solution**: STL (Seasonal and Trend decomposition using Loess) is the industry-standard algorithm (Cleveland et al., 1990) for separating additive/multiplicative time series into $T_t$ (Trend), $S_t$ (Seasonal), and $R_t$ (Remainder).
4. **Operational Integration**:
   - By running an upstream time-series extraction and STL decomposition node prior to agent fan-out, the orchestrator can:
     a. Dynamically estimate the expected baseline $\hat{Y}_t = T_t + S_t$.
     b. Compute the residual variance $\sigma_R$ and dynamic confidence bounds $[\hat{Y}_t \pm z \cdot \sigma_R]$.
     c. Automatically evaluate statistical anomaly score $Z_t = \frac{|Y_t - \hat{Y}_t|}{\sigma_R}$.
     d. Auto-generate `KPIMovementEvent` to trigger agent investigation only when movements are statistically material.
     e. Populate `metadata.trend_data` with decomposition components for Vega-Lite frontend visualization.

---

## 3. Caveats

- **Contextual Debouncing**: Per explicit instructions in Requirement R2, contextual debouncing was excluded from this specification.
- **Library Selection**: The specification recommends `statsmodels.tsa.seasonal.STL` as the primary engine with a clean mathematical fallback in pure Python/SciPy. If `statsmodels` is omitted to minimize container size, the explicit mathematical formulation provided in Section 3 of `survey_report.md` can be implemented natively.
- **MSTL for Multiple Seasonalities**: Single-season STL is specified as the baseline. If intraday (hourly) data with both 24-hr and 168-hr cycles is ingested, MSTL (Multiple STL) extension should be enabled.

---

## 4. Conclusion

Requirement R2 is fully researched and specified. The complete technical deliverable is documented in:
`c:\Users\Abhay\Desktop\CODING\BuisnessIntelligence.ai\.agents\explorer_survey_2\survey_report.md`

Key Deliverables in the Report:
1. Complete codebase inventory and gap analysis across orchestrator, analytics, and dependencies.
2. Full mathematical equations for LOESS (tricube weights, local WLS) and the two-loop iterative STL algorithm (inner detrend/subseries/lowpass/deseasonalize/trend loop + outer bisquare robustness loop).
3. Parameter specification table with Cleveland formulas for $n_{(p)}, n_{(s)}, n_{(t)}, n_{(l)}, n_{(i)}, n_{(o)}, d$ mapped to 5 business cadences (Hourly, Daily, Weekly, Monthly, Quarterly).
4. Interface contracts (`STLParameters`, `TrendDataPoint`, `STLDecompositionResult`, `InvestigationState`).
5. Edge case mitigation protocols (sparse history fallback, missing data imputation, zero/negative log transforms, structural breaks, outlier isolation).
6. Objective synthetic verification assertions.

---

## 5. Verification Method

To independently verify the findings and specifications:
1. **Codebase Inspection**:
   - Inspect `kpi-engine/requirements.txt` to verify missing time-series dependencies.
   - Inspect `kpi-engine/app/orchestrator/graph.py` and `app/orchestrator/nodes.py` to verify the entry point expecting `KPIMovementEvent`.
   - Inspect `frontend/Visualizers/api/main.py` lines 29-74 to verify `metadata.trend_data` consumption.
2. **Report Review**:
   - Review `c:\Users\Abhay\Desktop\CODING\BuisnessIntelligence.ai\.agents\explorer_survey_2\survey_report.md` for mathematical and algorithmic completeness.
3. **Mock Data Validation**:
   - Verify that the synthetic test equation $Y_t = (1000 + 5t) + 200 \sin(2\pi t / 7) + \epsilon_t + A_t$ produces the exact orthogonality and bisquare weight assertions detailed in Section 8.
