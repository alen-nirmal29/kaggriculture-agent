# V5 land-expansion design

V5 preserves frozen V4 farming, four-hand hiring, crop economics, market logic, scheduling, and endgame behavior. `agent_v5.land` owns official unlock state, sequential prices, cash reserve, payback estimation, and the purchase decision.

The ROI estimate credits only 35% of ideal per-plot crop score because V4 workers were already 86% utilized at 24 plots. It scales value by remaining season, requires at least 96 turns, demands expected value above 115% of land cost, and preserves a reserve of 500 plus 20 per currently serviceable plot. Land is evaluated only at hours zero or one. Seed and worker orders precede a single `BUY_LAND` order, so operating purchases receive priority and insufficient residual cash safely prevents expansion.

The managed route preserves V4's original 24-tile prefix, then grows deterministically outward from the shed across unlocked quadrants. No worker-count, crop-economic, animal, fertilizer, opponent, or land-order variable was added.
