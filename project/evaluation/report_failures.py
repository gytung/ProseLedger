import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def decoded_record(source):
    path = ROOT / source
    record = json.loads(path.read_text())
    parsed = json.loads(record['text'].strip().removeprefix('```json').removesuffix('```').strip())
    name = path.parent.parent.name + '_' + path.parent.name + '_' + path.name.replace('.response.json', '.json')
    dest = ROOT / 'decoded_audits' / name
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(parsed, ensure_ascii=False, indent=2))
    return parsed, str(dest.relative_to(ROOT)), hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    chosen = json.loads((ROOT / 'curated_failure_cases.json').read_text())['cases']
    reports = []
    for case in chosen:
        event = case['observedEvent']
        case_id, condition = event['caseId'], event.get('condition')
        report = {k: v for k, v in case.items() if k != 'observedEvent'}
        report.update(caseId=case_id, condition=condition, originalQuote=event.get('originalQuote'),
                      candidateQuote=event.get('revisedQuote'), finding=event.get('problem', event.get('reason')),
                      classification=event.get('type', 'known_answer_false_positive'))
        source = event.get('source')
        if source and source.endswith('.response.json'):
            parsed, decoded, source_hash = decoded_record(source)
            review_index = next(i for i, r in enumerate(parsed['reviews']) if r['id'] == event['sectionId'])
            review = parsed['reviews'][review_index]
            issue_index = next(i for i, issue in enumerate(review['issues']) if issue['problem'] == event['problem'])
            report['evidence'] = [{'path': decoded, 'jsonPointer': '/reviews/' + str(review_index) + '/issues/' + str(issue_index)},
                                  {'path': source, 'jsonPointer': '/text', 'responseSHA256': source_hash}]
            folder = ROOT / 'runs' / case_id / condition
            ledger = json.loads((folder / 'revision_ledger.json').read_text())
            edit_index = next(i for i, edit in enumerate(ledger['edits']) if edit['id'] == event['sectionId'])
            edit = ledger['edits'][edit_index]
            report['section'] = edit['heading']
            report['finalSectionRestoredToOriginal'] = edit['retained'] == edit['original']
            report['finalSectionStatus'] = edit['status']
            report['repairDecision'] = {k:v for k,v in edit.get('repair', {}).items() if k in ('ok', 'reason')}
            report['evidence'].append({'path': str((folder/'revision_ledger.json').relative_to(ROOT)), 'jsonPointer': '/edits/' + str(edit_index)})
            repair_path = folder / 'repair_section_findings.response.json'
            if repair_path.exists():
                repairs, repair_decoded, _ = decoded_record(str(repair_path.relative_to(ROOT)))
                section_index = next((i for i,s in enumerate(repairs['sections']) if s['id'] == event['sectionId']), None)
                if section_index is not None:
                    patches = repairs['sections'][section_index]['patches']
                    report['proposedPatchesForThisFinding'] = [p for p in patches if p.get('issueIndex') == issue_index]
                    report['evidence'].append({'path': repair_decoded, 'jsonPointer': '/sections/' + str(section_index) + '/patches'})
            report['action'] = 'The original section was retained.' if report['finalSectionRestoredToOriginal'] else 'A bounded repair was applied and the revised section was retained after the final automated audit.' if edit.get('repair', {}).get('ok') else 'The revised section was retained after automated checks.'
            report['finalManuscriptSource'] = json.loads((folder/'run.json').read_text())['retained']
        elif event.get('type') == 'bounded_repair_rejected':
            folder = ROOT / 'runs' / case_id / condition
            ledger = json.loads((folder/'revision_ledger.json').read_text())
            edit_index = next(i for i,x in enumerate(ledger['edits']) if x['id'] == event['sectionId'])
            edit = ledger['edits'][edit_index]
            parsed, decoded, _ = decoded_record(str((folder/'repair_section_findings.response.json').relative_to(ROOT)))
            section_index = next(i for i,x in enumerate(parsed['sections']) if x['id'] == event['sectionId'])
            patches = parsed['sections'][section_index]['patches']
            deletion = next(x for x in patches if x['after'] == '')
            report.update(section=edit['heading'], originalQuote=edit['original'], candidateQuote=edit['candidate'],
                          proposedDeletion=deletion, finalSectionRestoredToOriginal=edit['retained'] == edit['original'],
                          finalSectionStatus=edit['status'], repairDecision=edit['repair'],
                          action='The complete patch set was rejected because one replacement was empty. The original section was restored; changes in the other sections remained eligible.',
                          finalManuscriptSource=json.loads((folder/'run.json').read_text())['retained'])
            report['evidence'] = [{'path': decoded, 'jsonPointer': '/sections/' + str(section_index) + '/patches'},
                                  {'path': source, 'jsonPointer': '/edits/' + str(edit_index) + '/repair'}]
        elif event.get('type') == 'whole_document_audit_finding':
            checks = json.loads((ROOT / source).read_text())
            issue_index = next(i for i,x in enumerate(checks['audit']['issues']) if x['problem'] == event['problem'])
            report.update(section=event['section'], finalManuscriptSource='original',
                          action='The final audit rejected the complete candidate. Under the standard policy, no additional full-audit repair round is allowed; the original manuscript was retained.',
                          evidence=[{'path': source, 'jsonPointer': '/audit/issues/' + str(issue_index)},
                                    {'path': 'runs/' + case_id + '/' + condition + '/run.json', 'jsonPointer': '/retained'}])
        else:
            report.update(section='Methodology', originalQuote=event['before'], candidateQuote=event['after'],
                          finding='The digit token 18 is absent after a meaning-preserving conversion to eighteen.',
                          action='The deterministic guard rejects the valid paraphrase. The semantic checker accepts it, but their conjunction retains the false rejection.',
                          finalManuscriptSource='component challenge; no writing run',
                          evidence=[{'path': 'semantic_challenges/C02_benign/result.json', 'jsonPointer': '/audit'},
                                    {'path': 'semantic_challenges/C02_benign/result.json', 'jsonPointer': '/combinedCorrect'}])
        reports.append(report)
    (ROOT / 'report_failure_cases.json').write_text(json.dumps(reports, ensure_ascii=False, indent=2))
    lines = ['# Mechanism-based failure analysis', '',
             'These cases were selected to cover distinct mechanisms, not to estimate their prevalence. All observed events remain in observed_failure_events.json. Most candidate faults were corrected or rolled back before the retained output. Automated auditor findings are distinguished from the constructed known-answer false positive.', '']
    for r in reports:
        lines.extend(['## ' + r['failureId'] + ' — ' + r['title'], '',
                      '**Record:** ' + r['caseId'] + ' / ' + str(r.get('condition') or 'component challenge') + ' / ' + str(r.get('section', '')), '',
                      '**Original:** ' + str(r.get('originalQuote') or 'See source record.'), '',
                      '**Candidate:** ' + str(r.get('candidateQuote') or 'See source record.'), '',
                      '**Finding and cause:** ' + str(r.get('finding') or '') + ' ' + r['analysis'], '',
                      '**Action and retained outcome:** ' + r['action'] + ' Final manuscript: ' + r['finalManuscriptSource'] + '.', '',
                      '**Next step:** ' + r['nextStep'], '', '**Evidence:**'])
        lines.extend('- `' + e['path'] + '#' + e['jsonPointer'] + '`' for e in r['evidence'])
        lines.append('')
    (ROOT / 'report_failure_cases.md').write_text('\n'.join(lines))
    print(json.dumps({'failureCases': len(reports), 'allHaveEvidencePointers': all(bool(r.get('evidence')) for r in reports)}))


if __name__ == '__main__':
    main()
