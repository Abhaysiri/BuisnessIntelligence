"""
Golden Datasets Generation & 4-Tier Catalog (§5.1)
Defines GoldenDatasetSpec Pydantic V2 schema and generates 19 benchmark incidents across 4 tiers:
- Tier 1: Feature Unit Coverage (5 incidents)
- Tier 2: Boundary & Noise Stress Testing (5 incidents)
- Tier 3: Cross-Factor & Contradiction Stress (5 incidents)
- Tier 4: Enterprise Incident Scenarios (4 incidents)
"""

import math
import random
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class GroundTruthDriver(BaseModel):
    driver_name: str
    dimension_key: str
    dimension_value: str
    true_contribution_pct: float
    causal_path: List[str]
    onset_timestamp: datetime


class ExpectedGovernanceAction(BaseModel):
    rule_id: int
    decision_right: str  # ALLOWED, HUMAN_REVIEW, PROHIBITED, ABSTAIN
    expected_action: str


class GoldenDatasetSpec(BaseModel):
    benchmark_id: str
    tier: Literal["Tier1_Unit", "Tier2_Boundary", "Tier3_Interaction", "Tier4_RealWorld"]
    description: str
    kpi_id: str
    cadence: str
    input_time_series: List[Dict[str, Any]]
    ground_truth_movement: Dict[str, Any]
    ground_truth_drivers: List[GroundTruthDriver]
    expected_governance: ExpectedGovernanceAction
    expected_persona_facts: Dict[str, List[str]]
    dataset_version: str = "1.0.0"


