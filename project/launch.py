from pathlib import Path
import argparse
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description='ProseLedger desktop launcher')
    parser.add_argument('action', choices=('open', 'setup', 'login', 'verify'), default='open', nargs='?')
    args = parser.parse_args()
    if sys.version_info < (3, 10):
        parser.error('Python 3.10 or later is required.')
    root = Path(__file__).resolve().parent
    for name in ('runs', 'runtime'):
        (root / name).mkdir(exist_ok=True)
    if args.action == 'open' and (root / 'runtime/models').is_dir():
        ready = subprocess.call([sys.executable, '-I', '-u', str(root / 'tools/local_qwen.py'),
                                 '--package', str(root), '--serve'], cwd=root)
        if ready:
            print('Local Qwen needs attention. The app can still use a hosted writer.', flush=True)
    commands = {
        'open': [str(root / 'app/server.py'), '--package', str(root)],
        'setup': [str(root / 'tools/local_qwen.py'), '--package', str(root), '--setup', '--ui'],
        'login': [str(root / 'tools/account_login.py'), str(root)],
        'verify': [str(root / 'tools/verify_package.py'), str(root)],
    }
    raise SystemExit(subprocess.call([sys.executable, '-I', '-u', *commands[args.action]], cwd=root))


if __name__ == '__main__':
    main()
