"""Deterministic task-based Kaggriculture V1 strategy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from agent import crops
from agent.economics import choose_v1_crop
from agent.endgame import is_final_day, should_invest
from agent.market import build_market_orders
from agent.routing import manhattan_distance, nearest_shed_access, next_move, shed_access_positions
from agent.state import GameState, Position

PRIMARY_CROP = choose_v1_crop()
MANAGED_PLOTS: tuple[Position, ...] = ((4, 4), (3, 4), (2, 4), (1, 4), (1, 3), (2, 3))
SAFE_ACTION = {"farmer": ["PASS"], "hands": [], "market": []}

TaskKind = Literal["HARVEST", "WATER", "DIG", "PLANT"]


@dataclass(frozen=True)
class Task:
    kind: TaskKind
    target: Position
    priority: int


def _managed_positions(state: GameState) -> tuple[Position, ...]:
    return tuple(
        position
        for position in MANAGED_PLOTS
        if position[0] < state.board_size
        and position[1] < state.board_size
        and not state.tile_at(position).is_locked
    )


def generate_tasks(state: GameState, invest: bool) -> list[Task]:
    tasks: list[Task] = []
    for position in _managed_positions(state):
        tile = state.tile_at(position)
        if crops.is_crop(tile):
            if crops.is_at_target_harvest_age(tile, state.day) or (
                is_final_day(state.day) and crops.is_harvestable(tile, state.day)
            ):
                tasks.append(Task("HARVEST", position, 100))
            elif not is_final_day(state.day) and crops.needs_water(tile):
                # A plant already missed once is at immediate risk at day end.
                missed = int(tile.raw.get("consecutive_unwatered", 0))
                tasks.append(Task("WATER", position, 90 + missed))
        elif crops.is_weed(tile) and invest:
            tasks.append(Task("DIG", position, 75))
        elif crops.is_usable_empty(tile) and invest and state.seed_count(PRIMARY_CROP) > 0:
            tasks.append(Task("PLANT", position, 70))
    return tasks


def _choose_task(state: GameState, tasks: list[Task]) -> Task | None:
    if not tasks:
        return None
    # Prefer the highest need, then shortest movement, then the explicit plot
    # route. The stable route index makes equal situations reproducible.
    route_index = {position: index for index, position in enumerate(MANAGED_PLOTS)}
    return min(
        tasks,
        key=lambda task: (
            -task.priority,
            manhattan_distance(state.farmer, task.target),
            route_index.get(task.target, 999),
        ),
    )


def _farmer_action(state: GameState, tasks: list[Task]) -> list[str]:
    task = _choose_task(state, tasks)
    if task is not None:
        if state.farmer == task.target:
            return [task.kind, PRIMARY_CROP] if task.kind == "PLANT" else [task.kind]
        return [next_move(state.farmer, task.target, state.board_size)]

    # End-of-day auto-drop handles normal harvests cheaply. Explicitly return
    # carried goods in the endgame so the final bank reward includes them.
    if state.carried_count > 0 and is_final_day(state.day):
        if state.farmer in shed_access_positions(state.board_size):
            return ["DROP"]
        target = nearest_shed_access(state.farmer, state.board_size)
        return [next_move(state.farmer, target, state.board_size)]
    return ["PASS"]


def decide(state: GameState) -> dict[str, list]:
    invest = should_invest(state.day, PRIMARY_CROP)
    managed = _managed_positions(state)
    existing_plants = sum(1 for position in managed if crops.is_crop(state.tile_at(position)))
    market = build_market_orders(state, PRIMARY_CROP, len(managed), existing_plants, invest)
    farmer = _farmer_action(state, generate_tasks(state, invest))
    return {"farmer": farmer, "hands": [], "market": market}
