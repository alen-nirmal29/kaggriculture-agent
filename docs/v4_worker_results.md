# V4 worker-scheduling results

## Fixed 12-plot worker sweep

All policies played frozen V3 for 100 games with identical 50-seed pairs and balanced positions. Final rewards are already net of hiring charges.

| Max hands | W-L-D | Decisive win rate | V4 reward | V3 reward | Difference | Hires/day | Total cost | Worker productive | Worker idle | Utilization |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 4-4-92 | 50% | 18,558.58 | 18,558.58 | 0.00 | 0.000 | 0.00 | 0.00 | 0.00 | N/A |
| 1 | 0-100-0 | 0% | 16,112.23 | 20,226.43 | -4,114.20 | 0.995 | 29.84 | 188.82 | 59.41 | 91.3% |
| 2 | 100-0-0 | 100% | 20,759.58 | 17,615.18 | +3,144.40 | 2.000 | 60.00 | 298.74 | 605.25 | 56.1% |
| 3 | 100-0-0 | 100% | 23,882.55 | 14,368.12 | +9,514.43 | 2.971 | 118.84 | 341.09 | 1,060.23 | 48.2% |
| 4 | 100-0-0 | 100% | 24,453.43 | 13,640.10 | +10,813.33 | 3.958 | 207.79 | 368.65 | 1,507.18 | 44.8% |

The zero-hand control delegates directly to V3. Its few symmetric wins/losses instead of 100 draws reflect player-order effects in the shared market; aggregate reward difference was exactly zero. One hand materially regressed, showing that labor value depends on coordinated parallel capacity rather than the nominally tiny hire price. Four hands was selected on net reward and perfect reliability despite lower utilization than the one-hand policy.

At 12 plots, four hands reduced end-of-day unwatered observations from the V3 reference 32.84 to 0.04 and weed-blocked plot-turns from 213.056 to 0.46. Mature-crop waiting was 1,388.17 plot-turns, so absolute waiting did not improve; more parallel harvest opportunity was offset by task timing and the metric counting every harvestable plot each observation.

## Worker-supported capacity sweep

The selected four-hand policy was frozen. The installed map exposes 25 valid initially unlocked NW tiles; no land was purchased. Capacities 12, 16, 20, and 24 each played 100 matched, balanced games versus V3.

| Capacity | W-L-D | Average reward | Difference | Utilization | Worker idle | Missed watering | Weed blockage | Unsold inventory |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 12 | 100-0-0 | 24,427.55 | +10,553.20 | 44.8% | 1,509.15 | 0.04 | 0.46 | 0.00 |
| 16 | 100-0-0 | 22,918.79 | +5,346.72 | 63.1% | 1,015.62 | 3.76 | 1.54 | 0.00 |
| 20 | 100-0-0 | 26,664.85 | +11,446.63 | 80.6% | 533.13 | 13.89 | 56.52 | 0.00 |
| 24 | 100-0-0 | 27,161.62 | +11,573.56 | 86.2% | 379.53 | 15.45 | 144.03 | 0.62 |

Capacity 24 was selected because it had the highest reward, reward advantage, and utilization with perfect reliability and position balance. Capacity 20 was operationally cleaner and close in reward; the selected 24-plot farm should therefore be viewed as the measured boundary, not evidence for land expansion.

## Final V4 versus V3

- Frozen configuration: maximum four temporary hands, 24 managed plots, no land purchases.
- Outcome: 500 V4 wins, zero V3 wins, zero draws; 250/250 wins from each player side.
- Decisive win rate: 100%; Wilson 95% CI 99.2376% to 100%.
- Average reward: V4 26,599.260; V3 15,234.554; difference +11,364.706.
- Hiring: 119.424 hands and 208.632 total cost per episode; 3.981 hires and 6.954 cost per day.
- Worker work: 641.982 productive, 1,704.198 movement, and 383.092 idle actions; 86.014% non-idle utilization.
- Operations: 2,933.056 mature-crop plot-turns, 15.840 unwatered day-end observations, 136.480 weed-blocked plot-turns, and 1.726 final unsold units per episode.
- Reliability: 500/500 complete; zero crashes, timeouts, or other failures.
- Decision latency: 0.667 ms mean, 0.593 ms median, 216.611 ms maximum; three decisions over 100 ms and none over 500 ms.

V4 qualifies for promotion under every required gate. V3 remains unchanged. No V5 feature was implemented.
