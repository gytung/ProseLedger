"""Publication-scale mechanism diagrams tied to the implemented editing contract."""
from pathlib import Path
import argparse
import json
import hashlib
from style import C,F,mix,canvas,text,box,line,arrow,tag,page,agent,save
from matplotlib import patches
ROOT=Path(__file__).resolve().parent

def panel_head(ax,x,y,label):text(ax,x,y,label,9.4,'title')

def architecture(out):
    fig,ax=canvas(6.5,4.25)
    text(ax,.12,4.14,'Evidence-bound editing: trace the claim, constrain the patch, retain the evidence',10.5,'title')
    # One shared document workspace and one nested verification workspace.
    box(ax,.10,1.03,6.29,2.86,'lavender',.085,r=.08)
    box(ax,3.88,1.10,2.43,2.70,'sage',.12,r=.07)
    text(ax,.24,3.78,'DOCUMENT TRACKS',7.0,'flow')
    text(ax,4.04,3.68,'VERIFICATION + ADMISSION',7.0,'flow')
    for y,col,name in [(3.05,'sky','Supplied sources'),(2.25,'lavender','Original section'),(1.45,'lavender','Candidate section')]:
        page(ax,.25,y,2.78,.57,col,0)
        text(ax,.36,y+.48,name,7.3,'title')
    text(ax,.36,3.35,'[S1] No field measurements collected.',7.15)
    text(ax,.36,3.17,'[S2] The study will not estimate annual retreat rates.',7.05)
    text(ax,.36,2.55,'Its contribution',7.5)
    box(ax,1.14,2.36,.40,.22,'lavender',.50,r=.015,z=8)
    text(ax,1.19,2.55,'would',7.5,'bold')
    text(ax,1.60,2.55,'be a more explicit account …',7.5)
    text(ax,.36,1.75,'Its contribution',7.5)
    box(ax,1.14,1.56,.40,.22,'apricot',.62,r=.015,z=8)
    text(ax,1.22,1.75,'will',7.5,'bold')
    text(ax,1.60,1.75,'be a more explicit account …',7.5)
    # The shared term position makes semantic drift visible before any aggregate score.
    line(ax,(1.34,2.33),(1.34,2.05),'lavender',1.0)
    arrow(ax,(1.34,2.05),(1.34,1.99),'apricot',head=5)
    text(ax,.33,2.12,'one token, changed commitment',7.0,'italic')
    agent(ax,3.26,2.35,'lavender',1.18)
    text(ax,3.44,2.99,'Qwen / API\n6 rules',7.3,'title',ha='center')
    arrow(ax,(3.04,2.52),(3.25,2.52),'lavender')
    arrow(ax,(3.48,2.29),(3.04,1.72),'lavender',rad=-.30)
    arrow(ax,(3.03,3.25),(3.25,2.77),'sky',rad=.08)
    text(ax,.29,1.31,'Actor → verb   •   supplied detail   •   order / focus   •   preserve “may”',7.0,'italic')
    # Three aligned inputs bind review to evidence and exact original/candidate spans.
    agent(ax,4.12,2.96,'sage',1.10)
    ax.add_patch(patches.Circle((4.57,3.26),.115,facecolor='white',edgecolor=C['sage'],lw=.8,zorder=8))
    line(ax,(4.50,3.16),(4.43,3.08),'sage',1.2,z=8)
    arrow(ax,(3.05,3.42),(4.11,3.36),'sky',rad=-.05,lw=.7)
    arrow(ax,(3.05,2.69),(4.11,3.18),'lavender',rad=-.22,lw=.7)
    arrow(ax,(3.05,1.88),(4.10,3.03),'apricot',rad=.45,lw=.7)
    text(ax,4.77,3.48,'Quoted finding',8.1,'title')
    text(ax,4.77,3.25,'would → will\nConditional → definite',7.1)
    # Patch window is a magnified local text operation, not another pipeline box.
    text(ax,4.12,2.84,'Proposed patch · issue 2',7.2,'title')
    text(ax,5.42,2.84,'≤3 · ≤35%',7.0)
    page(ax,4.11,1.97,2.02,.68,'apricot',0)
    text(ax,4.22,2.54,'before',7.0,'italic');text(ax,4.79,2.54,'“contribution will be”',7.2,'bold')
    line(ax,(4.21,2.32),(6.01,2.32),'apricot',.7)
    text(ax,4.22,2.23,'after',7.0,'italic');text(ax,4.79,2.23,'“contribution would be”',7.2,'bold')
    line(ax,(4.08,2.96),(4.02,2.96),'apricot',.8)
    line(ax,(4.02,2.96),(4.02,2.54),'apricot',.8)
    arrow(ax,(4.02,2.54),(4.11,2.54),'apricot',head=4)
    text(ax,4.13,1.86,'Unique anchors',7.0)
    # Two distinct admission decisions; the fallback is a continuous return lane.
    for x,t in [(3.70,'section'),(4.64,'whole')]:
        ax.add_patch(patches.Polygon([(x-.32,1.53),(x,1.76),(x+.32,1.53),(x,1.30)],facecolor=mix('sage',.44),edgecolor=C['sage'],lw=.65,zorder=6))
        text(ax,x,1.53,t,7.2,'bold',ha='center',va='center')
    arrow(ax,(3.04,1.73),(3.36,1.58),'sage',head=5)
    arrow(ax,(4.03,1.53),(4.31,1.53),'sage',head=5)
    arrow(ax,(5.13,1.96),(4.85,1.76),'apricot',head=5)
    text(ax,3.70,1.21,'quote / citation',7.0,'italic',ha='center')
    text(ax,4.64,1.21,'audit / guards',7.0,'italic',ha='center')
    page(ax,5.49,1.17,.56,.46,'sage',3)
    text(ax,5.76,1.77,'Retained',7.6,'title',ha='center')
    arrow(ax,(4.97,1.53),(5.46,1.53),'sage',head=5)
    line(ax,(.24,2.38),(.17,2.38),'lavender',.7)
    line(ax,(.17,2.38),(.17,1.10),'lavender',.7,ls='--')
    line(ax,(.17,1.10),(5.30,1.10),'lavender',.7,ls='--')
    arrow(ax,(5.30,1.10),(5.49,1.26),'lavender',ls='--',head=5)
    box(ax,.40,1.02,2.58,.18,'white',0,r=0,z=7)
    text(ax,.47,1.17,'If a gate fails: retain the original text',7.1,'italic')
    # A narrow, continuous ledger slot records the evidence and decisions together.
    line(ax,(.14,.82),(6.35,.82),'lavender',1.0)
    text(ax,.16,.70,'CURRENT-RUN LEDGER',7.1,'flow')
    fields=[(.16,'Original / candidate','text + source IDs'),(1.58,'Review','quoted issues'),(2.75,'Repair','anchors + issueIndex'),(4.13,'Decision','retained + status'),(5.38,'Integrity','text hashes')]
    for x,h,b in fields:
        text(ax,x,.47,h,7.4,'title');text(ax,x,.27,b,7.1)
    arrow(ax,(5.77,1.13),(5.77,.91),'sky',head=5)
    text(ax,4.32,.96,'GPTZero after retention only',7.1,'flow')
    arrow(ax,(6.06,1.30),(6.26,.80),'lavender',rad=-.10,head=5)
    text(ax,6.32,1.15,'record',7.0,'italic',ha='right')
    text(ax,.16,.09,'No historical-card retrieval or training; detector outputs do not enter admission.',7.1,'italic')
    save(fig,out/'architecture')


