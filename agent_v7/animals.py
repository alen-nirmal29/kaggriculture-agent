"""Official-mechanics livestock model and deterministic animal work generation."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Mapping
from agent_v4.routing import nearest_shed_access
from agent_v4.strategy import EXTENDED_ROUTE
from agent_v4.workers import WorkTask, Unit
from agent_v6.state import GameState

Species = Literal["GOOSE", "COW", "SHEEP"]
Mode = Literal["NONE", "GOOSE_ONLY", "COW_ONLY", "SHEEP_ONLY", "MIXED"]
ANIMAL_DATA = {
    "GOOSE": {"cost": 300, "structure": "COOP", "first_yield_day": 4, "interval": 1, "max_held": 4, "product": "EGG"},
    "COW": {"cost": 400, "structure": "PASTURE", "first_yield_day": 8, "interval": 2, "max_held": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "first_yield_day": 6, "interval": 3, "max_held": 6, "product": "WOOL"},
}
PRODUCT_BASE = {"EGG": 50, "MILK": 160, "WOOL": 200}

@dataclass(frozen=True)
class AnimalEconomics:
    species: Species
    remaining_cycles: int
    product_revenue: float
    fertilizer_value: float
    purchase_cost: float
    structure_cost: float
    feed_cost: float
    labor_cost: float
    crop_opportunity_cost: float
    expected_value: float

def production_cycles(species: Species, current_day: int, placed_day: int | None = None) -> int:
    data = ANIMAL_DATA[species]
    start = current_day if placed_day is None else placed_day
    first = start + int(data["first_yield_day"])
    return 0 if first > 29 else 1 + (29 - first) // int(data["interval"])

def animal_roi(species: Species, current_day: int, prices: Mapping[str, int], *, structure_cost: float = 0.0,
               crop_opportunity_cost: float = 500.0, labor_action_value: float = 2.0,
               fertilizer_enabled: bool = False) -> AnimalEconomics:
    data = ANIMAL_DATA[species]
    cycles, days = production_cycles(species, current_day), max(0, 30 - current_day)
    product_revenue = cycles * float(prices.get(str(data["product"]), PRODUCT_BASE[str(data["product"])]))
    feed_cost = days * float(prices.get("WHEAT", 25))
    labor_cost = (days + 3 + cycles) * labor_action_value
    fertilizer_value = days * float(prices.get("FERTILIZER", 100)) if fertilizer_enabled else 0.0
    purchase = float(data["cost"])
    value = product_revenue + fertilizer_value - purchase - structure_cost - feed_cost - labor_cost - crop_opportunity_cost
    return AnimalEconomics(species, cycles, product_revenue, fertilizer_value, purchase, structure_cost,
                           feed_cost, labor_cost, crop_opportunity_cost, value)

def configured_species(mode: Mode, caps: Mapping[str, int]) -> tuple[Species, ...]:
    if mode == "NONE": return ()
    names = ("GOOSE", "COW", "SHEEP") if mode == "MIXED" else (mode.removesuffix("_ONLY"),)
    return tuple(name for name in names for _ in range(max(0, int(caps.get(name, 0)))))  # type: ignore[misc]

def structure_positions(state: GameState, count: int) -> tuple[tuple[int, int], ...]:
    usable = [p for p in EXTENDED_ROUTE if not state.tile_at(p).is_locked]
    return tuple(reversed(usable[-count:])) if count else ()

def carried_total(state: GameState, item: str) -> int:
    return sum(int(state.unit_inventory(i).get(item, 0)) for i in range(len(state.hands) + 1))

def required_market_orders(state: GameState, species: tuple[Species, ...], positions, buy_allowed=True):
    orders = []
    for product in ("EGG", "MILK", "WOOL"):
        if (n := int(state.shed.get(product, 0))): orders.append(["SELL", product, n])
    existing = {s.position: s for s in state.structures}
    available = {name: int(state.shed.get(name, 0)) + carried_total(state, name) for name in ANIMAL_DATA}
    for wanted, position in zip(species, positions):
        if existing.get(position) and existing[position].animal: continue
        if buy_allowed and available[wanted] <= 0:
            orders.append(["BUY_ANIMAL", wanted, 1]); available[wanted] += 1
    living = sum(1 for s in state.structures if s.animal)
    wheat = int(state.shed.get("WHEAT", 0)) + carried_total(state, "WHEAT")
    if living and wheat < living: orders.append(["BUY_PRODUCT", "WHEAT", living - wheat])
    return orders

def animal_tasks(state: GameState, species: tuple[Species, ...], positions, fertilizer_enabled=False):
    tasks = []; existing = {s.position: s for s in state.structures}; unit_count = len(state.hands) + 1
    if fertilizer_enabled:
        carrier = next((i for i in range(unit_count) if int(state.unit_inventory(i).get("FERTILIZER", 0)) > 0), None)
        candidates = [t for t in state.iter_tiles() if isinstance(t.raw, dict) and t.raw.get("kind") == "PLANT"
                      and int(t.raw.get("fertilized_until_day", -1)) < state.day]
        if carrier is not None and candidates and state.day < 29:
            target = max(candidates, key=lambda t: (float(state.market_prices.get(t.raw.get("crop"), 0)), -t.position[1], -t.position[0]))
            tasks.append(WorkTask("FERTILIZE", target.position, 75, owner=carrier,
                                  economic_value=float(state.market_prices.get(target.raw.get("crop"), 0))))  # type: ignore[arg-type]
        elif carrier is None and int(state.shed.get("FERTILIZER", 0)) > 0 and state.day < 29:
            tasks.append(WorkTask("PICKUP_FERTILIZER", nearest_shed_access(state.farmer, state.board_size), 74))  # type: ignore[arg-type]
    for wanted, pos in zip(species, positions):
        tile, structure = state.tile_at(pos).raw, existing.get(pos)
        if structure is None:
            kind = "DIG" if tile is not None else ("BUILD_COOP" if wanted == "GOOSE" else "BUILD_PASTURE")
            tasks.append(WorkTask(kind, pos, 125, economic_value=1000.0)); continue  # type: ignore[arg-type]
        if structure.animal is None:
            carrier = next((i for i in range(unit_count) if int(state.unit_inventory(i).get(wanted, 0)) > 0), None)
            if carrier is not None: tasks.append(WorkTask("PLACE_ANIMAL", pos, 124, owner=carrier, crop=wanted))  # type: ignore[arg-type]
            elif int(state.shed.get(wanted, 0)) > 0:
                tasks.append(WorkTask("PICKUP_ANIMAL", nearest_shed_access(state.farmer, state.board_size), 124, crop=wanted))  # type: ignore[arg-type]
            continue
        if not structure.fed_today:
            feeder = next((i for i in range(unit_count) if int(state.unit_inventory(i).get("WHEAT", 0)) > 0), None)
            if feeder is not None: tasks.append(WorkTask("FEED", pos, 150 + structure.consecutive_unfed * 20, owner=feeder))
            elif int(state.shed.get("WHEAT", 0)) > 0:
                tasks.append(WorkTask("PICKUP_FEED", nearest_shed_access(state.farmer, state.board_size), 149 + structure.consecutive_unfed * 20))  # type: ignore[arg-type]
            continue
        if structure.yield_units:
            tasks.append(WorkTask("HARVEST", pos, 130, economic_value=float(structure.yield_units * PRODUCT_BASE[str(ANIMAL_DATA[structure.animal]["product"])])))
        elif not structure.cared_today and production_cycles(structure.animal, state.day, structure.placed_day) > 0:  # type: ignore[arg-type]
            tasks.append(WorkTask("CARE", pos, 65))  # type: ignore[arg-type]
        elif fertilizer_enabled and structure.fertilizer_available:
            tasks.append(WorkTask("COLLECT_FERTILIZER", pos, 55))  # type: ignore[arg-type]
    return tasks

def format_animal_action(state: GameState, unit: Unit, task: WorkTask | None):
    special = {"BUILD_COOP", "BUILD_PASTURE", "PLACE_ANIMAL", "PICKUP_ANIMAL", "PICKUP_FEED", "PICKUP_FERTILIZER", "FEED", "CARE", "COLLECT_FERTILIZER"}
    if task is None or task.kind not in special: return None
    if unit.position != task.target:
        from agent_v4.routing import next_move
        return [next_move(unit.position, task.target, state.board_size)]
    if task.kind == "PLACE_ANIMAL": return ["PLACE", str(task.crop)]
    if task.kind == "PICKUP_ANIMAL": return ["PICKUP", str(task.crop), "1"]
    if task.kind == "PICKUP_FEED": return ["PICKUP", "WHEAT", "1"]
    if task.kind == "PICKUP_FERTILIZER": return ["PICKUP", "FERTILIZER", "1"]
    return [str(task.kind)]