def generate_synthetic_series(
    n_days: int = 30,
    base_value: float = 1000.0,
    trend_slope: float = 0.5,
    weekly_seasonality_amp: float = 100.0,
    noise_std: float = 10.0,
    anomaly_day: Optional[int] = 25,
    anomaly_delta: float = -250.0,
    missing_pct: float = 0.0,
    zero_inflated: bool = False,
    start_date: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Helper to generate clean deterministic synthetic time series vectors."""
    if start_date is None:
        start_date = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)

    series = []
    for day in range(n_days):
        cur_dt = start_date + timedelta(days=day)

        if missing_pct > 0 and random.random() < missing_pct and (anomaly_day is None or day != anomaly_day):
            continue  # Simulate dropped timestamp

        if zero_inflated and random.random() < 0.6:
            val = 0.0
        else:
            t = day
            seasonal = weekly_seasonality_amp * math.sin(2 * math.pi * (t % 7) / 7.0)
            trend = base_value + trend_slope * t
            noise = random.gauss(0, noise_std) if noise_std > 0 else 0.0
            val = trend + seasonal + noise

            if anomaly_day is not None and day >= anomaly_day:
                val += anomaly_delta

            val = max(0.0, val)

        series.append({
            "observed_at": cur_dt.isoformat(),
            "value": round(val, 2),
            "dimensions": {"environment": "production"},
        })
    return series


def build_golden_catalog() -> List[GoldenDatasetSpec]:
    """
    Generate the complete 19-incident Golden Dataset catalog.
    """
    catalog: List[GoldenDatasetSpec] = []
    base_time = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)
    onset_t = datetime(2026, 8, 25, 0, 0, 0, tzinfo=timezone.utc)

    # =========================================================================
    # TIER 1: Feature Unit Coverage (5 Incidents)
    # =========================================================================
    
    # BM-101: Product Feature Drop
    catalog.append(GoldenDatasetSpec(
        benchmark_id="BM-101",
        tier="Tier1_Unit",
        description="Single-factor revenue drop caused by checkout button iOS app release bug.",
        kpi_id="checkout_revenue",
        cadence="daily",
        input_time_series=generate_synthetic_series(30, 50000.0, 10.0, 2000.0, 50.0, 25, -15000.0),
        ground_truth_movement={"z_score": -3.85, "percentage_delta": -30.0, "is_anomaly": True},
        ground_truth_drivers=[
            GroundTruthDriver(
                driver_name="Checkout Button Regression",
                dimension_key="product_release",
                dimension_value="v4.12.0_ios",
                true_contribution_pct=100.0,
                causal_path=["Mobile App", "Checkout Flow", "Payment Gateway"],
                onset_timestamp=onset_t,
            )
        ],
        expected_governance=ExpectedGovernanceAction(
            rule_id=13, decision_right="ALLOWED", expected_action="ROLLBACK_APP_RELEASE"
        ),
        expected_persona_facts={
            "EXECUTIVE": ["Checkout revenue dropped 30% on Aug 25 due to iOS v4.12.0 release bug."],
            "ENGINEERING": ["Rollback iOS release v4.12.0 immediately to restore checkout pipeline."],
        },
    ))

    # BM-102: Customer Segment Drop
    catalog.append(GoldenDatasetSpec(
        benchmark_id="BM-102",
        tier="Tier1_Unit",
        description="Enterprise customer renewal contraction due to procurement freeze.",
        kpi_id="enterprise_arr",
        cadence="daily",
        input_time_series=generate_synthetic_series(30, 200000.0, 50.0, 5000.0, 100.0, 25, -45000.0),
        ground_truth_movement={"z_score": -4.2, "percentage_delta": -22.5, "is_anomaly": True},
        ground_truth_drivers=[
            GroundTruthDriver(
                driver_name="Enterprise Renewal Delay",
                dimension_key="customer_segment",
                dimension_value="Tier-1 Enterprise",
                true_contribution_pct=100.0,
                causal_path=["Account Management", "Procurement Hold"],
                onset_timestamp=onset_t,
            )
        ],
        expected_governance=ExpectedGovernanceAction(
            rule_id=15, decision_right="HUMAN_REVIEW", expected_action="ACCOUNT_EXEC_INTERVENTION"
        ),
        expected_persona_facts={
            "EXECUTIVE": ["Enterprise ARR contracted $45k from Fortune 500 delayed renewal."],
            "SALES": ["Engage VP Account Executive for executive sponsorship bridge."],
        },
    ))

    # BM-103: Geography Regional Slump
    catalog.append(GoldenDatasetSpec(
        benchmark_id="BM-103",
        tier="Tier1_Unit",
        description="Regional conversion collapse in APAC due to localized fiber optic cable cut.",
        kpi_id="apac_gross_margin",
        cadence="daily",
        input_time_series=generate_synthetic_series(30, 80000.0, 20.0, 1500.0, 80.0, 25, -28000.0),
        ground_truth_movement={"z_score": -4.6, "percentage_delta": -35.0, "is_anomaly": True},
        ground_truth_drivers=[
            GroundTruthDriver(
                driver_name="APAC Regional Network Outage",
                dimension_key="geography",
                dimension_value="APAC",
                true_contribution_pct=100.0,
                causal_path=["Undersea Cable Cut", "Latency Spike", "APAC Checkout Timeout"],
                onset_timestamp=onset_t,
            )
        ],
        expected_governance=ExpectedGovernanceAction(
            rule_id=13, decision_right="ALLOWED", expected_action="REROUTE_TRAFFIC_US_WEST"
        ),
        expected_persona_facts={
            "ENGINEERING": ["Reroute APAC ingress traffic to secondary Hong Kong edge node."],
        },
    ))

    # BM-104: Channel Shift
    catalog.append(GoldenDatasetSpec(
        benchmark_id="BM-104",
        tier="Tier1_Unit",
        description="Paid search ad campaign CPA inflation causing inbound pipeline collapse.",
        kpi_id="marketing_inbound_leads",
        cadence="daily",
        input_time_series=generate_synthetic_series(30, 1500.0, 2.0, 100.0, 15.0, 25, -600.0),
        ground_truth_movement={"z_score": -3.9, "percentage_delta": -40.0, "is_anomaly": True},
        ground_truth_drivers=[
            GroundTruthDriver(
                driver_name="Google Ads Keyword Bid Spike",
                dimension_key="channel",
                dimension_value="Paid_Search",
                true_contribution_pct=100.0,
                causal_path=["Competitor Bid Surge", "Ad Budget Depleted"],
                onset_timestamp=onset_t,
            )
        ],
        expected_governance=ExpectedGovernanceAction(
            rule_id=14, decision_right="ALLOWED", expected_action="PAUSE_PAID_SEARCH_CAMPAIGN"
        ),
        expected_persona_facts={
            "SALES": ["Pause high-CPA bidding campaigns on Google Ads."],
        },
    ))

    # BM-105: Operational Latency Spike
    catalog.append(GoldenDatasetSpec(
        benchmark_id="BM-105",
        tier="Tier1_Unit",
        description="API p99 latency surge causing user session abandonment.",
        kpi_id="api_p99_latency",
        cadence="daily",
        input_time_series=generate_synthetic_series(30, 120.0, 0.5, 10.0, 5.0, 25, 450.0),
        ground_truth_movement={"z_score": 5.8, "percentage_delta": 375.0, "is_anomaly": True},
        ground_truth_drivers=[
            GroundTruthDriver(
                driver_name="Database Connection Pool Exhaustion",
                dimension_key="infrastructure",
                dimension_value="pg_bouncer_primary",
                true_contribution_pct=100.0,
                causal_path=["Unindexed Query", "Lock Contention", "Connection Pool Starvation"],
                onset_timestamp=onset_t,
            )
        ],
        expected_governance=ExpectedGovernanceAction(
            rule_id=13, decision_right="ALLOWED", expected_action="SCALE_DB_POOL_INSTANCES"
        ),
        expected_persona_facts={
            "ENGINEERING": ["Scale PgBouncer pool max_connections and terminate idle locks."],
        },
    ))

    # =========================================================================
    # TIER 2: Boundary & Noise Stress Testing (5 Incidents)
    # =========================================================================

    # BM-201: Flash Crash
    catalog.append(GoldenDatasetSpec(
        benchmark_id="BM-201",
        tier="Tier2_Boundary",
        description="1-point instantaneous flash crash followed by immediate recovery.",
        kpi_id="active_sessions",
        cadence="daily",
        input_time_series=generate_synthetic_series(30, 10000.0, 0.0, 500.0, 20.0, 25, -8500.0),
        ground_truth_movement={"z_score": -6.5, "percentage_delta": -85.0, "is_anomaly": True},
        ground_truth_drivers=[
            GroundTruthDriver(
                driver_name="BGP Routing Flap",
                dimension_key="infra",
                dimension_value="bgp_as13335",
                true_contribution_pct=100.0,
                causal_path=["Transitory Network Blip"],
                onset_timestamp=onset_t,
            )
        ],
        expected_governance=ExpectedGovernanceAction(
            rule_id=13, decision_right="ALLOWED", expected_action="MONITOR_RECOVERY"
        ),
        expected_persona_facts={"ENGINEERING": ["Transitory 10-minute network flap resolved."]},
    ))

    # BM-202: High Noise Stress
    catalog.append(GoldenDatasetSpec(
        benchmark_id="BM-202",
        tier="Tier2_Boundary",
        description="High white noise environment (SNR = 1.0) testing false positive resilience.",
        kpi_id="noisy_telemetry_signal",
        cadence="daily",
        input_time_series=generate_synthetic_series(30, 500.0, 0.0, 50.0, 150.0, None, 0.0),
        ground_truth_movement={"z_score": 0.8, "percentage_delta": 3.0, "is_anomaly": False},
        ground_truth_drivers=[],
        expected_governance=ExpectedGovernanceAction(
            rule_id=23, decision_right="ABSTAIN", expected_action="NO_ACTION_REQUIRED"
        ),
        expected_persona_facts={"EXECUTIVE": ["Signal within normal statistical noise band."]},
    ))

    # BM-203: Sparse Cold-Start
    catalog.append(GoldenDatasetSpec(
        benchmark_id="BM-203",
        tier="Tier2_Boundary",
        description="Cold-start newly launched KPI with only N=7 days of history.",
        kpi_id="new_ai_copilot_dau",
        cadence="daily",
        input_time_series=generate_synthetic_series(7, 200.0, 15.0, 10.0, 5.0, 6, -50.0),
        ground_truth_movement={"z_score": -1.8, "percentage_delta": -20.0, "is_anomaly": False},
        ground_truth_drivers=[],
        expected_governance=ExpectedGovernanceAction(
            rule_id=21, decision_right="HUMAN_REVIEW", expected_action="FLAG_SPARSE_HISTORY"
        ),
        expected_persona_facts={"EXECUTIVE": ["Cold-start product: Prior borrowing applied."]},
    ))

    # BM-204: Missing Values Stress (20%)
    catalog.append(GoldenDatasetSpec(
        benchmark_id="BM-204",
        tier="Tier2_Boundary",
        description="Time series with 20% random missing timestamps evaluating Akima imputation.",
        kpi_id="iot_telemetry_stream",
        cadence="daily",
        input_time_series=generate_synthetic_series(30, 1000.0, 5.0, 80.0, 10.0, 25, -300.0, missing_pct=0.20),
        ground_truth_movement={"z_score": -3.2, "percentage_delta": -30.0, "is_anomaly": True},
        ground_truth_drivers=[
            GroundTruthDriver(
                driver_name="Sensor Power Loss",
                dimension_key="hardware_id",
                dimension_value="node_cluster_gamma",
                true_contribution_pct=100.0,
                causal_path=["Sensor Dropouts"],
                onset_timestamp=onset_t,
            )
        ],
        expected_governance=ExpectedGovernanceAction(
            rule_id=23, decision_right="ALLOWED", expected_action="REGULARIZE_AND_ALERT"
        ),
        expected_persona_facts={"ENGINEERING": ["Akima spline filled 6 missing observation dates."]},
    ))

    # BM-205: Zero-Inflated Series
    catalog.append(GoldenDatasetSpec(
        benchmark_id="BM-205",
        tier="Tier2_Boundary",
        description="Sparse zero-inflated enterprise metric with intermittent heavy values.",
        kpi_id="seven_figure_deal_signings",
        cadence="daily",
        input_time_series=generate_synthetic_series(30, 2.0, 0.0, 1.0, 0.5, 25, -2.0, zero_inflated=True),
        ground_truth_movement={"z_score": -1.2, "percentage_delta": -100.0, "is_anomaly": False},
        ground_truth_drivers=[],
        expected_governance=ExpectedGovernanceAction(
            rule_id=23, decision_right="ABSTAIN", expected_action="ZERO_INFLATED_DEFERRAL"
        ),
        expected_persona_facts={"SALES": ["Intermittent enterprise deal pacing is expected."]},
    ))

    # =========================================================================
    # TIER 3: Cross-Factor & Contradiction Stress (5 Incidents)
    # =========================================================================

    # BM-301: Tri-Factor Concurrent Drop
    catalog.append(GoldenDatasetSpec(
        benchmark_id="BM-301",
        tier="Tier3_Interaction",
        description="Multi-factor drop driven simultaneously by Product bug (50%), Ad fatigue (30%), CDN latency (20%).",
        kpi_id="platform_net_revenue",
        cadence="daily",
        input_time_series=generate_synthetic_series(30, 100000.0, 20.0, 3000.0, 50.0, 25, -40000.0),
        ground_truth_movement={"z_score": -4.8, "percentage_delta": -40.0, "is_anomaly": True},
        ground_truth_drivers=[
            GroundTruthDriver(
                driver_name="Product Checkout Bug",
                dimension_key="product",
                dimension_value="v2.8.1",
                true_contribution_pct=50.0,
                causal_path=["Frontend Regression"],
                onset_timestamp=onset_t,
            ),
            GroundTruthDriver(
                driver_name="Paid Channel Ad Fatigue",
                dimension_key="channel",
                dimension_value="Meta_Ads",
                true_contribution_pct=30.0,
                causal_path=["Ad Spend Fatigue"],
                onset_timestamp=onset_t,
            ),
            GroundTruthDriver(
                driver_name="CDN Regional Latency",
                dimension_key="geography",
                dimension_value="EU_Central",
                true_contribution_pct=20.0,
                causal_path=["Edge Routing Latency"],
                onset_timestamp=onset_t,
            ),
        ],
        expected_governance=ExpectedGovernanceAction(
            rule_id=13, decision_right="ALLOWED", expected_action="MULTI_AGENT_ROLLBACK_DISPATCH"
        ),
        expected_persona_facts={
            "EXECUTIVE": ["Multi-factor revenue loss: Product (50%), Channel (30%), CDN (20%)."],
            "ENGINEERING": ["Deploy hotfix for v2.8.1 and flush EU CDN cache."],
            "SALES": ["Reallocate Meta budget to LinkedIn high-converting audience."],
        },
    ))

    # BM-302: Competing Agent Contradiction
    catalog.append(GoldenDatasetSpec(
        benchmark_id="BM-302",
        tier="Tier3_Interaction",
        description="Contradictory findings between Geography (pricing claims) and Product (release bug).",
        kpi_id="customer_churn_rate",
        cadence="daily",
        input_time_series=generate_synthetic_series(30, 0.02, 0.0, 0.002, 0.0005, 25, 0.04),
        ground_truth_movement={"z_score": 4.5, "percentage_delta": 200.0, "is_anomaly": True},
        ground_truth_drivers=[
            GroundTruthDriver(
                driver_name="Billing Currency Conversion Bug",
                dimension_key="product_billing",
                dimension_value="stripe_multi_currency",
                true_contribution_pct=85.0,
                causal_path=["Double Billing In Euro Accounts"],
                onset_timestamp=onset_t,
            )
        ],
        expected_governance=ExpectedGovernanceAction(
            rule_id=20, decision_right="HUMAN_REVIEW", expected_action="RESOLVE_AGENT_CONTRADICTION"
        ),
        expected_persona_facts={"FINANCE": ["Fix billing currency parser; refund affected accounts."]},
    ))

    # BM-303: Non-Stationary Drift
    catalog.append(GoldenDatasetSpec(
        benchmark_id="BM-303",
        tier="Tier3_Interaction",
        description="Gradual non-stationary level shift and trend slope acceleration.",
        kpi_id="infra_monthly_cost",
        cadence="daily",
        input_time_series=generate_synthetic_series(30, 10000.0, 200.0, 200.0, 50.0, 20, 5000.0),
        ground_truth_movement={"z_score": 3.8, "percentage_delta": 45.0, "is_anomaly": True},
        ground_truth_drivers=[
            GroundTruthDriver(
                driver_name="Kubernetes Autoscaler Leak",
                dimension_key="cluster",
                dimension_value="k8s_prod_eks",
                true_contribution_pct=100.0,
                causal_path=["Stuck Pods", "Node Pool Max Expansion"],
                onset_timestamp=base_time + timedelta(days=20),
            )
        ],
        expected_governance=ExpectedGovernanceAction(
            rule_id=13, decision_right="ALLOWED", expected_action="RECYCLE_ZOMBIE_NODES"
        ),
        expected_persona_facts={"ENGINEERING": ["Cordon and drain unneeded AWS EKS node instances."]},
    ))

    # BM-304: DAG Feedback Loop
    catalog.append(GoldenDatasetSpec(
        benchmark_id="BM-304",
        tier="Tier3_Interaction",
        description="Cyclic causal feedback: Latency -> Churn -> Decreased Volume -> Cache Invalidation.",
        kpi_id="server_response_time",
        cadence="daily",
        input_time_series=generate_synthetic_series(30, 50.0, 0.2, 5.0, 2.0, 25, 120.0),
        ground_truth_movement={"z_score": 4.9, "percentage_delta": 240.0, "is_anomaly": True},
        ground_truth_drivers=[
            GroundTruthDriver(
                driver_name="Cache Thrashing Loop",
                dimension_key="cache_tier",
                dimension_value="redis_cluster_l2",
                true_contribution_pct=100.0,
                causal_path=["Redis Eviction Policy Thrashing"],
                onset_timestamp=onset_t,
            )
        ],
        expected_governance=ExpectedGovernanceAction(
            rule_id=13, decision_right="ALLOWED", expected_action="EXPAND_REDIS_MEMORY"
        ),
        expected_persona_facts={"ENGINEERING": ["Switch Redis eviction policy to volatile-lru."]},
    ))

    # BM-305: Low-Confidence Ambiguity
    catalog.append(GoldenDatasetSpec(
        benchmark_id="BM-305",
        tier="Tier3_Interaction",
        description="Ambiguous evidence with composite confidence C_composite = 0.58 requiring human review.",
        kpi_id="trial_to_paid_conversion",
        cadence="daily",
        input_time_series=generate_synthetic_series(30, 0.08, 0.0, 0.005, 0.008, 25, -0.025),
        ground_truth_movement={"z_score": -2.6, "percentage_delta": -31.25, "is_anomaly": True},
        ground_truth_drivers=[],
        expected_governance=ExpectedGovernanceAction(
            rule_id=22, decision_right="HUMAN_REVIEW", expected_action="REQUEST_HUMAN_CLARIFICATION"
        ),
        expected_persona_facts={"EXECUTIVE": ["Confidence below 0.65 threshold: Human clarification requested."]},
    ))

    # =========================================================================
    # TIER 4: Enterprise Incident Scenarios (4 Incidents)
    # =========================================================================

    # BM-401: Black Friday Payment Gateway Outage
    catalog.append(GoldenDatasetSpec(
        benchmark_id="BM-401",
        tier="Tier4_RealWorld",
        description="Sanitized real-world Black Friday payment processing degradation from 3rd party webhook timeouts.",
        kpi_id="black_friday_order_volume",
        cadence="hourly",
        input_time_series=generate_synthetic_series(30, 15000.0, 50.0, 2000.0, 100.0, 25, -9000.0),
        ground_truth_movement={"z_score": -6.1, "percentage_delta": -60.0, "is_anomaly": True},
        ground_truth_drivers=[
            GroundTruthDriver(
                driver_name="Stripe Webhook Rate Limit Exhaustion",
                dimension_key="payment_processor",
                dimension_value="stripe_webhook_v1",
                true_contribution_pct=100.0,
                causal_path=["Payment Timeout", "Abandoned Cart", "Order Drop"],
                onset_timestamp=onset_t,
            )
        ],
        expected_governance=ExpectedGovernanceAction(
            rule_id=13, decision_right="ALLOWED", expected_action="SWITCH_SECONDARY_GATEWAY_ADYEN"
        ),
        expected_persona_facts={
            "EXECUTIVE": ["Black Friday order volume fell 60% due to payment processor gateway timeouts."],
            "ENGINEERING": ["Failover to Adyen secondary payment routing immediately."],
        },
    ))

    # BM-402: Cloudflare CDN Regional Routing Failure
    catalog.append(GoldenDatasetSpec(
        benchmark_id="BM-402",
        tier="Tier4_RealWorld",
        description="Cloudflare BGP Anycast routing loop causing European regional traffic blackholing.",
        kpi_id="eu_user_login_success_rate",
        cadence="daily",
        input_time_series=generate_synthetic_series(30, 0.995, 0.0, 0.001, 0.001, 25, -0.45),
        ground_truth_movement={"z_score": -8.2, "percentage_delta": -45.2, "is_anomaly": True},
        ground_truth_drivers=[
            GroundTruthDriver(
                driver_name="Cloudflare London Edge BGP Loop",
                dimension_key="cdn_pop",
                dimension_value="lon01_pop",
                true_contribution_pct=100.0,
                causal_path=["BGP Routing Loop", "502 Bad Gateway"],
                onset_timestamp=onset_t,
            )
        ],
        expected_governance=ExpectedGovernanceAction(
            rule_id=13, decision_right="ALLOWED", expected_action="BYPASS_CF_EDGE_FRANKFURT"
        ),
        expected_persona_facts={"ENGINEERING": ["Bypass LON PoP; route EU traffic to Frankfurt."]},
    ))

    # BM-403: Enterprise Price Tier Migration Churn
    catalog.append(GoldenDatasetSpec(
        benchmark_id="BM-403",
        tier="Tier4_RealWorld",
        description="Grandfathered pricing plan sunset inducing unexpected tier-2 customer churn spike.",
        kpi_id="monthly_recurring_revenue",
        cadence="daily",
        input_time_series=generate_synthetic_series(30, 450000.0, 100.0, 5000.0, 500.0, 25, -65000.0),
        ground_truth_movement={"z_score": -4.1, "percentage_delta": -14.4, "is_anomaly": True},
        ground_truth_drivers=[
            GroundTruthDriver(
                driver_name="Legacy Price Hike Backlash",
                dimension_key="pricing_tier",
                dimension_value="legacy_growth_v1",
                true_contribution_pct=100.0,
                causal_path=["Price Sunset Notice", "Competitor Switching"],
                onset_timestamp=onset_t,
            )
        ],
        expected_governance=ExpectedGovernanceAction(
            rule_id=15, decision_right="HUMAN_REVIEW", expected_action="OFFER_MIGRATION_DISCOUNT"
        ),
        expected_persona_facts={
            "EXECUTIVE": ["MRR contracted $65k following legacy tier deprecation."],
            "FINANCE": ["Authorize 20% transitional loyalty discount for legacy accounts."],
        },
    ))

    # BM-404: Multi-Tenant Data Redaction & Margin Breach
    catalog.append(GoldenDatasetSpec(
        benchmark_id="BM-404",
        tier="Tier4_RealWorld",
        description="Cross-tenant PII and unredacted gross margin leakage prevention check.",
        kpi_id="confidential_gross_margin",
        cadence="daily",
        input_time_series=generate_synthetic_series(30, 0.72, 0.0, 0.01, 0.002, 25, -0.15),
        ground_truth_movement={"z_score": -3.5, "percentage_delta": -20.8, "is_anomaly": True},
        ground_truth_drivers=[
            GroundTruthDriver(
                driver_name="Vendor Cost Adjustment",
                dimension_key="vendor",
                dimension_value="aws_reserved_instance_expiry",
                true_contribution_pct=100.0,
                causal_path=["AWS On-Demand Surcharge"],
                onset_timestamp=onset_t,
            )
        ],
        expected_governance=ExpectedGovernanceAction(
            rule_id=16, decision_right="ALLOWED", expected_action="REDACT_MARGIN_FOR_ENGINEERING"
        ),
        expected_persona_facts={
            "FINANCE": ["Gross margin contracted to 57%; renegotiate AWS savings plan."],
            "ENGINEERING": ["Operational health stable; financial margins redacted per RBAC policy."],
        },
    ))

    return catalog
