"""Fixed-seed V3 capacity sweep and final V3-versus-V2 evaluation."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from kaggle_environments import make  # noqa: E402

from agent_v3 import crops  # noqa: E402
from agent_v3.state import GameState  # noqa: E402
from agent_v3.strategy import SUPPORTED_CAPACITIES, select_managed_tiles  # noqa: E402
from main_v2 import agent as v2_agent  # noqa: E402
from main_v3 import make_agent  # noqa: E402

RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"
FUNCTIONAL_PATH = RESULTS_DIR / "v3_functional.json"
SWEEP_PATH = RESULTS_DIR / "v3_capacity_sweep.json"
FINAL_PATH = RESULTS_DIR / "v3_vs_v2.json"
EXPERIMENTS_PATH = RESULTS_DIR / "experiments.csv"
FUNCTIONAL_SEED_START = 500_000
SWEEP_SEED_START = 600_000
FINAL_SEED_START = 700_000
PRODUCTIVE = {"DIG", "PLANT", "WATER", "HARVEST"}
MOVEMENT = {"NORTH", "SOUTH", "EAST", "WEST"}
INVENTORY = {"DROP", "PICKUP", "PLACE"}


def stats(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"mean": None, "median": None, "minimum": None, "maximum": None, "standard_deviation": None}
    return {"mean": statistics.fmean(values), "median": statistics.median(values), "minimum": min(values), "maximum": max(values), "standard_deviation": statistics.pstdev(values)}


def wilson(wins: int, games: int, z: float = 1.959963984540054) -> dict[str, float | None]:
    if not games:
        return {"lower": None, "upper": None}
    p = wins / games
    denominator = 1 + z * z / games
    center = (p + z * z / (2 * games)) / denominator
    margin = z * math.sqrt(p * (1 - p) / games + z * z / (4 * games * games)) / denominator
    return {"lower": center - margin, "upper": center + margin}


class InstrumentedAgent:
    def __init__(self, function: Callable[[Any], dict], capacity: int) -> None:
        self.function = function
        self.capacity = capacity
        self.timings: list[float] = []
        self.actions: Counter[str] = Counter()
        self.idle_by_phase: Counter[str] = Counter()
        self.indicators: Counter[str] = Counter()

    def __call__(self, observation: Any, configuration: Any = None) -> dict:
        state = GameState.from_observation(observation)
        started = time.perf_counter()
        action = self.function(observation)
        self.timings.append(time.perf_counter() - started)
        operation = action.get("farmer", ["PASS"])[0]
        self.actions[operation] += 1
        self.actions["idle" if operation == "PASS" else "non_idle"] += 1
        if operation in PRODUCTIVE:
            self.actions["productive"] += 1
        if operation in MOVEMENT:
            self.actions["movement"] += 1
        if operation in INVENTORY:
            self.actions["inventory"] += 1
        if operation == "PASS":
            self.idle_by_phase["early" if state.day < 10 else "mid" if state.day < 20 else "late"] += 1
        if state.carried_count:
            self.indicators["turns_carrying_inventory"] += 1
        for position in select_managed_tiles(state, self.capacity):
            tile = state.tile_at(position)
            if crops.is_harvestable(tile, state.day):
                self.indicators["mature_crop_wait_turns"] += 1
            if state.hour == 23 and crops.needs_water(tile):
                self.indicators["unwatered_crop_day_ends"] += 1
            if crops.is_weed(tile):
                self.indicators["weed_blocked_turns"] += 1
        return action


def run_episode(index: int, seed: int, capacity: int, candidate_position: int, opponent: Any) -> tuple[dict[str, Any], InstrumentedAgent]:
    measured = InstrumentedAgent(make_agent(capacity), capacity)
    agents = [opponent, opponent]
    agents[candidate_position] = measured
    env = make("kaggriculture", configuration={"seed": seed}, debug=True)
    error = None
    try:
        env.run(agents)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    candidate = env.state[candidate_position]
    reference = env.state[1 - candidate_position]
    completed = error is None and len(env.steps) == 720 and candidate.status == "DONE" and reference.status == "DONE"
    candidate_reward = float(candidate.reward) if candidate.reward is not None else None
    reference_reward = float(reference.reward) if reference.reward is not None else None
    if completed and candidate_reward is not None and reference_reward is not None:
        winner = "V3" if candidate_reward > reference_reward else "V2" if candidate_reward < reference_reward else "DRAW"
    else:
        winner = "INVALID"
    final_state = GameState.from_observation(candidate.observation)
    unrealized = sum(crops.is_crop(final_state.tile_at(position)) for position in select_managed_tiles(final_state, capacity))
    episode = {
        "game_index": index, "seed": seed, "capacity": capacity, "v3_position": candidate_position,
        "v3_final_reward": candidate_reward, "opponent_final_reward": reference_reward,
        "reward_difference": candidate_reward - reference_reward if candidate_reward is not None and reference_reward is not None else None,
        "winner": winner, "completed": completed, "steps": len(env.steps), "v3_status": candidate.status,
        "opponent_status": reference.status, "error": error, "actions": dict(measured.actions),
        "idle_by_phase": dict(measured.idle_by_phase), "workload_indicators": {**measured.indicators, "final_unrealized_managed_crops": unrealized, "final_unsold_inventory": final_state.carried_count + final_state.shed_count},
        "decisions": len(measured.timings), "average_decision_seconds": statistics.fmean(measured.timings) if measured.timings else 0.0,
        "median_decision_seconds": statistics.median(measured.timings) if measured.timings else 0.0,
        "maximum_decision_seconds": max(measured.timings, default=0.0),
    }
    return episode, measured


def summarize(episodes: list[dict[str, Any]], timings: list[float], label: str) -> dict[str, Any]:
    valid = [episode for episode in episodes if episode["completed"]]
    wins = sum(episode["winner"] == "V3" for episode in valid)
    losses = sum(episode["winner"] == "V2" for episode in valid)
    draws = len(valid) - wins - losses
    action_keys = ("idle", "movement", "productive", "WATER", "HARVEST", "PLANT", "inventory")
    indicator_keys = ("mature_crop_wait_turns", "unwatered_crop_day_ends", "turns_carrying_inventory", "weed_blocked_turns", "final_unrealized_managed_crops", "final_unsold_inventory")
    by_position = {}
    for position in (0, 1):
        subset = [episode for episode in valid if episode["v3_position"] == position]
        position_wins = sum(episode["winner"] == "V3" for episode in subset)
        position_losses = sum(episode["winner"] == "V2" for episode in subset)
        by_position[str(position)] = {"games": len(subset), "wins": position_wins, "losses": position_losses, "draws": len(subset) - position_wins - position_losses, "raw_win_rate": position_wins / len(subset) if subset else 0.0, "decisive_win_rate": position_wins / (position_wins + position_losses) if position_wins + position_losses else 0.0}
    crashes = sum(episode["v3_status"] == "ERROR" or episode["opponent_status"] == "ERROR" for episode in episodes)
    timeouts = sum(episode["v3_status"] == "TIMEOUT" or episode["opponent_status"] == "TIMEOUT" for episode in episodes)
    return {
        "metadata": {"label": label, "environment": "kaggriculture", "python": sys.version.split()[0], "episode_steps": 720, "balanced_positions": True, "matched_seed_pairs": True, "v2_frozen": True},
        "summary": {"games": len(episodes), "completed_games": len(valid), "v3_wins": wins, "v2_wins": losses, "draws": draws, "raw_v3_win_rate": wins / len(valid) if valid else 0.0, "decisive_v3_win_rate": wins / (wins + losses) if wins + losses else 0.0},
        "position_results": by_position,
        "confidence_interval": {"method": "Wilson 95%, decisive games only", **wilson(wins, wins + losses)},
        "reward_statistics": {"v3": stats([episode["v3_final_reward"] for episode in valid]), "v2": stats([episode["opponent_final_reward"] for episode in valid]), "difference_v3_minus_v2": stats([episode["reward_difference"] for episode in valid])},
        "actions_per_episode": {key: stats([float(episode["actions"].get(key, 0)) for episode in valid]) for key in action_keys},
        "idle_by_phase_per_episode": {key: stats([float(episode["idle_by_phase"].get(key, 0)) for episode in valid]) for key in ("early", "mid", "late")},
        "workload_indicators_per_episode": {key: stats([float(episode["workload_indicators"].get(key, 0)) for episode in valid]) for key in indicator_keys},
        "reliability": {"episodes_attempted": len(episodes), "episodes_completed": len(valid), "crashes": crashes, "timeouts": timeouts, "failed_episodes": len(episodes) - len(valid)},
        "timing": {**stats(timings), "decisions": len(timings), "decisions_over_100ms": sum(value > 0.1 for value in timings), "decisions_over_500ms": sum(value > 0.5 for value in timings)},
        "episodes": episodes,
    }


def run_balanced(capacity: int, games: int, seed_start: int, opponent: Any, label: str) -> dict[str, Any]:
    if games <= 0 or games % 2:
        raise ValueError("games must be a positive even number")
    episodes, timings = [], []
    for index in range(games):
        episode, measured = run_episode(index, seed_start + index // 2, capacity, index % 2, opponent)
        episodes.append(episode)
        timings.extend(measured.timings)
        if (index + 1) % 10 == 0 or index + 1 == games:
            print(f"{label}: {index + 1}/{games}", flush=True)
    return summarize(episodes, timings, label)


def save(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def run_functional() -> dict[str, Any]:
    results = {}
    for offset, capacity in enumerate(SUPPORTED_CAPACITIES):
        episode, measured = run_episode(offset, FUNCTIONAL_SEED_START + offset, capacity, 0, "starter")
        results[str(capacity)] = {**episode, "timing": stats(measured.timings)}
        print(f"functional-{capacity}: reward={episode['v3_final_reward']} idle={episode['actions'].get('idle', 0)} status={episode['v3_status']}", flush=True)
    payload = {"metadata": {"reference": "starter", "one_full_game_per_capacity": True}, "capacities": results}
    save(FUNCTIONAL_PATH, payload)
    return payload


def run_sweep() -> dict[str, Any]:
    candidates = {str(capacity): run_balanced(capacity, 100, SWEEP_SEED_START, v2_agent, f"V3-{capacity}-vs-V2") for capacity in SUPPORTED_CAPACITIES}
    payload = {"metadata": {"candidates": list(SUPPORTED_CAPACITIES), "games_per_capacity": 100, "seed_start": SWEEP_SEED_START, "same_seeds_for_every_capacity": True, "no_mid_sweep_tuning": True}, "capacities": candidates}
    save(SWEEP_PATH, payload)
    return payload


def run_sweep_candidate(capacity: int) -> dict[str, Any]:
    """Run one frozen candidate, checkpointing so long sweeps survive tool windows."""
    if SWEEP_PATH.exists():
        payload = json.loads(SWEEP_PATH.read_text(encoding="utf-8"))
    else:
        payload = {"metadata": {"candidates": list(SUPPORTED_CAPACITIES), "games_per_capacity": 100, "seed_start": SWEEP_SEED_START, "same_seeds_for_every_capacity": True, "no_mid_sweep_tuning": True}, "capacities": {}}
    payload["capacities"][str(capacity)] = run_balanced(capacity, 100, SWEEP_SEED_START, v2_agent, f"V3-{capacity}-vs-V2")
    save(SWEEP_PATH, payload)
    return payload


def run_final(capacity: int) -> dict[str, Any]:
    report = run_balanced(capacity, 500, FINAL_SEED_START, v2_agent, f"V3-{capacity}-vs-V2-final")
    report["metadata"]["selected_capacity"] = capacity
    save(FINAL_PATH, report)
    return report


def run_final_part(capacity: int, start: int, games: int) -> dict[str, Any]:
    if start < 0 or games <= 0 or games % 2 or start + games > 500:
        raise ValueError("final part requires an even positive game count within 0..500")
    episodes, timings = [], []
    for index in range(start, start + games):
        episode, measured = run_episode(index, FINAL_SEED_START + index // 2, capacity, index % 2, v2_agent)
        episodes.append(episode)
        timings.extend(measured.timings)
        if (index - start + 1) % 10 == 0:
            print(f"final-{capacity}: {index - start + 1}/{games} (global {index + 1}/500)", flush=True)
    part = {"episodes": episodes, "timings": timings}
    save(RESULTS_DIR / f"v3_vs_v2_part_{start:03d}.json", part)
    return part


def merge_final_parts(capacity: int) -> dict[str, Any]:
    episodes, timings = [], []
    for start in range(0, 500, 100):
        part = json.loads((RESULTS_DIR / f"v3_vs_v2_part_{start:03d}.json").read_text(encoding="utf-8"))
        episodes.extend(part["episodes"])
        timings.extend(part["timings"])
    episodes.sort(key=lambda episode: episode["game_index"])
    if len(episodes) != 500 or [episode["game_index"] for episode in episodes] != list(range(500)):
        raise ValueError("final part set is incomplete or duplicated")
    report = summarize(episodes, timings, f"V3-{capacity}-vs-V2-final")
    report["metadata"]["selected_capacity"] = capacity
    report["metadata"]["checkpointed_parts"] = 5
    save(FINAL_PATH, report)
    return report


def repair_sweep_movement() -> None:
    payload = json.loads(SWEEP_PATH.read_text(encoding="utf-8"))
    for report in payload["capacities"].values():
        values = [float(sum(episode["actions"].get(direction, 0) for direction in MOVEMENT)) for episode in report["episodes"] if episode["completed"]]
        report["actions_per_episode"]["movement"] = stats(values)
    save(SWEEP_PATH, payload)


def update_experiments(capacity: int, report: dict[str, Any], promoted: bool) -> None:
    rows = list(csv.DictReader(EXPERIMENTS_PATH.open(newline="", encoding="utf-8")))
    rows = [row for row in rows if row.get("version") != "V3"]
    summary, rewards, ci = report["summary"], report["reward_statistics"], report["confidence_interval"]
    rows.append({"version": "V3", "change": f"Managed farm capacity experiment; selected {capacity} plots", "champion": "V2", "games_vs_champion": summary["games"], "wins": summary["v3_wins"], "losses": summary["v2_wins"], "draws": summary["draws"], "win_rate": summary["raw_v3_win_rate"], "decisive_win_rate": summary["decisive_v3_win_rate"], "ci_lower": ci["lower"], "ci_upper": ci["upper"], "avg_reward": rewards["v3"]["mean"], "avg_champion_reward": rewards["v2"]["mean"], "avg_reward_difference": rewards["difference_v3_minus_v2"]["mean"], "status": "V3 QUALIFIES FOR PROMOTION" if promoted else "V2 REMAINS CHAMPION", "notes": f"Best capacity from fixed 100-game sweep: {capacity}."})
    with EXPERIMENTS_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("functional", "sweep", "sweep-one", "repair-sweep", "final", "final-part", "merge-final"))
    parser.add_argument("--capacity", type=int, choices=SUPPORTED_CAPACITIES)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--games", type=int, default=100)
    args = parser.parse_args()
    if args.mode == "functional":
        run_functional()
    elif args.mode == "sweep":
        run_sweep()
    elif args.mode == "sweep-one":
        if args.capacity is None:
            parser.error("sweep-one mode requires --capacity")
        run_sweep_candidate(args.capacity)
    elif args.mode == "repair-sweep":
        repair_sweep_movement()
    elif args.mode == "final-part":
        if args.capacity is None:
            parser.error("final-part mode requires --capacity")
        run_final_part(args.capacity, args.start, args.games)
    elif args.mode == "merge-final":
        if args.capacity is None:
            parser.error("merge-final mode requires --capacity")
        merge_final_parts(args.capacity)
    elif args.capacity is None:
        parser.error("final mode requires --capacity")
    else:
        run_final(args.capacity)


if __name__ == "__main__":
    main()
