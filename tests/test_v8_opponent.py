from copy import deepcopy
from dataclasses import replace
import pytest
from kaggle_environments import make
from agent_v8.opponent import OpponentHistory,adjusted_prices,animal_pipeline,parse_snapshot,predicted_production,supply_pressure
from agent_v8.state import GameState
from main_v6 import agent as v6_agent
from main_v8 import make_agent

def with_opp(initial_observation,tiles=None,hands=None):
 o=deepcopy(initial_observation)
 if tiles:
  for (x,y),raw in tiles.items():o.farms[1].tiles[y][x]=raw
 if hands is not None:o.farms[1].hands=hands
 return GameState.from_observation(o)

def plant(crop,day=0,yield_units=1,watered=True):return {'kind':'PLANT','crop':crop,'planted_day':day,'yield_units':yield_units,'watered_today':watered,'consecutive_unwatered':0,'fertilized_until_day':-1}
def animal(kind,name):return {'kind':kind,'animal':name,'placed_day':0,'yield_units':1,'consecutive_unfed':0,'fed_today':True,'cared_today':True,'fertilizer_available':True}

def test_public_state_parser(initial_observation):
 s=with_opp(initial_observation,hands=[[1,1]]);assert s.opponent.player==1 and len(s.opponent.hands)==1 and s.opponent.money==3000
def test_no_private_opponent_field(initial_observation):assert not hasattr(with_opp(initial_observation).opponent,'private')
def test_crop_counts(initial_observation):assert parse_snapshot(with_opp(initial_observation,{(0,0):plant('CARROT')})).crops['CARROT']==1
def test_growth_pipeline(initial_observation):
 s=with_opp(initial_observation,{(0,0):plant('WHEAT',0,3)});assert parse_snapshot(replace(s,day=2),'PIPELINE').pipeline['WHEAT']>1
def test_structure_extraction(initial_observation):assert parse_snapshot(with_opp(initial_observation,{(0,0):{'kind':'COOP'}})).structures['COOP']==1
def test_animal_extraction(initial_observation):assert parse_snapshot(with_opp(initial_observation,{(0,0):animal('PASTURE','COW')})).animals['COW']==1
def test_worker_count(initial_observation):assert parse_snapshot(with_opp(initial_observation,hands=[[1,1],[2,2]])).workers==3
def test_history_tracking(initial_observation):
 s=with_opp(initial_observation);h=OpponentHistory(window=2);h.update(parse_snapshot(s));h.update(parse_snapshot(replace(s,step=1)));h.update(parse_snapshot(replace(s,step=2)));assert len(h.points)==2
def test_history_reset(initial_observation):
 s=with_opp(initial_observation);h=OpponentHistory();h.update(parse_snapshot(s));h.update(parse_snapshot(replace(s,step=1)));h.update(parse_snapshot(s));assert h.resets==1 and len(h.points)==1
def test_crop_pipeline(initial_observation):assert predicted_production(parse_snapshot(with_opp(initial_observation,{(0,0):plant('MELON')}),'PIPELINE'),'PIPELINE')['MELON']>0
def test_animal_pipeline(initial_observation):assert animal_pipeline(parse_snapshot(with_opp(initial_observation,{(0,0):animal('PASTURE','COW')})))['MILK']==.5
def test_confidence_increases(initial_observation):
 s=with_opp(initial_observation,{(0,0):plant('WHEAT')});h=OpponentHistory();h.update(parse_snapshot(s));low=h.confidence();[h.update(parse_snapshot(replace(s,step=i))) for i in range(1,7)];assert h.confidence()>low
def test_supply_pressure_bounded(initial_observation):
 s=with_opp(initial_observation,{(x,y):plant('CARROT') for y in range(5) for x in range(5)});h=OpponentHistory();[h.update(parse_snapshot(replace(s,step=i),'PIPELINE')) for i in range(6)];assert 0<supply_pressure(h.points[-1],h,'PIPELINE')['CARROT']<=1
def test_weak_signal_small_adjustment(initial_observation):
 s=with_opp(initial_observation,{(0,0):plant('CARROT')});h=OpponentHistory();h.update(parse_snapshot(s));assert abs(adjusted_prices(s,h,'PIPELINE')['CARROT']-s.market_prices['CARROT'])<=1
def test_strong_signal_changes_close_value(initial_observation):
 s=with_opp(initial_observation,{(x,y):plant('CARROT') for y in range(5) for x in range(5)});h=OpponentHistory();[h.update(parse_snapshot(replace(s,step=i),'PIPELINE')) for i in range(6)];assert adjusted_prices(replace(s,step=6),h,'PIPELINE',.2)['CARROT']<s.market_prices['CARROT']
def test_large_advantage_not_zeroed(initial_observation):
 s=with_opp(initial_observation,{(x,y):plant('MELON') for y in range(5) for x in range(5)});h=OpponentHistory();[h.update(parse_snapshot(replace(s,step=i),'PIPELINE')) for i in range(6)];assert adjusted_prices(replace(s,step=6),h,'PIPELINE',.2)['MELON']>=.8*s.market_prices['MELON']
def test_endgame_disables(initial_observation):
 s=replace(with_opp(initial_observation,{(0,0):plant('CARROT')}),step=700);h=OpponentHistory();h.update(parse_snapshot(s));assert adjusted_prices(s,h,'PIPELINE')==s.market_prices

@pytest.mark.parametrize('mode',['CONTROL','STATIC_SNAPSHOT','PIPELINE','FULL_OPPONENT'])
def test_modes_action(initial_observation,mode):assert set(make_agent(mode)(initial_observation))=={'farmer','hands','market'}
def test_control_equivalent(initial_observation):assert make_agent('CONTROL')(initial_observation)==v6_agent(initial_observation)
def test_feed_reserve_preserved(initial_observation):
 a=make_agent('FULL_OPPONENT')(initial_observation);assert not any(o[:2]==['SELL','WHEAT'] and o[2]>int(initial_observation.private.shed['WHEAT']) for o in a['market'])
def test_one_cow(initial_observation):assert sum(o[:2]==['BUY_ANIMAL','COW'] for o in make_agent('FULL_OPPONENT')(initial_observation)['market'])<=1
def test_no_land(initial_observation):assert not any(o[0]=='BUY_LAND' for o in make_agent('FULL_OPPONENT')(initial_observation)['market'])
def test_no_holding(initial_observation):assert make_agent('STATIC_SNAPSHOT')(initial_observation)['market']==v6_agent(initial_observation)['market']
def test_agent_reset(initial_observation):
 a=make_agent('PIPELINE');a(initial_observation);o=deepcopy(initial_observation);o.step=1;a(o);a(initial_observation);assert a.opponent_history.resets==1
def test_full_episode():
 e=make('kaggriculture',configuration={'seed':1180002},debug=True);e.run([make_agent('FULL_OPPONENT'),v6_agent]);assert len(e.steps)==720 and all(s.status=='DONE' for s in e.state)
