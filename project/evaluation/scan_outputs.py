import argparse
import datetime
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from urllib.request import Request, build_opener, HTTPRedirectHandler

ROOT = Path(__file__).resolve().parent


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Detector redirects are not followed.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--key-stdin', action='store_true')
    args = parser.parse_args()
    key = sys.stdin.readline().strip() if args.key_stdin else os.environ.get('GPTZERO_API_KEY', '').strip()
    if not key or len(key) > 2048:
        raise SystemExit('Supply GPTZERO_API_KEY or --key-stdin. The key is never saved.')
    queue = []
    for path in sorted((ROOT / 'inputs').glob('*.json')):
        item = json.loads(path.read_text())
        queue.append((item['caseId'], 'original', item['draft']))
        for condition in ('generic', 'rules'):
            folder = ROOT / 'runs' / item['caseId'] / condition
            run = folder / 'run.json'
            if not run.exists() or json.loads(run.read_text()).get('status') != 'completed':
                raise SystemExit('All 24 runs must complete before detector evaluation: ' + item['caseId'] + '/' + condition)
            queue.append((item['caseId'], condition, (folder / 'proposal.md').read_text()))
    destination = ROOT / 'detector'
    destination.mkdir(exist_ok=True)
    index = []
    opener = build_opener(NoRedirect())
    for case_id, condition, text in queue:
        digest = hashlib.sha256(text.encode()).hexdigest()
        path = destination / (digest + '.json')
        if path.exists():
            record = json.loads(path.read_text())
        else:
            started = time.monotonic()
            request = Request('https://api.gptzero.me/v2/predict/text',
                              data=json.dumps({'document': text}).encode(),
                              headers={'Content-Type': 'application/json', 'x-api-key': key,
                                       'User-Agent': 'ProseLedger-Evaluation/1'})
            try:
                with opener.open(request, timeout=90) as response:
                    raw = json.loads(response.read(3_000_001))
            except Exception as error:
                (destination / 'error.json').write_text(json.dumps({'case': case_id, 'condition': condition,
                    'textSHA256': digest, 'errorType': type(error).__name__, 'httpStatus': getattr(error, 'code', None)}))
                raise SystemExit('Detector request failed; completed scans remain saved. Error type: ' + type(error).__name__) from None
            if key in json.dumps(raw):
                raise SystemExit('Detector echoed credential material; response discarded.')
            document = raw.get('documents', [{}])[0]
            probability = document.get('class_probabilities', {}).get('ai')
            if not isinstance(probability, (int, float)) or not 0 <= probability <= 1:
                raise SystemExit('Detector response did not contain a supported AI class probability.')
            record = {'textSHA256': digest, 'characters': len(text),
                      'scannedAtUTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                      'elapsedSeconds': round(time.monotonic() - started, 3),
                      'aiProbability': probability, 'predictedClass': document.get('predicted_class'),
                      'version': document.get('version', raw.get('version')), 'raw': raw}
            path.write_text(json.dumps(record, ensure_ascii=False, indent=2))
        index.append({'caseId': case_id, 'condition': condition, 'textSHA256': digest,
                      'aiProbability': record['aiProbability'], 'predictedClass': record.get('predictedClass'),
                      'version': record.get('version'), 'responseFile': path.name})
        (destination / 'index.json').write_text(json.dumps(index, indent=2))
        print(json.dumps({'case': case_id, 'condition': condition, 'aiProbability': record['aiProbability']}), flush=True)
    key = ''


if __name__ == '__main__':
    main()
