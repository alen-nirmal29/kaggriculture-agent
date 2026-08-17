"""V6: frozen V4 crops plus isolated, capacity-aware livestock tasks."""
from __future__ import annotations
from collections import Counter
from typing import Mapping
from agent_v4 import crops
from agent_v4.economics import score_all_crops
from agent_v4.market import live_crop_prices
from agent_v4.strategy import EXTENDED_ROUTE
from agent_v3.strategy import CropPlan, _capacity_safe_allocation
from agent_v4.endgame import is_final_day
from agent_v4.market import build_market_orders
from agent_v4.strategy import SAFE_ACTION
from agent_v4.workers import WorkTask, assign_tasks, hiring_orders, task_action, units
from agent_v6.animals import Mode, animal_roi, animal_tasks, configured_species, format_animal_action, required_market_orders, structure_positions
from agent_v6.state import GameState

def _crop_tasks(state: GameState, capacity: int):
    positions = tuple(p for p in EXTENDED_ROUTE if not state.tile_at(p).is_locked)[:capacity]
    existing = [c for p in positions if (c := crops.crop_type(state.tile_at(p))) is not None]
    scores = score_all_crops(state.step, live_crop_prices(state)); allocation = _capacity_safe_allocation(scores, existing, len(positions))
    targets = {}; assigned = Counter(existing)
    for p in positions:
        if (c := crops.crop_type(state.tile_at(p))) is not None: targets[p] = c
    for p in positions:
        tile = state.tile_at(p)
        if p in targets or not (crops.is_usable_empty(tile) or crops.is_weed(tile)): continue
        viable = [(n-assigned.get(c,0), scores[c].score, c) for c,n in allocation.items() if n-assigned.get(c,0)>0]
        if viable:
            _,_,c=max(viable); targets[p]=c; assigned[c]+=1
    plan = CropPlan(scores, allocation, targets); result=[]
    for p in positions:
        tile=state.tile_at(p); kind=None; priority=0; crop=crops.crop_type(tile); urgency=0
        if crops.is_crop(tile):
            if crops.should_harvest(tile,state.day,is_final_day(state.day)): kind,priority="HARVEST",100
            elif crops.is_exhausted_recurring(tile,state.day): kind,priority="DIG",80
            elif not is_final_day(state.day) and crops.needs_water(tile): kind,priority="WATER",90; urgency=int(tile.raw.get("consecutive_unwatered",0))
        elif crops.is_weed(tile) and p in targets: kind,priority="DIG",80
        elif crops.is_usable_empty(tile) and p in targets and state.seed_count(targets[p])>0: kind,priority,crop="PLANT",70,targets[p]
        if kind: result.append(WorkTask(kind,p,priority,urgency,float(state.market_prices.get(crop,0)) if crop else 0.0,crop))
    return plan, result

def decide(state: GameState, max_hands=4, capacity=24, *, mode: Mode="NONE", caps: Mapping[str, int] | None=None, fertilizer_enabled=False):
    if mode == "NONE":
        from agent_v4.strategy import decide as v4_decide
        return v4_decide(state, max_hands, capacity)
    caps = dict(caps or {"GOOSE": 1, "COW": 1, "SHEEP": 1})
    proposed = configured_species(mode, caps)
    affordable = tuple(s for s in proposed if animal_roi(s, state.day, state.market_prices, fertilizer_enabled=fertilizer_enabled).expected_value > 0)
    species = proposed if any(s.animal for s in state.structures) else affordable
    positions = structure_positions(state, len(species)); crop_capacity = max(12, capacity - len(positions))
    plan, crop_tasks = _crop_tasks(state, crop_capacity)
    empty = {p: c for p, c in plan.targets.items() if state.tile_at(p).is_empty}
    market = build_market_orders(state, empty)
    if any(s.animal for s in state.structures):
        # Retain a survival reserve instead of selling wheat and buying it back.
        reserve = sum(1 for s in state.structures if s.animal)
        adjusted = []
        for order in market:
            if order[:2] == ["SELL", "WHEAT"]:
                quantity = max(0, int(order[2]) - reserve)
                if quantity: adjusted.append(["SELL", "WHEAT", quantity])
            else: adjusted.append(order)
        market = adjusted
    market += required_market_orders(state, species, positions, state.day < 29)
    tasks = crop_tasks + animal_tasks(state, species, positions, fertilizer_enabled)
    hires = hiring_orders(state, max_hands, len(tasks) + len(empty))
    assignments = assign_tasks(state, tasks); active = units(state); actions = []
    for unit in active:
        task = assignments.get(unit.index); actions.append(format_animal_action(state, unit, task) or task_action(state, unit, task))
    if is_final_day(state.day) and state.remaining_turns < 4: hires = []
    return {"farmer": actions[0], "hands": actions[1:], "market": market + hires}
