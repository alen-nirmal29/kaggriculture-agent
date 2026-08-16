"""Crop-only V2 market orders using live state and safe affordability."""

from collections import Counter
from typing import Mapping

from agent_v2.crops import CROPS, CROP_NAMES
from agent_v2.state import GameState, Position


def live_crop_prices(state: GameState) -> dict[str, int]:
    return {crop: int(state.market_prices.get(crop, 1)) for crop in CROP_NAMES}


def live_crop_inventory(state: GameState) -> dict[str, int]:
    return {crop: int(state.market_inventory.get(crop, 0)) for crop in CROP_NAMES}


def sell_orders(state: GameState) -> list[list[object]]:
    return [["SELL", crop, int(state.shed.get(crop, 0))] for crop in CROP_NAMES if int(state.shed.get(crop, 0)) > 0]


def seed_orders(state: GameState, empty_targets: Mapping[Position, str]) -> list[list[object]]:
    needed = Counter(empty_targets.values())
    budget = int(state.money)
    orders: list[list[object]] = []
    for crop in CROP_NAMES:
        missing = max(0, needed.get(crop, 0) - state.seed_count(crop))
        affordable = budget // CROPS[crop].seed_cost
        quantity = min(missing, affordable)
        if quantity > 0:
            orders.append(["BUY_SEED", crop, quantity])
            budget -= quantity * CROPS[crop].seed_cost
    return orders


def build_market_orders(state: GameState, empty_targets: Mapping[Position, str]) -> list[list[object]]:
    return sell_orders(state) + seed_orders(state, empty_targets)
