"""Verified land state, payback, and cash-safe purchase policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from agent_v5.state import GameState

QUADRANTS = ("NW", "NE", "SW", "SE")
UNLOCK_ORDER = ("NE", "SW", "SE")
LAND_COSTS = (1000, 2000, 4000)
PLOTS_PER_QUADRANT = 25
BASE_CAPACITY = 24


@dataclass(frozen=True)
class LandEstimate:
    expansion_index: int
    quadrant: str | None
    cost: int | None
    additional_managed_plots: int
    remaining_turns: int
    expected_incremental_profit: float
    operating_reserve: float
    affordable: bool
    repayable: bool


def expansion_count(state: GameState) -> int:
    return max(0, len(state.unlocked_quadrants) - 1)


def next_quadrant(state: GameState) -> str | None:
    count = expansion_count(state)
    return UNLOCK_ORDER[count] if count < len(UNLOCK_ORDER) else None


def next_land_cost(state: GameState) -> int | None:
    count = expansion_count(state)
    return LAND_COSTS[count] if count < len(LAND_COSTS) else None


def operating_reserve(managed_capacity: int) -> float:
    # One likely seed purchase per managed plot plus a stable cash safety buffer.
    return 500.0 + 20.0 * managed_capacity


def estimate_land_payback(state: GameState, max_capacity: int, best_crop_score: float, pending_market_cost: float = 0.0) -> LandEstimate:
    count = expansion_count(state)
    quadrant = next_quadrant(state)
    cost = next_land_cost(state)
    available_after = min((count + 2) * PLOTS_PER_QUADRANT, max_capacity)
    current_possible = min((count + 1) * PLOTS_PER_QUADRANT, max_capacity)
    additional = max(0, available_after - max(BASE_CAPACITY, current_possible))
    remaining_fraction = max(0.0, min(1.0, state.remaining_turns / 720.0))
    # Four hands were already 86% utilized at 24 plots. Credit only 35% of ideal
    # per-plot economics, reduced further as the horizon closes.
    realizable = additional * max(0.0, best_crop_score) * 0.35 * remaining_fraction
    reserve = operating_reserve(max(BASE_CAPACITY, current_possible))
    affordable = cost is not None and state.money - pending_market_cost - cost >= reserve
    repayable = cost is not None and additional > 0 and state.remaining_turns >= 96 and realizable > cost * 1.15
    return LandEstimate(count, quadrant, cost, additional, state.remaining_turns, realizable, reserve, affordable, repayable)


def should_buy_next_land(state: GameState, max_expansions: int, max_capacity: int, best_crop_score: float, pending_market_cost: float = 0.0) -> bool:
    if not 0 <= max_expansions <= 3:
        raise ValueError("max_expansions must be between 0 and 3")
    if expansion_count(state) >= max_expansions or state.hour > 1:
        return False
    estimate = estimate_land_payback(state, max_capacity, best_crop_score, pending_market_cost)
    return estimate.affordable and estimate.repayable


def market_order_cost(orders: list[list], seed_costs: Mapping[str, int], hires_today: int) -> float:
    from agent_v5.workers import hire_cost
    total, hire_offset = 0.0, 0
    for order in orders:
        if not order:
            continue
        if order[0] == "BUY_SEED" and len(order) >= 3:
            total += seed_costs.get(order[1], 0) * int(order[2])
        elif order[0] == "HIRE":
            total += hire_cost(hires_today + hire_offset); hire_offset += 1
    return total
