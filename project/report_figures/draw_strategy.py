from pathlib import Path
import hashlib
import json
import os
import argparse
import tempfile

os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'proseledger-mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyBboxPatch, FancyArrowPatch, Polygon, PathPatch, Rectangle
from matplotlib.path import Path as MP
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import numpy as np

from style import C, F, mix, save

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'assets' / 'strategy'
DATA_FILE = ROOT / 'strategy_figure_data.json'
DATA = None
PLUM = C['plum']
LAV, SKY, SAGE, APR = (C[k] for k in ['lavender', 'sky', 'sage', 'apricot'])
MUTED = '#726877'


def txt(ax, x, y, s, size=12, style='body', color=PLUM, ha='left', va='center', z=20):
    return ax.text(x,y,s,fontsize=size,fontproperties=F[style],color=color,
                   ha=ha,va=va,linespacing=1.13,zorder=z,parse_math=False)


def slab(ax,x,y,w,h,fill,edge='none',r=1.2,lw=.9,dash=False,z=2):
    p=FancyBboxPatch((x,y),w,h,boxstyle=f'round,pad=0,rounding_size={r}',
                    facecolor=fill,edgecolor=edge,linewidth=lw,
                    linestyle=(0,(3.4,3)) if dash else '-',zorder=z)
    ax.add_patch(p);return p


def blob(ax,x,y,w,h,color,strength=.13,z=0,dashed=False):
    pts=[(x-w*.46,y-h*.33),(x-w*.58,y+h*.05),(x-w*.48,y+h*.45),(x-w*.14,y+h*.47),
         (x+w*.20,y+h*.57),(x+w*.47,y+h*.32),(x+w*.48,y+h*.08),
         (x+w*.55,y-h*.22),(x+w*.36,y-h*.50),(x+w*.08,y-h*.46),
         (x-w*.19,y-h*.54),(x-w*.39,y-h*.49),(x-w*.46,y-h*.33)]
    ax.add_patch(PathPatch(MP(pts,[MP.MOVETO]+[MP.CURVE4]*12),facecolor=mix(color,strength),edgecolor=color if dashed else 'none',linewidth=.75,linestyle=(0,(3.2,2.8)) if dashed else '-',zorder=z))


def shadow(ax,x,y,w,h=.85,z=1):
    for scale,alpha in [(1.0,.025),(.80,.035),(.62,.045)]:
        ax.add_patch(Ellipse((x,y),w*scale,h*scale,facecolor=PLUM,edgecolor='none',alpha=alpha,zorder=z))


def flow(ax,start,end,color=LAV,lw=1.7,curve=0,dashed=False,ms=10,z=3):
    ax.add_patch(FancyArrowPatch(start,end,arrowstyle='-|>',mutation_scale=ms,
                   linewidth=lw,color=color,connectionstyle=f'arc3,rad={curve}',
                   linestyle=(0,(4,3)) if dashed else '-',zorder=z))


def bezier_flow(ax,points,color=LAV,lw=1.6,dashed=False,ms=10,z=3):
    p=MP(points,[MP.MOVETO,MP.CURVE4,MP.CURVE4,MP.CURVE4])
    ax.add_patch(FancyArrowPatch(path=p,arrowstyle='-|>',mutation_scale=ms,
                   linewidth=lw,color=color,linestyle=(0,(4,3)) if dashed else '-',zorder=z))


def document(ax,x,y,w=5.2,h=7.0,color=SKY,stack=2,check=False,lines=3,z=6):
    shadow(ax,x+w*.52,y-.2,w*1.3,z=z-2)
    for i in range(stack,0,-1):
        slab(ax,x+i*.33,y-i*.23,w,h,mix(color,.18),color,r=.48,lw=.65,z=z-1)
    fold=w*.23
    ax.add_patch(Polygon([(x,y),(x+w,y),(x+w,y+h-fold),(x+w-fold,y+h),(x,y+h)],
                         closed=True,facecolor='white',edgecolor=color,linewidth=1.0,zorder=z))
    ax.add_patch(Polygon([(x+w-fold,y+h),(x+w-fold,y+h-fold),(x+w,y+h-fold)],
                         closed=True,facecolor=mix(color,.33),edgecolor=color,linewidth=.6,zorder=z+1))
    for i in range(lines):
        yy=y+h*.67-i*h*.16
        ax.plot([x+w*.17,x+w*(.75 if i%2==0 else .62)],[yy,yy],lw=1.2,color=color,solid_capstyle='round',zorder=z+1)
    if check:
        ax.add_patch(Circle((x+w*.94,y+.65),1.0,facecolor=mix(SAGE,.25),edgecolor='white',linewidth=.8,zorder=z+2))
        ax.plot([x+w*.94-.5,x+w*.94-.13,x+w*.94+.58],[y+.68,y+.3,y+1.0],color='#74906E',lw=1.3,zorder=z+3)


