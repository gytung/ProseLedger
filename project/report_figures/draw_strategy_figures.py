from pathlib import Path
import json
import os
import tempfile

os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'proseledger-mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Polygon, FancyArrowPatch, PathPatch, Rectangle
from matplotlib.path import Path as MplPath
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib import font_manager
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'assets' / 'strategy'
OUT.mkdir(parents=True, exist_ok=True)
DATA = json.loads((ROOT / 'strategy_figure_data.json').read_text())
P = DATA['style']
INK = P['title']
MUTED = '#6C6571'
LAV = P['lavender']
SAGE = P['sage']
SKY = P['sky']
APR = P['apricot']
ROSE = P['rose']

for f in Path('/System/Library/Fonts/Supplemental').glob('Times New Roman*.ttf'):
    font_manager.fontManager.addfont(str(f))
try:
    font_manager.findfont(font_manager.FontProperties(family='Times New Roman'), fallback_to_default=False)
    family = 'Times New Roman'
except ValueError:
    family = 'DejaVu Serif'
plt.rcParams.update({
    'font.family': family, 'font.size': 12, 'text.color': INK,
    'axes.labelcolor': INK, 'xtick.color': INK, 'ytick.color': INK,
    'svg.fonttype': 'none', 'pdf.fonttype': 42, 'text.parse_math': False,
    'savefig.facecolor': 'white', 'figure.facecolor': 'white',
})

def light(hexcolor, strength=.20):
    v = np.array(matplotlib.colors.to_rgb(hexcolor))
    return tuple(1 - strength * (1-v))

def text(ax, x, y, s, size=12, ha='left', va='center', bold=False,
         italic=False, color=INK, **kw):
    return ax.text(x, y, s, fontsize=size, ha=ha, va=va,
                   weight='bold' if bold else 'normal',
                   style='italic' if italic else 'normal', color=color,
                   linespacing=1.15, **kw)

def rounded(ax, x, y, w, h, face, edge='none', lw=.8, radius=.015,
            dashed=False, z=1):
    p = FancyBboxPatch((x,y),w,h,boxstyle=f'round,pad=0,rounding_size={radius}',
                      facecolor=face, edgecolor=edge, linewidth=lw,
                      linestyle=(0,(4,3)) if dashed else '-', zorder=z)
    ax.add_patch(p)
    return p

def arrow(ax, a, b, color=LAV, lw=1.4, curve=0, dashed=False, ms=12, z=2):
    p=FancyArrowPatch(a,b,arrowstyle='-|>', mutation_scale=ms,
                     linewidth=lw,color=color,connectionstyle=f'arc3,rad={curve}',
                     linestyle=(0,(4,3)) if dashed else '-',zorder=z)
    ax.add_patch(p)
    return p

def page(ax,x,y,w=.064,h=.085,color=SKY,stack=True):
    if stack:
        rounded(ax,x+.009,y-.009,w,h,light(color,.30),radius=.006,z=3)
        rounded(ax,x+.004,y-.004,w,h,'white',light(color,.8),radius=.006,z=4)
    rounded(ax,x,y,w,h,'white',color,lw=1.1,radius=.006,z=5)
    for i,frac in enumerate([.70,.83,.64]):
        yy=y+h*(.72-.19*i)
        ax.plot([x+w*.15,x+w*frac],[yy,yy],color=color,lw=1.5,zorder=6)

def person(ax,x,y,color,rx=.022,ry=.032):
    ax.add_patch(matplotlib.patches.Ellipse((x,y),rx*2,ry*2,facecolor=light(color,.28),edgecolor='none',zorder=3))
    ax.add_patch(Circle((x,y+.007),.0055,facecolor=INK,edgecolor='none',alpha=.70,zorder=4))
    p=PathPatch(MplPath([(x-.010,y-.013),(x-.011,y+.001),(x+.011,y+.001),(x+.010,y-.013)],
                       [MplPath.MOVETO,MplPath.CURVE4,MplPath.CURVE4,MplPath.CURVE4]),
                facecolor=INK,edgecolor='none',alpha=.70,zorder=4)
    ax.add_patch(p)

