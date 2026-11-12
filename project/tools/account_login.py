"""Open the user's official model-account login flow."""
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / 'app'))
from transport import Client

try:
    executable = Client({'mode': 'codex'}, root).executable()
except ValueError as exc:
    print(str(exc))
    print('Official CLI setup: https://developers.openai.com/codex/cli/')
    print('Alternatively, choose API mode in the app; no CLI is required.')
    raise SystemExit(1)
raise SystemExit(subprocess.call([executable, 'login']))
