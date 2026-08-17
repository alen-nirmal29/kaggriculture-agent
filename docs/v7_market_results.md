# V7 market and town results

V6 was frozen and unchanged. The preflight suite passed 98 tests; the completed V1–V7 suite passed 123. All V6 hashes matched before and after V7.

## Mode comparison

| Mode | W-L-D vs V6 | Decisive rate | Mean V7 reward | Mean difference | Units held |
|---|---:|---:|---:|---:|---:|
| CONTROL | 28-28-44 | 50.00% | 26,809.28 | 0.00 | 0 |
| SELL | 25-25-50 | 50.00% | 27,172.26 | 0.00 | 0 |
| PRODUCTION | 24-32-44 | 42.86% | 27,139.30 | -65.84 | 0 |
| FULL | 20-18-62 | 52.63% | 26,947.99 | +5.78 | 0 |

SELL never found a projected price gain large enough to pass the 10% liquidity/safety threshold, so its actions were identical to V6. FULL's small positive result was not promotion-grade and came entirely from production adjustments.

## Refinements

The FULL horizon sweep used mechanics-derived windows. Four turns was 25-25-50 with zero mean difference; 12 turns was 19-19-62 with zero difference; 24 turns was 26-28-46 with -5.67. No horizon added value. The holding-threshold sweep was skipped because SELL and FULL held zero units in 200 combined mode games.

Forecast directional accuracy was not separately scored because forecasts caused no holds and horizon-adjusted production had no stable benefit. Price-at-harvest was not instrumented; price-at-sale and quantities are retained in aggregate evaluator metrics. This is reported as unavailable rather than inferred.

## Final

The final V7 configuration is CONTROL, which is V6-equivalent. Over 500 games it went 123-123-254, decisive rate 50.0%, Wilson 95% interval 43.800%–56.200%, and zero mean reward difference. Each agent averaged 26,950.042. Position 0 was 59-64-127; position 1 was the mirror 64-59-127.

V7 averaged 318.908 units sold, 21.34 milk sold, 2.968 final unsold inventory, one cow purchase, no land orders, no holds, 92.581% worker utilization, 19.252 missed-watering observations, and 272.592 weed observations. It completed 500/500 with zero crashes and timeouts.

Decision time across 359,500 calls was mean 0.784 ms, median 0.794 ms, maximum 116.868 ms, one call over 100 ms, and none over 500 ms.

V7 fails the 55% promotion threshold and has no reward improvement. V6 remains champion. The practical lesson is that public shop demand changes stock too slowly relative to the market's 10,000-unit baseline to justify conservative holding, while demand-adjusted crop changes add noise rather than robust value.
