"""Kaggle-compatible entry point for the independent V2 agent."""

from agent_v2.state import GameState
from agent_v2.strategy import SAFE_ACTION, decide


def agent(obs):
    try:
        state = GameState.from_observation(obs)
    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
        return SAFE_ACTION.copy()
    return decide(state)
