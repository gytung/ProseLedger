import json
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'engine'))
import core
import native_runtime
from run_paired import REVIEWER, log, verify_freeze


class SemanticClient:
    def public_config(self):
        return {'model': REVIEWER, 'mode': 'official-native-cli', 'task': 'fixed-known-answer-semantic-audit'}

    def stage_backend(self, stage):
        return 'hosted'

    def call(self, messages, cancel, stage):
        response = native_runtime.call(messages, REVIEWER, cancel, timeout=240)
        response['backend'] = 'hosted'
        return response

    def safe_error(self, error):
        return str(error)[:500]


def main():
    verify_freeze()
    challenges = json.loads((ROOT / 'known_answer_challenges.json').read_text())['cases']
    summaries = []
    for item in challenges:
        case_id = item['caseId']
        original = json.loads((ROOT / 'inputs' / (case_id + '.json')).read_text())
        candidate = original['draft'].replace(item['before'], item['after'], 1)
        folder = ROOT / 'semantic_challenges' / (case_id + '_' + item['challenge'])
        result_path = folder / 'result.json'
        if result_path.exists():
            summaries.append(json.loads(result_path.read_text()))
            continue
        run = core.RevisionRun(folder, SemanticClient())
        record = {**item, 'originalSHA256': core.digest(original['draft']), 'candidateSHA256': core.digest(candidate),
                  'sourceScope': 'same pre-existing fixed mutation challenge; semantic audit extension frozen after deterministic guard outcomes'}
        try:
            audit = run.full_audit('audit_full_revision', original['draft'], candidate, original['sources'])
            semantic_pass = audit['contentPreserved'] and not audit['issues']
            combined_pass = item['actualPass'] and semantic_pass
            record.update(status='completed', audit=audit, semanticPass=semantic_pass,
                          combinedPass=combined_pass, semanticCorrect=semantic_pass == item['expectedPass'],
                          combinedCorrect=combined_pass == item['expectedPass'])
            record['issueQuotes'] = [{'originalQuoteExact': x.get('originalQuote', '') in original['draft'],
                                     'revisedQuoteExact': x.get('revisedQuote', '') in candidate}
                                    for x in audit['issues']]
            run.checkpoint(status='completed', stage='Finished')
            result_path.write_text(json.dumps(record, ensure_ascii=False, indent=2))
        except Exception as error:
            run.checkpoint(status='failed', error=str(error)[:500])
            record.update(status='failed', error=str(error)[:500])
            (folder / 'failure.json').write_text(json.dumps(record, ensure_ascii=False, indent=2))
        summaries.append(record)
        summary = {'protocol': 'known-answer-semantic-audit-extension-20261113', 'scheduled': len(challenges),
                   'completed': sum(x['status'] == 'completed' for x in summaries), 'cases': summaries}
        for check_name, pass_key in [('semantic', 'semanticPass'), ('combined', 'combinedPass'), ('deterministic', 'actualPass')]:
            eligible = [x for x in summaries if x['status'] == 'completed']
            summary[check_name] = {
                'TP': sum(not x['expectedPass'] and not x[pass_key] for x in eligible),
                'FN': sum(not x['expectedPass'] and x[pass_key] for x in eligible),
                'TN': sum(x['expectedPass'] and x[pass_key] for x in eligible),
                'FP': sum(x['expectedPass'] and not x[pass_key] for x in eligible)}
        (ROOT / 'semantic_challenge_results.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
        log({'semanticChallenge': case_id, 'type': item['challenge'], 'status': record['status'],
             'semanticCorrect': record.get('semanticCorrect'), 'combinedCorrect': record.get('combinedCorrect')})


if __name__ == '__main__':
    main()
