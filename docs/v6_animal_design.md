# V6 animal design

V6 starts from frozen V4. Control mode directly calls V4 decision logic. Livestock state, payback estimates, task creation, placement, feed survival, products, and fertilizer are isolated in `agent_v6/animals.py`; unchanged crop, worker, route, market, and endgame modules remain V4-derived.

The ROI gate is deliberately explainable: realizable product cycles at live product price, plus optional fertilizer value, minus animal cash cost, zero official structure cash cost, daily wheat at live price, an action-value labor proxy, and a crop-tile opportunity charge. Remaining cycles use the actual first-yield delay, interval, and Day 30 boundary. A non-positive late purchase is rejected. Existing animals remain feed-priority obligations even when current feed economics deteriorate.

Structure cells are deterministic tail cells of V4's NW 5x5 route. They are removed from crop management, so tile loss is real. Animal tasks join V4's reservation scheduler. Feed outranks all other work; harvest and setup follow; care and fertilizer are lower. Owner constraints bind carried wheat, animals, or fertilizer to the correct unit and tile reservation prevents duplicate service.

Feed comes from retained farm wheat first and `BUY_PRODUCT WHEAT` only covers an immediate shortfall. V6 reserves one shed wheat per living animal instead of selling and rebuying it. The hand ceiling stays four. Near the end, the ROI horizon stops new purchases; existing animals are fed and final products are sold.

Configurations are `NONE`, `GOOSE_ONLY`, `COW_ONLY`, `SHEEP_ONLY`, and `MIXED`, with per-species caps. Mixed is an experimental option only and is not enabled by the selected policy.
