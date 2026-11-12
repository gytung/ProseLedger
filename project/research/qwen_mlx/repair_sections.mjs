import {readFile,writeFile} from 'node:fs/promises';
import {ask,root,input} from './experiment_utils.mjs';
import {guardCandidate} from './guard.mjs';
const labels=process.argv.length>2?process.argv.slice(2):['qwen_plain','qwen_contrastive'];
const words=t=>(t.match(/\b[\p{L}\p{N}]+(?:[-'][\p{L}\p{N}]+)*\b/gu)||[]).length;
for(const label of labels){
 const raw=JSON.parse(await readFile(new URL('dev_'+label+'.raw.json',root),'utf8'));
 const checks=JSON.parse(await readFile(new URL('dev_'+label+'.checks.json',root),'utf8'));
 const needRepair=checks.selected.filter(r=>!r.accepted&&r.finished&&r.review.issues.length>0&&r.review.issues.length<=3);
 const response=await ask('dev_'+label+'_minimal_repairs',`Repair only the specified independently detected scientific or grammatical problems. Keep the candidate's wording everywhere else. Return {sections:[{id:number,patches:[{before:"exact unique substring in candidate",after:"replacement",issueIndex:0}],reason:string}]}. Include every supplied section exactly once. At most three patches per section. Total matched before text must be at most 35 percent of that section's candidate characters. Do not rewrite the section or make a second style pass. Each patch must address one listed issue and be supported by the original. Preserve uncertainty and planned-work status. No additional research claims. If a local repair cannot fix the issues, return patches=[] and explain. This is not an opportunity to improve a detector score.`,{sections:needRepair.map(r=>({id:r.id,original:r.original,candidate:r.text,issues:r.review.issues})),sources:input.sources});
 const records=raw.records.map(r=>{const orig=checks.selected.find(s=>s.id===r.id);if(orig.accepted)return {...r,text:orig.retained,repairApplied:false};const item=response.sections.find(s=>s.id===r.id);const patches=item?.patches||[];let text=r.text;let valid=patches.length>0&&patches.length<=3;const intervals=[];
 for(const patch of patches){const start=text.indexOf(patch.before);if(typeof patch.before!=='string'||!patch.before||typeof patch.after!=='string'||start<0||text.indexOf(patch.before,start+1)!==-1||!Number.isInteger(patch.issueIndex)||patch.issueIndex<0||patch.issueIndex>=orig.review.issues.length){valid=false;break;}intervals.push({start,end:start+patch.before.length,...patch});}
 intervals.sort((a,b)=>a.start-b.start);if(intervals.some((r,i)=>i>0&&r.start<intervals[i-1].end)||intervals.reduce((n,p)=>n+p.before.length,0)>.35*text.length)valid=false;
 if(valid)for(const patch of [...intervals].reverse())text=text.slice(0,patch.start)+patch.after+text.slice(patch.end);
 return {...r,text:valid?text:orig.retained,repairApplied:valid,repairRecord:item||null,preRepairText:r.text};});
 let text=input.text.split('\n')[0]+'\n\n'+records.map(r=>'## '+r.heading+'\n\n'+r.text).join('\n\n');
 const audit=await ask('dev_'+label+'_repair_audit',`Independently verify this full revision against the original and evidence. Return {contentPreserved:boolean,issues:[{section,originalQuote,revisedQuote,problem}],readability:"better|similar|worse",reason:string}. Check ALL scientific propositions, qualifications, source relations, method operations and planned evaluation details, not just listed repairs. Do not use detector scores. The writer's own preservation assurances are not evidence.`,{original:input.text,sources:input.sources,candidate:text});
 const guard=guardCandidate(input.text,text,input.sources),ratio=words(text)/words(input.text);const eligible=guard.passed&&ratio>=.85&&ratio<=1.15&&audit.contentPreserved===true&&audit.issues.length===0&&audit.readability!=='worse';
 await writeFile(new URL('dev_'+label+'_repaired.md',root),text);await writeFile(new URL('dev_'+label+'_repaired.checks.json',root),JSON.stringify({records,wordRatio:ratio,guard,audit,eligible,repairBounds:{maxPatchesPerSection:3,maxCandidateFraction:.35}},null,2));console.log(label,{eligible,ratio,repairs:records.filter(r=>r.repairApplied).length,audit});
}
