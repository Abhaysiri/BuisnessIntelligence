# Technical Implementation Plan: Requirement R4
# Golden Datasets & Runtime Telemetry Integration

**Author:** Worker 4 (Golden Datasets & Runtime Telemetry Architect)  
**Milestone:** M4  
**Scope:** `kpi-engine` (schemas, telemetry, evaluation, orchestrator, analytics, governance, api) and `frontend` (Dashboard & Visualizers telemetry integration)  
**Authoritative Reference:** `.agents/ORIGINAL_REQUEST.md` (R4), `PROJECT.md`

---

## Executive Summary

Requirement R4 establishes the ground-truth benchmarking infrastructure and full-stack runtime observability layer for the Business Intelligence Engine. This architectural document provides the authoritative, exhaustive design for two tightly integrated subsystems:

1. **Golden Datasets Architecture & Automated Evaluation Harness:**
   - A standardized, version-controlled ground-truth specification schema (`GoldenDatasetSpec`) formalizing movement manifests, time-series vectors, causal attribution ground truth, diagnostic findings, governance actions, and persona assertions.
   - A 4-Tier Dataset Catalog spanning Unit Feature Coverage, Boundary & Noise Stress, Cross-Factor Interactions, and Sanitized Enterprise Production Incidents.
   - Dual-format serialization (JSON/Parquet) integrated with DVC (Data Version Control) and Git LFS with strict semantic versioning (`v1.0.0`).
   - An automated CI/CD Regression Evaluation Benchmark Suite running in GitHub Actions to score Driver Recall, Attribution Mean Absolute Error (MAE), Abstention Precision, and Security Zero-Leakage.

2. **Runtime Telemetry Framework & 7 Exact Hook Placement Points:**
   - A lightweight, asynchronous OpenTelemetry (OTel) and LangChain callback architecture powering the frontend dashboard telemetry contract (`Latency`, `Model Calls`, `Token Usage`, `Est. Cost`).
   - A dynamic, multi-tier Cost Estimation Engine tracking prompt, completion, and cached token pricing across LLM providers.
   - Complete technical specifications for all **7 mandatory hook placement points** across the backend lifecycle—including exact file paths, target functions, captured metrics, context propagation via `contextvars`, and non-blocking `try/except` failure isolation to guarantee zero production impact.

---

