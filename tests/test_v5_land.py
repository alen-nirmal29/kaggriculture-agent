"""V5 official land mechanics, ROI decisions, selection, and reliability."""

import copy
from kaggle_environments import make
import pytest

from agent_v5.land import LAND_COSTS, estimate_land_payback, expansion_count, next_land_cost, next_quadrant, should_buy_next_land
from agent_v5.state import GameState
from agent_v5.strategy import select_managed_tiles
from main_v4 import agent as v4_agent
from main_v5 import make_agent


def expanded_observation(initial_observation, quadrants):
    obs = copy.deepcopy(initial_observation); farm = obs["farms"][obs["player"]]
    farm["unlocked_quadrants"] = list(quadrants)
    for y, row in enumerate(farm["tiles"]):
        for x, tile in enumerate(row):
            quadrant = ("N" if y < 5 else "S") + ("W" if x < 5 else "E")
            if quadrant in quadrants and tile == "LOCKED": row[x] = None
    return obs


def test_initial_land_parser_and_next_unlock(initial_observation):
    state = GameState.from_observation(initial_observation)
    assert state.unlocked_quadrants == ("NW",) and expansion_count(state) == 0
    assert next_quadrant(state) == "NE" and next_land_cost(state) == 1000


def test_official_land_cost_sequence(initial_observation):
    for count, cost in enumerate(LAND_COSTS):
        quadrants = ("NW", "NE", "SW", "SE")[:count + 1]
        assert next_land_cost(GameState.from_observation(expanded_observation(initial_observation, quadrants))) == cost


@pytest.mark.parametrize("cap", range(4))
def test_expansion_caps_and_buy_schema(initial_observation, cap):
    action = make_agent(cap)(initial_observation)
    buys = [order for order in action["market"] if order == ["BUY_LAND"]]
    assert len(buys) <= (1 if cap else 0)


def test_zero_expansion_is_exact_v4_control(initial_observation):
    assert make_agent(0)(initial_observation) == v4_agent(initial_observation)


def test_land_rejected_by_cash_reserve(initial_observation):
    obs = copy.deepcopy(initial_observation); obs["farms"][0]["money"] = 1200
    state = GameState.from_observation(obs)
    assert not should_buy_next_land(state, 1, 48, 10000)


def test_land_rejected_near_endgame(initial_observation):
    obs = copy.deepcopy(initial_observation); obs.update(step=700, day=29, hour=4)
    state = GameState.from_observation(obs)
    assert not should_buy_next_land(state, 1, 48, 10000)


def test_land_accepted_in_clearly_profitable_state(initial_observation):
    state = GameState.from_observation(initial_observation)
    assert should_buy_next_land(state, 1, 48, 10000)
    estimate = estimate_land_payback(state, 48, 10000)
    assert estimate.repayable and estimate.affordable


def test_new_land_becomes_eligible_without_duplicates(initial_observation):
    state = GameState.from_observation(expanded_observation(initial_observation, ("NW", "NE")))
    positions = select_managed_tiles(state, 40)
    assert len(positions) == len(set(positions)) == 40
    assert any(x >= 5 and y < 5 for x, y in positions)
    assert all(not state.tile_at(position).is_locked for position in positions)


def test_post_purchase_transition_changes_next_cost(initial_observation):
    before = GameState.from_observation(initial_observation)
    after = GameState.from_observation(expanded_observation(initial_observation, ("NW", "NE")))
    assert next_land_cost(before) == 1000 and next_land_cost(after) == 2000


def test_v5_full_episode_completes():
    env = make("kaggriculture", configuration={"seed": 850001}, debug=True)
    env.run([make_agent(3), "starter"])
    assert len(env.steps) == 720 and env.state[0].status == "DONE"
