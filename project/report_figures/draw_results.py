from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir())/"proseledger-mpl"))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import patches
from matplotlib.colors import LinearSegmentedColormap, ListedColormap, BoundaryNorm
from matplotlib.lines import Line2D
from matplotlib.offsetbox import AnnotationBbox, DrawingArea
from matplotlib.text import Text
from style import C, F, mix, save
from draw_paired_figures import load_complete, CASE_LABELS

HERE = Path(__file__).resolve().parent
ARMS = ("generic", "rules")
ARM_COLORS = {"generic": C["sky"], "rules": C["lavender"]}
PATHS = ("direct", "repair", "original")
PATH_COLORS = [C["sky"], C["lavender"], C["apricot"]]
SECTION_NAMES = ["Abs.", "Intro.", "Related", "Method", "Eval.", "Limits"]
plt.rcParams.update({"font.family": F["body"].get_name(), "font.size": 7.5,
    "text.color": C["ink"], "axes.labelcolor": C["ink"], "xtick.color": C["ink"],
    "ytick.color": C["ink"], "axes.edgecolor": C["gray"], "axes.linewidth": .65,
    "xtick.major.width": .6, "ytick.major.width": .6, "xtick.major.size": 2,
    "ytick.major.size": 2, "axes.spines.top": False, "axes.spines.right": False,
    "pdf.fonttype": 42, "svg.fonttype": "none"})


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text(ax, x, y, label, size=7.5, style="body", ha="left", va="center", **kw):
    return ax.text(x, y, label, fontsize=size, fontproperties=F[style], ha=ha, va=va,
                   color=C["ink"], parse_math=False, **kw)


def panel(ax, label, title):
    ax.set_title(f"({label})  {title}", loc="left", fontsize=10.1,
                 fontproperties=F["title"], color=C["ink"], pad=7)


def style_axes(ax, grid=None):
    ax.set_facecolor("white")
    for lab in ax.get_xticklabels()+ax.get_yticklabels():
        lab.set_fontproperties(F["body"])
        lab.set_fontsize(7)
    for lab in (ax.xaxis.label, ax.yaxis.label):
        lab.set_fontproperties(F["bold"])
        lab.set_fontsize(7.5)
    if grid:
        ax.grid(axis=grid, color=mix("lavender", .28), linewidth=.5)
        ax.set_axisbelow(True)


def legend(ax, items, **kwargs):
    handles = [Line2D([], [], color=color, marker=marker, markersize=4.5,
                      linestyle=line, linewidth=1.1, label=label)
               for label, color, marker, line in items]
    return ax.legend(handles=handles, frameon=False, prop=F["body"],
                     fontsize=7, handlelength=1.4, handletextpad=.4, borderaxespad=0,
                     labelspacing=.35, **kwargs)


def note(fig, value, y=.025):
    fig.text(.05, y, value, fontproperties=F["italic"], fontsize=6.8, color=C["ink"])


def neutral(ax):
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)


def load_pilot():
    audit = HERE.parent/"evidence_audit/archived_cohorts.json"
    if audit.exists():
        return read(audit)["heldout_summary.json"]["data"], audit
    path = HERE.parent/"research/qwen_mlx/archive/heldout_summary.json"
    return read(path), path


