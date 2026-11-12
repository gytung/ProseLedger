from pathlib import Path
import hashlib
import json
import os
import argparse
import tempfile

os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir())/'proseledger-mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyBboxPatch, Polygon, PathPatch, FancyArrowPatch
from matplotlib.path import Path as VectorPath
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import numpy as np
from style import C, F, mix, canvas, text, box, arrow, line, page, agent, save

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'assets' / 'strategy'
DATA_PATH = ROOT / 'strategy_figure_data.json'
DATA = None
INK = '#302B3A'


def t(ax,x,y,s,size=7.4,style='body',ha='left',color=INK,va='center',**kw):
    return text(ax,x,y,s,size,style,color,ha=ha,va=va,**kw)


def header(ax,h,title,subtitle=None):
    t(ax,.12,h-.16,title,10.8,'title')
    if subtitle:t(ax,.12,h-.36,subtitle,7.0,color=C['muted'])


def human(ax,x,y,color='sage',s=1):
    ax.add_patch(Ellipse((x,y-.015*s),.27*s,.032*s,facecolor=mix('gray',.70),edgecolor='none',zorder=2))
    torso=VectorPath([(x-.12*s,y),(x-.13*s,y+.12*s),(x-.05*s,y+.17*s),(x,y+.16*s),
                     (x+.05*s,y+.17*s),(x+.13*s,y+.12*s),(x+.12*s,y),(x-.12*s,y)],
                    [VectorPath.MOVETO]+[VectorPath.CURVE4]*6+[VectorPath.CLOSEPOLY])
    ax.add_patch(PathPatch(torso,facecolor=mix(color,.78),edgecolor='none',zorder=5))
    ax.add_patch(Circle((x,y+.20*s),.075*s,facecolor=mix('apricot',.45),edgecolor='none',zorder=6))
    hair=VectorPath([(x-.075*s,y+.22*s),(x-.08*s,y+.33*s),(x+.08*s,y+.33*s),(x+.075*s,y+.22*s),
                    (x+.01*s,y+.255*s),(x-.035*s,y+.27*s),(x-.075*s,y+.22*s)],
                   [VectorPath.MOVETO]+[VectorPath.CURVE4]*6)
    ax.add_patch(PathPatch(hair,facecolor=INK,edgecolor='none',alpha=.70,zorder=7))
    for d in [-.028,.028]:
        ax.add_patch(Ellipse((x+d*s,y+.205*s),.052*s,.033*s,facecolor='white',edgecolor=INK,lw=.35,zorder=8))
    line(ax,(x-.008*s,y+.205*s),(x+.008*s,y+.205*s),'ink',.35,z=8)


def abacus(ax,x,y,w=.40,h=.30):
    box(ax,x,y,w,h,'apricot',.18,edge=True,r=.035,z=4)
    for yy in [.07,.15,.23]:line(ax,(x+.04,y+yy),(x+w-.04,y+yy),'lavender',.55,z=5)
    for xx,yy,c in [(.10,.07,'lavender'),(.16,.07,'lavender'),(.27,.15,'sage'),(.32,.15,'sage'),(.10,.23,'sky'),(.18,.23,'sky'),(.25,.23,'sky')]:
        ax.add_patch(Ellipse((x+xx,y+yy),.044,.068,facecolor=C[c],edgecolor='white',lw=.25,zorder=6))


def curved(ax,pts,color='apricot',lw=.8):
    path=VectorPath(pts,[VectorPath.MOVETO]+[VectorPath.CURVE4]*3)
    ax.add_patch(FancyArrowPatch(path=path,arrowstyle='-|>',mutation_scale=5.4,color=C[color],lw=lw,zorder=5))


