# V9 final design

V9 is a bounded integration of the frozen V8 champion. It retains V8's public
opponent pipeline, V6's one-cow fertilizer policy, 24 managed plots, crop
economics, scheduler, market realization, and endgame behavior. It does not add
new forecasting, land expansion, extra livestock, learning, or external data.

## Gap analysis and experiments

The principal under-tested interaction was labor capacity. Fixed 100-game,
balanced, disjoint-seed comparisons tested caps of four, five, and six hands.
Only after that result were one-cow, two-cow, and first-land interactions gated.
Nearby opponent strengths and horizons were then compared without broad search.

The frozen candidate is:

- six hands maximum;
- one cow maximum and fertilizer enabled;
- 24 managed plots and no land purchases;
- `FULL_OPPONENT`, strength `0.075`, horizon three days.

Two cows and land expansion are permanently rejected in V9. Crop economics,
task priorities, and endgame rules were not reopened because no measured gap
justified the regression risk.

## Standalone architecture

`evaluation/build_v9_submission.py` reads the frozen dependency closure and
generates one deterministic Python file. At import time that file installs the
embedded modules in memory and exports the same `main_v9.agent` callable. It
does not read files, import repository modules, use the network, or require a
third-party runtime package.
