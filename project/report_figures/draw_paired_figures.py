"""Draw complete paired-evaluation results; incomplete evidence is never plotted."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile

os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'proseledger-mpl'))

HERE = Path(__file__).resolve().parent
DEFAULT_EVALUATION = HERE if (HERE / 'input_index.json').exists() else HERE.parent / 'evaluation'
COLORS = {'plum': '#5D425F', 'ink': '#514A56', 'lavender': '#C4B7D7',
          'sage': '#A8BCA3', 'sky': '#8FBFDA', 'apricot': '#E8B792',
          'gray': '#E5E1E8', 'soft': '#FAF8FC'}
CASE_LABELS = ['Glacier mapping', 'Bus reliability', 'Salt stress', 'Code review',
               'Museum provenance', 'Water quality', 'Oral histories',
               'Energy forecasts', 'Material fractions', 'Accessible routes',
               'Reasoning feedback', 'Archaeological dates']
ARMS = ('generic', 'rules')
CONDITIONS = ('original', 'generic', 'rules')
OUTCOME_LABELS = {'generic': 'Generic', 'rules': 'Rules', 'tie': 'Tie', 'inconclusive': 'Inconclusive'}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_complete(root):
    index = read(root / 'input_index.json')
    case_ids = [row['caseId'] for row in index]
    if case_ids != [f'C{i:02d}' for i in range(1, 13)]:
        raise ValueError('Expected the complete frozen C01–C12 input set.')
    summary = read(root / 'summary.json')
    rows = summary.get('cases', [])
    if len(rows) != 12 or {r['caseId'] for r in rows} != set(case_ids):
        raise ValueError('Summary must contain all 12 cases.')
    summaries = {r['caseId']: r for r in rows}
    detector_rows = read(root / 'detector' / 'index.json')
    expected = {(case, condition) for case in case_ids for condition in CONDITIONS}
    if len(detector_rows) != 36 or {(r['caseId'], r['condition']) for r in detector_rows} != expected:
        raise ValueError(f'Detector mapping is incomplete ({len(detector_rows)}/36).')
    detector = {(r['caseId'], r['condition']): r for r in detector_rows}
    paths = Counter()
    section_details = []
    comparisons = []
    scans = []
    judge_models = set()
    detector_versions = set()
    source_hashes = {}
    for case in case_ids:
        row = summaries[case]
        for arm in ARMS:
            directory = root / 'runs' / case / arm
            status = read(directory / 'run.json')
            if status.get('status') != 'completed' or row.get(arm + '_status') != 'completed':
                raise ValueError(f'{case}/{arm}: generation not completed.')
            ledger = read(directory / 'revision_ledger.json')
            if len(ledger['edits']) != 6:
                raise ValueError(f'{case}/{arm}: expected six ledger sections.')
            changed = 0
            for position, edit in enumerate(ledger['edits']):
                equal = edit['retained'] == edit['original']
                if equal:
                    category = 'original'
                    if edit['status'] != 'unchanged_or_rejected':
                        raise ValueError(f'{case}/{arm}: unchanged text has inconsistent status.')
                else:
                    if edit['status'] != 'verified_edit':
                        raise ValueError(f'{case}/{arm}: changed text has inconsistent status.')
                    category = 'repair' if edit.get('repair', {}).get('ok') is True else 'direct'
                    changed += 1
                paths[arm, category] += 1
                section_details.append({'caseId': case, 'condition': arm, 'sectionIndex': position,
                                        'status': edit['status'], 'repairAccepted': edit.get('repair', {}).get('ok') is True,
                                        'finalPath': category})
            if changed != row.get(arm + '_changedSections'):
                raise ValueError(f'{case}/{arm}: ledger and summary changed-section totals differ.')
            source_hashes[str((directory / 'revision_ledger.json').relative_to(root))] = sha(directory / 'revision_ledger.json')
        for condition in CONDITIONS:
            item = detector[case, condition]
            probability = item.get('aiProbability')
            if isinstance(probability, bool) or not isinstance(probability, (int, float)) or not math.isfinite(probability) or not 0 <= probability <= 1:
                raise ValueError(f'{case}/{condition}: missing or invalid detector probability.')
            raw_file = root / 'detector' / item['responseFile']
            raw = read(raw_file)
            text_file = root / 'runs' / case / ('generic' if condition == 'original' else condition) / ('initial.md' if condition == 'original' else 'proposal.md')
            text_hash = sha(text_file)
            if text_hash != item['textSHA256'] or raw.get('textSHA256') != text_hash:
                raise ValueError(f'{case}/{condition}: detector/text hash mismatch.')
            if raw.get('aiProbability') != probability or not raw.get('raw'):
                raise ValueError(f'{case}/{condition}: detector response does not support index.')
            if row.get(condition + '_aiProbability') != probability:
                raise ValueError(f'{case}/{condition}: summary is stale; regenerate it after scans finish.')
            detector_versions.add(item.get('version', 'not reported'))
            scans.append({'caseId': case, 'condition': condition, 'probability': probability,
                          'textSHA256': text_hash, 'responseFile': item['responseFile']})
            source_hashes[str(raw_file.relative_to(root))] = sha(raw_file)
        choices = []
        mappings = []
        for order in (0, 1):
            path = root / 'judgments' / case / f'order{order}.json'
            judgment = read(path)
            if judgment.get('status') != 'completed':
                raise ValueError(f'{case}/order{order}: judgment not completed.')
            pref = judgment['judgment']['preference']
            mapped = 'tie' if pref == 'tie' else judgment['labelMapping'].get(pref)
            if mapped not in ('generic', 'rules', 'tie'):
                raise ValueError(f'{case}/order{order}: invalid mapped preference.')
            choices.append(mapped)
            mappings.append(judgment['labelMapping'])
            judge_models.add(judgment.get('model', 'not reported'))
            source_hashes[str(path.relative_to(root))] = sha(path)
        if mappings[0]['A'] != mappings[1]['B'] or mappings[0]['B'] != mappings[1]['A']:
            raise ValueError(f'{case}: the two judgments do not reverse presentation order.')
        winner = choices[0] if choices[0] == choices[1] else 'inconclusive'
        if row.get('blindedChoices') != choices or row.get('naturalnessWinner') != winner:
            raise ValueError(f'{case}: summary is stale; regenerate it after judgments finish.')
        comparisons.append({'caseId': case, 'firstOrder': choices[0], 'reversedOrder': choices[1],
                            'concordantOutcome': winner, 'labelMappings': mappings})
    counts = {arm: {key: paths[arm, key] for key in ('direct', 'repair', 'original')} for arm in ARMS}
    for arm in ARMS:
        if sum(counts[arm].values()) != 72:
            raise ValueError(f'{arm}: section paths must sum to 72.')
        if counts[arm]['direct'] + counts[arm]['repair'] != summary['changedSectionTotals'][arm]:
            raise ValueError(f'{arm}: global changed-section summary is inconsistent.')
    for file in ('summary.json', 'input_index.json', 'detector/index.json'):
        source_hashes[file] = sha(root / file)
    return {'caseIds': case_ids, 'detector': scans, 'comparisons': comparisons,
            'sectionPathCounts': counts, 'sectionPaths': section_details,
            'judgeModels': sorted(judge_models), 'detectorVersions': sorted(detector_versions),
            'sourceSHA256': source_hashes}


def setup_plotting():
    global plt, patches, MPath, F
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import patches
    from matplotlib.path import Path as MPath
    from matplotlib.font_manager import FontProperties, findfont
    font_dir = Path('/System/Library/Fonts/Supplemental')
    font_files = {'body': 'Times New Roman.ttf', 'bold': 'Times New Roman Bold.ttf',
                  'italic': 'Times New Roman Italic.ttf', 'title': 'Times New Roman Bold Italic.ttf'}
    F = {}
    for name, filename in font_files.items():
        if (font_dir / filename).exists():
            F[name] = FontProperties(fname=str(font_dir / filename))
        else:
            weight = 'bold' if name in ('bold', 'title') else 'normal'
            style = 'italic' if name in ('italic', 'title') else 'normal'
            properties = FontProperties(family='Times New Roman', weight=weight, style=style)
            try:
                F[name] = FontProperties(fname=findfont(properties, fallback_to_default=False))
            except ValueError:
                F[name] = FontProperties(family='DejaVu Serif', weight=weight, style=style)
    plt.rcParams.update({'pdf.fonttype': 42, 'ps.fonttype': 42, 'svg.fonttype': 'none',
                         'figure.facecolor': 'white', 'savefig.facecolor': 'white'})


def text(ax, x, y, value, size=15, style='body', color='ink', ha='left', va='top'):
    return ax.text(x, y, value, fontsize=size, fontproperties=F[style], color=COLORS.get(color, color),
                   ha=ha, va=va, linespacing=1.14, zorder=5)


def canvas(height):
    fig, ax = plt.subplots(figsize=(12, height))
    fig.subplots_adjust(left=0, bottom=0, right=1, top=1)
    ax.set(xlim=(0, 12), ylim=(0, height))
    ax.axis('off')
    return fig, ax


def heading(ax, height, title, subtitle):
    text(ax, .38, height - .24, title, 27, 'title', 'plum')
    text(ax, .4, height - .8, subtitle, 14.5)


def rounded(ax, x, y, w, h, color, alpha=1):
    ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad=0,rounding_size={min(.09,h/2)}',
                                      edgecolor='none', facecolor=COLORS.get(color, color), alpha=alpha, zorder=1))


def save(fig, output, name):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    width, height = fig.canvas.get_width_height()
    for ax in fig.axes:
        for label in ax.texts:
            bb = label.get_window_extent(renderer)
            if bb.x0 < -1 or bb.y0 < -1 or bb.x1 > width + 1 or bb.y1 > height + 1:
                raise ValueError(f'{name}: clipped label {label.get_text()!r}')
    for extension in ('pdf', 'svg', 'png'):
        fig.savefig(output / f'{name}.{extension}', dpi=240, facecolor='white')
    plt.close(fig)


def detector_figure(data, output):
    fig, ax = canvas(8.25)
    heading(ax, 8.25, 'Paired detector probabilities across twelve proposals',
            'All cases and all three texts · full 0–100% scale · detector observed after selection')
    plot_left, plot_right = 3.06, 8.38
    y_top, row_height = 6.36, .385
    values = {(row['caseId'], row['condition']): row['probability'] * 100 for row in data['detector']}
    palette = {'original': 'apricot', 'generic': 'sky', 'rules': 'lavender'}
    markers = {'original': 's', 'generic': 'o', 'rules': 'D'}
    offsets = {'original': .085, 'generic': 0, 'rules': -.085}
    for i, condition in enumerate(CONDITIONS):
        x = .53 + 2.22 * i
        ax.scatter([x], [6.98], c=[COLORS[palette[condition]]], marker=markers[condition], s=44, zorder=4)
        text(ax, x + .16, 7.1, condition.title(), 14, 'bold')
    for tick in range(0, 101, 20):
        x = plot_left + (plot_right - plot_left) * tick / 100
        ax.plot([x, x], [1.91, 6.57], color=COLORS['gray'], lw=.75, zorder=0)
        text(ax, x, 1.73, str(tick), 12.5, ha='center')
    text(ax, (plot_left + plot_right) / 2, 1.35, 'GPTZero AI probability (%)', 14.5, 'bold', ha='center')
    columns = [9.12, 10.12, 11.13]
    for x, label in zip(columns, ['Original', 'Generic', 'Rules']):
        text(ax, x, 6.84, label, 13, 'bold', ha='center')
    for i, case in enumerate(data['caseIds']):
        y = y_top - row_height * i
        if i % 2 == 0:
            rounded(ax, .4, y - .17, 11.15, .34, 'soft')
        text(ax, .54, y, case, 13.1, 'bold', va='center')
        text(ax, 1.0, y, CASE_LABELS[i], 12.8, va='center')
        scores = [values[case, c] for c in CONDITIONS]
        points = [plot_left + (plot_right - plot_left) * score / 100 for score in scores]
        ax.plot([min(points), max(points)], [y, y], color=COLORS['gray'], lw=2.2, zorder=2)
        for condition, x, score, col in zip(CONDITIONS, points, scores, columns):
            ax.scatter([x], [y + offsets[condition]], marker=markers[condition],
                       s=38 if condition != 'rules' else 36, facecolor=COLORS[palette[condition]],
                       edgecolor=COLORS['plum'], linewidth=.35, zorder=4)
            text(ax, col, y, f'{score:.2f}', 12.4, ha='center', va='center')
    all_scores = list(values.values())
    if min(all_scores) == max(all_scores):
        finding = f'All 36 case–condition observations returned {all_scores[0]:g}%.'
    else:
        decreased = sum(values[c, 'rules'] < values[c, 'generic'] for c in data['caseIds'])
        equal = sum(values[c, 'rules'] == values[c, 'generic'] for c in data['caseIds'])
        increased = 12 - decreased - equal
        finding = f'Rules versus Generic: {decreased} lower · {equal} equal · {increased} higher probabilities.'
    text(ax, .52, .93, finding, 15, 'bold', 'plum')
    text(ax, .52, .55, 'Marker offsets separate overlapping observations; horizontal position alone encodes probability.', 12.5, 'italic')
    text(ax, .52, .27, 'Detector version: ' + ', '.join(data['detectorVersions']) + '. This is a detector response, not a human-authorship rate.', 12, 'italic')
    save(fig, output, 'paired_gptzero_probabilities')


def preference_figure(data, output):
    fig, ax = canvas(8.0)
    heading(ax, 8.0, 'Naturalness judgments under reversed presentation order',
            'LLM proxy · anonymous texts · preferences mapped back to their generation condition')
    x_positions = [3.25, 5.82, 8.39]
    cell_width, row_height, y_top = 2.34, .345, 5.95
    labels = [('First presentation', 'firstOrder'), ('Reversed presentation', 'reversedOrder'),
              ('Concordant outcome', 'concordantOutcome')]
    color_for = {'rules': 'lavender', 'generic': 'sky', 'tie': 'sage', 'inconclusive': 'apricot'}
    for x, (label, key) in zip(x_positions, labels):
        text(ax, x + cell_width / 2, 6.46, label, 15, 'bold', ha='center')
    for i, row in enumerate(data['comparisons']):
        y = y_top - row_height * i
        text(ax, .53, y + .02, row['caseId'], 13, 'bold', va='center')
        text(ax, 1.01, y + .02, CASE_LABELS[i], 12.8, va='center')
        for x, (_, key) in zip(x_positions, labels):
            value = row[key]
            rounded(ax, x, y - .12, cell_width, .28, color_for[value], alpha=.60)
            text(ax, x + cell_width / 2, y + .018, OUTCOME_LABELS[value], 13, 'bold', 'plum', ha='center', va='center')
    counts = Counter(row['concordantOutcome'] for row in data['comparisons'])
    text(ax, .53, 1.69, 'Concordant outcomes across 12 cases', 16, 'title', 'plum')
    for i, value in enumerate(('rules', 'generic', 'tie', 'inconclusive')):
        x = .55 + 2.8 * i
        rounded(ax, x, .83, 2.45, .56, color_for[value], alpha=.30)
        text(ax, x + .15, 1.21, str(counts[value]), 19, 'bold', 'plum')
        text(ax, x + .55, 1.15, OUTCOME_LABELS[value], 13.5, 'bold')
    text(ax, .53, .54, 'Two display orders are two model calls, not two independent human raters. Disagreement is inconclusive.', 12.3, 'italic')
    text(ax, .53, .26, 'Judge: ' + ', '.join(data['judgeModels']) + '. Naturalness preference and factual preservation are assessed separately.', 12.0, 'italic')
    save(fig, output, 'paired_naturalness_orders')


def ribbon(ax, x0, lo0, hi0, x1, lo1, hi1, color):
    a, b = x0 + (x1 - x0) * .42, x0 + (x1 - x0) * .58
    points = [(x0, hi0), (a, hi0), (b, hi1), (x1, hi1),
              (x1, lo1), (b, lo1), (a, lo0), (x0, lo0), (x0, hi0)]
    codes = [MPath.MOVETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4,
             MPath.LINETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4, MPath.CLOSEPOLY]
    ax.add_patch(patches.PathPatch(MPath(points, codes), facecolor=COLORS[color],
                                  edgecolor='white', lw=.6, alpha=.64, zorder=2))


def retention_figure(data, output):
    fig, ax = canvas(8.4)
    heading(ax, 8.4, 'Where every revised section ends up',
            'Twelve proposals per arm · six sections per proposal · complete final-ledger accounting')
    names = {'direct': 'Revised text retained directly', 'repair': 'Revised text retained after repair',
             'original': 'Original text retained / restored'}
    palette = {'direct': 'sage', 'repair': 'lavender', 'original': 'apricot'}
    for arm, top in [('generic', 6.84), ('rules', 3.82)]:
        counts = data['sectionPathCounts'][arm]
        text(ax, .56, top - .55, arm.title(), 24, 'title', 'plum')
        text(ax, .57, top - 1.07, '72 sections', 17, 'bold')
        text(ax, .57, top - 1.45, '12 manuscripts', 13, 'italic')
        source_top = top - .35
        target_top = top
        scale = 2.10 / 72
        for key in ('direct', 'repair', 'original'):
            n = counts[key]
            thick = n * scale
            lo_source = source_top - thick
            lo_target = target_top - thick
            rounded(ax, 2.43, lo_source, .18, thick, palette[key], alpha=.95)
            ribbon(ax, 2.61, lo_source, source_top, 6.45, lo_target, target_top, palette[key])
            rounded(ax, 6.45, lo_target, .18, thick, palette[key], alpha=.95)
            mid = (lo_target + target_top) / 2
            text(ax, 6.9, mid, str(n), 24, 'bold', 'plum', va='center')
            text(ax, 7.53, mid + .10, names[key], 13.6, 'bold', va='center')
            text(ax, 7.53, mid - .16, f'{n}/72 sections · {100*n/72:.1f}%', 12.3, 'italic', va='center')
            source_top = lo_source
            target_top = lo_target - .25
    text(ax, .54, .64, 'Ribbon thickness is proportional to the number of sections; paths sum to 72 in each arm.', 13.2, 'italic')
    text(ax, .54, .35, 'Final retained text determines the path. A repair that returns the original text belongs to “original retained”, not “revised after repair”.', 11.6, 'italic')
    save(fig, output, 'paired_section_retention_paths')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluation', type=Path, default=DEFAULT_EVALUATION)
    parser.add_argument('--output', type=Path, default=HERE / 'assets' / 'paired')
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    try:
        data = load_complete(args.evaluation.resolve())
    except (FileNotFoundError, KeyError, ValueError) as error:
        print(json.dumps({'ready': False, 'reason': str(error), 'figuresWritten': False}))
        raise SystemExit(2)
    if args.check_only:
        print(json.dumps({'ready': True, 'cases': 12, 'detectorObservations': 36, 'judgments': 24,
                          'sectionPathCounts': data['sectionPathCounts']}, indent=2))
        return
    setup_plotting()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    detector_figure(data, output)
    preference_figure(data, output)
    retention_figure(data, output)
    (output / 'figure_data.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'ready': True, 'figures': ['paired_gptzero_probabilities', 'paired_naturalness_orders',
                                               'paired_section_retention_paths'], 'formats': ['pdf', 'svg', 'png'],
                      'sectionPathCounts': data['sectionPathCounts']}, indent=2))


if __name__ == '__main__':
    main()
