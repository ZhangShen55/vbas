from pathlib import Path
import math
import argparse,json,hashlib,re,collections,statistics,csv
p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('baseline',type=Path);p.add_argument('baseline_raw',type=Path);p.add_argument('output',type=Path);a=p.parse_args();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pct(v,q):
 v=sorted(v);t=(len(v)-1)*q;i=int(t);return v[i]+(v[min(i+1,len(v)-1)]-v[i])*(t-i)
def stage_usage(rows,role,expected):
 previous={};cpus=[];rss=[];g=[]
 for row in rows:
  t=row['unix'];workers=[x for x in row['processes'] if x['role']==role];cur={x['pid']:x for x in workers}
  if len(workers)==expected:
   rss.append(math.fsum(x['rss_kib'] for x in workers)/1024)
   if all(x['pid'] in previous for x in workers):
    loads=[(x['cpu_seconds']-previous[x['pid']][1])/(t-previous[x['pid']][0])*100 for x in workers if t>previous[x['pid']][0]]
    if len(loads)==expected:cpus.append(math.fsum(loads))
  for x in workers:previous[x['pid']]=(t,x['cpu_seconds'])
  g.append(float(row['gpu'].split(',')[0]))
 return dict(stage_gpu_memory_peak_mib=max(g),stage_worker_rss_sum_peak_mib=max(rss),stage_worker_cpu_sum_mean_one_core_100=statistics.mean(cpus) if cpus else None,stage_scope='includes startup/warmup/formal/idle; worker aggregates only when all workers sampled; not formal-only means')
old=json.loads(a.baseline.read_text());baseplan=json.loads((a.baseline_raw/'plan.json').read_text());assert sha(a.baseline_raw/'plan.json')==old['plan_sha256'];points=[dict(W=1,**x) for x in old['points']];allcases=[];phases=[];pool_ref=baseplan['pools']
base_resources=list(map(json.loads,(a.baseline_raw/'resources.jsonl').read_text().splitlines()));phases.append(dict(W=1,phase_gpu_peak_mib=max(float(x['gpu'].split(',')[0]) for x in base_resources),source='previous fixed100 raw records, not rerun'))
for W in [2,4,6]:
 o=a.root/f'uvicorn-workers-fixed100-20261123-w{W}-r2';plan=json.loads((o/'plan.json').read_text());cleanup=json.loads((o/'cleanup.json').read_text());assert cleanup['verified'] and json.loads((o/'result.json').read_text())['completed_cases']==72;assert not (o/'controller-error.txt').exists()
 assert plan['engines']==baseplan['engines'] and plan['manifest_sha256']==baseplan['manifest_sha256'] and plan['source_config_sha256']==baseplan['source_config_sha256']
 assert all(sha(o/'inputs'/name/x['file'])==x['sha256'] for name,ps in pool_ref.items() for x in ps['selected'])
 assert plan['pools']==pool_ref and plan['workers']==W and plan['code']==old['code']
 ids=json.loads((o/'server-pids.json').read_text())['workers'];assert len(set(ids))==W
 resources=list(map(json.loads,(o/'resources.jsonl').read_text().splitlines()));roles={p['role'] for row in resources for p in row['processes']};assert {'controller','uvicorn_parent','server_worker','load_generator'}<=roles
 sampled_workers={p['pid'] for row in resources for p in row['processes'] if p['role']=='server_worker'};assert sampled_workers==set(ids)
 logs=(o/'server.log').read_text();assert not any(t in logs for t in ['Traceback','CUDA out of memory','CUDA error','NMS time limit']);cases=[];raw_by_label={}
 for name,endpoint in [('sync','/AE/SyncTasks2'),('student','/ImageDetect/student/v1.0.0'),('teacher','/ImageDetect/teacher/v1.0.0')]:
  warm=json.loads((o/(name+'-warmup.json')).read_text());assert set(map(int,warm['per_worker']))==set(ids)
  accesses=[int(x) for x in re.findall(r'(?m)^(\d+) INFO:.*"POST '+re.escape(endpoint)+r' HTTP/[^\"]+" 200 OK',logs)];offset=warm['count'];assert len(accesses)==offset+2400
  assert dict(collections.Counter(accesses[:offset]))=={int(k):v for k,v in warm['per_worker'].items()}
  for job in [x for x in plan['jobs'] if x['name']==name]:
   d=o/job['label'];s=json.loads((d/'summary.json').read_text());case=json.loads((d/'case-result.json').read_text());rows=list(map(json.loads,(d/'responses.jsonl').read_text().splitlines()));assert len(rows)==100 and {x['sequence'] for x in rows}==set(range(100))
   assert all(x['image_id']==plan['pools'][name]['selected'][x['sequence']]['image_id'] for x in rows)
   for row in rows:
    b=row.get('response',{});valid=row['status']==200 and ((b.get('Response',{}).get('ErrCode')==0 and len(b.get('TaskResult',[]))==1) if name=='sync' else (len(b.get('DataList',[]))==1 and b['DataList'][0].get('StatusObject',{}).get('StatusCode')==0));assert valid==row['valid']
   assert all(case[k]==v for k,v in s.items())
   good=[x for x in rows if x['valid']];assert len(good)==s['successful'] and s['failed']==100-len(good);assert max(x['completed_offset_s'] for x in rows)==s['makespan_s']
   for k,q in [('p50',.5),('p95',.95),('p99',.99)]:assert pct([x['latency_ms'] for x in good],q)==s['latency_ms'][k]
   distribution={int(k):v for k,v in case['per_worker_http200'].items()};assert dict(collections.Counter(accesses[offset:offset+100]))==distribution;offset+=100
   samples=[x for x in resources if s['started_unix']<=x['unix']<=s['ended_unix']];s.update(W=W,job=job,per_worker_http200=distribution,active_workers=len(distribution),formal_samples=len(samples),responses_sha256=sha(d/'responses.jsonl'));cases.append(s);raw_by_label[job['label']]=rows
 for name in ['sync','student','teacher']:
  for C in [1,2,4,8,16,32,50,100]:
   cs=[x for x in cases if x['name']==name and x['C']==C];assert len(cs)==3;ts=[x['makespan_s'] for x in cs];lat=[r['latency_ms'] for x in cs for r in raw_by_label[x['job']['label']] if r['valid']];valid=all(x['failed']==0 for x in cs)
   points.append(dict(W=W,name=name,C=C,seconds=ts,median_s=statistics.median(ts),min_s=min(ts),max_s=max(ts),successful=sum(x['successful'] for x in cs),failed=sum(x['failed'] for x in cs),valid=valid,tps_100_over_median=100/statistics.median(ts) if valid else None,pooled_success_p95_ms=pct(lat,.95),active_workers=[x['active_workers'] for x in cs],generator_cpu_percent=100*math.fsum(x['generator_measurement_cpu_seconds'] for x in cs)/math.fsum(ts)))
 allcases+=cases;phases.append(dict(W=W,pids=ids,roles=sorted(roles),cleanup=cleanup,plan_sha256=sha(o/'plan.json'),phase_peak_gpu_mib=max(float(x['gpu'].split(',')[0]) for x in resources)))
