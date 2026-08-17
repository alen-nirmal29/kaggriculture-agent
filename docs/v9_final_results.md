# V9 final results

## Integrity and selection

All 151 pre-V9 tests passed before work. Frozen V8 hashes were unchanged after
V9. The final suite passed 190/190 tests.

Development used balanced, disjoint seed blocks (100 games/candidate):

| Experiment | W-L-D vs V8 | Decisive rate | Mean V9 reward | Mean difference |
|---|---:|---:|---:|---:|
| 4 hands (control) | 20-20-60 | 50% | 26,815.65 | 0.00 |
| 5 hands | 75-25-0 | 75% | 27,584.99 | +610.14 |
| 6 hands | 98-2-0 | 98% | 30,908.82 | +3,727.92 |
| 6 hands, 1 cow | 98-2-0 | 98% | 29,545.88 | +2,641.35 |
| 6 hands, 2 cows | 0-100-0 | 0% | 122.30 | -38,232.51 |
| 6 hands, first land | 0-100-0 | 0% | 23,545.79 | -2,918.66 |

Mean final hand counts were 3.52, 4.96, and 5.60 for the four-, five-, and
six-hand caps. Per-action utilization, crop waiting, missed watering, weeds,
animal-task completion, and movement were not separately instrumented in the
V9 evaluator; no values are inferred for them.

Strength 0.075 and 0.10 both went 98-2; 0.075 won the reward tiebreak
(+2,565.00 versus +2,324.62). Strength 0.125 went 97-3. At strength 0.075,
three- and four-day horizons both went 97-3; three days won the reward
tiebreak (+2,580.18 versus +2,277.48). Five days went 90-10. The shortlist was
untouched V8, six hands with V8 opponent parameters, and six hands with the
0.075/three-day refinement. The strongest development candidate alone advanced
to the expensive validation and was not changed afterward.

No crop economics, scheduler, or endgame change was accepted. Two cows, land
expansion, V7 town forecasting, and broader tuning remain rejected.

## Independent validation and final holdout

The 500-game validation result was 490-10-0 against V8 (98.0%; Wilson 95% CI
96.358%-98.910%), with mean rewards 29,397.690 versus 26,912.336 and a
+2,485.354 difference. Player-position results were 246-4 and 244-6. All 500
episodes completed with zero crashes/timeouts.

The untouched 1,000-game holdout was 969-31-0 (96.9%; Wilson 95% CI
95.633%-97.808%). Player 0 was 485-15 and Player 1 was 484-16. V9 mean/median
rewards were 29,517.358/29,716; V8 mean/median rewards were
27,017.382/27,196. Mean difference was +2,499.976. Mean final hand count was
5.709 and mean final unsold inventory was 5.708 units. All 1,000 completed with
zero crashes/timeouts and no status-detected invalid-action failure.

Across 719,000 holdout decisions: mean 1.825 ms, median 1.471 ms, p95 2.641 ms,
p99 5.969 ms, maximum 632.284 ms, 363 over 100 ms, one over 500 ms, and zero
timeouts. This retains margin below the official one-second limit, though the
single 632 ms local scheduling outlier is recorded rather than hidden.

## Opponent pool, self-play, and artifact

On held-out, position-balanced blocks, the exact standalone file went 50-0
against V6, 50-0 against V4, and 50-0 against starter. Mean reward differences
were +3,016.42, +5,483.24, and +37,238.06. It also completed 100/100 games
against an independently loaded copy of itself. These 250 episodes had zero
crashes, timeouts, or invalid-action failures.

Development (1,200), validation (500), holdout (1,000), and final corrected
artifact stress (250) comprise 2,950 completed V9 experimental episodes. The
discarded pre-fix stress run is not counted because a mixed-import harness
collision made it invalid evidence. The collision-safe loader subsequently
passed exact action parity across complete 720-turn episodes in both positions.

## Decision

V9 qualifies. It exceeds every strategic promotion gate, is balanced by player
position, passes the final unseen holdout with a Wilson lower bound far above
50%, and preserves perfect observed reliability. The strategic champion and
submission configuration is 24 plots, economic hiring up to six hands, one cow,
fertilizer enabled, no land expansion, V8 crop/selling/endgame systems, and the
FULL_OPPONENT model at strength 0.075 with a three-day horizon.
