from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir())/"proseledger-mpl"))

import numpy as np
from matplotlib import patches
from matplotlib.colors import LinearSegmentedColormap, to_rgb
from matplotlib.path import Path as MPath

from draw_paired_figures import load_complete, CASE_LABELS
from style import C, F, canvas, text, save


HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def pale(color, saturation=.20):
    value = np.array(to_rgb(C.get(color, color)))
    return tuple(1 - saturation * (1 - value))


def label(ax, x, y, value, size=16, style="body", color="ink", ha="left", va="center"):
    return text(ax, x, y, value, size=size, style=style, color=color, ha=ha, va=va)


def capsule(ax, x, y, w, h, color, saturation=.25, radius=.13):
    ax.add_patch(patches.FancyBboxPatch((x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=pale(color, saturation), edgecolor="none", zorder=0))


def heading(ax, height, title, subtitle):
    label(ax, .45, height-.47, title, 27, "title", "plum")
    label(ax, .47, height-1.00, subtitle, 15, "body")


def foot(ax, y, value, size=12.5):
    label(ax, .47, y, value, size, "italic")


def dot_legend(ax, x, y, color, value, size=14):
    ax.add_patch(patches.Circle((x, y), .055, color=C[color], linewidth=0))
    label(ax, x+.15, y, value, size)


def donut(ax, cx, cy, values, colors, radius=1.0, width=.28, center="", subtitle="", count_labels=True):
    angle = 90
    total = sum(values)
    for value, color in zip(values, colors):
        if not value:
            continue
        arc = value / total * 360
        ax.add_patch(patches.Wedge((cx, cy), radius, angle-arc, angle,
            width=width, facecolor=C[color], edgecolor="white", linewidth=2))
        if count_labels:
            mid = np.radians(angle-arc/2)
            rr = radius-width/2
            label(ax, cx+rr*np.cos(mid), cy+rr*np.sin(mid), str(value),
                  17, "bold", "ink", ha="center")
        angle -= arc
    ax.add_patch(patches.Circle((cx, cy), radius-width-.06,
                               facecolor=pale("lavender", .09), edgecolor="none", zorder=0))
    label(ax, cx, cy+.11, center, 29, "flow", "plum", ha="center")
    label(ax, cx, cy-.34, subtitle, 13.5, "italic", ha="center")


def pilot_figure(pilot, output):
    rows = pilot["rows"]
    assert len(rows) == 4 and all(r["targeted"]["ai"] == 1 for r in rows)
    probabilities = [r["new"]["ai"]*100 for r in rows]
    counts = Counter(r["outcome"] for r in rows)
    assert counts == {"tie": 3, "win": 1}
    fig, ax = canvas(12, 6.75)
    heading(ax, 6.75, "Detector response in the Mac MLX pilot",
            "Four fresh manuscripts · Mac MLX Qwen + hosted review · GPTZero AI-class probability")
    dot_legend(ax, .55, 5.28, "gray", "Targeted control", 14)
    dot_legend(ax, 2.65, 5.28, "lavender", "Qwen + review (retained)", 14)
    left, right = 3.58, 8.20
    ys = [4.67, 3.89, 3.11, 2.33]
    names = ["Evidence-linked revision", "Laboratory handover", "Citation preservation", "Negative findings"]
    for tick in [0, 25, 50, 75, 100]:
        x = left + (right-left)*tick/100
        ax.plot([x, x], [1.91, 4.98], color=pale("lavender", .30), lw=.7, zorder=-1)
        label(ax, x, 1.69, str(tick), 13, ha="center")
    for i, (name, value, y) in enumerate(zip(names, probabilities, ys)):
        if value < 100:
            capsule(ax, .38, y-.29, 8.13, .58, "lavender", .14, .15)
        label(ax, .53, y, name, 16.5, "bold" if value < 100 else "body")
        x = left+(right-left)*value/100
        ax.plot([x, right], [y, y], color=C["lavender"], lw=6, solid_capstyle="round", zorder=1)
        ax.scatter([right], [y], s=126, marker="o", facecolor="white", edgecolor=C["gray"], lw=1.8, zorder=3)
        ax.scatter([x], [y], s=47, marker="o", facecolor=C["plum"], edgecolor="white", lw=.6, zorder=4)
        label(ax, x-.15, y+.20, f"{value:.2f}%", 15.5, "bold", "plum", ha="right")
    label(ax, (left+right)/2, 1.28, "AI-class probability (%) · full scale", 14, "italic", ha="center")
    donut(ax, 10.15, 3.94, [1, 3], ["lavender", "sky"], 1.04, .25,
          "1 / 4", "lower", count_labels=False)
    dot_legend(ax, 9.10, 2.56, "lavender", "1 lower", 14)
    dot_legend(ax, 10.38, 2.56, "sky", "3 unchanged", 14)
    label(ax, 10.15, 1.84, f"{pilot['targetedMean']*100:.2f}% → {pilot['newMean']*100:.2f}%",
          19, "title", "plum", ha="center")
    label(ax, 10.15, 1.42, "Mean across all four", 14, "italic", ha="center")
    foot(ax, .40, "Four-case pilot: one lower, three unchanged; all retained texts remain AI-classified.", 13.5)
    save(fig, output/"pilot_results")


def human_figure(human, output):
    source, fluency = human["source_summary"], human["fluency_summary"]
    a = [source["correct"], source["generated_chosen_as_published"], source["cannot_tell"]]
    b = [fluency["revised_preferred"], fluency["original_preferred"], fluency["cannot_tell"]]
    assert a == b == [4, 5, 1]
    fig, ax = canvas(12, 6.35)
    heading(ax, 6.35, "Human judgments: source recognition and fluency",
            "Complete response-level counts · ten submitted comparisons per task")
    panels = [(3.00, "Source recognition", "Which passage came from a published paper?", a,
               ["Published selected", "Generated selected", "Cannot tell"], "4 / 10 correct"),
              (9.00, "Fluency preference", "Which passage reads more fluently?", b,
               ["Revision selected", "Initial selected", "Cannot tell"], "4 / 10 prefer revision")]
    for cx, title, question, values, names, result in panels:
        label(ax, cx, 4.79, title, 22, "title", "plum", ha="center")
        label(ax, cx, 4.35, question, 14.3, "italic", ha="center")
        donut(ax, cx-1.04, 2.83, values, ["lavender", "sky", "apricot"],
              1.05, .34, "10", "judgments")
        for i, (value, color, name) in enumerate(zip(values, ["lavender", "sky", "apricot"], names)):
            y = 3.55-.56*i
            dot_legend(ax, cx+.33, y, color, name, 15)
            label(ax, cx+.51, y-.25, f"{value} of 10", 13.5, "italic")
        capsule(ax, cx-2.48, 1.19, 4.96, .46, "lavender", .20)
        label(ax, cx, 1.42, result, 18, "title", "plum", ha="center")
    foot(ax, .46, "Ten submitted judgments per task; the exports do not identify the distinct raters behind those responses.", 13.5)
    save(fig, output/"human_results")


def verifier_figure(evaluation, output):
    data = read(evaluation/"semantic_challenge_metrics.json")
    assert data["completed"] == data["scheduled"] == 24
    fig, ax = canvas(12, 6.8)
    heading(ax, 6.8, "Preservation checks on known-answer edits",
            "Known-answer component challenge · 12 invalid edits + 12 valid paraphrases · identical inputs")
    cases = [("deterministic", "Lexical guard"), ("semantic", "Semantic review"), ("combined", "Both must pass")]
    for i, (key, title) in enumerate(cases):
        x0 = .20 + 4*i
        item = data["metrics"][key]
        label(ax, x0+1.98, 5.15, title, 21, "title", "plum", ha="center")
        label(ax, x0+1.54, 4.62, "Reject", 15, "bold", ha="center")
        label(ax, x0+2.74, 4.62, "Allow", 15, "bold", ha="center")
        for row, (row_name, vals, hues) in enumerate([
            ("Invalid", [item["TP"], item["FN"]], ["lavender", "apricot"]),
            ("Valid", [item["FP"], item["TN"]], ["apricot", "sage"]) ]):
            y = 3.87-row*1.16
            label(ax, x0+.82, y, row_name, 15, "bold", ha="right")
            for col, (value, hue) in enumerate(zip(vals, hues)):
                x = x0+1.54+col*1.20
                capsule(ax, x-.55, y-.51, 1.1, 1.02, hue, .12+.74*value/12, .16)
                label(ax, x, y+.09, str(value), 29, "bold", "plum", ha="center")
                label(ax, x, y-.27, ["TP", "FN", "FP", "TN"][row*2+col], 13, "italic", ha="center")
        correct = item["TP"]+item["TN"]
        label(ax, x0+1.98, 1.72, f"{correct} / 24 correct", 22, "title", "plum", ha="center")
        capsule(ax, x0+.90, 1.25, 2.16, .09, "gray", .28, .045)
        capsule(ax, x0+.90, 1.25, 2.16*correct/24, .09, "lavender", .90, .045)
    foot(ax, .46, "Rows: known input status. Columns: verifier decision. Counts describe the constructed component suite.", 13.5)
    save(fig, output/"verifier_results")


def detector_figure(data, output):
    fig, ax = canvas(12, 7.35)
    heading(ax, 7.35, "Detector response under the controlled Ollama condition",
            "Twelve controlled proposals · observed after retention · no detector feedback into writing")
    xcols = [4.35, 5.66, 6.97]
    conditions = ["original", "generic", "rules"]
    labels = ["Original", "Generic", "Rules"]
    vals = {(r["caseId"], r["condition"]): r["probability"]*100 for r in data["detector"]}
    for x, name in zip(xcols, labels):
        label(ax, x+.51, 5.76, name, 17, "bold", ha="center")
    for i, cid in enumerate(data["caseIds"]):
        y = 5.30-i*.325
        label(ax, .53, y, cid, 14, "bold")
        label(ax, 1.03, y, CASE_LABELS[i], 14.4)
        for x, condition in zip(xcols, conditions):
            v = vals[cid, condition]
            capsule(ax, x, y-.135, 1.04, .27, "lavender", .12+.72*v/100, .055)
            label(ax, x+.52, y, f"{v:g}%", 14, "bold", "plum", ha="center")
    for y, number, name in [(5.16, "12", "inputs"), (4.70, "3", "conditions"), (4.24, "35", "unique scans")]:
        label(ax, 9.03, y, number, 24, "title", "plum", ha="right")
        label(ax, 9.23, y, name, 16)
    cmap = LinearSegmentedColormap.from_list("probability", [pale("lavender", .12), pale("lavender", .84)])
    ax.imshow(np.linspace(0, 1, 256)[None, :], extent=(8.73, 11.35, 3.48, 3.67),
              cmap=cmap, vmin=0, vmax=1, aspect="auto", interpolation="bicubic", zorder=1)
    for value in [0, 50, 100]:
        x = 8.73+2.62*value/100
        label(ax, x, 3.25, str(value), 13, ha="center")
    label(ax, 10.04, 2.94, "Full AI-probability scale (%)", 13.5, "italic", ha="center")
    capsule(ax, 8.74, 1.65, 2.60, .90, "sky", .18)
    label(ax, 10.04, 2.20, "0 lower · 12 equal", 18, "title", "plum", ha="center")
    label(ax, 10.04, 1.87, "Rules versus Generic", 13.5, "italic", ha="center")
    foot(ax, .72, "36 mapped texts · detector "+", ".join(data["detectorVersions"])+" · all scans follow text retention.", 13.5)
    save(fig, output/"paired_gptzero_probabilities")


def preference_figure(data, output):
    fig, ax = canvas(12, 7.50)
    heading(ax, 7.50, "Naturalness preferences across presentation orders",
            "Anonymous model assessment · two display orders · complete twelve-case accounting")
    hues = {"generic": "sky", "rules": "lavender", "tie": "sage", "inconclusive": "apricot"}
    names = {"generic": "Generic", "rules": "Rules", "tie": "Tie", "inconclusive": "Unresolved"}
    xs = [3.55, 5.06, 6.57]
    for x, title in zip(xs, ["First order", "Reversed", "Both orders"]):
        label(ax, x+.66, 5.91, title, 16.5, "bold", ha="center")
    for i, row in enumerate(data["comparisons"]):
        y = 5.44-.335*i
        label(ax, .53, y, row["caseId"], 14, "bold")
        label(ax, 1.03, y, CASE_LABELS[i], 14.0)
        for x, key in zip(xs, ["firstOrder", "reversedOrder", "concordantOutcome"]):
            value = row[key]
            capsule(ax, x, y-.145, 1.32, .29, hues[value], .60 if key == "concordantOutcome" else .35, .06)
            label(ax, x+.66, y, names[value], 13.8, "bold", "plum", ha="center")
    counts = Counter(r["concordantOutcome"] for r in data["comparisons"])
    assert counts == {"rules": 7, "generic": 2, "inconclusive": 3}
    donut(ax, 10.07, 4.49, [7, 2, 3], ["lavender", "sky", "apricot"], 1.08, .30,
          "12", "cases", count_labels=True)
    for i, (value, key) in enumerate([(7, "rules"), (2, "generic"), (3, "inconclusive")]):
        y = 2.93-.47*i
        word = {"rules": "Rules preferred", "generic": "Generic preferred", "inconclusive": "Order-sensitive"}[key]
        dot_legend(ax, 8.84, y, hues[key], f"{value}  {word}", 15)
    label(ax, 10.07, 1.44, "0 consistent ties", 14, "italic", ha="center")
    foot(ax, .66, "Judge: "+", ".join(data["judgeModels"])+". Automated two-order comparison; all three order-sensitive cases remain unresolved.", 13)
    save(fig, output/"paired_naturalness_orders")


def ribbon(ax, x0, lo0, hi0, x1, lo1, hi1, color):
    a, b = x0+(x1-x0)*.45, x0+(x1-x0)*.55
    pts = [(x0, hi0), (a, hi0), (b, hi1), (x1, hi1), (x1, lo1),
           (b, lo1), (a, lo0), (x0, lo0), (x0, hi0)]
    codes = [MPath.MOVETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4,
             MPath.LINETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4, MPath.CLOSEPOLY]
    ax.add_patch(patches.PathPatch(MPath(pts, codes), facecolor=pale(color, .66), edgecolor="white", lw=.7))


def retention_figure(data, output):
    fig, ax = canvas(12, 7.60)
    heading(ax, 7.60, "Section retention after verification and repair",
            "Twelve proposals per condition · six sections each · ribbon thickness encodes counts")
    palette = {"direct": "sage", "repair": "lavender", "original": "apricot"}
    for condition, xoffset in [("generic", 0), ("rules", 6)]:
        counts = data["sectionPathCounts"][condition]
        x0, x1 = xoffset+.80, xoffset+3.35
        label(ax, xoffset+.53, 5.96, condition.title(), 23, "title", "plum")
        label(ax, xoffset+4.70, 5.96, "Final retained text", 14.5, "italic", ha="center")
        scale = 2.88/72
        source_top, target_top = 5.15, 5.52
        for kind in ["direct", "repair", "original"]:
            value = counts[kind]
            thickness = value*scale
            s_lo, t_lo = source_top-thickness, target_top-thickness
            capsule(ax, x0-.18, s_lo, .18, thickness, palette[kind], .95, .025)
            ribbon(ax, x0, s_lo, source_top, x1, t_lo, target_top, palette[kind])
            capsule(ax, x1, t_lo, .18, thickness, palette[kind], .95, .025)
            mid = (target_top+t_lo)/2
            label(ax, x1+.39, mid+.10, str(value), 25, "bold", "plum")
            label(ax, x1+1.02, mid+.11, {"direct": "Direct", "repair": "After repair", "original": "Original"}[kind], 17, "bold")
            label(ax, x1+1.02, mid-.19, f"{value/72*100:.1f}%", 13.5, "italic")
            source_top = s_lo
            target_top = t_lo-.38
        label(ax, x0+.10, 1.75, "72", 29, "flow", "plum")
        label(ax, x0+.85, 1.75, "section opportunities", 15, "italic")
        label(ax, xoffset+.54, 1.24, f"{counts['direct']+counts['repair']} / 72 sections changed", 20, "title", "plum")
    foot(ax, .48, "Final wording determines the path: repairs that restore the original are counted under “Original”.", 13.5)
    save(fig, output/"paired_section_retention_paths")


def load_pilot():
    audit = HERE.parent/"evidence_audit/archived_cohorts.json"
    if audit.exists():
        return read(audit)["heldout_summary.json"]["data"]
    return read(HERE.parent/"research/qwen_mlx/archive/heldout_summary.json")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation", type=Path, default=HERE.parent/"evaluation")
    parser.add_argument("--human", type=Path)
    parser.add_argument("--output", type=Path, default=HERE/"assets")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output/"paired").mkdir(exist_ok=True)
    human = args.human or next(p for p in [HERE.parent/"human/analysis.json", args.evaluation/"human/analysis.json"] if p.exists())
    paired = load_complete(args.evaluation.resolve())
    (output/"paired/figure_data.json").write_text(json.dumps(paired, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    pilot_figure(load_pilot(), output)
    human_figure(read(human), output)
    verifier_figure(args.evaluation, output)
    detector_figure(paired, output/"paired")
    preference_figure(paired, output/"paired")
    retention_figure(paired, output/"paired")
    print(json.dumps({"figures": 6, "data_verified": True, "section_paths": paired["sectionPathCounts"]}, indent=2))


if __name__ == "__main__":
    main()
