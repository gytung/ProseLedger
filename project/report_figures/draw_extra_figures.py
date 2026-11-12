from pathlib import Path
import os
import tempfile
os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'proseledger-mpl'))
import json
import math
import textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import patches
from matplotlib.path import Path as MPath
from matplotlib.font_manager import FontProperties, findfont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'assets' / 'extra'
OUT.mkdir(parents=True, exist_ok=True)
FONT = Path('/System/Library/Fonts/Supplemental')
def font(filename, family, weight='normal', style='normal', fallback='DejaVu Serif'):
    if (FONT / filename).exists():
        return FontProperties(fname=str(FONT / filename))
    properties = FontProperties(family=family, weight=weight, style=style)
    try:
        return FontProperties(fname=findfont(properties, fallback_to_default=False))
    except ValueError:
        return FontProperties(family=fallback, weight=weight, style=style)


F = {
    'body': font('Times New Roman.ttf', 'Times New Roman'),
    'bold': font('Times New Roman Bold.ttf', 'Times New Roman', weight='bold'),
    'italic': font('Times New Roman Italic.ttf', 'Times New Roman', style='italic'),
    'title': font('Times New Roman Bold Italic.ttf', 'Times New Roman', weight='bold', style='italic'),
    'flow': font('Comic Sans MS Bold.ttf', 'Comic Sans MS', weight='bold', fallback='DejaVu Sans'),
}
C = {'plum':'#5D425F','lav':'#C4B7D7','sage':'#A8BCA3','sky':'#8FBFDA',
     'apricot':'#E8B792','rose':'#CA8894','gray':'#E3E1E6','ink':'#4F4854',
     'softlav':'#F4F0F8','softsage':'#F1F5EF','softsky':'#EFF6FA',
     'softapricot':'#FCF1E8','softrose':'#F9EDF0'}
plt.rcParams.update({'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none',
                     'savefig.facecolor':'white','figure.facecolor':'white'})


def canvas(h):
    fig, ax = plt.subplots(figsize=(12, h))
    fig.subplots_adjust(left=0,right=1,top=1,bottom=0)
    ax.set_xlim(0,12);ax.set_ylim(0,h);ax.axis('off')
    return fig,ax


def text(ax,x,y,s,size=16,style='body',color='ink',ha='left',va='top',alpha=1):
    return ax.text(x,y,s,fontsize=size,fontproperties=F[style],color=C.get(color,color),
                   ha=ha,va=va,linespacing=1.18,alpha=alpha,zorder=10)


def line(ax,x1,y1,x2,y2,color='lav',lw=1.4,alpha=1,ls='-'):
    ax.plot([x1,x2],[y1,y2],color=C.get(color,color),lw=lw,alpha=alpha,ls=ls,zorder=3)


def arrow(ax,start,end,color='lav',rad=0,lw=1.8,style='-|>',alpha=1):
    ax.add_patch(patches.FancyArrowPatch(start,end,arrowstyle=style,mutation_scale=13,
        connectionstyle=f'arc3,rad={rad}',color=C.get(color,color),lw=lw,alpha=alpha,zorder=4))


def capsule(ax,x,y,w,h,fill='softlav',edge=None,r=.16,shadow=False,lw=1):
    if shadow:
        ax.add_patch(patches.FancyBboxPatch((x+.035,y-.045),w,h,boxstyle=f'round,pad=0,rounding_size={r}',
            facecolor='#DAD5DF',edgecolor='none',alpha=.24,zorder=1))
    p=patches.FancyBboxPatch((x,y),w,h,boxstyle=f'round,pad=0,rounding_size={r}',
        facecolor=C.get(fill,fill),edgecolor=C.get(edge,edge) if edge else 'none',lw=lw,zorder=2)
    ax.add_patch(p);return p


