"""Kaggle-compatible V5 land-ROI entry point."""

from main_v4 import agent as v4_agent
from agent_v5.state import GameState
from agent_v5.strategy import decide, validate_expansions

DEFAULT_MAX_EXPANSIONS = 0
DEFAULT_MANAGED_CAPACITY = 24


def make_agent(max_expansions: int, capacity: int = DEFAULT_MANAGED_CAPACITY):
    validated = validate_expansions(max_expansions)
    if validated == 0:
        return v4_agent
    def configured_agent(obs):
        try: return decide(GameState.from_observation(obs), validated, capacity)
        except (AttributeError, IndexError, KeyError, TypeError, ValueError):
            return {"farmer": ["PASS"], "hands": [], "market": []}
    return configured_agent


agent = make_agent(DEFAULT_MAX_EXPANSIONS)
