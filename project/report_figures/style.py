"""Shared vector illustration language for the ProseLedger report figures."""
from pathlib import Path
import os
import tempfile
os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'proseledger-mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import patches, colors
from matplotlib.path import Path as VectorPath
from matplotlib.font_manager import FontProperties, findfont

C = {'lavender':'#C4B7D7', 'sage':'#A8BCA3', 'sky':'#8FBFDA', 'apricot':'#E8B792',
     'plum':'#5D425F', 'ink':'#514958', 'gray':'#DED9E2', 'rose':'#CA8894',
     'muted':'#7B7181', 'white':'#FFFFFF'}


def font(filename, family, weight='normal', style='normal', fallback='DejaVu Serif'):
    path = Path('/System/Library/Fonts/Supplemental') / filename
    if path.exists():
        return FontProperties(fname=str(path))
    target = FontProperties(family=family, weight=weight, style=style)
    try:
        return FontProperties(fname=findfont(target, fallback_to_default=False))
    except ValueError:
        return FontProperties(family=fallback, weight=weight, style=style)


F = {
    'body':font('Times New Roman.ttf','Times New Roman'),
    'bold':font('Times New Roman Bold.ttf','Times New Roman','bold'),
    'italic':font('Times New Roman Italic.ttf','Times New Roman',style='italic'),
    'title':font('Times New Roman Bold Italic.ttf','Times New Roman','bold','italic'),
    'flow':font('Comic Sans MS Bold Italic.ttf','Comic Sans MS','bold','italic','DejaVu Sans'),
}
plt.rcParams.update({'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none',
                     'figure.facecolor':'white','savefig.facecolor':'white',
                     'axes.spines.top':False,'axes.spines.right':False})


def mix(color, amount=.20):
    rgb=colors.to_rgb(C.get(color,color))
    return tuple(1-amount*(1-v) for v in rgb)


def dark(color, amount=.80):
    rgb=colors.to_rgb(C.get(color,color))
    plum=colors.to_rgb(C['plum'])
    return tuple(amount*p+(1-amount)*v for p,v in zip(plum,rgb))


def canvas(w=12,h=7):
    fig,ax=plt.subplots(figsize=(w,h))
    fig.subplots_adjust(left=0,right=1,top=1,bottom=0)
    ax.set(xlim=(0,w),ylim=(0,h));ax.axis('off')
    return fig,ax


def text(ax,x,y,s,size=16,style='body',color='ink',ha='left',va='top',**kwargs):
    return ax.text(x,y,s,fontsize=size,fontproperties=F[style],color=C.get(color,color),
                   ha=ha,va=va,linespacing=1.15,zorder=20,**kwargs)


def title(ax,h,heading,sub=None):
    text(ax,.35,h-.22,heading,29,'title','plum')
    if sub:text(ax,.38,h-.78,sub,14.7,'body','muted')


def rounded(ax,x,y,w,h,color='lavender',strength=.16,r=.18,edge=None,lw=.8,shadow=False,z=2):
    if shadow:
        for offset,alpha in [(.06,.055),(.035,.07)]:
            ax.add_patch(patches.FancyBboxPatch((x+offset,y-offset),w,h,
                boxstyle=f'round,pad=0,rounding_size={r}',facecolor=C['plum'],edgecolor='none',alpha=alpha,zorder=z-1))
    p=patches.FancyBboxPatch((x,y),w,h,boxstyle=f'round,pad=0,rounding_size={r}',
        facecolor=mix(color,strength),edgecolor=C.get(edge,edge) if edge else 'none',lw=lw,zorder=z)
    ax.add_patch(p);return p


def panel(ax,x,y,w,h,color='lavender',r=.24,shadow=False):
    clip=rounded(ax,x,y,w,h,color,.13,r,shadow=shadow,z=1)
    for i in range(22):
        p=patches.Rectangle((x,y+h*i/22),w,h/22+.004,facecolor=mix(color,.11+.12*(1-i/22)),edgecolor='none',zorder=2)
        p.set_clip_path(clip);ax.add_patch(p)
    return clip


def line(ax,a,b,color='lavender',lw=1.2,alpha=1,ls='-',z=4):
    ax.plot([a[0],b[0]],[a[1],b[1]],color=C.get(color,color),lw=lw,alpha=alpha,ls=ls,zorder=z)


def arrow(ax,a,b,color='lavender',lw=1.8,rad=0,ls='-',z=6,head=12):
    ax.add_patch(patches.FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=head,
        connectionstyle=f'arc3,rad={rad}',color=C.get(color,color),lw=lw,linestyle=ls,zorder=z))


def ribbon(ax,a,b,width=.14,color='lavender',alpha=.35):
    x0,y0=a;x1,y1=b
    verts=[(x0,y0+width/2),(x0+(x1-x0)*.45,y0+width/2),(x1-(x1-x0)*.45,y1+width/2),(x1,y1+width/2),
           (x1,y1-width/2),(x1-(x1-x0)*.45,y1-width/2),(x0+(x1-x0)*.45,y0-width/2),(x0,y0-width/2),(x0,y0+width/2)]
    codes=[VectorPath.MOVETO]+[VectorPath.CURVE4]*3+[VectorPath.LINETO]+[VectorPath.CURVE4]*3+[VectorPath.CLOSEPOLY]
    ax.add_patch(patches.PathPatch(VectorPath(verts,codes),facecolor=C[color],edgecolor='none',alpha=alpha,zorder=3))


