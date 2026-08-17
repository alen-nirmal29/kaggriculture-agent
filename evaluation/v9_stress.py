"""Held-out opponent-pool and standalone self-play smoke suite."""
from __future__ import annotations
import importlib.util,json,sys,time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from kaggle_environments import make
from evaluation.v3_capacity import stats,wilson
from main_v4 import make_agent as make_v4
from main_v6 import make_agent as make_v6
ARTIFACT=ROOT/'submission'/'main.py'

def standalone(name):
 spec=importlib.util.spec_from_file_location(name,ARTIFACT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m.agent

def opponent(name):
 if name=='V6':return make_v6()
 if name=='V4':return make_v4(4)
 if name=='starter':return 'starter'
 raise ValueError(name)

def one(a):
 i,seed,pos,opp=a;times=[];candidate=standalone(f'v9_stress_{i}_{pos}')
 def measured(obs,configuration=None):
  t=time.perf_counter();x=candidate(obs);times.append(time.perf_counter()-t);return x
 agents=[opponent(opp),opponent(opp)];agents[pos]=measured;e=make('kaggriculture',configuration={'seed':seed},debug=True);err=None
 try:e.run(agents)
 except Exception as x:err=f'{type(x).__name__}: {x}'
 x,y=e.state[pos],e.state[1-pos];ok=err is None and len(e.steps)==720 and x.status==y.status=='DONE';xr=float(x.reward or 0);yr=float(y.reward or 0)
 return {'seed':seed,'position':pos,'opponent':opp,'completed':ok,'winner':'V9' if ok and xr>yr else opp if ok and xr<yr else 'DRAW' if ok else 'INVALID','v9_reward':xr,'opponent_reward':yr,'difference':xr-yr,'statuses':[x.status,y.status],'error':err,'times':times}

def self_one(a):
 i,seed=a;left=standalone(f'v9_self_a_{i}');right=standalone(f'v9_self_b_{i}');e=make('kaggriculture',configuration={'seed':seed},debug=True);err=None
 try:e.run([left,right])
 except Exception as x:err=f'{type(x).__name__}: {x}'
 ok=err is None and len(e.steps)==720 and all(x.status=='DONE' for x in e.state)
 return {'seed':seed,'completed':ok,'statuses':[x.status for x in e.state],'rewards':[x.reward for x in e.state],'error':err}

def summarize(es):
 good=[e for e in es if e['completed']];w=sum(e['winner']=='V9' for e in good);l=sum(e['winner']==e['opponent'] for e in good);d=len(good)-w-l;ts=[t for e in es for t in e['times']]
 return {'games':len(es),'completed':len(good),'wins':w,'losses':l,'draws':d,'decisive_win_rate':w/(w+l) if w+l else 0,'wilson':wilson(w,w+l),'v9_reward':stats([e['v9_reward'] for e in good]),'opponent_reward':stats([e['opponent_reward'] for e in good]),'difference':stats([e['difference'] for e in good]),'crashes':sum('ERROR' in e['statuses'] for e in es),'timeouts':sum('TIMEOUT' in e['statuses'] for e in es),'invalid_action_failures':sum(not e['completed'] for e in es),'timing':stats(ts)}

def main():
 tasks=[]
 for j,opp in enumerate(('V6','V4','starter')):
  tasks.extend((j*50+i,1690000+j*1000+i//2,i%2,opp) for i in range(50))
 with ProcessPoolExecutor(max_workers=4) as p:episodes=list(p.map(one,tasks,chunksize=1))
 by={opp:summarize([e for e in episodes if e['opponent']==opp]) for opp in ('V6','V4','starter')}
 with ProcessPoolExecutor(max_workers=4) as p:selfplay=list(p.map(self_one,[(i,1695000+i) for i in range(100)],chunksize=1))
 result={'opponents':by,'self_play':{'games':100,'completed':sum(x['completed'] for x in selfplay),'crashes':sum('ERROR' in x['statuses'] for x in selfplay),'timeouts':sum('TIMEOUT' in x['statuses'] for x in selfplay),'invalid_action_failures':sum(not x['completed'] for x in selfplay),'episodes':selfplay},'episodes':[{k:v for k,v in e.items() if k!='times'} for e in episodes]}
 (ROOT/'evaluation'/'results'/'v9_stress.json').write_text(json.dumps(result,indent=2),encoding='utf-8')

if __name__=='__main__':main()
