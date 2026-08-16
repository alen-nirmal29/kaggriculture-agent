"""V4 task scheduling over frozen V3 crop and market decisions."""

from __future__ import annotations

from collections import Counter

from agent_v3.strategy import SAFE_ACTION, COMPACT_ROUTE, CropPlan, Task, _capacity_safe_allocation

from agent_v4 import crops
from agent_v4.endgame import is_final_day
from agent_v4.market import build_market_orders
from agent_v4.state import GameState
from agent_v4.workers import WorkTask, assign_tasks, hiring_orders, task_action, units

SUPPORTED_HAND_LIMITS = (0, 1, 2, 3, 4)
SUPPORTED_CAPACITIES = (12, 16, 20, 24)
EXTENDED_ROUTE = COMPACT_ROUTE + tuple(
    sorted(
        ((x, y) for y in range(5) for x in range(5) if (x, y) not in COMPACT_ROUTE),
        key=lambda position: (abs(4 - position[0]) + abs(4 - position[1]), -position[1], -position[0]),
    )
)


def validate_hand_limit(max_hands: int) -> int:
    if max_hands not in SUPPORTED_HAND_LIMITS:
        raise ValueError(f"max_hands must be one of {SUPPORTED_HAND_LIMITS}")
    return max_hands


def select_managed_tiles(state: GameState, capacity: int) -> tuple[tuple[int, int], ...]:
    if capacity not in SUPPORTED_CAPACITIES:
        raise ValueError(f"capacity must be one of {SUPPORTED_CAPACITIES}")
    return tuple(position for position in EXTENDED_ROUTE if not state.tile_at(position).is_locked)[:capacity]


def build_crop_plan(state: GameState, capacity: int) -> CropPlan:
    from agent_v4.economics import score_all_crops
    from agent_v4.market import live_crop_prices
    positions = select_managed_tiles(state, capacity)
    existing = [crop for position in positions if (crop := crops.crop_type(state.tile_at(position))) is not None]
    scores = score_all_crops(state.step, live_crop_prices(state))
    allocation = _capacity_safe_allocation(scores, existing, len(positions))
    targets = {}
    assigned = Counter(existing)
    for position in positions:
        current = crops.crop_type(state.tile_at(position))
        if current is not None:
            targets[position] = current
    for position in positions:
        tile = state.tile_at(position)
        if position in targets or not (crops.is_usable_empty(tile) or crops.is_weed(tile)):
            continue
        deficits = [(wanted - assigned.get(crop, 0), scores[crop].score, crop) for crop, wanted in allocation.items()]
        viable = [item for item in deficits if item[0] > 0]
        if viable:
            _, _, chosen = max(viable, key=lambda item: (item[0], item[1], item[2]))
            targets[position] = chosen
            assigned[chosen] += 1
    return CropPlan(scores, allocation, targets)


def generate_tasks(state: GameState, capacity: int, plan: CropPlan) -> list[Task]:
    tasks = []
    for position in select_managed_tiles(state, capacity):
        tile = state.tile_at(position)
        if crops.is_crop(tile):
            if crops.should_harvest(tile, state.day, is_final_day(state.day)):
                tasks.append(Task("HARVEST", position, 100))
            elif crops.is_exhausted_recurring(tile, state.day):
                tasks.append(Task("DIG", position, 80))
            elif not is_final_day(state.day) and crops.needs_water(tile):
                tasks.append(Task("WATER", position, 90 + int(tile.raw.get("consecutive_unwatered", 0))))
        elif crops.is_weed(tile) and position in plan.targets:
            tasks.append(Task("DIG", position, 80))
        elif crops.is_usable_empty(tile) and position in plan.targets:
            crop = plan.targets[position]
            if state.seed_count(crop) > 0:
                tasks.append(Task("PLANT", position, 70, crop))
    return tasks


def build_tasks(state: GameState, capacity: int, plan) -> list[WorkTask]:
    result = []
    prices = state.market_prices
    for task in generate_tasks(state, capacity, plan):
        tile = state.tile_at(task.target)
        crop = crops.crop_type(tile) or task.crop
        value = float(prices.get(crop, 0)) if crop else 0.0
        urgency = 3 if task.kind == "HARVEST" else int(tile.raw.get("consecutive_unwatered", 0)) if task.kind == "WATER" and isinstance(tile.raw, dict) else 0
        result.append(WorkTask(task.kind, task.target, task.priority, urgency, value, task.crop))
    return result


def decide(state: GameState, max_hands: int, capacity: int = 12) -> dict[str, list]:
    validate_hand_limit(max_hands)
    plan = build_crop_plan(state, capacity)
    empty_targets = {position: crop for position, crop in plan.targets.items() if crops.is_usable_empty(state.tile_at(position))}
    market = build_market_orders(state, empty_targets)
    tasks = build_tasks(state, capacity, plan)
    estimated_work = len(tasks) + len(empty_targets)
    hires = hiring_orders(state, max_hands, estimated_work)
    assignments = assign_tasks(state, tasks)
    active_units = units(state)
    farmer = task_action(state, active_units[0], assignments.get(0))
    hands = [task_action(state, unit, assignments.get(unit.index)) for unit in active_units[1:]]
    # Preserve V3's no-new-planting endgame policy through its crop plan and stop speculative hires.
    if is_final_day(state.day) and state.remaining_turns < 4:
        hires = []
    return {"farmer": farmer, "hands": hands, "market": market + hires}
