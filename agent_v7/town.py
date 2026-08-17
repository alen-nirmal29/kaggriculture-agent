"""Verified public-town demand calculations for Kaggriculture 1.32.7."""
from __future__ import annotations
from collections import Counter
from typing import Iterable
SHOPS={
 "BAKERY":("EGG","WHEAT"),"PIZZA_SHOP":("MILK","TOMATO","WHEAT"),
 "BRUNCH_SPOT":("EGG","WHEAT","STRAWBERRY"),"YARN_STORE":("WOOL",),
 "ICE_CREAM_SHOP":("STRAWBERRY","MILK","WHEAT"),"PET_CAFE":("CARROT",),
 "SMOOTHIE_SHOP":("STRAWBERRY","MILK"),"FARMERS_MARKET":("WHEAT","CARROT","TOMATO","STRAWBERRY"),
}
PRODUCTS=("WHEAT","CARROT","TOMATO","STRAWBERRY","MELON","EGG","MILK","WOOL")

def turns_until_next_demand(step:int, interval:int=4)->int:
    return 0 if step%interval==0 else interval-step%interval

def expected_consumption(shops:Iterable[str], product:str, step:int, horizon:int,
                         shop_interval:int=4, center_interval:int=24)->int:
    if horizon<0:return 0
    events=sum(1 for t in range(step,step+horizon+1) if t%shop_interval==0)
    per=0
    for name in shops:
        goods=SHOPS.get(name,())
        if product in goods: per += 2 if len(goods)==1 else 1
    center=sum(1 for t in range(step,step+horizon+1) if t%center_interval==0) if product in PRODUCTS else 0
    return events*per+center

def expected_town_demand(shops:Iterable[str],step:int,horizon:int)->dict[str,int]:
    return {p:expected_consumption(shops,p,step,horizon) for p in PRODUCTS}

def demand_pressure(shops:Iterable[str],product:str,step:int,horizon:int,inventory:int)->float:
    return expected_consumption(shops,product,step,horizon)/max(1.0,float(inventory))

def demand_per_shop_event(shops:Iterable[str])->Counter:
    result=Counter()
    for name in shops:
        goods=SHOPS.get(name,()); mult=2 if len(goods)==1 else 1
        result.update({p:mult for p in goods})
    return result