def decision_trace(out,evaluation):
    root=evaluation/'runs/C01/rules'
    data=json.loads((root/'revision_ledger.json').read_text(encoding='utf-8'))
    last=data['edits'][-1]
    assert last['repair']=={'ok':False,'reason':'patch_type'}
    assert sum(e['status']=='verified_edit' for e in data['edits'])==5
    raw=json.loads((root/'repair_section_findings.response.json').read_text(encoding='utf-8'))
    pp=json.loads(raw['text'])['sections'][0]['patches']
    assert len(pp)==3 and pp[1]['after']==''
    fig,ax=canvas(6.5,4.08)
    text(ax,.13,3.97,'C01: the repair contract rejects a meaning-changing revision',10.8,'title')
    text(ax,.14,3.72,'Recorded Limitations section  •  Conditional scientific claims must survive stylistic editing',7.3,'italic')
    # Shared evidence grid makes the semantic edits directly comparable.
    box(ax,.13,2.15,6.24,1.40,'sky',.12)
    text(ax,.24,3.43,'Original claim',8.3,'title');text(ax,2.52,3.43,'Candidate wording',8.3,'title');text(ax,4.86,3.43,'Reviewer finding',8.3,'title')
    line(ax,(.23,3.26),(6.25,3.26),'sky',.7)
    ys=[3.12,2.79,2.46]
    left=['“while leaving a less complete map”','“may also contain outdated boundaries”','“its contribution would be …”']
    middle=['“but it will leave a less complete map”','“…, as no field measurements … [S1]”','“its contribution will be …”']
    right=['Possible → definite tradeoff','Adds unsupported causality','Conditional → definite outcome']
    for i,(y,a,b,c) in enumerate(zip(ys,left,middle,right)):
        text(ax,.24,y,a,7.1);box(ax,2.43,y-.21,2.31,.27,'apricot',.23,r=.02)
        text(ax,2.52,y,b,7.1,'bold');text(ax,4.86,y,c,7.1)
        if i<2:line(ax,(.24,y-.25),(6.23,y-.25),'white',.9)
    arrow(ax,(3.51,2.13),(3.51,1.96),'apricot')
    # Three concrete patches are a single atomic proposed update.
    box(ax,.13,.73,4.31,1.20,'apricot',.13)
    text(ax,.25,1.82,'One proposed patch set; three issue-linked replacements',8.7,'title')
    text(ax,.25,1.59,'issue',7.2,'bold');text(ax,.72,1.59,'before → after',7.2,'bold')
    patchlines=[('0','“, but it will leave” → “ while leaving”'),('1','“, as no field measurements … [S1]” → empty'),('2','“its contribution will be” → “its contribution would be”')]
    for y,(i,t) in zip([1.36,1.13,.90],patchlines):
        if i=='1':box(ax,.23,y-.18,4.08,.22,'rose',.18,r=.015)
        text(ax,.28,y,i,7.3,'bold');text(ax,.73,y,t,7.1)
    arrow(ax,(4.46,1.32),(4.63,1.32),'rose')
    text(ax,4.75,1.79,'Atomic rejection',8.6,'title')
    text(ax,4.75,1.53,'reason = patch_type\nEmpty replacement invalidates\nthe whole patch set.',7.15)
    tag(ax,4.73,.83,1.51,'original section kept','lavender',7.0)
    # Six section decisions stay in one manuscript, showing failure and retained progress.
    text(ax,.15,.55,'Final manuscript',7.8,'title')
    names=['Abstract','Introduction','Related work','Method','Evaluation','Limitations']
    for i,name in enumerate(names):
        x=1.30+i*.84;col='sage' if i<5 else 'lavender'
        box(ax,x,.31,.79,.24,col,.36,r=.025)
        text(ax,x+.395,.43,name,7.0,'bold',ha='center',va='center')
    text(ax,.15,.17,'Ledger: 5 verified edits + 1 original fallback; rejected candidate, exact findings and patch failure remain recorded.',7.1,'italic')
    save(fig,out/'extra/revision_decision_trace')


