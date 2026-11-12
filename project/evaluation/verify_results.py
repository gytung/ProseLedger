import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PIN = '845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e'


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def main():
    failures = []
    checked_runs = 0
    writer_responses = 0
    freeze = json.loads((ROOT / 'freeze.json').read_text())
    for name, expected in freeze['files'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            failures.append('Frozen source changed: ' + name)
    for path in sorted((ROOT / 'inputs').glob('*.json')):
        item = json.loads(path.read_text())
        case_id = item['caseId']
        for condition in ('generic', 'rules'):
            folder = ROOT / 'runs' / case_id / condition
            label = case_id + '/' + condition
            run_path = folder / 'run.json'
            if not run_path.exists() or json.loads(run_path.read_text()).get('status') != 'completed':
                failures.append('Incomplete run: ' + label)
                continue
            checked_runs += 1
            original = (folder / 'initial.md').read_text()
            retained = (folder / 'proposal.md').read_text()
            ledger = json.loads((folder / 'revision_ledger.json').read_text())
            if original != item['draft']:
                failures.append('Initial manuscript mismatch: ' + label)
            if ledger.get('originalSHA256') != sha(original) or ledger.get('retainedSHA256') != sha(retained):
                failures.append('Ledger hash mismatch: ' + label)
            if ledger.get('memoryCardsUsed') != 0 or ledger.get('detectorUsedForAdmission') is not False:
                failures.append('Unexpected admission mechanism: ' + label)
            for section in range(1, 7):
                record_path = folder / ('rewrite_section_' + str(section) + '.response.json')
                if not record_path.exists():
                    failures.append('Missing writer response: ' + label + '/' + str(section))
                    continue
                response = json.loads(record_path.read_text())
                writer_responses += 1
                if response.get('sectionSeed') != section + 41 or response.get('modelDigest') != PIN:
                    failures.append('Writer model or seed mismatch: ' + label + '/' + str(section))
                payload = json.loads(response['messages'][1]['content'].split('\nINPUT DATA:\n', 1)[1])
                if payload['fullManuscript'] != item['draft'] or payload['sources'] != item['sources']:
                    failures.append('Writer context mismatch: ' + label + '/' + str(section))
                if ('rules' in payload) != (condition == 'rules'):
                    failures.append('Condition mismatch: ' + label + '/' + str(section))
    detectors = ROOT / 'detector' / 'index.json'
    scan_rows = 0
    if detectors.exists():
        for scan in json.loads(detectors.read_text()):
            case_id, condition = scan['caseId'], scan['condition']
            if condition == 'original':
                text = json.loads((ROOT / 'inputs' / (case_id + '.json')).read_text())['draft']
            else:
                text = (ROOT / 'runs' / case_id / condition / 'proposal.md').read_text()
            if sha(text) != scan['textSHA256']:
                failures.append('Detector text mismatch: ' + case_id + '/' + condition)
            scan_rows += 1
    result = {'passed': not failures, 'frozenSourceFiles': len(freeze['files']),
              'completedRunsVerified': checked_runs, 'expectedRuns': 24,
              'writerResponsesVerified': writer_responses, 'expectedWriterResponses': 144,
              'detectorRowsVerified': scan_rows, 'failures': failures}
    (ROOT / 'integrity_checks.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
