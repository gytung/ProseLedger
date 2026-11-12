"""Vector mechanism figures for the implemented ProseLedger revision workflow."""
from pathlib import Path
import argparse
import json
import math
from style import C,F,mix,dark,canvas,text,title,panel,rounded,line,arrow,ribbon,document,robot,funnel,ledger,pill,save
from matplotlib import patches

ROOT=Path(__file__).resolve().parent


def architecture(out):
    fig,ax=canvas(12,7.1)
    title(ax,7.1,'Natural expression, governed by scientific commitments',
          'Section-level editing · exact evidence review · an auditable retained manuscript')
    panel(ax,.35,2.25,2.02,3.53,'sky',r=.25)
    text(ax,.59,5.56,'Evidence + draft',19,'title','plum')
    document(ax,.64,3.89,.77,1.14,'sky',2,3)
    document(ax,1.31,3.57,.66,1.09,'sage',1,3)
    text(ax,.61,3.33,'Attributed excerpts\nOriginal proposal',14.3,'bold')
    line(ax,(.61,2.91),(2.1,2.91),'sky',1)
    text(ax,.61,2.72,'Supply a draft, or\ngenerate it from a topic.',12.7,'italic')
    panel(ax,2.62,2.25,6.35,3.53,'lavender',r=.30)
    robot(ax,2.86,4.19,.76,'lavender','writer')
    text(ax,3.97,5.5,'Section writer',19,'title','plum')
    text(ax,4.0,5.08,'Six editorial operations\nOne section at a time',14.0,'bold')
    text(ax,3.05,4.04,'Qwen / API writer',12.1,'flow','plum')
    pill(ax,3.99,4.23,1.6,.36,'meaning stays', 'lavender',11.5)
    robot(ax,5.94,4.19,.76,'sage','reviewer')
    text(ax,7.13,5.50,'Section review',18,'title','plum')
    text(ax,7.15,5.06,'Exact quoted spans\nMeaning + readability',13.4,'bold')
    text(ax,6.14,4.04,'Hosted reviewer',12.1,'flow','plum')
    arrow(ax,(2.38,4.75),(2.82,4.75),'sky',lw=2)
    arrow(ax,(5.61,4.30),(5.90,4.30),'lavender',lw=2)
    line(ax,(3.02,3.79),(8.55,3.79),'lavender',.8,alpha=.65)
    text(ax,3.03,3.59,'Bounded repair',18,'title','plum')
    for x,y,w,col in [(3.1,3.08,.88,'apricot'),(3.99,3.08,.65,'sage'),(4.64,3.08,.65,'apricot')]:
        rounded(ax,x,y,w,.20,col,.7,r=.05,z=5)
    text(ax,3.08,2.77,'≤3 exact patches · ≤35% matched text',12.2,'bold')
    text(ax,3.08,2.51,'Unsolved section → original section',12.1,'italic')
    arrow(ax,(7.79,3.89),(5.65,3.55),'apricot',rad=.03,lw=1.7)
    funnel(ax,6.0,2.60,.65,.70,'sage')
    text(ax,6.93,3.53,'Whole-draft audit',17.2,'title','plum')
    text(ax,6.94,3.13,'Meaning · coherence\nLength · citations',12.5,'bold')
    arrow(ax,(5.4,3.10),(5.9,3.10),'apricot',lw=1.8)
    arrow(ax,(8.94,3.62),(9.37,4.32),'sage',rad=-.13,lw=1.7)
    document(ax,9.52,3.78,1.87,1.95,'sage',1,0)
    text(ax,9.73,5.45,'Retain',22,'title','plum')
    text(ax,9.73,4.98,'Checked candidate\nor original fallback',13.7,'bold')
    pill(ax,9.72,4.13,1.47,.35,'final text','sage',12)
    text(ax,9.58,3.47,'No unresolved issue\nReadability no worse\nLength within 85–115%',12.3,'italic')
    arrow(ax,(10.47,2.81),(10.47,2.45),'sky',ls='--',lw=1.4)
    pill(ax,9.55,1.95,1.97,.43,'GPTZero','sky',14)
    text(ax,10.54,1.78,'After retention only\nNo selection feedback',12.2,'italic',ha='center')
    panel(ax,2.62,.46,6.35,1.34,'lavender',r=.23)
    ledger(ax,2.86,.67,1.0,.77,'lavender')
    text(ax,4.12,1.55,'MemGuard-inspired revision ledger',18,'title','plum')
    text(ax,4.14,1.12,'Candidate + findings + patches + decision',13.7,'bold')
    text(ax,4.14,.78,'Verification stays with the edit; no historical-card retrieval.',12.1,'italic')
    arrow(ax,(5.85,2.16),(5.85,1.84),'lavender',lw=1.7)
    text(ax,.55,1.58,'Scientific claims\nstay intact.',17,'title','plum')
    text(ax,.56,.96,'A fluent sentence can still\nchange a scientific claim.',12.7,'italic')
    save(fig,out/'architecture')


