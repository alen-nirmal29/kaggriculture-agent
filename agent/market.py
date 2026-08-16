"""Minimal V1 seed purchasing and product selling."""

from agent.crops import CROPS
from agent.state import GameState

PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")


def sell_orders(state: GameState) -> list[list[object]]:
    return [["SELL", item, int(state.shed.get(item, 0))] for item in PRODUCTS if int(state.shed.get(item, 0)) > 0]


def seed_order(state: GameState, crop: str, desired_total: int, existing_plants: int, invest: bool) -> list[object] | None:
    if not invest:
        return None
    missing = max(0, desired_total - existing_plants - state.seed_count(crop))
    affordable = int(state.money) // CROPS[crop].seed_cost
    quantity = min(missing, affordable)
    return ["BUY_SEED", crop, quantity] if quantity > 0 else None


def build_market_orders(state: GameState, crop: str, desired_total: int, existing_plants: int, invest: bool) -> list[list[object]]:
    orders = sell_orders(state)
    buy = seed_order(state, crop, desired_total, existing_plants, invest)
    if buy is not None:
        orders.append(buy)
    return orders
