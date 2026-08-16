"""Kaggle-compatible entry point for the deterministic V1 agent."""

from agent.state import GameState
from agent.strategy import SAFE_ACTION, decide


def agent(obs):
    """Return one valid Kaggriculture action for the current observation."""
    try:
        state = GameState.from_observation(obs)
    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
        return SAFE_ACTION.copy()
    return decide(state)