def doc(ax,x,y,w,h,accent='lav',stack=True):
    if stack:
        for d in (.10,.05):
            capsule(ax,x+d,y-d,w,h,'white',edge='gray',r=.08,lw=.7)
    capsule(ax,x,y,w,h,'white',edge='gray',r=.08,shadow=True,lw=.8)
    line(ax,x+.15,y+h-.2,x+.15+w*.42,y+h-.2,accent,lw=4)


def doclines(ax,x,y,w,rows=4,color='lav',gap=.13):
    for i in range(rows):
        length=w*(.93 if i%3 else .70)
        line(ax,x,y-i*gap,x+length,y-i*gap,color,lw=2,alpha=.75)


def funnel(ax,x,y,w,h,color='lav'):
    verts=[(x,y+h),(x+w,y+h),(x+w*.65,y+h*.34),(x+w*.65,y),
           (x+w*.35,y),(x+w*.35,y+h*.34),(x,y+h)]
    ax.add_patch(patches.PathPatch(MPath(verts,[MPath.MOVETO]+[MPath.LINETO]*5+[MPath.CLOSEPOLY]),
                                  facecolor=C[color],edgecolor='none',alpha=.7,zorder=3))
    ax.add_patch(patches.Ellipse((x+w/2,y+h),w,.16,facecolor='white',edgecolor=C[color],lw=1.2,zorder=4))


def chip(ax,x,y,w=.8,h=.65,color='sage'):
    capsule(ax,x,y,w,h,'white',edge=color,r=.10,lw=1.2)
    for i in range(4):
        yy=y+.1+i*(h-.2)/3
        line(ax,x-.08,yy,x,yy,color,1.5);line(ax,x+w,yy,x+w+.08,yy,color,1.5)
    for i in range(3):
        xx=x+.14+i*(w-.28)/2
        line(ax,xx,y-.08,xx,y,color,1.5);line(ax,xx,y+h,xx,y+h+.08,color,1.5)
    capsule(ax,x+.16,y+.15,w-.32,h-.3,'soft'+color if 'soft'+color in C else 'softlav',r=.04)


def cloud(ax,x,y,w=1.2,h=.7,color='sky'):
    for xx,yy,rr in [(x+.25*w,y+.3*h,.25*w),(x+.5*w,y+.6*h,.32*w),(x+.76*w,y+.3*h,.26*w)]:
        ax.add_patch(patches.Ellipse((xx,yy),rr*2,rr*1.6,facecolor=C[color],edgecolor='none',alpha=.85,zorder=3))
    capsule(ax,x+.08*w,y-.01*h,.84*w,.42*h,color,r=.12)


def title(ax,h,heading,sub):
    text(ax,.35,h-.2,heading,29,'title','plum')
    text(ax,.37,h-.77,sub,15,'body','ink')


def save(fig,name):
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer();w,h=fig.canvas.get_width_height();outside=[]
    for ax in fig.axes:
        for item in ax.texts:
            bb=item.get_window_extent(renderer)
            if bb.x0 < -1 or bb.y0 < -1 or bb.x1 > w+1 or bb.y1 > h+1:outside.append(item.get_text())
    if outside:raise ValueError(name+' clipped labels: '+repr(outside))
    for ext in ('pdf','svg','png'):
        fig.savefig(OUT/(name+'.'+ext),dpi=220,facecolor='white',bbox_inches=None)
    plt.close(fig)