def opportunities():
    fig,ax=canvas(6.5,3.46)
    header(ax,3.46,'Shared capabilities, different approval paths',
           'A common editing service enters three distinct purchasing and review workflows.')
    # Shared core is a horizontal layer with a visible cross-row reuse spine.
    box(ax,.13,2.61,6.21,.35,'lavender',.22,r=.055)
    t(ax,.24,2.785,'REUSED CORE',6.9,'flow')
    stages=[(1.35,'Evidence'),(2.37,'Rule-guided edit'),(3.62,'Contextual review'),(4.98,'Retain + record')]
    for x,label in stages:t(ax,x,2.785,label,7.4,'bold')
    for start,end in [(1.91,2.29),(3.28,3.53),(4.64,4.90)]:arrow(ax,(start,2.785),(end,2.785),'lavender',lw=.9,head=5)
    # Table columns show relationships, not unmeasured market magnitudes.
    xs=[.25,1.34,2.55,4.24,5.25]
    labels=['Opportunity','Document / commitment','Author → approver','Buyer','Proposed pilot']
    for x,label in zip(xs,labels):t(ax,x,2.39,label,7.1,'title')
    rows=[
        (1.91,'lavender','University\nproposal support','Proposal\nEvidence; planned status','Author','Adviser','Programme\nmanager','30 proposals · 4 weeks\n10 authors · 2 advisers'),
        (1.18,'sky','Scholarly\nauthor services','Article sections\nScientific meaning','Editor','Author /\nscientific editor','Editorial\noperations','40 sections · 5 weeks\nAt least 2 disciplines'),
        (.45,'sage','R&D SME\nconcept notes','Concept note\nQuantities; commitments','Engineer','Technical\nlead','Founder /\nproject lead','20 notes · 6 weeks\n2 firms')]
    line(ax,(.105,2.61),(.105,.44),'lavender',.7)
    for y,c,sector,doc,user,approver,buyer,pilot in rows:
        box(ax,.16,y-.25,6.18,.59,c,.13,r=.045)
        line(ax,(.105,y),(.20,y),c,.8)
        t(ax,.25,y+.045,sector,8.0,'title')
        page(ax,1.33,y-.09,.20,.29,c,rows=1)
        t(ax,1.60,y+.035,doc,7.15)
        human(ax,2.73,y+.03,c,.71)
        human(ax,3.55,y+.03,c,.71)
        arrow(ax,(2.91,y+.15),(3.35,y+.15),c,.9,head=5)
        t(ax,2.73,y-.13,user,7.0,'bold',ha='center')
        t(ax,3.55,y-.145,approver,7.0,'bold',ha='center')
        t(ax,4.24,y+.035,buyer,7.3,'bold')
        t(ax,5.25,y+.035,pilot,7.05)
    # The shaded rows share a service but not an approval owner or buyer.
    t(ax,.18,.075,'Trial counts are prospective study plans; assess approved output, review effort and material errors.',6.85,'italic',color=C['muted'])
    save(fig,OUT/'strategy_opportunity_routes')


