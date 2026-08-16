"""Routing tests."""

from agent.routing import manhattan_distance, nearest_shed_access, next_move


def test_route_is_deterministic_and_bounded() -> None:
    assert next_move((4, 4), (1, 3)) == "WEST"
    assert next_move((1, 3), (1, 3)) == "PASS"
    assert next_move((0, 0), (-1, 0)) == "PASS"
    assert manhattan_distance((4, 4), (1, 3)) == 4
    assert nearest_shed_access((0, 0)) == (4, 4)
