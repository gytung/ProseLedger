"""Interactive official API client; credentials exist only in this process memory."""
import getpass,hashlib,json,sys,time,argparse
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input-root',type=Path,default=Path(__file__).resolve().parent,help='Only files inside this directory may be submitted')
args=parser.parse_args();ROOT=args.input_root.resolve()
if not ROOT.is_dir():parser.error('--input-root must be an existing directory')
KEY=getpass.getpass('GPTZero key (not saved): ')
print('READY: submit {"path": "...", "label": "..."}; empty line quits.',flush=True)
count=0
for line in sys.stdin:
 if not line.strip():break
 try:
  task=json.loads(line);path=Path(task['path']).resolve()
  if ROOT not in path.parents:raise ValueError('Input must be within --input-root')
  text=path.read_text(encoding='utf-8')
  if len(text)<250:raise ValueError('Text too short')
  if count>=24:raise ValueError('Session scan limit reached')
  body=json.dumps({'document':text}).encode()
  req=Request('https://api.gptzero.me/v2/predict/text',data=body,headers={'Content-Type':'application/json','x-api-key':KEY,'User-Agent':'ProseLedger-Research/1.0'})
  start=time.monotonic()
  with urlopen(req,timeout=90) as response:raw=json.load(response)
  count+=1
  output={'label':task['label'],'textSHA256':hashlib.sha256(text.encode()).hexdigest(),'characters':len(text),'requestVersion':'provider-default-returned-version-recorded','elapsedSeconds':round(time.monotonic()-start,2),'raw':raw}
  dest=path.with_suffix('.gptzero.json');dest.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
  doc=raw.get('documents',[{}])[0]
  print(json.dumps({'scan':count,'label':task['label'],'class':doc.get('predicted_class'),'probabilities':doc.get('class_probabilities'),'confidence':doc.get('confidence_category'),'version':raw.get('version'),'output':str(dest)}),flush=True)
 except HTTPError as e:print(json.dumps({'error':'GPTZero HTTP '+str(e.code),'detail':e.read().decode('utf-8',errors='replace').replace(KEY,'[redacted]')[:350]}),flush=True)
 except Exception as e:print(json.dumps({'error':type(e).__name__+': '+str(e)[:180]}),flush=True)
KEY=''