def pilot_figure(pilot, out):
    rows = pilot["rows"]
    control = np.array([r["targeted"]["ai"]*100 for r in rows])
    retained = np.array([r["new"]["ai"]*100 for r in rows])
    assert len(rows) == 4 and np.all(control == 100)
    assert np.isclose(retained.mean(), 90.85579844067697)
    assert Counter(r["outcome"] for r in rows) == {"tie": 3, "win": 1}
    fig = plt.figure(figsize=(6.5, 3.05))
    gs = fig.add_gridspec(1, 2, left=.245, right=.975, top=.82, bottom=.27,
                         width_ratios=[1.55, 1], wspace=.39)
    ax, ecdf = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    names = ["Evidence-linked", "Lab handover", "Citation preservation", "Negative findings"]
    for i, (a, b) in enumerate(zip(control, retained)):
        ax.plot([a, b], [i, i], color=C["lavender"], lw=3.5, solid_capstyle="round")
        ax.scatter([a], [i], s=37, facecolor="white", edgecolor=C["ink"], lw=.8, zorder=3)
        ax.scatter([b], [i], s=15, facecolor=C["lavender"], edgecolor=C["ink"], lw=.35, zorder=4)
        text(ax, b-3, i-.14, f"{b:.2f}", 7, "bold", ha="right")
    ax.set(xlim=(0, 105), ylim=(3.5, -.55), xticks=[0, 25, 50, 75, 100],
           yticks=range(4), yticklabels=names, xlabel="GPTZero AI-class probability (%)")
    ax.spines["left"].set_visible(False);ax.tick_params(axis="y", length=0, pad=6)
    panel(ax, "a", "Paired manuscript outcomes");style_axes(ax, "x")
    for values, col, ls in [(control, C["sky"], "--"), (retained, C["lavender"], "-")]:
        x = np.r_[0, np.sort(values), 100]
        y = np.r_[0, np.arange(1, 5)/4, 1]
        ecdf.step(x, y, where="post", color=col, lw=1.6, linestyle=ls)
    ecdf.scatter([100],[1],s=34,facecolor='white',edgecolor=C['sky'],lw=1.15,zorder=5)
    ecdf.scatter([100],[1],s=9,facecolor=C['lavender'],edgecolor=C['ink'],lw=.25,zorder=6)
    ecdf.set(xlim=(0, 103), ylim=(0, 1.08), xticks=[0, 50, 100],
             yticks=[0, .25, .5, .75, 1], yticklabels=["0", "¼", "½", "¾", "1"],
             xlabel="AI-class probability (%)", ylabel="Fraction of four manuscripts")
    panel(ecdf, "b", "Empirical distribution");style_axes(ecdf, "y")
    legend(ecdf, [("Targeted", C["sky"], "", "--"), ("Qwen + review", C["lavender"], "", "-")], loc="upper left", bbox_to_anchor=(0,.93))
    fig.text(.05,.95,"Mac MLX pilot",fontproperties=F["title"],fontsize=10.5,color=C["ink"])
    fig.text(.05,.135,"Mean  100.00 → 90.86%",fontproperties=F["bold"],fontsize=8.3)
    fig.text(.49,.135,"1 lower  ·  3 unchanged  ·  0 higher",fontproperties=F["flow"],fontsize=7.6)
    note(fig,"All four retained texts remain AI-classified; this compares complete configurations with different writers.")
    save(fig,out/"pilot_results")


def human_figure(human, out):
    source, fluency = human["source_summary"], human["fluency_summary"]
    assert [source["correct"],source["incorrect"],source["cannot_tell"]] == [4,5,1]
    assert [fluency["revised_preferred"],fluency["original_preferred"],fluency["cannot_tell"]] == [4,5,1]
    selection = np.zeros((2,3),dtype=int)
    for row in human["rows"]:
        selection[["A","B"].index(row["source_published_side"]),
                  ["A","B","Cannot tell"].index(row["source_choice"])] += 1
    assert selection.tolist() == [[2,3,0],[2,2,1]]
    fig = plt.figure(figsize=(6.5,2.95))
    gs=fig.add_gridspec(1,2,left=.13,right=.975,bottom=.33,top=.80,width_ratios=[1.15,1],wspace=.47)
    ax,b=fig.add_subplot(gs[0]),fig.add_subplot(gs[1])
    colors=[C["lavender"],C["sky"],C["apricot"]]
    for i in range(2):
        left=0
        for j in range(3):
            n=selection[i,j]
            ax.barh(i,n,left=left,height=.42,color=colors[j],edgecolor="white",linewidth=1)
            if n: text(ax,left+n/2,i,str(n),8.8,"bold",ha="center")
            left += n
    ax.set(xlim=(0,5.15),ylim=(1.55,-.60),yticks=[0,1],yticklabels=["Published = A","Published = B"],
           xticks=[0,1,2,3,4,5],xlabel="Submitted source judgments")
    ax.tick_params(axis="y",length=0);ax.spines["left"].set_visible(False)
    panel(ax,"a","Source selection by reference side");style_axes(ax,"x")
    for i,(lab,col) in enumerate(zip(["Selected A","Selected B","Cannot tell"],colors)):
        ax.plot([],[],lw=5,color=col,label=lab)
    ax.legend(loc="upper left",bbox_to_anchor=(0,-.30),ncol=3,frameon=False,fontsize=6.8,
              handlelength=.65,handletextpad=.4,columnspacing=.8)
    vals=[4,5,1];labels=["Revision","Initial","Cannot tell"]
    b.barh(np.arange(3),vals,color=[C["lavender"],C["sky"],C["apricot"]],height=.45)
    for i,v in enumerate(vals):text(b,v+.13,i,f"{v}/10",8,"bold")
    b.set(xlim=(0,6),ylim=(2.6,-.6),yticks=range(3),yticklabels=labels,xticks=range(0,7,2),xlabel="Submitted fluency judgments")
    b.tick_params(axis="y",length=0);b.spines["left"].set_visible(False)
    panel(b,"b","Original–revision preference");style_axes(b,"x")
    fig.text(.05,.94,"Human evaluation",fontproperties=F["title"],fontsize=10.5)
    fig.text(.16,.105,"4/10 source choices correct",fontproperties=F["bold"],fontsize=8)
    fig.text(.62,.105,"4/10 prefer revision",fontproperties=F["bold"],fontsize=8)
    note(fig,"Counts are submitted judgments; shared response codes do not identify ten independent raters per task.")
    save(fig,out/"human_results")


