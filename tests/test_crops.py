"""Crop rule helper tests."""

from agent.crops import crop_age, is_at_target_harvest_age, is_harvestable, needs_water, watering_adds_yield


def wheat(planted_day=0, watered=False, yield_units=1):
    return {"kind": "PLANT", "crop": "WHEAT", "planted_day": planted_day, "watered_today": watered, "yield_units": yield_units, "max_lifespan_step": 120}


def test_wheat_age_water_and_harvest_rules() -> None:
    tile = wheat()

    assert crop_age(tile, 2) == 2
    assert needs_water(tile)
    assert watering_adds_yield(tile, 2)
    assert is_harvestable(tile, 2)
    assert not is_at_target_harvest_age(tile, 2)
    assert is_at_target_harvest_age(tile, 4)
