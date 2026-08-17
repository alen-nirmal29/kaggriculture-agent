"""V9 integration: V8 opponent model with configurable final labor cap."""
from dataclasses import replace
from agent_v4.endgame import is_final_day
from agent_v4.market import build_market_orders
from agent_v4.workers import assign_tasks,task_action,units
from agent_v6.animals import animal_tasks,format_animal_action,required_market_orders,structure_positions
from agent_v6.strategy import SAFE_ACTION,_crop_tasks
from agent_v8.opponent import OpponentHistory,adjusted_prices,parse_snapshot
from agent_v9.config import V9Config
from agent_v9.state import GameState
from agent_v9.workers import hiring_orders_v9

def _expanded_crop_tasks(state,capacity):
 from agent_v5.strategy import build_crop_plan,generate_tasks
 from agent_v4.workers import WorkTask
 from agent_v5 import crops
 plan=build_crop_plan(state,capacity);result=[]
 for task in generate_tasks(state,capacity,plan):
  tile=state.tile_at(task.target);crop=crops.crop_type(tile) or task.crop
  result.append(WorkTask(task.kind,task.target,task.priority,3 if task.kind=='HARVEST' else 0,float(state.market_prices.get(crop,0)) if crop else 0.0,task.crop))
 return plan,result

def decide(state:GameState,history:OpponentHistory,config:V9Config):
 snapshot=parse_snapshot(state,config.mode);history.update(snapshot)
 chosen=state if config.mode=='CONTROL' else replace(state,market_prices=adjusted_prices(state,history,config.mode,config.strength,config.horizon_days))
 proposed=tuple('COW' for _ in range(config.max_cows));positions=structure_positions(chosen,len(proposed));crop_capacity=max(12,min(config.managed_plots,len(chosen.unlocked_quadrants)*25-len(positions)))
 plan,crop_tasks=(_expanded_crop_tasks(chosen,crop_capacity) if config.buy_land else _crop_tasks(chosen,crop_capacity));empty={p:c for p,c in plan.targets.items() if chosen.tile_at(p).is_empty}
 market=build_market_orders(chosen,empty)
 if any(s.animal for s in chosen.structures):
  reserve=sum(1 for s in chosen.structures if s.animal);adjusted=[]
  for order in market:
   if order[:2]==['SELL','WHEAT']:
    n=max(0,int(order[2])-reserve)
    if n:adjusted.append(['SELL','WHEAT',n])
   else:adjusted.append(order)
  market=adjusted
 market+=required_market_orders(chosen,proposed,positions,chosen.day<29)
 tasks=crop_tasks+animal_tasks(chosen,proposed,positions,config.fertilizer);hires=hiring_orders_v9(chosen,config.max_hands,len(tasks)+len(empty))
 assignments=assign_tasks(chosen,tasks);active=units(chosen);actions=[]
 for unit in active:
  task=assignments.get(unit.index);actions.append(format_animal_action(chosen,unit,task) or task_action(chosen,unit,task))
 if is_final_day(chosen.day) and chosen.remaining_turns<4:hires=[]
 market=market+hires
 if config.buy_land and len(chosen.unlocked_quadrants)==1:
  from agent_v5.land import should_buy_next_land
  best=max((x.score for x in plan.scores.values()),default=0.0)
  if should_buy_next_land(chosen,1,config.managed_plots,best,0):market.append(['BUY_LAND'])
 market=[o for o in market if o and (config.buy_land or o[0]!='BUY_LAND')]
 return {'farmer':actions[0],'hands':actions[1:],'market':market}
