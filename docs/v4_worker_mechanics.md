# Verified Kaggriculture 1.32.7 farm-hand mechanics

Source of truth: the installed `kaggle_environments/envs/kaggriculture/kaggriculture.py` and `kaggriculture.json`.

- `HIRE` is a market order formatted as `["HIRE"]`. Multiple orders may be submitted, subject to the default ten-market-order turn limit.
- The next hire costs `farmHandCostMult * fib(hires_today)`, with the sequence indexed as `1, 1, 2, 3, 5, 8, ...`; the default multiplier is one.
- Hiring fails silently when cash is insufficient. There is no explicit maximum-hand count in the implementation.
- Market processing occurs after all farmer and existing-hand actions. A newly hired hand therefore cannot act on its hiring turn and first appears in the following observation.
- Hands spawn on the four inner shed-access coordinates. The least occupied coordinate is chosen, with NW, NE, SW, SE order breaking ties. Multiple units may occupy the same coordinate.
- Public `farm["hands"]` is an ordered position list. Private `inventories` is `[farmer_inventory, hand_0_inventory, hand_1_inventory, ...]`.
- `hands` actions are ordered by the same index and formatted as a list of unit actions: `[[op, ...args], ...]`. Actions for nonexistent indices are ignored; missing actions mean those hands do nothing.
- Hands support the same unit operations as the farmer: movement, `PASS`, shed `DROP`/`PICKUP`/`PLACE`, `PLANT`, `WATER`, `HARVEST`, `DIG`, and the animal/fertilizer operations that V4 deliberately does not use.
- Each hand has an independent unlimited mapping-style carried inventory. Seeds remain shared in `private["seeds"]` and are consumed directly by planting.
- Unit actions resolve sequentially: farmer first, then hands in index order. If simultaneous plant demand exceeds available seeds, every request for that crop is replaced with `PASS` atomically.
- There is no collision or blocking rule. Units can share tiles and cross through each other. Duplicate tile work usually leaves later actions as silent no-ops.
- At each day boundary, all unit inventories are dropped into the shed up to shed capacity (overflow is discarded), the farmer resets to the default spawn, all hands disappear, `hires_today` resets to zero, and inventories reset to only the farmer.
- Movement onto locked tiles is allowed, but productive tile operations on locked tiles silently no-op. Shed operations remain valid from locked shed-access coordinates.
- The initially unlocked NW quadrant contains 25 valid tile coordinates. V4 does not buy land.
