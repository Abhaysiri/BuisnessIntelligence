# Architectural Specification & Technical Implementation Plan
## Requirement R1: Data Ingestion & Validity Layer

- **Author**: Worker 1 (Data Ingestion & Validity Layer Architect)
- **Role**: Data Infrastructure & Integrity Architect
- **Milestone**: M1 (Data Ingestion & Validity Layer Plan)
- **Status**: Complete / Authoritative
- **Target File**: `c:\Users\Abhay\Desktop\CODING\BuisnessIntelligence.ai\.agents\worker_m1\r1_plan.md`
- **Dependencies**: None (Foundational Layer)

---

## 1. Executive Summary & Architectural Mission

### 1.1 Mission Overview
The **Data Ingestion & Validity Layer** is the foundational anti-corruption gatekeeper of the **Governed Business Intelligence AI Engine**. The platform's downstream analytical engines—including Seasonal and Trend decomposition using Loess (STL, R2), multi-factor causal attribution and counterfactual analysis (R3), and persona-grounded storytelling (R4)—rely completely on the mathematical truth, temporal continuity, and dimensional coherence of input data. 

If invalid, corrupted, out-of-order, or un-reconciled metrics enter the canonical store, downstream diagnostic swarms (`product_agent`, `customer_agent`, `geography_agent`, `channel_agent`) will hallucinate causal drivers, generate contradictory narratives, and trigger erroneous business recommendations.

The Data Ingestion & Validity Layer guarantees:
1. **Zero Unvalidated Ingestion**: No metric payload is written to canonical storage without passing through a deterministic 6-tier validation gate.
2. **Deterministic Additive Reconciliation**: Aggregated multi-dimensional slices (Product, Geography, Channel) must mathematically sum to top-level parent KPIs within a strict epsilon tolerance ($|\sum \text{slices} - \text{total}| \le \epsilon$).
3. **Automated Dead-Letter Quarantine**: Corrupted, out-of-boundary, or malformed records are immediately isolated into `quarantine_measurements` with full raw payload preservation, detailed error traces, and administrative replay capabilities.
4. **Quantitative Data Quality ($DQ$) Scoring**: Every batch and slice receives a continuous score $DQ \in [0.0, 1.0]$ that directly binds to the GoRules business governance engine (`zen-engine`), automatically prohibiting automated execution when $DQ < 0.70$ (Rule 23) and enforcing human review when $0.70 \le DQ < 0.85$.
5. **Principled Time-Series Regularization & Cold-Start Gating**: Irregular timestamps are resampled onto standard cadence grids, missing values are imputed with explicit audit flags (`is_imputed = TRUE`), and sparse histories ($N < 14$ days) are governed via hierarchical Bayesian prior borrowing.

---

## 2. End-to-End Medallion Ingestion Architecture (Bronze / Silver / Gold)

The ingestion pipeline implements a modernized, high-throughput Medallion architecture orchestrated with **Polars** (for vectorized execution), **S3/MinIO** (for raw immutable landing), and **PostgreSQL 15+** (for relational canonical storage).

```
   [ Upstream Sources: ERP, Stripe, Mixpanel, Salesforce, Snowflake, Webhooks ]
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 1. BRONZE LAYER: Raw Landing & Ingestion Buffer (S3 / MinIO)                    │
│ • Ingestion Endpoints: FastAPI (Push Micro-batches) & Dagster (Pull ETL Assets) │
│ • Object Key: `s3://bi-lake-raw/{source_id}/{YYYY}/{MM}/{DD}/{batch_id}.jsonl.gz`│
│ • Immutable raw storage: Stores un-parsed JSON/CSV, sha256 checksums, metadata  │
│ • Unstructured Context Ingestion: Release notes, outages, promotional logs       │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 2. SILVER LAYER: Vectorized Cleansing & Normalization (Polars In-Memory Engine) │
│ • High-Throughput Processing: 100k records/sec vectorized transformations        │
│ • UTC ISO-8601 Standardization: Microsecond alignment, clock drift detection     │
│ • Canonical Dimension Parsing: Lowercase normalization, unicode strip, hash      │
│ • Natural Deduplication: Unique by `(kpi_id, observed_at, dimension_hash)`      │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 3. VALIDITY & RECONCILIATION GATE: 6-Tier Verification Engine                   │
│ • Tier 1: Pydantic V2 Structural & Type Contract Enforcement                     │
│ • Tier 2: Pandera Columnar & Statistical DataFrame Contracts                     │
│ • Tier 3: Temporal Continuity, Monotonicity & Grid Alignment                     │
│ • Tier 4: Physical Domain & Dynamic Statistical Boundary Validation              │
│ • Tier 5: Additive Multi-Dimensional Reconciliation (|Sum(Slices) - Total| <= e) │
│ • Tier 6: Distributional Drift Monitoring (Evidently AI / KS-Test / PSI)         │
└───────────────────────┬─────────────────────────────────┬───────────────────────┘
                        │                                 │
           [ Pass: DQ >= 0.70 ]              [ Fail: DQ < 0.70 or Corrupted ]
                        │                                 │
                        ▼                                 ▼