def canvas(w,h,title,subtitle=None):
    fig,ax=plt.subplots(figsize=(w,h))
    ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    fig.subplots_adjust(left=.025,right=.975,bottom=.025,top=.975)
    text(ax,.02,.963,title,20,bold=True,italic=True)
    if subtitle: text(ax,.02,.914,subtitle,11.7,color=MUTED)
    return fig,ax

def save(fig,name):
    for ext in ['pdf','svg','png']:
        fig.savefig(OUT/f'{name}.{ext}', dpi=240, facecolor='white')
    plt.close(fig)

def opportunity_routes():
    fig,ax=canvas(10.6,7.3,'Three entry points, three approval paths',
                  'One revision core; different users, approval authority and purchasing decisions.')
    for x,label in [(.38,'USER'),(.61,'APPROVAL'),(.84,'BUYER')]:
        text(ax,x,.85,label,10.5,ha='center',bold=True,color=MUTED)
    rows=[
        {'y':.712,'color':LAV,'title':'University\nproposal support',
         'need':'Preserve evidence and\nproposed research status.',
         'roles':['Research\nauthor','Adviser','Programme\nmanager'],
         'pilot':'Proposed pilot: 30 proposals · 10 authors · 2 advisers · 4 weeks',
         'metric':'Decision: total editing time + material errors'},
        {'y':.440,'color':SKY,'title':'Scholarly\nauthor services',
         'need':'Preserve scientific meaning\nacross language edits.',
         'roles':['Professional\neditor','Author /\nscientific editor','Editorial operations\nmanager'],
         'pilot':'Proposed pilot: 40 authorised sections · 2+ disciplines · 5 weeks',
         'metric':'Decision: review time + accepted alerts + rework'},
        {'y':.168,'color':SAGE,'title':'R&D SME\nconcept notes',
         'need':'Preserve quantities,\nexclusions and commitments.',
         'roles':['Engineer /\ntechnical author','Technical\nlead','Founder /\nproject lead'],
         'pilot':'Proposed pilot: 20 completed notes · 2 firms · 6 weeks',
         'metric':'Decision: review effort + commitment errors'},
    ]
    for i,r in enumerate(rows):
        y,c=r['y'],r['color']
        rounded(ax,.02,y-.123,.96,.241,light(c,.12),radius=.024)
        rounded(ax,.02,y-.123,.009,.241,c,radius=.005,z=2)
        text(ax,.047,y+.069,r['title'],16,bold=True,italic=True)
        text(ax,.047,y-.002,r['need'],10.7,color=MUTED)
        for x,label in zip([.38,.61,.84],r['roles']):
            person(ax,x,y+.074,c)
            text(ax,x,y+.012,label,12.7,ha='center',bold=True)
        for a,b in [(.422,.568),(.652,.798)]:
            arrow(ax,(a,y+.067),(b,y+.067),c,lw=1.8,ms=12)
        text(ax,.302,y-.060,r['pilot'],11.2,bold=True)
        text(ax,.302,y-.095,r['metric'],10.7,color=MUTED)
        if i<2:
            ax.plot([.025,.975],[y-.142,y-.142],color=light(c,.4),lw=.7)
    save(fig,'strategy_opportunity_routes')

