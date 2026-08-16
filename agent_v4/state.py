"""V4 state abstraction with official farm-hand parsing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from agent_v3.state import GameState as V3GameState, Position, TileView


def _get(value: Any, key: str, default: Any = None) -> Any:
    return value.get(key, default) if isinstance(value, Mapping) else getattr(value, key, default)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


@dataclass(frozen=True)
class HandState:
    index: int
    position: Position
    carried: Mapping[str, int]

    @property
    def carried_count(self) -> int:
        return sum(int(value) for value in self.carried.values())


@dataclass(frozen=True)
class GameState(V3GameState):
    hands: tuple[HandState, ...]
    hires_today: int

    @classmethod
    def from_observation(cls, obs: Any) -> "GameState":
        base = V3GameState.from_observation(obs)
        farm = (_get(obs, "farms", ()) or ())[base.player]
        positions = _get(farm, "hands", ()) or ()
        private = _get(obs, "private", {}) or {}
        inventories = _get(private, "inventories", ()) or ()
        hands = tuple(
            HandState(index, (int(position[0]), int(position[1])), _mapping(inventories[index + 1]) if index + 1 < len(inventories) else {})
            for index, position in enumerate(positions)
        )
        return cls(**base.__dict__, hands=hands, hires_today=int(_get(farm, "hires_today", 0)))
