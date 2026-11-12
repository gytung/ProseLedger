import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description='Create a new evaluation workspace from frozen inputs, with no archived model responses.')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--execute', action='store_true', help='Run generation and automated evaluation after creating the workspace.')
    args = parser.parse_args()
    destination = args.out.expanduser().resolve()
    if destination.exists():
        raise SystemExit('The output directory already exists. Choose a new directory; prior results are never overwritten.')
    freeze = json.loads((ROOT / 'freeze.json').read_text())
    for name, expected in freeze['files'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise SystemExit('Frozen source verification failed: ' + name)
    required = set(freeze['files']) | {'freeze.json', 'analysis_freeze.json', 'semantic_extension_freeze.json'}
    required.update(p.name for p in ROOT.glob('*.py'))
    required.update({'README.md', 'DATA_CARD.md', 'EXECUTION_NOTES.md', 'SEMANTIC_CHALLENGE_PROTOCOL.md'})
    destination.mkdir(parents=True, exist_ok=False)
    for name in sorted(required):
        source = ROOT / name
        if source.is_file():
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    print('Created fresh workspace:', destination, flush=True)
    print('Archived responses, judgments, detector scans and run outcomes were not copied.', flush=True)
    commands = [
        [sys.executable, 'check_challenges.py'],
        [sys.executable, 'run_paired.py'],
        [sys.executable, 'judge_pairs.py'],
        [sys.executable, 'audit_challenges.py'],
        [sys.executable, 'summarize.py'],
        [sys.executable, 'fact_consensus.py'],
        [sys.executable, 'cost_summary.py'],
        [sys.executable, 'trace_summary.py'],
        [sys.executable, 'extract_failures.py'],
        [sys.executable, 'verify_results.py']
    ]
    if args.execute:
        for command in commands:
            print('Running:', ' '.join(command), flush=True)
            subprocess.run(command, cwd=destination, check=True, env={**os.environ, 'PYTHONUTF8': '1'})
        print('Generation and automated evaluation finished. Inspect summary.json for completion counts.', flush=True)
    else:
        print('Start the pinned local model and sign in to the review CLI, then run the scripts listed in README.md.', flush=True)
    print('Optional GPTZero scans: run scan_outputs.py --key-stdin in the new directory, then summarize.py.', flush=True)


if __name__ == '__main__':
    main()