def decision_trace(out,evaluation):
    record=json.loads((evaluation/'runs/C01/rules/revision_ledger.json').read_text(encoding='utf-8'))
    assert sum(e['status']=='verified_edit' for e in record['edits'])==5
    last=record['edits'][-1]
    assert last['repair']['reason']=='patch_type' and last['retained']==last['original']
    fig,ax=canvas(12,7.2)
    title(ax,7.2,'From revision error to an auditable fallback',
          'Recorded case C01 · Rules condition · glacier mapping with explicit uncertainty')
    panel(ax,.37,3.52,7.48,2.25,'sky',r=.23)
    document(ax,.57,3.89,.7,1.32,'sky',1,4)
    text(ax,1.50,5.53,'Original commitment',18,'title','plum')
    text(ax,1.52,5.1,'“may make … clearer”\n“while leaving a less complete map”\n“its contribution would be …”',13.4)
    arrow(ax,(4.27,4.60),(4.68,4.60),'lavender',lw=1.8)
    text(ax,4.85,5.53,'Rewritten candidate',18,'title','plum')
    rounded(ax,4.84,4.62,2.71,.43,'apricot',.32,r=.07)
    text(ax,4.98,4.94,'“but it will leave …”',14.1,'bold')
    rounded(ax,4.84,4.05,2.71,.43,'apricot',.26,r=.07)
    text(ax,4.98,4.37,'“its contribution will be …”',13.4,'bold')
    text(ax,1.52,3.96,'Uncertainty is part of the claim.',12.9,'italic','plum')
    robot(ax,8.25,4.16,.85,'sage','reviewer')
    text(ax,9.48,5.50,'Review findings',17.8,'title','plum')
    text(ax,9.49,5.03,'Two stronger claims\nOne new causal link',13.6,'bold')
    text(ax,8.26,3.91,'Added: “as no field measurements\nhave been collected …”',13.0,'italic')
    arrow(ax,(7.93,4.72),(8.31,4.72),'sage',lw=1.8)
    panel(ax,.39,.92,7.47,2.19,'apricot',r=.25)
    text(ax,.65,2.85,'Exact repair proposal',19,'title','plum')
    text(ax,.66,2.39,'Delete the unsupported causal span',14.4,'bold')
    rounded(ax,.67,1.59,2.87,.49,'apricot',.38,r=.07)
    text(ax,.80,1.91,'“as no field measurements …”',13.1,'italic')
    arrow(ax,(3.67,1.84),(4.18,1.84),'apricot',lw=1.7)
    rounded(ax,4.30,1.59,1.0,.49,'white',0,r=.07,edge='apricot')
    text(ax,4.80,1.84,'empty',13.5,'italic',ha='center',va='center')
    funnel(ax,5.66,1.53,.70,.79,'lavender')
    text(ax,6.62,2.34,'Patch set\nrejected',16.5,'title','plum')
    text(ax,.68,1.26,'The patch contract requires non-empty replacements; no partial patch set is applied.',12.7,'italic')
    arrow(ax,(9.46,3.48),(7.17,3.00),'apricot',rad=-.14,lw=1.7)
    document(ax,8.42,.95,2.79,2.15,'sage',1,0)
    text(ax,8.65,2.89,'Retained manuscript',19,'title','plum')
    for i in range(5):
        rounded(ax,8.66,2.36-i*.18,1.09+.11*(i%2),.11,'sage',.58,r=.04,z=6)
    rounded(ax,8.66,1.32,1.09,.22,'lavender',.78,r=.04,z=6)
    text(ax,10.07,2.32,'5 sections\nrevised',14.4,'bold')
    text(ax,10.07,1.59,'Limitations\nrestored',13.5,'bold')
    arrow(ax,(7.91,2.02),(8.35,2.02),'sage',lw=1.8)
    ledger(ax,.56,.24,.85,.52,'lavender')
    text(ax,1.69,.65,'The ledger preserves the candidate, exact findings, rejected repair and final section decision.',13.1,'italic')
    save(fig,out/'extra/revision_decision_trace')


