import argparse
import concurrent.futures
import hashlib
import json
import platform
import re
import sys
import threading
import time
from pathlib import Path
from urllib.request import Request, ProxyHandler, build_opener

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'engine'))
import core
import native_runtime
import transport

WRITER_LOCK = threading.Lock()
PRINT_LOCK = threading.Lock()
MODEL = 'qwen2.5:7b-instruct-q4_K_M'
REVIEWER = 'gpt-6.1-sol'
BASELINE_INSTRUCTION = (
    'Copy-edit only the supplied section to improve fluency, clarity and academic readability. '
    'Preserve every substantive proposition, technical term, citation occurrence, method step, '
    'comparison, metric and limitation. Do not move material across sections. Do not invent details '
    'or deliberately introduce errors. Keep approximately the original length. Return {text:string} '
    'with only the revised section body; no headings. Use the full manuscript for context.'
)


def log(value):
    with PRINT_LOCK:
        print(json.dumps(value, ensure_ascii=False), flush=True)


def verify_freeze():
    freeze = json.loads((ROOT / 'freeze.json').read_text())
    for relative, expected in freeze['files'].items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError('Frozen file changed: ' + relative)
    return freeze


class EvaluationClient:
    def __init__(self, condition, metadata):
        self.condition = condition
        self.metadata = metadata
        self.holds_writer = False

    def prepare(self):
        return None

    def public_config(self):
        return {'condition': self.condition, 'writer': self.metadata, 'reviewer': REVIEWER,
                'sectionSeeds': list(range(42, 48)), 'reviewTransport': 'official-native-cli',
                'writerTemperature': 0.2, 'writerContextTokens': 8192,
                'protocol': 'controlled-paired-section-study-20261113'}

    def stage_backend(self, stage):
        return 'local_qwen' if re.fullmatch(r'rewrite_section_[1-6]', stage) else 'hosted'

    def safe_error(self, error):
        return str(error)[:500]

    def release(self):
        if self.holds_writer:
            self.holds_writer = False
            WRITER_LOCK.release()

    def call(self, messages, cancel, stage):
        began = time.monotonic()
        if self.stage_backend(stage) == 'local_qwen':
            if not self.holds_writer:
                WRITER_LOCK.acquire()
                self.holds_writer = True
            seed = 41 + int(stage.rsplit('_', 1)[-1])
            response = transport.local_qwen_chat(messages, cancel, seed)
            response['modelDigest'] = self.metadata['digest']
            response['backend'] = 'local_qwen'
        else:
            self.release()
            response = native_runtime.call(messages, REVIEWER, cancel, timeout=240)
            response['backend'] = 'hosted'
        response['elapsedSeconds'] = round(time.monotonic() - began, 2)
        return response


class PairedRun(core.RevisionRun):
    def ask(self, stage, instruction, payload):
        if self.client.condition == 'generic' and re.fullmatch(r'rewrite_section_[1-6]', stage):
            instruction = BASELINE_INSTRUCTION
            payload = {key: value for key, value in payload.items() if key != 'rules'}
        if self.client.stage_backend(stage) == 'hosted':
            self.client.release()
        return super().ask(stage, instruction, payload)


def probe():
    opener = build_opener(ProxyHandler({}))
    with opener.open(Request('http://127.0.0.1:11436/api/tags'), timeout=10) as response:
        tags = json.load(response)
    selected = next((x for x in tags.get('models', []) if x.get('name') == MODEL), None)
    if not selected:
        raise ValueError('Pinned local Qwen model is not running on port 11436.')
    if selected.get('digest') != transport.LOCAL_QWEN_DIGEST:
        raise ValueError('Pinned local Qwen weight digest does not match.')
    with opener.open(Request('http://127.0.0.1:11436/api/version'), timeout=10) as response:
        version = json.load(response)
    return {'model': MODEL, 'digest': selected['digest'], 'size': selected.get('size'),
            'ollamaVersion': version.get('version'), 'hostSystem': platform.system(),
            'hostArchitecture': platform.machine(), 'runtime': 'Ollama', 'quantization': 'Q4_K_M'}


def run_one(case_id, condition, metadata, resume):
    supplied = json.loads((ROOT / 'inputs' / (case_id + '.json')).read_text())
    folder = ROOT / 'runs' / case_id / condition
    record_path = folder / 'run.json'
    if record_path.exists():
        old = json.loads(record_path.read_text())
        if old.get('status') == 'completed':
            log({'case': case_id, 'condition': condition, 'status': 'existing-completed'})
            return
        if not resume:
            log({'case': case_id, 'condition': condition, 'status': 'existing-incomplete-use-resume'})
            return
    client = EvaluationClient(condition, metadata)
    previous = None
    def progress(value):
        nonlocal previous
        pair = (value.get('stage'), value.get('status'))
        if pair != previous:
            log({'case': case_id, 'condition': condition, 'stage': pair[0], 'status': pair[1],
                 'calls': value.get('completedCalls'), 'seconds': value.get('elapsedSeconds')})
            previous = pair
    try:
        result = PairedRun(folder, client, progress=progress).execute(supplied)
        sections = json.loads((folder / 'section_candidates.json').read_text())
        title, _ = core.split_sections(supplied['draft'])
        raw = title + '\n\n' + '\n\n'.join('## ' + x['heading'] + '\n\n' + x['candidate'] for x in sections)
        (folder / 'raw_candidate.md').write_text(raw)
        log({'case': case_id, 'condition': condition, 'status': result['status'],
             'retained': result['retained'], 'changedSections': result['changedSections'],
             'seconds': result['elapsedSeconds']})
    except Exception as exc:
        log({'case': case_id, 'condition': condition, 'status': 'failed', 'error': str(exc)[:300]})
    finally:
        client.release()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cases', nargs='*')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--workers', type=int, choices=(1, 2), default=2)
    args = parser.parse_args()
    freeze = verify_freeze()
    metadata = probe()
    (ROOT / 'execution_environment.json').write_text(json.dumps(metadata, indent=2))
    tasks = []
    for index, item in enumerate(json.loads((ROOT / 'input_index.json').read_text())):
        case_id = item['caseId']
        if args.cases and case_id not in args.cases:
            continue
        conditions = ['generic', 'rules'] if index % 2 == 0 else ['rules', 'generic']
        tasks.extend((case_id, condition) for condition in conditions)
    log({'event': 'start', 'runs': len(tasks), 'frozenAtUTC': freeze['frozenAtUTC'],
         'writerSerialized': True, 'workers': args.workers, 'detectorUsed': False})
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run_one, case, condition, metadata, args.resume) for case, condition in tasks]
        for future in concurrent.futures.as_completed(futures):
            future.result()
    statuses = []
    for case, condition in tasks:
        path = ROOT / 'runs' / case / condition / 'run.json'
        statuses.append({'case': case, 'condition': condition,
                         'status': json.loads(path.read_text()).get('status') if path.exists() else 'not-run'})
    (ROOT / 'completion.json').write_text(json.dumps(statuses, indent=2))
    log({'event': 'finished', 'completed': sum(x['status'] == 'completed' for x in statuses), 'total': len(tasks)})


if __name__ == '__main__':
    main()
