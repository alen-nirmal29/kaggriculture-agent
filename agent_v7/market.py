"""Small reset-safe market history and deterministic aggregate-market signals."""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass,field
from typing import Literal
from agent_v7.state import GameState
from agent_v7.town import expected_consumption
PRODUCTS=("WHEAT","CARROT","TOMATO","STRAWBERRY","MELON","EGG","MILK","WOOL")
Mode=Literal["CONTROL","SELL_INTELLIGENCE","PRODUCTION_INTELLIGENCE","FULL_INTELLIGENCE"]

@dataclass
class MarketPoint:
    step:int; prices:dict[str,int]; inventory:dict[str,int]

@dataclass
class MarketHistory:
    window:int=12
    points:deque=field(default_factory=deque)
    resets:int=0
    def update(self,state:GameState):
        if self.points and state.step<=self.points[-1].step:
            self.points.clear();self.resets+=1
        self.points.append(MarketPoint(state.step,{p:int(state.market_prices.get(p,1)) for p in PRODUCTS},{p:int(state.market_inventory.get(p,0)) for p in PRODUCTS}))
        while len(self.points)>self.window:self.points.popleft()
    def price_trend(self,p:str)->float:
        return 0.0 if len(self.points)<2 else float(self.points[-1].prices[p]-self.points[0].prices[p])/(len(self.points)-1)
    def inventory_trend(self,p:str)->float:
        return 0.0 if len(self.points)<2 else float(self.points[-1].inventory[p]-self.points[0].inventory[p])/(len(self.points)-1)

def market_signal(state:GameState,history:MarketHistory,product:str,horizon:int=24)->float:
    demand=expected_consumption(state.town_shops,product,state.step,horizon)
    inv=max(1,int(state.market_inventory.get(product,1)));price=max(1,int(state.market_prices.get(product,1)))
    scarcity=demand/inv
    return price*(1+min(.25,scarcity*20))-history.inventory_trend(product)*.02+history.price_trend(product)*.5

def expected_future_price(state:GameState,history:MarketHistory,product:str,horizon:int=24)->float:
    current=float(state.market_prices.get(product,1));signal=market_signal(state,history,product,horizon)
    return max(1.0,current+.5*(signal-current))

def liquidity_safe(state:GameState,product:str,quantity:int)->bool:
    if state.remaining_turns<=48 or state.money<300 or state.shed_count>=90:return False
    if product=="WHEAT":
        living=sum(s.animal is not None for s in state.structures)
        if int(state.shed.get("WHEAT",0))-quantity<max(2,living*2):return False
    return True

def should_hold(state:GameState,history:MarketHistory,product:str,quantity:int,horizon:int=24,threshold=.10)->bool:
    if not liquidity_safe(state,product,quantity):return False
    now=float(state.market_prices.get(product,1));future=expected_future_price(state,history,product,horizon)
    return future>=now*(1+threshold) and expected_consumption(state.town_shops,product,state.step,horizon)>0
