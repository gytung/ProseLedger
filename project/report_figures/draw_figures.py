from pathlib import Path
import os
import tempfile
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "proseledger-mpl"))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon, Circle
from matplotlib import font_manager

OUT=Path(__file__).parent/'assets'
OUT.mkdir(exist_ok=True)
for p in Path('/System/Library/Fonts/Supplemental').glob('Times New Roman*.ttf'):
    font_manager.fontManager.addfont(str(p))
try:
    font_manager.findfont(font_manager.FontProperties(family='Times New Roman'), fallback_to_default=False)
    family = 'Times New Roman'
except ValueError:
    family = 'DejaVu Serif'
plt.rcParams.update({'font.family':family,'font.size':11,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
P='#79628F'; L='#C4B7D7'; LL='#F2EEF7'; S='#A8BCA3'; SL='#EFF4ED'; B='#8FBFDA'; BL='#EEF6FA'; A='#E8B792'; AL='#FCF1E9'; R='#CA8894'; INK='#443B4A'; G='#8C8A91'

def save(fig,name):
    for ext in ('pdf','svg','png'): fig.savefig(OUT/(name+'.'+ext),bbox_inches='tight',facecolor='white',dpi=180)
    plt.close(fig)

def label(ax,x,y,t,size=11,weight='normal',color=INK,ha='center',style='normal'):
    return ax.text(x,y,t,ha=ha,va='center',fontsize=size,fontweight=weight,color=color,fontstyle=style)

def rounded(ax,x,y,w,h,color,edge='none',r=.2):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle=f'round,pad=0.025,rounding_size={r}',facecolor=color,edgecolor=edge,lw=1))

def arrow(ax,a,b,color=P,rad=0,ls='-',lw=1.6):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=11,color=color,lw=lw,connectionstyle=f'arc3,rad={rad}',linestyle=ls))

fig,ax=plt.subplots(figsize=(13,5.4));ax.set(xlim=(0,13),ylim=(0,5.4));ax.axis('off')
label(ax,.3,5.13,'EXPRESSION CAN CHANGE. SCIENTIFIC COMMITMENTS MUST SURVIVE.',12,'bold',P,'left','italic')
for dx,dy in [(0,0),(.08,.08),(.16,.16)]:
    rounded(ax,.25+dx,3.09+dy,1.62,1.18,BL,'#B9D2DF',.08)
for y in [3.95,3.75,3.55]:ax.plot([.58,1.54],[y,y],color=B,lw=2)
label(ax,1.1,2.73,'Sources + proposal',11,'bold');label(ax,1.1,2.34,'Exact evidence packet\nand original claims',9)
arrow(ax,(2.05,3.72),(2.6,3.72),B)
rounded(ax,2.7,3.03,2.15,1.37,LL)
label(ax,3.78,4.1,'SECTION WRITER',11,'bold',P,style='italic')
label(ax,3.78,3.55,'Six editorial rules\nOne section at a time',10)
label(ax,3.78,2.55,'Direct verbs · clear relations\nPrecise scope · less repetition',9)
arrow(ax,(4.93,3.72),(5.49,3.72),L)
ax.add_patch(Polygon([[5.56,4.37],[7.65,4.37],[7.24,3.36],[6.73,3.03],[6.19,3.36]],closed=True,facecolor=SL,edgecolor='none'))
label(ax,6.6,4.05,'CONTEXTUAL REVIEW',10,'bold','#56734F',style='italic')
label(ax,6.6,3.65,'Meaning · evidence\nReadability',9)
label(ax,6.6,2.55,'Quotes identify the problem;\nnot a score alone',9)
arrow(ax,(7.58,3.72),(8.18,3.72),S)
rounded(ax,8.28,3.0,1.8,1.42,AL)
label(ax,9.18,4.05,'BOUNDED REPAIR',10,'bold','#A46C45',style='italic')
for y,x,w in [(3.71,8.57,1.23),(3.47,8.57,.65),(3.23,8.57,1.05)]:ax.plot([x,x+w],[y,y],color=A,lw=4,solid_capstyle='round')
label(ax,9.18,2.55,'Exact anchors; limited edits\nThen audit the whole draft',9)
arrow(ax,(10.15,3.72),(10.7,3.72),A)
rounded(ax,10.8,3.0,1.93,1.4,LL)
label(ax,11.77,4.08,'RETAIN',12,'bold',P,style='italic')
label(ax,11.77,3.57,'Checked candidate\nor original fallback',10)
label(ax,11.77,2.55,'Export the manuscript\nand its decision trail',9)
rounded(ax,2.75,.48,7.3,1.18,'#F8F6FA',r=.16)
label(ax,3.02,1.39,'REVISION LEDGER',11,'bold',P,'left','italic')
for i,(x,w,t,c) in enumerate([(3.03,1.62,'Original + candidate',B),(4.96,2.18,'Findings + exact patches',A),(7.43,2.3,'Decision + text hashes',L)]):
    ax.plot([x,x+w],[.92,.92],color=c,lw=4,solid_capstyle='round');label(ax,x,.68,t,9,ha='left')
