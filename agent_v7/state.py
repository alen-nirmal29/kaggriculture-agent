"""V7 state adds the public town shop list to frozen V6 parsing."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any,Mapping
from agent_v6.state import GameState as V6GameState,StructureState,Position

def _get(v:Any,k:str,d=None):return v.get(k,d) if isinstance(v,Mapping) else getattr(v,k,d)

@dataclass(frozen=True)
class GameState(V6GameState):
    town_shops:tuple[str,...]
    @classmethod
    def from_observation(cls,obs:Any)->"GameState":
        base=V6GameState.from_observation(obs);town=_get(obs,"town",{}) or {}
        return cls(**base.__dict__,town_shops=tuple(_get(town,"unlocked_shops",()) or ()))
