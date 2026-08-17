"""Matched-seed V5 land-cap evaluation against frozen V4."""
from __future__ import annotations
import argparse,json,statistics,sys,time
from collections import Counter
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from kaggle_environments import make
from evaluation.v3_capacity import stats,wilson
from main_v4 import agent as v4_agent
from main_v5 import make_agent
from agent_v5.strategy import decide
from agent_v5.land import LAND_COSTS
from agent_v5.state import GameState
from agent_v5.strategy import select_managed_tiles
from agent_v5 import crops

RESULTS=ROOT/'evaluation'/'results'; CONTROL=RESULTS/'v5_land_control.json'; SWEEP=RESULTS/'v5_land_sweep.json'; FINAL=RESULTS/'v5_vs_v4.json'
SEED=860_000; FINAL_SEED=880_000; MOVE={'NORTH','SOUTH','EAST','WEST'}; PROD={'DIG','PLANT','WATER','HARVEST'}

class Measured:
 def __init__(self,cap,capacity): self.f=make_agent(cap,capacity);self.t=[];self.c=Counter();self.i=Counter();self.purchase_turns=[]
 def __call__(self,obs,configuration=None):
  s=GameState.from_observation(obs);a0=time.perf_counter();a=self.f(obs);self.t.append(time.perf_counter()-a0)
  self.c['managed_sum']+=len(select_managed_tiles(s,min(100,max(24,len(s.unlocked_quadrants)*25-1))))
  hands=a.get('hands',[]);self.c['available']+=len(s.hands)
  for x in hands[:len(s.hands)]:
   op=x[0] if x else 'PASS';self.c['nonidle']+=op!='PASS';self.c['idle']+=op=='PASS';self.c['productive']+=op in PROD
  buys=sum(o==['BUY_LAND'] for o in a.get('market',[]))
  for j in range(buys):
   idx=len(s.unlocked_quadrants)-1+j
   if idx<len(LAND_COSTS): self.c['land_spend']+=LAND_COSTS[idx];self.purchase_turns.append(s.step)
  self.c['expansion_orders']+=buys
  self.c['hire_cost_proxy']+=sum(o==['HIRE'] for o in a.get('market',[]))
  for p in select_managed_tiles(s,min(100,max(24,len(s.unlocked_quadrants)*25-1))):
   tile=s.tile_at(p);self.i['mature']+=crops.is_harvestable(tile,s.day);self.i['unwatered']+=s.hour==23 and crops.needs_water(tile);self.i['weed']+=crops.is_weed(tile)
  return a

def episode(idx,seed,cap,pos,capacity):
 m=Measured(cap,capacity);agents=[v4_agent,v4_agent];agents[pos]=m;e=make('kaggriculture',configuration={'seed':seed},debug=True);err=None
 try:e.run(agents)
 except Exception as x:err=f'{type(x).__name__}: {x}'
 a,b=e.state[pos],e.state[1-pos];ok=err is None and len(e.steps)==720 and a.status==b.status=='DONE';ar=float(a.reward) if a.reward is not None else None;br=float(b.reward) if b.reward is not None else None
 winner='V5' if ok and ar>br else 'V4' if ok and ar<br else 'DRAW' if ok else 'INVALID';final=GameState.from_observation(a.observation);exp=len(final.unlocked_quadrants)-1
 return {'game_index':idx,'seed':seed,'v5_position':pos,'winner':winner,'completed':ok,'v5_reward':ar,'v4_reward':br,'difference':ar-br if ar is not None and br is not None else None,'v5_status':a.status,'v4_status':b.status,'error':err,'expansions':exp,'purchase_turns':m.purchase_turns,'metrics':dict(m.c),'indicators':{**m.i,'unsold':final.carried_count+final.shed_count}},m.t

