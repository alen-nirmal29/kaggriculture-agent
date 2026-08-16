"""Deterministic Manhattan routing within the Kaggriculture board."""

from agent.state import Position


def manhattan_distance(start: Position, target: Position) -> int:
    return abs(start[0] - target[0]) + abs(start[1] - target[1])


def next_move(start: Position, target: Position, board_size: int = 10) -> str:
    """Move x-first, then y; return PASS for identical/invalid targets."""
    sx, sy = start
    tx, ty = target
    if not (0 <= sx < board_size and 0 <= sy < board_size):
        return "PASS"
    if not (0 <= tx < board_size and 0 <= ty < board_size):
        return "PASS"
    if tx < sx:
        return "WEST"
    if tx > sx:
        return "EAST"
    if ty < sy:
        return "NORTH"
    if ty > sy:
        return "SOUTH"
    return "PASS"


def nearest_position(origin: Position, positions: list[Position]) -> Position | None:
    if not positions:
        return None
    return min(positions, key=lambda p: (manhattan_distance(origin, p), p[1], p[0]))


def shed_access_positions(board_size: int = 10) -> tuple[Position, ...]:
    half = board_size // 2
    return ((half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half))


def nearest_shed_access(origin: Position, board_size: int = 10) -> Position:
    return nearest_position(origin, list(shed_access_positions(board_size))) or origin