def book(ax,x,y,w=9,h=5.5,color=LAV,z=6):
    shadow(ax,x,y-h*.52,w*1.2,z=z-2)
    ax.add_patch(Polygon([(x-w*.5,y-h*.47),(x,y-h*.55),(x+w*.5,y-h*.47),
                         (x+w*.5,y+h*.39),(x,y+h*.23),(x-w*.5,y+h*.39)],
                         facecolor=mix(color,.55),edgecolor=color,linewidth=.7,zorder=z))
    for side in [-1,1]:
        pts=[(x,y-h*.35),(x+side*w*.18,y-h*.48),(x+side*w*.36,y-h*.36),(x+side*w*.48,y-h*.30),
             (x+side*w*.48,y+h*.47),(x+side*w*.23,y+h*.48),(x,y+h*.27),(x,y-h*.35)]
        ax.add_patch(PathPatch(MP(pts,[MP.MOVETO,MP.CURVE4,MP.CURVE4,MP.CURVE4,MP.LINETO,MP.CURVE3,MP.CURVE3,MP.CLOSEPOLY]),
                              facecolor='white',edgecolor=color,linewidth=.75,zorder=z+1))
        for off in [.20,-.02,-.24]:
            ax.plot([x+side*w*.10,x+side*w*.38],[y+h*off,y+h*(off+.07)],color=mix(color,.8),lw=.9,zorder=z+2)
    ax.plot([x,x],[y-h*.37,y+h*.25],color=color,lw=.8,zorder=z+3)


def person(ax,x,y,s=1,color=SAGE,reviewer=False,z=7):
    # Lower y is the torso baseline; the face and glasses remain quiet and small.
    shadow(ax,x,y-.12,7*s,z=z-2)
    torso=MP([(x-3.3*s,y),(x-3.7*s,y+3.0*s),(x-1.9*s,y+4.4*s),(x,y+4.2*s),
              (x+1.9*s,y+4.4*s),(x+3.7*s,y+3.0*s),(x+3.3*s,y),(x-3.3*s,y)],
             [MP.MOVETO,MP.CURVE4,MP.CURVE4,MP.CURVE4,MP.CURVE4,MP.CURVE4,MP.CURVE4,MP.CLOSEPOLY])
    ax.add_patch(PathPatch(torso,facecolor=mix(color,.72),edgecolor='none',zorder=z))
    ax.add_patch(Circle((x,y+5.0*s),1.7*s,facecolor=mix(APR,.45),edgecolor='none',zorder=z+1))
    hair=MP([(x-1.7*s,y+5.2*s),(x-2.1*s,y+7.3*s),(x+1.8*s,y+7.4*s),(x+1.7*s,y+5.1*s),
             (x+.6*s,y+5.7*s),(x-.7*s,y+6.2*s),(x-1.7*s,y+5.2*s)],
            [MP.MOVETO]+[MP.CURVE4]*6)
    ax.add_patch(PathPatch(hair,facecolor=PLUM,edgecolor='none',alpha=.73,zorder=z+2))
    if reviewer:
        for dx in [-.65,.65]:
            ax.add_patch(Ellipse((x+dx*s,y+4.95*s),1.05*s,.65*s,facecolor='white',edgecolor=PLUM,lw=.6,zorder=z+3))
        ax.plot([x-.12*s,x+.12*s],[y+4.95*s,y+4.95*s],color=PLUM,lw=.6,zorder=z+3)
    else:
        for dx in [-.55,.55]:ax.add_patch(Circle((x+dx*s,y+4.95*s),.12*s,facecolor=PLUM,edgecolor='none',zorder=z+3))
    if reviewer:
        document(ax,x+1.0*s,y-.1*s,w=3.4*s,h=4.0*s,color=color,stack=0,check=True,z=z+4)


