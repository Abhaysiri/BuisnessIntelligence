# Business Intelligence Engine

An enterprise-grade, governed Business Intelligence (BI) platform that transforms KPI anomalies into explainable, evidence-backed root-cause diagnoses and policy-governed actions. The engine bridges the gap between raw metric data and business decisions through an automated medallion data pipeline, pure additive STL time-series anomaly detection, empirical causal attribution, a 1-pass diagnostic orchestrator, and an interactive React dashboard with embedded Vega-Lite visualizers.

---

## 1. System Architecture

The platform operates on a lean **2-Tier Topology** (Backend on `localhost:8000`, Frontend on `localhost:5173`):

```text
[ Data Sources: JSON / CSV / TSV / Parquet ]
                      │
                      ▼
┌───────────────────────────────────────────────────────────┐
│        Medallion Ingestion Gateway (FastAPI :8000)        │
│  ├─ Bronze Storage: raw_ingestions (Immutable + SHA-256)   │
│  ├─ 6-Tier Data Quality Validation Gate                    │
│  │    ├─ Pass  → Gold: canonical_measurements             │
│  │    └─ Fail  → DLQ:  quarantine_measurements            │
│  └─ Immediate HTTP 202 ACCEPTED (<1s)                      │
└───────────────────────────────────────────────────────────┘
                      │
                      ▼
┌───────────────────────────────────────────────────────────┐
│           Time-Series & Diagnostic Engine                 │
│  ├─ Adaptive STL Anomaly Detection (Pure Additive)        │
│  ├─ Dynamic 4-Lens Dimension Resolver                     │
│  │    (Offering, Actor, Location, Pathway)                │
│  ├─ Exact Shapley Factor Attribution (2^M Coalitions)     │
│  ├─ Qualitative Document Context RAG                      │
│  └─ 1-Pass Unified Diagnostic LLM Synthesis (~2s)         │
└───────────────────────────────────────────────────────────┘
                      │
                      ▼
┌───────────────────────────────────────────────────────────┐
│               GoRules Policy Governance                   │
│  ├─ Automated policy validation & risk scoring             │
│  └─ Decision Rights: ALLOWED vs. REQUIRES_HUMAN_REVIEW     │
└───────────────────────────────────────────────────────────┘
                      │
                      ▼
┌───────────────────────────────────────────────────────────┐
│             React Dashboard (Vite :5173)                  │
│  ├─ Multi-format Document & Metric Ingestion              │
│  ├─ Persona-Tailored Storytelling & Role Masking          │
│  ├─ Embedded Vega-Lite Charts (Driver Contribution, etc.) │
│  └─ Interactive Action Review Cards (Approve / Reject)    │
└───────────────────────────────────────────────────────────┘
```

---

## 2. Core Capabilities

| Capability | Technical Implementation |
|---|---|
| **Fast Micro-Batch Ingestion** | Ingests JSON, CSV, and TSV payloads with client-side header mapping and immediate HTTP 202 responses. |
| **Medallion Data Storage** | Immutable Bronze (`raw_ingestions` with SHA-256 deduplication), Silver normalization with Akima spline imputation, and Gold (`canonical_measurements`). |
| **Quarantine & Replay** | Dead-letter queue (`quarantine_measurements`) capturing structural/temporal violations with an administrative `/api/v1/quarantine/replay` endpoint. |
| **Pure Additive STL Engine** | Cleveland Additive decomposition ($Y_t = T_t + S_t + R_t$) preserving native metric units ($USD, counts, ms) with zero log math crashes. Adaptive thresholding runs STL when $N \ge 30$, or rolling baseline when $N < 30$. |
| **4-Lens Dimension Contract** | Deterministically projects datasets into 4 analytical archetypes: **Offering** (Product/Plan), **Actor** (Customer/User), **Location** (Region/DC), and **Pathway** (Channel/Source) via `kpi_definitions.dimension_mapping`. |
| **3-Step Empirical Causality** | Replaces brittle static DAGs with temporal precedence checks, first-order partial correlation, and exact Shapley coalition attribution ($2^M$ subsets). |
| **1-Pass Diagnostic LLM** | In-memory parallel dimensional extraction (<20ms) coupled with a single unified diagnostic LLM synthesis pass (~2s) that outputs root causes, uncertainty, and recommendations. |
| **Governed Action Review** | Policy evaluation sets decision rights (`ALLOWED` vs `REQUIRES_HUMAN_REVIEW`). Interactive dashboard cards allow one-click Approve, Reject, or Modify with reviewer notes. |
| **Interactive Visualizations** | Generates curated declarative Vega-Lite specifications (KPI Trend with Bounds, Driver Contribution Bar, Dimensional Breakdown) rendered directly via `<VegaEmbed />`. |

---

## 3. Technology Stack

- **Backend**: FastAPI, Uvicorn, Python 3.10+, Pydantic V2
- **Data & Math**: Polars, Pandas, NumPy, Statsmodels, SciPy, Zen-Engine (GoRules)
- **Database**: PostgreSQL (Supabase / local) with resilient local SQLite fallback
- **Frontend**: React 19, Vite, Tailwind CSS, Lucide React, `react-vega`, `vega-embed`
- **Testing**: Pytest, Typeguard, AnyIO

