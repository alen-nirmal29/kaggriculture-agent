"""Read-only state abstraction for the independent V2 agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator, Mapping

Position = tuple[int, int]


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


@dataclass(frozen=True)
class TileView:
    position: Position
    raw: Any

    @property
    def is_locked(self) -> bool:
        return self.raw == "LOCKED"

    @property
    def is_empty(self) -> bool:
        return self.raw is None

    @property
    def kind(self) -> str | None:
        return _get(self.raw, "kind") if self.raw is not None else None


@dataclass(frozen=True)
class GameState:
    observation: Any
    player: int
    step: int
    day: int
    hour: int
    money: float
    farmer: Position
    tiles: tuple[tuple[Any, ...], ...]
    unlocked_quadrants: tuple[str, ...]
    carried: Mapping[str, int]
    shed: Mapping[str, int]
    seeds: Mapping[str, int]
    market_inventory: Mapping[str, int]
    market_prices: Mapping[str, int]

    @classmethod
    def from_observation(cls, obs: Any) -> "GameState":
        player = int(_get(obs, "player", 0))
        farms = _get(obs, "farms", ()) or ()
        if player < 0 or player >= len(farms):
            raise ValueError(f"Observation has no farm for player {player}")
        farm = farms[player]
        private = _get(obs, "private", {}) or {}
        inventories = _get(private, "inventories", ()) or ()
        market = _get(obs, "market", {}) or {}
        raw_tiles = _get(farm, "tiles", ()) or ()
        farmer = _get(farm, "farmer", (0, 0))
        return cls(
            observation=obs,
            player=player,
            step=int(_get(obs, "step", 0)),
            day=int(_get(obs, "day", 0)),
            hour=int(_get(obs, "hour", 0)),
            money=float(_get(farm, "money", 0.0)),
            farmer=(int(farmer[0]), int(farmer[1])),
            tiles=tuple(tuple(row) for row in raw_tiles),
            unlocked_quadrants=tuple(_get(farm, "unlocked_quadrants", ()) or ()),
            carried=_mapping(inventories[0]) if inventories else {},
            shed=_mapping(_get(private, "shed", {}) or {}),
            seeds=_mapping(_get(private, "seeds", {}) or {}),
            market_inventory=_mapping(_get(market, "inventory", {}) or {}),
            market_prices=_mapping(_get(market, "prices", {}) or {}),
        )

    @property
    def board_size(self) -> int:
        return len(self.tiles)

    @property
    def remaining_turns(self) -> int:
        return max(0, 720 - self.step)

    def tile_at(self, position: Position) -> TileView:
        x, y = position
        if not (0 <= y < len(self.tiles) and 0 <= x < len(self.tiles[y])):
            raise IndexError(f"Tile position outside board: {position}")
        return TileView(position, self.tiles[y][x])

    def iter_tiles(self) -> Iterator[TileView]:
        for y, row in enumerate(self.tiles):
            for x, raw in enumerate(row):
                yield TileView((x, y), raw)

    def seed_count(self, crop: str) -> int:
        return int(self.seeds.get(crop, 0))

    @property
    def carried_count(self) -> int:
        return sum(int(n) for n in self.carried.values())

    @property
    def shed_count(self) -> int:
        return sum(int(n) for n in self.shed.values())