arrow(ax,(6.6,2.17),(6.6,1.71),S)
arrow(ax,(9.18,2.17),(8.52,1.71),A)
arrow(ax,(11.76,2.17),(9.6,1.71),L)
label(ax,1.15,1.1,'Verification signals\nstay with the edit',10,'bold',P,style='italic')
label(ax,11.75,1.35,'GPTZero',11,'bold',P)
label(ax,11.75,.9,'After retention only\nSeparate observation',9)
arrow(ax,(11.77,2.15),(11.77,1.7),L,ls='--')
save(fig,'architecture')

fig,ax=plt.subplots(figsize=(6.2,3.8))
vals=[100,100,63.4231937627,100];names=['Evidence-linked','Lab handover','Citation preservation','Negative findings']
for y,(n,v) in enumerate(zip(names,vals)):
    ax.plot([v,100],[y,y],color=L,lw=5,solid_capstyle='round')
    ax.scatter(100,y,s=48,facecolor='white',edgecolor=G,zorder=4)
    ax.scatter(v,y,s=60,color=P,zorder=5)
    ax.text(v-2.3,y-.19,f'{v:.2f}%',ha='right',fontsize=10,color=P)
ax.set_yticks(range(4),names);ax.invert_yaxis();ax.set_xlim(0,108);ax.set_ylim(3.6,-.55)
ax.set_xticks([0,25,50,75,100]);ax.set_xlabel('GPTZero AI-class probability (%)')
ax.grid(axis='x',color='#EDEAF1',lw=.7);ax.set_axisbelow(True);ax.spines['left'].set_visible(False);ax.spines['bottom'].set_color('#D8D1E0');ax.tick_params(axis='y',length=0)
ax.set_title('Four fresh manuscripts · Mac MLX pilot',fontweight='bold',fontstyle='italic',color=P,pad=16)
fig.text(.18,.005,'Control: 100% each. Retained mean: 90.86%. All remain AI-classified.',fontsize=9,color=INK)
save(fig,'pilot_results')

fig,axs=plt.subplots(1,2,figsize=(10,2.8))
for ax,title,labs in zip(axs,['Source recognition','Fluency preference'],[['Published selected','Generated selected','Cannot tell'],['Revision selected','Initial selected','Cannot tell']]):
    left=0
    for v,c,lab in zip([4,5,1],[L,S,'#E6E1EA'],labs):
        ax.barh(0,v,left=left,color=c,height=.48);ax.text(left+v/2,0,str(v),ha='center',va='center',weight='bold',color=INK,fontsize=16);left+=v
    ax.set(xlim=(0,10),ylim=(-.65,.65),yticks=[],xticks=[]);ax.axis('off');ax.set_title(title,color=P,fontweight='bold',fontstyle='italic')
    for i,(lab,c) in enumerate(zip(labs,[L,S,'#E6E1EA'])):
        ax.scatter(.3,-.41-i*.2,s=35,color=c,clip_on=False);ax.text(.65,-.41-i*.2,lab,va='center',fontsize=10)
save(fig,'human_results')

fig,ax=plt.subplots(figsize=(6.2,3.6))
import numpy as np
ys=np.arange(3)
ax.barh(ys-.15,[2,12,12],height=.27,color=L,label='Violations detected / 12')
ax.barh(ys+.15,[11,12,11],height=.27,color=S,label='Valid edits allowed / 12')
for i,(a,b) in enumerate(zip([2,12,12],[11,12,11])):
    ax.text(a+.15,i-.15,str(a),va='center',fontsize=10,color=P)
    ax.text(b+.15,i+.15,str(b),va='center',fontsize=10,color='#56734F')
ax.set_yticks(ys,['Lexical guard','Semantic review','Both must pass']);ax.invert_yaxis();ax.set_xlim(0,13.2);ax.set_xticks([0,3,6,9,12]);ax.grid(axis='x',color='#EDEAF1',lw=.7);ax.set_axisbelow(True)
ax.spines['left'].set_visible(False);ax.spines['bottom'].set_color('#D8D1E0');ax.tick_params(axis='y',length=0)
ax.legend(loc='lower center',bbox_to_anchor=(.4,-.34),frameon=False,ncol=1,fontsize=10)
ax.set_title('Known-answer preservation challenge',fontweight='bold',fontstyle='italic',color=P,pad=15)
save(fig,'verifier_results')