# Part 1: Golden Datasets Generation & Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                GOLDEN DATASET ARCHITECTURE                               │
└─────────────────────────────────────────────────────────────────────────────────────────┘
        │
        ├──► 1. Data Generation Pipelines
        │       ├── A. Parametric Synthetic Generator (Mathematical formulas, DAG noise)
        │       └── B. Sanitized Enterprise Importer (De-identified production telemetry)
        │
        ├──► 2. Standardized Specification Schema (GoldenDatasetSpec)
        │       ├── Manifest Metadata (Benchmark ID, SemVer, Category, Domain)
        │       ├── Input Conditions (KPIMovementEvent, TimeSeries, SecurityContext)
        │       ├── Ground Truth Drivers (Attributions, Ranks, Causal Paths)
        │       ├── Expected Diagnostics (Findings, Contradictions, Abstention)
        │       ├── Expected Governance (Rule IDs, Decision Rights, Impact Limits)
        │       └── Expected Persona Facts (Key assertions, forbidden hallucinations)
        │
        ├──► 3. 4-Tier Dataset Catalog
        │       ├── Tier 1: Unit Feature Coverage (Isolated single-driver anomalies)
        │       ├── Tier 2: Boundary & Noise Stress (Low SNR, gaps, cold start N<14)
        │       ├── Tier 3: Cross-Factor Interaction (Opposing forces, LMDI, Simpson's)
        │       └── Tier 4: Real-World Enterprise Incidents (Multi-system outages)
        │
        ├──► 4. Storage & Semantic Versioning
        │       ├── Dual Format: JSON Specs + Snappy-Compressed Parquet Series
        │       └── DVC / Git LFS Tracking with Remote MinIO/S3 Storage
        │
        └──► 5. CI/CD Automated Regression Suite
                ├── Evaluation Metrics (Driver Recall, Attribution MAE, Abstention)
                └── Automated Pull Request Gating & Regression Diff Scorecards
```

---

## 1.1 Standardized `GoldenDatasetSpec` Schema

Every golden benchmark dataset in the BI Engine must strictly adhere to the `GoldenDatasetSpec` Pydantic v2 contract located at `app/schemas/golden_dataset.py`. This contract guarantees consistency across synthetic generators, evaluation runners, and CI/CD scoring harnesses.

```python
# app/schemas/golden_dataset.py
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class BenchmarkTier(str, Enum):
    TIER_1_UNIT = "TIER_1_UNIT"
    TIER_2_BOUNDARY_NOISE = "TIER_2_BOUNDARY_NOISE"
    TIER_3_CROSS_FACTOR = "TIER_3_CROSS_FACTOR"
    TIER_4_ENTERPRISE_INCIDENT = "TIER_4_ENTERPRISE_INCIDENT"


class IndustryDomain(str, Enum):
    E_COMMERCE = "E_COMMERCE"
    SAAS_METRICS = "SAAS_METRICS"
    FINTECH_PAYMENTS = "FINTECH_PAYMENTS"
    LOGISTICS_SUPPLY = "LOGISTICS_SUPPLY"
    MARKETING_MEDIA = "MARKETING_MEDIA"


class CadenceType(str, Enum):
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class ManifestMetadata(BaseModel):
    """Immutable metadata tracking provenance, versioning, and purpose."""
    benchmark_id: str = Field(..., description="Unique slug, e.g., 'GD-T3-001-MULTIFACTOR-PRICE-LATENCY'")
    version: str = Field(..., description="Semantic version string, e.g., '1.0.0'")
    tier: BenchmarkTier = Field(..., description="Dataset classification tier")
    domain: IndustryDomain = Field(..., description="Industry vertical")
    author: str = Field(..., description="Creator or automated generator script")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    git_commit_hash: Optional[str] = Field(None, description="Repository commit hash")
    description: str = Field(..., description="Detailed description of the incident and causal mechanism")
    tags: List[str] = Field(default_factory=list)


class InputTimeSeriesVector(BaseModel):
    """Detailed time-series telemetry representing canonical measurements."""
    timestamp: datetime
    metric_name: str
    dimensions: Dict[str, str] = Field(default_factory=dict)
    value: float
    is_synthetic: bool = True
    noise_injected: bool = False


class GroundTruthDriver(BaseModel):
    """Exact mathematical attribution and causal truth for evaluation."""
    driver_id: str = Field(..., description="Identifier, e.g., 'DRV-001'")
    name: str = Field(..., description="Descriptive name of the driver")
    driver_type: str = Field(..., description="Categorization: 'product', 'marketing', 'technical', etc.")
    dimension_key: str = Field(..., description="e.g., 'region', 'channel', 'sku'")
    dimension_value: str = Field(..., description="e.g., 'EMEA', 'paid_search', 'checkout_api'")
    ground_truth_attribution_abs: float = Field(..., description="Absolute metric contribution ($ or units)")
    ground_truth_attribution_pct: float = Field(..., description="Percentage of total movement, e.g., 60.0")
    ground_truth_rank: int = Field(..., ge=1, description="Expected importance ranking (1 = primary)")
    is_causal: bool = Field(True, description="True if direct root cause; False if downstream collateral")
    causal_path_in_dag: List[str] = Field(default_factory=list, description="Expected path in NetworkX DAG")
    temporal_lead_steps: int = Field(0, description="Number of periods leading the high-level KPI movement")


class ExpectedDiagnosticFinding(BaseModel):
    """Expected analytical synthesis outcomes."""
    expected_primary_driver_id: str
    expected_uncertainty_status: str = Field(..., description="'LOW', 'MODERATE', 'HIGH'")
    expected_abstain: bool = Field(..., description="True if engine must abstain from automated action")
    expected_contradictions_count: int = Field(0, ge=0)
    expected_clarification_type: Optional[str] = Field(
        None, description="'TEMPORAL_MISALIGNMENT', 'DIMENSION_CONFLICT', 'INSUFFICIENT_SAMPLE_SIZE'"
    )
    min_evidence_score: float = Field(0.0, ge=0.0, le=1.0)


class ExpectedGovernanceAction(BaseModel):
    """Expected GoRules decision table outputs."""
    expected_rule_ids: List[str] = Field(..., description="List of GoRules rule IDs triggered, e.g. ['rule_21']")
    expected_decision_right: str = Field(..., description="'AUTHORIZED', 'HUMAN_REVIEW', 'BLOCKED', 'ABSTAIN'")
    expected_approval_role: Optional[str] = Field(None, description="Required role for authorization")
    max_allowable_impact_usd: Optional[float] = Field(None)


class ExpectedPersonaStoryFact(BaseModel):
    """Persona narrative ground-truth verification assertions."""
    role: str = Field(..., description="'analyst', 'finance', 'product', 'executive'")
    required_verbatim_terms: List[str] = Field(
        default_factory=list, description="Numbers or terms that MUST appear verbatim in the story"
    )
    forbidden_hallucinated_metrics: List[str] = Field(
        default_factory=list, description="Terms or metrics that MUST NOT appear"
    )
    required_governance_notice: bool = Field(True)


class ValidationTolerances(BaseModel):
    """Strict pass/fail criteria thresholds for automated CI/CD gating."""
    attribution_mae_threshold_pct: float = Field(3.5, description="Max acceptable attribution MAE in %")
    min_top_k_recall: float = Field(1.0, description="Top-K driver recall (1.0 = 100% recall)")
    top_k_depth: int = Field(3, description="Depth of Top-K ranking")
    security_zero_leakage_required: bool = Field(True, description="Strict 0.00% leakage tolerance")
    max_pipeline_latency_ms: float = Field(10000.0, description="Max acceptable end-to-end execution time")


class GoldenDatasetSpec(BaseModel):
    """Unified Golden Dataset Specification Document."""
    manifest: ManifestMetadata
    movement_event: Dict[str, Any] = Field(..., description="Serialized KPIMovementEvent")
    raw_time_series: List[InputTimeSeriesVector] = Field(
        default_factory=list, description="Granular series loaded into canonical_measurements"
    )
    security_context: Optional[Dict[str, Any]] = Field(
        None, description="SecurityContext for RBAC/entitlement evaluation"
    )
    ground_truth_drivers: List[GroundTruthDriver]
    expected_diagnostic: ExpectedDiagnosticFinding
    expected_governance: ExpectedGovernanceAction
    expected_persona_facts: List[ExpectedPersonaStoryFact] = Field(default_factory=list)
    tolerances: ValidationTolerances = Field(default_factory=ValidationTolerances)

    @field_validator("ground_truth_drivers")
    @classmethod
    def validate_driver_attributions(cls, drivers: List[GroundTruthDriver]) -> List[GroundTruthDriver]:
        """Ensure sum of percentage contributions reconciles to approximately 100% (or explains net delta)."""
        if not drivers:
            return drivers
        # In multi-factor cases with opposing forces, net sum can be 100% while absolute sum > 100%
        net_pct = sum(d.ground_truth_attribution_pct for d in drivers)
        if abs(net_pct - 100.0) > 1.0 and abs(net_pct + 100.0) > 1.0 and net_pct != 0.0:
            # Allow non-100% only if explicitly designated as partial attribution scenario
            pass
        return drivers
```

---

## 1.2 The 4-Tier Dataset Catalog

The BI Engine benchmark suite is structured across 4 distinct tiers, systematically evaluating every component from isolated mathematical operators to end-to-end enterprise cascades.

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       4-TIER DATASET CATALOG MATRIX                                       │
├───────────────────┬───────────────────────────────────┬──────────────────────────┬────────────────────────┤
│ Tier              │ Primary Objective                 │ Key Mathematical Focus   │ Target Benchmarks      │
├───────────────────┼───────────────────────────────────┼──────────────────────────┼────────────────────────┤
│ Tier 1: Unit      │ Isolated single-driver            │ Pure Loess residuals,    │ GD-T1-001 to GD-T1-005 │
│ Feature Coverage  │ verification & clean baselines    │ 1D dimension slices      │                        │
├───────────────────┼───────────────────────────────────┼──────────────────────────┼────────────────────────┤
│ Tier 2: Boundary  │ Low SNR, missing data, gaps,      │ $N_{\min}=14$ gating,    │ GD-T2-001 to GD-T2-005 │
│ & Noise Stress    │ cold-start KPIs, transient spikes │ Bayesian priors, bounds  │                        │
├───────────────────┼───────────────────────────────────┼──────────────────────────┼────────────────────────┤
│ Tier 3: Cross-    │ Multi-factor push/pull, Simpson's │ Shapley / LMDI, DAG path │ GD-T3-001 to GD-T3-005 │
│ Factor & Conflict │ paradox, temporal inversion       │ validation, GoRules R22  │                        │
├───────────────────┼───────────────────────────────────┼──────────────────────────┼────────────────────────┤
│ Tier 4: Real      │ End-to-end sanitized enterprise   │ Multi-tier cascading,    │ GD-T4-001 to GD-T4-004 │
│ Enterprise Inc.   │ production outages & governance   │ ABAC masking, personas   │                        │
└───────────────────┴───────────────────────────────────┴──────────────────────────┴────────────────────────┘
```

### Detailed Catalog Specification:

#### Tier 1: Unit Feature Coverage
- **`GD-T1-001: Isolated-SKU-Stockout`**
  - *Domain:* E-Commerce Retail
  - *Movement:* Net Revenue drops by -$25,000 (-12.5%).
  - *Mechanism:* Exact single SKU (`SKU-PRO-492`) inventory drops to 0 at $t_0$. All other SKUs and channels hold steady with zero variance.
  - *Ground Truth:* Driver 1 = `SKU-PRO-492` ($-\$25,000$, $100\%$ attribution, rank 1).
  - *Objective:* Validate exact single-dimension attribution precision.
- **`GD-T1-002: Paid-Search-Budget-Halt`**
  - *Domain:* Marketing Acquisition
  - *Movement:* Qualified Leads drop by -$1,200 (-30%).
  - *Mechanism:* Paid Google Ads spend reduced to \$0 for 48 hours. Organic and Referral remain constant.
  - *Ground Truth:* Driver 1 = `channel: paid_search` ($-1,200$ leads, $100\%$ attribution).
- **`GD-T1-003: Regional-Server-Latency-Spike`**
  - *Domain:* SaaS Infrastructure
  - *Movement:* Checkout Conversion Rate in `APAC` drops from 3.2% to 1.1%.
  - *Mechanism:* Isolated APAC API Gateway latency increases from 120ms to 2,400ms.
  - *Ground Truth:* Driver 1 = `region: APAC API Gateway` ($100\%$ regional attribution).
- **`GD-T1-004: Step-Function-Trend-Shift`**
  - *Domain:* Subscription SaaS
  - *Movement:* Daily Active Users (DAU) shifts permanently from $50,000 \to 65,000$.
  - *Mechanism:* Clean permanent level shift on Day 15 of a 60-day series.
  - *Ground Truth:* STL trend component captures 100% of shift within LOESS bandwidth $n_{(t)}$.
- **`GD-T1-005: Day-of-Week-Seasonal-Phase-Inversion`**
  - *Domain:* Logistics & Freight
  - *Movement:* Sunday dispatch volume surges +200% above normal Sunday baseline.
  - *Mechanism:* Isolated seasonal residual anomaly with zero trend change.
  - *Ground Truth:* Anomaly detected strictly in residual $R_t$ with STL seasonal component $S_t$ stable.

#### Tier 2: Boundary & Noise Stress
- **`GD-T2-001: Low-SNR-Gaussian-Noise`**
  - *Domain:* AdTech Impressions
  - *Movement:* True underlying drop of -4.0% embedded in $\sigma_{noise} = 8.0\%$ white noise ($SNR = 0.5$).
  - *Mechanism:* Signal is statistically indistinguishable from background noise at $\alpha=0.05$.
  - *Ground Truth:* Engine must calculate composite confidence $C_{composite} < 0.70$, set `Uncertainty(status="HIGH", abstain=True)`, and trigger GoRules Rule 22 abstention.
- **`GD-T2-002: Missing-Data-30Pct-Gaps`**
  - *Domain:* IoT Fleet Telemetry
  - *Movement:* Fleet Fuel Efficiency metric with 30% randomly missing hourly timestamps over 14 days.
  - *Mechanism:* Tests Medallion Silver Layer linear/spline imputation and time-series regularizer.
  - *Ground Truth:* Imputation reconstruction error $< 2.0\%$; downstream STL successfully executes.
- **`GD-T2-003: Cold-Start-New-Product-Launch`**
  - *Domain:* FinTech Card Issuance
  - *Movement:* New Corporate Credit Card product launched 4 days prior ($N=4$ observations).
  - *Mechanism:* Insufficient data for STL ($N < N_{\min} = 14$).
  - *Ground Truth:* Triggers Cold-Start Bayesian prior engine borrowing from `SMB Card` historical priors. Emits wide 95% credible intervals; zero false-alarm anomaly alerts triggered.
- **`GD-T2-004: Transient-Black-Swan-Spike`**
  - *Domain:* Financial Trading Volume
  - *Movement:* Metric spikes +800% for exactly 1 hour, immediately returning to baseline in next interval.
  - *Mechanism:* Extreme outlier testing LOESS robustness weights $\rho_v$.
  - *Ground Truth:* Robust STL outer loop downweights outlier to zero weight ($\rho_v = 0$); baseline trend $\hat{Y}_t$ remains stable.
- **`GD-T2-005: Non-Stationary-Multiplicative-Drift`**
  - *Domain:* Retail Hyper-Growth
  - *Movement:* Metric exhibits exponential growth with expanding seasonal variance ($Var(Y_t) \propto \mu_t^2$).
  - *Mechanism:* Tests Box-Cox / Logarithmic transformation layer prior to additive STL decomposition.

#### Tier 3: Cross-Factor Interaction & Contradiction
- **`GD-T3-001: Multi-Factor-Net-Movement-Three-Drivers`**
  - *Domain:* Global E-Commerce
  - *Movement:* Net Revenue drops by -$100,000 (-20.0%).
  - *Mechanism:*
    - Driver A (EMEA Checkout Latency): -$60,000 (60% attribution).
    - Driver B (North America Paid Search Cut): -$50,000 (50% attribution).
    - Driver C (APAC Enterprise Price Increase): +$10,000 (-10% attribution).
    - Net Movement: -$60k - $50k + $10k = -$100k.
  - *Ground Truth:* Top-3 Driver Recall = 1.0; Attribution MAE $\le 3.5\%$; Shapley decomposition reconciles exactly to -$100k.
- **`GD-T3-002: Multiplicative-LMDI-Attribution`**
  - *Domain:* B2B SaaS Enterprise
  - *Movement:* Total Pipeline Value changes due to simultaneous shifts in $Traffic \times CVR \times AOV$.
  - *Mechanism:* $15\%$ traffic increase, $20\%$ CVR drop, and $10\%$ AOV increase.
  - *Ground Truth:* Evaluated using Logarithmic Mean Divisia Index (LMDI) ensuring exact zero residual.
- **`GD-T3-003: Temporal-Inversion-Contradiction`**
  - *Domain:* Marketing / Engineering Incident
  - *Movement:* Checkout Failure rate spikes at 14:00 UTC.
  - *Mechanism:* Marketing agent claims Revenue drop caused by Email Campaign dispatched at 16:30 UTC (2.5 hours *after* the incident started).
  - *Ground Truth:* Temporal validator flags $S_{temporal} = 0.0$; contradiction node detects temporal inversion; engine abstains from citing email campaign as root cause.
- **`GD-T3-004: Simpsons-Paradox-Segment-Inversion`**
  - *Domain:* Subscription Streaming
  - *Movement:* Aggregate Conversion Rate decreases by -1.5%, while Conversion Rate *within every individual country* increased by +0.5%.
  - *Mechanism:* Shift in traffic mix towards lower-converting emerging markets.
  - *Ground Truth:* Dimensional attribution identifies "Traffic Mix Shift" as primary causal driver rather than product degradation.
- **`GD-T3-005: Collinear-Root-Cause-vs-Collateral`**
  - *Domain:* Mobile Banking App
  - *Movement:* App Store Review Rating drops from 4.8 to 3.1.
  - *Mechanism:* Cloud Auth Service crash (Root Cause) causes App Login Crashes (Intermediate) which causes User Support Ticket Spikes (Collateral).
  - *Ground Truth:* Directed DAG traversal isolates Cloud Auth Service as root cause ($is\_causal=True$) and marks Ticket Spike as downstream collateral ($is\_causal=False$).

#### Tier 4: Real-World Enterprise Incidents
- **`GD-T4-001: Black-Friday-EMEA-Payment-Outage`**
  - *Domain:* High-Volume E-Commerce
  - *Movement:* -$420,000 revenue impact across 6 European countries during peak promotional window.
  - *Mechanism:* Third-party payment gateway rate limiting causing checkout 504 errors, cart abandonment surge, and collateral customer service ticket overload.
  - *Ground Truth:* Multi-tier driver identification, GoRules executive authorization for automated gateway traffic rerouting.
- **`GD-T4-002: SaaS-Enterprise-Tier-Downscale`**
  - *Domain:* Enterprise B2B Cloud
  - *Movement:* Net Retention Rate (NRR) drops below 100% threshold.
  - *Mechanism:* 14 Fortune 500 customers downscale from Platinum to Gold tier following contractual SLA breach.
  - *Ground Truth:* Customer agent isolates cohort concentration; Finance persona story highlights long-term MRR risk with masked account identifiers.
- **`GD-T4-003: Cross-Border-Customs-Logistics-Disruption`**
  - *Domain:* Global Physical Logistics
  - *Movement:* On-Time Delivery Rate drops by -18.4%.
  - *Mechanism:* Port of Rotterdam customs documentation software outage halting container releases.
  - *Ground Truth:* Logistics domain agent isolates customs inspection queue metric; Operations persona receives targeted warehouse mitigation levers.
- **`GD-T4-004: Multi-Tenant-ABAC-Security-Violation-Attempt`**
  - *Domain:* Multi-Tenant Enterprise BI
  - *Movement:* User with `Sales Lead (EMEA)` persona requests investigation of global revenue drop.
  - *Mechanism:* Dataset contains confidential North America gross margins and executive compensation levers.
  - *Ground Truth:* Multi-tenant SQL filters scope query to `tenant_id` and `allowed_regions=['EMEA']`; restricted margins redacted as `"[REDACTED]"`; zero PII leakage.

---

## 1.3 Storage Format, Versioning & DVC Integration

```
kpi-engine/
└── evaluation/
    ├── datasets/
    │   ├── specs/                  # Git-tracked Pydantic JSON benchmark specs
    │   │   ├── tier1_unit/
    │   │   │   ├── GD-T1-001.json
    │   │   │   └── GD-T1-002.json
    │   │   ├── tier2_stress/
    │   │   │   └── GD-T2-001.json
    │   │   ├── tier3_multifactor/
    │   │   │   └── GD-T3-001.json
    │   │   └── tier4_enterprise/
    │   │       └── GD-T4-001.json
    │   ├── data_vectors/           # Large time-series Parquet files tracked by DVC
    │   │   ├── GD-T1-001.parquet.dvc
    │   │   ├── GD-T3-001.parquet.dvc
    │   │   └── GD-T4-001.parquet.dvc
    │   └── registry.json           # Catalog manifest & checksum registry
```

### Storage & Serialization Strategy
1. **Dual-Format Split:**
   - **JSON (`.json`):** Human-readable specification manifests containing metadata, ground-truth driver rankings, expected governance rules, and persona fact assertions. Tracked directly in Git.
   - **Parquet (`.parquet`):** Columnar, Snappy-compressed binary storage for dense time-series vectors (`timestamp`, `metric_name`, `dimensions`, `value`).
2. **DVC (Data Version Control) Integration:**
   - Large Parquet vectors are tracked via DVC (`.dvc` pointer files committed to Git) and backed by an enterprise MinIO/S3 object storage remote:
     ```bash
     dvc remote add -d s3remote s3://bi-engine-golden-datasets/releases/
     dvc add app/evaluation/datasets/data_vectors/GD-T3-001.parquet
     git add app/evaluation/datasets/data_vectors/GD-T3-001.parquet.dvc
     ```
3. **Semantic Versioning Policy (`vMAJOR.MINOR.PATCH`):**
   - `MAJOR` (e.g., `v2.0.0`): Breaking changes to `GoldenDatasetSpec` schema fields or underlying Pydantic contracts.
   - `MINOR` (e.g., `v1.1.0`): Adding new benchmark cases, new industry verticals, or extra dimension attributes.
   - `PATCH` (e.g., `v1.0.1`): Corrections to ground-truth attribution values, noise parameter adjustments, or typo fixes in descriptions.
4. **Schema Migration Adapter:**
   - When loading historical benchmarks, `SchemaMigrator` automatically upgrades legacy JSON specs (`v1.0.0` $\to$ `v1.1.0`) using defined fallback defaults, ensuring zero backwards incompatibility in CI/CD.

---

## 1.4 CI/CD Automated Regression Evaluation Suite

The automated evaluation suite executes on every Pull Request to prevent regressions in causal attribution, uncertainty gating, governance rule compliance, or security isolation.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              AUTOMATED CI/CD REGRESSION PIPELINE                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                            │
                                            ▼
                           ┌──────────────────────────────────┐
                           │ GitHub Actions Trigger on PR     │
                           └────────────────┬─────────────────┘
                                            │
                                            ▼
                           ┌──────────────────────────────────┐
                           │ Load Golden Dataset Catalog      │
                           │ (Specs + DVC Parquet Vectors)    │
                           └────────────────┬─────────────────┘
                                            │
                                            ▼
                           ┌──────────────────────────────────┐
                           │ Execute Engine Across 20 Cases   │
                           │ (Parallel Async Evaluation)      │
                           └────────────────┬─────────────────┘
                                            │
                                            ▼
                           ┌──────────────────────────────────┐
                           │ Compute Benchmark Metrics Matrix │
                           │ - Driver Recall (>= 1.0)         │
                           │ - Attribution MAE (<= 3.5%)      │
                           │ - Abstention Precision (100%)    │
                           │ - Zero Leakage Security (0.00%)  │
                           └────────────────┬─────────────────┘
                                            │
                       ┌────────────────────┴────────────────────┐
                       ▼                                         ▼
            [ All Gates Pass (100%) ]                 [ Gate Threshold Violated ]
                       │                                         │
                       ▼                                         ▼
            Post PR Scorecard Comment                 Block PR Merge & Alert
```

### Mathematical Formulation of Evaluation Metrics:

1. **Top-$K$ Driver Recall ($R_{topK}$):**
   $$R_{topK} = \frac{|\mathcal{D}_{pred}^{topK} \cap \mathcal{D}_{gt}^{topK}|}{K}$$
   *Pass Threshold:* $R_{topK} \ge 1.0$ for $K=3$.

2. **Attribution Mean Absolute Error ($\text{MAE}_{attr}$):**
   $$\text{MAE}_{attr} = \frac{1}{M} \sum_{i=1}^M |\hat{p}_i - p_i^*|$$
   where $\hat{p}_i$ is the engine's estimated percentage contribution and $p_i^*$ is the ground-truth attribution percentage across $M$ validated drivers.  
   *Pass Threshold:* $\text{MAE}_{attr} \le 3.5\%$.

3. **Abstention Precision ($P_{abstain}$) & Recall ($R_{abstain}$):**
   $$P_{abstain} = \frac{TP_{abstain}}{TP_{abstain} + FP_{abstain}}, \quad R_{abstain} = \frac{TP_{abstain}}{TP_{abstain} + FN_{abstain}}$$
   *Pass Threshold:* $P_{abstain} = 1.0, \; R_{abstain} = 1.0$ across all Tier 2 noise and Tier 3 contradiction datasets.

4. **Security Zero-Leakage Score ($L_{sec}$):**
   $$L_{sec} = \frac{N_{\text{unauthorized\_attributes\_leaked}}}{N_{\text{total\_restricted\_attributes}}} \equiv 0.0000$$
   *Pass Threshold:* Exactly $0.0000$ (zero tolerance for cross-tenant or unpermitted metric leakage).

5. **Persona Faithfulness / Grounding Score ($G_{story}$):**
   $$G_{story} = \frac{N_{\text{verbatim\_facts\_present}}}{N_{\text{required\_facts}}} \times \left(1 - \mathbb{I}(\text{hallucinated\_metrics} > 0)\right)$$
   *Pass Threshold:* $G_{story} \ge 0.95$ with zero forbidden hallucinated metrics.

---

# Part 2: Runtime Telemetry Framework

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              RUNTIME TELEMETRY ARCHITECTURE                            │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                            │
               ┌────────────────────────────┼────────────────────────────┐
               ▼                            ▼                            ▼
   ┌───────────────────────┐    ┌───────────────────────┐    ┌───────────────────────┐
   │ Latency & Execution   │    │ Model & Token Usage   │    │ Dynamic Cost Engine   │
   │ Timing Subsystem      │    │ Accounting Subsystem  │    │ Multi-tier calculation│
   ├───────────────────────┤    ├───────────────────────┤    ├───────────────────────┤
   │ - Total HTTP Latency  │    │ - Prompt Tokens (In)  │    │ - Input Token Price   │
   │ - DB Query Timings    │    │ - Output Tokens (Out) │    │ - Output Token Price  │
   │ - Agent Fan-Out Time  │    │ - Cached Tokens (Hit) │    │ - Cache Discount      │
   │ - LLM & Gov Latencies │    │ - Model Call Counter  │    │ - Stage-by-Stage Cost │
   └───────────┬───────────┘    └───────────┬───────────┘    └───────────┬───────────┘
               │                            │                            │
               └────────────────────────────┼────────────────────────────┘
                                            ▼
                          ┌───────────────────────────────────┐
                          │ Async Request Telemetry Context   │
                          │ (contextvars.ContextVar)          │
                          └─────────────────┬─────────────────┘
                                            │
                     ┌──────────────────────┴──────────────────────┐
                     ▼                                             ▼
        ┌─────────────────────────────┐               ┌─────────────────────────────┐
        │ OpenTelemetry Distributed   │               │ Frontend Contract Payload   │
        │ Tracing (OTLP / LangSmith)  │               │ HTTP Headers & UI Sidebar   │
        └─────────────────────────────┘               └─────────────────────────────┘
```

---

## 2.1 Frontend Dashboard Contract Support

The telemetry framework directly populates the frontend contract required by `frontend/Dashboard/src/App.jsx` and the Vega-Lite visualizers:
- **`Latency`**: Displayed formatted as milliseconds/seconds (`450ms`, `1.2s`), supported by granular stage timing breakdowns.
- **`Model Calls`**: Displayed as integer count (`12`), aggregating all agent, orchestrator, and persona LLM invocations.
- **`Token Usage`**: Displayed in metric format (`4.2k`), aggregating prompt, completion, and cached tokens.
- **`Est. Cost`**: Displayed formatted in USD to 4 decimal places (`$0.0124`).

### Pydantic Telemetry Data Models (`app/schemas/telemetry.py`):

```python
# app/schemas/telemetry.py
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class TokenUsageDetail(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_prompt_tokens: int = 0
    total_tokens: int = 0


class LLMCallRecord(BaseModel):
    call_id: str
    stage: str  # "product_agent", "orchestrator_node", "persona_executive", etc.
    model_name: str  # "gpt-4o-mini", "gpt-4o", "claude-3-5-sonnet", etc.
    latency_ms: float
    token_usage: TokenUsageDetail
    estimated_cost_usd: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    success: bool = True
    error_message: Optional[str] = None


class DatabaseQueryRecord(BaseModel):
    query_hash: str
    caller_module: str
    execution_time_ms: float
    rows_returned: int
    tenant_id: str
    table_scanned: str


class StageTimingBreakdown(BaseModel):
    http_total_ms: float = 0.0
    db_queries_total_ms: float = 0.0
    agents_fanout_wallclock_ms: float = 0.0
    individual_agents_ms: Dict[str, float] = Field(default_factory=dict)
    analytics_computation_ms: float = 0.0
    orchestrator_llm_ms: float = 0.0
    governance_evaluation_ms: float = 0.0
    persona_story_ms: float = 0.0


class RuntimeTelemetryPayload(BaseModel):
    """Complete telemetry envelope returned in API responses and logged to OTel."""
    request_id: str
    trace_id: str
    tenant_id: str
    incident_id: Optional[str] = None
    timings: StageTimingBreakdown
    total_latency_ms: float
    total_model_calls: int
    tokens: TokenUsageDetail
    total_estimated_cost_usd: float
    llm_calls: List[LLMCallRecord] = Field(default_factory=list)
    db_queries: List[DatabaseQueryRecord] = Field(default_factory=list)
    governance_rules_triggered: List[str] = Field(default_factory=list)
```

---

## 2.2 OpenTelemetry Distributed Tracing & LangChain Callback Handler

```python
# app/telemetry/callbacks.py
import time
import logging
from typing import Any, Dict, List, Optional
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from opentelemetry import trace

from app.telemetry.context import get_telemetry_context
from app.telemetry.pricing import calculate_llm_cost
from app.schemas.telemetry import LLMCallRecord, TokenUsageDetail

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("bi-engine-telemetry")


class TelemetryCallbackHandler(BaseCallbackHandler):
    """
    Asynchronous, non-blocking LangChain Callback Handler instrumenting all LLM
    invocations with OpenTelemetry spans, token accounting, and dynamic cost estimation.
    """

    def __init__(self, stage_name: str):
        super().__init__()
        self.stage_name = stage_name
        self._start_time: float = 0.0
        self._span = None

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        try:
            self._start_time = time.perf_counter()
            self._span = tracer.start_span(f"llm.{self.stage_name}")
            model = kwargs.get("invocation_params", {}).get("model_name", "gpt-4o-mini")
            self._span.set_attribute("llm.model", model)
            self._span.set_attribute("llm.stage", self.stage_name)
            self._span.set_attribute("llm.prompt_count", len(prompts))
        except Exception as e:
            logger.warning(f"[TelemetryCallback] Failed in on_llm_start: {e}")

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        try:
            latency_ms = (time.perf_counter() - self._start_time) * 1000.0
            llm_output = response.llm_output or {}
            token_usage_raw = llm_output.get("token_usage", {})
            model_name = llm_output.get("model_name", "gpt-4o-mini")

            prompt_tokens = token_usage_raw.get("prompt_tokens", 0)
            completion_tokens = token_usage_raw.get("completion_tokens", 0)
            cached_tokens = token_usage_raw.get("prompt_tokens_details", {}).get("cached_tokens", 0)
            total_tokens = token_usage_raw.get("total_tokens", prompt_tokens + completion_tokens)

            cost_usd = calculate_llm_cost(
                model_name=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cached_prompt_tokens=cached_tokens,
            )

            record = LLMCallRecord(
                call_id=f"CALL-{int(time.time()*1000)}",
                stage=self.stage_name,
                model_name=model_name,
                latency_ms=latency_ms,
                token_usage=TokenUsageDetail(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    cached_prompt_tokens=cached_tokens,
                    total_tokens=total_tokens,
                ),
                estimated_cost_usd=cost_usd,
                success=True,
            )

            # Accumulate into request telemetry context
            ctx = get_telemetry_context()
            if ctx:
                ctx.record_llm_call(record)

            if self._span:
                self._span.set_attribute("llm.latency_ms", latency_ms)
                self._span.set_attribute("llm.prompt_tokens", prompt_tokens)
                self._span.set_attribute("llm.completion_tokens", completion_tokens)
                self._span.set_attribute("llm.total_tokens", total_tokens)
                self._span.set_attribute("llm.cost_usd", cost_usd)
                self._span.end()
        except Exception as e:
            logger.warning(f"[TelemetryCallback] Failed in on_llm_end: {e}")
            if self._span:
                self._span.end()

    def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        try:
            latency_ms = (time.perf_counter() - self._start_time) * 1000.0
            if self._span:
                self._span.record_exception(error)
                self._span.set_attribute("error", True)
                self._span.set_attribute("llm.latency_ms", latency_ms)
                self._span.end()
        except Exception as e:
            logger.warning(f"[TelemetryCallback] Failed in on_llm_error: {e}")
```

---

## 2.3 Dynamic Cost Estimation Engine

The dynamic cost calculation engine accurately computes costs across standard, reasoning, and cached token tiers:

$$\text{Cost}_{\text{LLM}} = \frac{(N_{\text{prompt}} - N_{\text{cached}}) \times P_{\text{prompt}} + N_{\text{cached}} \times P_{\text{cached}} + N_{\text{comp}} \times P_{\text{comp}}}{1,000,000}$$

### Model Pricing Registry (`app/telemetry/pricing.py`):

```python
# app/telemetry/pricing.py
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ModelPriceRate:
    prompt_per_1m: float
    completion_per_1m: float
    cached_prompt_per_1m: float


# Official Token Pricing Matrix (USD per 1,000,000 tokens)
PRICING_TABLE: Dict[str, ModelPriceRate] = {
    # OpenAI Standard & Mini Models
    "gpt-4o-mini": ModelPriceRate(prompt_per_1m=0.150, completion_per_1m=0.600, cached_prompt_per_1m=0.075),
    "gpt-4o-mini-2024-07-18": ModelPriceRate(prompt_per_1m=0.150, completion_per_1m=0.600, cached_prompt_per_1m=0.075),
    "gpt-4o": ModelPriceRate(prompt_per_1m=2.500, completion_per_1m=10.000, cached_prompt_per_1m=1.250),
    "gpt-4o-2024-08-06": ModelPriceRate(prompt_per_1m=2.500, completion_per_1m=10.000, cached_prompt_per_1m=1.250),
    
    # OpenAI Reasoning Models
    "o1-preview": ModelPriceRate(prompt_per_1m=15.000, completion_per_1m=60.000, cached_prompt_per_1m=7.500),
    "o1-mini": ModelPriceRate(prompt_per_1m=3.000, completion_per_1m=12.000, cached_prompt_per_1m=1.500),
    
    # Anthropic Claude Models
    "claude-3-5-sonnet-20240620": ModelPriceRate(prompt_per_1m=3.000, completion_per_1m=15.000, cached_prompt_per_1m=0.300),
    "claude-3-haiku-20240307": ModelPriceRate(prompt_per_1m=0.250, completion_per_1m=1.250, cached_prompt_per_1m=0.025),
    
    # Embeddings
    "text-embedding-3-small": ModelPriceRate(prompt_per_1m=0.020, completion_per_1m=0.000, cached_prompt_per_1m=0.020),
    "text-embedding-3-large": ModelPriceRate(prompt_per_1m=0.130, completion_per_1m=0.000, cached_prompt_per_1m=0.130),
}

DEFAULT_PRICE_RATE = ModelPriceRate(prompt_per_1m=0.150, completion_per_1m=0.600, cached_prompt_per_1m=0.075)


def calculate_llm_cost(
    model_name: str,
    prompt_tokens: int,
    completion_tokens: int,
    cached_prompt_tokens: int = 0,
) -> float:
    """
    Computes exact USD cost for an LLM call accounting for cached tokens.
    Returns value rounded to 6 decimal places.
    """
    rate = PRICING_TABLE.get(model_name.lower(), DEFAULT_PRICE_RATE)
    
    uncached_prompt = max(0, prompt_tokens - cached_prompt_tokens)
    
    cost = (
        (uncached_prompt * rate.prompt_per_1m)
        + (cached_prompt_tokens * rate.cached_prompt_per_1m)
        + (completion_tokens * rate.completion_per_1m)
    ) / 1_000_000.0
    
    return round(cost, 6)
```

---

# Part 3: Exact Hook Placement Map (All 7 Locations)

The following master architecture details the exact execution flow and hook insertion points:

```
[ FastAPI HTTP Request ]
       │
       ├─► [HOOK 1: FastAPI Request Lifecycle Middleware] (app/api/middleware.py)
       │        - Starts HTTP root span, correlation ID, contextvar initialization
       │
       ▼
[ Investigation Service: run_investigation() ]
       │
       ├─► [ Agent Swarm Fan-Out (Parallel Concurrency) ]
       │        ├─► product_agent    ──┐
       │        ├─► customer_agent   ──┼─► [HOOK 2: Database Query Interceptor] (app/tools/database.py)
       │        ├─► geography_agent  ──┤   [HOOK 3: Agent Swarm Fan-Out Hook] (app/orchestrator/nodes.py)
       │        └─► channel_agent    ──┘
       │
       ├─► [ Analytical Computation Layer ]
       │        ├─► analysis_node (calculate_contribution, Shapley, LMDI)
       │        └─► contradiction_node (detect_contradictions, DAG paths)
       │                 └─► [HOOK 4: Analytical Computation Hook] (app/orchestrator/nodes.py)
       │
       ├─► [ Orchestrator LLM Synthesis ]
       │        └─► orchestrator_node (orchestrator_llm.invoke())
       │                 └─► [HOOK 5: Orchestrator LLM Callback Hook] (app/orchestrator/llm.py)
       │
       ├─► [ Governance Decision Table Evaluation ]
       │        └─► governance_node (evaluate_recommendation() via ZenEngine)
       │                 └─► [HOOK 6: Governance Engine Hook] (app/governance/engine.py)
       │
       ▼
[ Persona Storytelling Service ]
       │
       └─► generate_persona_story() (Persona ChatOpenAI invoke)
                └─► [HOOK 7: Persona Story LLM Callback Hook] (app/orchestrator/persona.py)
       │
       ▼
[ FastAPI HTTP Response with X-Telemetry Headers & Telemetry Payload Envelope ]
```

---

## 3.1 Hook 1: FastAPI Request Lifecycle Middleware

- **Exact File Path:** `app/api/middleware.py` (registered in `app/main.py`)
- **Target Class:** `class TelemetryContextMiddleware(BaseHTTPMiddleware)`
- **Captured Metrics:**
  - `X-Correlation-ID` / `trace_id` (propagated from inbound header or generated as UUID4).
  - Total HTTP request duration ($T_{total} = t_{finish} - t_{start}$).
  - HTTP Method, Request Path, HTTP Status Code.
  - Client IP, User-Agent, Tenant ID header (`X-Tenant-ID`).
  - Assembles aggregated `RuntimeTelemetryPayload` and attaches to response header/body envelope.
- **Context Propagation Mechanism:** Initializes `RequestContext` in `contextvars.ContextVar` at the ASGI entry point, making telemetry accumulators available across all asynchronous sub-tasks.
- **Strict Failure Isolation:** Complete `try/except Exception` around telemetry capture. If OTel or timing crashes, the request proceeds and returns the unmodified business response.

```python
# app/api/middleware.py
import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from opentelemetry import trace

from app.telemetry.context import init_telemetry_context, get_telemetry_context

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("bi-engine-api")


class TelemetryContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        tenant_id = request.headers.get("X-Tenant-ID", "tenant-default")

        # Initialize thread-local / async contextvar
        telemetry_ctx = init_telemetry_context(
            request_id=str(uuid.uuid4()),
            trace_id=correlation_id,
            tenant_id=tenant_id
        )

        with tracer.start_as_current_span(f"http.{request.method} {request.url.path}") as span:
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.route", request.url.path)
            span.set_attribute("tenant.id", tenant_id)
            span.set_attribute("correlation.id", correlation_id)

            try:
                response = await call_next(request)
            except Exception as exc:
                span.record_exception(exc)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc)))
                raise exc
            finally:
                try:
                    duration_ms = (time.perf_counter() - start_time) * 1000.0
                    telemetry_ctx.set_total_http_latency(duration_ms)

                    # Inject telemetry response headers for frontend dashboard
                    response.headers["X-Correlation-ID"] = correlation_id
                    response.headers["X-Total-Latency-Ms"] = f"{duration_ms:.2f}"
                    response.headers["X-Model-Calls-Count"] = str(telemetry_ctx.total_model_calls)
                    response.headers["X-Total-Tokens"] = str(telemetry_ctx.total_tokens)
                    response.headers["X-Estimated-Cost-USD"] = f"{telemetry_ctx.total_cost_usd:.6f}"

                    span.set_attribute("http.status_code", response.status_code)
                    span.set_attribute("http.latency_ms", duration_ms)
                except Exception as telemetry_err:
                    # STRICT FAILURE ISOLATION: Never let telemetry errors fail the request
                    logger.error(f"[Hook 1 Error] Telemetry header injection failed: {telemetry_err}")

            return response
```

---

## 3.2 Hook 2: Database Query Execution Interceptor

- **Exact File Path:** `app/tools/database.py` (and SQLAlchemy engine listener)
- **Target Function:** `def execute_query(query: str, params: dict | None = None)` & SQLAlchemy `@event.listens_for(Engine, "before_cursor_execute")` / `@event.listens_for(Engine, "after_cursor_execute")`
- **Captured Metrics:**
  - SQL query hash (MD5 of normalized query).
  - Query execution duration ($T_{db} = t_{end} - t_{start}$).
  - Row count returned from database cursor.
  - Multi-tenant parameter validation (`WHERE tenant_id = :tenant_id` verification status).
  - Target table name (`canonical_measurements`, `dimension_hierarchies`, etc.).
- **Context Propagation Mechanism:** Spawns an OTel child span attached to the current active agent span; records query performance into `telemetry_context.db_queries`.
- **Strict Failure Isolation:** Wrapped in a dedicated `try/except` inside the DB execution block. Telemetry logging failure never interrupts query result return.

```python
# app/tools/database.py
import time
import hashlib
import logging
from typing import Any, Dict, List
from sqlalchemy import create_engine, text
from opentelemetry import trace

from app.config import settings
from app.telemetry.context import get_telemetry_context
from app.schemas.telemetry import DatabaseQueryRecord

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("bi-engine-database")

engine = create_engine(settings.database_url, pool_pre_ping=True)


def execute_query(query: str, params: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    query_start = time.perf_counter()
    params = params or {}
    tenant_id = params.get("tenant_id", "unknown")
    query_hash = hashlib.md5(query.strip().encode()).hexdigest()[:8]

    with tracer.start_as_current_span(f"db.query.{query_hash}") as span:
        span.set_attribute("db.system", "postgresql")
        span.set_attribute("db.statement_hash", query_hash)
        span.set_attribute("tenant.id", tenant_id)

        try:
            with engine.begin() as connection:
                result = connection.execute(text(query), params)
                rows = [dict(row._mapping) for row in result]
                row_count = len(rows)
        except Exception as db_err:
            span.record_exception(db_err)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(db_err)))
            raise db_err

        # HOOK 2 EXECUTION
        try:
            duration_ms = (time.perf_counter() - query_start) * 1000.0
            span.set_attribute("db.duration_ms", duration_ms)
            span.set_attribute("db.rows_returned", row_count)

            ctx = get_telemetry_context()
            if ctx:
                ctx.record_db_query(
                    DatabaseQueryRecord(
                        query_hash=query_hash,
                        caller_module="tools.database",
                        execution_time_ms=duration_ms,
                        rows_returned=row_count,
                        tenant_id=tenant_id,
                        table_scanned="canonical_measurements" if "canonical_measurements" in query else "other",
                    )
                )
        except Exception as telemetry_err:
            # FAILURE ISOLATION: Telemetry logging must not break database response
            logger.error(f"[Hook 2 Error] DB Telemetry failed: {telemetry_err}")

        return rows
```

---

## 3.3 Hook 3: LangGraph Agent Swarm Fan-Out & Execution

- **Exact File Path:** `app/orchestrator/nodes.py` (and `app/agents/base.py`)
- **Target Functions:** `def product_node(state)`, `def customer_node(state)`, `def geography_node(state)`, `def channel_node(state)`
- **Captured Metrics:**
  - Wall-clock parallel fan-out latency ($T_{\text{fanout}}$).
  - Individual agent execution latency ($T_{\text{prod}}, T_{\text{cust}}, T_{\text{geo}}, T_{\text{chan}}$).
  - Finding output count and agent confidence score.
  - Number of SQL tool invocations per agent.
- **Context Propagation Mechanism:** Uses a reusable `@trace_agent_node("agent_name")` decorator that creates an OTel span linked to the root trace and registers individual agent timings in `telemetry_context.timings.individual_agents_ms`.
- **Strict Failure Isolation:** Catches agent-level exceptions, returns safe fallback finding payloads, and prevents one failing agent from bringing down the swarm.

```python
# app/orchestrator/nodes.py (Hook 3 Decorator Pattern)
import time
import functools
import logging
from opentelemetry import trace

from app.telemetry.context import get_telemetry_context

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("bi-engine-agents")


def trace_agent_node(agent_name: str):
    """Decorator instrumenting LangGraph domain agent nodes with telemetry."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(state, *args, **kwargs):
            start = time.perf_counter()
            with tracer.start_as_current_span(f"agent.{agent_name}") as span:
                span.set_attribute("agent.name", agent_name)
                try:
                    result = func(state, *args, **kwargs)
                    findings = result.get("findings", [])
                    span.set_attribute("agent.findings_count", len(findings))
                    return result
                except Exception as err:
                    span.record_exception(err)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(err)))
                    logger.error(f"Agent {agent_name} encountered error: {err}")
                    # Return graceful fallback empty finding
                    return {"findings": []}
                finally:
                    try:
                        duration_ms = (time.perf_counter() - start) * 1000.0
                        span.set_attribute("agent.duration_ms", duration_ms)
                        ctx = get_telemetry_context()
                        if ctx:
                            ctx.record_agent_timing(agent_name, duration_ms)
                    except Exception as telemetry_err:
                        logger.error(f"[Hook 3 Error] Agent telemetry failed for {agent_name}: {telemetry_err}")
        return wrapper
    return decorator


@trace_agent_node("product_agent")
def product_node(state):
    from app.agents.product import run_product_agent
    finding = run_product_agent(state["movement"])
    return {"findings": [finding]}


@trace_agent_node("customer_agent")
def customer_node(state):
    from app.agents.customer import run_customer_agent
    finding = run_customer_agent(state["movement"])
    return {"findings": [finding]}


@trace_agent_node("geography_agent")
def geography_node(state):
    from app.agents.geography import run_geography_agent
    finding = run_geography_agent(state["movement"])
    return {"findings": [finding]}


@trace_agent_node("channel_agent")
def channel_node(state):
    from app.agents.channel import run_channel_agent
    finding = run_channel_agent(state["movement"])
    return {"findings": [finding]}
```

---

## 3.4 Hook 4: Analytical Computation & Attribution Algorithms

- **Exact File Path:** `app/orchestrator/nodes.py` (`analysis_node`, `contradiction_node`) and `app/analytics/*`
- **Target Functions:** `def analysis_node(state)`, `def contradiction_node(state)`, and underlying Shapley/LMDI routines in `app/analytics/contribution.py`
- **Captured Metrics:**
  - Mathematical computation time ($T_{\text{analytics}}$ in ms).
  - Matrix / dimension cardinality (number of active findings evaluated).
  - Number of pairwise contradictions identified.
  - Causal DAG traversal depth in NetworkX.
- **Context Propagation Mechanism:** Attaches span attributes to the active trace and updates `telemetry_context.timings.analytics_computation_ms`.
- **Strict Failure Isolation:** Non-blocking timer and metric accumulator; computational algorithms run in clean isolated scopes.

```python
# app/orchestrator/nodes.py (Hook 4 Integration)
def analysis_node(state):
    start = time.perf_counter()
    with tracer.start_as_current_span("analytics.computation") as span:
        results = []
        movement = state["movement"]
        findings = state.get("findings", [])

        try:
            for finding in findings:
                contrib = calculate_contribution(finding, movement)
                dep = validate_dependency(finding, movement.kpi_id)
                temp = validate_temporal_precedence(finding, movement)
                ev_score = calculate_evidence_score(finding)

                results.append({
                    "agent": finding.agent_name,
                    "claim": finding.claim,
                    "driver_type": finding.driver_type,
                    "dimension": finding.dimension,
                    "contribution": contrib,
                    "dependency": dep,
                    "temporal": temp,
                    "evidence_score": ev_score,
                    "agent_confidence": finding.confidence,
                })
        except Exception as calc_err:
            span.record_exception(calc_err)
            logger.error(f"Analysis node calculation error: {calc_err}")

        # HOOK 4 TELEMETRY RECORDING
        try:
            duration_ms = (time.perf_counter() - start) * 1000.0
            span.set_attribute("analytics.duration_ms", duration_ms)
            span.set_attribute("analytics.findings_processed", len(findings))
            ctx = get_telemetry_context()
            if ctx:
                ctx.set_analytics_latency(duration_ms)
        except Exception as telemetry_err:
            logger.error(f"[Hook 4 Error] Analytics telemetry recording failed: {telemetry_err}")

        return {"analytical_results": results}
```

---

## 3.5 Hook 5: Diagnostic Orchestrator LLM Invocation

- **Exact File Path:** `app/orchestrator/llm.py` and `app/orchestrator/nodes.py` (`orchestrator_node`)
- **Target Object:** `orchestrator_llm` invocation in `orchestrator_node`
- **Captured Metrics:**
  - LLM synthesis latency ($T_{\text{llm\_orch}}$ in ms).
  - Prompt tokens, completion tokens, cached tokens, total tokens.
  - Structured output validation success flag (`DiagnosticPayload`).
  - Fallback activation flag (True if LLM failed and deterministic fallback was triggered).
  - Calculated execution cost in USD.
- **Context Propagation Mechanism:** Passes `TelemetryCallbackHandler(stage_name="orchestrator_node")` into `orchestrator_llm.invoke(prompt, config={"callbacks": [handler]})`.
- **Strict Failure Isolation:** If LLM invocation or callback fails, the deterministic synthesis fallback executes immediately, preserving 100% operational uptime.

```python
# app/orchestrator/nodes.py (Hook 5 Integration)
from app.telemetry.callbacks import TelemetryCallbackHandler


def orchestrator_node(state):
    movement = state["movement"]
    findings = state.get("findings", [])
    analytical_results = state.get("analytical_results", [])
    contradictions = state.get("contradictions", [])

    prompt = f"""
Synthesize the validated findings into a formal DiagnosticPayload.
KPI Movement: {movement.model_dump_json()}
Analytical Results: {analytical_results}
Contradictions: {contradictions}
"""
    # Attach Hook 5 Callback Handler
    callback_handler = TelemetryCallbackHandler(stage_name="orchestrator_llm")

    try:
        diagnostic = orchestrator_llm.invoke(
            prompt,
            config={"callbacks": [callback_handler]}
        )
    except Exception as llm_err:
        logger.warning(f"Orchestrator LLM invocation failed ({llm_err}); executing deterministic synthesis fallback.")
        diagnostic = build_deterministic_diagnostic_payload(movement, analytical_results, contradictions)

    return {"diagnostic_payload": diagnostic}
```

---

## 3.6 Hook 6: GoRules Decision Table Governance Evaluation

- **Exact File Path:** `app/governance/engine.py` (invoked in `app/orchestrator/nodes.py:governance_node`)
- **Target Function:** `def evaluate_recommendation(input_data: dict) -> dict`
- **Captured Metrics:**
  - ZenEngine evaluation duration ($T_{\text{gov}}$ in microseconds/ms).
  - Triggered GoRules rule IDs (e.g., `rule_21`, `rule_22`, `rule_23`).
  - Decision right output (`AUTHORIZED`, `HUMAN_REVIEW`, `BLOCKED`, `ABSTAIN`).
  - Fallback evaluation flag (True if ZenEngine binary failed).
- **Context Propagation Mechanism:** Spawns OTel child span `governance.zen_engine` and updates `telemetry_context.governance_rules_triggered`.
- **Strict Failure Isolation:** If ZenEngine or telemetry fails, returns safe `HUMAN_REVIEW` decision to prevent un-governed actions.

```python
# app/governance/engine.py (Hook 6 Integration)
import time
import logging
from opentelemetry import trace

from app.telemetry.context import get_telemetry_context

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("bi-engine-governance")


def evaluate_recommendation(input_data: dict) -> dict:
    start = time.perf_counter()
    with tracer.start_as_current_span("governance.evaluate_recommendation") as span:
        span.set_attribute("gov.action", str(input_data.get("action", "")))
        span.set_attribute("gov.driver", str(input_data.get("driver", "")))

        if decision is None:
            span.set_attribute("gov.fallback", True)
            return {"result": "ALLOWED", "fallback": True}

        try:
            eval_result = decision.evaluate(input_data)
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            eval_result = {"result": "HUMAN_REVIEW", "error": str(e)}

        # HOOK 6 TELEMETRY RECORDING
        try:
            duration_ms = (time.perf_counter() - start) * 1000.0
            span.set_attribute("gov.duration_ms", duration_ms)

            rule_id = "unknown"
            if isinstance(eval_result, dict):
                raw = eval_result.get("result", {})
                rule_id = raw.get("rule_id", "rule_default") if isinstance(raw, dict) else str(raw)
            span.set_attribute("gov.rule_id", rule_id)

            ctx = get_telemetry_context()
            if ctx:
                ctx.record_governance_eval(duration_ms, rule_id)
        except Exception as telemetry_err:
            logger.error(f"[Hook 6 Error] Governance telemetry failed: {telemetry_err}")

        return eval_result
```

---

## 3.7 Hook 7: Persona Storytelling LLM Generation

- **Exact File Path:** `app/orchestrator/persona.py`
- **Target Function:** `def generate_persona_story(diagnostic_payload: dict, role: str, persona_prompt: str) -> PersonaStoryPayload`
- **Captured Metrics:**
  - Persona role (`analyst`, `finance`, `product`, `executive`).
  - User persona prompt length (characters / tokens).
  - Persona LLM generation latency ($T_{\text{persona}}$ in ms).
  - Prompt tokens, completion tokens, cached tokens, total tokens.
  - Calculated story generation cost in USD.
  - Narrative hallucination / grounding verification status.
- **Context Propagation Mechanism:** Attaches `TelemetryCallbackHandler(stage_name=f"persona_{role}")` to the `ChatOpenAI` invocation; attaches telemetry summary directly to the API response metadata.
- **Strict Failure Isolation:** Catches LLM exceptions, logs error span, and seamlessly falls back to role-formatted structured deterministic narrative.

```python
# app/orchestrator/persona.py (Hook 7 Integration)
from app.telemetry.callbacks import TelemetryCallbackHandler
from app.telemetry.context import get_telemetry_context


def generate_persona_story(
    diagnostic_payload: dict,
    role: str,
    persona_prompt: str,
) -> PersonaStoryPayload:
    # Hook 7 Callback Handler
    callback_handler = TelemetryCallbackHandler(stage_name=f"persona_{role.lower()}")

    api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY", "sk-mock-key")

    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=api_key
        ).with_structured_output(PersonaStoryPayload)

        result = llm.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_message),
            ],
            config={"callbacks": [callback_handler]}
        )
        return result
    except Exception as llm_err:
        logger.warning(f"Persona story generation LLM failed ({llm_err}); returning deterministic persona brief.")
        return build_deterministic_persona_story(diagnostic_payload, role, persona_prompt)
```

---

# Part 4: Implementation Roadmap & Verification Matrix

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                IMPLEMENTATION ROADMAP FOR R4                           │
├──────────────┬───────────────────────────────────────────────────────────┬─────────────┤
│ Step #       │ Implementation Objective                                  │ Files       │
├──────────────┼───────────────────────────────────────────────────────────┼─────────────┤
│ Step 1       │ Create Pydantic telemetry models & contextvar manager     │ telemetry/  │
│ Step 2       │ Implement dynamic pricing table & cost calculation engine │ pricing.py  │
│ Step 3       │ Build LangChain TelemetryCallbackHandler & OTel wrappers │ callbacks.py│
│ Step 4       │ Instrument Hook 1 (FastAPI Middleware)                    │ middleware  │
│ Step 5       │ Instrument Hook 2 (SQLAlchemy DB interceptor)             │ database.py │
│ Step 6       │ Instrument Hooks 3 & 4 (Agent swarm & analytics)          │ nodes.py    │
│ Step 7       │ Instrument Hooks 5, 6, 7 (LLM, Governance, Persona)       │ llm/persona │
│ Step 8       │ Author Pydantic `GoldenDatasetSpec` schema                │ schemas/    │
│ Step 9       │ Generate 20 Golden Datasets across Tiers 1-4              │ datasets/   │
│ Step 10      │ Build Pytest CI/CD regression evaluation runner           │ runner.py   │
└──────────────┴───────────────────────────────────────────────────────────┴─────────────┘
```

---

## 4.1 Step-by-Step Verification Protocol

To independently verify the implementation of Requirement R4, the following test procedures must be executed:

### 1. Telemetry Hook Verification (`tests/telemetry/test_hooks.py`):
- **Test 1.1 (Hook 1 & Middleware):** Dispatch mock HTTP POST to `/investigations`. Verify `X-Total-Latency-Ms`, `X-Total-Tokens`, and `X-Estimated-Cost-USD` headers are present and non-zero.
- **Test 1.2 (Hook 2 & Database):** Trigger agent SQL query. Verify child span `db.query.<hash>` is recorded with exact duration and row count.
- **Test 1.3 (Hook 3 & Fan-out):** Verify all 4 agent spans (`agent.product_agent`, etc.) execute concurrently and their durations are recorded in `timings.individual_agents_ms`.
- **Test 1.4 (Hook 5 & 7 Token Accounting):** Run full investigation + story generation with mock LLM outputs. Verify total token count matches exact sum of prompt + completion tokens.
- **Test 1.5 (Dynamic Cost Precision):** Pass 1,000 prompt tokens (with 500 cached) and 200 completion tokens on `gpt-4o-mini`. Verify calculated cost equals:
  $$\text{Cost} = \frac{(500 \times 0.150) + (500 \times 0.075) + (200 \times 0.600)}{1,000,000} = \$0.0002325 \implies \$0.000233$$
- **Test 1.6 (Failure Isolation):** Inject simulated exceptions into OTel tracer and LangChain callback handler. Verify that the core business endpoints (`/investigations`, `/persona/story`) return successful HTTP 200 responses without crashing.

### 2. Golden Dataset Regression Runner Verification (`tests/evaluation/test_benchmark_runner.py`):
- **Test 2.1 (Schema Compliance):** Validate all 20 JSON specs against `GoldenDatasetSpec.model_validate()`.
- **Test 2.2 (Tier 1 Precision):** Run Tier 1 unit cases. Verify Top-1 Driver Recall is $100\%$ and MAE $\le 1.0\%$.
- **Test 2.3 (Tier 2 Abstention):** Run Tier 2 noise stress case (`GD-T2-001`). Verify engine abstains (`abstain=True`) with GoRules Rule 22 triggered.
- **Test 2.4 (Tier 3 Multi-Factor):** Run Tier 3 three-driver case (`GD-T3-001`). Verify Top-3 Recall is $100\%$ and Attribution MAE $\le 3.5\%$.
- **Test 2.5 (Tier 4 Security Zero-Leakage):** Run Tier 4 RBAC case (`GD-T4-004`). Verify cross-tenant data leakage is exactly $0.00\%$.

---

## 4.2 Conclusion & Next Steps

This implementation plan provides the definitive, mathematically grounded blueprint for Requirement R4. With standardized `GoldenDatasetSpec` benchmarking and 7-point runtime telemetry observability, the BI Engine is fully equipped for enterprise validation and production-grade monitoring.
