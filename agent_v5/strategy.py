"""Frozen V4 farming plus configurable ROI-driven land expansion."""

from __future__ import annotations

from collections import Counter

from agent_v3.strategy import CropPlan, Task, _capacity_safe_allocation
from agent_v4.strategy import EXTENDED_ROUTE
from agent_v5 import crops
from agent_v5.economics import score_all_crops
from agent_v5.endgame import is_final_day
from agent_v5.land import BASE_CAPACITY, market_order_cost, should_buy_next_land
from agent_v5.market import build_market_orders, live_crop_prices
from agent_v5.state import GameState
from agent_v5.workers import assign_tasks, hiring_orders, task_action, units

MAX_HANDS = 4
SUPPORTED_EXPANSIONS = (0, 1, 2, 3)


def validate_expansions(value: int) -> int:
    if value not in SUPPORTED_EXPANSIONS:
        raise ValueError(f"max_expansions must be one of {SUPPORTED_EXPANSIONS}")
    return value


def _quadrant(position: tuple[int, int]) -> str:
    x, y = position
    return ("N" if y < 5 else "S") + ("W" if x < 5 else "E")


def full_route() -> tuple[tuple[int, int], ...]:
    # Preserve V4's first 24/25 NW ordering, then add stable compact rings.
    remaining = ((x, y) for y in range(10) for x in range(10) if (x, y) not in EXTENDED_ROUTE)
    return EXTENDED_ROUTE + tuple(sorted(remaining, key=lambda p: (abs(p[0] - 4.5) + abs(p[1] - 4.5), p[1], p[0])))


def select_managed_tiles(state: GameState, capacity: int) -> tuple[tuple[int, int], ...]:
    unlocked = set(state.unlocked_quadrants)
    return tuple(position for position in full_route() if _quadrant(position) in unlocked and not state.tile_at(position).is_locked)[:capacity]


def build_crop_plan(state: GameState, capacity: int) -> CropPlan:
    positions = select_managed_tiles(state, capacity)
    existing = [crop for position in positions if (crop := crops.crop_type(state.tile_at(position))) is not None]
    scores = score_all_crops(state.step, live_crop_prices(state))
    allocation = _capacity_safe_allocation(scores, existing, len(positions))
    targets, assigned = {}, Counter(existing)
    for position in positions:
        current = crops.crop_type(state.tile_at(position))
        if current is not None: targets[position] = current
    for position in positions:
        tile = state.tile_at(position)
        if position in targets or not (crops.is_usable_empty(tile) or crops.is_weed(tile)): continue
        viable = [(wanted - assigned.get(crop, 0), scores[crop].score, crop) for crop, wanted in allocation.items() if wanted > assigned.get(crop, 0)]
        if viable:
            _, _, chosen = max(viable); targets[position] = chosen; assigned[chosen] += 1
    return CropPlan(scores, allocation, targets)


def generate_tasks(state: GameState, capacity: int, plan: CropPlan) -> list[Task]:
    tasks = []
    for position in select_managed_tiles(state, capacity):
        tile = state.tile_at(position)
        if crops.is_crop(tile):
            if crops.should_harvest(tile, state.day, is_final_day(state.day)): tasks.append(Task("HARVEST", position, 100))
            elif crops.is_exhausted_recurring(tile, state.day): tasks.append(Task("DIG", position, 80))
            elif not is_final_day(state.day) and crops.needs_water(tile): tasks.append(Task("WATER", position, 90 + int(tile.raw.get("consecutive_unwatered", 0))))
        elif crops.is_weed(tile) and position in plan.targets: tasks.append(Task("DIG", position, 80))
        elif crops.is_usable_empty(tile) and position in plan.targets and state.seed_count(plan.targets[position]) > 0: tasks.append(Task("PLANT", position, 70, plan.targets[position]))
    return tasks


def decide(state: GameState, max_expansions: int, max_capacity: int) -> dict[str, list]:
    validate_expansions(max_expansions)
    capacity = min(max_capacity, len(state.unlocked_quadrants) * 25 - 1)
    plan = build_crop_plan(state, capacity)
    empty_targets = {p: c for p, c in plan.targets.items() if crops.is_usable_empty(state.tile_at(p))}
    market = build_market_orders(state, empty_targets)
    raw_tasks = generate_tasks(state, capacity, plan)
    # Reuse V4's task enrichment by temporarily supplying compatible inputs.
    tasks = []
    from agent_v5.workers import WorkTask
    for task in raw_tasks:
        tile = state.tile_at(task.target); crop = crops.crop_type(tile) or task.crop
        tasks.append(WorkTask(task.kind, task.target, task.priority, 3 if task.kind == "HARVEST" else 0, float(state.market_prices.get(crop, 0)) if crop else 0.0, task.crop))
    hires = hiring_orders(state, MAX_HANDS, len(tasks) + len(empty_targets))
    market += hires
    seed_costs = {name: definition.seed_cost for name, definition in crops.CROPS.items()}
    best_score = max((score.score for score in plan.scores.values()), default=0.0)
    if should_buy_next_land(state, max_expansions, max_capacity, best_score, market_order_cost(market, seed_costs, state.hires_today)):
        market.append(["BUY_LAND"])
    assignments = assign_tasks(state, tasks); active = units(state)
    return {"farmer": task_action(state, active[0], assignments.get(0)), "hands": [task_action(state, unit, assignments.get(unit.index)) for unit in active[1:]], "market": market}