def desk_scene(ax,x,y,s=1,color=LAV,variant='research'):
    person(ax,x,y+3.7*s,s=.81*s,color=color,z=5)
    slab(ax,x-7*s,y+1.6*s,14*s,.65*s,mix(color,.66),r=.3,z=11)
    for dx in [-5.5,5.5]:
        ax.plot([x+dx*s,x+dx*s],[y-1.0*s,y+1.65*s],color=mix(color,.80),lw=1.5,zorder=3)
    if variant=='editor':
        book(ax,x-.8*s,y+3.5*s,w=8*s,h=4.0*s,color=color,z=12)
        ax.plot([x+3.4*s,x+5.0*s],[y+3.3*s,y+5.4*s],color=PLUM,lw=1.5,zorder=15)
    else:
        slab(ax,x-4.2*s,y+2.0*s,7.7*s,4.5*s,mix(SKY,.19),SKY,r=.5,lw=.8,z=12)
        slab(ax,x-3.7*s,y+2.5*s,6.7*s,3.5*s,'white',r=.2,z=13)
        for i in range(3):ax.plot([x-2.9*s,x+(1.7 if i!=1 else .5)*s],[y+(5.25-.72*i)*s]*2,color=color,lw=1.1,zorder=14)
        ax.add_patch(Polygon([(x-4.8*s,y+2.0*s),(x+4*s,y+2*s),(x+4.7*s,y+1.6*s),(x-5.2*s,y+1.6*s)],facecolor=SKY,edgecolor='none',zorder=14))
    if variant=='engineer':
        document(ax,x+4.5*s,y+2.1*s,w=2.3*s,h=3.3*s,color=APR,stack=0,lines=2,z=13)
    else:
        for i,c in enumerate([APR,SAGE]):slab(ax,x-6.4*s,y+(2+.42*i)*s,2.2*s,.35*s,mix(c,.7),r=.1,z=14)


def robot(ax,x,y,s=1,color=SKY,role='writer'):
    shadow(ax,x,y-.6*s,8.5*s,z=3)
    slab(ax,x-2.65*s,y,5.3*s,4.0*s,mix(color,.66),r=.85*s,z=6)
    for dx in [-1.7,1.7]:
        slab(ax,x+dx*s-.5*s,y-.65*s,1.3*s,1.1*s,mix(color,.82),r=.45*s,z=5)
    ax.plot([x,x],[y+8.3*s,y+9.1*s],color=color,lw=1.3,zorder=5)
    ax.add_patch(Circle((x,y+9.4*s),.43*s,facecolor=APR,edgecolor='white',lw=.6,zorder=6))
    for side in [-1,1]:slab(ax,x+side*3.4*s-.4*s,y+5.0*s,.8*s,1.9*s,mix(color,.85),r=.4*s,z=5)
    slab(ax,x-3.35*s,y+4.3*s,6.7*s,4.0*s,mix(color,.55),r=1.1*s,z=7)
    slab(ax,x-2.55*s,y+5.0*s,5.1*s,2.7*s,'white',r=.75*s,z=8)
    for dx in [-1.18,1.18]:
        ax.add_patch(Ellipse((x+dx*s,y+6.4*s),.70*s,1.1*s,facecolor=PLUM,edgecolor='none',zorder=9))
        ax.add_patch(Circle((x+(dx+.08)*s,y+6.62*s),.13*s,facecolor='white',edgecolor='none',zorder=10))
    ax.plot([x-.5*s,x+.5*s],[y+5.5*s]*2,color=color,lw=.8,zorder=9)
    ax.add_patch(Circle((x,y+2.6*s),.62*s,facecolor='white',edgecolor='none',zorder=8))
    ax.plot([x-2.5*s,x-4.3*s],[y+3.2*s,y+1.8*s],color=color,lw=2,zorder=4)
    ax.plot([x+2.5*s,x+4.1*s],[y+3.2*s,y+1.9*s],color=color,lw=2,zorder=4)
    if role=='writer':
        document(ax,x+2.3*s,y-.1*s,w=3.7*s,h=4.7*s,color=LAV,stack=0,z=10)
        ax.plot([x+3.8*s,x+5.8*s],[y+.9*s,y+4.0*s],color=PLUM,lw=2,zorder=12)
        ax.add_patch(Polygon([(x+3.45*s,y+.4*s),(x+3.75*s,y+1.2*s),(x+4.15*s,y+.85*s)],facecolor=APR,edgecolor='none',zorder=13))
    else:
        ax.add_patch(Circle((x+4.1*s,y+3.25*s),1.65*s,facecolor=mix(SAGE,.17),edgecolor=SAGE,lw=1.7,zorder=12))
        ax.plot([x+5.3*s,x+6.55*s],[y+2.0*s,y+.7*s],color=SAGE,lw=3,solid_capstyle='round',zorder=11)
        ax.plot([x+3.3*s,x+3.9*s,x+4.9*s],[y+3.2*s,y+2.7*s,y+3.8*s],color='#789271',lw=1.2,zorder=13)


