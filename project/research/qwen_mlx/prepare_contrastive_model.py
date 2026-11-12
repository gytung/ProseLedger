import json,os
from pathlib import Path
os.environ['HF_HUB_DISABLE_XET']='1'
from huggingface_hub import snapshot_download
p=Path(__file__).resolve().parent;s=json.loads((p/'contrastive_model_source.json').read_text()); print('Downloading',s['repo'],s['sha'],flush=True)
folder=snapshot_download(repo_id=s['repo'],revision=s['sha'],allow_patterns=['*.json','*.txt','*.safetensors'],max_workers=2)
(p/'contrastive_model_path.json').write_text(json.dumps({'path':folder,**s},indent=2));print('Model ready',flush=True)
