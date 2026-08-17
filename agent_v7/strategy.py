"""Conservative market/town adjustments layered on frozen V6 decisions."""
from __future__ import annotations
from dataclasses import replace
from agent_v6.strategy import SAFE_ACTION,decide as v6_decide
from agent_v7.market import MarketHistory,Mode,expected_future_price,should_hold
from agent_v7.state import GameState

def _production_state(state:GameState,history:MarketHistory,horizon:int)->GameState:
    adjusted=dict(state.market_prices)
    for p in ("WHEAT","CARROT","TOMATO","STRAWBERRY","MELON"):
        # Bounded forecast adjustment: V6 economics remains dominant.
        forecast=expected_future_price(state,history,p,horizon)
        adjusted[p]=int(round(.8*float(state.market_prices.get(p,1))+.2*forecast))
    return replace(state,market_prices=adjusted)

def decide(state:GameState,history:MarketHistory,mode:Mode="CONTROL",horizon:int=24,hold_threshold:float=.10):
    history.update(state)
    production=mode in ("PRODUCTION_INTELLIGENCE","FULL_INTELLIGENCE")
    selling=mode in ("SELL_INTELLIGENCE","FULL_INTELLIGENCE")
    action=v6_decide(_production_state(state,history,horizon) if production else state,4,24,
                     mode="COW_ONLY",caps={"GOOSE":0,"COW":1,"SHEEP":0},fertilizer_enabled=True)
    if selling:
        kept=[]
        for order in action["market"]:
            if order and order[0]=="SELL" and should_hold(state,history,str(order[1]),int(order[2]),horizon,hold_threshold):continue
            kept.append(order)
        action["market"]=kept
    # Experimental invariant: V7 never expands and never adds livestock.
    action["market"]=[o for o in action["market"] if o and o[0]!="BUY_LAND"]
    return action
