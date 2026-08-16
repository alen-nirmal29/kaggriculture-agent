"""Minimal executable head-to-head foundation for future agent versions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from kaggle_environments import make  # noqa: E402

from main import agent as v1_agent  # noqa: E402


def resolve_agent(name: str):
    return v1_agent if name == "v1" else name


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent-a", choices=("v1", "pass", "random", "starter"), default="v1")
    parser.add_argument("--agent-b", choices=("v1", "pass", "random", "starter"), default="starter")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    env = make("kaggriculture", configuration={"seed": args.seed}, debug=True)
    env.run([resolve_agent(args.agent_a), resolve_agent(args.agent_b)])
    print(json.dumps({"agents": [args.agent_a, args.agent_b], "steps": len(env.steps), "results": [{"status": s.status, "reward": s.reward} for s in env.state]}, indent=2))


if __name__ == "__main__":
    main()
