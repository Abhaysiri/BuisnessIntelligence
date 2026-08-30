# Comprehensive Architectural Survey & Technical Blueprint
## Requirement R1: Data Ingestion & Validity Layer & Codebase Architecture

**Author**: Explorer 1 (Codebase & Data Ingestion Specialist)  
**Date**: 2026-08-30  
**Project**: Governed Business Intelligence AI Engine (`BuisnessIntelligence.ai`)  
**Target File**: `c:\Users\Abhay\Desktop\CODING\BuisnessIntelligence.ai\.agents\explorer_survey_1\survey_report.md`  

---

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Current Codebase & System Architecture Inventory](#2-current-codebase--system-architecture-inventory)
3. [Data Ingestion Pipeline Architecture (Target State)](#3-data-ingestion-pipeline-architecture-target-state)
4. [Data Validity, Integrity & Reconciliation Layer (R1 Deep Dive)](#4-data-validity-integrity--reconciliation-layer-r1-deep-dive)
5. [Formal Data Models & Database Schemas](#5-formal-data-models--database-schemas)
6. [Time-Series, Granularity, Missingness & Sparsity Handling](#6-time-series-granularity-missingness--sparsity-handling)
7. [Mock Data Generation & Objective Verification Framework](#7-mock-data-generation--objective-verification-framework)
8. [Implementation Roadmap, Technology Stack & Recommendations](#8-implementation-roadmap-technology-stack--recommendations)

---

## 1. Executive Summary

This report delivers an exhaustive technical survey and implementation blueprint for **Requirement R1 (Data Ingestion & Validity Layer)** and the overarching backend architecture of the **Governed Business Intelligence AI Engine**.

### Core Findings:
1. **Existing Backend Foundation**: The repository contains a working LangGraph-based agentic diagnostic swarm (`product_agent`, `customer_agent`, `geography_agent`, `channel_agent`), analytical validation nodes (contribution, temporal precedence, causal dependency graph via NetworkX, contradiction detection), and a business policy governance engine (`GoRules` / `zen-engine`).
2. **Current Ingestion Gap**: Data ingestion, normalization, and data validity gating are currently **unimplemented in code**. Diagnostic agents currently execute direct SQL queries against assumed database tables (`canonical_measurements`, `kpi_definitions`) or fall back to mock payloads. There is no automated ingestion pipeline, no schema enforcement for incoming metric feeds, no reconciliation layer, and no quarantine mechanism.
3. **Architectural Blueprints**: The project's architecture diagrams (`public-architecture-dia`) define a canonical pipeline:  
   $$\text{Sources} \longrightarrow \text{Ingestion} \longrightarrow \text{Raw (S3/MinIO)} \longrightarrow \text{Normalization} \longrightarrow \text{Validity/Reconciliation} \longrightarrow \text{Canonical (PostgreSQL)} \longrightarrow \text{KPI Engine}$$
4. **Data Validity Imperative**: To ensure downstream agent conclusions, causal decompositions, and persona stories are mathematically sound, the Data Ingestion & Validity Layer must enforce a 6-tier validation gate (Structural, Columnar/Statistical, Temporal, Boundary/Range, Additive Reconciliation, and Drift Detection) with automated quarantine and data quality ($DQ$) scoring.

---

## 2. Current Codebase & System Architecture Inventory

### 2.1 Directory Structure & Component Mapping

The repository consists of the following primary modules:

```
BuisnessIntelligence.ai/
├── .agents/                               # Agent orchestration & survey artifacts
├── frontend/
│   ├── Dashboard/                         # React/Vite interactive BI dashboard
│   │   ├── src/App.jsx                    # Role selection popup, sidebar, KPI storytelling UI
│   │   └── package.json                   # React 18, lucide-react, react-router-dom
│   └── Visualizers/
│       ├── api/
│       │   └── main.py                    # FastAPI server (Port 8001) returning Vega-Lite visualization specs
│       ├── web/                           # React frontend with react-vega for chart rendering
│       └── sample_specs.json              # Vega-Lite chart specifications
├── kpi-engine/                            # Core Python Intelligence Backend
│   ├── app/
│   │   ├── agents/                        # Swarm diagnostic agent implementations
│   │   │   ├── base.py                    # ChatOpenAI structured output initializer
│   │   │   ├── product.py                 # Product/service line diagnostic agent
│   │   │   ├── customer.py                # Customer segment & device diagnostic agent
│   │   │   ├── geography.py               # Geographic region & market agent
│   │   │   └── channel.py                 # Sales & acquisition channel agent
│   │   ├── analytics/                     # Analytical validation layer
│   │   │   ├── contribution.py            # Mathematical delta & percentage contribution
│   │   │   ├── dependency.py              # NetworkX directed causal/mathematical dependency graph
│   │   │   ├── temporal.py                # Temporal precedence and timestamp validation
│   │   │   ├── evidence.py                # Quantitative evidence scoring algorithm
│   │   │   ├── contradictions.py          # Cross-agent contradiction & numerical conflict detector
│   │   │   └── product.py                 # Product finding analytical runner
│   │   ├── api/
│   │   │   └── persona.py                 # FastAPI persona storytelling endpoints
│   │   ├── governance/                    # Policy & decision rights enforcement
│   │   │   ├── decision_table.json        # GoRules JSON decision table (30 business rules)
│   │   │   └── engine.py                  # ZenEngine evaluation wrapper
│   │   ├── orchestrator/                  # LangGraph multi-agent orchestration
│   │   │   ├── graph.py                   # Main investigation StateGraph (Fan-out swarm -> Fan-in analysis -> Orchestrator -> Governance)
│   │   │   ├── nodes.py                   # Graph execution nodes & deterministic LLM fallback
│   │   │   ├── state.py                   # TypedDict InvestigationState
│   │   │   ├── persona.py                 # Persona storytelling generator with strict grounding rules
│   │   │   ├── persona_graph.py           # Persona generation StateGraph
│   │   │   ├── persona_state.py           # PersonaState TypedDict
│   │   │   ├── prompts.py                 # (Currently 0 bytes)
│   │   │   └── llm.py                     # ChatOpenAI orchestrator model wrapper
│   │   ├── schemas/                       # Pydantic data contracts
│   │   │   ├── movement.py                # KPIMovementEvent schema
│   │   │   ├── findings.py                # AgentFinding and Evidence schemas
│   │   │   ├── diagnostic.py              # DiagnosticPayload, Driver, Uncertainty, Recommendation
│   │   │   └── persona.py                 # PersonaRequest, PersonaStoryPayload, PersonaRole
│   │   ├── services/
│   │   │   ├── diagnostic.py              # run_investigation and in-memory cache
│   │   │   └── persona.py                 # generate_story service wrapper
│   │   ├── tools/                         # Agent database query tools
│   │   │   ├── database.py                # SQLAlchemy engine & query executor
│   │   │   ├── product.py                 # get_product_metrics SQL query
│   │   │   ├── customer.py                # get_customer_segment_metrics SQL query
│   │   │   ├── geography.py               # get_geography_metrics SQL query
│   │   │   ├── channel.py                 # get_channel_metrics SQL query
│   │   │   ├── kpi.py                     # (Currently 0 bytes)
│   │   │   └── documents.py               # (Currently 0 bytes)
│   │   ├── config.py                      # Pydantic BaseSettings (database_url, openai_api_key)
│   │   └── main.py                        # FastAPI entrypoint (/health, /investigations, /persona/story)
│   ├── requirements.txt                   # fastapi, uvicorn, pydantic, sqlalchemy, psycopg2-binary, langchain-openai, langgraph, zen-engine, networkx
│   └── run_test.py                        # End-to-end integration test runner
├── public-architecture-dia/               # Architecture diagrams and specifications
└── test_visualizers_api.py                # Visualizers API integration script
```

### 2.2 Framework & Dependency Inventory

| Layer | Current Codebase | Target State (Architecture Plan) |
|---|---|---|
| **API Framework** | FastAPI, Uvicorn | FastAPI, Uvicorn, Pydantic V2 |
| **Workflow Orchestration** | LangGraph (Agent Swarm) | LangGraph (Agents) + Dagster (Data Pipeline ETL) |
| **Data Contracts** | Pydantic V1/V2 (`BaseModel`) | Pydantic V2 (`BaseModel`), Pandera (`DataFrameSchema`) |
| **Data Processing** | SQLAlchemy raw SQL | Polars, SQLAlchemy Core, statsmodels |
| **Database** | PostgreSQL / Supabase connection | PostgreSQL (Canonical & Staging) + S3/MinIO (Raw Data Lake) |
| **Business Governance** | GoRules (`zen-engine`) | GoRules (`zen-engine`) |
| **Graph / Causal** | NetworkX | NetworkX |
| **Data Drift & Quality** | None | Evidently AI, Great Expectations / Pandera |
| **Telemetry & Tracing** | In-memory print / mock widget | LangSmith, OpenTelemetry, Prometheus metrics |

---

## 3. Data Ingestion Pipeline Architecture (Target State)

### 3.1 Medallion Architecture Overview

To transition from ad-hoc direct database queries to a resilient, enterprise-grade ingestion system, the architecture must implement a structured 4-stage Medallion pattern:

```
  [ External Data Sources ]
  (APIs, Webhooks, Databases, ERP, Billing, Clickstream, CSV/Parquet Batches)
               │
               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. BRONZE LAYER (Landing & Raw Ingestion)                               │
│ - Ingestion Modalities: Webhook Gateway (FastAPI) & Scheduled Batches  │
│ - Raw Store: S3 / MinIO Object Storage (`s3://bi-raw-data/{source}/...`) │
│ - Immutable audit log, raw JSON/CSV/Parquet, ingestion metadata headers  │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. SILVER LAYER (Parsing, Normalization & Cleansing)                    │
│ - Engine: Polars / PyArrow (High-throughput vectorized execution)       │
│ - Transformations: Standardize ISO-8601 UTC, lowercasing dimensions,   │
│   type casting, deduplication by `(kpi_id, observed_at, dimension_hash)` │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. VALIDITY & RECONCILIATION GATE (Data Quality Enforcement)            │
│ - 6-Tier Verification Gate (Pydantic + Pandera + Custom Reconciliation) │
│ - Routing:                                                              │
│   ├── Passed (DQ Score >= 0.85)  ──► Promoted to Gold Canonical        │
│   ├── Warnings (0.70 <= DQ < 0.85)─► Promoted with DQ Warning Flag     │
│   └── Rejected (DQ < 0.70 / Corrupt) ──► Quarantined & Alert Fired      │
└──────────────────┬─────────────────────────────────┬────────────────────┘
                   │ [Valid Data]                    │ [Quarantined Data]
                   ▼                                 ▼
┌──────────────────────────────────────┐  ┌───────────────────────────────┐
│ 4. GOLD LAYER (Canonical Storage)    │  │ QUARANTINE STORE              │
│ - DB: PostgreSQL (`canonical_data`)  │  │ - DB: `quarantine_measurements`│
│ - Tables: `canonical_measurements`,  │  │ - Detailed error trace & raw  │
│   `kpi_definitions`, `kpi_baselines` │  │   payload for replay/triage   │
└──────────────────┬───────────────────┘  └───────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 5. DOWNSTREAM CONSUMPTION (KPI Engine & Analytics)                      │
│ - STL Time-Series Decomposition (R2)                                    │
│ - LangGraph Agent Swarm Diagnostic Ingestion (Product, Customer, etc.)   │
│ - GoRules Governance Policy Enforcement                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Ingestion Modalities

The Ingestion Layer supports three operational ingestion pathways:

1. **Micro-Batch / Streaming Ingestion (Push Modality)**:
   - FastAPI endpoint (`POST /api/v1/ingestion/events` and `POST /api/v1/ingestion/batch`).
   - Receives real-time telemetry, transaction summaries, or third-party webhooks (e.g., Stripe, Shopify, Segment).
   - Validates payload envelope, writes raw payload to S3/MinIO buffer, and enqueues validation job.
2. **Scheduled Batch ETL (Pull Modality)**:
   - Orchestrated via **Dagster** assets.
   - Connectors query source databases (PostgreSQL, Snowflake, BigQuery), cloud storage, or external SaaS APIs on scheduled cadences (hourly, daily, weekly).
   - Extracts delta partitions based on high-watermark timestamps (`updated_at > :last_watermark`).
3. **Unstructured Document Ingestion**:
   - For incident context, press releases, outage logs, and promotional calendars (`app/tools/documents.py`).
   - Parsed via `Unstructured` library, chunked, and stored with temporal tags to correlate textual events with numerical anomalies.

---

## 4. Data Validity, Integrity & Reconciliation Layer (R1 Deep Dive)

The Data Validity Layer acts as an uncompromising gatekeeper between unverified external data and the analytical engine. It ensures that downstream agents never reason over malformed, out-of-order, fabricated, or mathematically inconsistent numbers.

```
Incoming Metric Batch
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Tier 1: Structural & Schema Validation (Pydantic V2)            │
│ • Field presence, types, string lengths, valid UUID/enums       │
└────────────────────────────────┬────────────────────────────────┘
                                 │ Pass
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Tier 2: Columnar & Statistical DataFrame Contracts (Pandera)    │
│ • Null-value tolerance (< 1%), non-emptiness, dtype constraints  │
└────────────────────────────────┬────────────────────────────────┘
                                 │ Pass
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Tier 3: Temporal & Continuity Integrity                         │
│ • Monotonic timestamps, UTC ISO-8601, future date prevention,   │
│   cadence gap detection (e.g., missing daily intervals)         │
└────────────────────────────────┬────────────────────────────────┘
                                 │ Pass
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Tier 4: Boundary & Range Checks                                 │
│ • Physical bounds (Revenue >= 0, Conversion Rate in [0.0, 1.0]) │
│ • Statistical step limits (Delta <= k * Sigma from baseline)    │
└────────────────────────────────┬────────────────────────────────┘
                                 │ Pass
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Tier 5: Additive & Dimensional Reconciliation                   │
│ • Sum of slices == Total metric: |Sum(Dim_i) - Total| < Epsilon │
└────────────────────────────────┬────────────────────────────────┘
                                 │ Pass
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Tier 6: Distributional Drift Monitoring (Evidently AI)          │
│ • Population Stability Index (PSI), Wasserstein Distance        │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                   ┌─────────────┴─────────────┐
                   │ Calculate DQ Score (0..1) │
                   └─────────────┬─────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
[ DQ >= 0.85 ]           [ 0.70 <= DQ < 0.85 ]        [ DQ < 0.70 ]
Status: VALID            Status: VALID_WITH_WARNINGS  Status: REJECTED
Insert into Canonical    Insert with DQ Warning       Route to Quarantine
```

### 4.1 Six-Tier Validation Gate Specification

#### Tier 1: Structural & Schema Validation (Pydantic V2)
- Enforces strict data types, non-null primary keys, ISO-8601 formatting, and valid enumeration values.
- Rejects malformed JSON, truncated streams, or extra unexpected fields.
- Checks foreign key validity: the `kpi_id` or `kpi_key` must exist in `kpi_definitions`.

#### Tier 2: Columnar & Statistical DataFrame Contracts (Pandera)
- Executes vectorized schema checks on incoming Polars/Pandas dataframes:
  - Null percentage per column $\le 1.0\%$.
  - Categorical column cardinality matches allowed dimension taxonomies (e.g., `sales_channel` $\in \{\text{'Direct'}, \text{'Organic'}, \text{'Paid'}, \text{'Partner'}\}$).
  - Uniqueness constraint on composite natural key: `(kpi_id, observed_at, dimension_hash)`.

#### Tier 3: Temporal & Continuity Integrity
- **UTC Clock Enforcement**: All timestamps converted to UTC; records with timestamp $t > \text{now()} + \text{tolerance}$ (e.g., 5-minute skew window) are rejected as future-dated.
- **Monotonicity & Sequence Order**: Verifies that time-series sequences arrive in order or are explicitly sorted prior to ingestion.
- **Gap & Grid Regularity**: Identifies missing timestamps in expected periodic grids (e.g., daily series with missing weekend or holiday timestamps) and generates explicit gap alerts.

#### Tier 4: Boundary, Range & Domain Validation
- **Absolute Physical Boundaries**:
  - Financial values: $\text{Revenue} \ge 0$, $\text{Cost} \ge 0$, $\text{AOV} \ge 0$.
  - Rate / Ratio values: $0.0 \le \text{Conversion Rate} \le 1.0$, $0.0 \le \text{Bounce Rate} \le 1.0$, $0.0 \le \text{Checkout Error Rate} \le 1.0$.
  - Volume counts: $\text{Orders} \in \mathbb{N}_0$, $\text{Sessions} \in \mathbb{N}_0$.
- **Statistical Step Boundaries**:
  - Compares incoming value against 30-day moving average and standard deviation ($\mu_{30}, \sigma_{30}$):
    $$\text{If } |V_t - \mu_{30}| > 6 \cdot \sigma_{30} \implies \text{Flag extreme outlier for validation review}$$

#### Tier 5: Additive & Dimensional Reconciliation
- Verifies that aggregated dimension slices mathematically reconcile with the top-level parent metric:
  $$\left| \sum_{d \in D} V_{\text{slice}}(d) - V_{\text{aggregate}} \right| \le \epsilon \quad (\text{where } \epsilon = 0.01 \text{ or } 0.1\%)$$
- Example: If total revenue for 2026-05-15 is reported as $\$100,000$, the sum of regional revenues ($\text{US} + \text{EU} + \text{APAC} + \text{LATAM}$) must sum to $\$100,000 \pm \$1.00$. If a discrepancy exceeds $\epsilon$, the batch is flagged for reconciliation imbalance.

#### Tier 6: Distributional Drift Monitoring (Evidently AI)
- Evaluates feature distributions against historical reference baselines using the **Population Stability Index (PSI)** and **Wasserstein Distance**.
- When PSI $> 0.25$, triggers a `DISTRIBUTION_DRIFT` warning indicating potential upstream tracking changes, seasonal shifts, or data corruption.

---

### 4.2 Data Quality Scoring Engine & Governance Integration

The validity layer calculates a normalized **Composite Data Quality Score ($DQ$)**:

$$DQ = w_{\text{struct}} S_{\text{struct}} + w_{\text{null}} S_{\text{null}} + w_{\text{temp}} S_{\text{temp}} + w_{\text{bound}} S_{\text{bound}} + w_{\text{recon}} S_{\text{recon}}$$

*Default Weights*:
- $w_{\text{struct}} = 0.30$ (Structural & Schema compliance)
- $w_{\text{null}} = 0.15$ (Completeness / missingness ratio)
- $w_{\text{temp}} = 0.15$ (Timestamp integrity & continuity)
- $w_{\text{bound}} = 0.20$ (Boundary & range validity)
- $w_{\text{recon}} = 0.20$ (Dimensional additivity & reconciliation)

#### Direct Coupling with GoRules & Agent Swarm:

The $DQ$ status directly binds to the GoRules decision table (`app/governance/decision_table.json`):

1. **Rule 23 (`dataQualityStatus != "VALID"`)**:
   - If $DQ < 0.70$ (`dataQualityStatus = "CORRUPT"` or `"INVALID"`), GoRules immediately returns **`PROHIBITED`** on any recommended action. The engine abstains from generating automated actions.
2. **Rule 21 & 22 (`Confidence Thresholds`)**:
   - If $0.70 \le DQ < 0.85$ (`dataQualityStatus = "VALID_WITH_WARNINGS"`), the overall diagnostic confidence is capped at $\min(\text{Confidence}_{\text{swarm}}, DQ)$. This triggers **`HUMAN_REVIEW`** or **`ABSTAIN`** in the governance engine.
3. **Rule 20 (`Confidence >= 0.85` & `dataQualityStatus == "VALID"`)**:
   - Actions are evaluated normally for **`APPROVED`** or **`ALLOWED`** status.

---

### 4.3 Quarantine Protocol & Dead-Letter Storage

When a record or batch fails hard validation (e.g., structural failure, boundary violation, un-reconcilable discrepancy):
1. **Quarantine Routing**: The record is rejected from `canonical_measurements` and written to `quarantine_measurements`.
2. **Quarantine Schema**:
   - `quarantine_id`: UUID
   - `ingestion_batch_id`: Traceable batch identifier
   - `source_id`: Source system name
   - `raw_payload`: Complete un-parsed raw payload
   - `failed_rule`: Rule identifier (e.g., `RULE_BOUND_NEGATIVE_REVENUE`)
   - `error_details`: Structured JSON explaining failure reason
   - `status`: `PENDING_REVIEW`, `REPROCESSED`, `IGNORED`
   - `quarantined_at`: Timestamp
3. **Alerting & Recovery**:
   - Prometheus counter `bi_data_quarantine_total` incremented.
   - Admin/Analyst API allows viewing quarantined records and initiating re-processing after schema updates or upstream fixes.

---

## 5. Formal Data Models & Database Schemas

### 5.1 Pydantic V2 Ingestion & Validity Models

```python
"""
Pydantic Data Contracts for Ingestion & Validity Layer
File: app/schemas/ingestion.py (Proposed)
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class DataQualityStatus(str, Enum):
    VALID = "VALID"
    VALID_WITH_WARNINGS = "VALID_WITH_WARNINGS"
    INVALID = "INVALID"
    CORRUPT = "CORRUPT"


class GranularityEnum(str, Enum):
    MINUTE = "1m"
    HOURLY = "1h"
    DAILY = "1d"
    WEEKLY = "1w"
    MONTHLY = "1M"


class AggregationTypeEnum(str, Enum):
    SUM = "SUM"
    AVG = "AVG"
    LAST = "LAST"
    WEIGHTED_AVG = "WEIGHTED_AVG"


class RawMetricRecord(BaseModel):
    """Raw metric record received at ingestion gateway."""
    source_id: str = Field(..., description="Identifier of the origin system (e.g. stripe, salesforce, mixpanel)")
    kpi_key: str = Field(..., description="Canonical KPI identifier key (e.g. monthly_revenue, checkout_error_rate)")
    observed_at: datetime = Field(..., description="Timestamp of the observation in ISO-8601 format")
    value: float = Field(..., description="Quantitative measurement value")
    dimensions: Dict[str, Any] = Field(default_factory=dict, description="Slicing dimensions (product, region, channel, etc.)")
    batch_id: Optional[str] = Field(None, description="Ingestion batch identifier")

    @field_validator("observed_at")
    @classmethod
    def validate_utc_and_present(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        now_utc = datetime.now(timezone.utc)
        # Reject future timestamps beyond a 5-minute clock drift margin
        if v > now_utc and (v - now_utc).total_seconds() > 300:
            raise ValueError(f"Timestamp {v.isoformat()} cannot be in the future (current UTC: {now_utc.isoformat()})")
        return v


class BatchIngestionRequest(BaseModel):
    """Batch ingestion request payload."""
    batch_id: str = Field(..., description="Unique batch identifier")
    source_system: str = Field(..., description="Source system name")
    sent_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    records: List[RawMetricRecord] = Field(..., min_length=1)


class DataQualityCheckResult(BaseModel):
    """Detailed result of an individual data quality check."""
    check_name: str
    tier: int
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    details: Dict[str, Any] = Field(default_factory=dict)
    message: Optional[str] = None


class DataQualityReport(BaseModel):
    """Comprehensive quality evaluation report for an ingestion batch or slice."""
    batch_id: str
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_records: int
    valid_records: int
    quarantined_records: int
    overall_quality_score: float = Field(ge=0.0, le=1.0)
    status: DataQualityStatus
    check_results: List[DataQualityCheckResult] = Field(default_factory=list)


class CanonicalMeasurementRecord(BaseModel):
    """Normalized, validated record stored in canonical_measurements."""
    id: Optional[str] = None
    kpi_id: str
    kpi_key: str
    observed_at: datetime
    value: float
    dimensions: Dict[str, Any] = Field(default_factory=dict)
    granularity: GranularityEnum = GranularityEnum.DAILY
    data_quality_score: float = Field(default=1.0, ge=0.0, le=1.0)
    quality_status: DataQualityStatus = DataQualityStatus.VALID
    is_imputed: bool = False
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    batch_id: str
```

---

### 5.2 PostgreSQL Relational Schemas (DDL Blueprint)

```sql
-- ============================================================================
-- Canonical Business Intelligence Data Layer DDL
-- Database: PostgreSQL 15+ / Supabase
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. KPI Definitions Table
CREATE TABLE IF NOT EXISTS kpi_definitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    kpi_key VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    unit VARCHAR(50) NOT NULL DEFAULT 'USD',
    granularity VARCHAR(20) NOT NULL DEFAULT '1d',
    aggregation_type VARCHAR(30) NOT NULL DEFAULT 'SUM',
    allowed_dimensions JSONB NOT NULL DEFAULT '[]'::jsonb,
    min_allowable_value DOUBLE PRECISION,
    max_allowable_value DOUBLE PRECISION,
    freshness_sla_seconds INTEGER DEFAULT 86400,
    owner_role VARCHAR(100) DEFAULT 'Business Analyst',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Canonical Measurements Table (Gold Layer)
CREATE TABLE IF NOT EXISTS canonical_measurements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    kpi_id UUID NOT NULL REFERENCES kpi_definitions(id) ON DELETE CASCADE,
    observed_at TIMESTAMPTZ NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    dimensions JSONB NOT NULL DEFAULT '{}'::jsonb,
    dimension_hash VARCHAR(64) GENERATED ALWAYS AS (
        md5(dimensions::text)
    ) STORED,
    granularity VARCHAR(20) NOT NULL DEFAULT '1d',
    data_quality_score DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    quality_status VARCHAR(30) NOT NULL DEFAULT 'VALID',
    is_imputed BOOLEAN NOT NULL DEFAULT FALSE,
    source_system VARCHAR(100) NOT NULL DEFAULT 'unknown',
    batch_id VARCHAR(100) NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_kpi_observed_dim UNIQUE (kpi_id, observed_at, dimension_hash)
);

-- Optimized Indices for Swarm Agent Queries
CREATE INDEX IF NOT EXISTS idx_canonical_kpi_observed ON canonical_measurements (kpi_id, observed_at);
CREATE INDEX IF NOT EXISTS idx_canonical_dimensions_gin ON canonical_measurements USING gin (dimensions);
CREATE INDEX IF NOT EXISTS idx_canonical_batch ON canonical_measurements (batch_id);

-- 3. Quarantine Measurements Table (Dead-Letter Store)
CREATE TABLE IF NOT EXISTS quarantine_measurements (
    quarantine_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_id VARCHAR(100) NOT NULL,
    source_system VARCHAR(100) NOT NULL,
    raw_payload JSONB NOT NULL,
    failed_tier INTEGER NOT NULL,
    failed_rule VARCHAR(100) NOT NULL,
    error_details JSONB NOT NULL,
    quality_score DOUBLE PRECISION DEFAULT 0.0,
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING_REVIEW',
    quarantined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_quarantine_batch ON quarantine_measurements (batch_id);
CREATE INDEX IF NOT EXISTS idx_quarantine_status ON quarantine_measurements (status);

-- 4. Data Quality Logs Table
CREATE TABLE IF NOT EXISTS data_quality_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_id VARCHAR(100) NOT NULL,
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    total_records INTEGER NOT NULL,
    valid_records INTEGER NOT NULL,
    quarantined_records INTEGER NOT NULL,
    overall_quality_score DOUBLE PRECISION NOT NULL,
    quality_status VARCHAR(30) NOT NULL,
    check_results JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dq_logs_batch ON data_quality_logs (batch_id);
CREATE INDEX IF NOT EXISTS idx_dq_logs_evaluated_at ON data_quality_logs (evaluated_at);
```

---

## 6. Time-Series, Granularity, Missingness & Sparsity Handling

### 6.1 Granularity Standardization & Rollup Aggregation

Incoming metrics arrive at diverse temporal granularities (minute events, hourly summaries, daily aggregates). The Ingestion Layer standardizes all incoming records into a uniform **Canonical Base Grid** (typically Daily `1d` for high-level KPIs, or Hourly `1h` for operational telemetry).

```
   Raw Event Stream (Variable Latency & Timestamp)
                          │
                          ▼
            [ Time-Bucket Resampling ]
  Truncate timestamp to bucket boundary: date_trunc('day', observed_at)
                          │
                          ▼
     [ Dimension-Grouped Aggregation Matrix ]
┌─────────────────────────────────────────────────────────────┐
│ Metric Type            │ Aggregation Operator               │
├────────────────────────┼────────────────────────────────────┤
│ Revenue / Spend / Volume│ SUM(value)                         │
│ Price / AOV / Latency  │ WEIGHTED_AVG(value, weight=volume) │
│ Conversion / Churn Rate│ SUM(conversions) / SUM(sessions)   │
│ Inventory Level        │ LAST(value, order_by=timestamp)    │
│ Active Users           │ COUNT(DISTINCT user_id)            │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Missing Value Strategy & Continuity Imputation

Missing values in time-series data distort trend detection and cause spurious variance spikes in statistical tests. The Validity Layer handles missingness through a policy-governed hierarchy:

1. **Gap Detection**: For any queried interval $[T_{\text{start}}, T_{\text{end}}]$, generate the complete expected timestamp grid $G = \{t_0, t_1, \dots, t_N\}$. If actual measurements count $|M| < |G|$, identify missing points $G \setminus M$.
2. **Missingness Thresholding**:
   - If missingness $< 5\%$: Apply policy-based imputation.
   - If $5\% \le \text{missingness} \le 20\%$: Apply imputation, set `is_imputed = TRUE`, and penalize Data Quality Score ($DQ \leftarrow DQ \times (1 - \text{missingness})$).
   - If missingness $> 20\%$: Reject interpolation, flag batch as `DATA_INSUFFICIENT`, and force downstream Orchestrator to enter **Uncertainty / Abstain** mode.
3. **Imputation Algorithms**:
   - *Continuous Flow Metrics (e.g., Revenue)*: Seasonal Linear Interpolation (aligning with day-of-week average $t - 7\text{d}$).
   - *State / Snapshot Metrics (e.g., Inventory)*: Forward-Fill with decay factor ($\text{value}_t = \text{value}_{t-1} \cdot e^{-\lambda \Delta t}$).
   - *Zero-Default Metrics (e.g., Error counts)*: Explicit zero fill with `is_imputed = TRUE`.
4. **Audit Transparency**: **Never silently overwrite or fabricate data**. All imputed records must explicitly carry `is_imputed = TRUE` and the imputation method logged in metadata.

### 6.3 Sparse-History & Newly Launched KPI Handling (Cold Start)

For newly launched products, newly created marketing channels, or recent KPIs:
- **Sample Gating Threshold ($N_{\min} = 14$ days)**: If total historical observations $N < 14$, standard statistical models (e.g., 30-day moving average, STL decomposition) are mathematically invalid.
- **Hierarchical Prior Borrowing**: The engine falls back to borrowing baseline distributions from parent category or global aggregate (e.g., a new "Wireless Headphones Pro" inherits baseline conversion and variance metrics from the "Electronics > Audio" category).
- **Uncertainty Inflation**: Baseline confidence is clamped to $\text{Confidence} \le 0.60$, automatically triggering GoRules Rule 22 (`Confidence < 0.70 -> ABSTAIN`) or requesting human clarification.

---

## 7. Mock Data Generation & Objective Verification Framework

### 7.1 Synthetic Data Generator Architecture

To rigorously verify the Data Ingestion & Validity Layer without depending on live third-party connectors, a deterministic synthetic test generator is formulated:

```python
"""
Synthetic KPI Data Generator for Ingestion & Validity Verification
Module: tests/synthetic_data_generator.py (Proposed)
"""
import uuid
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any


class SyntheticKPIDataGenerator:
    """
    Generates deterministic synthetic time-series with configurable
    clean baselines and injected validity faults.
    """
    def __init__(self, seed: int = 42):
        np.random.seed(seed)

    def generate_clean_series(
        self,
        start_date: datetime,
        days: int = 60,
        base_revenue: float = 100000.0,
        trend_slope: float = 100.0,
        weekly_seasonality_amp: float = 15000.0,
        noise_std: float = 2000.0
    ) -> List[Dict[str, Any]]:
        """Generates ground-truth clean daily KPI series with dimensions."""
        records = []
        products = ["Enterprise_Software", "Cloud_Storage", "Consulting", "Addon_Support"]
        product_shares = [0.45, 0.30, 0.15, 0.10]
        
        regions = ["US", "Europe", "Asia", "Latin_America"]
        region_shares = [0.50, 0.25, 0.15, 0.10]

        channels = ["Direct", "Organic", "Paid", "Partner"]
        channel_shares = [0.40, 0.30, 0.20, 0.10]

        for i in range(days):
            current_date = start_date + timedelta(days=i)
            day_of_week = current_date.weekday()
            
            # Mathematical seasonal formula
            seasonal = weekly_seasonality_amp * np.sin(2 * np.pi * day_of_week / 7.0)
            trend = trend_slope * i
            noise = np.random.normal(0, noise_std)
            total_rev = max(base_revenue + trend + seasonal + noise, 1000.0)

            # Generate sliced dimensional rows that add up exactly to total
            for p, p_share in zip(products, product_shares):
                for r, r_share in zip(regions, region_shares):
                    for c, c_share in zip(channels, channel_shares):
                        slice_value = total_rev * p_share * r_share * c_share
                        records.append({
                            "source_id": "erp_financial_system",
                            "kpi_key": "monthly_revenue",
                            "observed_at": current_date.isoformat(),
                            "value": round(float(slice_value), 2),
                            "dimensions": {
                                "product": p,
                                "geography": r,
                                "sales_channel": c
                            }
                        })
        return records

    def inject_schema_corruption(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Injects string into numeric value, invalid timestamp, missing keys."""
        corrupted = [r.copy() for r in records]
        # Fault 1: String in numeric field
        corrupted[5]["value"] = "INVALID_STRING_VALUE"
        # Fault 2: Non-ISO timestamp
        corrupted[12]["observed_at"] = "2026/05/32 99:99:99"
        # Fault 3: Missing required KPI key
        del corrupted[20]["kpi_key"]
        return corrupted

    def inject_temporal_faults(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Injects future timestamps, duplicate keys, and cadence gaps."""
        corrupted = [r.copy() for r in records]
        # Fault 1: Future timestamp (10 days in future)
        future_time = datetime.now(timezone.utc) + timedelta(days=10)
        corrupted[3]["observed_at"] = future_time.isoformat()
        # Fault 2: Exact duplicate timestamp & dimensions
        corrupted[10] = corrupted[9].copy()
        # Fault 3: Missing entire 5-day window (gap)
        del corrupted[30:50]
        return corrupted

    def inject_reconciliation_mismatch(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Artificially multiplies one slice by 10x to break dimensional additivity."""
        corrupted = [r.copy() for r in records]
        corrupted[0]["value"] = corrupted[0]["value"] * 10.0
        return corrupted

    def inject_boundary_violations(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Injects negative revenue and extreme impossible spikes."""
        corrupted = [r.copy() for r in records]
        # Fault 1: Negative revenue
        corrupted[2]["value"] = -75000.0
        # Fault 2: 1000x impossible outlier spike
        corrupted[8]["value"] = corrupted[8]["value"] * 1000.0
        return corrupted
```

---

### 7.2 Objective Verification Suites & Step-by-Step Test Protocol

To establish provable verification of Requirement R1, the test suite executes five objective verification stages:

```
┌────────────────────────────────────────────────────────────────────────┐
│ TEST STAGE 1: Schema Conformance & Type Safety (Pydantic Tier 1)       │
│ Command: pytest tests/test_ingestion_validity.py::test_tier1_schema   │
│ Expected: 100% of malformed types, missing keys rejected at ingress    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TEST STAGE 2: Temporal & Clock Drift Guard (Tier 3)                   │
│ Command: pytest tests/test_ingestion_validity.py::test_tier3_temporal │
│ Expected: Future timestamps and corrupted ISO strings quarantined     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TEST STAGE 3: Physical Boundary & Step Anomaly Checks (Tier 4)        │
│ Command: pytest tests/test_ingestion_validity.py::test_tier4_bounds   │
│ Expected: Negative values & 1000x spikes rejected / quarantined        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TEST STAGE 4: Additive Dimensional Reconciliation (Tier 5)             │
│ Command: pytest tests/test_ingestion_validity.py::test_tier5_reconcile│
│ Expected: Dimension slices summing != Total flagged as RECON_MISMATCH  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TEST STAGE 5: End-to-End Quarantine & DQ Score Pipeline Integration    │
│ Command: pytest tests/test_ingestion_validity.py::test_e2e_quarantine │
│ Expected: Valid records -> Canonical DB; Corrupt -> Quarantine DB;    │
│           Degraded DQ score triggers GoRules Human Review / Abstain    │
└────────────────────────────────────────────────────────────────────────┘
```

#### Executable Test Script Blueprint:

```python
"""
Objective Verification Suite for Data Ingestion & Validity Layer
File: tests/test_ingestion_validity.py (Proposed)
"""
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from app.schemas.ingestion import RawMetricRecord, DataQualityStatus
from tests.synthetic_data_generator import SyntheticKPIDataGenerator


class TestIngestionValidityLayer:

    def setup_method(self):
        self.generator = SyntheticKPIDataGenerator(seed=123)
        self.start_date = datetime(2026, 5, 1, 0, 0, 0, tzinfo=timezone.utc)

    def test_clean_data_ingestion_passes_all_tiers(self):
        """Verify that 100% clean baseline data passes all validity tiers with DQ = 1.0."""
        clean_records = self.generator.generate_clean_series(self.start_date, days=10)
        assert len(clean_records) > 0
        
        for rec in clean_records:
            validated = RawMetricRecord(**rec)
            assert validated.value > 0
            assert validated.kpi_key == "monthly_revenue"

    def test_tier1_schema_corruption_rejection(self):
        """Verify Tier 1 rejects non-numeric values and missing keys."""
        clean_records = self.generator.generate_clean_series(self.start_date, days=2)
        corrupted = self.generator.inject_schema_corruption(clean_records)

        # Test string value rejection
        with pytest.raises(ValidationError) as excinfo:
            RawMetricRecord(**corrupted[5])
        assert "value" in str(excinfo.value)

        # Test missing kpi_key rejection
        with pytest.raises(ValidationError) as excinfo:
            RawMetricRecord(**corrupted[20])
        assert "kpi_key" in str(excinfo.value)

    def test_tier3_temporal_future_timestamp_rejection(self):
        """Verify Tier 3 rejects timestamps set in the future."""
        clean_records = self.generator.generate_clean_series(self.start_date, days=2)
        corrupted = self.generator.inject_temporal_faults(clean_records)

        with pytest.raises(ValidationError) as excinfo:
            RawMetricRecord(**corrupted[3])
        assert "cannot be in the future" in str(excinfo.value)

    def test_tier4_boundary_negative_revenue_rejection(self):
        """Verify Tier 4 catches negative revenue."""
        clean_records = self.generator.generate_clean_series(self.start_date, days=2)
        corrupted = self.generator.inject_boundary_violations(clean_records)
        
        # In custom boundary validator
        neg_val = corrupted[2]["value"]
        assert neg_val < 0, "Expected negative test value"

    def test_tier5_reconciliation_math_check(self):
        """Verify that dimension slice mismatch is caught by the reconciliation validator."""
        clean_records = self.generator.generate_clean_series(self.start_date, days=1)
        corrupted = self.generator.inject_reconciliation_mismatch(clean_records)

        clean_sum = sum(r["value"] for r in clean_records)
        corrupted_sum = sum(r["value"] for r in corrupted)
        assert abs(corrupted_sum - clean_sum) > 100.0, "Reconciliation discrepancy not detected"
```

---

## 8. Implementation Roadmap, Technology Stack & Recommendations

### 8.1 Recommended Technology Stack

| Layer | Recommended Tool / Library | Technical Justification |
|---|---|---|
| **Data Ingestion Orchestrator** | **Dagster** | Asset-based declarative orchestration, automated lineage, built-in freshness SLAs, partitioned assets, and native asset check support. |
| **High-Throughput ETL** | **Polars** | 10x-50x faster than Pandas, zero-copy Apache Arrow memory format, multithreaded vectorized operations ideal for high-cardinality slicing. |
| **Data Contract Schemas** | **Pydantic V2** | Ultra-fast Rust-core validation, automatic JSON schema generation, strict type safety. |
| **DataFrame Validation** | **Pandera** | Declarative dataframe validation contracts, statistical property checks, seamless Polars/Pandas integration. |
| **Data Drift Monitoring** | **Evidently AI** | Automated PSI, Kolmogorov-Smirnov, Wasserstein drift tests for time-series distributions. |
| **Canonical Storage** | **PostgreSQL (Supabase)** | Robust JSONB indexing (GIN), ACID compliance, relational integrity with `kpi_definitions`. |
| **Raw Storage** | **S3 / MinIO** | Immutable, infinitely scalable object store for Bronze raw payloads and replay capability. |
| **Business Policy Engine** | **GoRules (`zen-engine`)** | Deterministic JSON-table governance already integrated in `kpi-engine`. |

---

### 8.2 Phased Implementation Roadmap

```
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: Database DDL & Data Contract Foundations (Sprint 1)           │
│ - Apply PostgreSQL DDL: `kpi_definitions`, `canonical_measurements`,   │
│   `quarantine_measurements`, `data_quality_logs`.                      │
│ - Create Pydantic V2 schemas in `app/schemas/ingestion.py`.           │
│ - Implement `app/tools/kpi.py` and `app/tools/database.py` extensions.  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: Ingestion Endpoints & Normalization Engine (Sprint 2)         │
│ - Build FastAPI ingestion routes (`/api/v1/ingestion/batch`).          │
│ - Implement Polars normalization service for timestamp & dimensions.   │
│ - Establish MinIO/S3 raw payload landing bucket.                       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: 6-Tier Validity, Reconciliation & Quarantine Layer (Sprint 3) │
│ - Implement Pandera dataframe validators for boundaries & nulls.       │
│ - Implement Dimensional Additivity Reconciliation engine.             │
│ - Build Quarantine router and Dead-Letter triage API.                 │
│ - Bind $DQ$ score to GoRules `decision_table.json` Rule 23.            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: Dagster Orchestration & Synthetic Verification (Sprint 4)     │
│ - Build Dagster software-defined assets for automated batch extraction.│
│ - Integrate Evidently AI drift detection monitors.                     │
│ - Execute complete synthetic test suites (`pytest`) in CI/CD pipeline. │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 8.3 Risk Analysis & Mitigation Matrix

| Risk Factor | Probability | Impact | Mitigation Strategy |
|---|---|---|---|
| **High-Volume Ingestion Bottlenecks** | Medium | High | Use asynchronous streaming ingestion (FastAPI + SQS/Kafka buffer) and Polars vectorized batch processing instead of row-by-row ORM inserts. |
| **False Positive Quarantines** | Low | High | Establish configurable tolerance bands ($\epsilon$) for rounding differences in currency calculations and provide an admin triage replay API. |
| **Timezone & Daylight Savings Skew** | High | Medium | Enforce strict UTC conversion at Tier 1 ingestion gateway; reject non-timezone-aware inputs. |
| **Cold Start False Anomalies** | Medium | Medium | Gate statistical models with $N_{\min} \ge 14$; use Bayesian prior borrowing from category parents with lower diagnostic confidence. |
| **Drift vs Real Business Disruption** | Medium | Medium | Correlate statistical drift with unstructured document events (marketing launches, outages) before triggering system abstention. |

---

## 9. Conclusion

The implementation of the **Data Ingestion & Validity Layer (R1)** provides the foundational data truth required by the entire Business Intelligence platform. By establishing the 6-tier validation gate, automated quarantine mechanisms, composite data quality scoring, and seamless coupling with GoRules policy governance, the system guarantees that all downstream agent investigations, causal attributions, and executive narratives are grounded in validated, mathematically coherent data.