def architecture():
    fig,ax=canvas(10.6,6.8,'One revision core, explicit domain contracts',
                  'Reuse the implemented engine; adapt document boundaries and human approval.')
    # Future document contracts sit apart from the solid, implemented core.
    contracts=[(.04,.25,'University proposal',LAV),(.375,.25,'Manuscript section',SKY),(.71,.25,'SME concept note',SAGE)]
    for x,w,label,c in contracts:
        rounded(ax,x,.755,w,.084,light(c,.16),c,lw=1.05,radius=.026,dashed=True,z=2)
        text(ax,x+w/2,.797,label,12.9,ha='center',bold=True,italic=True)
        arrow(ax,(x+w/2,.752),(x+w/2,.705),c,lw=1.1,dashed=True,ms=10)
    rounded(ax,.09,.638,.82,.067,light(APR,.17),APR,lw=1,radius=.023,dashed=True)
    text(ax,.5,.674,'Document contract: evidence · protected commitments · editing scope',12.8,ha='center',bold=True)
    arrow(ax,(.118,.637),(.118,.547),APR,lw=1.3,dashed=True,ms=11)
    # Main data ribbon: one calm pathway behind distinct visual metaphors.
    rounded(ax,.063,.382,.877,.113,light(LAV,.10),radius=.05)
    for a,b in [(.157,.227),(.344,.420),(.535,.611),(.735,.811)]:
        arrow(ax,(a,.440),(b,.440),LAV,lw=3.2,ms=15,z=2)
    page(ax,.086,.408,w=.059,h=.093,color=SKY)
    text(ax,.117,.341,'Evidence\nand proposal',13.4,ha='center',bold=True)
    text(ax,.117,.285,'Attributed input',10.8,ha='center',color=MUTED)
    # Editing sheet, with an understated pencil.
    page(ax,.261,.410,w=.061,h=.09,color=LAV,stack=False)
    ax.plot([.292,.324],[.420,.480],color=INK,lw=3,solid_capstyle='round',zorder=7,alpha=.75)
    ax.add_patch(Polygon([[.291,.414],[.296,.422],[.290,.425]],facecolor=APR,edgecolor='none',zorder=8))
    text(ax,.29,.341,'Section\nrewrite',13.4,ha='center',bold=True)
    text(ax,.29,.285,'Six explicit rules',10.8,ha='center',color=MUTED)
    # A funnel expresses contextual checking and prioritisation.
    ax.add_patch(Polygon([[.443,.501],[.527,.501],[.497,.447],[.497,.415],[.476,.407],[.476,.447]],
                         closed=True,facecolor=light(SAGE,.48),edgecolor=SAGE,linewidth=1.3,zorder=5))
    for xx in [.461,.483,.505]:
        ax.add_patch(Circle((xx,.524),.006,facecolor=SAGE,edgecolor='none',zorder=6))
    ax.plot([.477,.485,.503],[.475,.463,.488],color=INK,lw=1.7,zorder=7)
    text(ax,.485,.341,'Contextual\nreview',13.4,ha='center',bold=True)
    text(ax,.485,.285,'Localise the issue',10.8,ha='center',color=MUTED)
    # Repair/retention is a revised sheet with a retained-line annotation.
    page(ax,.645,.410,w=.063,h=.09,color=APR,stack=False)
    rounded(ax,.651,.448,.049,.016,light(APR,.65),radius=.003,z=7)
    ax.plot([.681,.688,.707],[.414,.406,.430],color='#6C8E69',lw=2,zorder=8)
    text(ax,.674,.341,'Bounded repair\nand retention',13.4,ha='center',bold=True)
    text(ax,.674,.285,'Revise or keep original',10.8,ha='center',color=MUTED)
    # Ledger consists of overlapping lines, not a generic rectangular module.
    for d in [.014,.007,0]:
        rounded(ax,.835+d,.409-d,.075,.092,light(LAV,.16) if d else 'white',LAV,lw=1,radius=.009,z=5)
    for yy in [.481,.456,.431]:
        ax.add_patch(Circle((.846,yy),.004,facecolor=LAV,edgecolor='none',zorder=8))
        ax.plot([.858,.898],[yy,yy],color=LAV,lw=1.6,zorder=8)
    text(ax,.874,.341,'Run ledger\nand export',13.4,ha='center',bold=True)
    text(ax,.874,.285,'Inspectable decisions',10.8,ha='center',color=MUTED)
    # Only the review–repair loop is drawn; the record is not a retrieval loop.
    path=MplPath([(.672,.507),(.672,.611),(.485,.611),(.485,.545)],
                 [MplPath.MOVETO,MplPath.CURVE4,MplPath.CURVE4,MplPath.CURVE4])
    ax.add_patch(FancyArrowPatch(path=path,arrowstyle='-|>',mutation_scale=11,color=APR,linewidth=1.25,zorder=2))
    text(ax,.579,.615,'bounded recheck',10.6,ha='center',italic=True,color='#997351')
    rounded(ax,.753,.550,.228,.059,light(APR,.12),APR,lw=1,radius=.022,dashed=True)
    text(ax,.867,.580,'Named human approval',11.9,ha='center',bold=True)
    arrow(ax,(.867,.550),(.867,.508),APR,lw=1.2,dashed=True,ms=10)
    rounded(ax,.04,.058,.92,.088,light(LAV,.07),radius=.02)
    ax.plot([.065,.110],[.105,.105],color=LAV,lw=2)
    text(ax,.122,.106,'Implemented revision core',10.8)
    ax.plot([.480,.525],[.105,.105],color=APR,lw=1.5,linestyle=(0,(4,3)))
    text(ax,.537,.106,'Proposed domain / approval extensions',10.8)
    text(ax,.5,.033,'Run-level traceability; historical experience retrieval is not active in this route.',10.5,ha='center',color=MUTED)
    save(fig,'strategy_adaptation_architecture')

