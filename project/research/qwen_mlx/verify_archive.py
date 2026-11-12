"""Verify archived file fingerprints, submitted text and reported cohort means offline."""
from pathlib import Path
import hashlib,json,math
ROOT=Path(__file__).resolve().parent

def digest(data):return hashlib.sha256(data).hexdigest()
def main():
 manifest=json.loads((ROOT/'SOURCE_MANIFEST.json').read_text())
 failures=[]
 for item in manifest['files']:
  path=ROOT/item['file']
  if not path.is_file() or digest(path.read_bytes())!=item['packagedSHA256']:failures.append('File fingerprint: '+item['file'])
 detectors=[]
 for file in sorted((ROOT/'archive').rglob('*.gptzero.json')):
  record=json.loads(file.read_text());text=file.with_suffix('.md')
  # with_suffix removes .json; detector files have a double suffix.
  text=file.with_name(file.name.replace('.gptzero.json','.md'))
  if not text.exists():failures.append('Missing submitted text: '+str(text));continue
  submitted=text.read_text(encoding='utf-8')
  if digest(submitted.encode())!=record['textSHA256']:failures.append('Submitted-text fingerprint: '+str(file))
  raw=record['raw']['documents'][0]
  if raw.get('inputText')!=submitted:failures.append('Detector input differs: '+str(file))
  detectors.append({'file':str(file.relative_to(ROOT)),'sha256':record['textSHA256'],'ai':raw['class_probabilities']['ai'],'class':raw['predicted_class']})
 cohorts={}
 for name in ['heldout','confirmation']:
  summary=json.loads((ROOT/'archive'/f'{name}_summary.json').read_text())
  values=[];outcomes=[]
  for row in summary['rows']:
   folder=ROOT/'archive'/name/row['case'];pair=[]
   for field,stem in [('targeted','dev_targeted'),('new','dev_candidate')]:
    scan=json.loads((folder/(stem+'.gptzero.json')).read_text());prob=scan['raw']['documents'][0]['class_probabilities']['ai'];pair.append(prob)
    if abs(prob-row[field]['ai'])>1e-12 or scan['textSHA256']!=row[field]['sha256']:failures.append('Summary/scan mismatch: '+name+'/'+row['case']+'/'+field)
   values.append(pair);outcomes.append('lower' if pair[1]<pair[0] else 'higher' if pair[1]>pair[0] else 'unchanged')
  mean=sum(r[1] for r in values)/len(values)
  if abs(mean-summary['newMean'])>1e-12:failures.append('Mean mismatch: '+name)
  cohorts[name]={'n':len(values),'targetedMean':sum(r[0] for r in values)/len(values),'newMean':mean,'lower':outcomes.count('lower'),'unchanged':outcomes.count('unchanged'),'higher':outcomes.count('higher')}
 report={'scope':'Offline integrity and accounting only; no fresh model or detector execution','sourceFilesVerified':len(manifest['files']),'detectorInputsVerified':len(detectors),'cohorts':cohorts,'failures':failures}
 print(json.dumps(report,indent=2));return 1 if failures else 0
if __name__=='__main__':raise SystemExit(main())
