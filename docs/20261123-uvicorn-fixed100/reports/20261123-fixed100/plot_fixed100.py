from pathlib import Path
import argparse,hashlib,json,subprocess,sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser();p.add_argument('summary',type=Path);p.add_argument('output',type=Path);a=p.parse_args();s=json.loads(a.summary.read_text());a.output.mkdir(exist_ok=False,parents=True);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();files=[]
plt.rcParams.update({'svg.hashsalt':'fixed100-20261123','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
for label,key,ylabel in [('makespan','median_s','100-image wall time (seconds)'),('throughput','tps_100_over_median','Successful images / second'),('p95','pooled_success_p95_ms','Successful request P95 (ms), pooled 300')]:
 fig,axes=plt.subplots(1,3,figsize=(16,4.8),layout='constrained')
 for ax,name,title in zip(axes,['sync','student','teacher'],['Person / face','Student behavior','Teacher behavior']):
  ps=[x for x in s['points'] if x['name']==name];xs=[x['C'] for x in ps];ys=[x[key] if x[key] is not None else float('nan') for x in ps]
  ax.plot(xs,ys,'o-',label='3-repeat median' if label!='p95' else 'Pooled success P95')
  if label=='makespan':ax.errorbar(xs,ys,yerr=[[x['median_s']-x['min_s'] for x in ps],[x['max_s']-x['median_s'] for x in ps]],fmt='none',capsize=4,color='#1765ad');best=min(x['median_s'] for x in ps if x['valid']);ax.axhline(best*1.05,color='#888',linestyle=':',label='105% of best median')
  failed=[x for x in ps if x['failed']]
  if failed:ax.scatter([x['C'] for x in failed],[x[key] or 0 for x in failed],marker='x',color='red',s=70,label='Failures')
  rec=s['recommendations'][name]
  if rec:ax.axvline(rec['platform_candidate'],color='#188869',linestyle='--',label='Smallest C within 5% of best')
  ax.set_xscale('log',base=2);ax.set_xticks(xs,[str(x) for x in xs]);ax.set_xlabel('Concurrent single-image HTTP requests');ax.set_ylabel(ylabel);ax.set_title(title);ax.set_ylim(bottom=0);ax.grid(alpha=.2)
 fig.suptitle('Direct Uvicorn main:app / workers=1 / TensorRT FP16 / fixed 100 images / b=512, q=0')
 handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='outside lower center',ncol=3,frameon=False)
 for ext in ['png','svg']:
  f=a.output/(label+'.'+ext);fig.savefig(f,dpi=160,metadata={'Date':None} if ext=='svg' else {})
  if ext=='svg':f.write_text('\n'.join(line.rstrip() for line in f.read_text().splitlines())+'\n')
  files.append(dict(file=f.name,sha256=sha(f),bytes=f.stat().st_size))
 plt.close(fig)
(a.output/'requirements.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze','--all'],text=True));(a.output/'manifest.json').write_text(json.dumps(dict(summary_sha256=sha(a.summary),script_sha256=sha(__file__),matplotlib=matplotlib.__version__,files=files),indent=2))
print(json.dumps(dict(images=len(files),summary_sha256=sha(a.summary))))
