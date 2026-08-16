"""Crop lifecycle helpers grounded in Kaggriculture 1.32.7."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from agent_v2.state import TileView


@dataclass(frozen=True)
class CropDefinition:
    seed_cost: int
    first_yield_day: int
    max_yield_day: int
    interval: int
    max_yield: int
    ongoing: bool
    target_harvest_age: int
    expected_one_time_yield: int

    @property
    def production_ages(self) -> tuple[int, ...]:
        if not self.ongoing:
            return (self.target_harvest_age,)
        return tuple(self.first_yield_day + self.interval * index for index in range(self.max_yield))


CROPS: dict[str, CropDefinition] = {
    "WHEAT": CropDefinition(10, 2, 4, 0, 6, False, 4, 4),
    "CARROT": CropDefinition(20, 2, 3, 0, 4, False, 3, 3),
    "TOMATO": CropDefinition(50, 8, 8, 1, 4, True, 11, 0),
    "STRAWBERRY": CropDefinition(100, 10, 10, 2, 4, True, 16, 0),
    "MELON": CropDefinition(80, 10, 12, 0, 6, False, 10, 6),
}

CROP_NAMES = tuple(CROPS)


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
    return str(raw["crop"]) if is_crop(raw) and raw.get("crop") in CROPS else None


def crop_age(tile: TileView | Any, day: int) -> int | None:
    raw = _raw(tile)
    return day - int(raw["planted_day"]) if is_crop(raw) else None


def needs_water(tile: TileView | Any) -> bool:
    raw = _raw(tile)
    return is_crop(raw) and not bool(raw.get("watered_today", False))


def is_harvestable(tile: TileView | Any, day: int) -> bool:
    raw = _raw(tile)
    crop = crop_type(raw)
    return crop is not None and day - int(raw["planted_day"]) >= CROPS[crop].first_yield_day and int(raw.get("yield_units", 0)) > 0


def should_harvest(tile: TileView | Any, day: int, final_day: bool = False) -> bool:
    raw = _raw(tile)
    crop = crop_type(raw)
    if crop is None or not is_harvestable(raw, day):
        return False
    definition = CROPS[crop]
    return final_day or definition.ongoing or day - int(raw["planted_day"]) >= definition.target_harvest_age


def is_exhausted_recurring(tile: TileView | Any, day: int) -> bool:
    raw = _raw(tile)
    crop = crop_type(raw)
    if crop is None or not CROPS[crop].ongoing:
        return False
    age = day - int(raw["planted_day"])
    return age >= CROPS[crop].production_ages[-1] and int(raw.get("yield_units", 0)) <= 0
