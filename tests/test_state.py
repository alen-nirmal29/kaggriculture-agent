"""State parser tests."""

from agent.state import GameState


def test_state_parser_handles_real_initial_observation(initial_observation) -> None:
    state = GameState.from_observation(initial_observation)

    assert state.day == 0
    assert state.hour == 0
    assert state.money == 3000
    assert state.farmer == (4, 4)
    assert state.unlocked_quadrants == ("NW",)
    assert state.tile_at((0, 0)).is_empty
    assert state.tile_at((5, 0)).is_locked
    assert state.seed_count("WHEAT") == 0
    assert len(state.empty_tiles) == 25