for phase in phases:
 w=phase['W'];rows=list(map(json.loads,((a.baseline_raw if w==1 else a.root/f'uvicorn-workers-fixed100-20261123-w{w}-r2')/'resources.jsonl').read_text().splitlines()));phase.update(stage_usage(rows,'server' if w==1 else 'server_worker',w))
best={};platform=[]
for name in ['sync','student','teacher']:
 ps=[x for x in points if x['name']==name and x['valid']];fast=min(ps,key=lambda x:x['median_s']);eco=min((x for x in ps if x['median_s']<=fast['median_s']*1.05),key=lambda x:(x['W'],x['C']));best[name]=dict(fastest=fast,economical=eco)
 for W in [1,2,4,6]:
  ws=[x for x in ps if x['W']==W];f=min(ws,key=lambda x:x['median_s']);c=min((x for x in ws if x['median_s']<=f['median_s']*1.05),key=lambda x:x['C']);platform.append(dict(name=name,W=W,fastest_C=f['C'],fastest_s=f['median_s'],platform_C=c['C'],platform_s=c['median_s']))
unified=[]
for W in [1,2,4,6]:
 bs={name:min((x for x in points if x['W']==W and x['name']==name and x['valid']),key=lambda x:x['median_s']) for name in ['sync','student','teacher']};unified.append(dict(W=W,total_300_s=math.fsum(x['median_s'] for x in bs.values()),concurrency={name:x['C'] for name,x in bs.items()}))
a.output.mkdir(parents=True,exist_ok=False);s=dict(schema_version=1,code=old['code'],baseline_sha256=sha(a.baseline),analyzer_sha256=sha(__file__),new_requests=21600,new_successful=sum(x['successful'] for x in allcases),new_failed=sum(x['failed'] for x in allcases),points=points,cases=allcases,phases=phases,best=best,platform=platform,unified=unified,unified_fastest=min(unified,key=lambda x:x['total_300_s']))
(a.output/'summary.json').write_text(json.dumps(s,ensure_ascii=False,indent=2))
with (a.output/'metrics.csv').open('w',newline='') as f:
 cols=['W','name','C','median_s','min_s','max_s','successful','failed','tps_100_over_median','pooled_success_p95_ms','generator_cpu_percent'];w=csv.DictWriter(f,fieldnames=cols,lineterminator='\n');w.writeheader();w.writerows({k:x[k] for k in cols} for x in points)
print(json.dumps(dict(best={k:dict(W=v['fastest']['W'],C=v['fastest']['C'],seconds=v['fastest']['median_s']) for k,v in best.items()},unified=s['unified_fastest'],new_successful=s['new_successful'],new_failed=s['new_failed'])))