def operations(out):
    fig,ax=canvas(6.5,3.84)
    text(ax,.13,3.73,'Six editorial operations with explicit preservation boundaries',10.8,'title')
    text(ax,.14,3.49,'Six rules supplied together to the section writer; examples below are illustrative, not measured outputs.',7.2,'italic')
    xs=[.23,1.37,3.05,4.75]
    box(ax,.13,3.13,6.24,.25,'lavender',.34,r=.03)
    for x,t in zip(xs,['Operation','Before','Constrained rewrite','What must survive']):text(ax,x,3.31,t,7.7,'bold')
    rows=[
      ('Actor + verb','“We perform an analysis\nof the samples.”','“We analyse the samples.”','The actor and action'),
      ('Concrete detail','“We use the method.”','“We use the boundary check.”','Only already-supplied detail'),
      ('Remove redundancy','“in order to assess”','“to assess”','Every substantive qualifier'),
      ('Information order','“It fails under cloud cover.\nThis model uses optical images.”','“The optical-image model\nfails under cloud cover.”','Existing logical relations'),
      ('Sentence focus','One sentence carries\nmethod + limitation.','Separate the two claims;\nkeep their dependency.','Method steps and citations'),
      ('Calibrated claim','“The method may improve\nthe proposed comparison.”','Use clear prose while\nretaining “may”.','Uncertainty and study status')]
    for i,row in enumerate(rows):
        top=3.03-i*.38
        if i%2==0:box(ax,.13,top-.29,6.24,.35,'lavender',.10,r=.02)
        for j,(x,t) in enumerate(zip(xs,row)):
            text(ax,x,top,t,7.2,'bold' if j==0 else 'body')
        arrow(ax,(2.88,top-.10),(3.01,top-.10),'lavender',head=4)
    # One shared boundary joins all rules to the admission policy.
    line(ax,(.23,.65),(6.24,.65),'lavender',.8)
    tag(ax,.23,.27,1.00,'candidate','lavender',7.2)
    arrow(ax,(1.25,.37),(1.44,.37),'sage')
    text(ax,1.55,.52,'Review against original + sources',8,'title')
    text(ax,1.55,.32,'Meaning • citation occurrences • quantities • limitations',7.1)
    arrow(ax,(4.31,.37),(4.49,.37),'sage')
    text(ax,4.63,.52,'Retain only after checks',8,'title')
    text(ax,4.63,.32,'Rules propose; verification decides.',7.1,'italic')
    save(fig,out/'extra/six_editorial_operations')


