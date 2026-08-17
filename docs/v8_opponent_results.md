# V8 opponent results

V6 remained frozen: 123 preflight tests passed, 151 tests passed after V8, and all V6 hashes were unchanged.

## Modes

| Mode | W-L-D | Decisive rate | V8 mean | V6 mean | Difference | Planting changes |
|---|---:|---:|---:|---:|---:|---:|
| CONTROL | 19-19-62 | 50.00% | 26,780.91 | 26,780.91 | 0.00 | 0.00 |
| STATIC | 47-53-0 | 47.00% | 26,712.24 | 26,874.06 | -161.82 | 10.62 |
| PIPELINE | 55-45-0 | 55.00% | 26,836.72 | 26,754.23 | +82.49 | 8.18 |
| FULL | 64-32-4 | 66.67% | 27,038.61 | 26,650.32 | +388.29 | 9.04 |

Static composition overreacted. Growth-stage weighting was positive, and adding public animal/structure context produced the strongest initial result.

## Refinements

Strength results were contradictory: 0.05 went 44-42-14 with -38.75 reward; 0.10 went 46-52-2 with +65.66; 0.20 went 54-46 with -24.87. No alternative strength improved both criteria, so the conservative 0.10 remained.

At 0.10 strength, two days went 53-47 with +125.59; four days went 53-43-4 with +170.46; eight days went 47-45-8 with -87.44. Four days was selected because it was the only horizon at the 55% promotion threshold with positive reward.

Forecast correctness was not directly classifiable from the saved evaluator because opponent tile transitions were aggregated rather than linked prediction-by-prediction. Predictions are therefore marked not verifiable, not assumed correct. Their practical usefulness is instead measured by changed decisions and tournament outcomes.

## Self-play and final

FULL self-play completed 50/50 with zero crashes/timeouts. Mean absolute reward separation was 133.1; no runaway or reliability pathology was detected.

The selected FULL_OPPONENT, strength 0.10, four-day policy won the final 500-game match 262-212 with 26 draws. Decisive rate was 55.274%; Wilson 95% interval 50.774%–59.690%. Player 0 was 135-102-13 and Player 1 was 127-110-13. Mean rewards were 27,067.358 versus 26,919.600, a +147.758 difference.

V8 changed 7.84 planting decisions/game, mainly toward WHEAT (3.13) and CARROT (3.012), with 0.514 toward STRAWBERRY. Mean confidence was 0.9147. Mean pressure was 0.2527 WHEAT, 0.2089 CARROT, 0.0666 STRAWBERRY, and 0.2822 MELON. It retained one cow, made zero land orders, and averaged 92.873% worker utilization, 19.418 missed-watering observations, 303.784 weeds, and 2.894 final unsold units.

All 500 episodes completed with zero crashes/timeouts. Decision time over 359,500 calls was mean 1.342 ms, median 1.311 ms, maximum 105.789 ms, one call over 100 ms, and none over 500 ms.

V8 meets every mandatory promotion gate and the Wilson lower bound exceeds 50%. V8 qualifies for promotion. The improvement is real but modest, so later work should retain the conservative bounds rather than amplify opponent reactions.
