"""Render independent revalidation aggregates; all measured points remain visible."""
from pathlib import Path
import argparse,json,hashlib,subprocess,sys,math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser();p.add_argument('summary',type=Path);p.add_argument('output',type=Path);a=p.parse_args();s=json.loads(a.summary.read_text());a.output.mkdir(parents=True);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();files=[];checks=[]
plt.rcParams.update({'svg.hashsalt':'sync-trt-revalidation-20261123','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
colors=['#1765ad','#de7b1c','#188869','#9256a8']
def save(fig,name):
 fig.canvas.draw()
 for ax in fig.axes:
  lo,hi=ax.get_ylim()
  for line in ax.lines:
   for y in line.get_ydata():
    if math.isfinite(float(y)):assert lo-1e-8<=y<=hi+1e-8,(name,lo,y,hi)
 for ext in ('png','svg'):
  f=a.output/(name+'.'+ext);fig.savefig(f,dpi=160,metadata={'Date':None} if ext=='svg' else {})
  if ext=='svg':f.write_text('\n'.join(x.rstrip() for x in f.read_text().splitlines())+'\n')
  files.append(dict(file=f.name,bytes=f.stat().st_size,sha256=sha(f)))
 checks.append(dict(figure=name,all_line_values_inside_y_limits=True));plt.close(fig)
fig,axes=plt.subplots(1,3,figsize=(16,5.3),layout='constrained')
for ax,key,title,ylabel in zip(axes,['median_s','tps','p95'],['100-image completion time','100 / median completion time','Single-request P95 (pooled 300)'],['Seconds','Successful images / second','Milliseconds']):
 for W,color in zip((1,2,4,6),colors):
  ps=sorted([x for x in s['points'] if x['W']==W],key=lambda x:x['C']);ys=[x['latency_ms']['p95'] if key=='p95' else x[key] for x in ps]
  ax.plot([x['C'] for x in ps],ys,'o-',color=color,label=f'workers={W}')
  if key=='median_s':ax.errorbar([x['C'] for x in ps],ys,yerr=[[x['median_s']-x['min_s'] for x in ps],[x['max_s']-x['median_s'] for x in ps]],fmt='none',color=color,capsize=2,alpha=.65)
 b=s['best'];ax.scatter(b['C'],b['latency_ms']['p95'] if key=='p95' else b[key],marker='*',s=170,facecolor='#ffca28',edgecolor='black',zorder=6)
 ax.set_xscale('log',base=2);ax.set_xticks([1,2,4,8,16,32,50,100],['1','2','4','8','16','32','50','100']);ax.set_xlabel('Total concurrent HTTP requests');ax.set_ylabel(ylabel);ax.set_title(title);ax.set_ylim(bottom=0);ax.grid(alpha=.2)
fig.suptitle('/AE/SyncTasks2 parallel / FP16 RTX3090 / shared Uvicorn socket / 100 images x 3 repeats')
fig.legend(*axes[0].get_legend_handles_labels(),loc='outside lower center',ncol=4,frameon=False);save(fig,'fixed100')
fig,axes=plt.subplots(1,3,figsize=(16,5.3),layout='constrained')
for I,color in zip((1,2,4),colors):
 ps=sorted([x for x in s['pressure'] if x['job']['instances']==I],key=lambda x:x['job']['concurrency']);cs=[x['job']['concurrency'] for x in ps]
 for ax,ys in zip(axes,[[x['tps'] for x in ps],[x['latency_ms']['p95'] for x in ps],[x['failed'] for x in ps]]):ax.plot(cs,ys,'o-',color=color,label=f'instances={I}, one worker each')
 for x in ps:
  if x['failed']:
   axes[0].scatter(x['job']['concurrency'],x['tps'],marker='x',color='red',s=90,zorder=6)
   axes[0].annotate('failures: '+str(x['failed']),(x['job']['concurrency'],x['tps']),xytext=(0,8),textcoords='offset points',ha='center',fontsize=8)
for ax,title,ylabel in zip(axes,['Successful completions inside 180 s','Successful request P95 (incl. drain)','All observed failed requests'],['Images / second','Milliseconds','Count']):
 ax.set_xlabel('Total concurrent HTTP requests');ax.set_xticks([50,100,200]);ax.set_title(title);ax.set_ylabel(ylabel);ax.set_ylim(bottom=0);ax.margins(y=.18);ax.grid(alpha=.2)
from matplotlib.ticker import MaxNLocator
axes[2].yaxis.set_major_locator(MaxNLocator(integer=True))
fig.suptitle('/AE/SyncTasks2 parallel / full 2162-image pool / 180 s closed loop / failures retained')
fig.legend(*axes[0].get_legend_handles_labels(),loc='outside lower center',ncol=3,frameon=False);save(fig,'pressure')
(a.output/'requirements.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze','--all'],text=True));(a.output/'manifest.json').write_text(json.dumps(dict(summary_sha256=sha(a.summary),script_sha256=sha(__file__),matplotlib=matplotlib.__version__,files=files,range_checks=checks),indent=2));print(json.dumps(dict(images=len(files))))
