import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    rows = []
    for path in sorted((ROOT / 'inputs').glob('*.json')):
        source = json.loads(path.read_text())
        case = source['caseId']
        observed = {'generic': collections.defaultdict(list), 'rules': collections.defaultdict(list)}
        for order in (0, 1):
            p = ROOT / 'judgments' / case / ('order' + str(order) + '.json')
            if not p.exists():
                continue
            record = json.loads(p.read_text())
            if record.get('status') != 'completed':
                continue
            for item in record['judgment']['facts']:
                for label in ('A', 'B'):
                    condition = record['labelMapping'][label]
                    observed[condition][item['id']].append({'order': order, **item[label]})
        for fact_id, reference in enumerate(source['knownFacts']):
            for condition in ('generic', 'rules'):
                findings = observed[condition][fact_id]
                statuses = [x['status'] for x in findings]
                if len(statuses) != 2:
                    result = 'incomplete'
                elif statuses[0] == statuses[1]:
                    result = 'consistent_' + statuses[0]
                else:
                    result = 'disagreement'
                rows.append({'caseId': case, 'factId': fact_id, 'condition': condition,
                             'referenceFact': reference, 'consensus': result, 'judgments': findings,
                             'bothQuotesExact': len(findings) == 2 and all(x.get('exactQuoteVerified') for x in findings)})
    totals = {}
    for condition in ('generic', 'rules'):
        selected = [x for x in rows if x['condition'] == condition]
        totals[condition] = {'referenceFacts': len(selected),
                            'counts': dict(collections.Counter(x['consensus'] for x in selected)),
                            'consistentPreservedWithBothQuotesExact': sum(x['consensus'] == 'consistent_preserved' and x['bothQuotesExact'] for x in selected)}
    output = {'scope': '72 reference facts per condition, with two-order automated agreement per fact. Two judgments do not create two independent facts. Exact quote checks validate substring presence, not entailment.',
              'totals': totals, 'facts': rows}
    (ROOT / 'fact_consensus.json').write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(json.dumps(totals, indent=2))


if __name__ == '__main__':
    main()
