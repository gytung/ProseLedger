import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    events = []
    for folder in sorted((ROOT / 'runs').glob('*/*')):
        case_id, condition = folder.parent.name, folder.name
        run_path = folder / 'run.json'
        if not run_path.exists():
            continue
        run = json.loads(run_path.read_text())
        if run.get('status') == 'failed':
            events.append({'caseId': case_id, 'condition': condition, 'type': 'execution_failure',
                           'reason': run.get('error'), 'source': str(run_path.relative_to(ROOT))})
        ledger_path = folder / 'revision_ledger.json'
        ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {}
        edits = {x['id']: x for x in ledger.get('edits', [])}
        response_path = folder / 'audit_sections.response.json'
        if response_path.exists():
            response = json.loads(response_path.read_text())
            audit = json.loads(response['text'].strip().removeprefix('```json').removesuffix('```').strip())
            for review in audit.get('reviews', []):
                edit = edits.get(review['id'], {})
                for issue in review.get('issues', []):
                    events.append({'caseId': case_id, 'condition': condition, 'type': 'section_audit_finding',
                                   'sectionId': review['id'], 'section': edit.get('heading'), **issue,
                                   'repair': {k:v for k,v in edit.get('repair', {}).items() if k in ('ok', 'reason')},
                                   'finalEditStatus': edit.get('status'),
                                   'originalSectionRestored': bool(edit and edit.get('retained') == edit.get('original')),
                                   'source': str(response_path.relative_to(ROOT)),
                                   'evidenceType': 'model audit finding with exact supplied quotations; assess its validity before treating it as a confirmed error'})
        for edit in edits.values():
            repair = edit.get('repair', {})
            if not repair.get('ok') and repair.get('reason') not in (None, 'not_needed_or_not_repairable'):
                events.append({'caseId': case_id, 'condition': condition, 'type': 'bounded_repair_rejected',
                               'sectionId': edit['id'], 'section': edit['heading'], 'reason': repair.get('reason'),
                               'finalEditStatus': edit.get('status'), 'source': str(ledger_path.relative_to(ROOT))})
        checks_path = folder / 'checks.json'
        if checks_path.exists():
            checks = json.loads(checks_path.read_text())
            for issue in checks.get('audit', {}).get('issues', []):
                events.append({'caseId': case_id, 'condition': condition, 'type': 'whole_document_audit_finding',
                               **issue, 'candidateRetained': checks.get('eligible'),
                               'source': str(checks_path.relative_to(ROOT))})
            for finding in checks.get('guard', {}).get('findings', []):
                events.append({'caseId': case_id, 'condition': condition, 'type': 'deterministic_guard_rejected',
                               'reason': finding, 'candidateRetained': checks.get('eligible'),
                               'source': str(checks_path.relative_to(ROOT))})
    (ROOT / 'observed_failure_events.json').write_text(json.dumps({'events': events, 'count': len(events)}, ensure_ascii=False, indent=2))
    print(json.dumps({'events': len(events), 'distinctCases': len({x['caseId'] for x in events})}))


if __name__ == '__main__':
    main()
