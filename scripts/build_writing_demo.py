"""Render the language-edit walkthrough from the exported real-run evidence."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'docs/natural-writing-evidence.json'
data = json.loads(source.read_text(encoding='utf-8'))
template = (ROOT / 'scripts/writing-demo.template.html').read_text(encoding='utf-8')
encoded = json.dumps(data, ensure_ascii=True, separators=(',', ':')).replace('<', '\\u003c')
(ROOT / 'docs/writing-demo.html').write_text(template.replace('__EVIDENCE__', encoded), encoding='utf-8')
print('Built docs/writing-demo.html from recorded evidence; no model calls.')
