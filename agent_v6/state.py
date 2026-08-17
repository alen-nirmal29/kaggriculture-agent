"""V6 observation parsing for workers, structures, and livestock."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping
from agent_v4.state import GameState as V4GameState
Position = tuple[int, int]

@dataclass(frozen=True)
class StructureState:
    position: Position
    kind: str
    animal: str | None
    consecutive_unfed: int = 0
    fed_today: bool = False
    cared_today: bool = False
    yield_units: int = 0
    fertilizer_available: bool = False
    placed_day: int | None = None

@dataclass(frozen=True)
class GameState(V4GameState):
    structures: tuple[StructureState, ...]

    @classmethod
    def from_observation(cls, obs: Any) -> "GameState":
        base = V4GameState.from_observation(obs)
        found = []
        for tile in base.iter_tiles():
            raw = tile.raw
            if not isinstance(raw, Mapping) or raw.get("kind") not in ("COOP", "PASTURE"):
                continue
            found.append(StructureState(tile.position, str(raw["kind"]), raw.get("animal"),
                int(raw.get("consecutive_unfed", 0)), bool(raw.get("fed_today", False)),
                bool(raw.get("cared_today", False)), int(raw.get("yield_units", 0)),
                bool(raw.get("fertilizer_available", False)),
                int(raw["placed_day"]) if raw.get("placed_day") is not None else None))
        return cls(**base.__dict__, structures=tuple(found))

    def unit_inventory(self, index: int) -> Mapping[str, int]:
        if index == 0:
            return self.carried
        hand = index - 1
        return self.hands[hand].carried if 0 <= hand < len(self.hands) else {}
