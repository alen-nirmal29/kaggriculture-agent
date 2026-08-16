"""V3 reuses frozen V2 crop definitions and lifecycle helpers unchanged."""

from agent_v2.crops import CROP_NAMES, CROPS, crop_type, is_crop, is_exhausted_recurring, is_harvestable, is_usable_empty, is_weed, needs_water, should_harvest

__all__ = ["CROP_NAMES", "CROPS", "crop_type", "is_crop", "is_exhausted_recurring", "is_harvestable", "is_usable_empty", "is_weed", "needs_water", "should_harvest"]
