from pathlib import Path
import argparse,json,hashlib,subprocess,sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser();p.add_argument('summary',type=Path);p.add_argument('output',type=Path);a=p.parse_args();s=json.loads(a.summary.read_text());a.output.mkdir(parents=True,exist_ok=False);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();files=[]
plt.rcParams.update({'svg.hashsalt':'workers-fixed100-20261123','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
for label,key,ylabel in [('makespan','median_s','100-image wall time (seconds)'),('throughput','tps_100_over_median','Successful images / second'),('p95','pooled_success_p95_ms','Pooled successful request P95 (ms)')]:
 fig,axes=plt.subplots(1,3,figsize=(16,5),layout='constrained')
 for ax,name,title in zip(axes,['sync','student','teacher'],['Person / face','Student behavior','Teacher behavior']):
  for W,color in zip([1,2,4,6],['#1765ad','#de7b1c','#188869','#9256a8']):
   ps=[x for x in s['points'] if x['name']==name and x['W']==W];ps.sort(key=lambda x:x['C']);x=[p['C'] for p in ps];y=[p[key] if p[key] is not None else float('nan') for p in ps];ax.plot(x,y,'o-',color=color,label=f'workers={W}')
   if label=='makespan':ax.errorbar(x,y,yerr=[[p['median_s']-p['min_s'] for p in ps],[p['max_s']-p['median_s'] for p in ps]],fmt='none',color=color,capsize=2,alpha=.6)
   bad=[p for p in ps if p['failed']]
   if bad:ax.scatter([p['C'] for p in bad],[p[key] or 0 for p in bad],marker='x',color='red',s=60,zorder=5)
  best=s['best'][name]['fastest'];ax.scatter([best['C']],[best[key]],marker='*',s=160,facecolor='#ffca28',edgecolor='black',zorder=6)
  ax.set_xscale('log',base=2);ax.set_xticks([1,2,4,8,16,32,50,100],['1','2','4','8','16','32','50','100']);ax.set_xlabel('Total concurrent HTTP requests');ax.set_ylabel(ylabel);ax.set_title(title);ax.set_ylim(bottom=0);ax.grid(alpha=.2)
 fig.suptitle('Direct Uvicorn main:app / shared socket / FP16 RTX3090 / 100 images x 3 repeats / b512 q0')
 h,l=axes[0].get_legend_handles_labels();fig.legend(h,l,loc='outside lower center',ncol=4,frameon=False)
 for ext in ['png','svg']:
  f=a.output/(label+'.'+ext);fig.savefig(f,dpi=160,metadata={'Date':None} if ext=='svg' else {})
  if ext=='svg':f.write_text('\n'.join(x.rstrip() for x in f.read_text().splitlines())+'\n')
  files.append(dict(file=f.name,bytes=f.stat().st_size,sha256=sha(f)))
 plt.close(fig)
(a.output/'requirements.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze','--all'],text=True));(a.output/'manifest.json').write_text(json.dumps(dict(summary_sha256=sha(a.summary),script_sha256=sha(__file__),matplotlib=matplotlib.__version__,files=files),indent=2));print(json.dumps(dict(images=6)))