def verifier_figure(evaluation,out):
    data=read(evaluation/"semantic_challenge_metrics.json")
    assert data["completed"]==data["scheduled"]==24
    names=[("deterministic","Lexical"),("semantic","Semantic"),("combined","Both must pass")]
    assert [(data['metrics'][k]['TP'],data['metrics'][k]['FN'],data['metrics'][k]['TN'],data['metrics'][k]['FP'])
            for k,_ in names]==[(2,10,11,1),(12,0,12,0),(12,0,11,1)]
    fig=plt.figure(figsize=(6.5,3.55))
    gs=fig.add_gridspec(2,3,left=.10,right=.975,top=.84,bottom=.19,height_ratios=[1.07,.86],hspace=.82,wspace=.48)
    for i,(key,title) in enumerate(names):
        ax=fig.add_subplot(gs[0,i]);m=data["metrics"][key]
        matrix=np.array([[m["TP"],m["FN"]],[m["FP"],m["TN"]]])
        for row in range(2):
            for col in range(2):
                v=int(matrix[row,col]);side=.80*np.sqrt(v/12)
                color=C["lavender"] if row==col else C["apricot"]
                ax.add_patch(patches.Rectangle((col-.44,row-.44),.88,.88,facecolor=mix("lavender",.10),edgecolor="none"))
                if v:ax.add_patch(patches.Rectangle((col-side/2,row-side/2),side,side,facecolor=color,edgecolor="white",lw=.7))
                text(ax,col,row,str(v),8.7,"bold",ha="center")
        ax.set(xlim=(-.6,1.6),ylim=(1.6,-.6),aspect="equal",xticks=[0,1],xticklabels=["Reject","Allow"],
               yticks=[0,1],yticklabels=["Invalid","Valid"] if i==0 else ["",""])
        ax.xaxis.tick_top();neutral(ax);style_axes(ax)
        panel(ax,chr(ord('a')+i),"Combined" if key=='combined' else title)
        ax.text(.5,-.15,f"{m['TP']+m['TN']}/24 correct",transform=ax.transAxes,
                fontproperties=F['bold'],fontsize=7.4,ha='center')
    perf=fig.add_subplot(gs[1,:])
    for metric,label,col,marker in [("sensitivity","Violations detected",C["lavender"],"o"),
        ("specificity","Valid edits allowed",C["sky"],"s"),("accuracy","Correct decisions",C["sage"],"D")]:
        values=[100*data['metrics'][k][metric]['proportion'] for k,_ in names]
        perf.plot(range(3),values,color=col,lw=1.3,marker=marker,markersize=4,label=label)
    perf.set(xlim=(-.1,2.1),ylim=(0,108),xticks=range(3),xticklabels=[x[1] for x in names],yticks=[0,50,100],ylabel="Rate (%)")
    panel(perf,"d","Matched component outcomes");style_axes(perf,"y")
    perf.legend(loc="lower center",bbox_to_anchor=(.60,.03),ncol=3,frameon=False,fontsize=6.6,
                handlelength=1.1,columnspacing=.8,handletextpad=.3)
    fig.text(.05,.96,"Known-answer preservation checks",fontproperties=F["title"],fontsize=10.5)
    note(fig,"Square area encodes count; 12 invalid + 12 valid edits. Lines connect checker configurations, not time.")
    save(fig,out/"verifier_results")


