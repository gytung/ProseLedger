"""Render the walkthrough from recorded generation and detector evidence."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def bind_external_validation(data, report):
    """Attach detector observations only after verifying their exact manuscripts."""
    run_id = report.get('runId')
    matches = [run for run in data['runs'] if run['id'] == run_id]
    if len(matches) != 1:
        raise ValueError('Detector evidence must identify exactly one recorded run.')
    result = matches[0]['result']
    manuscripts = {'initial': result['initialText']}
    manuscripts.update({key: result['branches'][key]['text']
                        for key in ('targeted', 'planner', 'memory')})
    observations = report.get('observations', [])
    document_ids = [observation.get('documentId') for observation in observations]
    if (set(document_ids) != set(manuscripts)
            or len(document_ids) != len(manuscripts)
            or report.get('completedScans') != len(observations)):
        raise ValueError('Detector evidence must contain one scan of each exact manuscript.')
    for observation in observations:
        manuscript = manuscripts[observation['documentId']]
        digest = hashlib.sha256(manuscript.encode('utf-8')).hexdigest()
        if observation.get('textSHA256') != digest:
            raise ValueError('Detector manuscript hash mismatch: ' + observation['documentId'])
    return {**data, 'externalValidation': {run_id: report}}


def main():
    data = json.loads((ROOT / 'docs/natural-writing-evidence.json').read_text(encoding='utf-8'))
    report = json.loads((ROOT / 'docs/validation/gptzero-observations.json').read_text(encoding='utf-8'))
    data = bind_external_validation(data, report)
    template = (ROOT / 'scripts/writing-demo.template.html').read_text(encoding='utf-8')
    encoded = json.dumps(data, ensure_ascii=True, separators=(',', ':')).replace('<', '\\u003c')
    (ROOT / 'docs/writing-demo.html').write_text(template.replace('__EVIDENCE__', encoded), encoding='utf-8')
    print('Built docs/writing-demo.html; four detector manuscript hashes verified; no model calls.')


if __name__ == '__main__':
    main()
