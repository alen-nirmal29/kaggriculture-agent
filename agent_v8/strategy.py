"""Opponent-aware crop-price tie breaking layered on frozen V6 behavior."""
from __future__ import annotations
from dataclasses import replace
from agent_v6.strategy import SAFE_ACTION,decide as v6_decide
from agent_v8.opponent import Mode,OpponentHistory,adjusted_prices,parse_snapshot
from agent_v8.state import GameState

def decide(state:GameState,history:OpponentHistory,mode:Mode='CONTROL',strength:float=.10,horizon_days:int=4):
 snapshot=parse_snapshot(state,mode);history.update(snapshot)
 chosen=state if mode=='CONTROL' else replace(state,market_prices=adjusted_prices(state,history,mode,strength,horizon_days))
 action=v6_decide(chosen,4,24,mode='COW_ONLY',caps={'GOOSE':0,'COW':1,'SHEEP':0},fertilizer_enabled=True)
 action['market']=[o for o in action['market'] if o and o[0]!='BUY_LAND']
 return action
