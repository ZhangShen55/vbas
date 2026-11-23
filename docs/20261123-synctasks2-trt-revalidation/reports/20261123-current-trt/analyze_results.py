"""Offline independent recomputation; no GPU or source mutation."""
from pathlib import Path
import argparse,json,hashlib,math,statistics,collections,csv,re
p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('output',type=Path);p.add_argument('--old',type=Path,required=True);a=p.parse_args();B=a.root;O=B/'sync-trt-revalidation-20261123-r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pct(v,q):
 v=sorted(v);x=(len(v)-1)*q;i=int(x);return v[i]+(v[min(i+1,len(v)-1)]-v[i])*(x-i)
def norm(v):
 if isinstance(v,dict):return {k:norm(x) for k,x in v.items() if k not in ('TimeStamp','UseTimeMs','FreeCapacity')}
 if isinstance(v,list):return sorted((norm(x) for x in v),key=lambda x:json.dumps(x,sort_keys=True))
 if isinstance(v,float):assert math.isfinite(v)
 return v
CONT=B/'sync-trt-revalidation-continuation-20261123-r1'
prior=[json.loads(x)['phase'] for x in (O/'journal.jsonl').read_text().splitlines()]
continued=[json.loads(x)['phase'] for x in (CONT/'journal.jsonl').read_text().splitlines()]
assert prior==['functional','audit','fixed-w1','fixed-w2']
assert continued==['fixed-w4','fixed-w6','pressure']
assert json.loads((CONT/'result.json').read_text())['completed_phases']==3 and not (CONT/'campaign-error.txt').exists()
assert 'Address already in use' in (O/'fixed-w4.log').read_text()
campaign=json.loads((O/'plan.json').read_text());code=campaign['code']
# Audit responses serve as a current-image map; independently compare against the original baseline.
audit=B/'sync-trt-audit-20261123-r1';audit_s=json.loads((audit/'result.json').read_text());refs={}
reference=B/'trt-corrected-baseline-20261118/predictions.jsonl'
for line in reference.read_text().splitlines():
 r=json.loads(line)
 if r['endpoint']=='/AE/SyncTasks2':refs[r['image_id']]=norm(r['response'])
