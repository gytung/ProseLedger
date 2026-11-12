import collections
import csv
import hashlib
import json
import math
import random
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def bootstrap(values):
    if not values:
        return None
    rng = random.Random(20261113)
    draws = sorted(statistics.mean(rng.choices(values, k=len(values))) for _ in range(10000))
    return {'mean': statistics.mean(values), 'lower95': draws[249], 'upper95': draws[9749],
            'method': 'paired case bootstrap percentile, 10000 resamples, seed 20261113', 'n': len(values)}


def wilson(k, n):
    if not n:
        return None
    z = 1.959963984540054
    centre = (k / n + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt((k / n) * (1 - k / n) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return {'proportion': k / n, 'lower95': centre - half, 'upper95': centre + half, 'numerator': k, 'denominator': n}


def main():
    rows = []
    detector_path = ROOT / 'detector' / 'index.json'
    detectors = json.loads(detector_path.read_text()) if detector_path.exists() else []
    detector = {(x['caseId'], x['condition']): x for x in detectors}
    for item in json.loads((ROOT / 'input_index.json').read_text()):
        case = item['caseId']
        row = {'caseId': case, 'title': item['title'], 'inputWords': item['words']}
        for condition in ('generic', 'rules'):
            folder = ROOT / 'runs' / case / condition
            path = folder / 'run.json'
            run = json.loads(path.read_text()) if path.exists() else {'status': 'not-run'}
            row[condition + '_status'] = run['status']
            for field in ('newCandidateAccepted', 'changedSections', 'initialWords', 'retainedWords', 'readability', 'contentPreserved', 'guardPassed', 'totalElapsedSeconds', 'totalCompletedCalls', 'totalLocalWriterCalls', 'totalHostedCalls'):
                row[condition + '_' + field] = run.get(field)
            responses = [json.loads(p.read_text()) for p in folder.glob('*.response.json')] if folder.exists() else []
            row[condition + '_activeModelSeconds'] = round(sum(x.get('localDurationSeconds', x.get('elapsedSeconds', 0)) for x in responses), 2)
            row[condition + '_inputTokens'] = sum(x.get('usage', {}).get('input_tokens', 0) for x in responses)
            row[condition + '_outputTokens'] = sum(x.get('usage', {}).get('output_tokens', 0) for x in responses)
            row[condition + '_cachedInputTokens'] = sum(x.get('usage', {}).get('cached_input_tokens', 0) for x in responses)
            if run['status'] == 'completed':
                raw = (folder / 'raw_candidate.md').read_text()
                retained = (folder / 'proposal.md').read_text()
                row[condition + '_rawSHA256'] = hashlib.sha256(raw.encode()).hexdigest()
                row[condition + '_retainedSHA256'] = hashlib.sha256(retained.encode()).hexdigest()
            for field in ('aiProbability', 'predictedClass'):
                row[condition + '_' + field] = detector.get((case, condition), {}).get(field)
        row['original_aiProbability'] = detector.get((case, 'original'), {}).get('aiProbability')
        choices = []
        fact_orders = []
        for orientation in (0, 1):
            path = ROOT / 'judgments' / case / ('order' + str(orientation) + '.json')
            if not path.exists():
                continue
            record = json.loads(path.read_text())
            if record.get('status') != 'completed':
                continue
            verdict = record['judgment']['preference']
            choices.append(record['labelMapping'].get(verdict, 'tie'))
            scores = {'generic': collections.Counter(), 'rules': collections.Counter()}
            for fact in record['judgment']['facts']:
                for label in ('A', 'B'):
                    condition = record['labelMapping'][label]
                    status = fact[label]['status']
                    if status == 'preserved' and not fact[label].get('exactQuoteVerified'):
                        status = 'unverified_quote'
                    scores[condition][status] += 1
            fact_orders.append({k: dict(v) for k, v in scores.items()})
        row['blindedChoices'] = choices
        row['blindedConsistency'] = len(choices) == 2 and choices[0] == choices[1]
        row['naturalnessWinner'] = choices[0] if row['blindedConsistency'] else 'inconclusive' if len(choices) == 2 else 'not-evaluated'
        row['factAssessments'] = fact_orders
        if all(row[c + '_aiProbability'] is not None for c in ('generic', 'rules')):
            delta = (row['rules_aiProbability'] - row['generic_aiProbability']) * 100
            row['detectorDeltaPercentagePoints'] = delta
            row['detectorRulesVsGeneric'] = 'win' if delta < -.01 else 'loss' if delta > .01 else 'tie'
        rows.append(row)
    completed = {c: sum(r[c + '_status'] == 'completed' for r in rows) for c in ('generic', 'rules')}
    summary = {'caseCount': len(rows), 'scheduledRuns': len(rows)*2, 'completedRuns': completed,
               'acceptedCandidates': {c: sum(r[c + '_newCandidateAccepted'] is True for r in rows) for c in ('generic', 'rules')},
               'changedSectionTotals': {c: sum(r[c + '_changedSections'] or 0 for r in rows) for c in ('generic', 'rules')},
               'naturalness': dict(collections.Counter(r['naturalnessWinner'] for r in rows)),
               'detectorRulesVsGeneric': dict(collections.Counter(r.get('detectorRulesVsGeneric', 'not-scanned') for r in rows)),
               'detectorPairedDifferencePercentagePoints': bootstrap([r['detectorDeltaPercentagePoints'] for r in rows if 'detectorDeltaPercentagePoints' in r]),
               'detectorIsPostHoc': True, 'detectorUsedForSelection': False, 'memoryCardsUsed': 0,
               'conditions': 'Generic vs six-rule section writing, with the same verification and repair process',
               'scope': '12 author-constructed controlled proposals; automated comparisons, not human ratings or population-level validation',
               'cases': rows}
    for condition in ('generic', 'rules'):
        values = [(r[condition + '_aiProbability']-r['original_aiProbability'])*100 for r in rows if r[condition + '_aiProbability'] is not None and r['original_aiProbability'] is not None]
        summary[condition + 'VsOriginalDetectorDifferencePP'] = bootstrap(values)
        counts = collections.Counter('decrease' if v < -.01 else 'increase' if v > .01 else 'unchanged' for v in values)
        summary[condition + 'VsOriginalDetectorCounts'] = dict(counts)
        summary[condition + 'DetectorDecreaseWilson95'] = wilson(counts['decrease'], len(values))
    (ROOT / 'summary.json').write_text(json.dumps(summary, indent=2))
    fields = list(dict.fromkeys(key for row in rows for key in row if key not in ('factAssessments', 'blindedChoices')))
    with (ROOT / 'case_results.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({key:value for key,value in summary.items() if key != 'cases'}, indent=2))


if __name__ == '__main__':
    main()
