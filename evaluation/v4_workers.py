"""Matched-seed V4 worker-policy evaluation against frozen V3."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from kaggle_environments import make  # noqa: E402

from agent_v4 import crops  # noqa: E402
from agent_v4.state import GameState  # noqa: E402
from agent_v4.workers import hire_cost  # noqa: E402
from agent_v4.strategy import select_managed_tiles  # noqa: E402
from evaluation.v3_capacity import stats, wilson  # noqa: E402
from main_v3 import agent as v3_agent  # noqa: E402
from main_v4 import make_agent  # noqa: E402

RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"
SWEEP_PATH = RESULTS_DIR / "v4_worker_sweep.json"
CAPACITY_PATH = RESULTS_DIR / "v4_capacity_sweep.json"
FINAL_PATH = RESULTS_DIR / "v4_vs_v3.json"
EXPERIMENTS_PATH = RESULTS_DIR / "experiments.csv"
SWEEP_SEED_START = 820_000
CAPACITY_SEED_START = 830_000
FINAL_SEED_START = 840_000
MOVEMENT = {"NORTH", "SOUTH", "EAST", "WEST"}
PRODUCTIVE = {"DIG", "PLANT", "WATER", "HARVEST"}


class MeasuredV4:
    def __init__(self, max_hands: int, capacity: int = 12) -> None:
        self.function = make_agent(max_hands, capacity)
        self.max_hands = max_hands
        self.capacity = capacity
        self.timings: list[float] = []
        self.counts: Counter[str] = Counter()
        self.indicators: Counter[str] = Counter()

    def __call__(self, observation: Any, configuration: Any = None) -> dict:
        state = GameState.from_observation(observation)
        started = time.perf_counter()
        action = self.function(observation)
        self.timings.append(time.perf_counter() - started)
        farmer_op = action.get("farmer", ["PASS"])[0]
        self.counts["farmer_productive"] += farmer_op in PRODUCTIVE
        self.counts["farmer_movement"] += farmer_op in MOVEMENT
        hand_actions = action.get("hands", [])
        self.counts["worker_available_actions"] += len(state.hands)
        for hand_action in hand_actions[:len(state.hands)]:
            operation = hand_action[0] if isinstance(hand_action, list) and hand_action else "PASS"
            self.counts["worker_productive"] += operation in PRODUCTIVE
            self.counts["worker_movement"] += operation in MOVEMENT
            self.counts["worker_idle"] += operation == "PASS"
            self.counts["worker_non_idle"] += operation != "PASS"
        hire_orders = sum(order == ["HIRE"] for order in action.get("market", []))
        self.counts["hands_hired"] += hire_orders
        self.counts["hiring_cost"] += sum(hire_cost(state.hires_today + offset) for offset in range(hire_orders))
        for position in select_managed_tiles(state, self.capacity):
            tile = state.tile_at(position)
            self.indicators["mature_crop_wait_turns"] += crops.is_harvestable(tile, state.day)
            self.indicators["unwatered_crop_day_ends"] += state.hour == 23 and crops.needs_water(tile)
            self.indicators["weed_blocked_turns"] += crops.is_weed(tile)
        return action


def run_episode(index: int, seed: int, max_hands: int, v4_position: int, capacity: int = 12) -> tuple[dict[str, Any], list[float]]:
    measured = MeasuredV4(max_hands, capacity)
    agents = [v3_agent, v3_agent]
    agents[v4_position] = measured
    env = make("kaggriculture", configuration={"seed": seed}, debug=True)
    error = None
    try:
        env.run(agents)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    candidate, champion = env.state[v4_position], env.state[1 - v4_position]
    completed = error is None and len(env.steps) == 720 and candidate.status == "DONE" and champion.status == "DONE"
    v4_reward = float(candidate.reward) if candidate.reward is not None else None
    v3_reward = float(champion.reward) if champion.reward is not None else None
    winner = "INVALID"
    if completed and v4_reward is not None and v3_reward is not None:
        winner = "V4" if v4_reward > v3_reward else "V3" if v4_reward < v3_reward else "DRAW"
    final_state = GameState.from_observation(candidate.observation)
    episode = {
        "game_index": index, "seed": seed, "max_hands": max_hands, "capacity": capacity, "v4_position": v4_position,
        "v4_final_reward": v4_reward, "v3_final_reward": v3_reward,
        "reward_difference": v4_reward - v3_reward if v4_reward is not None and v3_reward is not None else None,
        "net_increment_after_hiring_cost": v4_reward - v3_reward if v4_reward is not None and v3_reward is not None else None,
        "winner": winner, "completed": completed, "steps": len(env.steps), "v4_status": candidate.status, "v3_status": champion.status, "error": error,
        "worker_metrics": dict(measured.counts), "workload_indicators": {**measured.indicators, "final_unsold_inventory": final_state.carried_count + final_state.shed_count},
    }
    return episode, measured.timings


def summarize(episodes: list[dict[str, Any]], timings: list[float], label: str) -> dict[str, Any]:
    valid = [episode for episode in episodes if episode["completed"]]
    wins = sum(episode["winner"] == "V4" for episode in valid)
    losses = sum(episode["winner"] == "V3" for episode in valid)
    draws = len(valid) - wins - losses
    by_position = {}
    for position in (0, 1):
        subset = [episode for episode in valid if episode["v4_position"] == position]
        pw = sum(episode["winner"] == "V4" for episode in subset)
        pl = sum(episode["winner"] == "V3" for episode in subset)
        by_position[str(position)] = {"games": len(subset), "wins": pw, "losses": pl, "draws": len(subset) - pw - pl, "win_rate": pw / len(subset) if subset else 0.0, "decisive_win_rate": pw / (pw + pl) if pw + pl else 0.0}
    metric_keys = ("hands_hired", "hiring_cost", "worker_productive", "worker_movement", "worker_idle", "worker_non_idle", "worker_available_actions", "farmer_productive", "farmer_movement")
    indicator_keys = ("mature_crop_wait_turns", "unwatered_crop_day_ends", "weed_blocked_turns", "final_unsold_inventory")
    metric_stats = {key: stats([float(episode["worker_metrics"].get(key, 0)) for episode in valid]) for key in metric_keys}
    available = sum(episode["worker_metrics"].get("worker_available_actions", 0) for episode in valid)
    non_idle = sum(episode["worker_metrics"].get("worker_non_idle", 0) for episode in valid)
    metric_stats["worker_utilization"] = non_idle / available if available else 0.0
    crashes = sum(episode["v4_status"] == "ERROR" or episode["v3_status"] == "ERROR" for episode in episodes)
    timeouts = sum(episode["v4_status"] == "TIMEOUT" or episode["v3_status"] == "TIMEOUT" for episode in episodes)
    return {
        "metadata": {"label": label, "environment": "kaggriculture", "python": sys.version.split()[0], "balanced_positions": True, "matched_seed_pairs": True, "v3_frozen": True},
        "summary": {"games": len(episodes), "completed_games": len(valid), "v4_wins": wins, "v3_wins": losses, "draws": draws, "raw_v4_win_rate": wins / len(valid) if valid else 0.0, "decisive_v4_win_rate": wins / (wins + losses) if wins + losses else 0.0},
        "position_results": by_position,
        "confidence_interval": {"method": "Wilson 95%, decisive games only", **wilson(wins, wins + losses)},
        "reward_statistics": {"v4": stats([episode["v4_final_reward"] for episode in valid]), "v3": stats([episode["v3_final_reward"] for episode in valid]), "difference_v4_minus_v3": stats([episode["reward_difference"] for episode in valid])},
        "worker_metrics_per_episode": metric_stats,
        "worker_metrics_per_day": {"hands_hired": metric_stats["hands_hired"]["mean"] / 30 if valid else 0.0, "hiring_cost": metric_stats["hiring_cost"]["mean"] / 30 if valid else 0.0},
        "workload_indicators_per_episode": {key: stats([float(episode["workload_indicators"].get(key, 0)) for episode in valid]) for key in indicator_keys},
        "reliability": {"episodes_attempted": len(episodes), "episodes_completed": len(valid), "crashes": crashes, "timeouts": timeouts, "other_failures": len(episodes) - len(valid) - crashes - timeouts},
        "timing": {**stats(timings), "decisions": len(timings), "decisions_over_100ms": sum(value > 0.1 for value in timings), "decisions_over_500ms": sum(value > 0.5 for value in timings)},
        "episodes": episodes,
    }


def run_block(max_hands: int, start: int, games: int, seed_start: int, capacity: int = 12, label: str = "sweep") -> dict[str, Any]:
    episodes, timings = [], []
    for index in range(start, start + games):
        episode, values = run_episode(index, seed_start + index // 2, max_hands, index % 2, capacity)
        episodes.append(episode)
        timings.extend(values)
        if (index - start + 1) % 10 == 0:
            print(f"{label}: {index - start + 1}/{games}", flush=True)
    return {"episodes": episodes, "timings": timings}


def save(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def sweep_one(max_hands: int) -> None:
    block = run_block(max_hands, 0, 100, SWEEP_SEED_START, label=f"V4-{max_hands}-vs-V3")
    report = summarize(block["episodes"], block["timings"], f"V4-{max_hands}-vs-V3")
    payload = json.loads(SWEEP_PATH.read_text(encoding="utf-8")) if SWEEP_PATH.exists() else {"metadata": {"games_per_policy": 100, "seed_start": SWEEP_SEED_START, "same_seeds": True, "capacity": 12, "no_mid_sweep_tuning": True}, "policies": {}}
    payload["policies"][str(max_hands)] = report
    save(SWEEP_PATH, payload)


def capacity_one(capacity: int) -> None:
    block = run_block(4, 0, 100, CAPACITY_SEED_START, capacity, f"V4-h4-c{capacity}-vs-V3")
    report = summarize(block["episodes"], block["timings"], f"V4-h4-c{capacity}-vs-V3")
    payload = json.loads(CAPACITY_PATH.read_text(encoding="utf-8")) if CAPACITY_PATH.exists() else {"metadata": {"games_per_capacity": 100, "seed_start": CAPACITY_SEED_START, "same_seeds": True, "max_hands": 4, "starting_unlocked_valid_tiles": 25, "no_land_purchase": True}, "capacities": {}}
    payload["capacities"][str(capacity)] = report
    save(CAPACITY_PATH, payload)


def final_part(max_hands: int, capacity: int, start: int, games: int) -> None:
    if games <= 0 or games % 2 or start < 0 or start + games > 500:
        raise ValueError("final checkpoint must be a positive even range within 0..500")
    block = run_block(max_hands, start, games, FINAL_SEED_START, capacity, f"final-{start + 1}-{start + games}")
    save(RESULTS_DIR / f"v4_vs_v3_part_{start:03d}.json", block)


def merge_final(max_hands: int, capacity: int) -> dict[str, Any]:
    episodes, timings = [], []
    for start in range(0, 500, 50):
        block = json.loads((RESULTS_DIR / f"v4_vs_v3_part_{start:03d}.json").read_text(encoding="utf-8"))
        episodes.extend(block["episodes"]); timings.extend(block["timings"])
    episodes.sort(key=lambda episode: episode["game_index"])
    if [episode["game_index"] for episode in episodes] != list(range(500)):
        raise ValueError("final checkpoints missing or duplicated")
    report = summarize(episodes, timings, f"V4-h{max_hands}-c{capacity}-vs-V3-final")
    report["metadata"].update({"max_hands": max_hands, "capacity": capacity, "checkpointed_parts": 10})
    save(FINAL_PATH, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("sweep-one", "capacity-one", "final-part", "merge-final"))
    parser.add_argument("--max-hands", type=int, required=True, choices=range(5))
    parser.add_argument("--capacity", type=int, default=12)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--games", type=int, default=50)
    args = parser.parse_args()
    if args.mode == "sweep-one": sweep_one(args.max_hands)
    elif args.mode == "capacity-one": capacity_one(args.capacity)
    elif args.mode == "final-part": final_part(args.max_hands, args.capacity, args.start, args.games)
    else: merge_final(args.max_hands, args.capacity)


if __name__ == "__main__":
    main()
