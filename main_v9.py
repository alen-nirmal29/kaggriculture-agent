"""Configurable packaged V9; final defaults remain frozen after validation."""
from agent_v8.opponent import OpponentHistory
from agent_v9.config import DEFAULT_CONFIG,V9Config
from agent_v9.state import GameState
from agent_v9.strategy import SAFE_ACTION,decide
def make_agent(config:V9Config=DEFAULT_CONFIG):
 history=OpponentHistory()
 def configured_agent(obs):
  try:return decide(GameState.from_observation(obs),history,config)
  except (AttributeError,IndexError,KeyError,TypeError,ValueError):return SAFE_ACTION.copy()
 configured_agent.opponent_history=history
 return configured_agent
agent=make_agent()
