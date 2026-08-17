"""V8 parses only the official shared farm payload for opponent state."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any,Mapping
from agent_v6.state import GameState as V6GameState,Position,StructureState

def _get(v:Any,k:str,d=None):return v.get(k,d) if isinstance(v,Mapping) else getattr(v,k,d)

@dataclass(frozen=True)
class OpponentFarm:
    player:int;money:float;farmer:Position;hands:tuple[Position,...]
    unlocked_quadrants:tuple[str,...];hires_today:int;tiles:tuple[tuple[Any,...],...]

@dataclass(frozen=True)
class GameState(V6GameState):
    opponent:OpponentFarm
    @classmethod
    def from_observation(cls,obs:Any)->"GameState":
        base=V6GameState.from_observation(obs);farms=_get(obs,'farms',()) or ();oid=1-base.player
        if oid<0 or oid>=len(farms):raise ValueError('opponent public farm unavailable')
        f=farms[oid];farmer=_get(f,'farmer',(0,0));hands=_get(f,'hands',()) or ()
        opponent=OpponentFarm(oid,float(_get(f,'money',0)),(int(farmer[0]),int(farmer[1])),
            tuple((int(p[0]),int(p[1])) for p in hands),tuple(_get(f,'unlocked_quadrants',()) or ()),
            int(_get(f,'hires_today',0)),tuple(tuple(row) for row in (_get(f,'tiles',()) or ())))
        return cls(**base.__dict__,opponent=opponent)