def small_rule_icon(ax,x,y,kind,color):
    if kind=='actor':
        ax.add_patch(patches.Circle((x+.21,y+.47),.11,facecolor=mix(color,.8),edgecolor='none',zorder=5))
        ax.add_patch(patches.Arc((x+.21,y+.08),.48,.58,theta1=10,theta2=170,color=C[color],lw=4,zorder=5))
        arrow(ax,(x+.48,y+.25),(x+1.0,y+.25),color,lw=2)
        text(ax,x+1.08,y+.44,'act',16,'flow','plum')
    elif kind=='detail':
        document(ax,x+.10,y-.02,.55,.75,color,1,2)
        ax.add_patch(patches.Circle((x+.91,y+.45),.22,facecolor=(1,1,1,.75),edgecolor=C[color],lw=2,zorder=7))
        line(ax,(x+.76,y+.28),(x+.60,y+.09),color,3,z=8)
    elif kind=='trim':
        for i,w in enumerate([1.52,1.21,.85]):line(ax,(x,y+.52-i*.19),(x+w,y+.52-i*.19),color,3)
        line(ax,(x+.55,y+.52),(x+1.62,y+.52),'plum',1)
        pill(ax,x+1.12,y-.10,.72,.29,'less',color,10.5)
    elif kind=='flow':
        for i in range(3):
            ax.add_patch(patches.Ellipse((x+.18+i*.61,y+.30),.33,.25,facecolor=mix(color,.8),edgecolor='none',zorder=5))
            if i<2:arrow(ax,(x+.37+i*.61,y+.3),(x+.58+i*.61,y+.3),color,lw=1.2,head=9)
    elif kind=='sentence':
        for yy in [.55,.35,.15]:line(ax,(x, y+yy),(x+.55,y+yy),color,2)
        arrow(ax,(x+.66,y+.34),(x+.98,y+.34),color,lw=1.4,head=9)
        for xx,yy,w in [(1.12,.57,.65),(1.12,.42,.54),(1.12,.13,.65),(1.12,-.02,.47)]:line(ax,(x+xx,y+yy),(x+xx+w,y+yy),color,2)
    else:
        line(ax,(x,y+.25),(x+1.65,y+.25),color,2)
        for xx in [.08,.58,1.08,1.58]:ax.add_patch(patches.Circle((x+xx,y+.25),.055,facecolor=C[color],edgecolor='none',zorder=5))
        ax.add_patch(patches.Circle((x+.58,y+.25),.15,facecolor='white',edgecolor=C[color],lw=2,zorder=6))
        text(ax,x+.58,y+.75,'may',14.6,'flow','plum',ha='center')