def ledger(ax,x,y,s=1):
    shadow(ax,x+3*s,y-.4*s,8*s)
    slab(ax,x,y,6.8*s,5.5*s,mix(APR,.28),APR,r=.6*s,lw=.8,z=6)
    for yy in [1.1,2.6,4.1]:
        ax.plot([x+.7*s,x+6.1*s],[y+yy*s]*2,color=LAV,lw=1.1,zorder=7)
    for xx,yy,c in [(1.5,1.1,LAV),(2.4,1.1,LAV),(4.2,2.6,SAGE),(5.0,2.6,SAGE),(1.6,4.1,SKY),(3.1,4.1,SKY),(4.0,4.1,SKY)]:
        ax.add_patch(Ellipse((x+xx*s,y+yy*s),.7*s,1.0*s,facecolor=c,edgecolor='white',lw=.3,zorder=8))


def base(title,subtitle,h=68):
    fig,ax=plt.subplots(figsize=(10.6,10.6*h/100))
    ax.set(xlim=(0,100),ylim=(0,h));ax.set_aspect('equal');ax.axis('off')
    fig.subplots_adjust(left=.014,right=.986,bottom=.015,top=.985)
    txt(ax,2.2,h-3.0,title,21.5,'title')
    txt(ax,2.2,h-7.0,subtitle,11.8,color=MUTED)
    return fig,ax


def opportunities():
    fig,ax=base('Three entry points, three approval paths',
                'A shared revision engine; distinct document owners, reviewers and buyers.',h=72)
    centres=[17.8,50,82.2]
    configs=[
        ('University\nproposal support',LAV,'research','Research author','Adviser','Programme manager',
         'Evidence + planned status','30 proposals · 4 weeks','10 authors · 2 advisers'),
        ('Scholarly\nauthor services',SKY,'editor','Professional editor','Author / scientific editor','Editorial operations',
         'Scientific meaning','40 sections · 5 weeks','At least 2 disciplines'),
        ('R&D SME\nconcept notes',SAGE,'engineer','Technical author','Technical lead','Founder / project lead',
         'Quantities + commitments','20 notes · 6 weeks','2 firms')]
    for x,conf in zip(centres,configs):
        title,c,variant,user,approver,buyer,protected,pilot,detail=conf
        blob(ax,x,31.4,30.1,50,c,.105)
        txt(ax,x,59.3,title,16.6,'title',ha='center')
        desk_scene(ax,x,44.0,.9,c,variant)
        txt(ax,x,41.7,user,12.3,'bold',ha='center')
        txt(ax,x,38.8,protected,10.9,'italic',ha='center',color=MUTED)
        flow(ax,(x,37.0),(x,34.6),c,lw=1.55,ms=10)
        flow(ax,(x,28.4),(x,25.6),c,lw=1.55,ms=10)
        person(ax,x-5.2,18.6,.73,c,reviewer=True)
        txt(ax,x+1.0,22.3,approver.replace(' / ',' /\n') if len(approver)>17 else approver,
            11.8,'bold',ha='left')
        txt(ax,x,16.0,'Buyer',9.6,'flow',ha='center',color=MUTED)
        txt(ax,x,13.6,buyer,11.5,'bold',ha='center')
        txt(ax,x,7.5,pilot,12.0,'bold',ha='center')
        txt(ax,x,4.8,detail,10.9,ha='center',color=MUTED)
    # A continuous shared layer links the journeys without claiming a market ranking.
    shadow(ax,50,28.2,91,1.1)
    for x,w,c in [(4,31,LAV),(34,32,SKY),(65,31,SAGE)]:
        slab(ax,x,28.9,w,5.1,mix(c,.32),r=2.5,z=4)
    txt(ax,50,31.5,'Shared ProseLedger revision core',14.0,'flow',ha='center')
    txt(ax,50,10.0,'PROPOSED PILOTS',9.7,'flow',ha='center',color='#927F9A')
    save(fig,OUT/'strategy_opportunity_routes');plt.close(fig)


