import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'engine'))
import core


def main():
    rows = []
    for folder in sorted((ROOT / 'runs').glob('*/*')):
        if not (folder / 'revision_ledger.json').exists() or not (folder / 'raw_candidate.md').exists():
            continue
        case_id, condition = folder.parent.name, folder.name
        source = json.loads((ROOT / 'inputs' / (case_id + '.json')).read_text())
        ledger = json.loads((folder / 'revision_ledger.json').read_text())
        checks = json.loads((folder / 'checks.json').read_text())
        raw = (folder / 'raw_candidate.md').read_text()
        raw_guard = core.guard(source['draft'], raw, source['sources'])
        edits = ledger['edits']
        rows.append({'caseId': case_id, 'condition': condition, 'rawDeterministicGuardPassed': raw_guard['passed'],
                     'rawDeterministicFindings': raw_guard['findings'],
                     'sectionsWithReviewerFindings': sum(bool(x['review']['issues']) for x in edits),
                     'totalSectionReviewerFindings': sum(len(x['review']['issues']) for x in edits),
                     'boundedRepairAcceptedSections': sum(x.get('repair', {}).get('ok') is True for x in edits),
                     'boundedRepairRejectedSections': sum(x.get('repair', {}).get('reason') not in (None, 'not_needed_or_not_repairable') and not x.get('repair', {}).get('ok') for x in edits),
                     'finalFullAuditIssueCount': len(checks['audit']['issues']),
                     'finalCandidateEligible': checks['eligible'],
                     'retainedChangedSections': sum(x['status'] == 'verified_edit' for x in edits),
                     'automatedSignalsOnly': True})
    totals = {}
    fields = ['sectionsWithReviewerFindings', 'totalSectionReviewerFindings', 'boundedRepairAcceptedSections', 'boundedRepairRejectedSections', 'finalFullAuditIssueCount', 'retainedChangedSections']
    for condition in ('generic', 'rules'):
        selected = [x for x in rows if x['condition'] == condition]
        totals[condition] = {'completedCases': len(selected),
                             'rawGuardPassCases': sum(x['rawDeterministicGuardPassed'] for x in selected),
                             'eligibleFinalCandidates': sum(x['finalCandidateEligible'] for x in selected),
                             **{field: sum(x[field] for x in selected) for field in fields}}
    output = {'scope': 'Descriptive execution traces; model findings are not independently verified error labels.', 'totals': totals, 'cases': rows}
    (ROOT / 'trace_summary.json').write_text(json.dumps(output, indent=2))
    print(json.dumps(totals, indent=2))


if __name__ == '__main__':
    main()