def detector_figure(data,out):
    vals={(r['caseId'],r['condition']):r['probability']*100 for r in data['detector']}
    matrix=np.array([[vals[c,a] for a in ['original','generic','rules']] for c in data['caseIds']])
    assert matrix.shape==(12,3) and np.all(matrix==100)
    fig=plt.figure(figsize=(6.5,3.65))
    gs=fig.add_gridspec(1,2,left=.24,right=.96,bottom=.26,top=.83,width_ratios=[1.4,1],wspace=.48)
    ax,delta=fig.add_subplot(gs[0]),fig.add_subplot(gs[1])
    cmap=LinearSegmentedColormap.from_list('probability',[mix('lavender',.06),C['lavender']])
    im=ax.imshow(matrix,vmin=0,vmax=100,cmap=cmap,aspect='auto')
    for i in range(12):
        for j in range(3):text(ax,j,i,"100",7.1,"bold",ha='center')
    ax.set(xticks=range(3),xticklabels=['Original','Generic','Rules'],yticks=range(12),
           yticklabels=[f"{c}  {CASE_LABELS[i]}" for i,c in enumerate(data['caseIds'])])
    ax.xaxis.tick_top();neutral(ax);style_axes(ax)
    ax.set_xticks(np.arange(-.5,3,1),minor=True);ax.set_yticks(np.arange(-.5,12,1),minor=True)
    ax.grid(which='minor',color='white',linewidth=1.8);ax.tick_params(which='minor',length=0)
    panel(ax,'a','AI-class probabilities (%)')
    differences=matrix[:,2]-matrix[:,1]
    delta.axvline(0,color=C['gray'],lw=.8)
    delta.scatter(differences,np.arange(12),s=17,color=C['sky'],edgecolor=C['ink'],lw=.35,zorder=4)
    delta.set(xlim=(-100,100),ylim=(11.5,-.5),yticks=range(12),yticklabels=data['caseIds'],
              xticks=[-100,0,100],xlabel='Rules − Generic (pp)')
    neutral(delta);delta.spines['bottom'].set_visible(True);style_axes(delta,'x')
    panel(delta,'b','Paired detector difference')
    cax=fig.add_axes([.245,.103,.26,.022]);cb=fig.colorbar(im,cax=cax,orientation='horizontal',ticks=[0,50,100])
    cb.outline.set_visible(False);cb.ax.tick_params(labelsize=6.5,length=2,pad=1)
    fig.text(.62,.108,'0 lower · 12 equal · 0 higher',fontproperties=F['bold'],fontsize=7.8)
    fig.text(.05,.96,'Controlled Ollama condition',fontproperties=F['title'],fontsize=10.5)
    note(fig,'36 text mappings / 35 unique scans; GPTZero 2026-11-04-base, observed after retention.')
    save(fig,out/'paired_gptzero_probabilities')


def preference_figure(data,out):
    rows=data['comparisons'];names=['generic','tie','rules'];colors=[C['sky'],C['sage'],C['lavender'],C['apricot']]
    ids={k:i for i,k in enumerate(names+['inconclusive'])}
    matrix=np.array([[ids[r[k]] for k in ['firstOrder','reversedOrder','concordantOutcome']] for r in rows])
    transitions=np.zeros((3,3),dtype=int)
    for r in rows:transitions[names.index(r['firstOrder']),names.index(r['reversedOrder'])]+=1
    assert transitions.sum()==12 and np.trace(transitions)==9
    fig=plt.figure(figsize=(6.5,3.6))
    gs=fig.add_gridspec(1,2,left=.125,right=.97,top=.82,bottom=.20,width_ratios=[1.15,1],wspace=.46)
    ax,b=fig.add_subplot(gs[0]),fig.add_subplot(gs[1]);cmap=ListedColormap(colors)
    ax.imshow(matrix,cmap=cmap,norm=BoundaryNorm(np.arange(-.5,4.5),4),aspect='auto',alpha=.65)
    short=['G','Tie','R','?']
    for i in range(12):
        for j in range(3):text(ax,j,i,short[matrix[i,j]],7.5,'bold',ha='center')
    ax.set(xticks=range(3),xticklabels=['First','Reversed','Concordant'],yticks=range(12),yticklabels=data['caseIds'])
    ax.xaxis.tick_top();neutral(ax);style_axes(ax)
    ax.set_xticks(np.arange(-.5,3,1),minor=True);ax.set_yticks(np.arange(-.5,12,1),minor=True)
    ax.grid(which='minor',color='white',lw=1.8);ax.tick_params(which='minor',length=0)
    panel(ax,'a','Case-level preference')
    for i in range(3):
        for j in range(3):
            v=int(transitions[i,j]);col='lavender' if i==j else 'apricot'
            b.add_patch(patches.Rectangle((j-.47,i-.47),.94,.94,facecolor=mix(col,.12+.75*v/7),edgecolor='white',lw=.8))
            text(b,j,i,str(v),11,'bold',ha='center')
    b.set(xlim=(-.5,2.5),ylim=(2.5,-.5),aspect='equal',xticks=range(3),yticks=range(3),
          xticklabels=['Generic','Tie','Rules'],yticklabels=['Generic','Tie','Rules'],
          xlabel='Reversed presentation',ylabel='First presentation')
    neutral(b);style_axes(b);panel(b,'b','Order-transition counts')
    fig.text(.05,.96,'Naturalness preference and order consistency',fontproperties=F['title'],fontsize=10.5)
    fig.text(.125,.108,'R: 7 consistent   G: 2 consistent   ?: 3 unresolved   Ties: 0 consistent',fontproperties=F['bold'],fontsize=8)
    note(fig,'G = Generic; R = Rules. Two-order automated proxy, judged by the same hosted model used for review.')
    save(fig,out/'paired_naturalness_orders')


