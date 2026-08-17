from copy import deepcopy
import pytest
from kaggle_environments import make
from agent_v4.workers import Unit, WorkTask, assign_tasks
from agent_v6.animals import animal_roi, animal_tasks, configured_species, format_animal_action, production_cycles
from agent_v6.state import GameState
from main_v6 import make_agent

def observed_with(initial_observation, raw):
    obs=deepcopy(initial_observation); obs.farms[0].tiles[0][0]=raw; return GameState.from_observation(obs)

@pytest.mark.parametrize("animal,kind",[("GOOSE","COOP"),("COW","PASTURE"),("SHEEP","PASTURE")])
def test_animal_observation_parsing(initial_observation,animal,kind):
    s=observed_with(initial_observation,{"kind":kind,"animal":animal,"placed_day":0,"yield_units":2,"consecutive_unfed":1,"fed_today":True,"cared_today":False,"fertilizer_available":True})
    a=s.structures[0]; assert (a.animal,a.kind,a.yield_units,a.consecutive_unfed,a.fed_today,a.fertilizer_available)==(animal,kind,2,1,True,True)

@pytest.mark.parametrize("kind",["COOP","PASTURE"])
def test_empty_structure_parsing(initial_observation,kind):
    assert observed_with(initial_observation,{"kind":kind}).structures[0].animal is None

@pytest.mark.parametrize("mode,expected",[("NONE",()),("GOOSE_ONLY",("GOOSE",)),("COW_ONLY",("COW","COW")),("SHEEP_ONLY",("SHEEP",))])
def test_configuration(mode,expected): assert configured_species(mode,{"GOOSE":1,"COW":2,"SHEEP":1})==expected

@pytest.mark.parametrize("kind,crop,expected",[
 ("BUILD_COOP",None,["BUILD_COOP"]),("BUILD_PASTURE",None,["BUILD_PASTURE"]),
 ("PICKUP_ANIMAL","COW",["PICKUP","COW","1"]),("PLACE_ANIMAL","COW",["PLACE","COW"]),
 ("PICKUP_FEED",None,["PICKUP","WHEAT","1"]),("FEED",None,["FEED"]),
 ("CARE",None,["CARE"]),("COLLECT_FERTILIZER",None,["COLLECT_FERTILIZER"]),
 ("PICKUP_FERTILIZER",None,["PICKUP","FERTILIZER","1"]),])
def test_animal_action_formats(initial_observation,kind,crop,expected):
    s=GameState.from_observation(initial_observation);u=Unit(0,s.farmer,0);t=WorkTask(kind,s.farmer,1,crop=crop)
    assert format_animal_action(s,u,t)==expected

def test_roi_remaining_season(): assert animal_roi("COW",0,{}).expected_value>animal_roi("COW",20,{}).expected_value
def test_roi_has_structure_cost(): assert animal_roi("COW",0,{},structure_cost=50).expected_value==animal_roi("COW",0,{}).expected_value-50
def test_roi_has_feed_cost(): assert animal_roi("COW",0,{"WHEAT":100}).feed_cost>animal_roi("COW",0,{"WHEAT":1}).feed_cost
def test_roi_has_crop_opportunity(): assert animal_roi("COW",0,{},crop_opportunity_cost=900).expected_value<animal_roi("COW",0,{},crop_opportunity_cost=0).expected_value
def test_late_purchase_rejected(): assert animal_roi("COW",29,{}).expected_value<0 and production_cycles("COW",29)==0

def test_duplicate_animal_task_prevented(initial_observation):
    s=GameState.from_observation(initial_observation);p=s.farmer;tasks=[WorkTask("FEED",p,150),WorkTask("CARE",p,50)]
    assigned=assign_tasks(s,tasks);assert sum(t is not None for t in assigned.values())==1

def test_feed_survival_priority(initial_observation):
    s=observed_with(initial_observation,{"kind":"PASTURE","animal":"COW","placed_day":0,"yield_units":2,"consecutive_unfed":1,"fed_today":False,"cared_today":False,"fertilizer_available":True})
    obs=deepcopy(s.observation);obs.private.shed["WHEAT"]=1;s=GameState.from_observation(obs)
    assert animal_tasks(s,("COW",),((0,0),))[0].kind=="PICKUP_FEED"

def test_control_uses_no_animals(initial_observation):
    a=make_agent("NONE")(initial_observation);assert not any(o and o[0]=="BUY_ANIMAL" for o in a["market"])

def test_animal_purchase_format(initial_observation):
    a=make_agent("COW_ONLY",{"COW":1})(initial_observation);assert ["BUY_ANIMAL","COW",1] in a["market"]

def test_full_v6_episode():
    from main_v4 import agent as v4
    e=make("kaggriculture",configuration={"seed":996001},debug=True);e.run([make_agent("COW_ONLY",{"COW":1},True),v4])
    assert len(e.steps)==720 and all(s.status=="DONE" for s in e.state)
