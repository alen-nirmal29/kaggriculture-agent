"""V1 strategy and entry-point tests."""

from kaggle_environments import make

from agent.state import GameState
from agent.strategy import PRIMARY_CROP, decide
from main import agent
from evaluation.run_match import run_match


def assert_valid_action(action) -> None:
    assert set(action) == {"farmer", "hands", "market"}
    assert isinstance(action["farmer"], list) and action["farmer"]
    assert isinstance(action["hands"], list)
    assert isinstance(action["market"], list)


def test_strategy_returns_structurally_valid_action(initial_observation) -> None:
    action = decide(GameState.from_observation(initial_observation))

    assert_valid_action(action)
    assert PRIMARY_CROP == "CARROT"
    assert action["market"] == [["BUY_SEED", "CARROT", 6]]


def test_main_agent_handles_real_initial_observation(initial_observation) -> None:
    assert_valid_action(agent(initial_observation))


def test_short_environment_interaction_succeeds() -> None:
    env = make("kaggriculture", configuration={"episodeSteps": 12, "seed": 3}, debug=True)
    env.run([agent, "pass"])

    assert len(env.steps) == 12
    assert all(state.status == "DONE" for state in env.state)


def test_full_v1_episode_completes() -> None:
    env = make("kaggriculture", configuration={"seed": 7}, debug=True)
    env.run([agent, "starter"])

    assert len(env.steps) == 720
    assert env.state[0].status == "DONE"
    assert env.state[0].reward is not None


def test_profiled_match_runner_completes() -> None:
    result = run_match("pass", our_position=1, seed=5)

    assert result["completed"]
    assert result["steps_completed"] == 720
    assert result["decision_count"] > 700
    assert result["error"] is None