def sensitivity():
    spec=DATA['figures'][2]
    fig=plt.figure(figsize=(10.6,6.0),facecolor='white')
    full=fig.add_axes([0,0,1,1]);full.set(xlim=(0,1),ylim=(0,1));full.axis('off')
    text(full,.045,.952,'Value depends on net time saved',20,bold=True,italic=True)
    text(full,.045,.895,'Illustrative assumptions: S$60/hour staff cost; S$3 non-labour cost per document.',12,color=MUTED)
    ax=fig.add_axes([.135,.235,.445,.55])
    matrix=np.array(spec['net_value_per_document'])
    cmap=LinearSegmentedColormap.from_list('soft_diverge',[ROSE,'#FCFBFA',SAGE])
    ax.imshow(matrix,cmap=cmap,norm=TwoSlopeNorm(vmin=-15,vcenter=0,vmax=15),aspect='auto')
    ax.set_xticks([0,1,2],['0 min','6 min','12 min'],fontsize=12)
    ax.set_yticks([0,1,2],['6 min','12 min','18 min'],fontsize=12)
    ax.set_xlabel('Additional checking time',fontsize=13,labelpad=10,weight='bold')
    ax.set_ylabel('Gross editing time saved',fontsize=13,labelpad=12,weight='bold')
    ax.tick_params(length=0,pad=9)
    for spine in ax.spines.values(): spine.set_visible(False)
    for k in [.5,1.5]:
        ax.axvline(k,color='white',lw=5);ax.axhline(k,color='white',lw=5)
    for i in range(3):
        for j in range(3):
            val=int(matrix[i,j]); label=('−' if val<0 else '')+'S$'+str(abs(val))
            ax.text(j,i,label,ha='center',va='center',fontsize=21,weight='bold',color=INK)
    ax.add_patch(Rectangle((.52,.52),.96,.96,fill=False,edgecolor='#A38AB6',linewidth=2.2))
    text(full,.355,.820,'NET VALUE PER COMPLETED DOCUMENT',10.7,ha='center',bold=True,color=MUTED)
    rounded(full,.653,.247,.305,.536,light(LAV,.11),radius=.025)
    text(full,.681,.734,'Break-even net time',15.5,bold=True,italic=True)
    text(full,.681,.690,'To cover S$3 per document',11.4,color=MUTED)
    for yy,rate,mins in zip([.616,.548,.480],spec['break_even']['staff_cost_per_hour'],spec['break_even']['required_net_minutes_saved']):
        text(full,.681,yy,f'S${rate}/hour',12.2)
        text(full,.929,yy,f'{mins:g} min',14,ha='right',bold=True)
    full.plot([.681,.931],[.437,.437],color=light(LAV,.75),lw=.9)
    text(full,.681,.398,'Central scenario',12.7,bold=True)
    text(full,.681,.351,'S$3 per document × 50 / month',11.3)
    text(full,.681,.305,'= S$150 before extra fixed cost',11.5,bold=True)
    text(full,.045,.100,'Net value = (gross time saved − new checking time) × staff cost − non-labour cost.',12,italic=True)
    text(full,.045,.052,'Scenario analysis, not measured savings. Human checking, retries and repair must be counted.',11.2,color=MUTED)
    save(fig,'strategy_cost_sensitivity')

if __name__=='__main__':
    opportunity_routes()
    architecture()
    sensitivity()
    print('\n'.join(str(p) for p in sorted(OUT.glob('*'))))
