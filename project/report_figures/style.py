"""Portable publication-scale typography and vector primitives."""
from pathlib import Path
import os
import tempfile
os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir())/'proseledger-mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import patches, colors
from matplotlib.font_manager import FontProperties, findfont

C={'lavender':'#C4B7D7','sky':'#8FBFDA','sage':'#A8BCA3','apricot':'#E8B792',
   'ink':'#302B3A','plum':'#302B3A','muted':'#625D69','gray':'#DAD6DF','rose':'#CA8894','white':'#FFFFFF'}

def font(file,family,weight='normal',style='normal',fallback='DejaVu Serif'):
    p=Path('/System/Library/Fonts/Supplemental')/file
    if p.exists():return FontProperties(fname=str(p),weight=weight,style=style)
    q=FontProperties(family=family,weight=weight,style=style)
    try:return FontProperties(fname=findfont(q,fallback_to_default=False),weight=weight,style=style)
    except ValueError:return FontProperties(family=fallback,weight=weight,style=style)
F={'body':font('Times New Roman.ttf','Times New Roman'),
   'bold':font('Times New Roman Bold.ttf','Times New Roman','bold'),
   'italic':font('Times New Roman Italic.ttf','Times New Roman',style='italic'),
   'title':font('Times New Roman Bold Italic.ttf','Times New Roman','bold','italic'),
   'flow':font('Comic Sans MS Bold Italic.ttf','Comic Sans MS','bold','italic','DejaVu Sans')}
plt.rcParams.update({'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','figure.facecolor':'white','savefig.facecolor':'white'})

def mix(color,amount=.22):
    rgb=colors.to_rgb(C.get(color,color));return tuple(1-amount*(1-v) for v in rgb)

def canvas(w=6.5,h=4.8):
    fig,ax=plt.subplots(figsize=(w,h));fig.subplots_adjust(left=0,right=1,top=1,bottom=0)
    ax.set(xlim=(0,w),ylim=(0,h));ax.axis('off');return fig,ax

def text(ax,x,y,s,size=7.5,style='body',color='ink',ha='left',va='top',**kw):
    return ax.text(x,y,s,fontsize=size,fontproperties=F[style],color=C.get(color,color),ha=ha,va=va,
       linespacing=1.12,zorder=20,parse_math=False,**kw)

def box(ax,x,y,w,h,color='lavender',alpha=.18,edge=False,r=.055,z=1):
    p=patches.FancyBboxPatch((x,y),w,h,boxstyle=f'round,pad=0,rounding_size={r}',facecolor=mix(color,alpha),
       edgecolor=C[color] if edge else 'none',linewidth=.65,zorder=z);ax.add_patch(p);return p

def line(ax,a,b,color='gray',lw=.65,ls='-',z=3):
    ax.plot([a[0],b[0]],[a[1],b[1]],color=C.get(color,color),lw=lw,linestyle=ls,zorder=z)

def arrow(ax,a,b,color='lavender',lw=.85,rad=0,ls='-',z=4,head=6):
    p=patches.FancyArrowPatch(a,b,arrowstyle='-|>',connectionstyle=f'arc3,rad={rad}',color=C.get(color,color),
       lw=lw,linestyle=ls,mutation_scale=head,zorder=z);ax.add_patch(p);return p

def tag(ax,x,y,w,label,color='lavender',size=7):
    box(ax,x,y,w,.20,color,.36,r=.04,z=5);text(ax,x+w/2,y+.10,label,size,'flow',ha='center',va='center')

def page(ax,x,y,w,h,color='sky',rows=4):
    box(ax,x+.035,y-.028,w,h,color,.20,edge=False,z=3)
    box(ax,x,y,w,h,'white',0,edge=False,z=4)
    ax.add_patch(patches.Polygon([(x,y),(x+w,y),(x+w,y+h-.12),(x+w-.12,y+h),(x,y+h)],
       facecolor='white',edgecolor=C[color],lw=.65,zorder=5))
    ax.add_patch(patches.Polygon([(x+w-.12,y+h),(x+w-.12,y+h-.12),(x+w,y+h-.12)],facecolor=mix(color,.6),edgecolor=C[color],lw=.55,zorder=6))
    for i in range(rows):
        yy=y+h-.20-i*.10
        if yy>y+.06:line(ax,(x+.07,yy),(x+w-.08-(i%2)*.07,yy),color,.8,z=7)

def agent(ax,x,y,color='lavender',scale=1):
    s=scale
    ax.add_patch(patches.Ellipse((x+.14*s,y),.31*s,.045*s,facecolor=C['gray'],edgecolor='none',zorder=2))
    box(ax,x+.04*s,y+.03*s,.20*s,.12*s,color,.8,r=.035,z=4)
    box(ax,x,y+.12*s,.28*s,.22*s,color,.75,r=.055,z=5)
    ax.add_patch(patches.Polygon([(x+.28*s,y+.15*s),(x+.31*s,y+.18*s),(x+.31*s,y+.32*s),(x+.28*s,y+.34*s)],facecolor=mix(color,.95),edgecolor='none',zorder=4))
    box(ax,x+.04*s,y+.19*s,.20*s,.085*s,'white',0,r=.025,z=6)
    for xx in [.10,.19]:ax.add_patch(patches.Circle((x+xx*s,y+.233*s),.015*s,facecolor=C['ink'],edgecolor='none',zorder=7))
    line(ax,(x+.14*s,y+.34*s),(x+.14*s,y+.39*s),color,.8,z=4)
    ax.add_patch(patches.Circle((x+.14*s,y+.41*s),.018*s,facecolor=C[color],edgecolor='none',zorder=5))

def save(fig,stem):
    stem=Path(stem);stem.parent.mkdir(parents=True,exist_ok=True)
    fig.canvas.draw();r=fig.canvas.get_renderer();w,h=fig.canvas.get_width_height()
    for ax in fig.axes:
        for t in ax.texts:
            if t.get_visible():
                b=t.get_window_extent(r)
                if min(b.x0,b.y0)<-1 or b.x1>w+1 or b.y1>h+1:raise ValueError(f'{stem.name}: clipped text {t.get_text()!r}')
    for ext in ['pdf','svg','png']:fig.savefig(stem.with_suffix('.'+ext),dpi=320,facecolor='white')
    plt.close(fig)