def decision_trace():
    record=json.loads((ROOT.parent/'evaluation/runs/C01/rules/revision_ledger.json').read_text())
    edits=record['edits'];assert sum(e['status']=='verified_edit' for e in edits)==5
    last=edits[-1];assert last['repair']['reason']=='patch_type' and last['retained']==last['original']
    fig,ax=canvas(7.4)
    title(ax,7.4,'One difficult section. One inspectable decision.','Recorded C01 · Rules arm · the proposed glacier-mapping study')
    doc(ax,.4,2.15,2.65,3.65,'sky')
    text(ax,.63,5.45,'Original limitation',20,'bold','plum')
    text(ax,.63,4.89,'A possible trade-off',16,'title','plum')
    text(ax,.63,4.51,'“may make the limits\nof the evidence clearer\nwhile leaving a less\ncomplete map”',16)
    text(ax,.63,3.28,'Conditional contribution',15,'title','plum')
    text(ax,.63,2.92,'“Its contribution would be\na more explicit account…”',15.5)
    arrow(ax,(3.15,4.0),(3.52,4.0),'sky')
    doc(ax,3.62,2.15,3.32,3.65,'apricot')
    text(ax,3.85,5.45,'Qwen candidate',20,'bold','plum')
    capsule(ax,3.82,4.22,2.92,.7,'softapricot',r=.08)
    text(ax,3.96,4.79,'“but it will leave a\nless complete map”',16,'bold')
    text(ax,3.86,4.06,'Possibility becomes certainty',14,'italic','plum')
    capsule(ax,3.82,3.02,2.92,.7,'softrose',r=.08)
    text(ax,3.96,3.59,'“as no field measurements\nhave been collected…”',15.5,'bold')
    text(ax,3.86,2.85,'A causal explanation is added',14,'italic','plum')
    text(ax,3.86,2.47,'“would be” → “will be”',15.5,'bold')
    arrow(ax,(7.03,4.0),(7.55,4.0),'apricot')
    funnel(ax,7.58,3.47,1.12,1.12,'lav')
    text(ax,8.14,5.39,'Review + repair',18,'bold','plum',ha='center')
    text(ax,8.14,4.93,'3 localized findings',14,'italic',ha='center')
    text(ax,8.14,3.14,'Patch set\nrejected',17,'bold','plum',ha='center')
    arrow(ax,(8.77,4.0),(9.23,4.0),'sage')
    doc(ax,9.31,2.15,2.24,3.65,'sage',stack=False)
    text(ax,9.51,5.45,'Retained draft',19,'bold','plum')
    labels=['Abstract','Introduction','Related Work','Methodology','Planned Evaluation']
    for i,label in enumerate(labels):
        yy=4.78-i*.37
        capsule(ax,9.49,yy-.12,1.87,.27,'softsage',r=.06)
        text(ax,9.6,yy+.08,label,12.3)
    capsule(ax,9.49,2.46,1.87,.44,'softlav',r=.06)
    text(ax,9.6,2.79,'Original limitation',13,'bold','plum')
    text(ax,9.51,2.02,'5 revised · 1 restored',12.5,'italic')
    capsule(ax,.44,.64,8.27,1.12,'softlav',r=.2)
    text(ax,.68,1.53,'Why the repair did not pass',18,'title','plum')
    text(ax,.68,1.16,'Requested replacement: empty text',15,'bold')
    arrow(ax,(4.05,1.02),(4.45,1.02),'lav')
    text(ax,4.58,1.27,'The patch contract requires non-empty text.\nThe whole patch set is rejected, not partly applied.',14.3)
    arrow(ax,(7.91,2.03),(7.91,1.79),'lav')
    text(ax,9.37,1.58,'The ledger keeps',16,'title','plum')
    text(ax,9.37,1.2,'candidate · findings\nfailed repair · decision',14.5)
    text(ax,.45,.28,'Review findings are automated observations. The final decision retains useful edits without forcing every section to change.',13,'italic')
    save(fig,'revision_decision_trace')


