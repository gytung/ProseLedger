/** Bounded repair of full-document audit findings. No detector feedback is used. */
import {readFile,writeFile} from 'node:fs/promises';
import {ask,root,input} from './experiment_utils.mjs';
import {guardCandidate} from './guard.mjs';
import {applyBoundedPatches} from './bounded_patches.mjs';
const label=process.argv[2]||'qwen_plain';
const base=JSON.parse(await readFile(new URL('dev_'+label+'_repaired.checks.json',root),'utf8'));
const title=input.text.split('\n')[0];
let records=base.records.map(r=>({...r})), audit=base.audit;
const history=[];
const assemble=()=>title+'\n\n'+records.map(r=>'## '+r.heading+'\n\n'+r.text).join('\n\n');
const wc=t=>(t.match(/\b[\p{L}\p{N}]+(?:[-'][\p{L}\p{N}]+)*\b/gu)||[]).length;
for(let round=1;round<=2;round++) {
  if(audit.contentPreserved===true&&audit.issues.length===0) break;
  if(!Array.isArray(audit.issues)||audit.issues.length===0||audit.issues.length>6) break;
  const grouped=records.map(r=>({id:r.id,heading:r.heading,original:r.original,candidate:r.text,issues:audit.issues.filter(i=>i.section===r.heading)})).filter(r=>r.issues.length);
  if(grouped.reduce((n,r)=>n+r.issues.length,0)!==audit.issues.length) break;
  const request=await ask('dev_'+label+'_closure_patch_'+round,
    'Repair only the listed full-document audit findings. Return {sections:[{id:number,patches:[{before:string,after:string,issueIndex:number}],reason:string}]}. Use exact unique substrings from the candidate. Each issueIndex refers to the issues in that section. At most 3 patches per section; their combined matched text must cover at most 35% of that candidate section. Keep wording elsewhere unchanged. Restore the original scope, uncertainty, evidence relationship, procedural detail, and planned-work status. Do not introduce facts or improve style. If bounded repairs cannot fix all findings in a section, return patches:[] for it. Include each supplied section once.',
    {sections:grouped,sources:input.sources});
  const changes=[];
  for(const group of grouped) {
    const matches=request.sections?.filter(s=>s.id===group.id)||[];
    if(matches.length!==1) {changes.push({id:group.id,ok:false,reason:'response_ids'});continue;}
    const applied=applyBoundedPatches(group.candidate,matches[0].patches,group.issues.length);
    changes.push({id:group.id,...applied});
    if(applied.ok) records.find(r=>r.id===group.id).text=applied.text;
  }
  if(!changes.some(r=>r.ok)) {history.push({round,auditBefore:audit,changes,stopped:'no_valid_patch'});break;}
  const previous=audit;
  audit=await ask('dev_'+label+'_closure_audit_'+round,
    'Independently verify this full revision against the original and evidence. Return {contentPreserved:boolean,issues:[{section,originalQuote,revisedQuote,problem}],readability:"better|similar|worse",reason:string}. Check ALL scientific propositions, qualifications, source relations, method operations and planned evaluation details. Section must be one of the exact supplied headings. Equivalent paraphrases are allowed; identify concrete meaning changes with quotations. Do not use detector scores or trust a writer\'s preservation assurances.',
    {original:input.text,sources:input.sources,sectionHeadings:records.map(r=>r.heading),candidate:assemble()});
  history.push({round,auditBefore:previous,changes,auditAfter:audit});
}
const text=assemble(),guard=guardCandidate(input.text,text,input.sources),ratio=wc(text)/wc(input.text);
const eligible=guard.passed&&ratio>=.85&&ratio<=1.15&&audit.contentPreserved===true&&audit.issues.length===0&&audit.readability!=='worse';
await writeFile(new URL('dev_'+label+'_closed.md',root),text);
await writeFile(new URL('dev_'+label+'_closed.checks.json',root),JSON.stringify({eligible,wordRatio:ratio,guard,audit,history,records,detectorUsedForSelection:false,bounds:{maxRounds:2,maxPatchesPerSection:3,maxMatchedFraction:.35}},null,2));
console.log(JSON.stringify({label,eligible,rounds:history.length,ratio,audit}));
