"""
edge_cases/sparse_history.py
Scenario 3 (§4.3): Sparse-History / Newly Launched KPI Scenario (Cold Start)

Simulates cold-start newly launched KPI or emerging regional market with N < 14 days
where standard STL decomposition (N >= 2 * period = 14) is statistically invalid.

Implements:
  1. Hierarchical Empirical Bayesian Prior Borrowing:
     theta_new ~ N(mu_0, sigma_0^2) from parent cohort / category benchmark.
     Posterior mean: mu_N = (1 - B) * y_bar + B * mu_0
     where shrinkage factor B = (sigma^2 / N) / (sigma_0^2 + sigma^2 / N) = kappa_0 / (kappa_0 + N)
     Posterior variance: sigma_N^2 = 1 / (N / sigma^2 + 1 / sigma_0^2)
  2. Surrogate Proxy Indicator Mapping across upstream funnel:
     Ad Clicks -> Trial Starts -> Product Activations -> Paid Conversions
  3. Dynamic 95% Bayesian Credible Interval Widening:
     kappa(N) = 1.0 + 2.5 / sqrt(N)
     Bounds = [mu_N - 1.96 * kappa(N) * sigma_N, mu_N + 1.96 * kappa(N) * sigma_N]
  4. Mandatory epistemic caveat persona narrative disclosure.
  5. Runtime [MOCK DATA] notification.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from pydantic import BaseModel, Field


MOCK_NOTICE = "[MOCK DATA] This output uses synthetic/simulated data. Replace with real ingested data."


class PriorCohortSpec(BaseModel):
    cohort_name: str
    mu_0: float = Field(..., description="Prior mean from parent cohort")
    sigma_0: float = Field(..., description="Prior standard deviation from parent cohort")
    observation_sigma: float = Field(..., description="Estimated observation noise sigma")


class BayesianEstimateResult(BaseModel):
    n_days: int
    sample_mean_ybar: float
    sample_variance_s2: float
    prior_mean_mu0: float
    prior_sigma0: float
    shrinkage_factor_B: float
    posterior_mean_muN: float
    posterior_sigma_N: float
    widening_multiplier_kappa: float
    widening_pct: float
    credible_interval_95_lower: float
    credible_interval_95_upper: float
    interval_width: float
    is_cold_start: bool
    epistemic_caveat_disclosure: str


class ColdStartBayesianEngine:
    """
    Hierarchical Empirical Bayesian Prior Borrowing engine for sparse time series (N < 14).
    """

    def __init__(self, prior: PriorCohortSpec):
        self.prior = prior
        self.sigma_0_sq = prior.sigma_0 ** 2
        self.sigma_obs_sq = prior.observation_sigma ** 2
        # kappa_0 = sigma_obs^2 / sigma_0^2
        self.kappa_0 = self.sigma_obs_sq / self.sigma_0_sq

    def estimate_posterior(
        self,
        observed_series: List[float],
        kpi_name: str = "Enterprise LTV (APAC Tier 2)"
    ) -> BayesianEstimateResult:
        """
        Computes Bayesian posterior shrinkage, credible interval widening, and epistemic caveat.
        """
        n = len(observed_series)
        if n == 0:
            raise ValueError("Observed time series must contain at least 1 observation.")

        y_bar = float(np.mean(observed_series))
        s_sq = float(np.var(observed_series, ddof=1)) if n > 1 else self.sigma_obs_sq

        # Shrinkage factor: B = (sigma^2 / N) / (sigma_0^2 + sigma^2 / N) = kappa_0 / (kappa_0 + N)
        b_shrinkage = self.kappa_0 / (self.kappa_0 + n)

        # Posterior mean: mu_N = (1 - B) * y_bar + B * mu_0
        mu_n = ((1.0 - b_shrinkage) * y_bar) + (b_shrinkage * self.prior.mu_0)

        # Posterior variance: sigma_N^2 = 1 / (N / sigma_obs^2 + 1 / sigma_0^2)
        inv_sigma_n_sq = (n / self.sigma_obs_sq) + (1.0 / self.sigma_0_sq)
        sigma_n_sq = 1.0 / inv_sigma_n_sq
        sigma_n = math.sqrt(sigma_n_sq)

        # Dynamic 95% Bayesian Credible Interval Widening: kappa(N) = 1.0 + 2.5 / sqrt(N)
        kappa_n = 1.0 + (2.5 / math.sqrt(n))
        widening_pct = (kappa_n - 1.0) * 100.0

        # Widened 95% CI bounds
        half_width = 1.96 * kappa_n * sigma_n
        ci_lower = mu_n - half_width
        ci_upper = mu_n + half_width

        is_cold_start = n < 14

        # Mandatory persona narrative disclosure
        if is_cold_start:
            caveat = (
                f"Notice: This metric ('{kpi_name}') was launched {n} days ago (N={n} < 14). "
                f"Baselines are synthesized via Empirical Bayesian prior borrowing from [{self.prior.cohort_name}]. "
                f"Confidence intervals are widened by {widening_pct:.1f}% to account for small-sample epistemic variance."
            )
        else:
            caveat = (
                f"Standard Regime: Sufficient time series depth (N={n} >= 14). "
                f"Shrinkage factor B={b_shrinkage:.4f} approaches empirical convergence with parent cohort."
            )

        return BayesianEstimateResult(
            n_days=n,
            sample_mean_ybar=round(y_bar, 2),
            sample_variance_s2=round(s_sq, 2),
            prior_mean_mu0=round(self.prior.mu_0, 2),
            prior_sigma0=round(self.prior.sigma_0, 2),
            shrinkage_factor_B=round(b_shrinkage, 4),
            posterior_mean_muN=round(mu_n, 2),
            posterior_sigma_N=round(sigma_n, 2),
            widening_multiplier_kappa=round(kappa_n, 4),
            widening_pct=round(widening_pct, 1),
            credible_interval_95_lower=round(ci_lower, 2),
            credible_interval_95_upper=round(ci_upper, 2),
            interval_width=round(ci_upper - ci_lower, 2),
            is_cold_start=is_cold_start,
            epistemic_caveat_disclosure=caveat
        )


@dataclass
class SurrogateProxyFunnel:
    """Simulates upstream fast-moving proxy indicator mapping (§4.3)."""
    ad_clicks: List[int]
    trial_starts: List[int]
    product_activations: List[int]
    paid_conversions: List[int]

    def project_surrogate_ltv(self, avg_contract_val: float = 12000.0) -> Dict[str, float]:
        """Projects estimated revenue and conversion rates from precursor funnel."""
        total_clicks = sum(self.ad_clicks)
        total_trials = sum(self.trial_starts)
        total_activations = sum(self.product_activations)
        total_conversions = sum(self.paid_conversions)

        click_to_trial = total_trials / max(1, total_clicks)
        trial_to_activation = total_activations / max(1, total_trials)
        activation_to_paid = total_conversions / max(1, total_activations)
        overall_conversion = total_conversions / max(1, total_clicks)

        projected_pipeline_arr = total_conversions * avg_contract_val

        return {
            "total_ad_clicks": total_clicks,
            "total_trial_starts": total_trials,
            "total_product_activations": total_activations,
            "total_paid_conversions": total_conversions,
            "click_to_trial_rate_pct": round(click_to_trial * 100.0, 2),
            "trial_to_activation_rate_pct": round(trial_to_activation * 100.0, 2),
            "activation_to_paid_rate_pct": round(activation_to_paid * 100.0, 2),
            "overall_funnel_conversion_pct": round(overall_conversion * 100.0, 3),
            "projected_pipeline_revenue": round(projected_pipeline_arr, 2)
        }


class SparseHistoryScenarioRunner:
    """
    Simulates Scenario 3 (§4.3) showing cold start N=6 vs progression up to N=30 days.
    """

    def __init__(self, seed: int = 101):
        self.rng = np.random.RandomState(seed)
        # Parent Cohort: SaaS Enterprise Tier (Global Established Baseline)
        self.prior_cohort = PriorCohortSpec(
            cohort_name="SaaS Enterprise Tier (Global)",
            mu_0=12500.0,          # $12,500 expected daily revenue
            sigma_0=1800.0,        # $1,800 between-series variation
            observation_sigma=2200.0  # $2,200 within-series daily noise
        )
        self.engine = ColdStartBayesianEngine(self.prior_cohort)

        # Generate a synthetic 30-day trajectory for a newly launched APAC market
        # True underlying mean for this new launch = $9,800/day (lower than global average)
        self.true_mean = 9800.0
        daily_noise = self.rng.normal(0, self.prior_cohort.observation_sigma, 30)
        self.daily_series_30d = [float(self.true_mean + noise) for noise in daily_noise]

    def run_cold_start_simulation(self) -> Dict[str, Any]:
        """
        Runs cold-start evaluation across sample sizes N = 1, 3, 6, 10, 14, 30 days.
        """
        eval_days = [1, 3, 6, 10, 14, 30]
        progression: List[BayesianEstimateResult] = []

        for n in eval_days:
            subseries = self.daily_series_30d[:n]
            est = self.engine.estimate_posterior(subseries, kpi_name="APAC Enterprise Net Revenue")
            progression.append(est)

        # Primary Scenario 3 focus: N = 6 days (Cold-Start regime)
        cold_start_6d = progression[2]  # N = 6

        # Fast-moving surrogate precursor funnel for the 6-day cold-start period
        funnel = SurrogateProxyFunnel(
            ad_clicks=[4200, 4600, 5100, 4800, 5300, 5600],
            trial_starts=[210, 245, 280, 260, 310, 335],
            product_activations=[95, 110, 125, 118, 140, 155],
            paid_conversions=[8, 10, 12, 9, 14, 15]
        )
        surrogate_metrics = funnel.project_surrogate_ltv(avg_contract_val=12000.0)

        return {
            "cold_start_primary_n6": cold_start_6d.model_dump(),
            "sample_size_progression": [p.model_dump() for p in progression],
            "surrogate_precursor_funnel": surrogate_metrics
        }


def run_scenario() -> Dict[str, Any]:
    """Entrypoint for Scenario 3."""
    print(MOCK_NOTICE)
    print("=" * 80)
    print("SCENARIO 3: SPARSE-HISTORY / COLD-START BAYESIAN PRIOR BORROWING (§4.3)")
    print("=" * 80)

    runner = SparseHistoryScenarioRunner()
    results = runner.run_cold_start_simulation()
    primary = results["cold_start_primary_n6"]

    print(f"Target KPI:              APAC Enterprise Net Revenue (Newly Launched)")
    print(f"Parent Cohort Prior:     {runner.prior_cohort.cohort_name} (mu_0 = ${runner.prior_cohort.mu_0:,.2f}, sigma_0 = ${runner.prior_cohort.sigma_0:,.2f})")
    print(f"Cold Start Period:       N = {primary['n_days']} days (Regime: Cold-Start < 14 days)")
    print(f"Observed Sample Mean:    ${primary['sample_mean_ybar']:,.2f}")
    print(f"Empirical Shrinkage (B): {primary['shrinkage_factor_B']:.4f} (Weights prior vs sample)")
    print(f"Bayesian Posterior Mean: ${primary['posterior_mean_muN']:,.2f}")
    print(f"Posterior Uncertainty:   sigma_N = ${primary['posterior_sigma_N']:,.2f}")
    print(f"Credible Band Widening:  kappa(N) = {primary['widening_multiplier_kappa']:.4f} (+{primary['widening_pct']}%)")
    print(f"Widened 95% CI Bounds:   [${primary['credible_interval_95_lower']:,.2f}, ${primary['credible_interval_95_upper']:,.2f}] (Width: ${primary['interval_width']:,.2f})")
    print("-" * 80)
    print("MANDATORY PERSONA NARRATIVE DISCLOSURE:")
    print(f'"{primary["epistemic_caveat_disclosure"]}"')
    print("-" * 80)
    print("BAYESIAN SHRINKAGE & CREDIBLE INTERVAL CONVERGENCE TABLE:")
    print(f"{'N Days':<8} | {'Sample y_bar':<14} | {'Shrinkage B':<12} | {'Post Mean mu_N':<16} | {'Widening %':<12} | {'95% Credible Interval':<30}")
    print("-" * 96)
    for p in results["sample_size_progression"]:
        ci_str = f"[${p['credible_interval_95_lower']:,.0f}, ${p['credible_interval_95_upper']:,.0f}]"
        print(f"{p['n_days']:<8} | ${p['sample_mean_ybar']:>12,.2f} | {p['shrinkage_factor_B']:>12.4f} | ${p['posterior_mean_muN']:>14,.2f} | +{p['widening_pct']:>9.1f}% | {ci_str:<30}")
    print("-" * 96)
    print("SURROGATE PRECURSOR FUNNEL (Fast-Moving Early Indicators):")
    for k, v in results["surrogate_precursor_funnel"].items():
        print(f"  - {k:<30}: {v}")
    print("=" * 80 + "\n")

    return results


if __name__ == "__main__":
    run_scenario()
