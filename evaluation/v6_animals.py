"""Balanced, matched-seed V6 livestock evaluation against frozen V4."""
from __future__ import annotations
import argparse, json, statistics, sys, time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from kaggle_environments import make
from evaluation.v3_capacity import stats, wilson
from main_v4 import agent as v4_agent
from main_v6 import make_agent
from agent_v6.state import GameState
RESULTS=ROOT/'evaluation'/'results'; BASE_SEED=960_000
ANIMAL_COST={"GOOSE":300,"COW":400,"SHEEP":500}; PRODUCTS={"EGG","MILK","WOOL"}; PROD={"DIG","PLANT","WATER","HARVEST"}

class Measured:
 def __init__(self,mode,caps,fertilizer): self.agent=make_agent(mode,caps,fertilizer);self.t=[];self.c=Counter();self.prev_animals=0
 def __call__(self,obs,configuration=None):
  s=GameState.from_observation(obs);t=time.perf_counter();a=self.agent(obs);self.t.append(time.perf_counter()-t)
  animals=sum(x.animal is not None for x in s.structures);self.c['animal_observations']+=animals;self.c['max_animals']=max(self.c['max_animals'],animals)
  if animals<self.prev_animals:self.c['escapes']+=self.prev_animals-animals
  self.prev_animals=animals; acts=[a.get('farmer',['PASS'])]+a.get('hands',[])
  self.c['available']+=len(acts);self.c['nonidle']+=sum(bool(x and x[0]!='PASS') for x in acts)
  for x in acts:
   op=x[0] if x else 'PASS';self.c['productive']+=op in PROD;self.c['animal_actions']+=op in {'BUILD_COOP','BUILD_PASTURE','PLACE','FEED','CARE','COLLECT_FERTILIZER'} or (op=='HARVEST' and any(z.position==next((u.position for u in []),None) for z in s.structures))
   self.c['feed_actions']+=op=='FEED';self.c['care_actions']+=op=='CARE';self.c['fertilizer_collected']+=op=='COLLECT_FERTILIZER';self.c['fertilizer_applied']+=op=='FERTILIZE';self.c['animal_movement']+=op in {'NORTH','SOUTH','EAST','WEST'} and animals>0
  for o in a.get('market',[]):
   if o and o[0]=='BUY_ANIMAL':self.c['animals_bought']+=int(o[2]);self.c['animal_spend']+=ANIMAL_COST[o[1]]*int(o[2])
   if o and o[:2]==['BUY_PRODUCT','WHEAT']:self.c['feed_bought']+=int(o[2]);self.c['feed_spend']+=int(o[2])*int(s.market_prices.get('WHEAT',25))
   if o and o[0]=='SELL' and o[1] in PRODUCTS:self.c['products_sold']+=int(o[2]);self.c['animal_revenue']+=int(o[2])*int(s.market_prices.get(o[1],0))
  for tile in s.iter_tiles():
   raw=tile.raw
   if isinstance(raw,dict) and raw.get('kind')=='PLANT':
    self.c['mature']+=int(raw.get('yield_units',0)>0);self.c['unwatered']+=int(s.hour==23 and not raw.get('watered_today',False))
   self.c['weed']+=int(isinstance(raw,dict) and raw.get('kind')=='WEED')
  return a

def one(args):
 idx,seed,mode,caps,fert,pos=args;m=Measured(mode,caps,fert);agents=[v4_agent,v4_agent];agents[pos]=m;e=make('kaggriculture',configuration={'seed':seed},debug=True);err=None
 try:e.run(agents)
 except Exception as x:err=f'{type(x).__name__}: {x}'
 a,b=e.state[pos],e.state[1-pos];ok=err is None and len(e.steps)==720 and a.status==b.status=='DONE';ar=float(a.reward) if a.reward is not None else None;br=float(b.reward) if b.reward is not None else None
 return {'index':idx,'seed':seed,'position':pos,'completed':ok,'winner':'V6' if ok and ar>br else 'V4' if ok and ar<br else 'DRAW' if ok else 'INVALID','v6_reward':ar,'v4_reward':br,'difference':ar-br if ar is not None and br is not None else None,'error':err,'status':[a.status,b.status],'metrics':dict(m.c),'timings':m.t}

