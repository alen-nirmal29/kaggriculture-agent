"""Configurable-capacity V3 strategy built from frozen V2 behavior."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from typing import Literal, Mapping

from agent_v3 import crops
from agent_v3.economics import CropScore, crop_allocation, score_all_crops
from agent_v3.endgame import is_final_day, should_liquidate_carried
from agent_v3.market import build_market_orders, live_crop_prices
from agent_v3.routing import manhattan_distance, nearest_shed_access, next_move, shed_access_positions
from agent_v3.state import GameState, Position

SUPPORTED_CAPACITIES = (6, 8, 10, 12)
COMPACT_ROUTE: tuple[Position, ...] = (
    (4, 4), (3, 4), (2, 4), (1, 4),
    (1, 3), (2, 3), (3, 3), (4, 3),
    (4, 2), (3, 2), (2, 2), (1, 2),
)
SAFE_ACTION = {"farmer": ["PASS"], "hands": [], "market": []}
MAX_RECURRING_PLOTS = 4
TaskKind = Literal["HARVEST", "WATER", "DIG", "PLANT"]


@dataclass(frozen=True)
class WorkloadEstimate:
    plots: int
    routine_actions: int
    renewal_actions: int
    renewal_days: int
    safe: bool


@dataclass(frozen=True)
class CropPlan:
    scores: Mapping[str, CropScore]
    allocation: Mapping[str, int]
    targets: Mapping[Position, str]


@dataclass(frozen=True)
class Task:
    kind: TaskKind
    target: Position
    priority: int
    crop: str | None = None


def validate_capacity(capacity: int) -> int:
    if capacity not in SUPPORTED_CAPACITIES:
        raise ValueError(f"capacity must be one of {SUPPORTED_CAPACITIES}, got {capacity}")
    return capacity


def estimate_workload(capacity: int) -> WorkloadEstimate:
    validate_capacity(capacity)
    movement = max(0, capacity - 1)
    routine = capacity + movement
    renewal = 3 * capacity + movement
    renewal_days = math.ceil(renewal / 24)
    return WorkloadEstimate(capacity, routine, renewal, renewal_days, routine <= 23 and renewal_days <= 2)


def select_managed_tiles(state: GameState, capacity: int) -> tuple[Position, ...]:
    validate_capacity(capacity)
    selected = []
    for position in COMPACT_ROUTE:
        if len(selected) >= capacity:
            break
        x, y = position
        if x < state.board_size and y < state.board_size and not state.tile_at(position).is_locked:
            selected.append(position)
    return tuple(selected)


def _capacity_safe_allocation(scores: Mapping[str, CropScore], existing: list[str], plot_limit: int) -> dict[str, int]:
    allocation = dict(crop_allocation(scores, existing, plot_limit))
    ongoing = [crop for crop in allocation if crops.CROPS[crop].ongoing]
    excess = max(0, sum(allocation[crop] for crop in ongoing) - MAX_RECURRING_PLOTS)
    if excess <= 0:
        return allocation
    for crop in sorted(ongoing, key=lambda name: (scores[name].score, name)):
        removed = min(excess, allocation[crop])
        allocation[crop] -= removed
        excess -= removed
        if allocation[crop] == 0:
            del allocation[crop]
        if excess == 0:
            break
    missing = plot_limit - sum(allocation.values())
    non_recurring = sorted(
        (score for score in scores.values() if not crops.CROPS[score.crop].ongoing and score.score > 0),
        key=lambda score: (-score.score, score.crop),
    )
    if missing and non_recurring:
        allocation[non_recurring[0].crop] = allocation.get(non_recurring[0].crop, 0) + missing
    return allocation


def build_crop_plan(state: GameState, capacity: int) -> CropPlan:
    positions = select_managed_tiles(state, capacity)
    existing_names = [crop for position in positions if (crop := crops.crop_type(state.tile_at(position))) is not None]
    scores = score_all_crops(state.step, live_crop_prices(state))
    allocation = _capacity_safe_allocation(scores, existing_names, len(positions))
    targets: dict[Position, str] = {}
    assigned = Counter(existing_names)
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
    tasks: list[Task] = []
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


def choose_task(state: GameState, tasks: list[Task]) -> Task | None:
    current = [task for task in tasks if task.target == state.farmer]
    if current:
        return min(current, key=lambda task: -task.priority)
    route_index = {position: index for index, position in enumerate(COMPACT_ROUTE)}
    return min(tasks, key=lambda task: (-task.priority, manhattan_distance(state.farmer, task.target), route_index.get(task.target, 999))) if tasks else None


def farmer_action(state: GameState, tasks: list[Task]) -> list[str]:
    task = choose_task(state, tasks)
    if task is not None:
        if state.farmer == task.target:
            return ["PLANT", task.crop] if task.kind == "PLANT" and task.crop else [task.kind]
        return [next_move(state.farmer, task.target, state.board_size)]
    if state.carried_count > 0 and should_liquidate_carried(state.day, state.hour):
        if state.farmer in shed_access_positions(state.board_size):
            return ["DROP"]
        return [next_move(state.farmer, nearest_shed_access(state.farmer, state.board_size), state.board_size)]
    return ["PASS"]


def decide(state: GameState, capacity: int) -> dict[str, list]:
    plan = build_crop_plan(state, capacity)
    empty_targets = {position: crop for position, crop in plan.targets.items() if crops.is_usable_empty(state.tile_at(position))}
    return {"farmer": farmer_action(state, generate_tasks(state, capacity, plan)), "hands": [], "market": build_market_orders(state, empty_targets)}
