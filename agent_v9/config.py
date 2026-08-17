"""Frozen, explainable V9 candidate configuration."""
from dataclasses import dataclass
from agent_v8.opponent import Mode
@dataclass(frozen=True)
class V9Config:
 mode:Mode='FULL_OPPONENT';strength:float=.075;horizon_days:int=3;max_hands:int=6
 managed_plots:int=24;max_cows:int=1;fertilizer:bool=True;buy_land:bool=False
DEFAULT_CONFIG=V9Config()
