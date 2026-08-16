# Kaggriculture V1 mechanics

Source of truth: the installed `kaggle-environments==1.32.7` `kaggriculture.py`, `kaggriculture.json`, and bundled README.

- Coordinates are `[x, y]`; `x` increases east and `y` increases south. Tiles are read as `tiles[y][x]` on a 10×10 board.
- The farmer starts at `(4, 4)`. Only the NW 5×5 quadrant (`x < 5`, `y < 5`) starts unlocked.
- The shed is between the four quadrants. `DROP`, `PICKUP`, and shed-directed `PLACE` work while standing at `(4,4)`, `(5,4)`, `(4,5)`, or `(5,5)`.
- Relevant observation fields are `step`, `day`, `hour`, `player`, `farms[player]`, `private`, `market`, and `town`. The farm contains `money`, `tiles`, `farmer`, `hands`, and `unlocked_quadrants`.
- `private.inventories[0]` is the main farmer's carried inventory. `private.shed` is stored, sellable inventory. `private.seeds` is separate, uncapped seed inventory; planting consumes it directly.
- An unlocked empty tile is `None`; a locked tile is `"LOCKED"`; weeds are `{"kind": "WEED"}`. Plants contain `kind`, `crop`, `planted_day`, `watered_today`, `consecutive_unwatered`, `yield_units`, `max_lifespan_step`, and `fertilized_until_day`.
- Movement actions are `NORTH`, `SOUTH`, `EAST`, and `WEST`. Board bounds are enforced. Movement through locked tiles is allowed, but farming actions on them are no-ops.
- Crop actions are `["PLANT", crop]`, `["WATER"]`, `["HARVEST"]`, and `["DIG"]`. `DIG` clears weeds and plants. `DROP` transfers all carried items to the shed when shed-adjacent, subject to the 100-item shed cap.
- Market orders are `["BUY_SEED", crop, n]` and `["SELL", item, n]`. Selling draws only from the shed. Invalid actions silently do nothing.
- Planting day counts as the first unwatered day. At each day end, two consecutive unwatered refreshes turn a plant into a weed, so a new plant must be watered on its planting day and every day thereafter.
- Wheat: seed $10, first harvest age 2 days, maximum-yield age 4, initial yield 1, and +1 yield for useful watering at ages 2–4. Carrot: seed $20, first harvest age 2, maximum-yield age 3, initial yield 1, and +1 at ages 2–3. One-time crops disappear after harvest.
- Harvest requires `yield_units > 0` and crop age at least `first_yield_day`; harvested goods enter the acting unit's carried inventory. All carried inventory is automatically moved to the shed at day end, then the farmer resets to `(4,4)`.
- Per turn, unit actions run first, market orders second, town consumption third, decay fourth, and day-end refresh last. Therefore a seed bought this turn cannot be planted until the next turn, while goods dropped this turn can be sold in the same turn.
- The season is 720 turns (30 days × 24 turns). Final reward is banked money; most money wins. Unsold shed or carried goods have no final reward value.
- The configured action timeout is 1 second.
