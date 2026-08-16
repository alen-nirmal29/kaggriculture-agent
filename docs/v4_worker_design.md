# V4 worker scheduling design

V4 preserves frozen V3 crop economics, market behavior, endgame rules, and compact routing. Its primary changes are labor and task scheduling.

`agent_v4.workers` owns worker parsing, official hire-cost calculation, explainable task records, target reservations, distance-adjusted assignment, per-crop seed reservations, and hiring decisions. Tasks retain V3's farming priorities: harvest, urgent watering, clearing exhausted crops/weeds, and planting. A worker carrying produce receives deposit support when ordinary farm work no longer dominates or liquidation is urgent.

Assignments are greedy and deterministic. Every unit selects the highest-priority unreserved reachable task adjusted by Manhattan travel distance. Once selected, its target is reserved so no other unit travels toward or acts on that target in the same decision. Exact-position work is favored. Plant assignments also reserve the shared seed budget to prevent Kaggriculture's atomic over-demand cancellation.

The configured `max_hands` is a ceiling, not a mandate. Hiring considers pending tasks (including planned empty plots before purchased seeds arrive), turns left in the day and season, current hands, Fibonacci marginal cost, a cash reserve for farming, and a conservative expected action value. New hires cannot work until the following turn. Hiring becomes stricter during the final day and is rejected when insufficient useful actions remain to recover cost.

The initial experiment fixes managed capacity at V3's 12 plots and varies only `max_hands` from zero through four. `max_hands=0` delegates directly to frozen V3 behavior as the labor control.
