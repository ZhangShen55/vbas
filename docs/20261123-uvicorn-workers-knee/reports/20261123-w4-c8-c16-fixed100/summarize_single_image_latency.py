"""从已封存响应离线补充单图HTTP耗时；不启动服务、不改原始记录。"""
from pathlib import Path
import argparse,hashlib,json,math,statistics
p=argparse.ArgumentParser();p.add_argument('raw',type=Path);p.add_argument('historical_raw',type=Path);p.add_argument('historical_checksums',type=Path);p.add_argument('summary',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pct(v,q):
 v=sorted(v);x=(len(v)-1)*q;i=int(x);return v[i]+(v[min(i+1,len(v)-1)]-v[i])*(x-i)
s=json.loads(a.summary.read_text());old_checksums=json.loads(a.historical_checksums.read_text());new_plan=json.loads((a.raw/'plan.json').read_text());old_plan=json.loads((a.historical_raw/'plan.json').read_text())
for k in ('code','pools','engines','manifest_sha256','source_config_sha256'):assert new_plan[k]==old_plan[k]
points=[]
for name in ('sync','student','teacher'):
 for C in (1,8,16):
  root=a.historical_raw if C==1 else a.raw;lat=[];sources=[];makespans=[]
  for rep in (1,2,3):
   label=f'{name}-r{rep}-c{C}';file=root/label/'responses.jsonl';digest=sha(file)
   if C==1:
    key=f'vbas-benchmarks/{root.name}/{label}/responses.jsonl';assert digest==old_checksums[key]['sha256'] and file.stat().st_size==old_checksums[key]['bytes']
   else:assert digest==next(c['responses_sha256'] for c in s['cases'] if c['label']==label)
   rows=[json.loads(t) for t in file.read_text().splitlines()];assert len(rows)==100 and {r['sequence'] for r in rows}==set(range(100));assert all(r['valid'] and r['status']==200 and math.isfinite(r['latency_ms']) for r in rows)
   assert all(r['image_id']==new_plan['pools'][name]['selected'][r['sequence']]['image_id'] for r in rows)
   summary=json.loads((root/label/'summary.json').read_text());assert summary['requests']==summary['successful']==100 and summary['failed']==0 and max(r['completed_offset_s'] for r in rows)==summary['makespan_s']
   makespans.append(summary['makespan_s']);lat.extend(r['latency_ms'] for r in rows);sources.append(dict(label=label,responses_sha256=digest))
  result=dict(name=name,C=C,workers=4,requests=300,source_run_id=root.name,latency_ms=dict(mean=statistics.mean(lat),p50=pct(lat,.5),p95=pct(lat,.95),p99=pct(lat,.99)),median_100_makespan_s=statistics.median(makespans),amortized_ms_per_image=statistics.median(makespans)*1000/100,sources=sources)
  if C!=1:
   old=next(x for x in s['points'] if x['name']==name and x['C']==C)
   for key in ('p50','p95','p99'):assert result['latency_ms'][key]==old['latency_ms'][key]
  points.append(result)
output=dict(code=new_plan['code'],workers=4,source_summary_sha256=sha(a.summary),historical_checksums_sha256=sha(a.historical_checksums),script_sha256=sha(__file__),points=points,scope='客户端每次发送POST至完整response body收到；含客户端/连接/HTTP/服务内等待及图像业务处理，非纯模型forward。C1为历史独立测试，C8/C16为本轮复核；各档合并3轮300条。amortized_ms_per_image仅为吞吐摊销，非并发下单请求时延。')
assert not a.output.exists();a.output.write_text(json.dumps(output,ensure_ascii=False,indent=2));print(json.dumps([dict(name=x['name'],C=x['C'],**x['latency_ms']) for x in points],ensure_ascii=False))
