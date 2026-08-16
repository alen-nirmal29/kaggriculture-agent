# Kaggriculture Agent

Develop and evaluate an autonomous Python agent for the Kaggle Kaggriculture competition. The project requires Python 3.11 and `kaggle-environments==1.32.7`.

V1 is implemented as a deterministic, task-driven carrot farmer. It maintains six nearby tiles in the starting quadrant, clears weeds, buys seeds, plants, waters daily, harvests at maximum-yield age, sells stored produce, and stops investments that cannot pay back before season end. The implementation is grounded in [the installed mechanics](docs/v1_mechanics.md); its design is summarized in [the V1 strategy](docs/v1_strategy.md).

## Setup

Create a project-local Python 3.11 virtual environment, then install the dependencies:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Verification

```powershell
.\.venv\Scripts\python.exe check_environment.py
.\.venv\Scripts\python.exe smoke_test.py
.\.venv\Scripts\python.exe -m pytest
```

## Evaluation

Run one match (use `--position 1` to swap sides):

```powershell
.\.venv\Scripts\python.exe evaluation\run_match.py --opponent starter
```

Run the full benchmark suite and save `evaluation/results/v1_benchmark.json`:

```powershell
.\.venv\Scripts\python.exe evaluation\benchmark.py
```

Measured over 80 complete games, alternating player positions:

| Opponent | Games | V1 wins | Win rate | Avg V1 final money | Avg opponent final money |
|---|---:|---:|---:|---:|---:|
| pass | 10 | 10 | 100% | 6806.40 | 3000.00 |
| random | 20 | 20 | 100% | 6018.35 | 0.00 |
| starter | 50 | 50 | 100% | 6178.70 | 3481.52 |

The benchmark recorded zero crashes, timeouts, or failed episodes. These are local seeded results, not a claim about leaderboard performance.
