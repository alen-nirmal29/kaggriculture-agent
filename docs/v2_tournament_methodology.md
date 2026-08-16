# V2 versus V1 tournament methodology

This is a frozen-agent evaluation using Python 3.11.9 and `kaggle-environments==1.32.7`. Neither `main.py`/`agent/` nor `main_v2.py`/`agent_v2/` may change during the experiment.

## Randomness and pairing

The installed `kaggriculture.json` officially defines `configuration.seed`. The interpreter resolves that seed, stores it in `env.info["seed"]`, and uses `random.Random((seed * 1_000_003) ^ day)` for reproducible daily weed spawning and town-shop selection. V1 and V2 are deterministic.

The 500-game tournament uses 250 distinct seeds. Every seed is run twice: once with V2 as Player 0 and once with V2 as Player 1. This exactly matches environment conditions across player orders. The 20-game sanity tournament similarly uses 10 paired seeds. Seed ranges are separate between sanity, main, and baseline runs.

The built-in `random` agent constructs its own unseeded `random.Random()`. Environment mechanics remain seeded and position-balanced in that regression, but random-agent actions are not exactly reproducible from the environment seed alone.

## Games and outcomes

- Sanity: 20 games, 10 per V2 position.
- Main: exactly 500 games, 250 per V2 position.
- Regression: 50 games versus starter and 20 versus random, balanced by position.
- A win means V2 final reward is greater than its opponent's; a loss is lower; equality is a draw.
- Installed source assigns final reward to `farms[player]["money"]`, so rewards and winners both use final banked money.
- An episode is complete only when both agents are `DONE` after 720 recorded steps. `ERROR` is a crash, `TIMEOUT` is a timeout, any other non-`DONE` status is invalid, and exceptions or incomplete episodes are separately retained as failures.

Raw win rate is wins divided by all completed games. Draws are neither wins nor losses. Decisive win rate and its 95% Wilson interval use only `wins + losses`.