def evaluation_design(out,evaluation):
    index=json.loads((evaluation/'input_index.json').read_text(encoding='utf-8'))
    inputs=[json.loads((evaluation/'inputs'/(r['caseId']+'.json')).read_text(encoding='utf-8')) for r in index]
    assert len(inputs)==12 and sum(len(v['knownFacts']) for v in inputs)==72
    fig,ax=canvas(6.5,3.67)
    text(ax,.12,3.56,'A frozen paired design: instructions vary; evidence and writer settings do not',10.3,'title')
    text(ax,.16,3.27,'12 inputs × 6 sections',8.0,'title')
    # The complete input lattice shows what is repeated, rather than a generic dataset box.
    for j in range(6):text(ax,.68+j*.145,3.02,str(j+1),7.0,ha='center')
    for i in range(12):
        y=2.81-i*.117
        text(ax,.19,y+.055,f'C{i+1:02}',7.0,va='center')
        for j in range(6):box(ax,.61+j*.145,y,.12,.09,'sky',.42 if i%2==0 else .25,r=.008)
    text(ax,.20,1.34,'2 source excerpts / case',7.1,'bold')
    page(ax,.26,.79,.42,.40,'sky',0);page(ax,.80,.79,.42,.40,'sky',0)
    text(ax,.47,1.04,'S1',7.0,'bold',ha='center');text(ax,1.01,1.04,'S2',7.0,'bold',ha='center')
    text(ax,.20,.61,'72 known reference facts',7.1,'italic')
    # Two explicit instruction streams enter one shared verification contract.
    box(ax,1.70,.73,3.01,2.59,'lavender',.09,r=.055)
    text(ax,1.85,3.19,'Qwen2.5 7B · fixed seeds + context',8.1,'title')
    for yy,col,label,desc in [(2.52,'sky','Generic','ordinary copy-edit'),(1.42,'lavender','Rules','six explicit operations')]:
        agent(ax,1.88,yy-.10,col,.85)
        text(ax,2.28,yy+.18,label,8.2,'title')
        text(ax,2.28,yy-.04,desc,7.0)
        for n in range(6):box(ax,2.28+n*.12,yy-.28,.09,.07,col,.65,r=.008)
        text(ax,2.28,yy-.40,'6 writer calls',7.0,'italic')
        arrow(ax,(1.47,yy+.05),(1.83,yy+.05),'sky',head=5)
        arrow(ax,(3.08,yy+.05),(3.30,yy+.05),col,head=5)
    box(ax,3.32,1.15,.68,1.78,'sage',.25,r=.22)
    text(ax,3.66,2.73,'Shared',7.8,'title',ha='center')
    text(ax,3.66,2.38,'Review\n↓\nRepair\n↓\nRetain',7.6,'bold',ha='center')
    text(ax,3.66,1.41,'same\npolicy',7.0,'italic',ha='center')
    for yy,col in [(2.43,'sky'),(1.41,'lavender')]:
        page(ax,4.22,yy-.17,.32,.47,col,3)
        arrow(ax,(4.01,yy+.07),(4.19,yy+.07),'sage',head=5)
    text(ax,4.39,2.97,'Retained',7.5,'title',ha='center')
    text(ax,1.87,.84,'≤3 patches · ≤35% matched characters',7.0)
    # Both retained texts feed all assessments, never the reverse.
    line(ax,(4.58,2.50),(4.78,2.50),'lavender',.7)
    line(ax,(4.58,1.48),(4.78,1.48),'lavender',.7)
    line(ax,(4.78,.95),(4.78,2.98),'lavender',.7)
    text(ax,4.97,3.27,'Post-selection observations',7.9,'title')
    arrow(ax,(4.78,2.94),(4.97,2.94),'lavender',head=5)
    text(ax,5.03,3.03,'Naturalness · LLM proxy',7.6,'title')
    for xx,yy,t,col in [(5.04,2.60,'A','sky'),(5.35,2.60,'B','lavender'),(5.04,2.34,'B','lavender'),(5.35,2.34,'A','sky')]:tag(ax,xx,yy,.23,t,col,7)
    text(ax,5.75,2.77,'12 pairs\n2 orders',7.15)
    text(ax,5.03,2.21,'Disagreement → inconclusive',7.0,'italic')
    arrow(ax,(4.78,1.87),(4.97,1.87),'sage',head=5)
    text(ax,5.03,1.97,'Content preservation',7.6,'title')
    text(ax,5.03,1.74,'72 reference facts per arm\nSeparate semantic challenges',7.0)
    arrow(ax,(4.78,1.08),(4.97,1.08),'sky',head=5)
    text(ax,5.03,1.19,'GPTZero · independent',7.6,'title')
    line(ax,(5.04,.88),(6.19,.88),'sky',1.8)
    text(ax,5.04,.81,'0%',7.0);text(ax,6.19,.81,'100%',7.0,ha='right')
    text(ax,5.03,.58,'12 originals + 24 retained texts',7.0)
    line(ax,(.15,.42),(6.35,.42),'gray',.7)
    text(ax,.16,.31,'Frozen controlled fixtures, not an external corpus. Writer calls match; adaptive repair cost can differ.',7.1,'italic')
    text(ax,.16,.13,'Current-run ledger only. Detector and preference results never feed back to retained-text selection.',7.1,'bold')
    save(fig,out/'extra/evaluation_design')


