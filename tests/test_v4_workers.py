"""V4 official mechanics, scheduling, configuration, and reliability tests."""

import copy

from kaggle_environments import make
import pytest

from agent_v4.state import GameState
from agent_v4.strategy import SUPPORTED_CAPACITIES, SUPPORTED_HAND_LIMITS, select_managed_tiles
from agent_v4.workers import WorkTask, assign_tasks, hire_cost, hiring_orders
from main_v3 import agent as v3_agent
from main_v4 import make_agent


def observation_with_hands(initial_observation, positions=((4, 4),), inventories=({}, {}), hires_today=1):
    observation = copy.deepcopy(initial_observation)
    farm = observation["farms"][observation["player"]]
    farm["hands"] = [list(position) for position in positions]
    farm["hires_today"] = hires_today
    observation["private"]["inventories"] = [dict(inventory) for inventory in inventories]
    return observation


def test_worker_observation_parsing(initial_observation) -> None:
    state = GameState.from_observation(observation_with_hands(initial_observation, ((4, 4), (3, 4)), ({}, {"MELON": 6}, {}), 2))
    assert len(state.hands) == 2
    assert state.hands[0].index == 0
    assert state.hands[0].position == (4, 4)
    assert state.hands[0].carried_count == 6
    assert state.hires_today == 2


def test_hire_cost_matches_official_fibonacci_sequence() -> None:
    assert [hire_cost(index) for index in range(7)] == [1, 1, 2, 3, 5, 8, 13]
    assert hire_cost(3, multiplier=4) == 12


@pytest.mark.parametrize("maximum", SUPPORTED_HAND_LIMITS)
def test_each_hand_limit_and_hire_format(initial_observation, maximum) -> None:
    state = GameState.from_observation(initial_observation)
    orders = hiring_orders(state, maximum, estimated_work=20)
    assert len(orders) <= maximum
    assert all(order == ["HIRE"] for order in orders)
    action = make_agent(maximum)(initial_observation)
    assert set(action) == {"farmer", "hands", "market"}
    assert isinstance(action["hands"], list)


def test_zero_hands_is_exact_v3_control(initial_observation) -> None:
    assert make_agent(0, 12)(initial_observation) == v3_agent(initial_observation)


def test_hiring_never_exceeds_remaining_slots(initial_observation) -> None:
    state = GameState.from_observation(observation_with_hands(initial_observation, ((4, 4), (3, 4)), ({}, {}, {}), 2))
    assert len(hiring_orders(state, 3, estimated_work=20)) <= 1


def test_target_reservation_prevents_duplicate_assignment(initial_observation) -> None:
    state = GameState.from_observation(observation_with_hands(initial_observation, ((3, 4),), ({}, {})))
    assignments = assign_tasks(state, [WorkTask("WATER", (2, 4), 90), WorkTask("HARVEST", (2, 4), 100)])
    targets = [task.target for task in assignments.values() if task]
    assert len(targets) == len(set(targets)) == 1
    assert next(task for task in assignments.values() if task).kind == "HARVEST"


def test_nearby_worker_gets_high_priority_task(initial_observation) -> None:
    state = GameState.from_observation(observation_with_hands(initial_observation, ((1, 1),), ({}, {})))
    assignments = assign_tasks(state, [WorkTask("HARVEST", (1, 2), 100)])
    assert assignments[1].target == (1, 2)
    assert assignments[0] is None


def test_plant_seed_budget_prevents_atomic_overrequest(initial_observation) -> None:
    observation = observation_with_hands(initial_observation, ((3, 4),), ({}, {}))
    observation["private"]["seeds"]["MELON"] = 1
    state = GameState.from_observation(observation)
    assignments = assign_tasks(state, [WorkTask("PLANT", (1, 1), 70, crop="MELON"), WorkTask("PLANT", (2, 1), 70, crop="MELON")])
    assert sum(task is not None and task.kind == "PLANT" for task in assignments.values()) == 1


def test_hiring_stops_near_endgame(initial_observation) -> None:
    observation = copy.deepcopy(initial_observation)
    observation["step"], observation["day"], observation["hour"] = 719, 29, 23
    assert hiring_orders(GameState.from_observation(observation), 4, estimated_work=20) == []


def test_day_boundary_reset_is_parsed(initial_observation) -> None:
    before = GameState.from_observation(observation_with_hands(initial_observation, ((4, 4),), ({}, {"MELON": 6}), 1))
    reset = copy.deepcopy(initial_observation)
    reset["day"], reset["hour"] = 1, 0
    reset["farms"][reset["player"]]["hands"] = []
    reset["farms"][reset["player"]]["hires_today"] = 0
    reset["private"]["inventories"] = [{}]
    after = GameState.from_observation(reset)
    assert len(before.hands) == 1 and before.hires_today == 1
    assert after.hands == () and after.hires_today == 0


def test_worker_action_schema_with_existing_hand(initial_observation) -> None:
    observation = observation_with_hands(initial_observation, ((4, 4),), ({}, {}))
    action = make_agent(1)(observation)
    assert len(action["hands"]) == 1
    assert isinstance(action["hands"][0], list) and action["hands"][0]


@pytest.mark.parametrize("capacity", SUPPORTED_CAPACITIES)
def test_worker_supported_capacity_uses_only_unique_unlocked_tiles(initial_observation, capacity) -> None:
    state = GameState.from_observation(initial_observation)
    positions = select_managed_tiles(state, capacity)
    assert len(positions) == capacity == len(set(positions))
    assert all(not state.tile_at(position).is_locked for position in positions)


def test_v4_full_episode_completes() -> None:
    env = make("kaggriculture", configuration={"seed": 810099}, debug=True)
    env.run([make_agent(4), "starter"])
    assert len(env.steps) == 720
    assert env.state[0].status == "DONE"
    assert env.state[0].reward is not None
