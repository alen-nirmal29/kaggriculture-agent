"""Kaggle-compatible V8 factory with isolated opponent history."""
from agent_v8.opponent import Mode,OpponentHistory
from agent_v8.state import GameState
from agent_v8.strategy import SAFE_ACTION,decide
DEFAULT_MODE:Mode='FULL_OPPONENT';DEFAULT_STRENGTH=.10;DEFAULT_HORIZON_DAYS=4
def make_agent(mode:Mode=DEFAULT_MODE,strength:float=DEFAULT_STRENGTH,horizon_days:int=DEFAULT_HORIZON_DAYS):
 history=OpponentHistory()
 def configured_agent(obs):
  try:return decide(GameState.from_observation(obs),history,mode,strength,horizon_days)
  except (AttributeError,IndexError,KeyError,TypeError,ValueError):return SAFE_ACTION.copy()
 configured_agent.opponent_history=history
 return configured_agent
agent=make_agent()
