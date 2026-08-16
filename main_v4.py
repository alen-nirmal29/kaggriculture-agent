"""Kaggle-compatible V4 entry point and local worker-policy factory."""

from main_v3 import agent as v3_agent

from agent_v4.state import GameState
from agent_v4.strategy import SAFE_ACTION, decide, validate_hand_limit

DEFAULT_MAX_HANDS = 4
DEFAULT_MANAGED_PLOT_LIMIT = 24


def make_agent(max_hands: int, capacity: int = DEFAULT_MANAGED_PLOT_LIMIT):
    validated = validate_hand_limit(max_hands)
    if validated == 0 and capacity == 12:
        return v3_agent

    def configured_agent(obs):
        try:
            state = GameState.from_observation(obs)
        except (AttributeError, IndexError, KeyError, TypeError, ValueError):
            return SAFE_ACTION.copy()
        return decide(state, validated, capacity)

    return configured_agent


agent = make_agent(DEFAULT_MAX_HANDS)
