"""Benchmark V1 against Kaggriculture built-in agents."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.run_match import run_match  # noqa: E402

DEFAULT_GAMES = {"pass": 10, "random": 20, "starter": 50}
RESULT_PATH = PROJECT_ROOT / "evaluation" / "results" / "v1_benchmark.json"


def summarize(opponent: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [r for r in results if r["completed"] and r["our_reward"] is not None and r["opponent_reward"] is not None]
    our_rewards = [r["our_reward"] for r in valid]
    opponent_rewards = [r["opponent_reward"] for r in valid]
    wins = sum(r["our_reward"] > r["opponent_reward"] for r in valid)
    losses = sum(r["our_reward"] < r["opponent_reward"] for r in valid)
    draws = len(valid) - wins - losses
    return {
        "opponent": opponent,
        "games": len(results),
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "win_rate": wins / len(valid) if valid else 0.0,
        "average_our_final_money": statistics.fmean(our_rewards) if our_rewards else None,
        "median_our_final_money": statistics.median(our_rewards) if our_rewards else None,
        "average_opponent_final_money": statistics.fmean(opponent_rewards) if opponent_rewards else None,
        "minimum_our_final_money": min(our_rewards, default=None),
        "maximum_our_final_money": max(our_rewards, default=None),
        "crashes": sum(r["our_status"] == "ERROR" or r["error"] is not None for r in results),
        "timeouts": sum(r["our_status"] == "TIMEOUT" for r in results),
        "invalid_or_failed_episodes": sum(not r["completed"] for r in results),
        "average_decision_seconds": statistics.fmean(r["average_decision_seconds"] for r in results),
        "maximum_decision_seconds": max((r["maximum_decision_seconds"] for r in results), default=0.0),
        "positions": {"player_0": sum(r["our_position"] == 0 for r in results), "player_1": sum(r["our_position"] == 1 for r in results)},
    }


def run_benchmark(game_counts: dict[str, int]) -> dict[str, Any]:
    summaries: dict[str, Any] = {}
    all_results: dict[str, list[dict[str, Any]]] = {}
    for opponent, count in game_counts.items():
        matches = [run_match(opponent, game % 2, game) for game in range(count)]
        all_results[opponent] = matches
        summaries[opponent] = summarize(opponent, matches)
        print(json.dumps(summaries[opponent], indent=2), flush=True)
    report = {
        "environment": "kaggriculture",
        "reward_semantics": "final banked money",
        "summaries": summaries,
        "matches": all_results,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="Run two games per opponent")
    parser.add_argument("--starter-games", type=int, default=DEFAULT_GAMES["starter"])
    args = parser.parse_args()
    counts = {name: 2 for name in DEFAULT_GAMES} if args.quick else dict(DEFAULT_GAMES)
    if not args.quick:
        counts["starter"] = max(1, args.starter_games)
    run_benchmark(counts)


if __name__ == "__main__":
    main()
