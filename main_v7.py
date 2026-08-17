"""Kaggle-compatible V7 mode factory with per-episode reset-safe history."""
from agent_v7.market import MarketHistory,Mode
from agent_v7.state import GameState
from agent_v7.strategy import SAFE_ACTION,decide
DEFAULT_MODE:Mode="CONTROL";DEFAULT_HORIZON=24;DEFAULT_HOLD_THRESHOLD=.10

def make_agent(mode:Mode=DEFAULT_MODE,horizon:int=DEFAULT_HORIZON,hold_threshold:float=DEFAULT_HOLD_THRESHOLD):
    history=MarketHistory()
    def configured_agent(obs):
        try:return decide(GameState.from_observation(obs),history,mode,horizon,hold_threshold)
        except (AttributeError,IndexError,KeyError,TypeError,ValueError):return SAFE_ACTION.copy()
    configured_agent.market_history=history
    return configured_agent
agent=make_agent()
