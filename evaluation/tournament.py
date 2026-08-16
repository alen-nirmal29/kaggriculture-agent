"""Controlled, paired-seed tournament runner for frozen V2 and V1 agents."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from kaggle_environments import make  # noqa: E402

from main import agent as v1_agent  # noqa: E402
from main_v2 import agent as v2_agent  # noqa: E402

RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"
SANITY_PATH = RESULTS_DIR / "v2_vs_v1_sanity.json"
MAIN_PATH = RESULTS_DIR / "v2_vs_v1.json"
BASELINES_PATH = RESULTS_DIR / "v2_baselines.json"
EXPERIMENTS_PATH = RESULTS_DIR / "experiments.csv"
SANITY_SEED_START = 100_000
MAIN_SEED_START = 200_000
STARTER_SEED_START = 300_000
RANDOM_SEED_START = 400_000


class TimedAgent:
    def __init__(self, function: Callable[[Any], dict]) -> None:
        self.function = function
        self.timings: list[float] = []

    def __call__(self, observation: Any, configuration: Any = None) -> dict:
        started = time.perf_counter()
        action = self.function(observation)
        self.timings.append(time.perf_counter() - started)
        return action


def run_episode(game_index: int, seed: int, v2_position: int, opponent: str | Callable[[Any], dict]) -> tuple[dict[str, Any], list[float], list[float]]:
    v2_timed = TimedAgent(v2_agent)
    opponent_function = v1_agent if opponent == "v1" else opponent
    v1_timed = TimedAgent(opponent_function) if callable(opponent_function) else None
    other_agent: Any = v1_timed if v1_timed is not None else opponent_function
    agents = [other_agent, other_agent]
    agents[v2_position] = v2_timed
    env = make("kaggriculture", configuration={"seed": seed}, debug=True)
    error = None
    try:
        env.run(agents)
    except Exception as exc:  # evaluation boundary: retain every failure
        error = f"{type(exc).__name__}: {exc}"

    v2_state = env.state[v2_position]
    other_position = 1 - v2_position
    other_state = env.state[other_position]
    v2_reward = float(v2_state.reward) if v2_state.reward is not None else None
    other_reward = float(other_state.reward) if other_state.reward is not None else None
    completed = error is None and len(env.steps) == 720 and v2_state.status == "DONE" and other_state.status == "DONE"
    if completed and v2_reward is not None and other_reward is not None:
        winner = "V2" if v2_reward > other_reward else "V1" if v2_reward < other_reward and opponent == "v1" else str(opponent) if v2_reward < other_reward else "DRAW"
    else:
        winner = "INVALID"
    episode = {
        "game_index": game_index,
        "seed": seed,
        "v2_position": v2_position,
        "v1_position": other_position if opponent == "v1" else None,
        "opponent": "V1" if opponent == "v1" else str(opponent),
        "v2_final_reward": v2_reward,
        "opponent_final_reward": other_reward,
        "v1_final_reward": other_reward if opponent == "v1" else None,
        "reward_difference": v2_reward - other_reward if v2_reward is not None and other_reward is not None else None,
        "winner": winner,
        "draw": winner == "DRAW",
        "v2_status": v2_state.status,
        "opponent_status": other_state.status,
        "v1_status": other_state.status if opponent == "v1" else None,
        "completed": completed,
        "steps": len(env.steps),
        "error": error,
        "v2_decisions": len(v2_timed.timings),
        "v2_average_decision_seconds": statistics.fmean(v2_timed.timings) if v2_timed.timings else 0.0,
        "v2_maximum_decision_seconds": max(v2_timed.timings, default=0.0),
        "opponent_decisions": len(v1_timed.timings) if v1_timed else None,
        "opponent_average_decision_seconds": statistics.fmean(v1_timed.timings) if v1_timed and v1_timed.timings else None,
        "opponent_maximum_decision_seconds": max(v1_timed.timings, default=0.0) if v1_timed else None,
    }
    return episode, v2_timed.timings, v1_timed.timings if v1_timed else []


def wilson_interval(wins: int, games: int, z: float = 1.959963984540054) -> dict[str, float | int | str | None]:
    if games <= 0:
        return {"method": "Wilson 95%", "wins": wins, "games": games, "lower": None, "upper": None}
    proportion = wins / games
    denominator = 1.0 + z * z / games
    center = (proportion + z * z / (2.0 * games)) / denominator
    margin = z * math.sqrt(proportion * (1.0 - proportion) / games + z * z / (4.0 * games * games)) / denominator
    return {"method": "Wilson 95%", "wins": wins, "games": games, "lower": center - margin, "upper": center + margin}


def numeric_statistics(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"mean": None, "median": None, "minimum": None, "maximum": None, "standard_deviation": None}
    return {"mean": statistics.fmean(values), "median": statistics.median(values), "minimum": min(values), "maximum": max(values), "standard_deviation": statistics.pstdev(values)}


def outcome_counts(episodes: list[dict[str, Any]]) -> dict[str, int | float]:
    valid = [episode for episode in episodes if episode["completed"]]
    wins = sum(episode["winner"] == "V2" for episode in valid)
    draws = sum(episode["winner"] == "DRAW" for episode in valid)
    losses = len(valid) - wins - draws
    decisive = wins + losses
    return {"games": len(episodes), "completed_games": len(valid), "v2_wins": wins, "v2_losses": losses, "draws": draws, "raw_v2_win_rate": wins / len(valid) if valid else 0.0, "decisive_v2_win_rate": wins / decisive if decisive else 0.0}


def reliability(episodes: list[dict[str, Any]]) -> dict[str, int]:
    crashes = sum(episode["v2_status"] == "ERROR" or episode["opponent_status"] == "ERROR" for episode in episodes)
    timeouts = sum(episode["v2_status"] == "TIMEOUT" or episode["opponent_status"] == "TIMEOUT" for episode in episodes)
    invalid = sum(episode["v2_status"] not in ("DONE", "ERROR", "TIMEOUT") or episode["opponent_status"] not in ("DONE", "ERROR", "TIMEOUT") for episode in episodes)
    other = sum(not episode["completed"] for episode in episodes) - crashes - timeouts - invalid
    return {"episodes_attempted": len(episodes), "episodes_completed": sum(episode["completed"] for episode in episodes), "crashes": crashes, "timeouts": timeouts, "invalid_statuses": invalid, "other_failures": max(0, other)}


def build_report(episodes: list[dict[str, Any]], v2_timings: list[float], opponent_timings: list[float], label: str) -> dict[str, Any]:
    summary = outcome_counts(episodes)
    positions = {str(position): outcome_counts([episode for episode in episodes if episode["v2_position"] == position]) for position in (0, 1)}
    valid = [episode for episode in episodes if episode["completed"]]
    decisive = int(summary["v2_wins"]) + int(summary["v2_losses"])
    timing = numeric_statistics(v2_timings)
    timing.update({"decisions": len(v2_timings), "decisions_over_100ms": sum(value > 0.100 for value in v2_timings), "decisions_over_500ms": sum(value > 0.500 for value in v2_timings), "opponent": numeric_statistics(opponent_timings)})
    return {
        "metadata": {"label": label, "environment": "kaggriculture", "python": sys.version.split()[0], "kaggle_environments": "1.32.7", "episode_steps": 720, "reward_semantics": "final banked money", "seed_pairing": "each seed is run once per V2 player position", "agents_frozen": True},
        "summary": summary,
        "position_results": positions,
        "reward_statistics": {"v2": numeric_statistics([episode["v2_final_reward"] for episode in valid]), "opponent": numeric_statistics([episode["opponent_final_reward"] for episode in valid]), "difference_v2_minus_opponent": numeric_statistics([episode["reward_difference"] for episode in valid])},
        "confidence_interval": {"sample": "decisive games only; draws excluded", **wilson_interval(int(summary["v2_wins"]), decisive)},
        "timing": timing,
        "reliability": reliability(episodes),
        "episodes": episodes,
    }


def run_balanced(games: int, seed_start: int, opponent: str | Callable[[Any], dict], label: str, progress_every: int = 10) -> dict[str, Any]:
    if games <= 0 or games % 2:
        raise ValueError("games must be a positive even number")
    episodes: list[dict[str, Any]] = []
    v2_timings: list[float] = []
    opponent_timings: list[float] = []
    for game_index in range(games):
        episode, v2_values, opponent_values = run_episode(game_index, seed_start + game_index // 2, game_index % 2, opponent)
        episodes.append(episode)
        v2_timings.extend(v2_values)
        opponent_timings.extend(opponent_values)
        if (game_index + 1) % progress_every == 0 or game_index + 1 == games:
            counts = outcome_counts(episodes)
            print(f"{label}: {game_index + 1}/{games} complete; V2 W/L/D={counts['v2_wins']}/{counts['v2_losses']}/{counts['draws']}", flush=True)
    return build_report(episodes, v2_timings, opponent_timings, label)


def save_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def promotion_decision(main_report: dict[str, Any], baselines: dict[str, Any] | None = None) -> tuple[str, str]:
    summary = main_report["summary"]
    rel = main_report["reliability"]
    ci_lower = main_report["confidence_interval"]["lower"]
    reliable = rel["episodes_completed"] == rel["episodes_attempted"] and all(rel[key] == 0 for key in ("crashes", "timeouts", "invalid_statuses", "other_failures"))
    strong = summary["decisive_v2_win_rate"] >= 0.55
    ci_clear = ci_lower is not None and ci_lower > 0.50
    baseline_ok = True if not baselines else all(report["summary"]["raw_v2_win_rate"] >= 0.90 and report["reliability"]["episodes_completed"] == report["reliability"]["episodes_attempted"] for report in baselines.values())
    if reliable and strong and ci_clear and baseline_ok:
        return "V2 QUALIFIES FOR PROMOTION", "All reliability gates passed, decisive win rate is at least 55%, Wilson lower bound exceeds 50%, and baseline regressions are clean."
    if not reliable or not strong or not baseline_ok:
        return "V1 REMAINS CHAMPION", "At least one required reliability, strength, or baseline-regression criterion was not met."
    return "INCONCLUSIVE", "Point estimate passed but statistical confidence did not clearly exceed 50%."


def write_experiments(main_report: dict[str, Any], baselines: dict[str, Any] | None = None) -> None:
    decision, reason = promotion_decision(main_report, baselines)
    summary = main_report["summary"]
    rewards = main_report["reward_statistics"]
    ci = main_report["confidence_interval"]
    fields = ["version", "change", "champion", "games_vs_champion", "wins", "losses", "draws", "win_rate", "decisive_win_rate", "ci_lower", "ci_upper", "avg_reward", "avg_champion_reward", "avg_reward_difference", "status", "notes"]
    rows = [
        {"version": "V1", "change": "Fixed six-tile carrot baseline", "champion": "V1", "games_vs_champion": 0, "wins": "", "losses": "", "draws": "", "win_rate": "", "decisive_win_rate": "", "ci_lower": "", "ci_upper": "", "avg_reward": 6178.70, "avg_champion_reward": "", "avg_reward_difference": "", "status": "existing_champion", "notes": "Pre-existing verified champion; average shown is historical vs starter."},
        {"version": "V2", "change": "Dynamic crop economics", "champion": "V1", "games_vs_champion": summary["games"], "wins": summary["v2_wins"], "losses": summary["v2_losses"], "draws": summary["draws"], "win_rate": summary["raw_v2_win_rate"], "decisive_win_rate": summary["decisive_v2_win_rate"], "ci_lower": ci["lower"], "ci_upper": ci["upper"], "avg_reward": rewards["v2"]["mean"], "avg_champion_reward": rewards["opponent"]["mean"], "avg_reward_difference": rewards["difference_v2_minus_opponent"]["mean"], "status": decision, "notes": reason},
    ]
    EXPERIMENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EXPERIMENTS_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run_sanity() -> dict[str, Any]:
    report = run_balanced(20, SANITY_SEED_START, "v1", "sanity", progress_every=5)
    save_json(SANITY_PATH, report)
    return report


def run_main() -> dict[str, Any]:
    report = run_balanced(500, MAIN_SEED_START, "v1", "main", progress_every=25)
    save_json(MAIN_PATH, report)
    write_experiments(report)
    return report


def run_baselines() -> dict[str, Any]:
    starter = run_balanced(50, STARTER_SEED_START, "starter", "starter", progress_every=10)
    random = run_balanced(20, RANDOM_SEED_START, "random", "random", progress_every=5)
    result = {"metadata": {"agents_frozen": True}, "starter": starter, "random": random}
    save_json(BASELINES_PATH, result)
    if MAIN_PATH.exists():
        write_experiments(json.loads(MAIN_PATH.read_text(encoding="utf-8")), {"starter": starter, "random": random})
    return result


def print_summary(report: dict[str, Any]) -> None:
    print(json.dumps({key: report[key] for key in ("summary", "position_results", "reward_statistics", "confidence_interval", "timing", "reliability")}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("sanity", "main", "baselines", "all"))
    args = parser.parse_args()
    if args.mode in ("sanity", "all"):
        print_summary(run_sanity())
    if args.mode in ("main", "all"):
        print_summary(run_main())
    if args.mode in ("baselines", "all"):
        result = run_baselines()
        print(json.dumps({name: value["summary"] for name, value in result.items() if name != "metadata"}, indent=2))


if __name__ == "__main__":
    main()
