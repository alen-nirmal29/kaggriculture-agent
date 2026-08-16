"""Crop rules mirrored from Kaggriculture 1.32.7."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from agent.state import TileView


@dataclass(frozen=True)
class CropDefinition:
    seed_cost: int
    first_yield_day: int
    max_yield_day: int
    interval: int
    max_yield: int
    ongoing: bool


CROPS: dict[str, CropDefinition] = {
    "WHEAT": CropDefinition(10, 2, 4, 0, 6, False),
    "CARROT": CropDefinition(20, 2, 3, 0, 4, False),
    "TOMATO": CropDefinition(50, 8, 8, 1, 4, True),
    "STRAWBERRY": CropDefinition(100, 10, 10, 2, 4, True),
    "MELON": CropDefinition(80, 10, 12, 0, 6, False),
}


def _raw(tile: TileView | Any) -> Any:
    return tile.raw if isinstance(tile, TileView) else tile


def is_usable_empty(tile: TileView | Any) -> bool:
    return _raw(tile) is None


def is_weed(tile: TileView | Any) -> bool:
    raw = _raw(tile)
    return isinstance(raw, Mapping) and raw.get("kind") == "WEED"


def is_crop(tile: TileView | Any) -> bool:
    raw = _raw(tile)
    return isinstance(raw, Mapping) and raw.get("kind") == "PLANT"


def crop_type(tile: TileView | Any) -> str | None:
    raw = _raw(tile)
    return str(raw["crop"]) if is_crop(raw) and "crop" in raw else None


def crop_age(tile: TileView | Any, day: int) -> int | None:
    raw = _raw(tile)
    return day - int(raw["planted_day"]) if is_crop(raw) else None


def is_watered(tile: TileView | Any) -> bool:
    raw = _raw(tile)
    return bool(raw.get("watered_today", False)) if is_crop(raw) else False


def needs_water(tile: TileView | Any) -> bool:
    return is_crop(tile) and not is_watered(tile)


def watering_adds_yield(tile: TileView | Any, day: int) -> bool:
    raw = _raw(tile)
    if not is_crop(raw) or raw.get("watered_today", False):
        return False
    definition = CROPS[str(raw["crop"])]
    if definition.ongoing:
        return True
    age = day - int(raw["planted_day"])
    window_start = (definition.max_yield_day + 1) // 2
    return window_start <= age <= definition.max_yield_day


def is_harvestable(tile: TileView | Any, day: int) -> bool:
    raw = _raw(tile)
    if not is_crop(raw):
        return False
    definition = CROPS[str(raw["crop"])]
    return day - int(raw["planted_day"]) >= definition.first_yield_day and int(raw.get("yield_units", 0)) > 0


def is_at_target_harvest_age(tile: TileView | Any, day: int) -> bool:
    raw = _raw(tile)
    if not is_crop(raw):
        return False
    definition = CROPS[str(raw["crop"])]
    return is_harvestable(raw, day) and (definition.ongoing or day - int(raw["planted_day"]) >= definition.max_yield_day)


def is_dead_or_expired(tile: TileView | Any, step: int) -> bool:
    raw = _raw(tile)
    if is_weed(raw):
        return True
    if not is_crop(raw):
        return False
    lifespan = int(raw.get("max_lifespan_step", -1))
    return lifespan >= 0 and step >= lifespan and int(raw.get("yield_units", 0)) <= 0
