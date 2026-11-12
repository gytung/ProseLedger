"""Build a checksum manifest for the distributed source."""
import hashlib
import json
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
files = {}
for p in sorted(root.rglob('*')):
    relative = p.relative_to(root)
    if not p.is_file() or p.name == 'PACKAGE_MANIFEST.json':
        continue
    if relative.parts[0] in ('runs', 'runtime'):
        continue
    if any(part in ('__pycache__', '.git', '.venv', '.qwen-env', 'node_modules', 'test-results', 'playwright-report') for part in relative.parts):
        continue
    if p.suffix == '.pyc' or p.name == '.DS_Store' or p.name.startswith('.env'):
        continue
    files[relative.as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
(root / 'PACKAGE_MANIFEST.json').write_text(json.dumps({
    'format': 'proseledger-package-manifest',
    'platforms': ['Windows 10 22H2 / 11 x86_64', 'macOS 14+ arm64 / x86_64'],
    'files': files,
}, indent=2), encoding='utf-8')
print('Manifest files:', len(files))