def operations():
    fig,ax=canvas(7.4)
    title(ax,7.4,'Six editorial operations, with explicit boundaries','Illustrative examples · apply only when the stated meaning and evidence already support the edit')
    xs=[.4,4.35,8.3];ys=[3.65,.65]
    cards=[
      ('Actor and action','Prefer a direct verb.','“measurement of” → “measure”','Do not invent an actor.','sky'),
      ('Concrete wording','Use detail already supplied.','“the method” → “the boundary check”','Do not invent a method detail.','sage'),
      ('Redundancy','Remove repeated framing.','“in order to” → “to”','Keep uncertainty and conditions.','lav'),
      ('Information flow','Clarify an existing relation.','evidence → claim → qualification','Do not invent causality.','sage'),
      ('Sentence focus','Separate competing ideas.','one crowded sentence → two','Keep dependencies and citations.','sky'),
      ('Calibrated claims','Match the stated evidence.','“may improve” remains “may improve”','Keep planned work and uncertainty.','apricot')]
    for i,(name,op,example,guard,color) in enumerate(cards):
        x=xs[i%3];y=ys[i//3]
        ax.add_patch(patches.Ellipse((x+.48,y+1.92),.95,.9,facecolor=C['soft'+color],edgecolor='none',zorder=1))
        if i==0:
            ax.add_patch(patches.Circle((x+.36,y+2.1),.095,facecolor=C[color],edgecolor='none'))
            ax.add_patch(patches.Arc((x+.36,y+1.79),.36,.45,theta1=0,theta2=180,color=C[color],lw=3))
            arrow(ax,(x+.59,y+1.98),(x+1.13,y+1.98),color)
            text(ax,x+1.2,y+2.13,'act',19,'flow',color)
        elif i==1:
            ax.add_patch(patches.Circle((x+.42,y+2.03),.19,facecolor='white',edgecolor=C[color],lw=2))
            line(ax,x+.57,y+1.89,x+.79,y+1.68,color,3)
            line(ax,x+.3,y+2.03,x+.52,y+2.03,color,2)
            doclines(ax,x+.95,y+2.16,1.0,3,color,.16)
        elif i==2:
            text(ax,x+.1,y+2.19,'to',24,'title',color)
            text(ax,x+.8,y+2.19,'in order to',18,'italic',alpha=.45)
            line(ax,x+.78,y+2.05,x+2.15,y+2.05,'lav',1.4)
        elif i==3:
            for k in range(3):
                ax.add_patch(patches.Circle((x+.22+.56*k,y+2.02),.11,facecolor=C[color],edgecolor='none'))
                if k<2:arrow(ax,(x+.36+.56*k,y+2.02),(x+.61+.56*k,y+2.02),color,lw=1.1)
            line(ax,x+.15,y+1.79,x+1.5,y+1.79,color,.8)
        elif i==4:
            doclines(ax,x+.05,y+2.15,.72,4,color,.11)
            arrow(ax,(x+.9,y+1.99),(x+1.24,y+1.99),color,lw=1.1)
            doclines(ax,x+1.38,y+2.2,.8,2,color,.12)
            doclines(ax,x+1.38,y+1.86,.65,2,color,.12)
        else:
            line(ax,x+.1,y+1.98,x+2.4,y+1.98,color,2)
            for k in range(4):ax.add_patch(patches.Circle((x+.2+k*.7,y+1.98),.055,facecolor=C[color],edgecolor='none'))
            ax.add_patch(patches.Circle((x+.9,y+1.98),.13,facecolor='white',edgecolor=C[color],lw=2))
            text(ax,x+.9,y+2.32,'may',15,'flow','plum',ha='center')
        text(ax,x,y+1.45,name,21,'title','plum')
        text(ax,x,y+1.02,op,16,'bold')
        text(ax,x,y+.59,example,13.8,'body')
        line(ax,x,y+.25,x+3.25,y+.25,color,lw=1.4,alpha=.85)
        text(ax,x,y+.1,guard,13.5,'italic')
    text(ax,.43,.25,'Operations change expression. They do not supply missing evidence, alter the proposed study or lower a detector score by construction.',12.5,'italic')
    save(fig,'six_editorial_operations')


def evaluation_design():
    index=json.loads((ROOT.parent/'evaluation/input_index.json').read_text())
    inputs=[json.loads((ROOT.parent/'evaluation/inputs'/(x['caseId']+'.json')).read_text()) for x in index]
    assert len(inputs)==12 and sum(len(x['knownFacts']) for x in inputs)==72
    fig,ax=canvas(8.15)
    title(ax,8.15,'Test the editing policy, with the writer held constant','Twelve frozen proposals · paired comparison · complete outcomes retained')
    doc(ax,.4,3.05,2.25,3.25,'sky')
    text(ax,.64,6.0,'Frozen input set',20,'title','plum')
    text(ax,.64,5.47,'12 proposals',21,'bold','sky')
    text(ax,.64,5.02,'6 sections each\n2 source excerpts each',15)
    line(ax,.65,4.2,2.35,4.2,'sky',1.3)
    text(ax,.64,3.99,'72 reference facts',17,'bold','plum')
    text(ax,.64,3.58,'Fixed before inference',14,'italic')
    for yy,col,label in [(5.35,'lav','Generic'),(3.45,'sage','Rules')]:
        capsule(ax,3.3,yy-.72,7.9,1.44,'soft'+col,r=.35)
        text(ax,3.55,yy+.46,label,20,'title','plum')
        text(ax,3.55,yy+.06,'Ordinary copy-editing' if label=='Generic' else 'Six explicit operations',13.8)
        chip(ax,5.65,yy-.22,.72,.55,col)
        text(ax,6.01,yy-.44,'Qwen2.5 7B',12.5,'bold',ha='center')
        arrow(ax,(5.16,yy+.01),(5.49,yy+.01),col)
        arrow(ax,(6.53,yy+.01),(7.03,yy+.01),col)
        funnel(ax,7.24,yy-.35,.75,.7,col)
        text(ax,7.61,yy-.49,'Audit + retain',12.8,'bold',ha='center')
        arrow(ax,(8.15,yy+.01),(8.69,yy+.01),col)
        doc(ax,8.9,yy-.47,.59,.96,col,stack=False)
        doclines(ax,9.0,yy+.2,.36,4,col,.12)
        text(ax,9.7,yy+.24,'Retained text',15,'bold')
        text(ax,9.7,yy-.13,'+ full ledger',13.5,'italic')
    arrow(ax,(2.73,4.85),(3.23,5.35),'sky',rad=-.12)
    arrow(ax,(2.73,4.5),(3.23,3.45),'sky',rad=.12)
    text(ax,5.45,6.53,'Same writer, sources and seeds',16,'title','plum')
    text(ax,5.45,6.17,'6 section calls per arm · shared verification policy',13.8)
    text(ax,.5,2.35,'No historical\ncard retrieval',16,'title','plum')
    text(ax,.5,1.6,'Reference facts support\ncontent-preservation checks.',14)
    capsule(ax,3.35,.73,3.57,1.27,'softsage',r=.22)
    text(ax,3.6,1.78,'Blind comparison',19,'title','plum')
    text(ax,3.6,1.36,'A/B and B/A · readability\n+ reference-fact judgments',14.4)
    capsule(ax,7.46,.73,3.74,1.27,'softlav',r=.22)
    text(ax,7.7,1.78,'External GPTZero',19,'title','plum')
    text(ax,7.7,1.36,'Original + retained text\nobserved after selection',14.4)
    line(ax,11.34,5.35,11.55,5.35,'lav',1.4)
    line(ax,11.34,3.45,11.55,3.45,'sage',1.4)
    line(ax,11.55,5.35,11.55,2.65,'lav',1.4)
    line(ax,5.52,2.65,11.55,2.65,'lav',1.4)
    text(ax,7.85,2.54,'Both retained outputs',12.5,'italic','plum',ha='center')
    arrow(ax,(5.52,2.65),(5.52,2.08),'sage',lw=1.4)
    arrow(ax,(9.67,2.65),(9.67,2.08),'lav',lw=1.4)
    arrow(ax,(2.66,1.62),(3.22,1.62),'sage',lw=1.3)
    text(ax,7.65,.44,'Observation only — no feedback to selection',12.7,'italic','plum')
    text(ax,.42,.2,'Writer configuration is matched; adaptive repair costs may differ. Automated judgments remain distinct from human ratings.',12.8,'italic')
    save(fig,'evaluation_design')


def deployment_routes():
    fig,ax=canvas(7.7)
    title(ax,7.7,'One revision task, three execution conditions','The interfaces share an editing logic; model identity and measured outcomes remain route-specific.')
    xs=[.43,4.47,8.51];cols=['sky','sage','lav']
    for x,col in zip(xs,cols):
        capsule(ax,x,1.56,3.08,4.73,'soft'+col,r=.42)
        ax.add_patch(patches.Ellipse((x+1.54,5.75),2.9,.65,facecolor=C[col],edgecolor='none',alpha=.16,zorder=2))
    text(ax,.69,6.0,'Browser API',23,'title','plum')
    text(ax,4.73,6.0,'Desktop Ollama',23,'title','plum')
    text(ax,8.77,6.0,'Mac MLX study',23,'title','plum')
    capsule(ax,.83,4.62,1.28,.93,'white',edge='sky',r=.1,shadow=True)
    line(ax,.84,5.34,2.1,5.34,'sky',1.2)
    for k in range(3):ax.add_patch(patches.Circle((.98+.13*k,5.44),.025,facecolor=C['sky'],edgecolor='none'))
    doclines(ax,1.01,5.13,.85,3,'sky',.14)
    arrow(ax,(2.2,5.08),(2.47,5.08),'sky',lw=1.3)
    cloud(ax,2.48,4.91,.73,.46,'sky')
    text(ax,.7,4.28,'Visitor-selected cloud model',16.5,'bold')
    text(ax,.7,3.83,'Draft · rewrite · review\nOptional separate writer ID\nSame provider and API key',15)
    text(ax,.7,2.78,'No local installation',16,'title','plum')
    text(ax,.7,2.36,'HTTPS + CORS\nVisitor’s own API credit',14)
    chip(ax,4.92,4.75,1.0,.73,'sage')
    text(ax,5.42,5.23,'7B',16,'bold','plum',ha='center')
    arrow(ax,(6.1,5.08),(6.38,5.08),'sage',lw=1.3)
    cloud(ax,6.39,4.91,.73,.46,'sky')
    text(ax,4.73,4.28,'Qwen2.5 7B · Q4_K_M',16,'bold')
    text(ax,4.73,3.83,'Local section rewriting\nHosted draft, audit and repair\nWindows + macOS application',14.8)
    text(ax,4.73,2.78,'Own computer + review access',15.5,'title','plum')
    text(ax,4.73,2.36,'Ollama model download\nNo Qwen API key',14)
    chip(ax,8.99,4.75,1.0,.73,'lav')
    text(ax,9.49,5.23,'MLX',14.5,'bold','plum',ha='center')
    doc(ax,10.56,4.72,.46,.72,'lav',stack=True)
    doclines(ax,10.64,5.2,.27,3,'lav',.12)
    text(ax,8.77,4.28,'Qwen2.5 7B · MLX 4-bit',16,'bold')
    text(ax,8.77,3.83,'Apple Silicon local writer\nHosted review and repairs\nPinned research configuration',14.8)
    text(ax,8.77,2.78,'Archived Mac measurements',15.5,'title','plum')
    text(ax,8.77,2.36,'Frozen inputs and outputs\nSeparate reproduction profile',14)
    for x,col in zip(xs,cols):
        arrow(ax,(x+1.54,1.49),(x+1.54,1.03),col,lw=1.4)
        text(ax,x+1.54,.92,'manuscript + decision ledger',14.5,'bold','plum',ha='center')
    line(ax,.55,.53,11.41,.53,'gray',1.3)
    text(ax,6,.32,'A detector score belongs to its text, model, runtime and detector version — it does not transfer across routes.',13.5,'italic',ha='center')
    save(fig,'deployment_routes')


if __name__=='__main__':
    decision_trace();operations();evaluation_design();deployment_routes()
    print(json.dumps({'figures':['revision_decision_trace','six_editorial_operations','evaluation_design','deployment_routes'],
       'formats':['pdf','svg','png'],'canvas':'white','svgText':'editable','pdfFonts':'embedded TrueType',
       'widthInches':12,'heightsInches':[7.4,7.4,8.15,7.7]},indent=2))
