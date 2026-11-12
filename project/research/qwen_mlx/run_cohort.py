"""Re-run one archived cohort from its frozen inputs into a new output directory."""
from pathlib import Path
import argparse,json,os,subprocess,sys

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--cohort',choices=['heldout','confirmation'],required=True)
 parser.add_argument('--out',type=Path,required=True,help='New directory; archived evidence is never overwritten')
 parser.add_argument('--node',default='node')
 parser.add_argument('--with-targeted',action='store_true',help='Also make fresh hosted Targeted control calls from each same frozen manuscript')
 args=parser.parse_args();here=Path(__file__).resolve().parent
 output=args.out.resolve();output.mkdir(parents=True,exist_ok=False)
 policy='section' if args.cohort=='heldout' else 'full-audit'
 env={**os.environ,'PROSELEDGER_PYTHON':sys.executable};records=[]
 for case in sorted((here/'archive'/args.cohort).glob('case*')):
  destination=output/case.name;destination.mkdir()
  if args.with_targeted:subprocess.run([args.node,str(here/'run_targeted.mjs'),'--input',str(case/'dev_input.json'),'--out',str(destination/'targeted')],env=env,check=True)
  subprocess.run([sys.executable,str(here/'run_revision.py'),'--input',str(case/'dev_initial.md'),'--sources',str(case/'dev_input.json'),'--topic',json.loads((case/'dev_input.json').read_text())['topic'],'--out',str(destination/'qwen'),'--policy',policy,'--node',args.node],env=env,check=True)
  records.append({'case':case.name,'policy':policy,'run':str(Path(case.name)/'qwen/run.json')})
  (output/'cohort.json').write_text(json.dumps({'cohort':args.cohort,'policy':policy,'freshTargetedControl':args.with_targeted,'detectorUsed':False,'runs':records},indent=2))
 print('Saved fresh runs to',output)
if __name__=='__main__':main()
