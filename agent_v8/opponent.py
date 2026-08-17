"""Compact reset-safe model of legally observable opponent production."""
from __future__ import annotations
from collections import Counter,deque
from dataclasses import dataclass,field
from typing import Literal,Mapping
from agent_v8.state import GameState,OpponentFarm
Mode=Literal['CONTROL','STATIC_SNAPSHOT','PIPELINE','FULL_OPPONENT']
CROP_DATA={'WHEAT':(2,6),'CARROT':(2,4),'TOMATO':(8,4),'STRAWBERRY':(10,4),'MELON':(10,6)}
ANIMAL_PRODUCT={'GOOSE':'EGG','COW':'MILK','SHEEP':'WOOL'}

@dataclass(frozen=True)
class OpponentSnapshot:
 step:int;crops:Mapping[str,int];mature:Mapping[str,int];pipeline:Mapping[str,float]
 structures:Mapping[str,int];animals:Mapping[str,int];workers:int;active_tiles:int;land:int

def parse_snapshot(state:GameState,mode:Mode='FULL_OPPONENT')->OpponentSnapshot:
 crops=Counter();mature=Counter();pipeline=Counter();structures=Counter();animals=Counter();active=0
 for row in state.opponent.tiles:
  for raw in row:
   if not isinstance(raw,Mapping):continue
   kind=raw.get('kind');active+=kind not in (None,'WEED')
   if kind=='PLANT':
    crop=str(raw.get('crop'));crops[crop]+=1;age=max(0,state.day-int(raw.get('planted_day',state.day)));first,maxyield=CROP_DATA.get(crop,(30,1))
    near=max(0.0,min(1.0,(age+2)/max(1,first)));pipeline[crop]+=near*max(1,int(raw.get('yield_units',1)))*.6
    mature[crop]+=int(age>=first and int(raw.get('yield_units',0))>0)
   elif kind in ('COOP','PASTURE'):
    structures[str(kind)]+=1
    if raw.get('animal'):animals[str(raw['animal'])]+=1
 if mode=='STATIC_SNAPSHOT':pipeline=Counter({c:float(n) for c,n in crops.items()})
 return OpponentSnapshot(state.step,dict(crops),dict(mature),dict(pipeline),dict(structures),dict(animals),
                         1+len(state.opponent.hands),int(active),len(state.opponent.unlocked_quadrants))

@dataclass
class OpponentHistory:
 window:int=12;points:deque=field(default_factory=deque);resets:int=0
 def update(self,snapshot:OpponentSnapshot):
  if self.points and snapshot.step<=self.points[-1].step:self.points.clear();self.resets+=1
  self.points.append(snapshot)
  while len(self.points)>self.window:self.points.popleft()
 def confidence(self)->float:
  if not self.points:return 0.0
  persistence=min(1.0,len(self.points)/6);scale=min(1.0,self.points[-1].active_tiles/12)
  return persistence*scale

def animal_pipeline(snapshot:OpponentSnapshot)->dict[str,float]:
 out=Counter()
 for animal,n in snapshot.animals.items():out[ANIMAL_PRODUCT.get(animal,animal)]+=float(n)*.5
 return dict(out)

def predicted_production(snapshot:OpponentSnapshot,mode:Mode)->dict[str,float]:
 out=Counter(snapshot.pipeline)
 if mode=='FULL_OPPONENT':out.update(animal_pipeline(snapshot))
 return dict(out)

def supply_pressure(snapshot:OpponentSnapshot,history:OpponentHistory,mode:Mode)->dict[str,float]:
 confidence=1.0 if mode=='STATIC_SNAPSHOT' else history.confidence();production=predicted_production(snapshot,mode)
 return {p:min(1.0,float(v)/12.0)*confidence for p,v in production.items()}

def adjusted_prices(state:GameState,history:OpponentHistory,mode:Mode,strength:float=.10,horizon_days:int=4)->dict[str,int]:
 if mode=='CONTROL' or state.remaining_turns<=max(48,horizon_days*24):return dict(state.market_prices)
 snapshot=parse_snapshot(state,mode);pressure=supply_pressure(snapshot,history,mode);result=dict(state.market_prices)
 for crop in CROP_DATA:
  base=int(state.market_prices.get(crop,1));result[crop]=max(1,int(round(base*(1-strength*pressure.get(crop,0.0)))))
 return result
