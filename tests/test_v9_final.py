from dataclasses import replace
from pathlib import Path
import hashlib
import importlib.util

import pytest
from kaggle_environments import make

from agent_v9.config import DEFAULT_CONFIG, V9Config
from agent_v9.state import GameState
from agent_v9.workers import hiring_orders_v9
from main_v8 import agent as v8_agent
from main_v9 import make_agent


def state(initial_observation):
    return GameState.from_observation(initial_observation)


def test_final_defaults():
    assert (DEFAULT_CONFIG.strength, DEFAULT_CONFIG.horizon_days) == (.075, 3)


def test_six_hand_cap():
    assert DEFAULT_CONFIG.max_hands == 6


def test_one_cow_cap():
    assert DEFAULT_CONFIG.max_cows == 1


def test_no_land_default():
    assert DEFAULT_CONFIG.buy_land is False and DEFAULT_CONFIG.managed_plots == 24


def test_fertilizer_retained():
    assert DEFAULT_CONFIG.fertilizer is True


def test_opponent_model_retained():
    assert DEFAULT_CONFIG.mode == "FULL_OPPONENT"


@pytest.mark.parametrize("cap", [0, 4, 5, 6])
def test_valid_labor_caps(initial_observation, cap):
    assert len(hiring_orders_v9(state(initial_observation), cap, 100)) <= cap


@pytest.mark.parametrize("cap", [-1, 7])
def test_invalid_labor_caps(initial_observation, cap):
    with pytest.raises(ValueError):
        hiring_orders_v9(state(initial_observation), cap, 100)


def test_hiring_respects_cash_reserve(initial_observation):
    s = replace(state(initial_observation), money=200)
    assert hiring_orders_v9(s, 6, 100) == []


def test_hiring_stops_late(initial_observation):
    s = replace(state(initial_observation), step=719)
    assert hiring_orders_v9(s, 6, 100) == []


def test_hiring_stops_at_night(initial_observation):
    s = replace(state(initial_observation), step=23, hour=23)
    assert hiring_orders_v9(s, 6, 100) == []


def test_action_schema(initial_observation):
    assert set(make_agent()(initial_observation)) == {"farmer", "hands", "market"}


def test_action_is_deterministic_for_fresh_agents(initial_observation):
    assert make_agent()(initial_observation) == make_agent()(initial_observation)


def test_no_buy_land(initial_observation):
    assert not any(x[0] == "BUY_LAND" for x in make_agent()(initial_observation)["market"])


def test_at_most_one_cow_order(initial_observation):
    orders = make_agent()(initial_observation)["market"]
    assert sum(x[:2] == ["BUY_ANIMAL", "COW"] for x in orders) <= 1


def test_no_future_version_imports():
    text = Path("main_v9.py").read_text(encoding="utf-8")
    assert "v10" not in text.lower()


def test_v8_and_v9_both_importable():
    assert callable(v8_agent) and callable(make_agent())


def test_artifacts_identical():
    a = Path("submission/main.py").read_bytes()
    b = Path("submission/final_agent.py").read_bytes()
    assert a == b and hashlib.sha256(a).digest() == hashlib.sha256(b).digest()


def test_artifact_has_agent_signature():
    p = Path("submission/main.py").resolve()
    spec = importlib.util.spec_from_file_location("v9_artifact_test", p)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.agent)


def test_full_v9_episode():
    env = make("kaggriculture", configuration={"seed": 1590000}, debug=True)
    env.run([make_agent(), v8_agent])
    assert len(env.steps) == 720 and all(x.status == "DONE" for x in env.state)
