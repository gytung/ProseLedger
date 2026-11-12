"""Run the tested section-rewrite and bounded-repair policy on a new manuscript.

MLX inference requires Apple Silicon. This runner never uses
GPTZero scores to select a candidate. Each output directory is created once so
that a new run cannot overwrite the archived evaluation evidence.
"""
from pathlib import Path
import argparse,subprocess,json,os,sys,hashlib,shutil,datetime,re

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--input',required=True,type=Path,help='Full proposal Markdown with the six standard sections')
 ap.add_argument('--sources',required=True,type=Path,help='JSON list of source objects, or an object with a sources field')
 ap.add_argument('--out',required=True,type=Path,help='A NEW output directory')
 ap.add_argument('--topic',default='Evidence-preserving scientific proposal revision')
 ap.add_argument('--node',default='node',help='Node.js executable')
 ap.add_argument('--policy',choices=['section','full-audit'],default='section',help='section reproduces the four-case policy; full-audit enables the two-case refinement')
 args=ap.parse_args();study=Path(__file__).resolve().parent
 if not (study/'contrastive_model_path.json').exists():ap.error('Run prepare_contrastive_model.py first in the configured MLX environment.')
 if not shutil.which(args.node) and not Path(args.node).is_file():ap.error('Node.js was not found; supply --node or install Node.js 20+.')
 text=args.input.read_text(encoding='utf-8');sources=json.loads(args.sources.read_text(encoding='utf-8'))
 if isinstance(sources,dict):sources=sources.get('sources')
 if not isinstance(sources,list) or not sources:ap.error('--sources must contain a nonempty source list.')
 expected=['Abstract','Introduction','Related Work','Methodology','Planned Evaluation','Limitations and Conclusion']
 if re.findall(r'^## (.+)$',text,re.M)!=expected:ap.error('Input must contain the six standard sections in order: '+', '.join(expected))
 out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
 (out/'dev_initial.md').write_text(text);(out/'dev_input.json').write_text(json.dumps({'topic':args.topic,'sources':sources,'text':text,'cards':[]},ensure_ascii=False,indent=2))
 env={**os.environ,'PROSELEDGER_CASE_DIR':str(out),'PROSELEDGER_VARIANTS':'qwen_plain','PROSELEDGER_PYTHON':sys.executable}
 stages=[('Rewrite sections',[sys.executable,str(study/'contrastive_transfer.py')]),('Audit sections',[args.node,str(study/'audit_contrastive.mjs'),'qwen_plain']),('Repair and verify',[args.node,str(study/'repair_sections.mjs'),'qwen_plain'])]
 if args.policy=='full-audit':stages.append(('Resolve remaining audit findings',[args.node,str(study/'repair_final_audit.mjs'),'qwen_plain']))
 prefix='dev_qwen_plain_closed' if args.policy=='full-audit' else 'dev_qwen_plain_repaired'
 try:
  for i,(label,cmd) in enumerate(stages,1):
   print(f'{i}/{len(stages)} {label}',flush=True)
   with (out/f'stage_{i}.log').open('w') as log:subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
  checks=json.loads((out/(prefix+'.checks.json')).read_text());eligible=checks['eligible'];selected=out/(prefix+'.md' if eligible else 'dev_initial.md')
  final=selected.read_text();(out/'proposal.md').write_text(final)
  record={'createdAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'completed','newCandidateAccepted':eligible,'retained':'repaired_candidate' if eligible else 'original','textSHA256':hashlib.sha256(final.encode()).hexdigest(),'detectorUsedForSelection':False,'auditIsAutomated':True,'checksFile':prefix+'.checks.json','policy':args.policy}
  (out/'run.json').write_text(json.dumps(record,indent=2))
  ledger={'scope':'This run only; records are not automatically evidence of general reuse benefit','sourceTextSHA256':hashlib.sha256(text.encode()).hexdigest(),'retainedTextSHA256':record['textSHA256'],'detectorUsedForAdmission':False,'fullAudit':checks['audit'],'edits':[{'section':r['heading'],'before':r['original'],'candidate':r['text'],'retained':r['text'] if eligible else r['original'],'status':'verified_edit' if eligible and r['text']!=r['original'] else 'unchanged_or_rejected'} for r in checks['records']],'repairHistory':checks.get('history',[])}
  (out/'revision_ledger.json').write_text(json.dumps(ledger,indent=2));print(json.dumps(record,indent=2));print('Output:',out/'proposal.md')
 except Exception as e:
  (out/'proposal.md').write_text(text)
  (out/'run.json').write_text(json.dumps({'status':'failed','error':str(e),'retained':'original','textSHA256':hashlib.sha256(text.encode()).hexdigest()},indent=2))
  print('Run failed; original retained. See stage logs.',file=sys.stderr);raise
if __name__=='__main__':main()