def architecture():
    fig,ax=base('One revision core, explicit domain contracts',
                'Model-generated edits meet contextual review before a document is retained.',h=73)
    for x,label,c in [(17,'University proposal',LAV),(49,'Manuscript section',SKY),(81,'SME concept note',SAGE)]:
        blob(ax,x,57.6,25,8.3,c,.16,dashed=True)
        if x==17:book(ax,x-8.4,58.0,w=5.4,h=3.4,color=c)
        else:document(ax,x-10.7,55.6,w=3.5,h=4.8,color=c,stack=1,lines=2)
        txt(ax,x+2.4,58.0,label,11.8,'title',ha='center')
        flow(ax,(x,53.7),(x,51.0),c,lw=1.0,dashed=True,ms=9)
    # Proposed domain/approval additions use the sole dashed-boundary convention.
    slab(ax,6.0,46.7,81.5,4.1,mix(APR,.14),APR,r=1.6,lw=.8,dash=True,z=2)
    txt(ax,46.75,48.75,'Evidence · protected commitments · authorised editing scope',11.7,'bold',ha='center')
    flow(ax,(11,46.3),(11,38.0),APR,lw=1.15,dashed=True,ms=10)
    blob(ax,49.6,26.5,55.5,36.5,LAV,.115)
    txt(ax,48.0,42.0,'Implemented editing core',11.1,'flow',ha='center',color='#8D769D')
    book(ax,11.3,32.9,w=10.1,h=6.6,color=SKY)
    document(ax,12.0,31.2,w=3.0,h=4.2,color=SKY,stack=0,lines=2,z=9)
    txt(ax,11.1,26.1,'Evidence + draft',12.5,'bold',ha='center')
    txt(ax,11.1,22.8,'Attributed sources',10.6,'italic',ha='center',color=MUTED)
    robot(ax,32.4,29.4,.82,SKY,'writer')
    txt(ax,33.4,25.6,'Section writer',13.0,'bold',ha='center')
    txt(ax,33.4,22.5,'Six editorial rules',10.7,'flow',ha='center',color='#748AA0')
    robot(ax,58.4,29.4,.82,SAGE,'reviewer')
    txt(ax,59.9,25.6,'Contextual reviewer',12.8,'bold',ha='center')
    txt(ax,59.9,22.5,'Compare claims + sources',10.4,'italic',ha='center',color=MUTED)
    # Factual admission is distinguished from the model reviewer.
    ax.add_patch(Polygon([(72.2,35.1),(78.5,35.1),(76.1,31.5),(76.1,29.8),(74.5,29.3),(74.5,31.5)],
                         facecolor=mix(LAV,.50),edgecolor=LAV,lw=1.05,zorder=7))
    txt(ax,75.2,25.8,'Retain?',11.7,'bold',ha='center')
    document(ax,86.7,30.1,w=5.8,h=7.8,color=LAV,stack=2,check=True)
    txt(ax,89.5,26.0,'Retained text',12.4,'bold',ha='center')
    txt(ax,89.5,22.8,'or original fallback',10.6,'italic',ha='center',color=MUTED)
    flow(ax,(17.5,33.4),(26.2,33.4),SKY,lw=2.25,ms=12)
    flow(ax,(38.2,34.1),(52.5,34.1),LAV,lw=2.25,ms=12)
    txt(ax,45.8,36.2,'candidate',10.4,'flow',ha='center',color='#947EAA')
    flow(ax,(65.3,33.4),(71.5,33.4),SAGE,lw=1.9,ms=11)
    flow(ax,(79.0,33.4),(85.7,33.4),LAV,lw=1.9,ms=11)
    # A bounded local loop repairs findings instead of retraining or retrieving history.
    document(ax,44.4,12.6,w=4.9,h=6.1,color=APR,stack=0,lines=2)
    slab(ax,45.0,14.5,3.7,.95,mix(APR,.65),r=.2,z=12)
    ax.plot([48.0,50.0],[13.0,16.2],color=PLUM,lw=1.8,zorder=13)
    txt(ax,47.3,9.4,'Bounded local repair',11.8,'bold',ha='center')
    bezier_flow(ax,[(60.3,20.6),(60.3,17.0),(55.4,15.6),(51.3,15.6)],APR,lw=1.5)
    bezier_flow(ax,[(43.2,16.8),(38.9,17.3),(44.3,31.3),(52.0,31.3)],APR,lw=1.5)
    txt(ax,31.5,16.9,'recheck',10.2,'flow',ha='center',color='#A88363')
    # Records are a separate artefact, not a hidden historical retrieval mechanism.
    ledger(ax,82.9,10.1,.98)
    txt(ax,86.4,6.8,'Decision ledger',11.5,'bold',ha='center')
    bezier_flow(ax,[(76.0,28.7),(76.0,16.1),(78.0,14.3),(81.8,13.6)],LAV,lw=1.3)
    txt(ax,73.5,15.8,'record',9.7,'flow',ha='center',color='#947EAA')
    # Human approval is proposed workflow integration, hence dashed.
    ax.add_patch(Ellipse((93.0,46.0),10.0,9.5,facecolor='none',edgecolor=APR,lw=.75,linestyle=(0,(3.2,2.8)),zorder=2))
    person(ax,93.0,42.5,.63,APR,reviewer=True)
    txt(ax,91.0,51.4,'Human approval',10.3,'title',ha='center')
    flow(ax,(92.8,42.0),(91.0,38.8),APR,lw=1.0,dashed=True,ms=9)
    ax.plot([3.1,6.5],[3.6,3.6],color=LAV,lw=1.8)
    txt(ax,7.4,3.6,'Existing core',11.0,'bold')
    ax.plot([29.4,33.4],[3.6,3.6],color=APR,lw=1.1,linestyle=(0,(4,3)))
    txt(ax,34.3,3.6,'Proposed additions',11.0,'bold')
    txt(ax,97.3,3.6,'Run-local records',11.0,'italic',ha='right',color=MUTED)
    save(fig,OUT/'strategy_adaptation_architecture');plt.close(fig)


