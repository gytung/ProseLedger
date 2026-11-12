import concurrent.futures
import json
import time
from pathlib import Path

from judge_pairs import judge, log

ROOT = Path(__file__).resolve().parent


def main():
    scheduled = set()
    cases = [x['caseId'] for x in json.loads((ROOT / 'input_index.json').read_text())]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        pending = {}
        while len(scheduled) < len(cases):
            for case in cases:
                if case in scheduled:
                    continue
                paths = [ROOT / 'runs' / case / condition / 'run.json' for condition in ('generic', 'rules')]
                if all(p.exists() and json.loads(p.read_text()).get('status') == 'completed' for p in paths):
                    for orientation in (0, 1):
                        pending[pool.submit(judge, case, orientation)] = (case, orientation)
                    scheduled.add(case)
                    log({'judgeScheduled': case})
            for future in list(pending):
                if future.done():
                    try:
                        future.result()
                    except Exception as exc:
                        log({'judgeFailed': pending[future], 'error': str(exc)[:250]})
                    del pending[future]
            if (ROOT / 'completion.json').exists() and len(scheduled) < len(cases):
                log({'notScheduledIncomplete': [x for x in cases if x not in scheduled]})
                break
            time.sleep(10)
        for future in pending:
            try:
                future.result()
            except Exception as exc:
                log({'judgeFailed': pending[future], 'error': str(exc)[:250]})


if __name__ == '__main__':
    main()