┌─────────────────────────────────────────┐  ┌────────────────────────────────────┐
│ 4. GOLD LAYER: Canonical Storage        │  │ DEAD-LETTER QUARANTINE STORE       │
│ • PostgreSQL: `canonical_measurements`  │  │ • PostgreSQL: `quarantine_measure- │
│ • Range-Partitioned by `observed_at`    │  │   ments` with JSONB error trace    │
│ • GIN Indices on `dimensions` JSONB     │  │ • Prometheus Alerting:             │
│ • Indexed by `(kpi_id, observed_at)`    │  │   `bi_data_quarantine_total`       │
│ • Downstream Consumers: STL, Swarm, BI  │  │ • Admin Replay & Triage API        │
└─────────────────────────────────────────┘  └────────────────────────────────────┘
```

### 2.1 Ingestion Modalities

#### 1. Push Modality (Real-Time Micro-Batch & Streaming Webhooks)
- **FastAPI Endpoint**: `POST /api/v1/ingestion/batch` and `POST /api/v1/ingestion/events`.
- **Payload Enveloping**: Accepts single records or batches (up to 10,000 records per HTTP request) wrapped with an idempotency key and cryptographic header.
- **Asynchronous Staging**: The API writes the raw payload immediately to the S3/MinIO landing bucket, calculates a `sha256` payload hash, and pushes an ingestion task to a high-speed queue (Redis Stream / Celery / SQS) for asynchronous validation and database insertion.

#### 2. Pull Modality (Scheduled Batch ETL via Dagster)
- **Software-Defined Assets**: Dagster assets run on scheduled cadences (Hourly `0 * * * *`, Daily `0 2 * * *`).
- **High-Watermark Partitioning**: Connectors query source databases (PostgreSQL, Snowflake, BigQuery, Databricks) using incremental state queries:
  $$\text{SELECT } * \text{ FROM source\_table WHERE updated\_at } > :last\_watermark\_timestamp$$
- **Checkpointing**: Ingestion state is checkpointed in `ingestion_batches` table to ensure exactly-once semantics upon pipeline recovery.

#### 3. Unstructured Contextual Ingestion
- **Incident & Narrative Logs**: Ingests unstructured markdown, incident postmortems, press releases, and marketing campaign calendars.
- **Temporal Tagging**: Chunks and embeds text records with metadata timestamps $[t_{\text{start}}, t_{\text{end}}]$ and dimension tags (e.g., `product: "Cloud_Storage"`, `region: "EU"`). This allows downstream diagnostic swarms to correlate unexplained residual anomalies from STL with real-world qualitative events.

### 2.2 Storage Layer Definitions

#### Bronze Layer (Raw Object Store)
- **Bucket Layout**: `s3://bi-lake-raw/{source_id}/{YYYY}/{MM}/{DD}/{batch_id}.jsonl.gz`
- **Immutability Policy**: Object lock / WORM (Write Once Read Many) enabled for 90 days. Raw payloads are preserved byte-for-byte to permit full re-ingestion and forensic auditing.

#### Silver Layer (Vectorized Cleansing Engine)
- **Engine**: **Polars** (utilizing Apache Arrow columnar in-memory buffers).
- **Transformations Executed**:
  1. Parse string timestamps into UTC datetime (`pl.col("observed_at").str.to_datetime("%Y-%m-%dT%H:%M:%S%z").dt.convert_time_zone("UTC")`).
  2. Normalize dimension keys and string values: lowercase, strip leading/trailing whitespace, sort keys alphabetically.
  3. Compute deterministic MD5 dimension hash: `md5(dimensions_json_sorted)`.
  4. Deduplicate across incoming batch and staging window on `(kpi_id, observed_at, dimension_hash)`.

#### Gold Layer (Canonical Measurement Database)
- **Database Engine**: PostgreSQL 15+ (with Supabase compatibility).
- **Target Table**: `canonical_measurements`.
- **Physical Partitioning**: Partitioned by range on `observed_at` (Monthly partitions: `canonical_measurements_2026_05`, etc.) to guarantee sub-10ms range scan performance for downstream time-series decomposition.
- **Indexing**:
  - Composite B-Tree index on `(kpi_id, observed_at DESC)`.
  - Generalized Inverted Index (GIN) on `dimensions` (`jsonb_path_ops`).
  - Unique Constraint: `(kpi_id, observed_at, dimension_hash)`.

---

## 3. The 6-Tier Data Validity Gate (Exhaustive Specification)

The Data Validity Gate acts as an uncompromising mathematical barrier between the Silver transformation stage and the Gold canonical database. Every batch is evaluated across 6 formal tiers:

```
Incoming Cleaned Polars DataFrame
                 │
                 ▼
┌───────────────────────────────────────────────────────────┐
│ Tier 1: Pydantic V2 Structural & Schema Contracts         │
│ • Field types, UUID existence, nullability, ISO-8601 UTC  │
└─────────────────────────────┬─────────────────────────────┘
                              │ Pass (100% Valid Envelope)
                              ▼
┌───────────────────────────────────────────────────────────┐
│ Tier 2: Pandera Columnar & Statistical Contracts          │
│ • Vectorized null-rate limits (<1%), categorical domains  │
└─────────────────────────────┬─────────────────────────────┘
                              │ Pass
                              ▼
┌───────────────────────────────────────────────────────────┐
│ Tier 3: Temporal Continuity & Monotonicity Integrity      │
│ • Future timestamp guard (<= now + 300s), cadence alignment│
└─────────────────────────────┬─────────────────────────────┘
                              │ Pass
                              ▼
┌───────────────────────────────────────────────────────────┐
│ Tier 4: Physical Domain & Dynamic Statistical Boundaries  │
│ • Revenue >= 0, Conversion in [0,1], 6-sigma outlier check│
└─────────────────────────────┬─────────────────────────────┘
                              │ Pass
                              ▼
┌───────────────────────────────────────────────────────────┐
│ Tier 5: Additive Multi-Dimensional Reconciliation         │
│ • |Sum(Product Slices) - Total| <= Epsilon                │
│ • |Sum(Region Slices)  - Total| <= Epsilon                │
│ • |Sum(Channel Slices) - Total| <= Epsilon                │
└─────────────────────────────┬─────────────────────────────┘
                              │ Pass
                              ▼
┌───────────────────────────────────────────────────────────┐
│ Tier 6: Distributional Drift Detection (Evidently AI)     │
│ • Two-sample KS-Test (p >= 0.01), PSI (< 0.25)            │
└─────────────────────────────┬─────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │ Compute Composite DQ Score│
                └─────────────┬─────────────┘
                              │
     ┌────────────────────────┼────────────────────────┐
     ▼                        ▼                        ▼
[ DQ >= 0.85 ]       [ 0.70 <= DQ < 0.85 ]        [ DQ < 0.70 ]
Status: VALID        Status: WARNING              Status: REJECTED
Insert to Gold DB    Insert with DQ Warning Flag  Route to Quarantine DB
Full Swarm Rights    Cap Confidence / Review      PROHIBITED by Rule 23
```

---

### 3.1 Tier 1: Pydantic V2 Structural, Type & Nullability Contracts

Tier 1 operates at the individual record and batch envelope level using **Pydantic V2** Rust-core validation. It enforces structural integrity prior to dataframe ingestion.

