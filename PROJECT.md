# Project: Business Intelligence Engine

## Architecture
The Business Intelligence (BI) Engine is an enterprise-grade agentic diagnostic platform. The new systems to build comprise:
1. **Medallion Ingestion & Validity Layer**:
   - `data-ingest/`: Bronze (MinIO WORM storage) -> Silver (Polars normalization, ISO-8601 UTC timestamp regularization, dimension hash standardization, Akima/seasonal imputation).
   - `data-validity/`: 4-Tier active validation gate (Tier 1 Pydantic V2, Tier 2 Pandera DataFrameSchema, Tier 4 Boundary/Outlier, Tier 6 Drift KS-test/PSI), dead-letter quarantine store with replay API, composite DQ scoring algorithm coupled with GoRules Rule 23.
   - `data-validity/telemetry/`: GoldenDatasetSpec & 4-tier catalog, benchmark runner, TelemetryCollector aggregating all 7 hooks, model token pricing tables, non-blocking perf_counter hooks.
2. **Upstream STL Time-Series Engine**:
   - `kpi-engine/app/timeseries/`: Cleveland et al. LOESS STL using `statsmodels.tsa.seasonal.STL`, cadence parameter matrix across 5 business cadences (Hourly, Daily, Weekly, Monthly, Quarterly), dynamic expected baseline Ŷ_t = T_t + S_t, MAD residual uncertainty σ_R, 99% CI bands (z=2.576), anomaly detection Z-score & KPIMovementEvent emitter.
   - `kpi-engine/app/schemas/`: timeseries.py, ingestion.py, telemetry.py, scenarios.py, golden.py.
   - `kpi-engine/app/api/middleware.py`: TelemetryMiddleware & response headers.
   - `kpi-engine/app/api/routes.py`: /ingest and /quarantine/replay endpoints.
3. **Edge-Case Scenario Simulators**:
   - `edge_cases/`: Multi-factor Shapley attribution (Scenario 1), Low-confidence composite C_composite with clarification & abstention (Scenario 2), Sparse-history Bayesian prior borrowing (Scenario 3), Role-based security & PII masking (Scenario 4).
   - All runtime outputs print `[MOCK DATA] This output uses synthetic/simulated data. Replace with real ingested data.`.
4. **Frontend Upload Documents Page**:
   - `frontend/Dashboard/src/`: 2-column layout (Unstructured vs Structured data) with drag-and-drop zones, file type hints, toast notifications, Tailwind CSS styling, registered under React Router in App.jsx.
5. **E2E & Golden Regression Verification**:
   - Comprehensive test suite executing TC-1.1..TC-1.6, 90-day synthetic STL wave test (§3.8), 19 Golden Dataset benchmark evaluation (§5.1-5.2), and integration verification.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Bronze Ingestion | MinIO immutable storage partitioned by tenant/kpi/YYYY/MM/DD | M1 | §2.1 |
