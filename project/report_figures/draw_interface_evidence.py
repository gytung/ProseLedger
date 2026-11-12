from pathlib import Path
import argparse,json,re,hashlib,os,tempfile
os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'proseledger-mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import patches
from style import F

HERE=Path(__file__).resolve().parent
INK='#302B3A';PURPLE='#9985B3';BLUE='#8FBFDA';SAGE='#A8BCA3';APRICOT='#E8B792'

def word_count(text):return len(re.findall(r"\b[^\W_]+(?:[-'][^\W_]+)*\b",text))
def main():
 p=argparse.ArgumentParser();p.add_argument('--evaluation',type=Path,default=HERE.parent/'evaluation');p.add_argument('--captures',type=Path,default=HERE/'reference_ui');p.add_argument('--output',type=Path,default=HERE/'assets/extra');a=p.parse_args()
 folder=a.evaluation/'runs/C01/rules'; ledger=json.loads((folder/'revision_ledger.json').read_text(encoding='utf-8'));run=json.loads((folder/'run.json').read_text(encoding='utf-8'))
 assert (run['initialWords'],run['retainedWords'],run['changedSections'],run['localWriterCalls'])==(379,374,5,6)
 assert len(ledger['edits'][-1]['review']['issues'])==3
 assert ledger['edits'][-1]['original']==ledger['edits'][-1]['retained']
 counts=[[word_count(e[s]) for s in ('original','candidate','retained')] for e in ledger['edits']]
 fig=plt.figure(figsize=(6.5,5.38)); fig.patch.set_facecolor('white')
 ax=fig.add_axes([0,0,1,1]);ax.set(xlim=(0,6.5),ylim=(0,5.38));ax.axis('off')
 def t(x,y,s,size=8,style='body',ha='left',va='center',color=INK):return ax.text(x,y,s,fontproperties=F[style],fontsize=size,color=color,ha=ha,va=va,linespacing=1.2)
 def box(x,y,w,h,c):ax.add_patch(patches.FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0,rounding_size=.055',facecolor=c,edgecolor='none'))
 t(.10,5.20,'One retained manuscript, traced back to its visible edits',11,'title')
 t(.12,4.99,'C01 · Rules condition · frozen execution displayed in the desktop application',7.6,'italic')
 box(.1,4.56,6.3,.30,'#F1ECF7')
 for x,s in [(.24,'379 → 374 words'),(2.25,'5 of 6 sections changed'),(4.63,'6 local writer calls')]:t(x,4.71,s,8.1,'bold')
 t(.14,4.40,'Actual interface: the proposed limitation section',8.5,'title')
 im=plt.imread(a.captures/'desktop_candidate_narrow.png');ax.imshow(im,extent=(.14,6.36,2.45,4.29),aspect='auto',zorder=3)
 ax.plot([.12,6.38],[2.39,2.39],color='#D8D0E2',lw=.6)
 t(.14,2.22,'Section-level text footprint',9.2,'title')
 t(3.73,2.22,'Three findings → bounded repair → fallback',8.9,'title')
 plot=fig.add_axes([1.50/6.5,.49/5.38,1.92/6.5,1.48/5.38]);plot.set_facecolor('white')
 names=['Abstract','Introduction','Related work','Methodology','Planned evaluation','Limitations']
 for i,vals in enumerate(counts):
  y=5-i;plot.plot([min(vals),max(vals)],[y,y],color='#D6CBE4',lw=2.0,zorder=1)
  for off,v,c,m in zip([.10,0,-.10],vals,[BLUE,APRICOT,PURPLE],['o','D','o']):plot.scatter(v,y+off,s=17 if m=='D' else 20,color=c,edgecolors='white',linewidth=.4,marker=m,zorder=3)
  t(1.41,.49+(5-i+.5)/6*1.48,names[i],7.6,ha='right')
  t(3.45,.49+(5-i+.5)/6*1.48,'/'.join(map(str,vals)),7.0,ha='left')
 plot.set(xlim=(45,86),ylim=(-.5,5.5),yticks=[],xticks=[50,60,70,80]);plot.tick_params(labelsize=7,length=2,color='#B4A9C3',pad=2)
 for item in plot.get_xticklabels():item.set_fontproperties(F['body']);item.set_fontsize(7);item.set_color(INK)
 for s in ['top','left','right']:plot.spines[s].set_visible(False)
 plot.spines['bottom'].set_color('#D8D0E2')
 plot.grid(axis='x',lw=.4,color='#E9E4F0',zorder=0)
 t(2.46,.22,'Words per section body',7.3,'italic',ha='center')
 for x,c,m,s in [(.17,BLUE,'o','Original'),(1.25,APRICOT,'D','Candidate'),(2.47,PURPLE,'o','Retained')]:
  ax.scatter(x,2.02,s=18,color=c,marker=m,edgecolors='white',lw=.4);t(x+.11,2.02,s,7.2)
 xx=3.98
 for y,head,desc in [(1.83,'Possible trade-off → definite prediction','“may make” / “will leave”'),(1.40,'Unsupported explanation introduced','“as no field measurements …”'),(.97,'Conditional contribution strengthened','“would be” → “will be”')]:
  box(xx-.13,y-.23,2.48,.41,'#FBF1E9');t(xx,y+.035,head,7.4,'bold');t(xx,y-.125,desc,7.3,'italic')
 box(xx-.13,.30,2.48,.37,'#ECE7F4');t(xx,.51,'Deletion-only patch rejected.',7.5,'bold');t(xx,.365,'Original limitation section restored.',7.3,'italic')
 t(.12,.055,'The word counts describe edit extent, not quality. The retained record preserves the rejected candidate and its review.',7.0,'italic')
 a.output.mkdir(parents=True,exist_ok=True)
 for ext in ['pdf','svg','png']:fig.savefig(a.output/('interface_evidence.'+ext),dpi=330,facecolor='white',bbox_inches='tight',pad_inches=.02)
 plt.close(fig)
 data={'case':'C01','condition':'rules','sectionWords':dict(zip(names,counts)),'order':['original','candidate','retained'],'screenshot':'desktop_candidate_narrow.png','screenshotSHA256':hashlib.sha256((a.captures/'desktop_candidate_narrow.png').read_bytes()).hexdigest(),'ledgerSHA256':hashlib.sha256((folder/'revision_ledger.json').read_bytes()).hexdigest(),'runSHA256':hashlib.sha256((folder/'run.json').read_bytes()).hexdigest(),'newInferenceCalls':0}
 (a.output/'interface_evidence_data.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(data,indent=2))
if __name__=='__main__':main()
