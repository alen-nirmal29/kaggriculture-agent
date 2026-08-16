"""V3 capacity configuration, interface, and environment tests."""

from kaggle_environments import make
import pytest

from agent_v2.economics import score_all_crops as v2_score_all_crops
from agent_v3.economics import score_all_crops as v3_score_all_crops
from agent_v3.state import GameState
from agent_v3.strategy import SUPPORTED_CAPACITIES, build_crop_plan, select_managed_tiles
from main_v3 import make_agent


def assert_valid_action(action) -> None:
    assert set(action) == {"farmer", "hands", "market"}
    assert isinstance(action["farmer"], list) and action["farmer"]
    assert isinstance(action["hands"], list)
    assert isinstance(action["market"], list)


@pytest.mark.parametrize("capacity", SUPPORTED_CAPACITIES)
def test_v3_supports_each_candidate_capacity(initial_observation, capacity) -> None:
    state = GameState.from_observation(initial_observation)
    positions = select_managed_tiles(state, capacity)
    plan = build_crop_plan(state, capacity)
    assert len(positions) <= capacity
    assert len(plan.targets) <= capacity
    assert sum(plan.allocation.values()) <= capacity


@pytest.mark.parametrize("capacity", SUPPORTED_CAPACITIES)
def test_managed_tiles_are_unique_accessible_and_in_bounds(initial_observation, capacity) -> None:
    state = GameState.from_observation(initial_observation)
    positions = select_managed_tiles(state, capacity)
    assert len(positions) == len(set(positions))
    assert all(0 <= x < state.board_size and 0 <= y < state.board_size for x, y in positions)
    assert all(not state.tile_at(position).is_locked for position in positions)


@pytest.mark.parametrize("capacity", SUPPORTED_CAPACITIES)
def test_v3_produces_structurally_valid_actions(initial_observation, capacity) -> None:
    assert_valid_action(make_agent(capacity)(initial_observation))


def test_v3_reuses_frozen_v2_crop_scoring() -> None:
    assert v3_score_all_crops is v2_score_all_crops


@pytest.mark.parametrize("capacity", (8, 10, 12))
def test_v3_full_episode_completes(capacity) -> None:
    env = make("kaggriculture", configuration={"seed": 30 + capacity}, debug=True)
    env.run([make_agent(capacity), "starter"])
    assert len(env.steps) == 720
    assert env.state[0].status == "DONE"
    assert env.state[0].reward is not None