def operations(out):
    fig,ax=canvas(12,8.1)
    title(ax,8.1,'Editing rules anchored to scientific commitments',
          'Illustrative edits · evidence, attribution and the status of the proposed study remain fixed')
    cases=[
      ('Actor and action','Prefer a direct verb.','“measurement of” → “measure”','Keep the stated actor.','actor','sky'),
      ('Concrete wording','Use details already supplied.','“the method” → “the boundary check”','Do not invent method details.','detail','sage'),
      ('Redundancy','Remove repeated meaning.','“in order to” → “to”','Preserve every qualification.','trim','lavender'),
      ('Information flow','Clarify an existing relation.','evidence → claim → qualification','Do not invent causality.','flow','sage'),
      ('Sentence focus','Separate competing ideas.','one crowded sentence → two','Keep dependencies and citations.','sentence','sky'),
      ('Calibrated claims','Match the stated evidence.','“may improve” stays conditional','Keep scope and planned status.','modal','apricot')]
    positions=[(.45,4.94),(8.13,4.94),(.45,2.89),(8.13,2.89),(.45,.84),(8.13,.84)]
    for i,((name,operation,example,boundary,kind,col),(x,y)) in enumerate(zip(cases,positions)):
        panel(ax,x,y,3.43,1.94,col,r=.19)
        small_rule_icon(ax,x+.18,y+1.20,kind,col)
        text(ax,x+.18,y+1.10,name,18.4,'title','plum')
        text(ax,x+.18,y+.72,operation,13.0,'bold')
        text(ax,x+.18,y+.43,example,11.8,'italic')
        text(ax,x+.18,y+.20,boundary,10.7,'body')
    ax.add_patch(patches.Ellipse((6.0,4.16),3.5,4.94,facecolor=mix('lavender',.10),edgecolor='none',zorder=0))
    document(ax,5.17,2.77,1.54,2.22,'lavender',2,6)
    robot(ax,5.20,4.21,1.13,'lavender','writer')
    text(ax,6,6.18,'Section writer',18.2,'title','plum',ha='center')
    pill(ax,4.64,2.08,2.72,.45,'change the expression','lavender',12.3)
    text(ax,6,1.45,'Scientific meaning\nis the boundary.',18.2,'title','plum',ha='center')
    for x,y in [(3.96,5.81),(3.96,3.76),(3.96,1.71)]:
        arrow(ax,(x,y),(4.72,4.18+(y-3.76)*.40),'lavender',lw=1.2,rad=-.12 if y<3.76 else .12)
    for x,y in [(8.04,5.81),(8.04,3.76),(8.04,1.71)]:
        arrow(ax,(x,y),(7.27,4.18+(y-3.76)*.40),'lavender',lw=1.2,rad=.12 if y<3.76 else -.12)
    text(ax,.52,.31,'Six operations are supplied to the writer as explicit instructions; verification decides which resulting text survives.',13.2,'italic')
    save(fig,out/'extra/six_editorial_operations')


