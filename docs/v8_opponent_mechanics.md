# V8 official opponent visibility

Verified from the installed `kaggle-environments==1.32.7` schema and interpreter.

`observation.farms` is shared and contains both players' complete public farm records. V8 may legally observe opponent money, farmer position, hand positions/count, hires today, unlocked quadrants, and every tile. Tile dictionaries expose crop type, planted day, watered state, consecutive unwatered count, yield units, fertilizer expiry, and lifecycle fields. Weeds, empty/locked cells, coops, pastures, animal type, placed day, held product, consecutive unfed count, feed/care flags, fertilizer availability, and pending care bonus are consequently public.

The shared market inventory/prices, town shops, day, and hour are also public. Reward is the player's final money and is not an opponent-planning field during play.

Each agent receives only its own `observation.private`: shed contents, seed counts, and farmer/hand inventories. The opponent's shed, seeds, carried inventory, submitted market/unit actions, action history, and future actions are unavailable. V8 never accesses them. Previous opponent behavior is inferred only by comparing successive public farm snapshots.
