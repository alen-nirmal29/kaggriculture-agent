# Verified Kaggriculture 1.32.7 land mechanics

- Farms are 10×10, divided into four 5×5 quadrants. NW is initially unlocked; NE, SW, then SE unlock sequentially.
- `LAND_PRICES` is `[1000, 2000, 4000]`. Prices are fixed and indexed by the number of already unlocked extra quadrants.
- A purchase is a market order formatted `["BUY_LAND"]`. It is parsed as an atomic order and processed after all unit actions, so newly unlocked cells cannot be used by units on the purchase turn; they are visible and usable from the next observation.
- `_do_buy_land` always unlocks the next quadrant. Earlier quadrants cannot be skipped. Once all three extras are unlocked, further purchases silently do nothing.
- Multiple `BUY_LAND` orders may appear in one turn, subject to the default ten-order market limit. They resolve sequentially and can unlock multiple quadrants if cash covers each current price.
- Payment occurs during market processing. Insufficient cash makes that individual purchase a silent no-op. Atomic orders are processed in player order at each market queue index; seed buys, hires, and land orders therefore interact through shared available cash and their submitted ordering.
- Each quadrant contains 25 tile coordinates. There are no blocked/non-productive tile objects in a quadrant: the shed is conceptual and accessed from four inner-corner standing tiles. The full farm therefore has 100 potentially productive cells.
- Locked cells are the string `LOCKED`. Unlocking replaces every locked cell in the purchased quadrant with `None`, so newly unlocked land starts empty and cannot already contain weeds.
- Any farmer or hand can move across quadrant boundaries. Movement onto locked cells is permitted, but productive operations there no-op. Once unlocked, all normal tile operations work immediately from the following turn.
- Weed spawning considers empty unlocked tiles at day end. Newly unlocked empty land can acquire weeds at later day boundaries.
