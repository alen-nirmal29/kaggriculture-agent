# V6 animal results

V4 integrity was preserved: 70 pre-V6 tests passed; 98 tests passed after V6; all recorded V4 SHA-256 hashes were unchanged.

## Selection experiments

Control (100 games) had identical mean rewards of 23,710.07 and zero mean difference. Symmetric player-order interactions produced 24 wins, 24 losses, and 52 draws.

| Species policy | W-L-D | Decisive rate | Mean V6 reward | Mean difference | Mean animals |
|---|---:|---:|---:|---:|---:|
| Goose | 24-24-52 | 50% | 23,710.07 | 0.00 | 0 |
| Cow | 97-3-0 | 97% | 26,764.52 | +2,720.81 | 1 |
| Sheep | 25-25-50 | 50% | 24,144.70 | 0.00 | 0 |

Goose and sheep failed the precommitted remaining-season ROI gate and therefore safely behaved as no-animal controls. The corrected cow run averaged 400 animal spend, 846.85 purchased-feed spend, 5,029.57 product revenue, 29 feed actions, 12.71 care actions, and zero escapes. An initial cow run exposed wheat sell/rebuy churn; feed reservation was corrected and the same cow seeds were rerun before selection.

| Cow cap | W-L-D | Mean difference | Mean max animals | Mean escapes |
|---:|---:|---:|---:|---:|
| 1 | 97-3-0 | +2,720.81 | 1 | 0 |
| 2 | 0-100-0 | -30,879.18 | 2 | 0.72 |
| 3 | 0-100-0 | -16,423.88 | 3 | 3.00 |
| 4 | 0-100-0 | -32,143.65 | 3 | 3.00 |

One cow is the labor-safe cap. Higher counts overwhelmed the frozen four-hand policy. Mixed livestock was skipped because fewer than two species were positive.

Fertilizer OFF (100 games) was 97-3 with mean reward 26,754.92. Fertilizer ON was 98-2 with mean reward 26,821.61, a +66.69 candidate reward delta. ON averaged 3.54 collections and 2.01 applications. Fertilizer is retained, although its incremental value is modest relative to milk.

## Final policy and tournament

The frozen V6 policy is one cow, one deterministic pasture tile, fertilizer ON, no expansion, and at most four hands.

Final 500-game result: V6 490, V4 10, draws 0. Decisive rate 98.0%; Wilson 95% interval 96.358%–98.910%. V6 was 245-5 as Player 0 and 245-5 as Player 1. Mean rewards were 26,902.018 versus 24,135.430, a +2,766.588 difference.

V6 averaged one animal, 400 animal spend, 863.368 purchased-feed spend, 4,986.652 animal-product revenue, 3.336 fertilizer collections, 1.794 applications, 29 feed actions, 12.782 care actions, zero escapes, and 92.591% measured worker utilization. It completed 500/500 with zero crashes and zero timeouts.

Decision time over 359,500 calls: mean 1.093 ms, median 1.036 ms, maximum 202.307 ms; 2 calls exceeded 100 ms and none exceeded 500 ms.

V6 qualifies for promotion under every stated gate. The main lesson is that one cow is highly profitable, fertilizer adds a small positive increment, and additional cows catastrophically exceed available labor.
