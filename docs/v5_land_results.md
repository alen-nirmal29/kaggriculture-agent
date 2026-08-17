# V5 land-expansion results

## Functional sanity

All four 720-turn starter episodes completed with `DONE`, no crash, and no timeout. Max-expansion zero earned 34,661 with no purchase. Caps one, two, and three each bought only NE at turn 265, spent 1,000, reached 49 available managed cells, and earned 28,457, 27,800, and 27,935 respectively. These games were sanity checks only.

## Control and expansion-cap sweep

The 100-game zero-expansion control delegated directly to V4: 23 wins, 23 losses, 54 draws, and exactly zero mean reward difference. Symmetric non-draws arise from player-order effects in the shared market.

Every land-enabled cap produced the same measured behavior: exactly one purchase at turn 265 in all 100 games, 1,000 average spend, 39.751 time-averaged managed plots, zero second or third purchases, and 100 losses to V4. V5 averaged 20,463.70 versus V4's 24,207.68, a −3,743.98 difference. All 300 games completed without crashes or timeouts.

Max caps two and three correctly did not force additional purchases. The ROI policy rejected their 2,000 and 4,000 follow-on costs, but it was still too optimistic about the first quadrant: four workers could not profitably service the jump toward 48 managed plots.

## Fixed timing validation

Two predeclared 50-game baselines bought the first quadrant at turn 24 or 120. Both lost 50/50. Their mean differences were −17,796.38 and −17,833.16, substantially worse than ROI timing at turn 265. Dynamic timing reduced damage but did not make land profitable.

## Capacity refinement

Skipped by design. No land-enabled policy improved on V4, so there was no valid selected expansion policy or newly unlocked capacity to refine. The final managed capacity remains V4's 24 plots.

## Final V5 versus V4

The selected V5 policy is zero expansions and delegates exactly to frozen V4. Across 500 matched, balanced games it recorded 138 wins, 138 losses, and 224 draws; decisive rate 50%, Wilson 95% CI 44.142%–55.858%. Both agents averaged 24,059.650 and mean difference was zero. All 500 games completed with zero crashes/timeouts.

No land was bought: 500 zero-expansion games, zero spend, no purchase turns, and 24 average managed plots. Worker utilization was 87.714%; mature waiting 4,188.078 plot-turns, missed watering 20.764, weed blockage 208.728, and unsold inventory 0.894 per episode. Decision latency was 0.509 ms mean, 0.448 ms median, and 59.953 ms maximum, with no decisions over 100 ms.

V4 remains champion. V5 does not meet win-rate, confidence, or positive-reward gates. No V6 feature was implemented.
