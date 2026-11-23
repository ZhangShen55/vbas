from pathlib import Path
import argparse,collections,csv,hashlib,json,statistics,shutil,sys,time
p=argparse.ArgumentParser();p.add_argument('evidence',type=Path);p.add_argument('output',type=Path);a=p.parse_args();r=a.evidence;plan=json.loads((r/'plan.json').read_text());cleanup=json.loads((r/'cleanup.json').read_text());post=json.loads((r/'post-cleanup-recheck.json').read_text());assert cleanup['port_closed'] and post['port_closed'] and not post['pid_exists'];assert all(x['gpu']=='3 MiB, 0 %' for x in post['samples']);assert not (r/'controller-error.txt').exists()
def percentile(v,q):
 v=sorted(v);x=(len(v)-1)*q;i=int(x);return v[i]+(v[min(i+1,len(v)-1)]-v[i])*(x-i)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
points=[];cases=[];resources=list(map(json.loads,(r/'resources.jsonl').read_text().splitlines()));roles={x['role'] for row in resources for x in row['processes']};assert roles=={'controller','server','load_generator'}
for job in plan['jobs']:
 d=r/job['label'];s=json.loads((d/'summary.json').read_text());rows=list(map(json.loads,(d/'responses.jsonl').read_text().splitlines()));assert len(rows)==100 and {x['sequence'] for x in rows}==set(range(100));assert all(x['image_id']==plan['pools'][job['name']]['selected'][x['sequence']]['image_id'] for x in rows)
 good=[x for x in rows if x['valid']];assert len(good)==s['successful'] and s['failed']==100-len(good);assert max(x['completed_offset_s'] for x in rows)==s['makespan_s']
 for k,q in [('p50',.5),('p95',.95),('p99',.99)]:
  if good:assert percentile([x['latency_ms'] for x in good],q)==s['latency_ms'][k]
 samples=[x for x in resources if s['started_unix']<=x['unix']<=s['ended_unix']];s.update(job=job,formal_resource_samples=len(samples),resource_pid_roles=sorted({v['role'] for x in samples for v in x['processes']}));cases.append(s)
for name in ['sync','student','teacher']:
 for c in [1,2,4,8,16,32,50,100]:
  cs=[s for s in cases if s['name']==name and s['C']==c];assert len(cs)==3
  lat=[x['latency_ms'] for s in cs for x in map(json.loads,(r/s['job']['label']/'responses.jsonl').read_text().splitlines()) if x['valid']];ts=[s['makespan_s'] for s in cs];good=all(s['all_100_successful'] for s in cs)
  points.append(dict(name=name,C=c,seconds=ts,median_s=statistics.median(ts),min_s=min(ts),max_s=max(ts),successful=sum(s['successful'] for s in cs),failed=sum(s['failed'] for s in cs),valid=good,tps_100_over_median=100/statistics.median(ts) if good else None,pooled_success_p95_ms=percentile(lat,.95) if lat else None,generator_cpu_percent=100*sum(s['generator_measurement_cpu_seconds'] for s in cs)/sum(ts),resource_samples=[s['formal_resource_samples'] for s in cs]))
recommend={}
for name in ['sync','student','teacher']:
 ps=[p for p in points if p['name']==name and p['valid']]
 if not ps:recommend[name]=None;continue
 best=min(ps,key=lambda x:x['median_s']);candidate=min((p for p in ps if p['median_s']<=best['median_s']*1.05),key=lambda x:x['C']);recommend[name]=dict(best=best['C'],platform_candidate=candidate['C'],candidate_median_s=candidate['median_s'],best_median_s=best['median_s'])
a.output.mkdir(parents=True,exist_ok=False);summary=dict(code=plan['code'],run_id=plan['run_id'],script_sha256=sha(Path(__file__)),plan_sha256=sha(r/'plan.json'),cases=cases,points=points,recommendations=recommend,cleanup=cleanup,roles_observed=sorted(roles),total_requests=7200,successful=sum(s['successful'] for s in cases),failed=sum(s['failed'] for s in cases))
summary['post_cleanup_recheck']=json.loads((r/'post-cleanup-recheck.json').read_text())
(a.output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
with (a.output/'metrics.csv').open('w',newline='') as f:
 fields=['name','C','median_s','min_s','max_s','successful','failed','tps_100_over_median','pooled_success_p95_ms','generator_cpu_percent'];w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows({k:x[k] for k in fields} for x in points)
print(json.dumps(dict(recommendations=recommend,successful=summary['successful'],failed=summary['failed'])))
