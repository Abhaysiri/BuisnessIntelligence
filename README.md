# Business Intelligence Engine

An enterprise-oriented Business Intelligence (BI) platform for turning KPI movements into governed, explainable actions. The repository combines a medallion-style data pipeline, data-quality controls, time-series anomaly detection, diagnostic agents, role-aware governance, observability, and a React upload experience.

> **Prototype status.** The repository contains working implementation and test assets, but several operating paths deliberately use synthetic data or local/in-memory fallbacks. Runtime output labels simulated data with `[MOCK DATA]`. Treat the solution as a validated prototype baseline, not a production deployment.

## Why it exists

Teams often discover a KPI change late, cannot confidently identify its drivers, and may expose sensitive data or make ungoverned recommendations while investigating. This project provides one controlled flow:

`Raw measurements → trusted canonical data → detected KPI movement → evidence-backed diagnosis → policy-governed action`

## What the platform does

| Capability | Implementation in this repository |
|---|---|
| Ingest and standardize data | Bronze/Silver/Gold-style pipeline, timestamp normalization, dimension hashing, and time-series imputation. |
| Protect data quality | Six validation tiers: structure, schema/taxonomy, temporal integrity, domain/outlier checks, reconciliation, and distributional drift. |
| Isolate bad records | Dead-letter quarantine plus an administrative replay API. |
| Detect changes early | STL decomposition, cadence-aware parameters, dynamic baseline/confidence bounds, and Z-score anomaly events. |
| Explain a KPI movement | Product, customer, geography, and channel investigation agents; contribution, dependency, temporal, evidence, and contradiction checks. |
| Handle uncertainty responsibly | Confidence-based decision gates, clarification requests, abstention, and sparse-history Bayesian prior borrowing. |
| Enforce secure action | Tenant/region-scoped query rewriting, PII and margin masking, and role-based approval controls. |
| Measure reliability | Golden benchmark catalog, telemetry/cost collection, trace/latency/cost response headers, and automated test suites. |
| Make data entry approachable | React/Vite upload page for structured and unstructured data, with validation feedback and progress display. |

## Architecture at a glance

```text
Sources / uploads
       │
       ▼
Bronze storage → Silver normalization & imputation → Six-tier validity gate
       │                                               │
       │                                               └── Quarantine & replay
       ▼
Gold / canonical measurements
       │
       ▼
STL baseline + anomaly detection
       │
       ▼
Specialist diagnostic agents → evidence/contradiction checks → governed recommendation
       │                                                     │
       └────────────────── telemetry, benchmark & audit ────┘
```

## Repository map

```text
data-ingest/                 Medallion ingestion, Bronze/Silver processing, imputation
data-validity/               Six-tier validation, quarantine, DQ scoring, telemetry, benchmarks
kpi-engine/app/              FastAPI service, STL engine, orchestration, governance, schemas
edge_cases/                  Attribution, low-confidence, sparse-history, and security scenarios
frontend/Dashboard/          React + Vite upload interface
tests/                       Unified end-to-end tests
kpi-engine/tests/            Time-series and API integration tests
public-architecture-dia/     Architecture and user-flow visuals
PROJECT.md                   Detailed feature inventory and architecture notes
TEST_READY.md                Repository-authored verification report
```

## Key API surface

The FastAPI service exposes:

| Endpoint | Purpose |
|---|---|
| `GET /health` | Health check for the KPI service. |
| `POST /investigations` | Runs a KPI-movement diagnostic. |
| `POST /api/v1/metrics/ingest` | Receives one or more metric records for ingestion. |
| `POST /api/v1/quarantine/replay` | Replays a remediated quarantined record. |
| `POST /api/v1/timeseries/decompose` | Performs STL decomposition and anomaly analysis. |

# Step 1: Launch Supporting Infrastructure

### 1.1 Verify MinIO Object Store
Ensure the MinIO Docker container is running on port 19000:
```powershell
docker ps --filter "name=minio"
```
*(If not running, start with:)*
```powershell
docker run -d -p 19000:9000 -p 19001:9001 --name minio -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin minio/minio server /data --console-address ":9001"
```

---

## Step 2: Start Backend Services

### 2.1 Launch KPI Engine API
In Terminal 1:
```powershell
cd C:\Users\Abhay\Desktop\CODING\BuisnessIntelligence.ai\kpi-engine
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2.2 Launch Visualizers Microservice
In Terminal 2:
```powershell
cd C:\Users\Abhay\Desktop\CODING\BuisnessIntelligence.ai\frontend\Visualizers\api
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```
## Step 3: Launch Enterprise Frontend Dashboard

In Terminal 3:
```powershell
cd C:\Users\Abhay\Desktop\CODING\BuisnessIntelligence.ai\frontend\Dashboard
npm run dev
```
Open **`http://localhost:5173`** in your browser.

---

## Step 4: Direct Verification of Core Mathematical Engines

To demonstrate the underlying analytical algorithms from the command line:

### 1. STL Decomposition & 90-Day Synthetic Anomaly Detection
```powershell
cd C:\Users\Abhay\Desktop\CODING\BuisnessIntelligence.ai
python -c "import pandas as pd, numpy as np; from kpi_engine.app.timeseries.stl import STLDecompositionEngine; t = pd.date_range('2026-01-01', periods=90, freq='D'); y = 1000 + 5*np.arange(90) + 200*np.sin(2*np.pi*np.arange(90)/7) + np.random.normal(0, 15, 90); y[60] -= 600; df = pd.DataFrame({'timestamp': t, 'value': y}); res = STLDecompositionEngine.decompose_series(df, cadence='daily'); print(f'Anomaly Detected: {res.anomaly_detected}, Z-Score: {res.latest_z_score:.2f}')"
```

### 2. Multi-Factor Shapley Value Attribution Simulator
```powershell
python edge_cases/multifactor.py
```

### 3. Low-Confidence & Contradiction Resolution Engine
```powershell
python edge_cases/low_confidence.py
```

### 4. Sparse-History Cold Start Bayesian Prior Borrowing
```powershell
python edge_cases/sparse_history.py
```

### 5. Role-Based Security & Dynamic PII Redaction
```powershell
python edge_cases/role_security.py
```


The development server is expected at `http://localhost:5173` and is already permitted by the backend CORS configuration.


`TEST_READY.md` records a prior project run reporting 22/22 unified tests, 11/11 edge-case tests, 11/11 ingestion tests, a successful frontend build, and zero lint errors. Re-run these commands in your own environment before making release or production claims.

## Design principles

- **Data before conclusions:** diagnose only from validated data and retain quality status.
- **Explainability before action:** preserve evidence, contribution, dependency, and uncertainty signals.
- **Abstention is a feature:** low-confidence or contradictory evidence triggers clarification or human review.
- **Security by context:** tenant, region, persona, and field entitlements restrict both access and actions.
- **Transparent demonstrations:** synthetic and fallback data must remain explicitly labeled.

## Current limitations and next steps

1. Replace simulated/local fallback storage and synthetic benchmarks with managed production data services.
2. Wire the API ingestion route to the full medallion pipeline for every production request.
3. Configure secrets, identity, tenant isolation, observability backends, and CI/CD outside source code.
4. Add load, security, integration, and user-acceptance testing with real governed datasets.
5. Establish operational ownership, alert thresholds, incident response, and model/rule-change controls.

## Technology stack

Python, FastAPI, Pydantic, Polars, Pandera, pandas, SciPy, statsmodels, LangChain/LangGraph, Zen Engine, LangSmith, React, Vite, Tailwind CSS, and Oxlint.