def document(ax,x,y,w=1.2,h=1.5,color='sky',stack=2,rows=4):
    for i in range(stack,0,-1):
        offset=.055*i
        rounded(ax,x+offset,y-offset,w,h,color,.08,r=.07,edge='gray',lw=.55,z=4)
    rounded(ax,x,y,w,h,'white',0,r=.07,edge=color,lw=.8,shadow=True,z=5)
    line(ax,(x+.13,y+h-.18),(x+w*.63,y+h-.18),color,3,z=6)
    for i in range(rows):
        yy=y+h-.41-i*.18
        if yy>y+.14:line(ax,(x+.14,yy),(x+w*(.8 if i%3 else .66),yy),color,1.5,.7,z=6)


def robot(ax,x,y,scale=1,color='lavender',kind='writer'):
    s=scale
    ax.add_patch(patches.Ellipse((x+.56*s,y+.02*s),.97*s,.14*s,facecolor=C['plum'],edgecolor='none',alpha=.09,zorder=3))
    rounded(ax,x+.23*s,y+.07*s,.66*s,.47*s,color,.65,r=.13*s,shadow=True,z=4)
    rounded(ax,x+.15*s,y+.47*s,.82*s,.64*s,color,.75,r=.17*s,shadow=True,z=6)
    ax.add_patch(patches.Polygon([(x+.97*s,y+.58*s),(x+1.04*s,y+.63*s),(x+1.04*s,y+1.04*s),(x+.97*s,y+1.11*s)],
        facecolor=mix(color,.98),edgecolor='none',zorder=5))
    rounded(ax,x+.25*s,y+.66*s,.62*s,.28*s,'white',0,r=.09*s,z=7)
    for xx in (.41,.70):ax.add_patch(patches.Circle((x+xx*s,y+.80*s),.037*s,facecolor=dark(color),edgecolor='none',zorder=8))
    line(ax,(x+.55*s,y+1.13*s),(x+.55*s,y+1.28*s),color,1.8,z=5)
    ax.add_patch(patches.Circle((x+.55*s,y+1.31*s),.045*s,facecolor=C[color],edgecolor='none',zorder=6))
    line(ax,(x+.34*s,y+.33*s),(x+.78*s,y+.33*s),'white',2,z=7)
    line(ax,(x+.34*s,y+.22*s),(x+.63*s,y+.22*s),'white',1.5,z=7)
    line(ax,(x+.18*s,y+.43*s),(x+.04*s,y+.20*s),color,5,z=4)
    line(ax,(x+.90*s,y+.43*s),(x+1.07*s,y+.64*s),color,5,z=4)
    if kind=='writer':
        line(ax,(x+1.02*s,y+.56*s),(x+1.24*s,y+.85*s),'apricot',3,z=7)
        ax.add_patch(patches.Polygon([(x+1.24*s,y+.85*s),(x+1.28*s,y+.93*s),(x+1.18*s,y+.89*s)],facecolor=C['plum'],edgecolor='none',zorder=7))
    elif kind=='reviewer':
        ax.add_patch(patches.Circle((x+1.20*s,y+.80*s),.17*s,facecolor=(1,1,1,.75),edgecolor=dark(color,.5),lw=1.5,zorder=8))
        line(ax,(x+1.07*s,y+.66*s),(x+.94*s,y+.52*s),color,3,z=8)


def funnel(ax,x,y,w=1,h=1,color='sage'):
    ax.add_patch(patches.Polygon([(x,y+h),(x+w,y+h),(x+w*.65,y+h*.34),(x+w*.65,y),(x+w*.36,y),(x+w*.36,y+h*.34)],
        facecolor=mix(color,.68),edgecolor='none',zorder=5))
    ax.add_patch(patches.Polygon([(x+w*.5,y+h),(x+w,y+h),(x+w*.65,y+h*.34),(x+w*.65,y),(x+w*.5,y)],
        facecolor=mix(color,.84),edgecolor='none',zorder=5))
    ax.add_patch(patches.Ellipse((x+w*.5,y+h),w,.17,facecolor='white',edgecolor=C[color],lw=1,zorder=6))


def ledger(ax,x,y,w=1.2,h=.95,color='lavender'):
    rounded(ax,x+.06,y-.05,w,h,color,.24,r=.07,z=3)
    rounded(ax,x,y,w,h,'white',0,r=.07,edge=color,lw=.8,z=4)
    for i in range(3):
        yy=y+h*(.75-.25*i)
        line(ax,(x+.13,yy),(x+w-.13,yy),color,.8,z=5)
        for j in range(i%2+1):
            xx=x+.27+j*.23+i*.08
            ax.add_patch(patches.Ellipse((xx,yy),min(.10,w*.10),min(.15,h*.22),facecolor=mix(color,.8),edgecolor='none',zorder=6))


def pill(ax,x,y,w,h,label,color='lavender',size=13.5,style='flow'):
    rounded(ax,x,y,w,h,color,.28,r=h/2,z=7)
    text(ax,x+w/2,y+h/2,label,size,style,'plum',ha='center',va='center')


def save(fig,outputstem):
    outputstem=Path(outputstem);outputstem.parent.mkdir(parents=True,exist_ok=True)
    fig.canvas.draw();renderer=fig.canvas.get_renderer();width,height=fig.canvas.get_width_height()
    for ax in fig.axes:
        for label in ax.texts:
            bb=label.get_window_extent(renderer)
            if bb.x0 < -1 or bb.y0 < -1 or bb.x1 > width+1 or bb.y1 > height+1:
                raise ValueError(f'{outputstem.name}: clipped text {label.get_text()!r}')
    for ext in ('pdf','svg','png'):
        fig.savefig(outputstem.with_suffix('.'+ext),dpi=260,facecolor='white')
    plt.close(fig)