ref_hashes={r['image_id']:r['image_sha256'] for r in map(json.loads,reference.read_text().splitlines()) if r['endpoint']=='/AE/SyncTasks2'}
assert len(refs)==2162
arows=list(map(json.loads,(audit/'full-sync/load/responses.jsonl').read_text().splitlines()));assert len(arows)==2162 and {x['image_id'] for x in arows}==refs.keys()
assert {r['sequence'] for r in arows}==set(range(2162)) and all(r['image_sha256']==ref_hashes[r['image_id']] for r in arows)
assert all(r['valid'] and r['status']==200 and norm(r['response'])==refs[r['image_id']] for r in arows)
assert sha(reference)==audit_s['reference_sha256']
assert audit_s['strict_equal_calls']==2162 and audit_s['http_or_business_failures']==0
old=json.loads(a.old.read_text());points=[];cases=[];stages=[]
identity=None
for W in (1,2,4,6):
 root=B/f'sync-trt-fixed100-20261123-w{W}-r1';plan=json.loads((root/'plan.json').read_text());cleanup=json.loads((root/'cleanup.json').read_text());assert plan['code']==code and cleanup['verified'] and json.loads((root/'result.json').read_text())['completed_cases']==24
 current_identity={k:plan[k] for k in ('manifest_sha256','engines','source_config_sha256','pools','b','q','gpu_uuid','timeout')}
 if identity is None:identity=current_identity
 assert identity==current_identity
 ids=json.loads((root/'server-pids.json').read_text())['workers'];assert len(set(ids))==W
 if W==1:assert ids==[cleanup['parent_pid']]
 for item in plan['pools']['sync']['selected']:assert sha(root/'inputs/sync'/item['file'])==item['sha256']
 warm=json.loads((root/'sync-warmup.json').read_text());assert set(map(int,warm['per_worker']))==set(ids)
 logs=(root/'server.log').read_text();assert not any(s in logs for s in ('Traceback','CUDA out of memory','CUDA error','NMS time limit'))
 access=[int(x) for x in re.findall(r'(?m)^(\d+) INFO:.*"POST /AE/SyncTasks2 HTTP/[^\"]+" 200 OK',logs)];offset=warm['count'];assert dict(collections.Counter(access[:offset]))=={int(k):v for k,v in warm['per_worker'].items()}
 allrows={};wc=[]
 for job in plan['jobs']:
  d=root/job['label'];s=json.loads((d/'summary.json').read_text());cr=json.loads((d/'case-result.json').read_text());rows=list(map(json.loads,(d/'responses.jsonl').read_text().splitlines()));assert len(rows)==100 and {r['sequence'] for r in rows}==set(range(100))
  for r in rows:
   assert r['image_id']==plan['pools']['sync']['selected'][r['sequence']]['image_id']
   valid=r['status']==200 and r.get('response',{}).get('Response',{}).get('ErrCode')==0 and len(r.get('response',{}).get('TaskResult',[]))==1;assert valid==r['valid']
   if valid:assert norm(r['response'])==refs[r['image_id']]
  good=[r for r in rows if r['valid']];assert len(good)==s['successful'] and 100-len(good)==s['failed'];assert s['makespan_s']==max(r['completed_offset_s'] for r in rows)
  for key,q in [('p50',.5),('p95',.95),('p99',.99)]:assert s['latency_ms'][key]==pct([r['latency_ms'] for r in good],q)
  counts={int(k):v for k,v in cr['per_worker_http200'].items()};assert dict(collections.Counter(access[offset:offset+s['successful']]))==counts;offset+=s['successful']
  wc.append(dict(W=W,C=job['C'],repeat=job['repeat'],label=job['label'],makespan_s=s['makespan_s'],successful=s['successful'],failed=s['failed'],started_unix=s['started_unix'],ended_unix=s['ended_unix'],per_worker=counts,response_sha256=sha(d/'responses.jsonl')));allrows[job['label']]=rows
 assert len(access)==offset
 resources=list(map(json.loads,(root/'resources.jsonl').read_text().splitlines()));assert {p['pid'] for r in resources for p in r['processes'] if p['role']=='server_worker'}==set(ids)
 rss=[math.fsum(p['rss_kib'] for p in r['processes'] if p['role']=='server_worker')/1024 for r in resources]
 stages.append(dict(W=W,pids=ids,gpu_peak_mib=max(float(r['gpu'].split(',')[0]) for r in resources),worker_rss_sum_peak_mib=max(rss),cleanup=cleanup,plan_sha256=sha(root/'plan.json'),resource_scope='includes startup/warmup/formal/idle; not formal-only means'))
 for C in (1,2,4,8,16,32,50,100):
  cs=sorted([x for x in wc if x['C']==C],key=lambda x:x['repeat']);assert len(cs)==3;ts=[x['makespan_s'] for x in cs];lat=[r['latency_ms'] for c in cs for r in allrows[c['label']] if r['valid']];failed=sum(c['failed'] for c in cs)
  historical=next(x for x in old['points'] if x['W']==W and x['name']=='sync' and x['C']==C)
  points.append(dict(W=W,C=C,seconds=ts,median_s=statistics.median(ts),min_s=min(ts),max_s=max(ts),successful=300-failed,failed=failed,tps=100/statistics.median(ts) if not failed else None,latency_ms=dict(mean=statistics.mean(lat),p50=pct(lat,.5),p95=pct(lat,.95),p99=pct(lat,.99)),active_workers=[len(x['per_worker']) for x in cs],old_serial_median_s=historical['median_s']))
 cases+=wc