def deployment_routes(out):
    fig,ax=canvas(6.5,3.65)
    text(ax,.12,3.54,'Separate execution profiles, one evidence-preserving editing contract',10.5,'title')
    text(ax,.15,3.29,'Profile / access',7.8,'title');text(ax,1.98,3.29,'Draft',7.8,'title');text(ax,3.13,3.29,'Section writer',7.8,'title');text(ax,4.61,3.29,'Audit + repair',7.8,'title')
    # Each role is a token on one execution lane; colours encode where compute occurs.
    lanes=[(2.70,'sky','Browser API','Own API credit; browser CORS',
            'Visitor API','Visitor API','Visitor API','Same provider; optional separate writer ID.'),
           (1.83,'sage','Desktop Ollama','Local model ≈4.7 GB',
            'Hosted / import','Qwen2.5 7B','Hosted review','Local Q4_K_M writer; API or native Codex review.'),
           (.96,'lavender','Archived Mac MLX','Separate reproduction profile',
            'Fixed input','Qwen2.5 7B','Pinned review','MLX 4-bit on Apple Silicon; four-case pilot.')]
    for y,col,name,access,draft,writer,review,note in lanes:
        box(ax,.13,y-.49,6.23,.73,col,.085,r=.04)
        text(ax,.24,y+.10,name,8.0,'title');text(ax,.24,y-.14,access,7.0)
        for x,w,label,c in [(1.85,1.07,draft,col),(3.10,1.18,writer,col),(4.47,1.17,review,'sky' if col=='sage' else col)]:
            box(ax,x,y-.10,w,.26,c,.40,r=.07)
            text(ax,x+w/2,y+.03,label,7.2,'bold',ha='center',va='center')
        arrow(ax,(2.94,y+.03),(3.08,y+.03),col,head=5)
        arrow(ax,(4.30,y+.03),(4.45,y+.03),col,head=5)
        arrow(ax,(5.67,y+.03),(5.86,y+.03),col,head=5)
        page(ax,5.89,y-.22,.30,.43,col,2)
        text(ax,1.85,y-.29,note,7.0,'italic')
    line(ax,(.16,.38),(6.35,.38),'gray',.7)
    text(ax,.17,.27,'All routes:',7.3,'title');text(ax,.85,.27,'retained text + checks + ledger + hashes; optional GPTZero scan after retention.',7.15)
    text(ax,.17,.10,'Model / runtime changes define a new run: a browser or Windows output does not inherit the archived Mac result.',7.1,'italic')
    save(fig,out/'extra/deployment_routes')