def retention_figure(data,out):
    fig,axs=plt.subplots(1,2,figsize=(6.5,3.0),sharey=True)
    fig.subplots_adjust(left=.09,right=.97,top=.80,bottom=.25,wspace=.18)
    for i,(ax,arm) in enumerate(zip(axs,ARMS)):
        counts=np.zeros((12,3),dtype=int)
        for r in data['sectionPaths']:
            if r['condition']==arm: counts[data['caseIds'].index(r['caseId']),PATHS.index(r['finalPath'])]+=1
        assert np.all(counts.sum(axis=1)==6)
        cum=np.vstack([np.zeros(3,dtype=int),counts.cumsum(axis=0)])
        totals=[data['sectionPathCounts'][arm][p] for p in PATHS]
        assert cum[-1].tolist()==totals
        low=np.zeros(13)
        for j,col in enumerate(PATH_COLORS):
            high=low+cum[:,j]
            ax.fill_between(np.r_[np.arange(13),12.45],np.r_[low,low[-1]],np.r_[high,high[-1]],
                            step='post',color=col,alpha=.83,lw=.5,edgecolor='white')
            low=high
        ax.set(xlim=(0,12.45),ylim=(0,74),xticks=[0,3,6,9,12],xticklabels=['0','C03','C06','C09','C12'],
               yticks=[0,24,48,72],xlabel='Cases accumulated in fixed ID order')
        if i==0:ax.set_ylabel('Cumulative sections')
        panel(ax,chr(ord('a')+i),arm.title());style_axes(ax,'y')
        ax.text(.02,-.31,f"Direct {totals[0]}  ·  Repair {totals[1]}  ·  Original {totals[2]}",
                transform=ax.transAxes,fontproperties=F['bold'],fontsize=7.7)
    handles=[patches.Patch(facecolor=c,label=l) for c,l in zip(PATH_COLORS,['Direct edit','After repair','Original retained'])]
    fig.legend(handles=handles,loc='upper right',bbox_to_anchor=(.985,.985),ncol=3,frameon=False,fontsize=7,
               handlelength=.9,handletextpad=.4,columnspacing=1)
    fig.text(.05,.96,'Section retention',fontproperties=F['title'],fontsize=10.5)
    note(fig,'Step accumulation follows case ID, not time. Final wording determines whether a section remains changed.')
    save(fig,out/'paired_section_retention_paths')


def rich_data(evaluation,data):
    cost=read(evaluation/'cost_summary.json');trace=read(evaluation/'trace_summary.json')
    resources={(r['caseId'],r['condition']):r for r in cost['cases']}
    findings={(r['caseId'],r['condition']):r for r in trace['cases']}
    rows=[];hashes={}
    for cid in data['caseIds']:
        for arm in ARMS:
            path=evaluation/'runs'/cid/arm/'revision_ledger.json';ledger=read(path)
            assert len(ledger['edits'])==6
            for j,e in enumerate(ledger['edits']):
                final='original' if e['retained']==e['original'] else ('repair' if e.get('repair',{}).get('ok') is True else 'direct')
                rows.append({'caseId':cid,'condition':arm,'section':j,'finalPath':final,
                    'issues':len(e.get('review',{}).get('issues',[])),
                    'repairAccepted':e.get('repair',{}).get('ok') is True,
                    'repairRejected':e.get('repair',{}).get('ok') is False and
                       e.get('repair',{}).get('reason')!='not_needed_or_not_repairable'})
            hashes[str(path.relative_to(evaluation))]=sha(path)
    for arm in ARMS:
        sub=[r for r in rows if r['condition']==arm]
        assert sum(r['issues'] for r in sub)==trace['totals'][arm]['totalSectionReviewerFindings']
        assert sum(r['repairAccepted'] for r in sub)==trace['totals'][arm]['boundedRepairAcceptedSections']
        assert sum(r['repairRejected'] for r in sub)==trace['totals'][arm]['boundedRepairRejectedSections']
        assert Counter(r['finalPath'] for r in sub)==data['sectionPathCounts'][arm]
    for f in ['cost_summary.json','trace_summary.json']:
        hashes[f]=sha(evaluation/f)
    return resources,findings,rows,cost,trace,hashes


