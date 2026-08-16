"""Shared fixtures backed by the real installed environment."""

import pytest
from kaggle_environments import make


@pytest.fixture
def initial_observation():
    env = make("kaggriculture", debug=True)
    env.reset(2)
    return env.state[0].observation
