# V2 crop economics

Source of truth: the installed `kaggle-environments==1.32.7` implementation and schema.

| Crop | Seed cost | First harvest | Recurring? | Unfertilized yield pattern | Key work requirements |
|---|---:|---:|---|---|---|
| Wheat | $10 | age 2 | No | Starts at 1; useful watering at ages 2–4 raises practical max-age yield to 4 | Plant, water every day, harvest, replant |
| Carrot | $20 | age 2 | No | Starts at 1; useful watering at ages 2–3 raises max-age yield to 3 | Plant, water every day, harvest, replant |
| Tomato | $50 | age 8 | Yes | One unit at ages 8, 9, 10, and 11; four lifetime production events | Plant once per cycle, water daily, harvest produced units; clear after exhaustion |
| Strawberry | $100 | age 10 | Yes | One unit at ages 10, 12, 14, and 16; four lifetime production events | Plant once per cycle, water daily, harvest produced units; clear after exhaustion |
| Melon | $80 | age 10 | No | Starts at 1; useful watering from age 6 reaches the six-unit cap by age 10 | Plant, water every day, harvest, replant |

Planting day counts as unwatered, and two consecutive missed day-end refreshes turn a plant into a weed. All live crops therefore need daily watering. One-time crops disappear on harvest. Recurring crops remain, stop producing after four scheduled events, then enter decay. Harvested goods are carried, automatically enter the shed at day end, and can only be sold from the shed.

The shared observation exposes `market.prices` and `market.inventory`. Sale prices are nonlinear functions of shared inventory, floored at $1, and refresh after market and town activity. Final reward is banked money after 720 turns (30 days × 24 turns), so unrealized crops and unsold inventory have no terminal value.

## V2 scoring

For each crop, V2 simulates complete production cycles that can still mature before turn 720. It estimates realizable units at the current live sale price, subtracts seed costs, and applies a small explicit penalty for planting, daily watering, harvesting, clearing exhausted recurring plants, and a share of route movement. Crops with no realizable output receive no allocation.

The model is recalculated when planting space exists. Existing crops are never uprooted merely because prices move. The current dominant crop remains preferred unless another crop's score is at least 15% higher. A runner-up receives at most two of six plots only when its score is at least 92% of the preferred crop, which provides controlled mixed-crop capability without unstable switching.
