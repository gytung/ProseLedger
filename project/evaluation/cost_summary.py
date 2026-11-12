import collections
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def totals(records):
    return {'responseCount': len(records),
            'inputTokens': sum(x.get('usage', {}).get('input_tokens', 0) for x in records),
            'cachedInputTokens': sum(x.get('usage', {}).get('cached_input_tokens', 0) for x in records),
            'outputTokens': sum(x.get('usage', {}).get('output_tokens', 0) for x in records),
            'activeSeconds': round(sum(x.get('localDurationSeconds', x.get('elapsedSeconds', 0)) for x in records), 2)}


def main():
    groups = collections.defaultdict(list)
    cases = []
    starts, finishes = [], []
    for folder in sorted((ROOT / 'runs').glob('*/*')):
        run_file = folder / 'run.json'
        if not run_file.exists():
            continue
        run = json.loads(run_file.read_text())
        responses = []
        for p in folder.glob('*.json'):
            x = json.loads(p.read_text())
            if isinstance(x, dict) and isinstance(x.get('text'), str) and isinstance(x.get('usage'), dict) and 'messages' in x:
                responses.append(x)
                backend = 'local_qwen' if x.get('backend') == 'local_qwen' else 'hosted_review_repair'
                groups[folder.name + '/' + backend].append(x)
        case_row = {'caseId': folder.parent.name, 'condition': folder.name, 'status': run['status'],
                    'wallElapsedSeconds': run.get('totalElapsedSeconds'),
                    **totals(responses)}
        cases.append(case_row)
        if run.get('attemptStartedAt') is not None:
            starts.append(run['attemptStartedAt'])
            if run['status'] in ('completed', 'failed', 'cancelled'):
                finishes.append(run['attemptStartedAt'] + run.get('elapsedSeconds', 0))
    for p in (ROOT / 'judgments').glob('*/*.json'):
        x = json.loads(p.read_text())
        if 'usage' in x:
            groups['blinded_evaluation'].append(x)
    for p in (ROOT / 'semantic_challenges').glob('*/*.response.json'):
        x = json.loads(p.read_text())
        if 'usage' in x:
            groups['known_answer_semantic_evaluation'].append(x)
    grouped = {k: totals(v) for k, v in groups.items()}
    means = {}
    for condition in ('generic', 'rules'):
        selected = [x for x in cases if x['condition'] == condition and x['status'] == 'completed']
        means[condition] = {'completedCases': len(selected),
                            'meanActiveSeconds': statistics.mean(x['activeSeconds'] for x in selected) if selected else None,
                            'meanWallSecondsIncludingQueue': statistics.mean(x['wallElapsedSeconds'] for x in selected) if selected else None,
                            'meanInputTokens': statistics.mean(x['inputTokens'] for x in selected) if selected else None,
                            'meanOutputTokens': statistics.mean(x['outputTokens'] for x in selected) if selected else None,
                            'meanSuccessfulResponseCount': statistics.mean(x['responseCount'] for x in selected) if selected else None}
    output = {'scope': 'Counts from actual saved response usage. Hosted CLI input tokens include its standard instruction overhead; cached input is a subset of input tokens, not an extra total. Active time sums response durations; wall time includes scheduler waiting. No monetary cost is inferred.',
              'groups': grouped, 'generationMeans': means,
              'generationWallSpanSeconds': round(max(finishes)-min(starts), 2) if starts and finishes else None,
              'generationRunsCompleted': sum(x['status'] == 'completed' for x in cases),
              'generationRunsScheduled': 24, 'cases': cases}
    (ROOT / 'cost_summary.json').write_text(json.dumps(output, indent=2))
    print(json.dumps({k: v for k, v in output.items() if k != 'cases'}, indent=2))


if __name__ == '__main__':
    main()