def cost_sensitivity():
    spec=DATA['figures'][2]
    matrix=np.array(spec['net_value_per_document'],dtype=float)
    saved=np.array(spec['row_gross_saved_minutes'])
    checking=np.array(spec['column_extra_check_minutes'])
    expected=(saved[:,None]-checking[None,:])*spec['staff_cost_per_hour']/60-spec['nonlabour_cost_per_document']
    assert np.array_equal(matrix,expected)
    fig,ax=base('Value depends on net time saved',
                'Illustrative assumptions, not measured savings or a market forecast.',h=64)
    # Small economic objects contextualise the chart without distorting its scale.
    person(ax,7.3,48.4,.52,LAV)
    txt(ax,11.8,51.3,'S$60 / staff hour',12.0,'bold')
    ax.add_patch(Circle((38.3,51.4),2.0,facecolor=mix(APR,.35),edgecolor=APR,lw=.8,zorder=5))
    ax.add_patch(Circle((38.3,51.4),1.45,facecolor='none',edgecolor='white',lw=.9,zorder=6))
    txt(ax,38.3,51.4,'$',12.5,'bold',ha='center')
    txt(ax,42.0,51.3,'S$3 / document',12.0,'bold')
    txt(ax,72.5,51.3,'Count checking time.',11.4,'flow',color='#8C759D')
    # Nine equal, flat cells. Colours encode net value only; shadows remain outside the data area.
    cmap=LinearSegmentedColormap.from_list('strategy_soft_value',[APR,'#FCFBFE',LAV])
    norm=TwoSlopeNorm(vmin=-15,vcenter=0,vmax=15)
    left,bottom,cw,ch=14.0,13.7,14.5,9.3
    for i in range(3):
        for j in range(3):
            xx=left+j*cw;yy=bottom+(2-i)*ch
            slab(ax,xx,yy,cw-.55,ch-.55,cmap(norm(matrix[i,j])),r=.75,z=3)
            value=int(matrix[i,j]);label=('−' if value<0 else '')+'S$'+str(abs(value))
            txt(ax,xx+(cw-.55)/2,yy+(ch-.55)/2,label,20,'bold',ha='center')
    # Exact central scenario is outlined, with no artificial elevation.
    slab(ax,left+cw+.12,bottom+ch+.12,cw-.79,ch-.79,'none',edge='#9E88B6',r=.65,lw=1.3,z=4)
    for i,v in enumerate(saved):txt(ax,left-2.1,bottom+(2-i)*ch+ch/2,f'{v} min',11.5,'bold',ha='right')
    for j,v in enumerate(checking):txt(ax,left+j*cw+(cw-.55)/2,bottom-2.5,f'{v} min',11.5,'bold',ha='center')
    txt(ax,35.5,44.7,'Net value per completed document',11.0,'flow',ha='center',color='#8C759D')
    txt(ax,35.5,7.7,'Additional checking time',12.4,'bold',ha='center')
    ax.text(3.0,27.0,'Gross editing time saved',fontproperties=F['bold'],fontsize=12.4,
            color=PLUM,rotation=90,ha='center',va='center')
    # Break-even inset uses real coordinates rather than decorative bars.
    blob(ax,79.4,30.3,35.0,30.7,SAGE,.11)
    txt(ax,79.6,42.7,'Break-even net time',14.5,'title',ha='center')
    txt(ax,79.6,39.6,'Minutes needed to cover S$3',10.6,ha='center',color=MUTED)
    rates=np.array(spec['break_even']['staff_cost_per_hour'])
    mins=np.array(spec['break_even']['required_net_minutes_saved'])
    xfun=lambda r:68.8+(r-40)/60*22.0
    yfun=lambda m:24.5+(m-1.8)/(4.5-1.8)*9.0
    ax.plot([xfun(x) for x in rates],[yfun(y) for y in mins],color=SAGE,lw=1.8,zorder=5)
    for rate,minute in zip(rates,mins):
        xx,yy=xfun(rate),yfun(minute)
        ax.add_patch(Circle((xx,yy),.50,facecolor=SAGE,edgecolor='white',lw=1,zorder=7))
        txt(ax,xx,yy+2.0,f'{minute:g} min',12,'bold',ha='center')
        txt(ax,xx,20.4,f'S${rate}/h',10.2,ha='center',color=MUTED)
    txt(ax,79.7,15.8,'Central case: S$3 per document',10.5,'bold',ha='center')
    txt(ax,79.7,13.2,'50 documents → S$150 / month',10.4,ha='center')
    txt(ax,79.7,10.7,'before additional fixed cost',9.8,'italic',ha='center',color=MUTED)
    txt(ax,50,3.3,'Net value = (time saved − new checking time) × staff cost − non-labour cost',11.3,'italic',ha='center')
    save(fig,OUT/'strategy_cost_sensitivity');plt.close(fig)


