"""Matched-seed V8 opponent-model evaluation against frozen V6."""
from __future__ import annotations
import argparse,json,statistics,sys,time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from kaggle_environments import make
from evaluation.v3_capacity import stats,wilson
from main_v6 import agent as v6_agent
from main_v8 import make_agent
from agent_v8.opponent import parse_snapshot,predicted_production,supply_pressure
from agent_v8.state import GameState
RESULTS=ROOT/'evaluation'/'results';SEED=1_180_000;CROPS=('WHEAT','CARROT','TOMATO','STRAWBERRY','MELON')

class Measured:
 def __init__(self,mode,strength,horizon):self.f=make_agent(mode,strength,horizon);self.base=make_agent('CONTROL');self.t=[];self.c=Counter();self.mode=mode
 def __call__(self,obs,configuration=None):
  s=GameState.from_observation(obs);base=self.base(obs);t=time.perf_counter();a=self.f(obs);self.t.append(time.perf_counter()-t)
  snap=parse_snapshot(s,self.mode);pred=predicted_production(snap,self.mode);press=supply_pressure(snap,self.f.opponent_history,self.mode);self.c['observations']+=1;self.c['confidence']+=self.f.opponent_history.confidence();self.c['workers_seen']+=snap.workers;self.c['active_seen']+=snap.active_tiles
  for p in CROPS:self.c['opp_'+p]+=snap.crops.get(p,0);self.c['pred_'+p]+=pred.get(p,0);self.c['pressure_'+p]+=press.get(p,0)
  aa=[a.get('farmer',['PASS'])]+a.get('hands',[]);bb=[base.get('farmer',['PASS'])]+base.get('hands',[])
  for x,y in zip(aa,bb):
   if x!=y and ((x and x[0]=='PLANT') or (y and y[0]=='PLANT')):
    self.c['changed']+=1
    if x and x[0]=='PLANT':self.c['changed_to_'+x[1]]+=1
   if x and x[0]=='PLANT':self.c['plant_'+x[1]]+=1
  self.c['available']+=len(aa);self.c['nonidle']+=sum(x and x[0]!='PASS' for x in aa)
  for o in a.get('market',[]):self.c['land']+=bool(o and o[0]=='BUY_LAND');self.c['cows']+=int(o[2]) if o and o[:2]==['BUY_ANIMAL','COW'] else 0
  for tile in s.iter_tiles():
   raw=tile.raw;self.c['weed']+=int(isinstance(raw,dict) and raw.get('kind')=='WEED')
   if isinstance(raw,dict) and raw.get('kind')=='PLANT':self.c['waiting']+=int(raw.get('yield_units',0)>0);self.c['unwatered']+=int(s.hour==23 and not raw.get('watered_today',False))
  return a

def one(args):
 idx,seed,mode,strength,horizon,pos=args;m=Measured(mode,strength,horizon);agents=[v6_agent,v6_agent];agents[pos]=m;e=make('kaggriculture',configuration={'seed':seed},debug=True);err=None
 try:e.run(agents)
 except Exception as x:err=f'{type(x).__name__}: {x}'
 a,b=e.state[pos],e.state[1-pos];ok=err is None and len(e.steps)==720 and a.status==b.status=='DONE';ar=float(a.reward) if a.reward is not None else None;br=float(b.reward) if b.reward is not None else None;final=GameState.from_observation(a.observation)
 return {'index':idx,'seed':seed,'position':pos,'completed':ok,'winner':'V8' if ok and ar>br else 'V6' if ok and ar<br else 'DRAW' if ok else 'INVALID','v8_reward':ar,'v6_reward':br,'difference':ar-br if ar is not None and br is not None else None,'error':err,'status':[a.status,b.status],'metrics':{**m.c,'unsold':final.shed_count+final.carried_count,'history_resets':m.f.opponent_history.resets},'timings':m.t}