assert len(points)==32 and len(cases)==96
# Nine duration-bound cases: validate raw counts, window, quantiles and independent management resource coverage.
pressure=[];proot=B/'sync-trt-pressure-20261123-r1';pp=json.loads((proot/'plan.json').read_text());assert len(pp['jobs'])==9 and json.loads((proot/'result.json').read_text())['completed_cases']==9
assert pp['engine_manifest_sha256']==identity['manifest_sha256'] and pp['engines']==identity['engines'] and pp['config_source_sha256']==identity['source_config_sha256']
watch=list(map(json.loads,(CONT/'pressure-tree-resources.jsonl').read_text().splitlines()))
for job in pp['jobs']:
 d=proot/job['label'];s=json.loads((d/'load/summary.json').read_text());rows=list(map(json.loads,(d/'load/requests.jsonl').read_text().splitlines()));good=[r for r in rows if r['valid']];assert len(rows)==s['requests'] and len(good)==s['successful'] and len(rows)-len(good)==s['failed'];assert {r['sequence'] for r in rows}==set(range(len(rows)))
 window=sum(r['completed_offset_s']<=180 for r in good);assert window/180==s['success_images_per_s_in_window']
 for key,q in [('p50',.5),('p95',.95),('p99',.99)]:assert s['successful_image_latency_ms'][key]==pct([r['latency_ms'] for r in good],q)
 events=list(map(json.loads,(d/'events.jsonl').read_text().splitlines()));assert events[-1]['event']=='cleanup_complete'
 start=s['started_unix_time'];formal=[r for r in watch if start<=r['unix']<=start+180];roles=collections.defaultdict(set);counts=collections.Counter()
 for r in formal:
  for p in r['processes']:
   roles[p['role']].add(p['pid']);counts[p['pid']]+=1
 assert len(roles['phase_controller'])==1 and len(roles['campaign_supervisor'])==1 and roles['instance_manager'] and roles['load_generator']
 ids=json.loads((d/'instances.json').read_text())['pids'];assert roles['server_worker']==set(ids)
 assert len(formal)>=150 and all(counts[pid]>=150 for role,pids in roles.items() if role in ('phase_controller','campaign_supervisor','instance_manager','load_generator','server_worker') for pid in pids)
 pid_stats=[]
 for role,pids in roles.items():
  if role not in ('phase_controller','campaign_supervisor','instance_manager','load_generator','server_worker'):continue
  for pid in sorted(pids):
   series=[(r['unix'],p) for r in formal for p in r['processes'] if p['pid']==pid]
   first,last=series[0],series[-1];elapsed=last[0]-first[0];assert elapsed>0 and first[1]['start_ticks']==last[1]['start_ticks']
   pid_stats.append(dict(role=role,pid=pid,samples=len(series),sampled_seconds=elapsed,cpu_one_core_100=(last[1]['cpu_seconds']-first[1]['cpu_seconds'])/elapsed*100,rss_peak_mib=max(p['rss_kib'] for _,p in series)/1024))
 gpu_memory=[float(r['gpu'].split(',')[0]) for r in formal];gpu_util=[float(r['gpu'].split(',')[1]) for r in formal]
 failure=collections.Counter(r.get('error_type','http_'+str(r.get('status'))) for r in rows if not r['valid'])
 per_port={}
 for url in sorted({r['instance'] for r in rows}):
  rs=[r for r in rows if r['instance']==url];port=url.rsplit(':',1)[1];log=(d/f'instance-{port}.log').read_text()
  assert not any(term in log for term in ('Traceback','CUDA out of memory','CUDA error','NMS time limit'))
  per_port[port]=dict(requests=len(rs),successful=sum(r['valid'] for r in rs),failed=sum(not r['valid'] for r in rs),access_200_including_warmup=log.count('"POST /AE/SyncTasks2 HTTP/1.1" 200 OK'))
 errors=[]
 assert all(r.get('error_type') in ('httpx.ReadError','httpx.ReadTimeout') for r in rows if not r['valid'])
 for r in rows:
  if not r['valid']:errors.append({k:r.get(k) for k in ('sequence','instance','image_id','status','error','error_type','error_chain','os_errno_available','latency_ms','sent_offset_s','completed_offset_s')})
 pressure.append(dict(job=job,requests=len(rows),successful=len(good),failed=len(rows)-len(good),completed_in_window=sum(r['completed_offset_s']<=180 for r in rows),in_flight_at_180=len(rows)-sum(r['completed_offset_s']<=180 for r in rows),elapsed_including_drain_s=s['elapsed_including_drain_s'],per_port=per_port,error_records=errors,formal_successes=window,tps=window/180,latency_ms=s['successful_image_latency_ms'],failures=dict(failure),formal_samples=len(formal),pid_resources=pid_stats,gpu_peak_mib=max(gpu_memory),gpu_util_mean=sum(gpu_util)/len(gpu_util),roles={k:sorted(v) for k,v in roles.items()},samples_by_pid=dict(counts),requests_sha256=sha(d/'load/requests.jsonl'),summary_sha256=sha(d/'load/summary.json')))