def provenance():
    names=[f['id'] for f in DATA['figures']]
    record={
        'generator':'draw_strategy.py',
        'shared_style':'style.py',
        'input_data':'strategy_figure_data.json',
        'input_sha256':hashlib.sha256(DATA_FILE.read_bytes()).hexdigest(),
        'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'visual_reference':'Diagram Design Visuals.md (visual styling only)',
        'data_changes':False,
        'facts':'Opportunity pilots are proposed; architecture distinguishes existing core from proposed adapters; cost values are assumed scenarios.',
        'figures':{name:{ext:hashlib.sha256((OUT/(name+'.'+ext)).read_bytes()).hexdigest() for ext in ['pdf','svg','png']} for name in names},
    }
    (OUT/'PROVENANCE.json').write_text(json.dumps(record,indent=2)+'\n', encoding='utf-8')


if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Render the strategic analysis figures without model calls.')
    parser.add_argument('--data', type=Path, default=DATA_FILE)
    parser.add_argument('--output-dir', type=Path, default=OUT)
    args = parser.parse_args()
    DATA_FILE = args.data
    DATA = json.loads(DATA_FILE.read_text(encoding='utf-8'))
    OUT = args.output_dir
    OUT.mkdir(parents=True, exist_ok=True)
    opportunities()
    architecture()
    cost_sensitivity()
    provenance()
    print('Rendered three strategy figures; numerical scenarios verified.')
