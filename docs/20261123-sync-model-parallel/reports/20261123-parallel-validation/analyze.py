from pathlib import Path
import argparse,json,hashlib,math,statistics,collections,re,csv
p=argparse.ArgumentParser();p.add_argument('raw',type=Path);p.add_argument('old_summary',type=Path);p.add_argument('old_raw',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pct(v,q):
 v=sorted(v);x=(len(v)-1)*q;i=int(x);return v[i]+(v[min(i+1,len(v)-1)]-v[i])*(x-i)
def norm(x):
 if isinstance(x,dict):return {k:norm(v) for k,v in x.items() if k not in ('TimeStamp','UseTimeMs','FreeCapacity')}
 if isinstance(x,list):return [norm(v) for v in x]
 if isinstance(x,float):assert math.isfinite(x)
 return x
plan=json.loads((a.raw/'plan.json').read_text());oldplan=json.loads((a.old_raw/'plan.json').read_text());old=json.loads(a.old_summary.read_text());cleanup=json.loads((a.raw/'cleanup.json').read_text());result=json.loads((a.raw/'result.json').read_text())
assert cleanup['verified'] and result['completed_cases']==9 and result['requests']==900 and not (a.raw/'controller-error.txt').exists()
assert plan['workers']==4 and len(plan['jobs'])==9 and len({j['label'] for j in plan['jobs']})==9
for key in ('engines','manifest_sha256','source_config_sha256'):assert plan[key]==oldplan[key]
assert plan['pools']=={'sync':oldplan['pools']['sync']}
for name,ps in plan['pools'].items():
 assert len(ps['selected'])==100
 for x in ps['selected']:assert sha(a.raw/'inputs'/name/x['file'])==x['sha256']
ids=json.loads((a.raw/'server-pids.json').read_text())['workers'];assert len(set(ids))==4
logs=(a.raw/'server.log').read_text();assert not any(x in logs for x in ('Traceback','CUDA out of memory','CUDA error','NMS time limit'))
resources=list(map(json.loads,(a.raw/'resources.jsonl').read_text().splitlines()));assert {p['pid'] for r in resources for p in r['processes'] if p['role']=='server_worker'}==set(ids)
cases=[];allrows={};differences=[];reference={}
for name,endpoint in [('sync','/AE/SyncTasks2')]:
 warm=json.loads((a.raw/(name+'-warmup.json')).read_text());assert set(map(int,warm['per_worker']))==set(ids)
 access=[int(x) for x in re.findall(r'(?m)^(\d+) INFO:.*"POST '+re.escape(endpoint)+r' HTTP/[^\"]+" 200 OK',logs)]
 offset=warm['count'];assert len(access)==offset+900 and dict(collections.Counter(access[:offset]))=={int(k):v for k,v in warm['per_worker'].items()}
 reference[name]={r['sequence']:norm(r['response']) for r in map(json.loads,(a.old_raw/f'{name}-r1-c8/responses.jsonl').read_text().splitlines())}
 for job in [j for j in plan['jobs'] if j['name']==name]:
  d=a.raw/job['label'];s=json.loads((d/'summary.json').read_text());case=json.loads((d/'case-result.json').read_text());rows=list(map(json.loads,(d/'responses.jsonl').read_text().splitlines()));assert all(case[k]==v for k,v in s.items())
  assert len(rows)==100 and {r['sequence'] for r in rows}==set(range(100)) and all(r['image_id']==plan['pools'][name]['selected'][r['sequence']]['image_id'] for r in rows)
  for r in rows:
   b=r.get('response',{});ok=r['status']==200 and ((b.get('Response',{}).get('ErrCode')==0 and len(b.get('TaskResult',[]))==1) if name=='sync' else (len(b.get('DataList',[]))==1 and b['DataList'][0].get('StatusObject',{}).get('StatusCode')==0));assert ok and r['valid']
   if norm(b)!=reference[name][r['sequence']]:differences.append(dict(label=job['label'],sequence=r['sequence']))
  assert s['requests']==s['successful']==100 and s['failed']==0 and max(r['completed_offset_s'] for r in rows)==s['makespan_s']
  for k,q in [('p50',.5),('p95',.95),('p99',.99)]:assert pct([r['latency_ms'] for r in rows],q)==s['latency_ms'][k]
  counts={int(k):v for k,v in case['per_worker_http200'].items()};assert counts==dict(collections.Counter(access[offset:offset+100]));offset+=100
  cases.append(dict(label=job['label'],name=name,C=job['C'],repeat=job['repeat'],makespan_s=s['makespan_s'],successful=s['successful'],failed=s['failed'],per_worker_http200=counts,formal_resource_samples=sum(s['started_unix']<=r['unix']<=s['ended_unix'] for r in resources),responses_sha256=sha(d/'responses.jsonl')));allrows[job['label']]=rows
points=[];comparisons=[]
for name in ('sync',):
 for C in (1,8,16):
  cs=sorted([s for s in cases if s['name']==name and s['C']==C],key=lambda s:s['repeat']);assert len(cs)==3
  times=[s['makespan_s'] for s in cs];lat=[r['latency_ms'] for s in cs for r in allrows[s['label']]];hist=next(x for x in old['points'] if x['W']==4 and x['name']==name and x['C']==C)
  points.append(dict(name=name,C=C,seconds=times,median_s=statistics.median(times),min_s=min(times),max_s=max(times),successful=300,failed=0,tps=100/statistics.median(times),latency_ms=dict(mean=statistics.mean(lat), **{k:pct(lat,q) for k,q in [('p50',.5),('p95',.95),('p99',.99)]}),historical_median_s=hist['median_s'],historical_p95_ms=hist['pooled_success_p95_ms']))
 x,y=[next(s for s in points if s['name']==name and s['C']==c) for c in (8,16)];ratios=[b/a for a,b in zip(x['seconds'],y['seconds'])]
 comparisons.append(dict(name=name,c16_over_c8_median_makespan=y['median_s']/x['median_s'],c16_time_reduction_percent=(1-y['median_s']/x['median_s'])*100,paired_ratios=ratios,paired_ratio_median=statistics.median(ratios),c16_over_c8_p95=y['latency_ms']['p95']/x['latency_ms']['p95']))
summary=dict(schema=1,code=plan['code'],run_id=plan['run_id'],plan_sha256=sha(a.raw/'plan.json'),analyzer_sha256=sha(__file__),groups=len(cases),requests=900,successful=900,failed=0,points=points,comparisons=comparisons,cases=cases,stage_gpu_peak_mib=max(float(r['gpu'].split(',')[0]) for r in resources),stage_all_worker_rss_peak_mib=max(math.fsum(p['rss_kib'] for p in r['processes'] if p['role']=='server_worker')/1024 for r in resources),normalized_business_comparison=dict(reference='historical W4 r1 C8 per same sequence; omit TimeStamp/UseTimeMs/FreeCapacity only',compared=900,difference_count=len(differences),differences=differences),cleanup=cleanup,resource_roles=sorted({p['role'] for r in resources for p in r['processes']}))
a.output.mkdir();(a.output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
with (a.output/'metrics.csv').open('w',newline='') as f:
 cols=['name','C','median_s','min_s','max_s','successful','failed','tps'];w=csv.DictWriter(f,fieldnames=cols,lineterminator='\n');w.writeheader();w.writerows({k:x[k] for k in cols} for x in points)
print(json.dumps(dict(points=points,comparisons=comparisons,business_differences=len(differences)),ensure_ascii=False))
