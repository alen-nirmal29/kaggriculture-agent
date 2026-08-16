"""Task-based dynamic-crop V2 strategy."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Literal, Mapping

from agent_v2 import crops
from agent_v2.economics import CropScore, crop_allocation, score_all_crops
from agent_v2.endgame import is_final_day, should_liquidate_carried
from agent_v2.market import build_market_orders, live_crop_prices
from agent_v2.routing import manhattan_distance, nearest_shed_access, next_move, shed_access_positions
from agent_v2.state import GameState, Position

MANAGED_PLOTS: tuple[Position, ...] = ((4, 4), (3, 4), (2, 4), (1, 4), (1, 3), (2, 3))
PLOT_LIMIT = len(MANAGED_PLOTS)
SAFE_ACTION = {"farmer": ["PASS"], "hands": [], "market": []}
TaskKind = Literal["HARVEST", "WATER", "DIG", "PLANT"]


@dataclass(frozen=True)
class CropPlan:
    scores: Mapping[str, CropScore]
    allocation: Mapping[str, int]
    targets: Mapping[Position, str]

    @property
    def preferred(self) -> str | None:
        return max(self.allocation, key=self.allocation.get) if self.allocation else None


@dataclass(frozen=True)
class Task:
    kind: TaskKind
    target: Position
    priority: int
    crop: str | None = None


def managed_positions(state: GameState) -> tuple[Position, ...]:
    return tuple(p for p in MANAGED_PLOTS if p[0] < state.board_size and p[1] < state.board_size and not state.tile_at(p).is_locked)


def build_crop_plan(state: GameState) -> CropPlan:
    positions = managed_positions(state)
    existing = [crops.crop_type(state.tile_at(p)) for p in positions]
    existing_names = [crop for crop in existing if crop is not None]
    scores = score_all_crops(state.step, live_crop_prices(state))
    allocation = crop_allocation(scores, existing_names, len(positions))
    targets: dict[Position, str] = {}
    assigned = Counter(existing_names)
    for position in positions:
        current = crops.crop_type(state.tile_at(position))
        if current is not None:
            targets[position] = current
    for position in positions:
        if position in targets or not (crops.is_usable_empty(state.tile_at(position)) or crops.is_weed(state.tile_at(position))):
            continue
        deficits = [(wanted - assigned.get(crop, 0), scores[crop].score, crop) for crop, wanted in allocation.items()]
        viable = [item for item in deficits if item[0] > 0]
        if viable:
            _, _, chosen = max(viable, key=lambda item: (item[0], item[1], item[2]))
            targets[position] = chosen
            assigned[chosen] += 1
    return CropPlan(scores, allocation, targets)


def generate_tasks(state: GameState, plan: CropPlan) -> list[Task]:
    tasks: list[Task] = []
    for position in managed_positions(state):
        tile = state.tile_at(position)
        if crops.is_crop(tile):
            if crops.should_harvest(tile, state.day, is_final_day(state.day)):
                tasks.append(Task("HARVEST", position, 100))
            elif crops.is_exhausted_recurring(tile, state.day):
                tasks.append(Task("DIG", position, 80))
            elif not is_final_day(state.day) and crops.needs_water(tile):
                missed = int(tile.raw.get("consecutive_unwatered", 0))
                tasks.append(Task("WATER", position, 90 + missed))
        elif crops.is_weed(tile) and position in plan.targets:
            tasks.append(Task("DIG", position, 80))
        elif crops.is_usable_empty(tile) and position in plan.targets:
            crop = plan.targets[position]
            if state.seed_count(crop) > 0:
                tasks.append(Task("PLANT", position, 70, crop))
    return tasks


def choose_task(state: GameState, tasks: list[Task]) -> Task | None:
    # Complete a valid task on the current tile before walking away. This turns
    # synchronized crop renewal into HARVEST -> PLANT -> WATER per tile and
    # avoids traversing the six-plot route twice on turnover days.
    current = [task for task in tasks if task.target == state.farmer]
    if current:
        return min(current, key=lambda task: -task.priority)
    route_index = {position: index for index, position in enumerate(MANAGED_PLOTS)}
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


def decide(state: GameState) -> dict[str, list]:
    plan = build_crop_plan(state)
    empty_targets = {position: crop for position, crop in plan.targets.items() if crops.is_usable_empty(state.tile_at(position))}
    return {
        "farmer": farmer_action(state, generate_tasks(state, plan)),
        "hands": [],
        "market": build_market_orders(state, empty_targets),
    }
