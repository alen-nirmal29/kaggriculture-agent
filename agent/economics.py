"""Simple crop utility estimates for V1."""

from dataclasses import dataclass

from agent.crops import CROPS

BASE_SALE_PRICES = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250}


@dataclass(frozen=True)
class CropEconomics:
    crop: str
    approximate_revenue: float
    profit: float
    profit_per_growth_day: float
    labor_adjusted_utility: float


def estimate_crop(crop: str) -> CropEconomics:
    definition = CROPS[crop]
    if definition.ongoing:
        expected_yield = definition.max_yield
        active_days = definition.first_yield_day + definition.interval * (definition.max_yield - 1)
    else:
        bonus_days = definition.max_yield_day - ((definition.max_yield_day + 1) // 2) + 1
        expected_yield = min(definition.max_yield, 1 + bonus_days)
        active_days = definition.max_yield_day
    revenue = expected_yield * BASE_SALE_PRICES[crop]
    profit = revenue - definition.seed_cost
    return CropEconomics(crop, revenue, profit, profit / max(1, active_days), profit / max(1, active_days))


def choose_v1_crop() -> str:
    candidates = (estimate_crop("WHEAT"), estimate_crop("CARROT"))
    return max(candidates, key=lambda item: (item.labor_adjusted_utility, -CROPS[item.crop].seed_cost)).crop