def summary(es,ts,label):
 v=[e for e in es if e['completed']];w=sum(e['winner']=='V5' for e in v);l=sum(e['winner']=='V4' for e in v);d=len(v)-w-l;counts=Counter(e['expansions'] for e in v)
 positions={}
 for p in (0,1):
  q=[e for e in v if e['v5_position']==p];pw=sum(e['winner']=='V5' for e in q);pl=sum(e['winner']=='V4' for e in q);positions[str(p)]={'games':len(q),'wins':pw,'losses':pl,'draws':len(q)-pw-pl,'win_rate':pw/len(q) if q else 0}
 def means(key,group='metrics'):return stats([float(e[group].get(key,0)) for e in v])
 turns={str(n):stats([float(e['purchase_turns'][n]) for e in v if len(e['purchase_turns'])>n]) for n in range(3)}
 available=sum(e['metrics'].get('available',0) for e in v);non=sum(e['metrics'].get('nonidle',0) for e in v)
 return {'metadata':{'label':label,'matched_seeds':True,'balanced_positions':True,'v4_frozen':True},'summary':{'games':len(es),'completed':len(v),'v5_wins':w,'v4_wins':l,'draws':d,'decisive_win_rate':w/(w+l) if w+l else 0},'position_results':positions,'confidence_interval':wilson(w,w+l),'rewards':{'v5':stats([e['v5_reward'] for e in v]),'v4':stats([e['v4_reward'] for e in v]),'difference':stats([e['difference'] for e in v])},'land':{'expansions':stats([float(e['expansions']) for e in v]),'distribution':{str(n):counts[n] for n in range(4)},'purchase_turns':turns,'spend':means('land_spend'),'managed_plots':{'mean':statistics.fmean(e['metrics'].get('managed_sum',0)/719 for e in v) if v else 0}},'workers':{'utilization':non/available if available else 0,'idle':means('idle'),'productive':means('productive')},'operations':{'mature':means('mature','indicators'),'unwatered':means('unwatered','indicators'),'weed':means('weed','indicators'),'unsold':means('unsold','indicators')},'reliability':{'attempted':len(es),'completed':len(v),'crashes':sum(e['v5_status']=='ERROR' or e['v4_status']=='ERROR' for e in es),'timeouts':sum(e['v5_status']=='TIMEOUT' or e['v4_status']=='TIMEOUT' for e in es)},'timing':{**stats(ts),'decisions':len(ts),'over100ms':sum(x>.1 for x in ts),'over500ms':sum(x>.5 for x in ts)},'episodes':es}

def block(cap,start,games,capacity,seed0):
 es=[];ts=[]
 for idx in range(start,start+games):
  e,t=episode(idx,seed0+idx//2,cap,idx%2,capacity);es.append(e);ts+=t
  if (idx-start+1)%10==0:print(f'{idx-start+1}/{games}',flush=True)
 return {'episodes':es,'timings':ts}
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2),encoding='utf-8')
def run_policy(cap):
 b=block(cap,0,100,48,SEED);r=summary(b['episodes'],b['timings'],f'V5-{cap}-vs-V4')
 if cap==0:save(CONTROL,r)
 else:
  p=json.loads(SWEEP.read_text()) if SWEEP.exists() else {'metadata':{'games_per_cap':100,'same_seeds':True},'caps':{}}
  p['caps'][str(cap)]=r;save(SWEEP,p)
def fixed_policy(turn):
 def f(obs):
  s=GameState.from_observation(obs);a=decide(s,0,48)
  if s.step==turn and len(s.unlocked_quadrants)==1:a['market'].append(['BUY_LAND'])
  return a
 return f
def fixed_episode(idx,seed,turn,pos):
 global make_agent
 original=make_agent
 try:
  make_agent=lambda cap,capacity:fixed_policy(turn)
  return episode(idx,seed,1,pos,48)
 finally:make_agent=original
def run_fixed(turn):
 es=[];ts=[]
 for idx in range(50):
  e,t=fixed_episode(idx,SEED+1000+idx//2,turn,idx%2);es.append(e);ts+=t
  if (idx+1)%10==0:print(f'{idx+1}/50',flush=True)
 r=summary(es,ts,f'fixed-{turn}-vs-V4');p=json.loads(SWEEP.read_text());p.setdefault('fixed_timing',{})[str(turn)]=r;save(SWEEP,p)
def final_part(cap,capacity,start):save(RESULTS/f'v5_vs_v4_part_{start:03d}.json',block(cap,start,50,capacity,FINAL_SEED))
def merge(cap,capacity):
 es=[];ts=[]
 for start in range(0,500,50):b=json.loads((RESULTS/f'v5_vs_v4_part_{start:03d}.json').read_text());es+=b['episodes'];ts+=b['timings']
 es.sort(key=lambda e:e['game_index']);assert [e['game_index'] for e in es]==list(range(500));r=summary(es,ts,'V5-final');r['metadata'].update(max_expansions=cap,capacity=capacity);save(FINAL,r)
def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=('policy','fixed','final-part','merge'));p.add_argument('--cap',type=int,required=True);p.add_argument('--capacity',type=int,default=48);p.add_argument('--start',type=int,default=0);p.add_argument('--turn',type=int,default=24);a=p.parse_args()
 if a.mode=='policy':run_policy(a.cap)
 elif a.mode=='fixed':run_fixed(a.turn)
 elif a.mode=='final-part':final_part(a.cap,a.capacity,a.start)
 else:merge(a.cap,a.capacity)
if __name__=='__main__':main()