froot=B/'sync-trt-functional-20261123-r1';comparison=json.loads((froot/'comparison.json').read_text());assert comparison['feature_pairs']==42 and not comparison['changed']
functional=[]
ends={'sync':'/AE/SyncTasks2','student':'/ImageDetect/student/v1.0.0','teacher':'/ImageDetect/teacher/v1.0.0'}
quick_refs={(r['endpoint'],r['image_id']):norm(r['response']) for r in map(json.loads,(B/'quick-regression-20261119/trt-reference.jsonl').read_text().splitlines())}
quick={}
for name,endpoint in ends.items():
 files=sorted((B/'quick-regression-20261119/payloads'/name).glob('*.json'));assert len(files)==64
 for i,f in enumerate(files):
  body=json.loads(f.read_text());im=body['ImageList'][0];image_id=im.get('ImageId',im.get('ImageID'));quick[f'{name}-{i:02}']=(body,quick_refs[(endpoint,image_id)])
features={r['id']:r for r in map(json.loads,(B/'trt-migration-20261119-functional-r2/new-trt/responses.jsonl').read_text().splitlines()) if r['kind']=='feature'}
for label,expected in [('new-trt',810),('new-trt-restart',192)]:
 s=json.loads((froot/label/'result.json').read_text());rows=list(map(json.loads,(froot/label/'responses.jsonl').read_text().splitlines()));assert s['success'] and s['calls']==len(rows)==expected;assert all(r['status']==r['expected_status'] for r in rows)
 for r in rows:
  if r['kind']=='feature':
   expected=features[r['id']];assert r['status']==expected['status'] and norm(r['response'])==norm(expected['response'])
  else:
   body,expected=quick[r['id']];assert r['request_sha256']==hashlib.sha256(json.dumps(body,sort_keys=True).encode()).hexdigest() and norm(r['response'])==expected
 functional.append(dict(label=label,result=s,responses_sha256=sha(froot/label/'responses.jsonl')))
valid=[x for x in points if x['failed']==0];best=min(valid,key=lambda x:x['median_s']);eco=min((x for x in valid if x['median_s']<=best['median_s']*1.05),key=lambda x:(x['W'],x['C']));platform=[]
for W in (1,2,4,6):
 ps=[x for x in valid if x['W']==W];fast=min(ps,key=lambda x:x['median_s']);candidate=min((x for x in ps if x['median_s']<=fast['median_s']*1.05),key=lambda x:x['C']);platform.append(dict(W=W,fastest_C=fast['C'],fastest_s=fast['median_s'],platform_C=candidate['C'],platform_s=candidate['median_s']))
schemas=[]
for root in [audit,proot,froot]+[B/f'sync-trt-fixed100-20261123-w{w}-r1' for w in (1,2,4,6)]:
 for p in root.rglob('*openapi*.json'):schemas.append(json.loads(p.read_text()))
assert len(schemas)==31 and len(schemas[0]['paths'])==7 and all(x==schemas[0] for x in schemas)
final_audit=json.loads((B/'sync-trt-final-audit-20261123-r1/result.json').read_text());assert final_audit['code']==code and final_audit['git_clean'] and final_audit['openapi_equal']
output=dict(code=code,analyzer_sha256=sha(__file__),plan_sha256=sha(O/'plan.json'),continuation_plan_sha256=sha(CONT/'plan.json'),startup_guard_failure_preserved=True,fixed_groups=96,fixed_requests=9600,fixed_successful=sum(x['successful'] for x in cases),fixed_failed=sum(x['failed'] for x in cases),points=points,cases=cases,stages=stages,final_audit=final_audit,pressure=pressure,audit=audit_s,functional=functional,best=best,economical=eco,platform=platform)
a.output.mkdir();(a.output/'summary.json').write_text(json.dumps(output,ensure_ascii=False,indent=2))
with (a.output/'fixed-metrics.csv').open('w',newline='') as f:
 cols=['W','C','median_s','min_s','max_s','successful','failed','tps'];w=csv.DictWriter(f,fieldnames=cols,lineterminator='\n');w.writeheader();w.writerows({k:x[k] for k in cols} for x in points)
print(json.dumps(dict(fixed_groups=96,fixed_failed=output['fixed_failed'],best=best,pressure_failed=sum(x['failed'] for x in pressure))))