def summarize(es,label,mode,caps,fert):
 valid=[e for e in es if e['completed']];w=sum(e['winner']=='V6' for e in valid);l=sum(e['winner']=='V4' for e in valid);d=len(valid)-w-l;times=[x for e in es for x in e['timings']]
 def mean_metric(k):return statistics.fmean(e['metrics'].get(k,0) for e in valid) if valid else 0
 positions={str(p):{'games':len(q:=[e for e in valid if e['position']==p]),'wins':sum(e['winner']=='V6' for e in q),'losses':sum(e['winner']=='V4' for e in q),'draws':sum(e['winner']=='DRAW' for e in q)} for p in (0,1)}
 return {'metadata':{'label':label,'mode':mode,'caps':caps,'fertilizer':fert,'matched_seeds':True,'balanced_positions':True,'v4_frozen':True},'summary':{'games':len(es),'completed':len(valid),'v6_wins':w,'v4_wins':l,'draws':d,'decisive_win_rate':w/(w+l) if w+l else 0},'confidence_interval':wilson(w,w+l),'position_results':positions,'rewards':{'v6':stats([e['v6_reward'] for e in valid]),'v4':stats([e['v4_reward'] for e in valid]),'difference':stats([e['difference'] for e in valid])},'animals':{k:mean_metric(k) for k in ('max_animals','animals_bought','animal_spend','feed_bought','feed_spend','products_sold','animal_revenue','animal_actions','animal_movement','escapes','feed_actions','care_actions','fertilizer_collected','fertilizer_applied')},'operations':{k:mean_metric(k) for k in ('mature','unwatered','weed','productive')},'workers':{'utilization':sum(e['metrics'].get('nonidle',0) for e in valid)/max(1,sum(e['metrics'].get('available',0) for e in valid))},'reliability':{'attempted':len(es),'completed':len(valid),'crashes':sum('ERROR' in e['status'] for e in es),'timeouts':sum('TIMEOUT' in e['status'] for e in es)},'timing':{**stats(times),'decisions':len(times),'over100ms':sum(x>.1 for x in times),'over500ms':sum(x>.5 for x in times)},'episodes':[{k:v for k,v in e.items() if k!='timings'} for e in es]}

def run(label,mode,caps,fert,games,seed0,workers):
 args=[(i,seed0+i//2,mode,caps,fert,i%2) for i in range(games)]
 with ProcessPoolExecutor(max_workers=workers) as pool: es=list(pool.map(one,args,chunksize=1))
 return summarize(es,label,mode,caps,fert)
def save(name,data):(RESULTS/name).write_text(json.dumps(data,indent=2),encoding='utf-8')
def main():
 p=argparse.ArgumentParser();p.add_argument('phase',choices=('control','species','species-one','count','fertilizer','final'));p.add_argument('--games',type=int,default=100);p.add_argument('--workers',type=int,default=4);p.add_argument('--species',default='COW');p.add_argument('--count',type=int,default=1);a=p.parse_args()
 if a.phase=='control':save('v6_control.json',run('V6-control','NONE',{},False,a.games,BASE_SEED,a.workers))
 elif a.phase=='species':
  out={'metadata':{'games_per_species':a.games},'species':{}}
  for j,s in enumerate(('GOOSE','COW','SHEEP')):out['species'][s]=run('V6-'+s,s+'_ONLY',{s:1},False,a.games,BASE_SEED+j*10_000,a.workers)
  save('v6_species_sweep.json',out)
 elif a.phase=='species-one':
  path=RESULTS/'v6_species_sweep.json';out=json.loads(path.read_text())
  offset={'GOOSE':0,'COW':10_000,'SHEEP':20_000}[a.species]
  out['species'][a.species]=run('V6-'+a.species,a.species+'_ONLY',{a.species:1},False,a.games,BASE_SEED+offset,a.workers);save('v6_species_sweep.json',out)
 elif a.phase=='count':
  out={'metadata':{'species':a.species,'games_per_count':a.games},'counts':{}}
  for n in (1,2,3,4):out['counts'][str(n)]=run(f'V6-{a.species}-{n}',a.species+'_ONLY',{a.species:n},False,a.games,BASE_SEED+n*10_000,a.workers)
  save('v6_animal_count_sweep.json',out)
 elif a.phase=='fertilizer':
  out={'metadata':{'species':a.species,'count':a.count,'games_per_policy':a.games},'off':run('fertilizer-off',a.species+'_ONLY',{a.species:a.count},False,a.games,BASE_SEED+60_000,a.workers),'on':run('fertilizer-on',a.species+'_ONLY',{a.species:a.count},True,a.games,BASE_SEED+60_000,a.workers)};save('v6_fertilizer_sweep.json',out)
 else:save('v6_vs_v4.json',run('V6-final',a.species+'_ONLY',{a.species:a.count},True,a.games,BASE_SEED+100_000,a.workers))
if __name__=='__main__':main()