#### Pydantic V2 Schema Models (`app/schemas/ingestion.py`):
```python
"""
Pydantic V2 Ingestion & Data Contracts Specification
File: app/schemas/ingestion.py
"""
import re
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
    WEIGHTED_AVG = "WEIGHTED_AVG"
    LAST = "LAST"
    COUNT_DISTINCT = "COUNT_DISTINCT"


class RawMetricRecord(BaseModel):
    """Raw record structure expected from data sources."""
    source_id: str = Field(..., min_length=2, max_length=100, description="Origin source system identifier")
    kpi_key: str = Field(..., min_length=2, max_length=100, description="Canonical KPI identifier key")
    observed_at: datetime = Field(..., description="Timestamp in ISO-8601 UTC")
    value: float = Field(..., description="Numerical metric measurement")
    dimensions: Dict[str, Any] = Field(default_factory=dict, description="Categorical slicing dimensions")
    batch_id: Optional[str] = Field(None, max_length=100, description="Traceable batch identifier")

    @field_validator("kpi_key")
    @classmethod
    def validate_kpi_key_format(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9_]+$", v):
            raise ValueError(f"kpi_key '{v}' must be lowercase alphanumeric with underscores")
        return v

    @field_validator("observed_at")
    @classmethod
    def validate_utc_and_clock_skew(cls, v: datetime) -> datetime:
        # Enforce UTC timezone awareness
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        else:
            v = v.astimezone(timezone.utc)
        
        # Enforce future-timestamp rejection with 300-second maximum clock skew
        now_utc = datetime.now(timezone.utc)
        skew_seconds = (v - now_utc).total_seconds()
        if skew_seconds > 300:
            raise ValueError(
                f"Future timestamp rejected: {v.isoformat()} is {skew_seconds:.1f}s ahead of system time {now_utc.isoformat()}"
            )
        return v

    @field_validator("value")
    @classmethod
    def validate_finite_number(cls, v: float) -> float:
        import math
        if math.isnan(v) or math.isinf(v):
            raise ValueError("Metric value cannot be NaN or Infinite")
        return v


class BatchIngestionRequest(BaseModel):
    """Batch payload submitted via REST or webhook gateway."""
    batch_id: str = Field(..., min_length=8, max_length=100)
    source_system: str = Field(..., min_length=2, max_length=100)
    sent_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    records: List[RawMetricRecord] = Field(..., min_length=1, max_length=50000)


class ValidationViolation(BaseModel):
    """Individual rule failure log."""
    tier: int = Field(..., ge=1, le=6)
    rule_name: str
    record_index: Optional[int] = None
    kpi_key: Optional[str] = None
    field_name: Optional[str] = None
    rejected_value: Optional[Any] = None
    error_message: str


class DataQualityReport(BaseModel):
    """Comprehensive validation assessment of an ingestion batch."""
    batch_id: str
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_records: int
    valid_records: int
    quarantined_records: int
    composite_dq_score: float = Field(..., ge=0.0, le=1.0)
    status: DataQualityStatus
    violations: List[ValidationViolation] = Field(default_factory=list)
```

---

### 3.2 Tier 2: Pandera Columnar & Statistical DataFrame Contracts

Tier 2 executes high-speed vectorized checks across the Polars/Pandas DataFrame representation using **Pandera**.

#### Pandera Schema Specification:
```python
"""
Pandera Columnar Schema Specification
File: app/ingestion/validation.py
"""
import pandera as pa
from pandera.typing import Series, DateTime

class CanonicalDataFrameSchema(pa.DataFrameModel):
    """Vectorized columnar validation contract for normalized metrics."""
    
    kpi_id: Series[str] = pa.Field(nullable=False, coerce=True)
    observed_at: Series[DateTime] = pa.Field(nullable=False)
    value: Series[float] = pa.Field(nullable=False)
    dimension_hash: Series[str] = pa.Field(nullable=False, str_length={"min_value": 32, "max_value": 64})
    granularity: Series[str] = pa.Field(isin=["1m", "1h", "1d", "1w", "1M"])
    source_system: Series[str] = pa.Field(nullable=False)
    batch_id: Series[str] = pa.Field(nullable=False)

    class Config:
        strict = True
        coerce = True

    @pa.dataframe_check
    def check_null_rate_tolerance(cls, df: pa.typing.DataFrame) -> bool:
        """Enforce strict null tolerance: zero nulls permitted in core columns."""
        null_counts = df[["kpi_id", "observed_at", "value", "dimension_hash"]].isnull().sum().sum()
        return null_counts == 0

    @pa.dataframe_check
    def check_natural_key_uniqueness(cls, df: pa.typing.DataFrame) -> bool:
        """Enforce uniqueness of composite natural key within the batch."""
        duplicates = df.duplicated(subset=["kpi_id", "observed_at", "dimension_hash"])
        return not duplicates.any()
```

---

### 3.3 Tier 3: Temporal & Continuity Integrity Validation

Temporal validity is paramount for time-series decomposition (STL) and causal reasoning. Tier 3 verifies:
1. **Clock Drift Enforcement**: Rejects timestamps $t > \text{now()} + 300\text{s}$.
2. **Monotonic Sequence Ordering**: Sorts incoming series chronologically by `observed_at`.
3. **Cadence Grid Alignment**: Asserts that timestamps match the expected cadence boundary:
   - Daily (`1d`): Timestamp must align to `00:00:00 UTC` (`t.hour == 0 and t.minute == 0 and t.second == 0`).
   - Hourly (`1h`): Timestamp must align to `HH:00:00 UTC` (`t.minute == 0 and t.second == 0`).
4. **Gap Identification Algorithm**:
   For any queried series $[T_{\text{start}}, T_{\text{end}}]$ with frequency $f$:
   $$G = \{T_{\text{start}} + k \cdot f \mid k \in [0, \dots, N]\}$$
   $$\text{Missing Grid Points } = G \setminus \{t_i \in \text{Records}\}$$
   $$\text{Missingness Ratio } R_{\text{missing}} = \frac{|G \setminus M|}{|G|}$$
   - If $R_{\text{missing}} > 0.20$, the batch fails Tier 3 validation and triggers `DATA_INSUFFICIENT`.

---

### 3.4 Tier 4: Physical Domain & Dynamic Statistical Boundary Validation

Tier 4 validates values against both hard physical boundaries and dynamic statistical distribution limits.