def evaluation_design(out,evaluation):
    index=json.loads((evaluation/'input_index.json').read_text(encoding='utf-8'))
    inputs=[json.loads((evaluation/'inputs'/(r['caseId']+'.json')).read_text(encoding='utf-8')) for r in index]
    assert len(inputs)==12 and sum(len(r['knownFacts']) for r in inputs)==72
    fig,ax=canvas(12,7.75)
    title(ax,7.75,'Paired evaluation with a fixed writer and evidence set',
          'Fixed inputs and writer configuration · common verification policy · post-selection evaluation')
    document(ax,.45,3.30,2.14,2.89,'sky',2,0)
    text(ax,.67,5.91,'Frozen inputs',21,'title','plum')
    text(ax,.68,5.41,'12 proposals',22,'flow','plum')
    text(ax,.68,4.86,'6 sections each\n2 source excerpts each',14.0,'bold')
    text(ax,.68,4.12,'72 reference facts',16,'bold')
    text(ax,.68,3.71,'Fixed before inference',12.8,'italic')
    panel(ax,3.13,3.12,8.36,3.18,'lavender',r=.28)
    text(ax,3.42,6.02,'Same Qwen2.5 7B writer · same sources and section seeds',17.0,'title','plum')
    for x,col,name,desc in [(3.48,'sky','Generic','Ordinary copy-editing'),(7.44,'lavender','Rules','Six explicit operations')]:
        robot(ax,x,4.24,.80,col,'writer')
        text(ax,x+1.25,5.50,name,21,'title','plum')
        text(ax,x+1.27,5.08,desc,13.7,'bold')
        text(ax,x+1.27,4.70,'6 section-writing calls',12.6,'italic')
        funnel(ax,x+.16,3.45,.61,.58,'sage')
        arrow(ax,(x+.49,4.14),(x+.49,4.05),'sage',lw=1.6)
        text(ax,x+1.15,3.97,'Audit → repair → retain',14.0,'bold')
        text(ax,x+1.15,3.57,'Preserve all decisions',12.7,'italic')
    arrow(ax,(2.75,5.05),(3.42,5.05),'sky',lw=1.8)
    ribbon(ax,(2.72,5.66),(7.88,5.66),.10,'sky',.25)
    arrow(ax,(7.88,5.66),(7.88,5.38),'sky',lw=1.4)
    text(ax,.62,2.77,'No historical\ncard retrieval',16.2,'title','plum')
    panel(ax,3.13,1.00,4.0,1.63,'sage',r=.25)
    text(ax,3.38,2.39,'Order-reversed blind comparison',17.3,'title','plum')
    pill(ax,3.41,1.59,.65,.40,'A','sage',14)
    pill(ax,4.12,1.59,.65,.40,'B','lavender',14)
    arrow(ax,(4.96,1.78),(5.40,1.78),'sage',lw=1.4)
    pill(ax,5.55,1.59,.65,.40,'B','lavender',14)
    pill(ax,6.26,1.59,.65,.40,'A','sage',14)
    text(ax,3.40,1.29,'Naturalness + reference-fact judgments',12.8,'bold')
    panel(ax,7.51,1.00,3.98,1.63,'sky',r=.25)
    text(ax,7.78,2.40,'Independent GPTZero observation',16.8,'title','plum')
    text(ax,7.79,1.95,'Original + both retained texts',14.0,'bold')
    line(ax,(7.85,1.53),(10.96,1.53),'sky',2)
    text(ax,7.85,1.42,'0%',11.8,'italic')
    text(ax,10.96,1.42,'100%',11.8,'italic',ha='right')
    line(ax,(3.94,3.37),(3.94,2.95),'lavender',1.3)
    line(ax,(7.90,3.37),(7.90,2.95),'lavender',1.3)
    line(ax,(3.94,2.95),(9.48,2.95),'lavender',1.3)
    text(ax,6.50,3.10,'Both retained texts',11.5,'italic','plum',ha='center')
    arrow(ax,(5.1,2.95),(5.1,2.70),'sage',lw=1.7)
    arrow(ax,(9.48,2.95),(9.48,2.70),'sky',lw=1.7)
    text(ax,.65,1.89,'Reference facts\nsupport content\npreservation checks.',13.3,'italic')
    arrow(ax,(2.51,1.85),(3.06,1.85),'sage',lw=1.3)
    text(ax,7.75,.73,'Observation only; no feedback to selection.',12.5,'italic','plum')
    text(ax,.51,.34,'Writer settings are matched. Adaptive repair costs may differ. Automated judgments remain separate from human ratings.',12.7,'italic')
    save(fig,out/'extra/evaluation_design')


def laptop(ax,x,y,color='sage',label='7B'):
    rounded(ax,x,y,.0+1.43,.92,color,.38,r=.10,shadow=True,z=4)
    rounded(ax,x+.08,y+.10,1.27,.72,'white',0,r=.06,z=5)
    text(ax,x+.71,y+.64,label,21,'flow','plum',ha='center')
    ax.add_patch(patches.Polygon([(x-.17,y-.11),(x+1.60,y-.11),(x+1.43,y),(x,y)],facecolor=mix(color,.88),edgecolor='none',zorder=5))


