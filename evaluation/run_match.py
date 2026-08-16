"""Run and report one V1 Kaggriculture match."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from kaggle_environments import make  # noqa: E402

from main import agent as v1_agent  # noqa: E402


class TimedAgent:
    def __init__(self, function: Callable[[Any], dict]) -> None:
        self.function = function
        self.timings: list[float] = []

    def __call__(self, observation: Any, configuration: Any = None) -> dict:
        started = time.perf_counter()
        action = self.function(observation)
        self.timings.append(time.perf_counter() - started)
        return action


def run_match(
    opponent: str = "starter",
    our_position: int = 0,
    seed: int | None = None,
    replay_path: Path | None = None,
) -> dict[str, Any]:
    if our_position not in (0, 1):
        raise ValueError("our_position must be 0 or 1")
    configuration = {"seed": seed} if seed is not None else None
    env = make("kaggriculture", configuration=configuration, debug=True)
    timed = TimedAgent(v1_agent)
    agents: list[Any] = [opponent, opponent]
    agents[our_position] = timed
    error: str | None = None
    try:
        env.run(agents)
    except Exception as exc:  # runner boundary: preserve the episode error in its report
        error = f"{type(exc).__name__}: {exc}"

    states = list(env.state)
    ours = states[our_position]
    theirs = states[1 - our_position]
    our_reward = float(ours.reward) if ours.reward is not None else None
    opponent_reward = float(theirs.reward) if theirs.reward is not None else None
    if our_reward is None or opponent_reward is None:
        winner = "unknown"
    elif our_reward > opponent_reward:
        winner = "v1"
    elif our_reward < opponent_reward:
        winner = opponent
    else:
        winner = "draw"

    if replay_path is not None:
        replay_path.parent.mkdir(parents=True, exist_ok=True)
        replay_path.write_text(json.dumps(env.toJSON()), encoding="utf-8")

    completed = error is None and all(state.status == "DONE" for state in states)
    return {
        "opponent": opponent,
        "our_position": our_position,
        "seed": seed,
        "completed": completed,
        "our_status": ours.status,
        "opponent_status": theirs.status,
        "our_reward": our_reward,
        "opponent_reward": opponent_reward,
        "winner": winner,
        "steps_completed": len(env.steps),
        "error": error,
        "decision_count": len(timed.timings),
        "average_decision_seconds": sum(timed.timings) / len(timed.timings) if timed.timings else 0.0,
        "maximum_decision_seconds": max(timed.timings, default=0.0),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opponent", choices=("pass", "random", "starter"), default="starter")
    parser.add_argument("--position", type=int, choices=(0, 1), default=0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--replay", type=Path)
    args = parser.parse_args()
    print(json.dumps(run_match(args.opponent, args.position, args.seed, args.replay), indent=2))


if __name__ == "__main__":
    main()