def summarize(es,label,mode,strength,horizon):
 v=[e for e in es if e['completed']];w=sum(e['winner']=='V8' for e in v);l=sum(e['winner']=='V6' for e in v);d=len(v)-w-l;ts=[x for e in es for x in e['timings']]
 def mm(k):return statistics.fmean(e['metrics'].get(k,0) for e in v) if v else 0
 obs=sum(e['metrics'].get('observations',0) for e in v) or 1;pos={}
 for p in (0,1):
  q=[e for e in v if e['position']==p];pos[str(p)]={'games':len(q),'wins':sum(e['winner']=='V8' for e in q),'losses':sum(e['winner']=='V6' for e in q),'draws':sum(e['winner']=='DRAW' for e in q)}
 return {'metadata':{'label':label,'mode':mode,'strength':strength,'horizon_days':horizon,'matched_seeds':True,'balanced_positions':True,'v6_frozen':True},'summary':{'games':len(es),'completed':len(v),'v8_wins':w,'v6_wins':l,'draws':d,'decisive_win_rate':w/(w+l) if w+l else 0},'confidence_interval':wilson(w,w+l),'position_results':pos,'rewards':{'v8':stats([e['v8_reward'] for e in v]),'v6':stats([e['v6_reward'] for e in v]),'difference':stats([e['difference'] for e in v])},'opponent':{'crop_counts':{p:sum(e['metrics'].get('opp_'+p,0) for e in v)/obs for p in CROPS},'predicted':{p:sum(e['metrics'].get('pred_'+p,0) for e in v)/obs for p in CROPS},'pressure':{p:sum(e['metrics'].get('pressure_'+p,0) for e in v)/obs for p in CROPS},'confidence':sum(e['metrics'].get('confidence',0) for e in v)/obs,'workers':sum(e['metrics'].get('workers_seen',0) for e in v)/obs,'active_tiles':sum(e['metrics'].get('active_seen',0) for e in v)/obs},'response':{'changed':mm('changed'),'changed_to':{p:mm('changed_to_'+p) for p in CROPS}},'crop_mix':{p:mm('plant_'+p) for p in CROPS},'operations':{k:mm(k) for k in ('waiting','unwatered','weed','unsold','land','cows','history_resets')},'workers':{'utilization':sum(e['metrics'].get('nonidle',0) for e in v)/max(1,sum(e['metrics'].get('available',0) for e in v))},'reliability':{'attempted':len(es),'completed':len(v),'crashes':sum('ERROR' in e['status'] for e in es),'timeouts':sum('TIMEOUT' in e['status'] for e in es)},'timing':{**stats(ts),'decisions':len(ts),'over100ms':sum(x>.1 for x in ts),'over500ms':sum(x>.5 for x in ts)},'episodes':[{k:x for k,x in e.items() if k!='timings'} for e in es]}

def run(mode,games,strength,horizon,workers,seed=SEED):
 args=[(i,seed+i//2,mode,strength,horizon,i%2) for i in range(games)]
 with ProcessPoolExecutor(max_workers=workers) as pool:es=list(pool.map(one,args,chunksize=1))
 return summarize(es,'V8-'+mode,mode,strength,horizon)
def save(n,x):(RESULTS/n).write_text(json.dumps(x,indent=2),encoding='utf-8')
def selfplay_one(args):
 i,seed=args;e=make('kaggriculture',configuration={'seed':seed},debug=True);err=None
 try:e.run([make_agent('FULL_OPPONENT'),make_agent('FULL_OPPONENT')])
 except Exception as x:err=f'{type(x).__name__}: {x}'
 return {'index':i,'seed':seed,'completed':err is None and len(e.steps)==720 and all(s.status=='DONE' for s in e.state),'statuses':[s.status for s in e.state],'rewards':[s.reward for s in e.state],'error':err}
def selfplay(games,workers):
 with ProcessPoolExecutor(max_workers=workers) as p:es=list(p.map(selfplay_one,[(i,SEED+90_000+i) for i in range(games)]))
 return {'summary':{'games':games,'completed':sum(e['completed'] for e in es),'crashes':sum('ERROR' in e['statuses'] for e in es),'timeouts':sum('TIMEOUT' in e['statuses'] for e in es)},'episodes':es}
def main():
 p=argparse.ArgumentParser();p.add_argument('phase',choices=('modes','strength','horizon','selfplay','final'));p.add_argument('--games',type=int,default=100);p.add_argument('--workers',type=int,default=4);p.add_argument('--mode',default='CONTROL');p.add_argument('--strength',type=float,default=.10);p.add_argument('--horizon',type=int,default=4);a=p.parse_args()
 if a.phase=='modes':
  names={'CONTROL':'v8_control.json','STATIC_SNAPSHOT':'v8_static_snapshot.json','PIPELINE':'v8_pipeline.json','FULL_OPPONENT':'v8_full_opponent.json'}
  for j,(m,n) in enumerate(names.items()):save(n,run(m,a.games,a.strength,a.horizon,a.workers,SEED+j*10_000))
 elif a.phase=='strength':save('v8_strength_sweep.json',{'mode':a.mode,'strengths':{str(x):run(a.mode,a.games,x,a.horizon,a.workers,SEED+int(x*100000)) for x in (.05,.10,.20)}})
 elif a.phase=='horizon':save('v8_horizon_sweep.json',{'mode':a.mode,'horizons':{str(x):run(a.mode,a.games,a.strength,x,a.workers,SEED+x*1000) for x in (2,4,8)}})
 elif a.phase=='selfplay':save('v8_selfplay.json',selfplay(a.games,a.workers))
 else:save('v8_vs_v6.json',run(a.mode,a.games,a.strength,a.horizon,a.workers,SEED+100_000))
if __name__=='__main__':main()
