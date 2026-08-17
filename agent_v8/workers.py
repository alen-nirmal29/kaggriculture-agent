"""Official-mechanics worker hiring and deterministic task assignment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from agent_v4.routing import manhattan_distance, nearest_shed_access, next_move, shed_access_positions
from agent_v4.state import GameState, Position

TaskKind = Literal["HARVEST", "WATER", "DIG", "PLANT", "DEPOSIT"]


@dataclass(frozen=True)
class WorkTask:
    kind: TaskKind
    target: Position
    priority: int
    urgency: int = 0
    economic_value: float = 0.0
    crop: str | None = None
    owner: int | None = None


@dataclass(frozen=True)
class Unit:
    index: int  # zero is farmer; positive values are hand indices + 1
    position: Position
    carried_count: int


def fibonacci(index: int) -> int:
    if index < 0:
        raise ValueError("hire index cannot be negative")
    a, b = 1, 1
    for _ in range(index):
        a, b = b, a + b
    return a


def hire_cost(hires_today: int, multiplier: int = 1) -> int:
    return multiplier * fibonacci(hires_today)


def units(state: GameState) -> tuple[Unit, ...]:
    return (Unit(0, state.farmer, state.carried_count),) + tuple(
        Unit(hand.index + 1, hand.position, hand.carried_count) for hand in state.hands
    )


def choose_task(unit: Unit, tasks: list[WorkTask], reserved: set[Position]) -> WorkTask | None:
    available = [task for task in tasks if task.target not in reserved and (task.owner is None or task.owner == unit.index)]
    if not available:
        return None
    return max(
        available,
        key=lambda task: (
            task.priority * 100 + task.urgency * 10 + task.economic_value - manhattan_distance(unit.position, task.target),
            unit.position == task.target,
            -task.target[1],
            -task.target[0],
        ),
    )


def task_action(state: GameState, unit: Unit, task: WorkTask | None) -> list[str]:
    if task is None:
        if unit.carried_count:
            target = nearest_shed_access(unit.position, state.board_size)
            return ["DROP"] if unit.position in shed_access_positions(state.board_size) else [next_move(unit.position, target, state.board_size)]
        return ["PASS"]
    if unit.position != task.target:
        return [next_move(unit.position, task.target, state.board_size)]
    if task.kind == "PLANT" and task.crop:
        return ["PLANT", task.crop]
    if task.kind == "DEPOSIT":
        return ["DROP"]
    return [task.kind]


def assign_tasks(state: GameState, tasks: list[WorkTask]) -> dict[int, WorkTask | None]:
    assignments: dict[int, WorkTask | None] = {unit.index: None for unit in units(state)}
    reserved: set[Position] = set()
    seed_remaining = {crop: state.seed_count(crop) for crop in state.seeds}
    available_units = list(units(state))
    ordered = sorted(tasks, key=lambda task: (-task.priority, -task.urgency, -task.economic_value, task.target[1], task.target[0]))
    for task in ordered:
        if task.target in reserved or (task.kind == "PLANT" and (not task.crop or seed_remaining.get(task.crop, 0) <= 0)):
            continue
        eligible = [unit for unit in available_units if task.owner is None or task.owner == unit.index]
        if not eligible:
            continue
        selected_unit = min(eligible, key=lambda unit: (manhattan_distance(unit.position, task.target), unit.index))
        assignments[selected_unit.index] = task
        available_units.remove(selected_unit)
        reserved.add(task.target)
        if task.kind == "PLANT" and task.crop:
            seed_remaining[task.crop] -= 1
    return assignments


def hiring_orders(state: GameState, max_hands: int, estimated_work: int, cash_reserve: float = 200.0) -> list[list[str]]:
    if not 0 <= max_hands <= 4:
        raise ValueError("max_hands must be between 0 and 4")
    current = len(state.hands)
    slots = max(0, max_hands - current)
    if slots == 0 or state.remaining_turns <= 2 or state.hour >= 22:
        return []
    orders: list[list[str]] = []
    money = state.money
    # A hire made now can contribute only on later turns and vanishes overnight.
    useful_turns = min(23 - state.hour, state.remaining_turns - 1)
    for offset in range(slots):
        cost = hire_cost(state.hires_today + offset)
        marginal_work = max(0, estimated_work - (current + len(orders) + 1))
        expected_value = min(useful_turns, marginal_work) * 2.0
        if useful_turns <= 0 or marginal_work <= 0 or expected_value <= cost or money - cost < cash_reserve:
            break
        orders.append(["HIRE"])
        money -= cost
    return orders
