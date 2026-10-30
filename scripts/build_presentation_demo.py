"""Build a self-contained recording view from the frozen evaluation record."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = json.loads((ROOT / 'docs/evidence.json').read_text(encoding='utf-8'))
case = source['cases'][1]
assert case['id'] == '02'
data = {
    'schema': 'proseledger-recording-1',
    'mode': 'Recorded model outputs; no new model calls',
    'case': case,
    'card': next(c for c in source['cards'] if c['id'] == 'existing_comparison'),
    'summary': source['summary'],
    'protocol': source['protocol'],
    'source_contract_hash': source['source_contract_hash'],
    'cases': [dict(id=c['id'], theme=c['theme'], initial=c['initial']['score'],
                   finals={k:b['score'] for k,b in c['branches'].items()},
                   rounds={k:[c['initial']['score']]+[r['retained_score'] for r in b['rounds']]
                           for k,b in c['branches'].items()}, outcome=c['memory_vs_targeted'])
              for c in source['cases']],
}
template = (ROOT / 'scripts/presentation.template.html').read_text(encoding='utf-8')
encoded = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
(ROOT / 'docs/presentation.html').write_text(template.replace('__EVIDENCE_JSON__', encoded), encoding='utf-8')
print('Built docs/presentation.html from docs/evidence.json')
