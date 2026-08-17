"""V8 worker primitives with a V9-only configurable economic hand cap."""
from agent_v4.workers import *  # noqa: F401,F403
from agent_v4.workers import hire_cost

def hiring_orders_v9(state,max_hands,estimated_work,cash_reserve=200.0):
 if not 0<=max_hands<=6:raise ValueError('max_hands must be between 0 and 6')
 current=len(state.hands);slots=max(0,max_hands-current)
 if slots==0 or state.remaining_turns<=2 or state.hour>=22:return []
 orders=[];money=state.money;useful=min(23-state.hour,state.remaining_turns-1)
 for offset in range(slots):
  cost=hire_cost(state.hires_today+offset);marginal=max(0,estimated_work-(current+len(orders)+1));value=min(useful,marginal)*2.0
  if useful<=0 or marginal<=0 or value<=cost or money-cost<cash_reserve:break
  orders.append(['HIRE']);money-=cost
 return orders
