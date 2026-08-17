from copy import deepcopy
from dataclasses import replace
import pytest
from kaggle_environments import make
from agent_v7.market import MarketHistory,expected_future_price,liquidity_safe,market_signal,should_hold
from agent_v7.state import GameState
from agent_v7.strategy import _production_state
from agent_v7.town import SHOPS,demand_pressure,expected_consumption,expected_town_demand,turns_until_next_demand
from main_v6 import agent as v6_agent
from main_v7 import make_agent

def state(obs):return GameState.from_observation(obs)

def test_market_state_parsing(initial_observation):
 assert state(initial_observation).market_inventory['WHEAT']==10000
def test_town_state_parsing(initial_observation):assert state(initial_observation).town_shops==()
def test_town_mapping():assert SHOPS['PIZZA_SHOP']==('MILK','TOMATO','WHEAT')
def test_demand_timing():assert turns_until_next_demand(5)==3 and turns_until_next_demand(8)==0
def test_exact_shop_demand():assert expected_consumption(('YARN_STORE',),'WOOL',1,7)==4
def test_town_demand_map():assert expected_town_demand(('PET_CAFE',),1,7)['CARROT']==4
def test_demand_pressure():assert demand_pressure(('YARN_STORE',),'WOOL',1,7,10)==.4

def test_history_storage(initial_observation):
 h=MarketHistory(window=2);s=state(initial_observation);h.update(s);h.update(replace(s,step=1));h.update(replace(s,step=2));assert len(h.points)==2
def test_history_reset(initial_observation):
 h=MarketHistory();s=state(initial_observation);h.update(s);h.update(replace(s,step=1));h.update(s);assert len(h.points)==1 and h.resets==1
def test_inventory_trend(initial_observation):
 h=MarketHistory();s=state(initial_observation);h.update(s);inv=dict(s.market_inventory);inv['MILK']-=10;h.update(replace(s,step=1,market_inventory=inv));assert h.inventory_trend('MILK')==-10
def test_price_trend(initial_observation):
 h=MarketHistory();s=state(initial_observation);h.update(s);p=dict(s.market_prices);p['MILK']+=5;h.update(replace(s,step=1,market_prices=p));assert h.price_trend('MILK')==5

def test_feed_wheat_protected(initial_observation):
 s=replace(state(initial_observation),shed={'WHEAT':2});assert not liquidity_safe(s,'WHEAT',1)
def test_holding_rejected_low_cash(initial_observation):
 s=replace(state(initial_observation),money=10,town_shops=('YARN_STORE',));assert not should_hold(s,MarketHistory(),'WOOL',1)
def test_holding_rejected_endgame(initial_observation):
 s=replace(state(initial_observation),step=700,town_shops=('YARN_STORE',));assert not should_hold(s,MarketHistory(),'WOOL',1)
def test_holding_accepted_when_clear(initial_observation):
 s=state(initial_observation);inv=dict(s.market_inventory);inv['WOOL']=10;s=replace(s,town_shops=('YARN_STORE',),market_inventory=inv,shed={'WOOL':1},money=1000)
 assert should_hold(s,MarketHistory(),'WOOL',1,horizon=24,threshold=.05)
def test_production_forecast_adjusts_prices(initial_observation):
 s=state(initial_observation);inv=dict(s.market_inventory);inv['WHEAT']=10
 s=replace(s,town_shops=('FARMERS_MARKET',),market_inventory=inv);h=MarketHistory();h.update(s)
 assert _production_state(s,h,24).market_prices!=s.market_prices

@pytest.mark.parametrize('mode',['CONTROL','SELL_INTELLIGENCE','PRODUCTION_INTELLIGENCE','FULL_INTELLIGENCE'])
def test_modes_complete_action(initial_observation,mode):
 a=make_agent(mode)(initial_observation);assert set(a)=={'farmer','hands','market'}
def test_control_matches_v6(initial_observation):assert make_agent('CONTROL')(initial_observation)==v6_agent(initial_observation)
def test_no_land_order(initial_observation):assert not any(o[0]=='BUY_LAND' for o in make_agent('FULL_INTELLIGENCE')(initial_observation)['market'])
def test_cow_count_max_one(initial_observation):assert sum(o[:2]==['BUY_ANIMAL','COW'] for o in make_agent('FULL_INTELLIGENCE')(initial_observation)['market'])<=1
def test_agent_history_resets(initial_observation):
 a=make_agent();a(initial_observation);o=deepcopy(initial_observation);o.step=1;a(o);a(initial_observation);assert a.market_history.resets==1
def test_full_episode():
 e=make('kaggriculture',configuration={'seed':997002},debug=True);e.run([make_agent('FULL_INTELLIGENCE'),v6_agent]);assert len(e.steps)==720 and all(s.status=='DONE' for s in e.state)