def efficiency_figure(evaluation,data,resources,findings,cost,out):
    fig,axs=plt.subplots(2,2,figsize=(6.5,4.45))
    fig.subplots_adjust(left=.105,right=.97,bottom=.16,top=.86,wspace=.38,hspace=.56)
    a,b,c,d=axs.flat
    for cid in data['caseIds']:
        g,r=[resources[cid,x] for x in ARMS]
        a.plot([g['inputTokens']/1000,r['inputTokens']/1000],[g['activeSeconds'],r['activeSeconds']],
               color=mix('gray',.65),lw=.65,zorder=1)
    grouped=Counter()
    for arm,marker in [('generic','o'),('rules','D')]:
        rr=[resources[c,arm] for c in data['caseIds']]
        a.scatter([r['inputTokens']/1000 for r in rr],[r['activeSeconds'] for r in rr],
                  color=ARM_COLORS[arm],marker=marker,s=18,edgecolor=C['ink'],linewidth=.3,zorder=3,label=arm.title())
        for cid in data['caseIds']:
            path=evaluation/'runs'/cid/arm
            hosted=sum(read(p).get('usage',{}).get('input_tokens',0) for p in path.glob('*.response.json')
                       if read(p).get('backend')=='hosted')
            hosted_calls=sum(read(p).get('backend')=='hosted' for p in path.glob('*.response.json'))
            local=sum(read(p).get('usage',{}).get('input_tokens',0) for p in path.glob('rewrite_section_*.response.json'))
            assert hosted>0 and local+hosted==resources[cid,arm]['inputTokens']
            assert hosted_calls==resources[cid,arm]['responseCount']-6
            rrn=findings[cid,arm]['boundedRepairAcceptedSections']
            grouped[rrn,hosted_calls,arm]+=1
    case_labels={'C01':(56.0,163),'C02':(56.0,141),'C03':(56.0,116),'C04':(32.0,114),
        'C05':(32.0,102),'C06':(56.0,175),'C07':(32.0,129),'C08':(32.0,137),
        'C09':(56.0,128),'C10':(32.0,146),'C11':(32.0,157),'C12':(56.0,152)}
    for cid,position in case_labels.items():
        g=resources[cid,'generic']
        a.annotate(cid,xy=(g['inputTokens']/1000,g['activeSeconds']),xytext=position,
            fontsize=6.5,fontproperties=F['body'],color=C['ink'],ha='center',va='center',
            arrowprops={'arrowstyle':'-','color':C['gray'],'lw':.45,'shrinkA':1,'shrinkB':2})
    for repairs,calls in sorted({(k[0],k[1]) for k in grouped}):
        counts=[grouped[repairs,calls,arm] for arm in ARMS];n=sum(counts)
        radius=3.5*np.sqrt(n);size=2*radius+2
        area=DrawingArea(size,size,0,0);angle=90
        for number,arm in zip(counts,ARMS):
            if number:
                sweep=360*number/n
                area.add_artist(patches.Wedge((size/2,size/2),radius,angle-sweep,angle,
                    facecolor=ARM_COLORS[arm],edgecolor='white',linewidth=.4))
                angle-=sweep
        area.add_artist(Text(size/2,size/2,str(n),ha='center',va='center',fontproperties=F['flow'],fontsize=6.6,color=C['ink']))
        b.add_artist(AnnotationBbox(area,(repairs,calls),frameon=False,pad=0))
    assert sum(grouped.values())==24
    a.set(xlabel='Total input tokens (thousands)',ylabel='Active call time (s)',xlim=(30,58),ylim=(95,182))
    a.legend(frameon=False,fontsize=7,loc='upper left',handletextpad=.3)
    b.set(xlabel='Sections with accepted repair',ylabel='Hosted review / repair calls',xticks=range(5),
          yticks=[2,3],xlim=(-.45,4.45),ylim=(1.67,3.33))
    panel(a,'a','Per-run resource profile');panel(b,'b','Repair workload · area = runs')
    xx=np.arange(12)
    delta_tokens=np.array([resources[cid,'rules']['inputTokens']-resources[cid,'generic']['inputTokens'] for cid in data['caseIds']])/1000
    delta_time=np.array([resources[cid,'rules']['activeSeconds']-resources[cid,'generic']['activeSeconds'] for cid in data['caseIds']])
    for ax,values,title,ylabel in [(c,delta_tokens,'Paired input-token difference','Rules − Generic (thousand tokens)'),
                                  (d,delta_time,'Paired active-time difference','Rules − Generic (s)')]:
        ax.axhline(0,color=C['ink'],lw=.65)
        colors=[C['lavender'] if v>=0 else C['sky'] for v in values]
        ax.vlines(xx,0,values,color=colors,lw=1.05,zorder=2)
        ax.scatter(xx,values,s=27,c=colors,edgecolor='white',linewidth=.5,zorder=3)
        ax.scatter(xx-.07,values+.01*np.ptp(values),s=3,color='white',alpha=.75,zorder=4)
        ax.set(xticks=xx,xticklabels=[cid[1:] for cid in data['caseIds']],xlabel='Case ID',ylabel=ylabel,xlim=(-.6,11.6))
        panel(ax,'c' if ax is c else 'd',title)
    for ax in axs.flat:style_axes(ax,'y')
    fig.text(.05,.97,'Resource use across all 24 writing runs',fontproperties=F['title'],fontsize=10.5)
    note(fig,'IDs mark Generic points; lines connect pairs. Bubble area = runs, sectors = arms. Active time excludes queue waiting.',.035)
    save(fig,out/'paired_efficiency_frontier')
    return {'perCaseDeltaInputTokens':{cid:resources[cid,'rules']['inputTokens']-resources[cid,'generic']['inputTokens'] for cid in data['caseIds']},
            'perCaseDeltaActiveSeconds':dict(zip(data['caseIds'],np.round(delta_time,2).tolist())),
            'repairWorkloadGroups':[{'acceptedRepairSections':k[0],'hostedResponseCalls':k[1],'condition':k[2],'runs':v}
                                    for k,v in sorted(grouped.items())]}