def main():
    p=argparse.ArgumentParser();p.add_argument('--evaluation',type=Path,default=ROOT.parent/'evaluation');p.add_argument('--output-dir',type=Path,default=ROOT/'assets');p.add_argument('--architecture-only',action='store_true')
    a=p.parse_args();architecture(a.output_dir)
    if not a.architecture_only:
        decision_trace(a.output_dir,a.evaluation);operations(a.output_dir)
        evaluation_design(a.output_dir,a.evaluation);deployment_routes(a.output_dir)
    names=['architecture'] if a.architecture_only else ['architecture','extra/revision_decision_trace','extra/six_editorial_operations','extra/evaluation_design','extra/deployment_routes']
    provenance={'generator':'draw_mechanisms.py','style':'style.py','width_inches':6.5,'brand_assets_used':False,
      'illustrative_examples':['architecture local span illustration','six_editorial_operations'],
      'recorded_trace':'evaluation/runs/C01/rules/revision_ledger.json',
      'figures':{name:{ext:hashlib.sha256((a.output_dir/(name+'.'+ext)).read_bytes()).hexdigest() for ext in ['pdf','svg','png']} for name in names}}
    (a.output_dir/'mechanism_asset_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
    print('Rendered publication-scale mechanism figures.')

if __name__=='__main__':main()
