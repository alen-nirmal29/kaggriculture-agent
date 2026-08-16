"""Run, profile, and diagnose one V2 match against a built-in agent."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from kaggle_environments import make  # noqa: E402

from agent_v2 import crops  # noqa: E402
from agent_v2.state import GameState  # noqa: E402
from agent_v2.strategy import build_crop_plan  # noqa: E402
from main_v2 import agent as v2_agent  # noqa: E402


class DiagnosedAgent:
    def __init__(self) -> None:
        self.timings: list[float] = []
        self.planted: Counter[str] = Counter()
        self.harvested: Counter[str] = Counter()
        self.preferred_by_phase: dict[str, Counter[str]] = defaultdict(Counter)
        self.pass_turns = 0

    def __call__(self, observation: Any, configuration: Any = None) -> dict:
        started = time.perf_counter()
        action = v2_agent(observation)
        self.timings.append(time.perf_counter() - started)
        state = GameState.from_observation(observation)
        phase = "early" if state.day < 10 else "mid" if state.day < 20 else "late"
        preferred = build_crop_plan(state).preferred
        if preferred:
            self.preferred_by_phase[phase][preferred] += 1
        farmer_action = action.get("farmer", ["PASS"])
        op = farmer_action[0] if farmer_action else "PASS"
        if op == "PLANT" and len(farmer_action) > 1:
            self.planted[str(farmer_action[1])] += 1
        elif op == "HARVEST":
            crop = crops.crop_type(state.tile_at(state.farmer))
            if crop:
                self.harvested[crop] += 1
        elif op == "PASS":
            self.pass_turns += 1
        return action

    def diagnostics(self, final_state: GameState) -> dict[str, Any]:
        phase_modes = {phase: counts.most_common(1)[0][0] if counts else None for phase, counts in self.preferred_by_phase.items()}
        return {
            "plants_by_crop": {crop: self.planted.get(crop, 0) for crop in crops.CROP_NAMES},
            "harvest_actions_by_crop": {crop: self.harvested.get(crop, 0) for crop in crops.CROP_NAMES},
            "preferred_crop_by_phase": phase_modes,
            "pass_turns": self.pass_turns,
            "final_unsold_shed_items": final_state.shed_count,
            "final_carried_items": final_state.carried_count,
        }


def run_v2_match(opponent: str = "starter", our_position: int = 0, seed: int = 0, replay_path: Path | None = None) -> dict[str, Any]:
    env = make("kaggriculture", configuration={"seed": seed}, debug=True)
    diagnosed = DiagnosedAgent()
    agents: list[Any] = [opponent, opponent]
    agents[our_position] = diagnosed
    error = None
    try:
        env.run(agents)
    except Exception as exc:  # evaluation boundary; report failures instead of losing them
        error = f"{type(exc).__name__}: {exc}"
    ours = env.state[our_position]
    theirs = env.state[1 - our_position]
    final_state = GameState.from_observation(ours.observation)
    if replay_path is not None:
        replay_path.parent.mkdir(parents=True, exist_ok=True)
        replay_path.write_text(json.dumps(env.toJSON()), encoding="utf-8")
    our_reward = float(ours.reward) if ours.reward is not None else None
    opponent_reward = float(theirs.reward) if theirs.reward is not None else None
    return {
        "opponent": opponent,
        "our_position": our_position,
        "seed": seed,
        "completed": error is None and ours.status == "DONE" and theirs.status == "DONE",
        "our_status": ours.status,
        "opponent_status": theirs.status,
        "our_reward": our_reward,
        "opponent_reward": opponent_reward,
        "winner": "v2" if our_reward is not None and opponent_reward is not None and our_reward > opponent_reward else opponent if our_reward is not None and opponent_reward is not None and our_reward < opponent_reward else "draw",
        "steps_completed": len(env.steps),
        "error": error,
        "decision_count": len(diagnosed.timings),
        "average_decision_seconds": sum(diagnosed.timings) / len(diagnosed.timings) if diagnosed.timings else 0.0,
        "maximum_decision_seconds": max(diagnosed.timings, default=0.0),
        "diagnostics": diagnosed.diagnostics(final_state),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opponent", choices=("pass", "random", "starter"), default="starter")
    parser.add_argument("--position", type=int, choices=(0, 1), default=0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--replay", type=Path)
    args = parser.parse_args()
    print(json.dumps(run_v2_match(args.opponent, args.position, args.seed, args.replay), indent=2))


if __name__ == "__main__":
    main()
