import {readFile,writeFile} from 'node:fs/promises';
import {ask,root,input} from './experiment_utils.mjs';
import {guardCandidate} from './guard.mjs';
const words=t=>(t.match(/\b[\p{L}\p{N}]+(?:[-'][\p{L}\p{N}]+)*\b/gu)||[]).length;
const labels=process.argv.length>2?process.argv.slice(2):['qwen_plain','qwen_contrastive'];
for(const label of labels){
 const data=JSON.parse(await readFile(new URL('dev_'+label+'.raw.json',root),'utf8'));
 if(data.records.length!==6)throw new Error('Not all sections generated');
 const audit=await ask('dev_'+label+'_audit',`Independently audit each proposed section edit against its original and the full manuscript. Approve only if it preserves all substantive claims, method steps, comparisons, evaluation measures, limitations, uncertainty, attribution, and proposal status. Reject dropped facts, new unsupported claims, turning a proposed system into a claimed accomplishment, changed citation meanings, awkward phrasing or incoherence. Tolerate ordinary wording changes. The model's own claim of equivalence does not count. Return {reviews:[{id:number,approve:boolean,issues:[{originalQuote,revisedQuote,problem}],readability:"better|similar|worse"}]}. Include each supplied section ID exactly once.`,{original:input.text,sources:input.sources,sections:data.records.map(r=>({id:r.id,heading:r.heading,original:r.original,candidate:r.text}))});
 const ids=new Set(audit.reviews.map(r=>r.id));if(ids.size!==6||audit.reviews.length!==6||data.records.some(r=>!ids.has(r.id)))throw new Error('Incomplete audit');
 const selected=data.records.map(r=>{const review=audit.reviews.find(x=>x.id===r.id);const refs=t=>JSON.stringify([...t.matchAll(/\[S\d+\]/g)].map(x=>x[0]).sort());const citations=refs(r.original)===refs(r.text);const ratio=words(r.text)/words(r.original);const accepted=r.finished&&review.approve===true&&review.issues?.length===0&&review.readability!=='worse'&&citations&&ratio>=.65&&ratio<=1.5&&!/^## /m.test(r.text);return {...r,review,citations,accepted,retained:accepted?r.text:r.original};});
 let text=input.text.split('\n')[0]+'\n\n'+selected.map(r=>'## '+r.heading+'\n\n'+r.retained).join('\n\n');const ratio=words(text)/words(input.text),guard=guardCandidate(input.text,text,input.sources);
 const finalGate=guard.passed&&ratio>=.85&&ratio<=1.15;
 await writeFile(new URL('dev_'+label+'.checks.json',root),JSON.stringify({method:label,selected,wordRatio:ratio,guard,finalGate,acceptedSections:selected.filter(r=>r.accepted).length},null,2));
 if(!finalGate)text=input.text;
 await writeFile(new URL('dev_'+label+'.md',root),text);console.log(label,{finalGate,accepted:selected.filter(r=>r.accepted).length,ratio});
 const fullAudit=await ask('dev_'+label+'_full_audit',`Review the complete revision against the original and evidence. Are any substantive claims, operations, comparisons, measures, limitations, source attributions or qualifications lost or changed? Does planned work appear completed? Are edited and original sections coherent together? Return {contentPreserved:boolean,issues:[{originalQuote,revisedQuote,problem}],readability:"better|similar|worse",reason:string}. Ignore provenance and detector scores.`,{original:input.text,sources:input.sources,candidate:text});
 await writeFile(new URL('dev_'+label+'.full_audit.json',root),JSON.stringify(fullAudit,null,2));console.log(label,fullAudit);
}
