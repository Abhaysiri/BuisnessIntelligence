"""
Dynamic Model Token Pricing Matrix & Cost Calculator (§5.3)
Calculates exact USD inference cost:
Cost = sum_models [ (PromptTokens/1M * P_prompt) + (CompletionTokens/1M * P_completion) + (CachedTokens/1M * P_cached) ]
"""

from typing import Dict, Optional
from pydantic import BaseModel, Field


class TokenPricing(BaseModel):
    model_name: str
    prompt_price_per_1m: float
    completion_price_per_1m: float
    cached_prompt_price_per_1m: float


# Pricing matrix as specified in §5.3
DEFAULT_PRICING_MATRIX: Dict[str, TokenPricing] = {
    "gpt-4o-mini": TokenPricing(
        model_name="gpt-4o-mini",
        prompt_price_per_1m=0.150,
        completion_price_per_1m=0.600,
        cached_prompt_price_per_1m=0.075,
    ),
    "gpt-4o": TokenPricing(
        model_name="gpt-4o",
        prompt_price_per_1m=2.500,
        completion_price_per_1m=10.000,
        cached_prompt_price_per_1m=1.250,
    ),
    "claude-3-5-sonnet": TokenPricing(
        model_name="claude-3-5-sonnet",
        prompt_price_per_1m=3.000,
        completion_price_per_1m=15.000,
        cached_prompt_price_per_1m=0.300,
    ),
}


class ModelPricingMatrix:
    """
    Manages model token rates and provides pricing lookups.
    """

    def __init__(self, custom_rates: Optional[Dict[str, TokenPricing]] = None):
        self.rates: Dict[str, TokenPricing] = dict(DEFAULT_PRICING_MATRIX)
        if custom_rates:
            self.rates.update(custom_rates)

    def get_pricing(self, model_name: str) -> TokenPricing:
        # Default to gpt-4o-mini if unrecognized
        clean_name = model_name.lower().strip()
        for k, v in self.rates.items():
            if k in clean_name:
                return v
        return self.rates["gpt-4o-mini"]


class CostCalculator:
    """
    Computes exact inference cost based on token counts and model pricing matrix.
    """

    def __init__(self, pricing_matrix: Optional[ModelPricingMatrix] = None):
        self.matrix = pricing_matrix or ModelPricingMatrix()

    def calculate_call_cost(
        self,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        cached_prompt_tokens: int = 0,
    ) -> float:
        pricing = self.matrix.get_pricing(model_name)
        
        # Effective non-cached prompt tokens
        uncached_prompt_tokens = max(0, prompt_tokens - cached_prompt_tokens)

        cost = (
            (uncached_prompt_tokens / 1_000_000.0) * pricing.prompt_price_per_1m
            + (completion_tokens / 1_000_000.0) * pricing.completion_price_per_1m
            + (cached_prompt_tokens / 1_000_000.0) * pricing.cached_prompt_price_per_1m
        )
        return float(round(cost, 6))

    def calculate_aggregate_cost(
        self,
        model_token_usage: Dict[str, Dict[str, int]],
    ) -> float:
        """
        model_token_usage format:
        {
            "gpt-4o-mini": {"prompt_tokens": 1000, "completion_tokens": 200, "cached_tokens": 500},
            "gpt-4o": {"prompt_tokens": 500, "completion_tokens": 100, "cached_tokens": 0}
        }
        """
        total_cost = 0.0
        for model_name, usage in model_token_usage.items():
            p_tokens = usage.get("prompt_tokens", 0)
            c_tokens = usage.get("completion_tokens", 0)
            cached_tokens = usage.get("cached_tokens", 0)
            total_cost += self.calculate_call_cost(model_name, p_tokens, c_tokens, cached_tokens)
        return float(round(total_cost, 6))
