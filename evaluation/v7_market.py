"""Matched-seed V7 market-intelligence evaluation against frozen V6."""
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
from main_v7 import make_agent
from agent_v7.state import GameState
RESULTS=ROOT/'evaluation'/'results';SEED=1_070_000;CROPS={"WHEAT","CARROT","TOMATO","STRAWBERRY","MELON"};MOVE={"NORTH","SOUTH","EAST","WEST"}

class Measured:
 def __init__(self,mode,horizon,threshold):self.f=make_agent(mode,horizon,threshold);self.base=make_agent("CONTROL");self.t=[];self.c=Counter();self.mode=mode;self.last=None
 def __call__(self,obs,configuration=None):
  s=GameState.from_observation(obs);base=self.base(obs);t=time.perf_counter();a=self.f(obs);self.t.append(time.perf_counter()-t);self.last=s
  baseline_sells={(o[1],int(o[2])) for o in base.get('market',[]) if o and o[0]=='SELL'};actual_sells={(o[1],int(o[2])) for o in a.get('market',[]) if o and o[0]=='SELL'}
  held=baseline_sells-actual_sells
  for p,n in held:self.c['units_held']+=n;self.c['hold_events']+=1;self.c['milk_held']+=n*(p=='MILK')
  for o in a.get('market',[]):
   if o and o[0]=='SELL':self.c['units_sold']+=int(o[2]);self.c['sale_value']+=int(o[2])*int(s.market_prices.get(o[1],0));self.c['milk_sold']+=int(o[2])*(o[1]=='MILK')
   self.c['land_orders']+=bool(o and o[0]=='BUY_LAND');self.c['cow_orders']+=int(o[2]) if o and o[:2]==['BUY_ANIMAL','COW'] else 0
  acts=[a.get('farmer',['PASS'])]+a.get('hands',[]);self.c['available']+=len(acts);self.c['nonidle']+=sum(x and x[0]!='PASS' for x in acts)
  for x in acts:
   if x and x[0]=='PLANT':self.c['plant_'+x[1]]+=1
  for tile in s.iter_tiles():
   raw=tile.raw;self.c['weed']+=int(isinstance(raw,dict) and raw.get('kind')=='WEED')
   if isinstance(raw,dict) and raw.get('kind')=='PLANT':self.c['waiting']+=int(raw.get('yield_units',0)>0);self.c['unwatered']+=int(s.hour==23 and not raw.get('watered_today',False))
  return a

def one(args):
 idx,seed,mode,horizon,threshold,pos=args;m=Measured(mode,horizon,threshold);agents=[v6_agent,v6_agent];agents[pos]=m;e=make('kaggriculture',configuration={'seed':seed},debug=True);err=None
 try:e.run(agents)
 except Exception as x:err=f'{type(x).__name__}: {x}'
 a,b=e.state[pos],e.state[1-pos];ok=err is None and len(e.steps)==720 and a.status==b.status=='DONE';ar=float(a.reward) if a.reward is not None else None;br=float(b.reward) if b.reward is not None else None
 final=GameState.from_observation(a.observation);unsold=final.shed_count+final.carried_count
 return {'index':idx,'seed':seed,'position':pos,'completed':ok,'winner':'V7' if ok and ar>br else 'V6' if ok and ar<br else 'DRAW' if ok else 'INVALID','v7_reward':ar,'v6_reward':br,'difference':ar-br if ar is not None and br is not None else None,'error':err,'status':[a.status,b.status],'metrics':{**m.c,'unsold':unsold,'history_resets':m.f.market_history.resets},'timings':m.t}

def summarize(es,label,mode,horizon,threshold):
 v=[e for e in es if e['completed']];w=sum(e['winner']=='V7' for e in v);l=sum(e['winner']=='V6' for e in v);d=len(v)-w-l;ts=[x for e in es for x in e['timings']]
 def mm(k):return statistics.fmean(e['metrics'].get(k,0) for e in v) if v else 0
 pos={}
 for p in (0,1):
  q=[e for e in v if e['position']==p];pos[str(p)]={'games':len(q),'wins':sum(e['winner']=='V7' for e in q),'losses':sum(e['winner']=='V6' for e in q),'draws':sum(e['winner']=='DRAW' for e in q)}
 return {'metadata':{'label':label,'mode':mode,'horizon':horizon,'hold_threshold':threshold,'matched_seeds':True,'balanced_positions':True,'v6_frozen':True},'summary':{'games':len(es),'completed':len(v),'v7_wins':w,'v6_wins':l,'draws':d,'decisive_win_rate':w/(w+l) if w+l else 0},'confidence_interval':wilson(w,w+l),'position_results':pos,'rewards':{'v7':stats([e['v7_reward'] for e in v]),'v6':stats([e['v6_reward'] for e in v]),'difference':stats([e['difference'] for e in v])},'market':{k:mm(k) for k in ('units_held','hold_events','milk_held','units_sold','sale_value','milk_sold','unsold','land_orders','cow_orders','history_resets')},'crop_mix':{p:mm('plant_'+p) for p in CROPS},'operations':{k:mm(k) for k in ('waiting','unwatered','weed')},'workers':{'utilization':sum(e['metrics'].get('nonidle',0) for e in v)/max(1,sum(e['metrics'].get('available',0) for e in v))},'reliability':{'attempted':len(es),'completed':len(v),'crashes':sum('ERROR' in e['status'] for e in es),'timeouts':sum('TIMEOUT' in e['status'] for e in es)},'timing':{**stats(ts),'decisions':len(ts),'over100ms':sum(x>.1 for x in ts),'over500ms':sum(x>.5 for x in ts)},'episodes':[{k:x for k,x in e.items() if k!='timings'} for e in es]}

def run(mode,games,horizon,threshold,workers,seed=SEED):
 args=[(i,seed+i//2,mode,horizon,threshold,i%2) for i in range(games)]
 with ProcessPoolExecutor(max_workers=workers) as pool:es=list(pool.map(one,args,chunksize=1))
 return summarize(es,'V7-'+mode,mode,horizon,threshold)
def save(name,x):(RESULTS/name).write_text(json.dumps(x,indent=2),encoding='utf-8')
def main():
 p=argparse.ArgumentParser();p.add_argument('phase',choices=('modes','horizon','threshold','final'));p.add_argument('--games',type=int,default=100);p.add_argument('--workers',type=int,default=4);p.add_argument('--mode',default='CONTROL');p.add_argument('--horizon',type=int,default=24);p.add_argument('--threshold',type=float,default=.10);a=p.parse_args()
 if a.phase=='modes':
  names={'CONTROL':'v7_control.json','SELL_INTELLIGENCE':'v7_sell_intelligence.json','PRODUCTION_INTELLIGENCE':'v7_production_intelligence.json','FULL_INTELLIGENCE':'v7_full_intelligence.json'}
  for j,(m,n) in enumerate(names.items()):save(n,run(m,a.games,a.horizon,a.threshold,a.workers,SEED+j*10_000))
 elif a.phase=='horizon':save('v7_horizon_sweep.json',{'mode':a.mode,'horizons':{str(h):run(a.mode,a.games,h,a.threshold,a.workers,SEED+h*1000) for h in (4,12,24)}})
 elif a.phase=='threshold':save('v7_hold_threshold_sweep.json',{'mode':a.mode,'thresholds':{str(t):run(a.mode,a.games,a.horizon,t,a.workers,SEED+int(t*100000)) for t in (.05,.10,.20)}})
 else:save('v7_vs_v6.json',run(a.mode,a.games,a.horizon,a.threshold,a.workers,SEED+100_000))
if __name__=='__main__':main()
