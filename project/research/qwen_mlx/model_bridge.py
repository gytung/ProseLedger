import json,sys,os
from pathlib import Path
from _review.codex_client import CodexCLIModel, CodexCLIError
payload=json.load(sys.stdin)
model_id=payload.get('model','gpt-6.1-sol')
explicit=os.environ.get('PROSELEDGER_CODEX_PATH')
model=CodexCLIModel(name=payload['stage'],model=model_id,executable=explicit,timeout=240)
r=model.invoke(payload['messages'])
print(json.dumps({'text':r.content,'usage':r.response_metadata,'requestedModel':model_id},ensure_ascii=False))