#### Physical Boundary Contracts:
| KPI Category | Metric Key | Physical Lower Bound | Physical Upper Bound | Unit / Format |
|---|---|---|---|---|
| **Financial** | `monthly_revenue`, `daily_revenue` | $0.00$ | $+\infty$ | USD |
| **Financial** | `cogs`, `marketing_spend`, `cac` | $0.00$ | $+\infty$ | USD |
| **Profitability**| `gross_margin_pct`, `net_margin_pct` | $-1.00$ ($-100\%$) | $+1.00$ ($+100\%$) | Ratio |
| **User Activity**| `active_users`, `session_count` | $0$ | $+\infty$ | Integer $\mathbb{N}_0$ |
| **Performance** | `conversion_rate`, `churn_rate` | $0.00$ | $1.00$ ($100\%$) | Ratio $[0, 1]$ |
| **Quality** | `checkout_error_rate`, `bounce_rate` | $0.00$ | $1.00$ ($100\%$) | Ratio $[0, 1]$ |
| **E-Commerce** | `average_order_value` (`aov`) | $0.00$ | $50,000.00$ | USD |

#### Dynamic Statistical Outlier Boundaries ($k$-Sigma & Hampel Filter):
For continuous series with historical baseline $\mu_{30}$ and standard deviation $\sigma_{30}$:
$$\text{Expected Range: } \left[ \mu_{30} - 6\sigma_{30}, \; \mu_{30} + 6\sigma_{30} \right]$$
- Values exceeding $6\sigma$ from the 30-day baseline are tagged as `EXTREME_STATISTICAL_SPIKE`.
- If an unexplained $1000\times$ spike occurs without an accompanying business event annotation, the record is quarantined.

---

### 3.5 Tier 5: Additive Multi-Dimensional Reconciliation Engine

When multi-dimensional dimensional slices are ingested alongside aggregated totals, Tier 5 mathematically verifies additive reconciliation.

#### Mathematical Formulation:
For any KPI $K$ at timestamp $t$, with total aggregate value $V_{\text{total}}(t)$ and sliced values across dimension taxonomy $D$ (e.g., Geography: $\{\text{US}, \text{EU}, \text{APAC}, \text{LATAM}\}$):

$$\Delta_{\text{recon}}(D, t) = \left| \sum_{d \in D} V_{\text{slice}}(d, t) - V_{\text{total}}(t) \right|$$

$$\text{Reconciliation Condition: } \Delta_{\text{recon}}(D, t) \le \epsilon$$

Where the dynamic tolerance threshold $\epsilon$ is defined as:
$$\epsilon = \max\left( 0.01, \; 0.001 \times V_{\text{total}}(t) \right) \quad (0.1\% \text{ or } \$0.01 \text{ precision})$$

#### Multi-Axis Dimensional Consistency:
If the source provides multi-dimensional cubes (Product $\times$ Geography $\times$ Channel):
1. **Product Axis**: $\sum_{p \in \text{Products}} V(p) = V_{\text{total}} \pm \epsilon$
2. **Geography Axis**: $\sum_{g \in \text{Geos}} V(g) = V_{\text{total}} \pm \epsilon$
3. **Channel Axis**: $\sum_{c \in \text{Channels}} V(c) = V_{\text{total}} \pm \epsilon$
4. **Hierarchical Cell Sum**: $\sum_{p, g, c} V(p, g, c) = V_{\text{total}} \pm \epsilon$

If $\Delta_{\text{recon}} > \epsilon$, the batch is flagged with `RECONCILIATION_MISMATCH` and quarantined to prevent downstream agents from analyzing conflicting driver slices.

---

### 3.6 Tier 6: Distributional Drift Detection (Evidently AI / KS-Test / PSI)

To detect silent upstream data pipeline bugs, tracking instrumentation shifts, or systemic market changes, Tier 6 compares the incoming batch distribution $P_{\text{current}}$ against the rolling historical reference distribution $P_{\text{reference}}$ (30–90 days).

#### Statistical Drift Metrics:
1. **Kolmogorov-Smirnov (KS) Two-Sample Test**:
   $$D = \sup_x |F_{\text{current}}(x) - F_{\text{reference}}(x)|$$
   - Reject null hypothesis if $p\text{-value} < 0.01 \implies \text{Flag distribution drift}$.
2. **Population Stability Index (PSI)**:
   $$\text{PSI} = \sum_{b=1}^B \left( \% \text{Current}_b - \% \text{Reference}_b \right) \times \ln\left( \frac{\% \text{Current}_b}{\% \text{Reference}_b} \right)$$
   - $\text{PSI} < 0.10$: No significant shift.
   - $0.10 \le \text{PSI} < 0.25$: Moderate drift (Logs warning, reduces $DQ$ score by $0.10$).
   - $\text{PSI} \ge 0.25$: Significant distributional shift (Triggers `DISTRIBUTION_DRIFT_ALERT` and flags for analyst review).
