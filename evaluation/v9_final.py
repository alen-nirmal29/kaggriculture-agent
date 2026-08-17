"""Disjoint-seed V9 candidate evaluation against frozen V8."""
from __future__ import annotations
import argparse,json,statistics,sys,time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from kaggle_environments import make
from evaluation.v3_capacity import stats,wilson
from main_v8 import agent as v8_agent
from main_v9 import make_agent
from agent_v9.config import V9Config
from agent_v9.state import GameState
RESULTS=ROOT/'evaluation'/'results'

def one(args):
 i,seed,pos,cfg=args;agent=make_agent(V9Config(**cfg));times=[]
 def measured(obs,configuration=None):
  t=time.perf_counter();a=agent(obs);times.append(time.perf_counter()-t);return a
 agents=[v8_agent,v8_agent];agents[pos]=measured;e=make('kaggriculture',configuration={'seed':seed},debug=True);err=None
 try:e.run(agents)
 except Exception as x:err=f'{type(x).__name__}: {x}'
 a,b=e.state[pos],e.state[1-pos];ok=err is None and len(e.steps)==720 and a.status==b.status=='DONE';ar=float(a.reward) if a.reward is not None else None;br=float(b.reward) if b.reward is not None else None;final=GameState.from_observation(a.observation)
 return {'index':i,'seed':seed,'position':pos,'completed':ok,'winner':'V9' if ok and ar>br else 'V8' if ok and ar<br else 'DRAW' if ok else 'INVALID','v9_reward':ar,'v8_reward':br,'difference':ar-br if ar is not None and br is not None else None,'statuses':[a.status,b.status],'error':err,'hands_final':len(final.hands),'hires_today':final.hires_today,'unsold':final.shed_count+final.carried_count,'times':times}

def summary(es,cfg,label):
 v=[e for e in es if e['completed']];w=sum(e['winner']=='V9' for e in v);l=sum(e['winner']=='V8' for e in v);d=len(v)-w-l;ts=[x for e in es for x in e['times']];pos={}
 for p in (0,1):
  q=[e for e in v if e['position']==p];pos[str(p)]={'games':len(q),'wins':sum(e['winner']=='V9' for e in q),'losses':sum(e['winner']=='V8' for e in q),'draws':sum(e['winner']=='DRAW' for e in q)}
 return {'metadata':{'label':label,'config':cfg,'matched':True,'balanced':True},'summary':{'games':len(es),'completed':len(v),'v9_wins':w,'v8_wins':l,'draws':d,'decisive_win_rate':w/(w+l) if w+l else 0},'confidence_interval':wilson(w,w+l),'position_results':pos,'rewards':{'v9':stats([e['v9_reward'] for e in v]),'v8':stats([e['v8_reward'] for e in v]),'difference':stats([e['difference'] for e in v])},'operations':{'unsold':statistics.fmean(e['unsold'] for e in v) if v else 0},'reliability':{'completed':len(v),'crashes':sum('ERROR' in e['statuses'] for e in es),'timeouts':sum('TIMEOUT' in e['statuses'] for e in es)},'timing':{**stats(ts),'p95':sorted(ts)[int(.95*(len(ts)-1))] if ts else 0,'p99':sorted(ts)[int(.99*(len(ts)-1))] if ts else 0,'over100ms':sum(x>.1 for x in ts),'over500ms':sum(x>.5 for x in ts),'decisions':len(ts)},'episodes':[{k:x for k,x in e.items() if k!='times'} for e in es]}
def run(cfg,games,base,workers,label):
 args=[(i,base+i//2,i%2,cfg) for i in range(games)]
 with ProcessPoolExecutor(max_workers=workers) as p:es=list(p.map(one,args,chunksize=1))
 return summary(es,cfg,label)
def save(n,x):(RESULTS/n).write_text(json.dumps(x,indent=2),encoding='utf-8')
def main():
 p=argparse.ArgumentParser();p.add_argument('phase',choices=('labor','interactions','nearby-strength','nearby-horizon','validation','holdout'));p.add_argument('--games',type=int,default=100);p.add_argument('--workers',type=int,default=4);p.add_argument('--strength',type=float,default=.075);p.add_argument('--horizon',type=int,default=3);a=p.parse_args()
 base={'labor':1290000,'interactions':1290100,'nearby-strength':1290200,'nearby-horizon':1290400,'validation':1390000,'holdout':1490000}[a.phase]
 if a.phase=='labor':save('v9_labor_sweep.json',{'candidates':{str(n):run({'max_hands':n},a.games,base+n*1000,a.workers,f'hands-{n}') for n in (4,5,6)}})
 elif a.phase=='interactions':
  save('v9_interaction_sweep.json',{'one_cow':run({'max_hands':6},a.games,base,a.workers,'six-hands-one-cow'),'two_cows':run({'max_hands':6,'max_cows':2},a.games,base+1000,a.workers,'six-hands-two-cows'),'first_land':run({'max_hands':6,'buy_land':True,'managed_plots':49},a.games,base+2000,a.workers,'six-hands-first-land')})
 elif a.phase=='nearby-strength':
  save('v9_strength_refinement.json',{'candidates':{str(s):run({'max_hands':6,'strength':s,'horizon_days':4},a.games,base+int(s*10000),a.workers,f'strength-{s}') for s in (.075,.10,.125)}})
 elif a.phase=='nearby-horizon':
  save('v9_horizon_refinement.json',{'strength':a.strength,'candidates':{str(h):run({'max_hands':6,'strength':a.strength,'horizon_days':h},a.games,base+h*100,a.workers,f'horizon-{h}') for h in (3,4,5)}})
 elif a.phase=='validation':
  save('v9_validation.json',run({'max_hands':6,'strength':a.strength,'horizon_days':a.horizon},a.games,base,a.workers,'V9-refined-validation'))
 else:save('v9_final_holdout.json',run({'max_hands':6,'strength':a.strength,'horizon_days':a.horizon},a.games,base,a.workers,'final-holdout'))
if __name__=='__main__':main()
