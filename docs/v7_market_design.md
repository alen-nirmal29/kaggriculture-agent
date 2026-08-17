# V7 market design

V7 layers aggregate market/town signals over frozen V6. CONTROL calls V6 logic with identical one-cow, fertilizer-on parameters. No land, additional livestock, or opponent inference is permitted.

`town.py` calculates exact consumption from currently public shop instances over a short horizon. `market.py` stores at most 12 observations per agent instance and clears them whenever step does not advance, preventing episode leakage. Price and inventory trends are simple endpoint slopes.

The market signal begins with live price, adds a bounded deterministic-demand/scarcity term and small recent price/inventory trends. Expected future price blends half of that signal back toward current price. Production intelligence then applies only 20% of that forecast adjustment to crop prices supplied to V6 economics, keeping V6 dominant.

Selling remains immediate by default. A product is held only if projected appreciation clears the configured threshold and public demand exists. Holding is disabled inside 48 remaining turns, below 300 cash, near shed capacity, or when it would violate the cow's two-day wheat reserve. Endgame therefore returns to V6 liquidation. Milk uses the same conservative safety gate; collection and cow servicing are unchanged.

Modes isolate CONTROL, SELL_INTELLIGENCE, PRODUCTION_INTELLIGENCE, and FULL_INTELLIGENCE. Forecast horizon and holding threshold are constructor parameters and history belongs to the constructed agent closure.
