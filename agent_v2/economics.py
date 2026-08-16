"""Explainable, horizon-aware crop scoring for V2."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Mapping, Sequence

from agent_v2.crops import CROPS, CROP_NAMES

TURNS_PER_DAY = 24
SEASON_TURNS = 720
LAST_DAY = 29
LABOR_COST_PER_ACTION = 2.0
MARKET_REALIZATION_FACTOR = 0.95
SWITCH_ADVANTAGE = 1.15
MIX_THRESHOLD = 0.92


@dataclass(frozen=True)
class CropScore:
    crop: str
    live_price: int
    harvest_opportunities: int
    expected_units: int
    seed_purchases: int
    expected_revenue: float
    seed_cost: float
    estimated_actions: float
    workload_penalty: float
    score: float


def planting_day(current_step: int) -> int:
    """A new crop needs PLANT and WATER before day end."""
    day, hour = divmod(max(0, current_step), TURNS_PER_DAY)
    return day if hour <= TURNS_PER_DAY - 2 else day + 1


def production_schedule(crop: str, current_step: int) -> tuple[tuple[int, int], ...]:
    """Return `(harvest_day, units)` events realizable by season end."""
    definition = CROPS[crop]
    start = planting_day(current_step)
    if start > LAST_DAY:
        return ()
    events: list[tuple[int, int]] = []
    cycle_start = start
    while cycle_start <= LAST_DAY:
        cycle_events: list[tuple[int, int]] = []
        if definition.ongoing:
            for age in definition.production_ages:
                day = cycle_start + age
                if day <= LAST_DAY:
                    cycle_events.append((day, 1))
            cycle_length = definition.production_ages[-1]
        else:
            day = cycle_start + definition.target_harvest_age
            if day <= LAST_DAY:
                cycle_events.append((day, definition.expected_one_time_yield))
            cycle_length = definition.target_harvest_age
        if not cycle_events:
            break
        events.extend(cycle_events)
        cycle_start += cycle_length
    return tuple(events)


def remaining_harvest_opportunities(crop: str, current_step: int) -> int:
    return len(production_schedule(crop, current_step))


def _seed_purchases(crop: str, schedule: Sequence[tuple[int, int]], current_step: int) -> int:
    if not schedule:
        return 0
    definition = CROPS[crop]
    start = planting_day(current_step)
    if definition.ongoing:
        # Count actual cycle starts by replaying the compact schedule.
        count = 0
        cycle_start = start
        last_event_day = schedule[-1][0]
        while cycle_start + definition.first_yield_day <= last_event_day:
            count += 1
            cycle_start += definition.production_ages[-1]
        return count
    return len(schedule)


def _estimated_actions(crop: str, schedule: Sequence[tuple[int, int]], seeds: int, current_step: int) -> float:
    if not schedule:
        return 0.0
    definition = CROPS[crop]
    horizon_days = max(1.0, (schedule[-1][0] - planting_day(current_step)) + 1)
    if definition.ongoing:
        harvests = len(schedule)
        full_span = definition.production_ages[-1]
        waters = min(horizon_days, seeds * full_span)
        clears = max(0, seeds - 1)
    else:
        harvests = len(schedule)
        waters = seeds * definition.target_harvest_age
        clears = 0
    # Six adjacent plots share about five movement actions per active day.
    movement_share = horizon_days * (5.0 / 6.0)
    return seeds + harvests + waters + clears + movement_share


def evaluate_crop(crop: str, current_step: int, live_price: int) -> CropScore:
    schedule = production_schedule(crop, current_step)
    units = sum(units for _, units in schedule)
    seeds = _seed_purchases(crop, schedule, current_step)
    revenue = float(live_price * units) * MARKET_REALIZATION_FACTOR
    seed_cost = float(seeds * CROPS[crop].seed_cost)
    actions = _estimated_actions(crop, schedule, seeds, current_step)
    penalty = actions * LABOR_COST_PER_ACTION
    score = revenue - seed_cost - penalty if units > 0 else float("-inf")
    return CropScore(crop, int(live_price), len(schedule), units, seeds, revenue, seed_cost, actions, penalty, score)


def score_all_crops(current_step: int, live_prices: Mapping[str, int]) -> dict[str, CropScore]:
    return {crop: evaluate_crop(crop, current_step, int(live_prices.get(crop, 1))) for crop in CROP_NAMES}


def preferred_crop(scores: Mapping[str, CropScore], existing_crops: Sequence[str] = ()) -> str | None:
    viable = [item for item in scores.values() if item.score > 0 and item.expected_units > 0]
    if not viable:
        return None
    best = max(viable, key=lambda item: (item.score, -CROPS[item.crop].seed_cost, item.crop))
    counts = Counter(crop for crop in existing_crops if crop in scores)
    incumbent = counts.most_common(1)[0][0] if counts else None
    if incumbent is not None:
        incumbent_score = scores[incumbent]
        if incumbent_score.score > 0 and best.score < incumbent_score.score * SWITCH_ADVANTAGE:
            return incumbent
    return best.crop


def crop_allocation(scores: Mapping[str, CropScore], existing_crops: Sequence[str], plot_limit: int = 6) -> dict[str, int]:
    leader = preferred_crop(scores, existing_crops)
    if leader is None or plot_limit <= 0:
        return {}
    leader_limit = min(plot_limit, 4) if CROPS[leader].ongoing else plot_limit
    allocation = {leader: leader_limit}
    runners = sorted(
        (item for item in scores.values() if item.crop != leader and item.score > 0),
        key=lambda item: (-item.score, item.crop),
    )
    if leader_limit < plot_limit and runners:
        allocation[runners[0].crop] = plot_limit - leader_limit
    elif runners and runners[0].score >= scores[leader].score * MIX_THRESHOLD and plot_limit >= 3:
        allocation[leader] = plot_limit - 2
        allocation[runners[0].crop] = 2
    return allocation