def architecture():
    fig,ax=canvas(6.5,4.02)
    header(ax,4.02,'Reuse the core; adapt the document and approval contract')
    t(ax,.16,3.64,'A   PROPOSED DOMAIN ADAPTERS',7.0,'flow')
    # One linked change matrix carries the domain distinctions without isolated module boxes.
    frame=FancyBboxPatch((.11,2.47),6.26,1.04,boxstyle='round,pad=0,rounding_size=.05',
                        facecolor=mix('apricot',.08),edgecolor=C['apricot'],lw=.65,linestyle=(0,(3,2.4)),zorder=1)
    ax.add_patch(frame)
    cols=[.24,1.56,3.22,5.03]
    for x,l in zip(cols,['Domain','Format adapter','Protected relations','Approval owner']):t(ax,x,3.37,l,7.0,'title')
    entries=[
        (3.12,'lavender','University','Six-section proposal','Evidence; planned status','Author + adviser'),
        (2.86,'sky','Author services','Original / revised section','Claims; conditions; attribution','Editor + author'),
        (2.60,'sage','R&D SME','Concept-note template','Quantity–role; exclusions','Technical owner')]
    for y,c,a,b,d,e in entries:
        ax.add_patch(Circle((.20,y),.023,facecolor=C[c],edgecolor='none',zorder=5))
        for x,l in zip(cols,[a,b,d,e]):t(ax,x,y,l,7.15,'bold' if x==cols[0] else 'body')
        if y>2.6:line(ax,(.21,y-.125),(6.24,y-.125),c,.45)
    # Existing stages are nested under a shared editing and admission layer.
    box(ax,.15,.34,4.63,1.92,'lavender',.12,r=.10)
    t(ax,.29,2.12,'B   IMPLEMENTED REVISION + ADMISSION',7.0,'flow')
    contract_path=VectorPath([(.25,2.47),(.12,2.15),(.15,1.92),(.39,1.88)],[VectorPath.MOVETO]+[VectorPath.CURVE4]*3)
    ax.add_patch(FancyArrowPatch(path=contract_path,arrowstyle='-|>',mutation_scale=5,color=C['apricot'],lw=.8,linestyle=(0,(3,2.4)),zorder=5))
    t(ax,.69,2.355,'Apply the selected contract',6.9,'italic',color=C['muted'])
    page(ax,.33,1.41,.31,.43,'sky',rows=2)
    t(ax,.48,1.21,'Evidence\n+ draft',7.3,'bold',ha='center')
    agent(ax,1.28,1.40,'sky',scale=1.05)
    page(ax,1.57,1.43,.15,.24,'lavender',rows=1)
    t(ax,1.47,1.20,'Section writer',7.35,'bold',ha='center')
    t(ax,1.47,1.02,'Six explicit rules',6.9,'italic',ha='center')
    agent(ax,2.62,1.40,'sage',scale=1.05)
    ax.add_patch(Circle((2.97,1.62),.10,facecolor=mix('sage',.22),edgecolor=C['sage'],lw=.7,zorder=8))
    line(ax,(3.04,1.55),(3.12,1.46),'sage',1.0,z=9)
    t(ax,2.80,1.20,'Contextual review',7.35,'bold',ha='center')
    t(ax,2.80,1.02,'Claims + sources',6.9,'italic',ha='center')
    funnel=[(3.78,1.76),(4.20,1.76),(4.05,1.52),(4.05,1.39),(3.94,1.35),(3.94,1.52)]
    ax.add_patch(Polygon(funnel,facecolor=mix('lavender',.55),edgecolor=C['lavender'],lw=.7,zorder=6))
    t(ax,4.00,1.19,'Retain?',7.35,'bold',ha='center')
    for a,b,c in [((.72,1.63),(1.19,1.63),'sky'),((1.82,1.63),(2.51,1.63),'lavender'),((3.20,1.63),(3.69,1.63),'sage')]:arrow(ax,a,b,c,.95,head=5.5)
    t(ax,2.13,1.82,'candidate',6.7,'flow',ha='center')
    page(ax,2.06,.48,.23,.31,'apricot',rows=1)
    line(ax,(2.24,.48),(2.36,.70),'ink',1.0,z=8)
    t(ax,1.88,.59,'Bounded\nrepair',7.15,'bold',ha='right')
    curved(ax,[(2.97,.95),(3.01,.73),(2.59,.61),(2.42,.61)],'apricot')
    curved(ax,[(2.05,.67),(1.91,.80),(2.35,1.45),(2.56,1.46)],'apricot')
    t(ax,1.74,.90,'recheck',6.7,'flow',ha='center')
    abacus(ax,4.12,.50,.43,.30)
    t(ax,4.33,.385,'Decision ledger',6.9,'bold',ha='center')
    curved(ax,[(4.08,1.41),(4.48,1.36),(4.60,.99),(4.42,.84)],'lavender',.7)
    t(ax,4.83,1.14,'record',6.7,'flow',ha='center')
    # Output lies beside—not inside—the proposed human-approval envelope.
    page(ax,5.35,1.39,.35,.49,'lavender',rows=2)
    arrow(ax,(4.26,1.63),(5.24,1.63),'lavender',.95,head=5.5)
    t(ax,4.83,1.84,'admit / fall back',6.9,'italic',ha='center')
    t(ax,5.53,1.18,'Retained text',7.35,'bold',ha='center')
    t(ax,5.53,1.00,'or unchanged original',6.8,'italic',ha='center')
    governance=FancyBboxPatch((4.99,.37),1.25,.43,boxstyle='round,pad=0,rounding_size=.06',
                             facecolor=mix('apricot',.10),edgecolor=C['apricot'],lw=.6,linestyle=(0,(3,2.3)))
    ax.add_patch(governance);human(ax,5.14,.44,'apricot',.75)
    t(ax,5.41,.60,'Human approval',7.0,'bold')
    arrow(ax,(5.66,.82),(5.66,.93),'apricot',.7,ls='--',head=4.5)
    t(ax,.17,.12,'Solid: existing core',6.9,'bold')
    t(ax,1.78,.12,'Dashed: proposed domain / approval integration',6.9,'italic')
    t(ax,6.32,.12,'Run-local ledger',6.9,'bold',ha='right')
    save(fig,OUT/'strategy_adaptation_architecture')