def diagnostics_figure(data,findings,section_rows,trace,out):
    fig,axs=plt.subplots(1,2,figsize=(6.5,4.15))
    fig.subplots_adjust(left=.075,right=.98,top=.82,bottom=.16,wspace=.17)
    cmap=ListedColormap(PATH_COLORS)
    for ax,arm,letter in zip(axs,ARMS,['a','b']):
        grid=np.zeros((12,6),dtype=int);issues=np.zeros((12,6),dtype=int);rejected=[]
        for r in section_rows:
            if r['condition']!=arm:continue
            i=data['caseIds'].index(r['caseId']);j=r['section'];grid[i,j]=PATHS.index(r['finalPath']);issues[i,j]=r['issues']
            if r['repairRejected']:rejected.append((i,j))
        ax.imshow(grid,cmap=cmap,norm=BoundaryNorm(np.arange(-.5,3.5),3),alpha=.55,aspect='auto',extent=(-.5,5.5,11.5,-.5))
        for i in range(12):
            for j in range(6):
                if issues[i,j]:text(ax,j,i,str(issues[i,j]),8,'bold',ha='center')
            f=findings[data['caseIds'][i],arm]
            text(ax,6.05,i,str(f['finalFullAuditIssueCount']),7.2,ha='center')
            text(ax,7.05,i,f"{f['retainedChangedSections']}/6",7.2,'bold',ha='center')
        for i,j in rejected:ax.scatter([j+.27],[i-.21],marker='x',s=10,color=C['ink'],linewidth=.7,zorder=5)
        ax.plot([5.64,5.64],[-.5,11.5],color=C['gray'],lw=.8)
        ax.set(xlim=(-.5,7.65),ylim=(11.5,-.5),xticks=list(range(6))+[6.05,7.05],
               xticklabels=SECTION_NAMES+['Audit','Kept'],yticks=range(12),yticklabels=data['caseIds'])
        ax.xaxis.tick_top();neutral(ax);style_axes(ax)
        ax.set_xticks(np.arange(-.5,6,1),minor=True);ax.set_yticks(np.arange(-.5,12,1),minor=True)
        ax.grid(which='minor',color='white',lw=1.7);ax.tick_params(which='minor',length=0)
        panel(ax,letter,f"{arm.title()}: {int(issues.sum())} section findings")
    handles=[patches.Patch(facecolor=mix(color,.55),label=name) for name,color in zip(['Direct edit','After repair','Original retained'],['sky','lavender','apricot'])]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.53,.125),ncol=3,frameon=False,fontsize=7.2,
               handlelength=1,handletextpad=.4,columnspacing=1.3)
    fig.text(.05,.965,'Section-level review, repair and retention',fontproperties=F['title'],fontsize=10.5)
    fig.text(.05,.91,'Numbers: section findings. Audit: findings on assembled candidate. Kept: changed retained sections.',
             fontproperties=F['body'],fontsize=7.2)
    note(fig,'× marks a rejected patch set. Blank cells have zero section findings; colour shows the final retained path.',.025)
    save(fig,out/'paired_case_diagnostics')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--evaluation',type=Path,default=HERE.parent/'evaluation')
    p.add_argument('--human',type=Path)
    p.add_argument('--output',type=Path,default=HERE/'assets')
    args=p.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    paired_out=out/'paired';paired_out.mkdir(exist_ok=True)
    human_path=args.human or next(x for x in [HERE.parent/'human/analysis.json',args.evaluation/'human/analysis.json'] if x.exists())
    data=load_complete(args.evaluation);pilot,pilot_path=load_pilot();human=read(human_path)
    resources,findings,sections,cost,trace,hashes=rich_data(args.evaluation,data)
    pilot_figure(pilot,out);human_figure(human,out);verifier_figure(args.evaluation,out)
    detector_figure(data,paired_out);preference_figure(data,paired_out);retention_figure(data,paired_out)
    deltas=efficiency_figure(args.evaluation,data,resources,findings,cost,paired_out)
    diagnostics_figure(data,findings,sections,trace,paired_out)
    hashes.update({'pilot_source':sha(pilot_path),'human_source':sha(human_path)})
    hashes.update(data['sourceSHA256'])
    hashes['semantic_challenge_metrics.json']=sha(args.evaluation/'semantic_challenge_metrics.json')
    manifest={'figures':8,'widthInches':6.5,'dataVerified':True,'sourceSHA256':hashes,
              'sectionPaths':data['sectionPathCounts'],'costDifferences':deltas,
              'assertions':{'pairedRuns':24,'cases':12,'sectionsPerArm':72,'detectorMappings':36,
                'allDetectorProbabilities':1.0,'pilotRetainedMean':pilot['newMean'],
                'humanCountsPerTask':[4,5,1],'semanticCorrect':24,'deterministicCorrect':13,'combinedCorrect':23},
              'newFigureCaptions':{
                'paired_efficiency_frontier':
                  'Resource use across all 24 writing runs. (a) Total input tokens versus summed active call duration; labels identify Generic endpoints and lines join paired Rules outputs. (b) Exact hosted response-call counts versus the number of sections with accepted repair. Bubble area represents the number of runs at the same coordinates, sectors represent conditions, and labels give the pooled frequency; all 24 runs are included without jitter or token binning. (c,d) Per-case Rules-minus-Generic input-token and active-time differences. Input totals include their cached subset and CLI overhead; active duration excludes scheduler waiting and is not pure hardware compute time. The display is not a Pareto-optimality or speedup claim.',
                'paired_case_diagnostics':
                  'Review and retention paths for every section in all twelve inputs and both conditions. Cell numbers count findings from the initial section review; blank cells have zero findings. Background colour records the final retained path: directly retained edit, changed text after repair, or original text. The cross marks the sole actually attempted patch set rejected by the patch contract (C01 Rules, limitations); an unnecessary repair is not a failed repair. Audit counts findings on the assembled candidate before final selection, whereas Kept counts changed sections in the retained manuscript. Thus C04 Generic has one candidate-level finding and retains zero changed sections after reverting to the original. These are recorded automated findings and controller outcomes, not independently confirmed final-text errors.'}}
    (out/'results_publication_provenance.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'figures':8,'dataVerified':True,'paths':data['sectionPathCounts']},indent=2))


if __name__=='__main__':main()