---

## 4. How to Run the Platform

Running **only two services** (`kpi-engine` and `frontend/Dashboard`) is fully sufficient:

### Prerequisites
1. Python 3.10+ installed.
2. Node.js 18+ and npm installed.

### Step 1: Configure Environment Variables
Inside `kpi-engine/.env`:
```env
DATABASE_URL=postgresql://<user>:<password>@<host>:5432/<dbname>
OPENAI_API_KEY=<your_openai_or_groq_api_key>
GROQ_API_KEY=<your_groq_api_key>
OPENAI_API_BASE=https://api.groq.com/openai/v1
OPENAI_MODEL=openai/gpt-oss-20b
GEMINI_API_KEY=<your_gemini_api_key>
LANGSMITH_TRACING=false
```
*(Note: If `DATABASE_URL` is omitted or PostgreSQL is unreachable, the engine automatically falls back to local SQLite `local_analytics.db` without crashing).*

---

### Step 2: Start the Backend Service (`kpi-engine`)

Open Terminal 1 in the repository root:

```powershell
cd kpi-engine
uvicorn app.main:api --reload --port 8000
```
- API starts at: `http://127.0.0.1:8000`
- Interactive Swagger docs: `http://127.0.0.1:8000/docs`

---

### Step 3: Start the Frontend Dashboard (`frontend/Dashboard`)

Open Terminal 2 in the repository root:

```powershell
cd frontend/Dashboard
npm run dev
```
- Web Dashboard starts at: `http://localhost:5173`

---

## 5. End-to-End Walkthrough (The Golden Path)

1. Open `http://localhost:5173` in your browser.
2. **Select Persona Role**: Choose your role (e.g. *Sales / Vice President of Sales* or *Marketing / VP of Marketing*).
3. **Upload Data** (`/upload-documents`):
   - Upload a `.json`, `.csv`, or `.tsv` metric file.
   - The file is validated across 6 tiers, committed to Bronze (`raw_ingestions`) & Gold (`canonical_measurements`), returning an immediate HTTP 202 response.
4. **Generate KPI Story** (`/kpi-analysis`):
   - Enter an analytical question or click a report filter (e.g., *"Analyze revenue decline"*).
   - The engine extracts all dimensional lenses, runs Shapley attribution, synthesizes the findings via the 1-pass LLM, and renders:
     - The tailored persona narrative.
     - The embedded interactive **Vega-Lite Driver Contribution** chart.
     - Governed **Action Review Cards** with Approve, Reject, and Modify buttons.
5. **Execute Governed Review**:
   - Click **Approve Action** or **Reject** on any recommendation to record human-in-the-loop decisions via `POST /api/v1/human-decisions/{recommendation_id}`.

---

## 6. Key API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health status and trace telemetry. |
| `POST` | `/api/v1/metrics/ingest` | Ingests micro-batches of measurements into Bronze/Silver/Gold. |
| `POST` | `/persona/story` | Generates tailored persona narrative with embedded Vega charts. |
| `POST` | `/persona/feedback` | Records human reviewer feedback (thumbs up/down, corrections). |
| `POST` | `/api/v1/human-decisions/{recommendation_id}` | Records Approve, Reject, or Modify decisions on governed recommendations. |
| `GET` | `/api/v1/human-decisions/history` | Retrieves audit history of human-in-the-loop decisions. |
| `POST` | `/api/v1/visualizations` | Generates curated Vega-Lite declarative specs for a diagnostic payload. |
| `POST` | `/api/v1/quarantine/replay` | Remediates and re-validates quarantined measurements into Gold. |
| `POST` | `/api/v1/timeseries/decompose` | Direct Cleveland additive STL decomposition and anomaly detection. |
| `GET` | `/api/v1/audit/ingestions` | Returns recent ingestion run logs and validation scores. |

---

## 7. Running Verification & Regression Suites

Run the unified test suites from the root directory:

```powershell
# Run the complete test suite (40 / 40 tests)
pytest tests/test_e2e_unified.py kpi-engine/tests/test_timeseries_stl.py edge_cases/test_edge_cases.py kpi-engine/tests/test_api_integration.py -v
```

To test the frontend build:
```powershell
npm --prefix frontend/Dashboard run build
```

---

## 8. Future Scopes

1. **Third-Party Ingestion Webhooks**: Direct native connectors for Stripe webhooks (`invoice.payment_failed`) and Databricks Delta Lake tables.
2. **Dynamic Specialist Agents**: User-defined plug-and-play analytical lenses configured via database metadata without backend redeployment.
3. **Automated Action Connectors**: Webhook triggers to dispatch approved operational actions directly to ticketing and orchestration systems (Jira, PagerDuty, Slack).

---

## 9. License

Proprietary and Confidential. Built for governed enterprise business intelligence.
