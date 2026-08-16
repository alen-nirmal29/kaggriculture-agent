"""Tests for local Kaggriculture environment availability."""

from kaggle_environments import make


def test_kaggriculture_environment_can_be_created() -> None:
    env = make("kaggriculture", debug=True)

    assert env.name == "kaggriculture"
