"""V2 dynamic crop economics tests."""

from agent_v2.crops import CROP_NAMES
from agent_v2.economics import crop_allocation, evaluate_crop, remaining_harvest_opportunities, score_all_crops

BASE_PRICES = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250}


def test_all_five_crops_are_evaluated() -> None:
    assert set(score_all_crops(0, BASE_PRICES)) == set(CROP_NAMES)


def test_higher_live_price_increases_crop_score() -> None:
    low = evaluate_crop("MELON", 0, 100)
    high = evaluate_crop("MELON", 0, 300)
    assert high.score > low.score
    assert high.expected_revenue > low.expected_revenue


def test_less_season_reduces_slow_crop_value() -> None:
    assert evaluate_crop("STRAWBERRY", 0, 120).score > evaluate_crop("STRAWBERRY", 24 * 15, 120).score


def test_crop_that_cannot_mature_is_not_allocated() -> None:
    scores = score_all_crops(719, BASE_PRICES)
    assert all(score.expected_units == 0 for score in scores.values())
    assert crop_allocation(scores, [], 6) == {}


def test_recurring_crop_counts_remaining_production_cycles() -> None:
    assert remaining_harvest_opportunities("TOMATO", 0) == 8
    assert remaining_harvest_opportunities("TOMATO", 24 * 15) == 4
    assert remaining_harvest_opportunities("TOMATO", 24 * 23) == 0


def test_recurring_crop_allocation_respects_workload_cap() -> None:
    prices = dict(BASE_PRICES, TOMATO=1000)
    scores = score_all_crops(0, prices)
    allocation = crop_allocation(scores, [], 6)
    assert allocation["TOMATO"] <= 4
    assert sum(allocation.values()) <= 6
