# Business Intelligence Engine

An enterprise-oriented KPI diagnostics platform that ingests business data, validates its quality, detects material time-series movement, identifies contributing drivers, and generates role-aware KPI narratives.

The project combines a Python/FastAPI backend with React dashboards for document ingestion, KPI storytelling, and visualizations.

## Highlights

- **Medallion ingestion**: immutable Bronze capture, Silver normalization, timestamp regularization, dimension hashing, and gap imputation.
- **Data-quality controls**: schema, dataframe, boundary/outlier, and distribution-drift validation; failed records can be quarantined and replayed.
- **KPI intelligence**: robust STL decomposition, dynamic baselines, confidence bands, anomaly scoring, and movement events.
- **Governed analysis**: confidence gating, sparse-history handling, multi-factor attribution, tenant isolation, and PII-aware role controls.
- **Persona storytelling**: LangGraph-driven, role-specific KPI narratives with traceable feedback.
- **Observability**: request traces, latency and cost telemetry, golden datasets, and regression benchmarks.

## Repository layout

```text
.
|-- data-ingest/                 # Bronze/Silver ingestion and imputation
|-- data-validity/               # Validation, scoring, quarantine, telemetry, benchmarks
|-- edge_cases/                  # Multi-factor, low-confidence, sparse-history, and security scenarios
|-- kpi-engine/                  # FastAPI service, orchestration, analytics, and time-series engine
|-- frontend/
|   |-- Dashboard/               # React dashboard and document upload experience
|   `-- Visualizers/             # Vega-Lite visualization service and React UI
|-- tests/                       # Unified end-to-end tests
|-- PROJECT.md                   # Feature inventory and implementation notes
`-- TEST_READY.md                # Detailed verification report
```

## Core workflow

1. A user selects a business domain and role in the dashboard.
2. The user selects a tenant and KPI, then stages structured or unstructured files.
3. Data progresses through Bronze storage, Silver cleansing, imputation, and data-quality validation.
4. Invalid records are quarantined for remediation and optional replay; accepted data creates a diagnostic payload.
5. The KPI engine decomposes time-series data, evaluates anomalies and drivers, and applies governance checks.
6. A persona-aware service produces a KPI story; users can submit feedback tied to the diagnostic trace.

## Architecture

### Ingestion and data quality

`data-ingest/` implements the Medallion pipeline:

- **Bronze**: immutable raw-payload capture, partitioned by tenant, KPI, and date.
- **Silver**: Polars-based normalization, ISO-8601 UTC regularization, and deterministic dimension hashes.
- **Imputation**: Akima interpolation for short gaps, seasonal persistence for medium gaps, and cold-start routing for insufficient history.

`data-validity/` supplies the validation gate:

- Tier 1 — structural and type checks.
- Tier 2 — dataframe schema and categorical checks.
- Tier 4 — physical bounds and outlier checks.
- Tier 6 — KS-test and PSI drift detection.
- Composite DQ status: `VALID`, `DEGRADED`, or `INVALID`.
- Dead-letter quarantine records and administrative replay.

### KPI diagnostics

The time-series engine in `kpi-engine/app/timeseries/` uses robust STL decomposition to calculate trend, seasonality, residuals, dynamic expected values, confidence bounds, and anomaly scores. The analytics and orchestration layers add evidence, contribution analysis, contradiction handling, and persona-specific explanations.

### Frontend applications

| Application | Location | Purpose |
|---|---|---|
| Dashboard | `frontend/Dashboard` | Persona onboarding, document/data upload, ingestion status, and KPI narrative requests. |
| Visualizers | `frontend/Visualizers/web` | Renders Vega-Lite KPI visualizations returned by the visualization API. |

## API

Start the KPI service from `kpi-engine`:

```powershell
uvicorn app.main:api --reload --port 8000
```

Main endpoints:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health check. |
| `POST` | `/investigations` | Runs an investigation for a KPI movement event. |
| `POST` | `/api/v1/metrics/ingest` | Accepts a batch of raw metric measurements for ingestion. |
| `POST` | `/api/v1/quarantine/replay` | Replays a remediated quarantined record. |
| `POST` | `/api/v1/timeseries/decompose` | Runs STL decomposition, baseline calculation, and anomaly detection. |
| `POST` | `/persona/story` | Generates a persona-tailored narrative for a diagnostic payload. |
| `POST` | `/persona/feedback` | Records feedback for a generated narrative. |

The service returns observability headers including `X-Trace-ID`, `X-Latency-MS`, and `X-Total-Cost-USD`.

## Getting started

### Prerequisites

- Python 3.11+ recommended
- Node.js 20+ and npm

### Backend

```powershell
cd kpi-engine
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:api --reload --port 8000
```

The complete time-series and validation test suites additionally use scientific/data packages such as NumPy, Pandas, Polars, SciPy, Statsmodels, and Pandera. Install the project environment dependencies used by your workflow before running those suites.

### Dashboard

In a separate terminal:

```powershell
cd frontend\Dashboard
npm install
npm run dev
```

Vite serves the dashboard locally (normally at `http://localhost:5173`). The frontend expects the KPI API on port `8000`.

### Visualizer UI

```powershell
cd frontend\Visualizers\web
npm install
npm run dev
```

The visualizer UI calls its visualization API at `http://localhost:8001/visualizations`.

## Quality and verification

Run the unified end-to-end suite from the repository root:

```powershell
pytest tests/test_e2e_unified.py -v
```

Additional focused checks:

```powershell
pytest edge_cases/test_edge_cases.py -v
pytest kpi-engine/tests -v

cd frontend\Dashboard
npm run build
npm run lint
```

The test coverage includes ingestion, validation, quarantine/replay, time-series decomposition, golden datasets, telemetry, confidence gating, sparse-history behavior, attribution, and role-based security. See `TEST_READY.md` for the recorded verification report.

## Data transparency

Several benchmarks and scenario simulators use synthetic data. Those execution paths emit the following notice:

```text
[MOCK DATA] This output uses synthetic/simulated data. Replace with real ingested data.
```

Treat mock and benchmark outputs as demonstration data, not production business results.

## Documentation

- `PROJECT.md` — capabilities, milestones, and component overview.
- `TEST_READY.md` — test readiness and verification details.
- `BI_ENGINE_IMPLEMENTATION_PLAN.md` — implementation plan and delivery notes.

## License

No license file is currently included. Add an explicit license before distributing or reusing this project outside its intended environment.