| 2 | Silver Cleansing | Polars type casting, ISO-8601 UTC regularization, dim_hash SHA256 | M1 | §2.1 |
| 3 | Time-Series Imputation | Akima spline (g<=3), seasonal persistence (3<g<=p), cold-start (>20%) | M1 | §2.5 |
| 4 | SQL DDL Statements | Canonical & quarantine DDL printed to console | M1 | §2.1, §2.3 |
| 5 | Tier 1 Validation | Pydantic V2 structural/type validation | M1 | §2.2 |
| 6 | Tier 2 Validation | Pandera DataFrameSchema columnar/categorical validation | M1 | §2.2 |
| 7 | Tier 4 Validation | Non-negative physical domain constraints & 6-sigma outlier screening | M1 | §2.2 |
| 8 | Tier 6 Drift Detection | Two-sample KS-test and PSI drift detection | M1 | §2.2 |
| 9 | Dead-Letter Quarantine | Quarantine store & replay API logic | M1 | §2.3 |
| 10 | Composite DQ Scoring | DQ score ∈ [0,1] mapped to VALID/DEGRADED/INVALID for Rule 23 | M1 | §2.4 |
| 11 | Telemetry Core | TelemetryCollector, pricing matrix, perf_counter decorators | M1 | §5.3, §5.4 |
| 12 | Golden Datasets & Benchmark | GoldenDatasetSpec schema, 19 incidents, benchmark runner | M1 | §5.1, §5.2 |
| 13 | Cadence Parameter Matrix | Parameters for Hourly, Daily, Weekly, Monthly, Quarterly | M2 | §3.4 |
| 14 | STL Engine | statsmodels.tsa.seasonal.STL decomposition wrapper | M2 | §3.1-3.5 |
| 15 | Dynamic Baseline & Bounds | Baseline Ŷ_t = T_t + S_t, MAD σ_R, 99% CI bands | M2 | §3.5 |
| 16 | Anomaly Z-Score & Event | Z-score computation & KPIMovementEvent emission | M2 | §3.5 |
| 17 | Time-Series Schemas | STLParameters, TrendDataPoint, STLDecompositionResult | M2 | §3.6 |
| 18 | API Integration & Middleware | TelemetryMiddleware (Hook 1), /ingest & /quarantine/replay routes | M2 | §5.4, §2.1 |
| 19 | Scenario 1 Multi-Factor | 3 concurrent drivers, exact Shapley value attribution | M3 | §4.1 |
| 20 | Scenario 2 Low-Confidence | Contradictory evidence, C_composite, clarification payload, Rule 20-22 | M3 | §4.2 |
| 21 | Scenario 3 Sparse-History | N<14 cold-start, Bayesian prior borrowing, widened credible interval | M3 | §4.3 |
| 22 | Scenario 4 Role Security | SecurityContext, multi-tenant AST query rewriting, PII masking | M3 | §4.4 |
| 23 | Frontend Upload Page | 2-column React page (Unstructured vs Structured), drag-drop, toasts | M3 | §6 |
| 24 | Verification Suite & Waves | TC-1.1..1.6, 90-day synthetic STL wave, Golden dataset evaluations | M4 | §2.6, §3.8, §5.2 |
| 25 | Forensic Integrity Audit | Systematic checks, zero mock masquerading, clean verdict | M5 | Auditing |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Ingestion & Validity Layer | `data-ingest/`, `data-validity/` | none | DONE |
| M2 | STL Engine & API Integration | `kpi-engine/app/timeseries/`, `kpi-engine/app/schemas/`, `kpi-engine/app/api/` | M1 | DONE |
| M3 | Edge Cases & Frontend Upload | `edge_cases/`, `frontend/Dashboard/src/` | M1 | DONE |
| M4 | Verification Suite & Benchmarks | Unit & E2E tests, 90-day wave, Golden catalog runner | M1, M2, M3 | DONE |
| M5 | Forensic Integrity Audit | Independent audit of all codebases & outputs | M4 | DONE |

## Code Layout
```
BuisnessIntelligence.ai/
├── data-ingest/
│   ├── pipeline.py
│   ├── bronze.py
│   ├── silver.py
│   └── imputation.py
├── data-validity/
│   ├── validation.py
│   ├── quarantine.py
│   ├── scoring.py
│   ├── golden_datasets.py
│   ├── benchmark_runner.py
│   └── telemetry/
│       ├── collector.py
│       ├── pricing.py
│       └── hooks.py
├── edge_cases/
│   ├── multifactor.py
│   ├── low_confidence.py
│   ├── sparse_history.py
│   └── role_security.py
├── kpi-engine/
│   ├── app/
│   │   ├── api/
│   │   │   ├── middleware.py
│   │   │   └── routes.py
│   │   ├── timeseries/
│   │   │   ├── stl.py
│   │   │   ├── baseline.py
│   │   │   ├── anomaly.py
│   │   │   └── parameters.py
│   │   └── schemas/
│   │       ├── timeseries.py
│   │       ├── ingestion.py
│   │       ├── telemetry.py
│   │       ├── scenarios.py
│   │       └── golden.py
│   └── tests/
└── frontend/
    └── Dashboard/
        └── src/
            ├── pages/
            │   └── UploadDocuments.jsx
            ├── App.jsx
            └── ...
```

## Interface Contracts
### Data Ingestion -> Data Validity
- Raw Payload Dict -> Bronze (MinIO URI) -> Silver Polars DataFrame -> Validation Gate (returns Validated DataFrame + DQ Score or Quarantine Record).

### Ingestion/Validity -> Time-Series Engine
- Clean Regularized Series (Pandas Series with DatetimeIndex / Polars DataFrame) -> STLDecompositionResult (Trend, Seasonal, Residual, Baseline, Anomaly Z-Score, Bounds).

### Scenario Simulators -> Presentation
- Simulation Runner -> Structured JSON Payloads with `[MOCK DATA]` logs.