def deployment_routes(out):
    fig,ax=canvas(12,7.6)
    title(ax,7.6,'One editing logic, three execution conditions',
          'Interfaces share revision principles; model identity and experimental outcomes belong to their own route')
    starts=[.43,4.48,8.52]
    palette=['sky','sage','lavender']
    for x,col in zip(starts,palette):
        ax.add_patch(patches.Ellipse((x+1.52,4.41),3.32,4.10,facecolor=mix(col,.15),edgecolor='none',zorder=0))
    text(ax,.67,6.12,'Browser API',23,'title','plum')
    text(ax,4.73,6.12,'Desktop Ollama',23,'title','plum')
    text(ax,8.77,6.12,'Archived MLX study',21,'title','plum')
    laptop(ax,.81,4.66,'sky','API')
    robot(ax,2.32,4.55,.63,'sky','reviewer')
    laptop(ax,4.89,4.66,'sage','7B')
    robot(ax,6.36,4.55,.63,'sage','reviewer')
    laptop(ax,8.93,4.66,'lavender','MLX')
    document(ax,10.51,4.53,.64,1.05,'lavender',2,3)
    text(ax,.68,4.18,'Visitor-selected cloud models',16.1,'bold')
    text(ax,.69,3.76,'Draft · rewrite · review\nOptional separate writer ID\nSame provider and API key',14.0)
    text(ax,.69,2.79,'Own API credit\nNo installation or local model',13.8,'title','plum')
    text(ax,4.73,4.18,'Qwen2.5 7B · Q4_K_M',16.0,'bold')
    text(ax,4.74,3.76,'Local section rewriting\nHosted draft, audit and repair\nWindows + macOS application',14.0)
    text(ax,4.74,2.79,'Own computer + review access\nNo Qwen API key',13.8,'title','plum')
    text(ax,8.77,4.18,'Qwen2.5 7B · MLX 4-bit',16.0,'bold')
    text(ax,8.78,3.76,'Apple Silicon local writer\nHosted review and repair\nPinned research configuration',14.0)
    text(ax,8.78,2.79,'Archived Mac measurements\nSeparate reproduction profile',13.8,'title','plum')
    for x,col in zip(starts,palette):
        arrow(ax,(x+1.52,2.28),(x+1.52,1.97),col,lw=1.6)
        document(ax,x+.10,.86,.56,.86,col,1,3)
        ledger(ax,x+.87,.88,.79,.64,col)
        text(ax,x+1.91,1.61,'Manuscript\n+ decision ledger',13.7,'bold')
    line(ax,(.5,.59),(11.48,.59),'gray',.9)
    text(ax,6,.35,'A detector score belongs to the exact text, model, runtime and detector version used in that run.',13.0,'italic',ha='center')
    save(fig,out/'extra/deployment_routes')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluation',type=Path,default=ROOT.parent/'evaluation')
    parser.add_argument('--output-dir',type=Path,default=ROOT/'assets')
    args=parser.parse_args();out=args.output_dir
    architecture(out);decision_trace(out,args.evaluation);operations(out)
    evaluation_design(out,args.evaluation);deployment_routes(out)
    (out/'mechanism_asset_provenance.json').write_text(json.dumps({
      'graphics':'Original vector drawings produced by the accompanying Matplotlib scripts.',
      'brandAssetsUsed':False,
      'modelDepiction':'Custom, explicitly labelled model and agent glyphs; not official Qwen logos.',
      'data':'C01 Rules revision ledger and frozen 12-case input set; illustrative editorial examples are labelled.',
      'figures':['architecture','extra/revision_decision_trace','extra/six_editorial_operations','extra/evaluation_design','extra/deployment_routes']
    },indent=2)+'\n',encoding='utf-8')
    print('Rendered 5 mechanism figure sets in PDF, SVG and PNG.')


if __name__=='__main__':main()
