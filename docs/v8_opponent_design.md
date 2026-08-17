# V8 opponent design

V8 starts from frozen V6. Only crop economics may change. Immediate selling, one cow, fertilizer, four-hand ceiling, routing, endgame liquidation, and no-land policy remain V6 behavior.

`state.py` reads the opponent exclusively from shared `observation.farms[1-player]`. `opponent.py` summarizes public crops, maturity, structures, animals, workers, active tiles, and land. It retains at most 12 snapshots and clears history when step does not advance, preventing episode leakage.

Static mode counts current crop composition. Pipeline mode weights public planted age, time to first yield, and visible yield at a conservative 0.6 realization factor. Full mode adds 0.5 expected product per visible animal. Confidence combines six-observation persistence with active-farm scale. Predicted output is normalized against 12 units and capped at pressure 1.

Opponent pressure reduces only the live crop-price input supplied to V6 economics. Default strength is 10%, scaled by confidence and pressure. This acts as a bounded tie-breaker; it cannot eliminate a crop's value. Influence becomes zero when fewer than the larger of 48 turns or the configured horizon remain. No opponent inventory, seed, action, or future behavior is guessed.

Modes are CONTROL, STATIC_SNAPSHOT, PIPELINE, and FULL_OPPONENT. Strength and crop-cycle-based horizon days are separately configurable. Main V8 defaults to CONTROL until measurements justify promotion.
