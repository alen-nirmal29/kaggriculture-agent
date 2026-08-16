# V3 capacity design

V2 is frozen. Its six-plot capacity is enforced by `agent_v2.strategy.MANAGED_PLOTS`, with `PLOT_LIMIT = len(MANAGED_PLOTS)`. Task generation and route tie-breaking iterate that fixed tuple. `crop_allocation` accepts a plot limit but defaults to six and caps a leading recurring crop at four plots. The unchanged economic workload estimate assumes six adjacent plots share five movement actions, expressed as `5/6` movement per tile-day.

V2's route is a continuous snake starting at the NW shed-access tile: `(4,4), (3,4), (2,4), (1,4), (1,3), (2,3)`. It is compact and x-first routing can service adjacent successive targets without obstacles.

V3 keeps the same first six positions and extends the continuous snake deterministically through `(3,3), (4,3), (4,2), (3,2), (2,2), (1,2)`. Capacities 6, 8, 10, and 12 are prefixes, remain inside the unlocked NW quadrant, contain no duplicates, and never change during an episode.

Capacity risks are daily watering plus route movement, synchronized harvest/replant spikes, weeds adding `DIG`, delayed inventory liquidation, and end-of-season unrealized crops. The normal-day estimate is `plots + (plots - 1)` actions. A one-time-crop renewal estimate is `3 * plots + (plots - 1)` and may span at most two days because a crop tolerates one missed refresh. Total recurring allocation is capped at four plots because recurring renewal additionally requires `DIG`. These constraints change capacity scheduling only; V2 crop scores, prices, horizon logic, penalties, and endgame rules are reused unchanged.
