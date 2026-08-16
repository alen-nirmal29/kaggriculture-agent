# V3 farm-capacity results

## Protocol

V3 varied only the deterministic managed-plot limit: 6, 8, 10, or 12. Crop scoring and endgame rules were reused directly from frozen V2. Every sweep candidate played frozen V2 for 100 games on the same 50 seeds, once in each player position. No candidate was tuned during the sweep.

## Functional sanity

Each capacity completed a 720-turn game against `starter` with status `DONE`, no crash, and no timeout.

| Capacity | Final reward | Idle turns |
|---:|---:|---:|
| 6 | 18,186 | 319 |
| 8 | 23,356 | 202 |
| 10 | 26,203 | 94 |
| 12 | 27,015 | 24 |

## Fixed 100-game capacity sweep versus V2

| Capacity | W-L-D | Decisive win rate | Mean reward | Median | Min | Max | Mean difference | Idle | Movement | Productive | Failures |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 6 | 0-0-100 | N/A (no decisive games) | 17,609.96 | 17,172.0 | 16,772 | 25,734 | 0.00 | 325.96 | 166.16 | 225.48 | 0 |
| 8 | 100-0-0 | 100% | 20,139.95 | 20,114.0 | 19,751 | 22,367 | 3,361.26 | 202.45 | 224.78 | 290.01 | 0 |
| 10 | 100-0-0 | 100% | 21,896.15 | 21,903.0 | 21,304 | 22,652 | 5,543.58 | 97.56 | 271.09 | 348.53 | 0 |
| 12 | 100-0-0 | 100% | 22,399.97 | 22,600.5 | 20,951 | 25,859 | 6,404.76 | 25.18 | 302.94 | 389.57 | 0 |

The capacity-6 control drew every game and had a zero reward difference, demonstrating behavioral equivalence with V2 under the controlled conditions. Capacities 8, 10, and 12 were equally perfect head-to-head and side-balanced. Capacity 12 was selected because it produced the highest average reward and reward advantage. Its improvement over capacity 10 was accompanied by stronger pressure signals: 33.22 unwatered-plot observations at day end, 202.68 weed-blocked plot-turns, and 4.5 final unsold units per episode in the sweep. This makes 12 the strongest measured candidate, but also the operational boundary rather than evidence that still larger farms would be safe.

## Final selected V3 (capacity 12) versus frozen V2

- Games: 500, using 250 matched seeds twice and balancing V3 250/250 by player side.
- Outcome: 499 V3 wins, 1 V2 win, 0 draws.
- V3 decisive win rate: 99.8%.
- Wilson 95% confidence interval: 98.8759% to 99.9647%.
- Player 0: 249/250 wins (99.6%).
- Player 1: 250/250 wins (100%).
- Average V3 reward: 22,398.844.
- Average V2 reward: 16,074.752.
- Average difference: +6,324.092.
- Reliability: 500/500 completed, zero crashes, zero timeouts.
- Decision latency: 0.361 ms mean, 0.314 ms median, 150.864 ms maximum; 5 of 359,500 decisions exceeded 100 ms and none exceeded 500 ms.

Operationally, V3 averaged 25.266 idle, 302.378 movement, and 390.068 productive actions per episode. Idle time was concentrated at 7.904 early, 5.902 mid, and 11.460 late turns. The farm ran near saturation: mature crops accumulated 1,223.054 plot-turn observations while harvestable, crops were unwatered at day end for 32.840 plot observations, and weeds occupied managed plots for 213.056 plot-turns. Endgame realization nevertheless remained strong: only one of 500 episodes ended with one managed crop, although final unsold inventory averaged 5.094 units (median zero).

## Promotion

V3 qualifies for promotion. It met 100% completion, zero-crash, zero-timeout, decisive-win-rate, confidence-bound, and position-consistency requirements. No V4 feature was implemented.
