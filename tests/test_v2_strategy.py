"""V2 strategy, interface, and reliability tests."""

import copy

from kaggle_environments import make

from agent_v2.state import GameState
from agent_v2.strategy import PLOT_LIMIT, Task, build_crop_plan, choose_task, decide
from main_v2 import agent


def assert_valid_action(action) -> None:
    assert set(action) == {"farmer", "hands", "market"}
    assert isinstance(action["farmer"], list) and action["farmer"]
    assert isinstance(action["hands"], list)
    assert isinstance(action["market"], list)


def test_v2_never_allocates_over_plot_limit(initial_observation) -> None:
    plan = build_crop_plan(GameState.from_observation(initial_observation))
    assert sum(plan.allocation.values()) <= PLOT_LIMIT
    assert len(plan.targets) <= PLOT_LIMIT


def test_v2_handles_real_initial_observation(initial_observation) -> None:
    action = agent(initial_observation)
    assert_valid_action(action)
    assert any(order[0] == "BUY_SEED" for order in action["market"])


def test_v2_preferred_seed_unaffordable_is_safe(initial_observation) -> None:
    observation = copy.deepcopy(initial_observation)
    observation["farms"][0]["money"] = 0
    action = decide(GameState.from_observation(observation))
    assert_valid_action(action)
    assert not any(order[0] == "BUY_SEED" for order in action["market"])


def test_v2_rejects_too_late_planting(initial_observation) -> None:
    observation = copy.deepcopy(initial_observation)
    observation["step"] = 719
    observation["day"] = 29
    observation["hour"] = 23
    action = decide(GameState.from_observation(observation))
    assert action["farmer"] == ["PASS"]
    assert not any(order[0] == "BUY_SEED" for order in action["market"])


def test_v2_finishes_current_tile_before_cross_plot_work(initial_observation) -> None:
    state = GameState.from_observation(initial_observation)
    tasks = [Task("HARVEST", (3, 4), 100), Task("PLANT", state.farmer, 70, "MELON")]
    assert choose_task(state, tasks).target == state.farmer


def test_v2_full_episode_completes() -> None:
    env = make("kaggriculture", configuration={"seed": 17}, debug=True)
    env.run([agent, "starter"])
    assert len(env.steps) == 720
    assert env.state[0].status == "DONE"
    assert env.state[0].reward is not None
