# V6 official animal mechanics

Source of truth: installed `kaggle-environments==1.32.7`, `kaggriculture.py`.

| Animal | Buy cost | Structure | First production | Interval | Held cap | Product | Base price |
|---|---:|---|---:|---:|---:|---|---:|
| Goose | 300 | Coop | 4 days after placement | 1 day | 4 | Egg | 50 |
| Cow | 400 | Pasture | 8 days after placement | 2 days | 6 | Milk | 160 |
| Sheep | 500 | Pasture | 6 days after placement | 3 days | 6 | Wool | 200 |

`BUILD_COOP` and `BUILD_PASTURE` require an owned empty tile, cost no cash, and permanently occupy one crop-capable tile until dug. There is no global structure limit; each structure holds one matching animal. `BUY_ANIMAL <type> <n>` puts animals in the private shed. A unit adjacent to the shed must `PICKUP` one and stand on the matching structure to `PLACE` it.

Every placed animal needs one carried wheat and one `FEED` action each day. Daily refresh resets `fed_today` and `cared_today`. A fed day resets `consecutive_unfed`; an unfed day increments it. At two consecutive unfed refreshes the animal escapes and its empty structure remains. Care is not required for survival. A day with both feed and care banks one bonus unit; that bonus is consumed at a later fed production event. Production adds one base unit plus any care bonus, capped by the held limit. `HARVEST` transfers all held egg/milk/wool to the acting unit.

Every surviving animal makes one fertilizer available at daily refresh, regardless of care. `COLLECT_FERTILIZER` transfers one unit to the acting unit. `FERTILIZE` consumes one carried fertilizer on a plant and covers the current day plus the next two. For a watered, non-ongoing crop in its yield window, the watering increment is two rather than one. It stacks with the need to water, not as a second independent yield event; all eligible crop types use the same +1 incremental rule. Fertilizer has base market price 100 but cannot be sold through the town market (`TOWN_CENTER_PRODUCTS` excludes it).

Farmer and hands share the same unit action implementation and may pick up, place, feed, care, harvest, collect, and fertilize. Each unit executes at most one action per turn. Market orders resolve after unit actions, so feed bought this turn cannot be picked up until a later turn. End-of-day inventory is returned to the shed subject to shed capacity. Exact market formats are `BUY_ANIMAL`, `BUY_PRODUCT WHEAT`, and `SELL EGG/MILK/WOOL`, each with a positive quantity.
