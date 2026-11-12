"""Check package integrity and the included input without making model calls."""
import ast
import hashlib
import json
import platform
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
manifest = json.loads((root / 'PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))
errors = []
for name, expected in manifest['files'].items():
    path = root / name
    if not path.is_file():
        errors.append('Missing: ' + name)
    elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        errors.append('Changed: ' + name)
for path in (root / 'app').glob('*.py'):
    ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
sys.path.insert(0, str(root / 'app'))
from core import guard, split_sections, validate_sources

sample = json.loads((root / 'examples/example.json').read_text(encoding='utf-8'))
validate_sources(sample['sources'])
split_sections(sample['text'])
assert guard('', sample['text'], sample['sources'])['passed']
print('Python:', platform.python_version())
print('Host:', platform.system(), platform.machine())
print('Checked package files:', len(manifest['files']))
if errors:
    print('\n'.join(errors))
    raise SystemExit(1)
print('Package integrity and included-input checks passed. No model call was made.')