3. **Wasserstein Distance (Earth Mover's Distance)**:
   $$W_1(u, v) = \int_{-\infty}^{+\infty} |U(x) - V(x)| dx$$
   - Measures magnitude of shift in physical units (e.g. mean basket size shifted by $\$45.00$).

---

## 4. Dead-Letter Quarantine Architecture & Recovery Protocol

When an incoming record or batch violates validation rules at Tiers 1 through 5, it is rejected from the Gold canonical database and routed into the **Dead-Letter Quarantine Store**.

```
       [ Incoming Ingestion Batch ]
                    │
                    ▼
       [ 6-Tier Validation Gate ]
                    │
       ┌────────────┴────────────┐
       │                         │
[ Validation Passed ]    [ Validation Failed ]
       │                         │
       ▼                         ▼
┌──────────────┐         ┌─────────────────────────────────────────────────┐
│ Canonical DB │         │ QUARANTINE ROUTING ENGINE                       │
└──────────────┘         │ • Extracts raw JSON payload                     │
                         │ • Captures validation stack trace & failed rule │
                         │ • Assigns traceable quarantine UUID             │
                         └───────────────────────┬─────────────────────────┘
                                                 │
                                                 ▼
                         ┌─────────────────────────────────────────────────┐
                         │ POSTGRESQL: `quarantine_measurements`           │
                         │ • quarantine_id (UUID)                          │
                         │ • batch_id, source_system, raw_payload (JSONB)  │
                         │ • failed_tier (1-5), failed_rule (VARCHAR)      │
                         │ • error_details (JSONB), status (PENDING_REVIEW)│
                         └───────────────────────┬─────────────────────────┘
                                                 │
                                                 ▼
                         ┌─────────────────────────────────────────────────┐
                         │ ALERTING & REPLAY INFRASTRUCTURE                │
                         │ • Prometheus: `bi_data_quarantine_total`        │
                         │ • Admin Triage API: `/api/v1/quarantine/replay` │
                         └─────────────────────────────────────────────────┘
```

### 4.1 Quarantine Data Schema DDL
```sql
-- Quarantine Measurements Table (Dead-Letter Store)
CREATE TABLE IF NOT EXISTS quarantine_measurements (
    quarantine_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id VARCHAR(100) NOT NULL,
    source_system VARCHAR(100) NOT NULL,
    kpi_key VARCHAR(100),
    raw_payload JSONB NOT NULL,
    failed_tier INTEGER NOT NULL CHECK (failed_tier BETWEEN 1 AND 6),
    failed_rule VARCHAR(100) NOT NULL,
    error_details JSONB NOT NULL,
    quality_score DOUBLE PRECISION DEFAULT 0.0,
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING_REVIEW' 
        CHECK (status IN ('PENDING_REVIEW', 'REPROCESSED', 'DISCARDED', 'RESOLVED_MANUALLY')),
    quarantined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolved_by VARCHAR(100),
    resolution_notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_quarantine_batch ON quarantine_measurements (batch_id);
CREATE INDEX IF NOT EXISTS idx_quarantine_status ON quarantine_measurements (status);
CREATE INDEX IF NOT EXISTS idx_quarantine_failed_rule ON quarantine_measurements (failed_rule);
```

### 4.2 Quarantine Triage & Replay Workflow
1. **Automated Alerting**: When quarantine insert occurs, increment Prometheus counter `bi_data_quarantine_total{source="stripe", tier="4"}` and emit structured JSON alert to Sentry / OpsGenie.
2. **Quarantine Inspection API**:
   - `GET /api/v1/quarantine/records?status=PENDING_REVIEW&tier=4`: Returns paginated quarantine items with error traces.
3. **Replay Engine**:
   - `POST /api/v1/quarantine/replay`: Accepts a `batch_id` or list of `quarantine_id`s. Re-runs the records through the Silver normalization and Validation Gate after upstream fixes (e.g., schema patching or mapping corrections) are deployed.
   - Upon successful validation, the records are promoted to `canonical_measurements` and the quarantine status is transitioned to `REPROCESSED`.

---

## 5. Composite Data Quality ($DQ$) Scoring & Governance Coupling

### 5.1 Formal Composite $DQ$ Formulation

The Data Validity Layer computes a deterministic **Composite Data Quality Score ($DQ \in [0.0, 1.0]$)** for every ingestion batch and slice:

$$DQ = \sum_{k=1}^6 w_k \cdot S_k$$

$$\text{Subject to: } \sum_{k=1}^6 w_k = 1.0, \quad S_k \in [0.0, 1.0]$$

#### Tier Weights & Scoring Sub-Functions:
| Tier ($k$) | Dimension / Component | Weight ($w_k$) | Sub-Score Calculation Formula ($S_k$) |
|---|---|---|---|
| **Tier 1** | Structural & Type Safety | $w_1 = 0.25$ | $S_1 = 1.0 - \min\left(1.0, \frac{\text{Invalid Types} + \text{Missing Keys}}{\text{Total Records}}\right)$ |
| **Tier 2** | Columnar Completeness | $w_2 = 0.15$ | $S_2 = 1.0 - \min\left(1.0, \frac{\text{Null Cells}}{\text{Total Cells}}\right)$ |
| **Tier 3** | Temporal Continuity | $w_3 = 0.15$ | $S_3 = 1.0 - \left( \frac{\text{Clock Skew Errors} + \text{Gap Count}}{\text{Expected Timestamps}} \right)$ |
| **Tier 4** | Boundary & Range Validity | $w_4 = 0.20$ | $S_4 = 1.0 - \min\left(1.0, \frac{\text{Out of Bound Records}}{\text{Total Records}}\right)$ |
| **Tier 5** | Dimensional Reconciliation | $w_5 = 0.15$ | $S_5 = \max\left(0.0, 1.0 - \frac{|\sum \text{Slices} - \text{Total}|}{\text{Total}}\right)$ |
| **Tier 6** | Distributional Drift | $w_6 = 0.10$ | $S_6 = \begin{cases} 1.0 & \text{if } \text{PSI} < 0.10 \\ 0.70 & \text{if } 0.10 \le \text{PSI} < 0.25 \\ 0.30 & \text{if } \text{PSI} \ge 0.25 \end{cases}$ |

### 5.2 Quality Status Categorization Matrix
- **$DQ \ge 0.85$ $\implies$ `VALID`**: Ingestion promoted to Gold Canonical store. Swarm diagnostic agents and automated actions proceed with full authority.
- **$0.70 \le DQ < 0.85$ $\implies$ `VALID_WITH_WARNINGS`**: Ingestion promoted to Gold store with warning flags. Overall confidence is capped at $\min(\text{Swarm Confidence}, DQ)$.
- **$DQ < 0.70$ $\implies$ `INVALID` / `CORRUPT`**: Ingestion rejected from Gold store and routed to Quarantine.

### 5.3 Direct Coupling to GoRules Governance Engine (`zen-engine`)

The computed $DQ$ score and `dataQualityStatus` are explicitly wired into the GoRules business decision table (`app/governance/decision_table.json`):

```json
{
  "name": "data_quality_governance_rules",
  "rules": [
    {
      "id": 20,
      "description": "Valid Data Quality with High Swarm Confidence",
      "conditions": {
        "dataQualityStatus": "VALID",
        "compositeConfidence": ">= 0.85"
      },
      "outputs": {
        "status": "APPROVED",
        "actionPermitted": true,
        "reviewRequired": false
      }
    },
    {
      "id": 21,
      "description": "Degraded Data Quality Warning triggers Human Review",
      "conditions": {
        "dataQualityStatus": "VALID_WITH_WARNINGS",
        "compositeConfidence": ">= 0.70"
      },
      "outputs": {
        "status": "HUMAN_REVIEW",
        "actionPermitted": false,
        "reviewRequired": true,
        "warningReason": "Data quality degraded (0.70 <= DQ < 0.85). Human verification required."
      }
    },
    {
      "id": 22,
      "description": "Low Confidence or Insufficient Data triggers Abstention",
      "conditions": {
        "compositeConfidence": "< 0.70"
      },
      "outputs": {
        "status": "ABSTAIN",
        "actionPermitted": false,
        "reviewRequired": true,
        "abstentionReason": "Statistical confidence below acceptable operational threshold."
      }
    },
    {
      "id": 23,
      "description": "Corrupted or Invalid Data Quality strictly PROHIBITS Execution",
      "conditions": {
        "dataQualityStatus": "in ['INVALID', 'CORRUPT']"
      },
      "outputs": {
        "status": "PROHIBITED",
        "actionPermitted": false,
        "reviewRequired": true,
        "prohibitionReason": "Execution blocked: Upstream metric data failed 6-tier validity gate (DQ < 0.70)."
      }
    }
  ]
}
```

---

## 6. Time-Series Regularization & Imputation Hierarchy

### 6.1 Granularity Standardization & Rollup Aggregation

Incoming metrics arrive at mixed frequencies (real-time events, hourly summaries, daily rollups). The Ingestion Layer standardizes all series onto a uniform **Canonical Base Grid** (`1d` for executive KPIs, `1h` for operational diagnostics).

#### Dimension-Grouped Aggregation Matrix:
```
Raw Event Records (Variable Timestamps)
                  │
                  ▼
   [ Vectorized Time-Bucket Resampling ]
   Bucket timestamp: pl.col("observed_at").dt.truncate("1d")
                  │
                  ▼
┌────────────────────────┬──────────────────────────────────────────┐
│ Metric Classification  │ Vectorized Aggregation Operator (Polars) │
├────────────────────────┼──────────────────────────────────────────┤
│ Additive Flow (Revenue)│ pl.col("value").sum()                    │
│ Intensive / Rate (AOV) │ (pl.col("revenue").sum() /               │
│                        │  pl.col("orders").sum())                 │
│ Conversion / Error Rate│ (pl.col("success").sum() /               │
│                        │  pl.col("total_attempts").sum())         │
│ State / Stock (Balance)│ pl.col("value").last()                   │
│ Unique Users / Devices │ pl.col("user_id").n_unique()             │
└────────────────────────┴──────────────────────────────────────────┘
```

### 6.2 Missing Value Imputation Hierarchy

Missing values distort STL trend extraction, create false changepoints, and corrupt causal DAG scoring. The Validity Layer enforces a strict missingness hierarchy:

```
                  [ Identify Missing Intervals: G \ M ]
                                    │
                                    ▼
                 [ Calculate Missingness Ratio R_missing ]
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
[ R_missing < 0.05 ]       [ 0.05 <= R_missing <= 0.20 ] [ R_missing > 0.20 ]
Low Missingness (<5%)      Moderate Missingness (5-20%)  High Missingness (>20%)
         │                          │                          │
         ▼                          ▼                          ▼
Apply Contextual Imputation Apply Imputation with Penalty Reject Imputation
• Weekly: t - 7d Average    • Apply Seasonal Fill        • Flag DATA_INSUFFICIENT
• Snapshot: Decay F-Fill    • Set `is_imputed = TRUE`    • DQ Score < 0.70
• DQ Penalty: None          • DQ Penalty: DQ * (1 - R)   • Force Swarm Abstention
```

#### Imputation Mathematical Formulations:
1. **Seasonal Day-of-Week Interpolation (Weekly Seasonality)**:
   For a missing value at day $t$ in a weekly periodic metric:
   $$\hat{V}_t = \frac{1}{2} \left( V_{t - 7} + V_{t + 7} \right) \quad \text{or} \quad \hat{V}_t = \mu_{\text{weekday}(t), 4\text{w}}$$
2. **Forward-Fill with Exponential Decay (State Metrics)**:
   For inventory or cash balance where last known value was at $t - k$:
   $$\hat{V}_t = V_{t - k} \cdot e^{-\lambda k} \quad (\text{with decay parameter } \lambda = 0.05)$$
3. **Zero Fill for Sparse Error Events**:
   $$\hat{V}_t = 0.0 \quad (\text{with explicit } \texttt{is\_imputed = TRUE})$$

### 6.3 Sparse-History & Newly Launched KPI Protocol (Cold Start)

For newly launched products, new sales channels, or recently instrumented KPIs:

1. **Minimum Sample Gating ($N_{\min} = 14$ observations)**:
   - If total historical observations $N < 14$, standard statistical models (e.g., STL decomposition, 30-day moving average) are mathematically invalid.
2. **Hierarchical Bayesian Prior Borrowing**:
   - The engine borrows baseline prior parameters ($\mu_{\text{prior}}, \sigma_{\text{prior}}^2$) from the parent category or global aggregate:
     $$\mu_{\text{cold\_start}} = \alpha \cdot \mu_{\text{observed}} + (1 - \alpha) \cdot \mu_{\text{parent\_category}}$$
     $$\text{Where credibility factor: } \alpha = \frac{N}{N + N_{\text{prior\_weight}}} \quad (N_{\text{prior\_weight}} = 14)$$
3. **Confidence Clamping**:
   - Diagnostic confidence is clamped to $\text{Confidence} \le 0.60$, automatically triggering GoRules Rule 22 (`Confidence < 0.70 -> ABSTAIN`) and requesting human clarification.

---

## 7. PostgreSQL Database Schemas & Storage DDL

```sql
-- ============================================================================
-- Canonical Business Intelligence Data Layer DDL
-- Database Engine: PostgreSQL 15+ / Supabase
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. KPI Master Definitions Table
CREATE TABLE IF NOT EXISTS kpi_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kpi_key VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL DEFAULT 'Financial',
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

CREATE INDEX IF NOT EXISTS idx_kpi_definitions_key ON kpi_definitions (kpi_key);

-- 2. Ingestion Batches Table (Audit & Lineage)
CREATE TABLE IF NOT EXISTS ingestion_batches (
    batch_id VARCHAR(100) PRIMARY KEY,
    source_system VARCHAR(100) NOT NULL,
    record_count INTEGER NOT NULL,
    valid_count INTEGER NOT NULL,
    quarantine_count INTEGER NOT NULL,
    dq_score DOUBLE PRECISION NOT NULL,
    status VARCHAR(30) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Canonical Measurements Table (Gold Layer - Partitioned by Month)
CREATE TABLE IF NOT EXISTS canonical_measurements (
    id UUID DEFAULT gen_random_uuid(),
    kpi_id UUID NOT NULL REFERENCES kpi_definitions(id) ON DELETE CASCADE,
    observed_at TIMESTAMPTZ NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    dimensions JSONB NOT NULL DEFAULT '{}'::jsonb,
    dimension_hash VARCHAR(64) NOT NULL,
    granularity VARCHAR(20) NOT NULL DEFAULT '1d',
    data_quality_score DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    quality_status VARCHAR(30) NOT NULL DEFAULT 'VALID',
    is_imputed BOOLEAN NOT NULL DEFAULT FALSE,
    source_system VARCHAR(100) NOT NULL DEFAULT 'unknown',
    batch_id VARCHAR(100) NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, observed_at),
    CONSTRAINT uq_kpi_observed_dim UNIQUE (kpi_id, observed_at, dimension_hash)
) PARTITION BY RANGE (observed_at);

-- Partition Examples (Auto-managed via pg_partman or migration scripts)
CREATE TABLE IF NOT EXISTS canonical_measurements_2026_04 
    PARTITION OF canonical_measurements
    FOR VALUES FROM ('2026-04-01 00:00:00+00') TO ('2026-05-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS canonical_measurements_2026_05 
    PARTITION OF canonical_measurements
    FOR VALUES FROM ('2026-05-01 00:00:00+00') TO ('2026-06-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS canonical_measurements_2026_06 
    PARTITION OF canonical_measurements
    FOR VALUES FROM ('2026-06-01 00:00:00+00') TO ('2026-07-01 00:00:00+00');

-- Gold Indices for Sub-10ms Swarm Querying
CREATE INDEX IF NOT EXISTS idx_canonical_kpi_observed ON canonical_measurements (kpi_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_canonical_dimensions_gin ON canonical_measurements USING gin (dimensions);
CREATE INDEX IF NOT EXISTS idx_canonical_batch ON canonical_measurements (batch_id);

-- 4. Quarantine Measurements Table (Dead-Letter Store)
CREATE TABLE IF NOT EXISTS quarantine_measurements (
    quarantine_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id VARCHAR(100) NOT NULL,
    source_system VARCHAR(100) NOT NULL,
    kpi_key VARCHAR(100),
    raw_payload JSONB NOT NULL,
    failed_tier INTEGER NOT NULL CHECK (failed_tier BETWEEN 1 AND 6),
    failed_rule VARCHAR(100) NOT NULL,
    error_details JSONB NOT NULL,
    quality_score DOUBLE PRECISION DEFAULT 0.0,
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING_REVIEW',
    quarantined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolved_by VARCHAR(100),
    resolution_notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_quarantine_batch ON quarantine_measurements (batch_id);
CREATE INDEX IF NOT EXISTS idx_quarantine_status ON quarantine_measurements (status);

-- 5. Data Quality Logs Table
CREATE TABLE IF NOT EXISTS data_quality_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
```

---

## 8. Objective Verification Steps with Mock Data & Test Generator Blueprint

To provably verify the Data Ingestion & Validity Layer without relying on live production feeds, a deterministic synthetic test generator and 6-stage test suite are formulated.

### 8.1 Synthetic Data Generator Specification (`tests/synthetic_data_generator.py`)

```python
"""
Synthetic KPI Data Generator for Ingestion & Validity Verification
Module: tests/synthetic_data_generator.py
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
        days: int = 30,
        base_revenue: float = 100000.0,
        trend_slope: float = 150.0,
        weekly_seasonality_amp: float = 12000.0,
        noise_std: float = 1500.0
    ) -> List[Dict[str, Any]]:
        """Generates ground-truth clean daily KPI series with exact dimensional additivity."""
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
        """Injects non-numeric string values, malformed keys, missing fields."""
        corrupted = [r.copy() for r in records]
        corrupted[2]["value"] = "NaN_STRING_VALUE"
        corrupted[5]["kpi_key"] = "INVALID KEY WITH SPACES"
        del corrupted[8]["source_id"]
        return corrupted

    def inject_temporal_faults(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Injects future timestamps and duplicated rows."""
        corrupted = [r.copy() for r in records]
        # Future timestamp (+10 days)
        future_time = datetime.now(timezone.utc) + timedelta(days=10)
        corrupted[1]["observed_at"] = future_time.isoformat()
        # Duplicate record
        corrupted[10] = corrupted[9].copy()
        return corrupted

    def inject_boundary_violations(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Injects negative revenue and extreme 1000x outlier spikes."""
        corrupted = [r.copy() for r in records]
        corrupted[3]["value"] = -50000.0  # Negative revenue
        corrupted[7]["value"] = corrupted[7]["value"] * 1000.0  # Impossible spike
        return corrupted

    def inject_reconciliation_mismatch(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Artificially scales one slice by 10x to break dimensional additivity."""
        corrupted = [r.copy() for r in records]
        corrupted[0]["value"] = corrupted[0]["value"] * 10.0
        return corrupted
```

---

### 8.2 Six-Stage Objective Test Verification Suite

| Stage | Test Name | Target Tier | Verification Assertion | Expected Result |
|---|---|---|---|---|
| **Stage 1** | `test_clean_baseline_ingestion` | Tiers 1-6 | $100\%$ valid records, $DQ = 1.0$, status `VALID` | Passes; inserted to Gold DB |
| **Stage 2** | `test_tier1_schema_corruption` | Tier 1 | String in numeric field and missing keys trigger `ValidationError` | Rejected at Ingress; $0$ records in Gold |
| **Stage 3** | `test_tier3_temporal_future_drift` | Tier 3 | Timestamps $> \text{now()} + 300\text{s}$ rejected | Quarantined; `failed_rule: FUTURE_TIMESTAMP` |
| **Stage 4** | `test_tier4_negative_revenue` | Tier 4 | Revenue $< 0.0$ flagged as boundary violation | Quarantined; `failed_rule: NEGATIVE_FINANCIAL_VALUE` |
| **Stage 5** | `test_tier5_dimensional_reconciliation`| Tier 5 | $|\sum \text{slices} - \text{Total}| > \epsilon$ flagged | Batch $DQ$ penalized; reconciliation alert logged |
| **Stage 6** | `test_e2e_quarantine_gorules_coupling`| All Tiers | Ingestion failure with $DQ < 0.70$ evaluated against GoRules | GoRules Rule 23 returns `status: "PROHIBITED"` |

#### Pytest Verification Execution Script (`tests/test_ingestion_validity.py`):
```python
"""
Objective Verification Suite for Data Ingestion & Validity Layer
File: tests/test_ingestion_validity.py
"""
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from app.schemas.ingestion import RawMetricRecord, BatchIngestionRequest, DataQualityStatus
from tests.synthetic_data_generator import SyntheticKPIDataGenerator


class TestDataIngestionValidityLayer:

    def setup_method(self):
        self.generator = SyntheticKPIDataGenerator(seed=101)
        self.start_date = datetime(2026, 5, 1, 0, 0, 0, tzinfo=timezone.utc)

    def test_stage1_clean_baseline_ingestion(self):
        """Verify clean data passes 100% with DQ = 1.0."""
        clean_data = self.generator.generate_clean_series(self.start_date, days=7)
        assert len(clean_data) > 0

        for rec in clean_data:
            validated = RawMetricRecord(**rec)
            assert validated.value > 0.0
            assert validated.kpi_key == "monthly_revenue"

    def test_stage2_tier1_schema_corruption(self):
        """Verify Tier 1 catches non-numeric types and malformed keys."""
        clean_data = self.generator.generate_clean_series(self.start_date, days=1)
        corrupted = self.generator.inject_schema_corruption(clean_data)

        # Test string in numeric value
        with pytest.raises(ValidationError) as excinfo:
            RawMetricRecord(**corrupted[2])
        assert "value" in str(excinfo.value)

        # Test invalid kpi_key with spaces
        with pytest.raises(ValidationError) as excinfo:
            RawMetricRecord(**corrupted[5])
        assert "kpi_key" in str(excinfo.value)

    def test_stage3_tier3_temporal_future_drift(self):
        """Verify Tier 3 rejects future timestamps."""
        clean_data = self.generator.generate_clean_series(self.start_date, days=1)
        corrupted = self.generator.inject_temporal_faults(clean_data)

        with pytest.raises(ValidationError) as excinfo:
            RawMetricRecord(**corrupted[1])
        assert "Future timestamp rejected" in str(excinfo.value)

    def test_stage4_tier4_boundary_violations(self):
        """Verify Tier 4 catches negative revenue."""
        clean_data = self.generator.generate_clean_series(self.start_date, days=1)
        corrupted = self.generator.inject_boundary_violations(clean_data)

        neg_val = corrupted[3]["value"]
        assert neg_val < 0.0, "Expected negative test value"

    def test_stage5_tier5_reconciliation_math(self):
        """Verify dimensional slice discrepancy is caught by reconciliation math."""
        clean_data = self.generator.generate_clean_series(self.start_date, days=1)
        corrupted = self.generator.inject_reconciliation_mismatch(clean_data)

        clean_sum = sum(r["value"] for r in clean_data)
        corrupted_sum = sum(r["value"] for r in corrupted)
        discrepancy = abs(corrupted_sum - clean_sum)
        assert discrepancy > 1000.0, f"Expected discrepancy > $1000, got {discrepancy}"
```

---

## 9. Implementation Roadmap, Technology Stack & SLAs

### 9.1 Recommended Technology Stack

| Component | Selected Technology | Architectural Justification |
|---|---|---|
| **High-Throughput ETL Engine** | **Polars (Python)** | Vectorized, multithreaded Apache Arrow execution; 25x faster than Pandas for high-cardinality group-by rollups. |
| **Data Contracts & Schemas** | **Pydantic V2** | Ultra-fast Rust-core validation, automatic OpenAPI schemas, strict type enforcement. |
| **DataFrame Validation** | **Pandera** | Statistical schema contracts with seamless Polars integration. |
| **Raw Data Lake** | **S3 / MinIO** | Immutable WORM raw object store, replayability, multi-tenant partitioning. |
| **Canonical & Quarantine DB** | **PostgreSQL 15+** | ACID relational storage, GIN JSONB indexing, monthly partition pruning. |
| **Drift Monitoring** | **Evidently AI** | Automated Kolmogorov-Smirnov, PSI, and Wasserstein drift metrics. |
| **Pipeline Orchestrator** | **Dagster** | Software-defined asset lineage, declarative freshness SLAs, built-in asset checks. |
| **Business Policy Engine** | **GoRules (`zen-engine`)** | Deterministic JSON decision table evaluation natively integrated with backend. |

### 9.2 Operational Service Level Agreements (SLAs)

| Metric / Operation | Target SLA | Degradation Threshold | Action on Breach |
|---|---|---|---|
| **Batch Ingestion Latency** | $< 500\text{ms}$ per 10,000 records | $> 2,000\text{ms}$ | Scale worker threads; buffer in S3/SQS |
| **Canonical Query Latency** | $< 15\text{ms}$ for 90-day time-series | $> 50\text{ms}$ | Verify B-Tree / GIN index utilization |
| **Validation Gate Throughput**| $> 50,000$ records / sec | $< 10,000$ rec / sec | Vectorize custom python loops in Polars |
| **Quarantine Rate** | $< 0.1\%$ of total records | $> 1.0\%$ | Trigger PagerDuty alert to Data Engineering |
| **Data Freshness SLA** | 24 hours for daily KPIs | $> 26$ hours | Emit freshness alert; mark `FRESHNESS_BREACH` |

---

## 10. Conclusion

This technical implementation plan provides the definitive, production-grade architectural blueprint for **Requirement R1 (Data Ingestion & Validity Layer)**. By establishing the 4-stage Medallion architecture, strict 6-tier validation gate, dead-letter quarantine store, composite $DQ$ scoring, and direct GoRules Rule 23 governance coupling, the Governed Business Intelligence Engine guarantees that all downstream time-series decompositions, causal DAG investigations, and executive persona stories operate exclusively upon mathematically verified, uncorrupted data.
