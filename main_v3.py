"""Kaggle-compatible entry point and local capacity factory for V3."""

from agent_v3.state import GameState
from agent_v3.strategy import SAFE_ACTION, decide, validate_capacity

DEFAULT_MANAGED_PLOT_LIMIT = 12


def make_agent(capacity: int):
    """Create a local Kaggle agent for one frozen capacity candidate."""
    validated = validate_capacity(capacity)

    def configured_agent(obs):
        try:
            state = GameState.from_observation(obs)
        except (AttributeError, IndexError, KeyError, TypeError, ValueError):
            return SAFE_ACTION.copy()
        return decide(state, validated)

    return configured_agent


agent = make_agent(DEFAULT_MANAGED_PLOT_LIMIT)
