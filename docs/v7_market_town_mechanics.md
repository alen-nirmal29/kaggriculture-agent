# V7 verified market and town mechanics

Source: installed `kaggle-environments==1.32.7` Kaggriculture implementation.

The shared market contains WHEAT, CARROT, TOMATO, STRAWBERRY, MELON, EGG, MILK, WOOL, and FERTILIZER. Each starts at inventory 10,000 and its configured base price. Prices are deterministic functions of stock relative to 10,000. Below baseline, price rises using the product's configured response function; above baseline, it falls. Functions include square root, logarithmic, linear, squared, and hinge curves. Prices are integer-rounded with a floor of 1 and no explicit ceiling.

SELL removes one item at a time from the player's shed, adds the quoted cash, and increases shared stock unless price is 1. BUY_PRODUCT is limited to WHEAT and FERTILIZER, removes shared stock, charges the post-buy quote, and deposits in the shed if cash and shed capacity allow. Seeds and animals use fixed costs. Malformed, unaffordable, unavailable, or capacity-blocked orders silently stop their remaining quantity. Positive quantities may partially execute. Up to `maxMarketOrdersPerTurn` (default 10) orders are accepted.

Orders resolve by queue index. For each unit of a quantity order, both players receive quotes from the same pre-commit inventory, then commits occur in player order. Thus equal simultaneous unit orders receive equal quotes. Unit actions happen first, then market orders, then town consumption, then price refresh. Prices refresh after every market queue entry and after town consumption. There is no independent daily market reset or external replenishment.

Public town state is `town.unlocked_shops`, including duplicate shop instances. Shop mappings are:

- BAKERY: EGG, WHEAT
- PIZZA_SHOP: MILK, TOMATO, WHEAT
- BRUNCH_SPOT: EGG, WHEAT, STRAWBERRY
- YARN_STORE: WOOL
- ICE_CREAM_SHOP: STRAWBERRY, MILK, WHEAT
- PET_CAFE: CARROT
- SMOOTHIE_SHOP: STRAWBERRY, MILK
- FARMERS_MARKET: WHEAT, CARROT, TOMATO, STRAWBERRY

Every fourth turn, every unlocked shop instance removes one of each listed product from shared stock. A single-product shop removes two. Every 24th turn the town center removes one WHEAT, CARROT, TOMATO, STRAWBERRY, MELON, EGG, MILK, and WOOL. Consumption can drive inventory below zero and always changes subsequent prices; shortages do not suppress demand.

One shop instance unlocks after every third day until eight instances exist. The type is drawn with replacement from the sorted shop names using the environment's seeded daily RNG. Existing-shop demand and timing are exactly predictable from public state. Future shop identity is not public before unlock, so V7 does not claim exact forecasts for unknown instances. Shops have no recipes, quantities beyond these fixed removals, or private state.