def cost_sensitivity():
    spec=DATA['figures'][2]
    values=np.array(spec['net_value_per_document'],float)
    gross=np.array(spec['row_gross_saved_minutes'],float)
    checking=np.array(spec['column_extra_check_minutes'],float)
    rate=spec['staff_cost_per_hour'];cost=spec['nonlabour_cost_per_document']
    assert np.array_equal(values,(gross[:,None]-checking[None,:])*rate/60-cost)
    fig,baseax=canvas(6.5,3.34)
    header(baseax,3.34,'Review time determines the value of faster editing',
           'Illustrative assumptions: S$60 per staff hour; S$3 non-labour cost per document.')
    t(baseax,.18,2.75,'A   NET VALUE PER DOCUMENT',7.0,'flow')
    t(baseax,3.52,2.75,'B   ADDITIONAL CHECKING SCENARIOS',7.0,'flow')
    hm=fig.add_axes([.105,.252,.365,.525])
    cmap=LinearSegmentedColormap.from_list('net_value',[C['apricot'],'#FCFBFE',C['lavender']])
    hm.imshow(values,cmap=cmap,norm=TwoSlopeNorm(vmin=-15,vcenter=0,vmax=15),aspect='auto')
    for i in range(3):
        for j in range(3):
            value=int(values[i,j]);label=('−' if value<0 else '')+'S$'+str(abs(value))
            hm.text(j,i,label,ha='center',va='center',fontsize=10.4,fontproperties=F['bold'],color=INK,parse_math=False)
    for k in [.5,1.5]:hm.axvline(k,color='white',lw=2.5);hm.axhline(k,color='white',lw=2.5)
    hm.set_xticks([0,1,2],['0','6','12']);hm.set_yticks([0,1,2],['6','12','18'])
    hm.tick_params(length=0,pad=3)
    for tick in hm.get_xticklabels()+hm.get_yticklabels():tick.set_fontproperties(F['body']);tick.set_fontsize(7.2);tick.set_color(INK)
    hm.set_xlabel('Additional checking (min)',fontproperties=F['bold'],fontsize=7.4,color=INK,labelpad=4)
    hm.set_ylabel('Gross time saved (min)',fontproperties=F['bold'],fontsize=7.4,color=INK,labelpad=5)
    for spine in hm.spines.values():spine.set_visible(False)
    hm.add_patch(matplotlib.patches.Rectangle((.52,.52),.96,.96,fill=False,lw=1.1,edgecolor='#9F89B7'))
    chart=fig.add_axes([.578,.252,.365,.525])
    colors=[C['lavender'],C['sky'],C['sage']]
    for j,(extra,col) in enumerate(zip(checking,colors)):
        chart.plot(gross,values[:,j],color=col,lw=1.35,marker='o',ms=4.0,mec='white',mew=.65)
        chart.annotate(f'{int(extra)} min',xy=(18,values[-1,j]),xytext=(5,0),textcoords='offset points',
                       ha='left',va='center',fontsize=7,fontproperties=F['bold'],color=INK)
    chart.axhline(0,color='#92889B',lw=.65,ls=(0,(3,3)))
    chart.set(xlim=(5.2,21.1),ylim=(-10.2,16.9),xticks=[6,12,18],yticks=[-9,-3,0,3,9,15])
    chart.tick_params(length=2,width=.45,pad=2.2)
    for tick in chart.get_xticklabels()+chart.get_yticklabels():tick.set_fontproperties(F['body']);tick.set_fontsize(7.0);tick.set_color(INK)
    chart.spines['top'].set_visible(False);chart.spines['right'].set_visible(False)
    for k in ['left','bottom']:chart.spines[k].set_color('#C3BDCA');chart.spines[k].set_linewidth(.55)
    chart.grid(axis='y',color='#EAE6EE',lw=.5);chart.set_axisbelow(True)
    chart.set_xlabel('Gross time saved (min)',fontproperties=F['bold'],fontsize=7.4,color=INK,labelpad=4)
    chart.set_ylabel('Net value (S$ / document)',fontproperties=F['bold'],fontsize=7.3,color=INK,labelpad=4)
    t(baseax,.16,.42,'Central scenario: 12 min saved, 6 min checking → S$3 net/document; 50 documents → S$150 before extra fixed cost.',6.85)
    t(baseax,.16,.23,'Covering S$3 requires 4.5 / 3.0 / 1.8 net minutes saved at staff costs of S$40 / S$60 / S$100 per hour.',6.85,'italic',color=C['muted'])
    t(baseax,.16,.075,'Scenario analysis only; none of these values is an observed ProseLedger saving.',6.85,'bold')
    save(fig,OUT/'strategy_cost_sensitivity')


def provenance():
    names=[x['id'] for x in DATA['figures']]
    result={
        'generator':'draw_strategy.py','shared_style':'style.py',
        'canvas':'white','text_color':INK,'nominal_width_inches':6.5,
        'input_data':'strategy_figure_data.json','input_sha256':hashlib.sha256(DATA_PATH.read_bytes()).hexdigest(),
        'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'helper_sha256':hashlib.sha256((ROOT/'style.py').read_bytes()).hexdigest(),
        'data_changed':False,
        'semantics':'Proposed pilots and domain adapters; implemented editing core; exact illustrative economic scenarios.',
        'figures':{n:{e:hashlib.sha256((OUT/f'{n}.{e}').read_bytes()).hexdigest() for e in ['pdf','svg','png']} for n in names}
    }
    (OUT/'PROVENANCE.json').write_text(json.dumps(result,indent=2)+'\n', encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Render strategic analysis figures from the included scenarios.')
    parser.add_argument('--data',type=Path,default=DATA_PATH)
    parser.add_argument('--output-dir',type=Path,default=OUT)
    args=parser.parse_args()
    DATA_PATH=args.data
    DATA=json.loads(DATA_PATH.read_text(encoding='utf-8'))
    OUT=args.output_dir
    OUT.mkdir(parents=True,exist_ok=True)
    opportunities();architecture();cost_sensitivity();provenance()
    print('Three publication-scale strategy figures written; input data unchanged.')
