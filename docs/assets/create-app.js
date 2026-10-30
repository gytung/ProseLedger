import { PRESETS, providerEndpoint, createModelClient } from './api-client.js?v=20261030d';
import { runProposal } from './browser-engine.js?v=20261030b';
import { createCheckpoint, restoreCheckpoint, CHECKPOINT_MAX_BYTES } from './run-checkpoint.js?v=20261030d';

const $ = id => document.getElementById(id);
const names = {initial:'Initial draft',targeted:'Targeted',planner:'Planner-only',memory:'Memory'};
const methods = ['targeted','planner','memory'];
const colors = {targeted:'#6c98af',planner:'#7e9874',memory:'#9b76ba'};
let defaults,result,client,controller,ticker,started,session;
let selected='initial', selectedRound='final', running=false, generating=false;
let importedRun=false,pendingComparison=false;
let usage=[],events=[],statuses=new Map(),logicalDone=new Set(),cacheHits=0,attempts=0;
const text = value => typeof value==='string' ? value : value==null ? '' : JSON.stringify(value);
const isFailure = row => ['execution_failure','generation_failed','review_failed'].includes(row.outcome);
const score = value => Number.isFinite(value) ? Number(value).toFixed(1) : '—';
function element(tag,content,className) { const n=document.createElement(tag);if(content!==undefined)n.textContent=content;if(className)n.className=className;return n; }
function showError(message) {$('error-panel').hidden=false;$('error-message').textContent=message;$('error-panel').scrollIntoView?.({behavior:'smooth',block:'center'});}
function clearSecret() {client?.clear();$('api-key').value='';}
function changeConnection() {
  if(running)return;clearSecret();$('consent').checked=false;
  $('connection-status').textContent='A connection test makes one small API call.';
  try {$('connection-destination').textContent=providerEndpoint($('api-base').value);}
  catch {$('connection-destination').textContent='Enter a valid public HTTPS API URL.';}
  if($('provider-preset').value==='custom')$('endpoint-settings').open=true;
  updateReadiness();
}
function serializeSources(sources) {return sources.map(s=>`[${s.id}] ${s.title}\n${s.excerpt}`).join('\n\n');}
function sourceInput() {
  const notes=$('source-notes').value.trim();if(notes.length>31000)throw new Error('Source notes are too long; keep combined excerpts within 24,000 characters.');
  const markers=[...notes.matchAll(/^\[(S\d+)\]\s+(.+)$/gm)];
  if(markers.length<2||markers.length>10||markers[0]?.index!==0)throw new Error('Supply 2–10 notes, each beginning with [S1] Title, [S2] Title, and so on.');
  const sources=markers.map((m,i)=>{const excerpt=notes.slice(m.index+m[0].length,markers[i+1]?.index??notes.length).trim();const original=defaults.sources.find(s=>s.id===m[1]&&s.title===m[2].trim()&&s.excerpt===excerpt);return original?structuredClone(original):{id:m[1],title:m[2].trim(),excerpt,provenance:'Visitor-supplied source note; not independently verified.'};});
  if(new Set(sources.map(s=>s.id)).size!==sources.length)throw new Error('Each source needs a unique [S#] ID.');
  if(sources.some(s=>s.excerpt.length<80||s.excerpt.length>4000))throw new Error('Each source excerpt must contain 80–4,000 characters.');
  if(sources.reduce((n,s)=>n+s.excerpt.length,0)>24000)throw new Error('The combined excerpts exceed 24,000 characters.');return sources;
}
function loadExample() {if(!defaults||running)return;$('topic').value=defaults.topic;$('source-notes').value=serializeSources(defaults.sources);updateReadiness();}
function canResume() {return Boolean(session&&result&&result.status!=='completed');}
function canCompare() {const stages=new Set([...(session?.cache?.values()||[])].map(r=>r.stage));return Boolean(session&&result?.status==='completed'&&session.snapshot.mode==='draft'&&result.initialText&&stages.has('draft')&&stages.has('audit_initial'));}
function updateReadiness() {
  if(!defaults)return;
  let issue='';try{const sources=sourceInput();$('input-summary').textContent=`${sources.length} sources · ${sources.reduce((n,s)=>n+s.excerpt.length,0).toLocaleString()} evidence characters · ready`;$('input-summary').className='input-summary ready';}catch(error){issue=error.message;$('input-summary').textContent=issue;$('input-summary').className='input-summary needs-attention';}
  const topic=$('topic').value.trim();if(topic.length<10)issue='Describe your research question in at least 10 characters.';
  try{providerEndpoint($('api-base').value);}catch{issue='Enter a valid provider endpoint under Advanced settings.';}
  if(!$('api-model').value.trim())issue='Enter the model ID from your provider.';
  if(!$('api-key').value.trim())issue='Add your API key to begin. Your sources are kept in this tab.';
  else if(!$('consent').checked)issue='Confirm API usage to enable a paid model run.';
  $('readiness-summary').textContent=running?'Run in progress. Completed steps can be saved as a checkpoint.':issue||($('generation-mode').value==='draft'?'Ready: generate and review one draft with 2 model calls.':'Ready: compare three routes from one common draft, with up to 14 model calls.');
  $('readiness-summary').className=`readiness-summary ${issue?'needs-attention':'ready'}`;
  $('generate').textContent=pendingComparison?'Compare this saved draft →':$('generation-mode').value==='draft'?'Generate draft →':'Generate and compare →';
  $('download-checkpoint').disabled=!session||!result;
  $('compare-draft').hidden=!canCompare();$('compare-draft').disabled=running;
}
function busy(value) {
  running=value;
  for(const id of ['provider-preset','api-base','api-model','api-key','topic','source-notes','source-upload','reset-inputs','generation-mode','consent','generate','test-connection','restore-run'])$(id).disabled=value;
  $('cancel').disabled=!value;$('resume').disabled=value;$('resume').hidden=!canResume();
  $('resume-hint').textContent=canResume()?'Unfinished run saved in this tab. Re-enter the original provider/model key and resume, or save a checkpoint before closing. Starting a new run replaces this workspace.':'Nothing is submitted until you start or test. Save a checkpoint before closing to keep the complete record.';
  updateReadiness();
}
function metrics() {
  $('call-count').textContent=String(usage.length);$('attempt-count').textContent=String(attempts);
  const known=usage.filter(u=>Number.isFinite(u.totalTokens));const tokens=known.reduce((n,u)=>n+u.totalTokens,0);
  $('token-count').textContent=known.length?`${tokens.toLocaleString()}${known.length<usage.length?' (partial)':''}`:'Not reported';
  const seconds=started?Math.floor((performance.now()-started)/1000):0;$('elapsed-time').textContent=`${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,'0')}`;
  $('progress-bar').value=logicalDone.size;$('cache-status').textContent=cacheHits?`${cacheHits} successful stage response(s) reused in this attempt. Reuse makes no new API request.`:'';
}
function statusEvent(event) {
  if(event.phase==='requesting')attempts++;
  statuses.set(event.stage,event);const active=[...statuses.values()].filter(e=>['queued','requesting','receiving','retrying'].includes(e.phase));
  $('stream-status').textContent=active.length?active.map(e=>`${stageName(e.stage)}: ${e.phase==='queued'?'queued to limit API load':e.phase==='retrying'?'waiting to retry':e.outputCharacters?`${e.outputCharacters.toLocaleString()} characters received`:e.phase==='receiving'?'provider active; preparing answer':'waiting for provider'}${e.attempt>1?` (attempt ${e.attempt})`:''}`).join(' · '):event.message||'No active request.';
  renderStages();metrics();
}
function stageName(stage) {if(stage==='draft')return 'Draft and outline';if(stage==='audit_initial')return 'Initial review';if(stage==='connection_test')return 'Connection test';const revision=/^revise_(targeted|planner|memory)_(\d)$/.exec(stage);if(revision)return `${names[revision[1]]} · round ${revision[2]}`;const review=/^review_round_(\d)$/.exec(stage);return review?`Blind review · round ${review[1]}`:stage.replaceAll('_',' ');}
function renderStages() {
  const list=$('stage-list');list.replaceChildren();
  for(const [stage,e] of statuses)list.append(element('li',`${stageName(stage)} · ${e.phase}`,e.phase==='completed'?'completed':e.phase==='cached'?'cached':['failed','cancelled','invalidated'].includes(e.phase)?'failed':'running'));
}
function markdownText(container,value) {
  container.replaceChildren();for(const block of text(value).split(/\n\s*\n/).filter(Boolean)) {const heading=/^(#{1,3})\s+(.+)$/.exec(block);container.append(element(heading?`h${Math.min(heading[1].length+1,4)}`:'p',heading?heading[2]:block));}
}
function blocks(value) {return text(value).split(/\n\s*\n/).filter(Boolean);}
function diffStats(before,after) {
  const a=text(before).match(/\S+/g)||[],b=text(after).match(/\S+/g)||[];
  const old=blocks(before),now=blocks(after);let changedParagraphs=0;
  for(let i=0;i<Math.max(old.length,now.length);i++)if(old[i]!==now[i]&&!/^#{1,3}\s/.test(now[i]||old[i]||''))changedParagraphs++;
  if(before===after)return {added:0,removed:0,changedParagraphs:0,words:b.length};
  // Bounded token LCS reports actual inserted/deleted tokens, not a quality score.
  if(a.length*b.length>4_000_000)return {added:null,removed:null,changedParagraphs,words:b.length};
  let prev=new Uint16Array(b.length+1),next=new Uint16Array(b.length+1);
  for(let i=1;i<=a.length;i++){for(let j=1;j<=b.length;j++)next[j]=a[i-1]===b[j-1]?prev[j-1]+1:Math.max(prev[j],next[j-1]);[prev,next]=[next,prev];next.fill(0);}
  return {added:b.length-prev[b.length],removed:a.length-prev[b.length],changedParagraphs,words:b.length};
}
function failedCount() {return Object.values(result?.branches||{}).reduce((n,b)=>n+b.rounds.filter(r=>isFailure(r)).length,0);}
function currentBranch() {return result?.branches?.[selected];}
function selectedRecord() {return currentBranch()?.rounds.find(r=>String(r.round)===selectedRound);}
function memoryEvidence(branch) {
  const rows=(branch?.rounds||[]).filter(r=>r.round>0&&(r.memoryApplications||[]).length);
  const retained=rows.filter(r=>r.accepted&&r.changed);
  const lower=retained.filter(r=>{const before=branch.rounds.find(x=>x.round===r.round-1)?.retainedScore;return Number.isFinite(before)&&r.retainedScore<before;});
  return {applied:rows.length,retained:retained.length,lower:lower.length};
}
function memorySummary(branch) {const m=memoryEvidence(branch);return `${m.applied} round(s) used a card · ${m.retained} card-guided edit round(s) retained · ${m.lower} also lowered the score. ${m.retained?'Retention shows this edit passed the checks, not that memory caused a gain over the other routes.':'No retained edit used an experience card; any retained improvement here cannot be credited to historical cards.'}`;}
function wordAlignment(before,after) {
  const a=[...before.matchAll(/\S+/g)],b=[...after.matchAll(/\S+/g)];
  const oldMatches=new Set(),newMatches=new Set();
  // Paragraph-sized traceback keeps exact original whitespace and punctuation.
  // Very large user paragraphs use the already-visible paragraph highlighting.
  if(a.length>600||b.length>600)return null;
  const width=b.length+1,grid=new Uint16Array((a.length+1)*width);
  for(let i=a.length-1;i>=0;i--)for(let j=b.length-1;j>=0;j--)grid[i*width+j]=a[i][0]===b[j][0]?1+grid[(i+1)*width+j+1]:Math.max(grid[(i+1)*width+j],grid[i*width+j+1]);
  let i=0,j=0;while(i<a.length&&j<b.length){if(a[i][0]===b[j][0]){oldMatches.add(i++);newMatches.add(j++);}else if(grid[(i+1)*width+j]>=grid[i*width+j+1])i++;else j++;}
  return {a,b,oldMatches,newMatches};
}
function highlightedParagraph(value,tokens,matched,kind) {
  const p=element('p',undefined,'diff-paragraph changed');let cursor=0,plain='';
  for(let k=0;k<tokens.length;k++){
    const token=tokens[k];plain+=value.slice(cursor,token.index);
    if(matched.has(k))plain+=token[0];else{if(plain){p.append(element('span',plain));plain='';}p.append(element(kind,token[0]));}
    cursor=token.index+token[0].length;
  }
  plain+=value.slice(cursor);if(plain)p.append(element('span',plain));if(!value)p.append(element('span','—'));return p;
}
function renderDiff(before,after) {
  const a=blocks(before),b=blocks(after);$('before-text').replaceChildren();$('after-text').replaceChildren();
  let section='Proposal',paragraph=0,omitted=0,shown=0;
  for(let i=0;i<Math.max(a.length,b.length);i++) {
    const old=a[i]??'',now=b[i]??'',heading=/^#{1,3}\s+(.+)$/.exec(old||now);
    if(heading){section=heading[1];continue;}
    paragraph++;
    if(old===now){omitted++;continue;}
    shown++;const alignment=wordAlignment(old,now);
    for(const [id,value,isOld]of[['before-text',old,true],['after-text',now,false]]){
      $(id).append(element('h4',`P${paragraph} · ${section}`));
      if(alignment)$(id).append(highlightedParagraph(value,isOld?alignment.a:alignment.b,isOld?alignment.oldMatches:alignment.newMatches,isOld?'del':'ins'));
      else $(id).append(element('p',value||'—','diff-paragraph changed'));
    }
  }
  if(!shown){$('before-text').append(element('p',a.length?'No paragraphs changed.':'The initial proposal will appear here.','diff-empty'));$('after-text').append(element('p',b.length?'The text is unchanged.':'Edits will appear after a candidate is prepared.','diff-empty'));}
  $('diff-context').textContent=shown?`Showing ${shown} changed paragraph pair(s); ${omitted} unchanged paragraph(s) omitted. Full retained and initial manuscripts remain below.`:'No changed paragraphs to compare. Full manuscripts remain below.';
}

function renderEdit() {
  if(!result)return;const branch=currentBranch(),r=selectedRecord();const explanation=$('edit-explanation');explanation.replaceChildren();
  let before=result.initialText||'',after=selected==='initial'?before:branch?.text||before;
  $('before-label').textContent='Initial draft';$('after-label').textContent=selected==='initial'?'Same initial draft':`${names[selected]} · retained output`;
  const state=$('candidate-state');state.className='candidate-state';
  if(r) {
    before=r.beforeText||before;after=r.candidateText??before;
    $('before-label').textContent=`Before round ${r.round} · retained draft`;
    $('after-label').textContent=`Round ${r.round} · ${r.candidateText?(r.accepted?'candidate retained':'candidate not retained'):'no candidate'}`;
    const sameCandidate=r.candidateText!==null&&r.candidateText!==undefined&&r.candidateText===before;
    const decision=isFailure(r)?'Invalid / failed candidate':r.route==='stop'?'No edit attempted':sameCandidate?'No textual change':r.accepted?'Candidate retained':'Candidate rejected';
    state.textContent=`${decision}. Candidate score ${score(r.candidateScore)}; retained score ${score(r.retainedScore)}. Blind before/after judgment: ${r.pairwise||'not available'}.`;
    if(!r.accepted&&r.route!=='stop')state.className+=' rejected';
    explanation.append(element('p',r.reason||'No reviewer explanation was recorded.'));
    for(const edit of r.edits||[])explanation.append(element('p',`${edit.paragraphId}: ${edit.reason||'Recorded local edit.'}`));
    for(const application of r.memoryApplications||[]) {
      const card=element('div',undefined,'memory-application');card.append(element('strong',`Memory applied: ${application.cardId}`),element('p',`Paragraphs: ${(application.paragraphIds||[]).join(', ')}. ${application.reason||''}`));if(application.conditionEvidence)card.append(element('blockquote',application.conditionEvidence));explanation.append(card);
    }
    if(selected==='memory'&&!(r.memoryApplications||[]).length)explanation.append(element('p','No historical card was applied in this round. This is recorded explicitly; ordinary feedback may still produce an edit.'));
  } else {
    const d=diffStats(before,after);state.textContent=selected==='initial'?'This is the common initial draft. Select a revision route to inspect its changes.':before===after?'The retained text is identical to the initial draft. This is a real tie in text, not evidence of an improvement.':`${d.changedParagraphs} paragraph(s) changed; ${d.added??'—'} words inserted and ${d.removed??'—'} removed compared with the initial draft. These counts measure editing activity, not writing quality.`;
    if(branch)explanation.append(element('p',`${branch.rounds.filter(r=>r.round>0&&r.accepted&&r.changed).length} revision round(s) with changes retained across ${branch.rounds.filter(r=>r.round>0).length} revision opportunities. Select a round to inspect the actual candidate and the reviewer’s reason.`));
    if(selected==='memory'&&branch)explanation.append(element('p',memorySummary(branch)));
  }
  renderDiff(before,after);
}
function displayBranch(method) {
  selected=method;const branch=currentBranch();if(selectedRound!=='final'&&!branch?.rounds.some(r=>String(r.round)===selectedRound))selectedRound='final';
  $('round-select').replaceChildren(element('option','Final retained output'));$('round-select').children[0].value='final';
  for(const r of branch?.rounds.filter(r=>r.round>0)||[]){const o=element('option',`Round ${r.round} · ${isFailure(r)?'failed':r.accepted?'retained':r.route==='stop'?'no edit':'rejected'}`);o.value=String(r.round);$('round-select').append(o);}
  $('round-select').value=selectedRound;$('round-select').disabled=!branch;
  for(const button of $('branch-tabs').children){const on=button.dataset.branch===selected;button.setAttribute('aria-selected',String(on));button.setAttribute('tabindex',on?'0':'-1');if(on)$('manuscript').setAttribute('aria-labelledby',button.id);}
  markdownText($('manuscript'),selected==='initial'?result.initialText:branch?.text);renderEdit();
}
function scoreTable(branches) {
  const table=element('table'),head=element('thead'),header=element('tr');['Retained score','R0','R1','R2','R3'].forEach(t=>header.append(element('th',t)));head.append(header);table.append(head);const body=element('tbody');
  for(const [method,branch] of Object.entries(branches)){const r=element('tr');r.append(element('th',names[method]));for(let k=0;k<=3;k++)r.append(element('td',score(branch.rounds.find(v=>v.round===k)?.retainedScore)));body.append(r);}table.append(body);return table;
}
function drawChart(branches) {
  const values=Object.values(branches).flatMap(b=>b.rounds.map(r=>r.retainedScore)).filter(Number.isFinite),zoom=$('zoom-scores').checked&&values.length;
  const low=zoom?Math.max(0,Math.floor((Math.min(...values)-.5)*2)/2):0,high=zoom?Math.min(20,Math.max(low+1,Math.ceil((Math.max(...values)+.5)*2)/2)):20;
  $('score-scale-note').textContent=zoom?`Zoomed axis: ${low.toFixed(1)}–${high.toFixed(1)}. The rating scale remains 0–20; zoom changes only the view, not the scores. R0 is the initial draft; R1–R3 are revision opportunities.`:'Full 0–20 axis. R0 is the initial draft; R1–R3 are revision opportunities. Flat scores alone do not show whether words changed or memory was useful.';
  const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 610 280');svg.setAttribute('role','img');svg.setAttribute('aria-label',`Retained problem scores, ${zoom?'zoomed':'full'} ${low} to ${high} axis, rounds zero to three`);
  const add=(tag,attrs,content)=>{const n=document.createElementNS(ns,tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);if(content!==undefined)n.textContent=content;svg.append(n);return n;};const x=k=>45+k*177,y=v=>230-(v-low)/(high-low)*190;
  for(let k=0;k<=4;k++){const v=low+(high-low)*k/4;add('line',{x1:45,y1:y(v),x2:580,y2:y(v),stroke:'#ece6f0'});add('text',{x:33,y:y(v)+4,'text-anchor':'end'},zoom?v.toFixed(2).replace(/0$/,''):v);}for(let k=0;k<=3;k++)add('text',{x:x(k),y:252,'text-anchor':'middle'},`R${k}`);
  Object.entries(branches).forEach(([method,branch],i)=>{const rows=branch.rounds.filter(r=>Number.isFinite(r.retainedScore));add('path',{d:rows.map((r,k)=>`${k?'L':'M'}${x(r.round)},${y(r.retainedScore)}`).join(' '),fill:'none',stroke:colors[method],'stroke-width':2.5,'stroke-dasharray':i===1?'7 4':i===2?'2 4':'none'});for(const r of rows){const circle=add('circle',{cx:x(r.round),cy:y(r.retainedScore),r:5-i,fill:'white',stroke:colors[method],'stroke-width':2});const title=document.createElementNS(ns,'title');title.textContent=`${names[method]} R${r.round}: ${score(r.retainedScore)}`;circle.append(title);}add('text',{x:45+i*180,y:20,class:`legend-${method}`,'font-weight':'bold'},names[method]);});return svg;
}
function displayResults() {
  if(!result)return;const branches=result.branches||{},failures=failedCount();$('results-panel').hidden=false;
  const draftOnly=session?.snapshot.mode==='draft',done=result.status==='completed';
  $('result-origin').textContent=importedRun?'Imported run record':'Your fresh result';
  $('results-intro').textContent=draftOnly?'A research proposal grounded in your supplied notes. Read the initial review, download the draft, or continue with three revision routes.':'Read the changes first. Three independent routes start from the same draft; every candidate is checked, including edits that are rejected. A higher-quality revision is not guaranteed.';
  $('results-heading').textContent=done?(draftOnly?'Your draft is ready. Choose what comes next.':'Read the writing. Inspect the decisions.'):result.status==='completed_with_errors'?'Comparison finished with incomplete candidates.':generating?'Work in progress. Completed steps appear below.':'Your completed work is saved here.';
  const origin=importedRun?'Imported checkpoint. This is a saved user record, not an independently verified evaluation. ':'';
  $('run-result-summary').textContent=origin+(failures?`${failures} invalid or unreviewed candidate(s) are visible below. The retained draft is carried forward at those steps; these are not successful revisions. Re-enter your key and resume to retry failed stages.`:done?draftOnly?'Draft and initial review complete. Read or download your proposal, or compare three revision routes using this exact draft. The two completed requests will be reused.':'Run complete. The scores, edits and manuscripts below belong to this run.':'Partial result: only completed stages are shown. Resume after checking the error, or save a checkpoint before closing.');
  $('download-manuscript').disabled=!result.initialText;$('copy-manuscript').disabled=!result.initialText;updateReadiness();
  const initialReview=$('initial-review');initialReview.replaceChildren();
  if(result.initialAudit){const table=element('table');for(const[key,value]of Object.entries(result.initialAudit.dimensions||{})){const row=element('tr');row.append(element('td',key.replaceAll('_',' ')),element('td',`${score(value.score)} / 4`),element('td',value.reason||'No separate issue recorded.'));table.append(row);}initialReview.append(table,element('p','These are expression ratings, not a check that the research design is complete. A low initial score leaves little room for numerical improvement.'));for(const issue of result.initialAudit.issues||[]){initialReview.append(element('p',`${issue.paragraphId}: ${issue.advice}`));if(issue.quote)initialReview.append(element('blockquote',issue.quote));}}
  else initialReview.append(element('p','The initial review has not completed. The generated draft remains available while you recover the missing step.'));
  const summary=$('branch-summary');summary.replaceChildren();
  for(const method of methods){const branch=branches[method];if(!branch)continue;const d=diffStats(result.initialText,branch.text),card=element('article',undefined,`branch-result ${method}`);
    const judged=branch.rounds.filter(r=>r.round>0&&typeof r.candidateText==='string'&&typeof r.beforeText==='string'&&r.candidateText!==r.beforeText&&['better','tie','worse'].includes(r.pairwise));
    const paired={better:0,tie:0,worse:0};for(const row of judged)paired[row.pairwise]++;
    card.append(element('h3',names[method]),element('p',judged.length?`${paired.better} preferred`:'No changed candidate reviewed','branch-verdict'));
    card.append(element('p',`${paired.better} better · ${paired.tie} tied · ${paired.worse} worse\nAgainst this route’s previous draft: all changed candidates, including rejected edits.`,'branch-review'));
    card.append(element('p',`Problem severity ${score(result.initialScore)} → ${score(branch.finalScore)}`,'branch-score'));
    const count=branch.rounds.filter(r=>r.round>0&&r.accepted&&r.changed).length;card.append(element('p',`${count} revision round(s) with changes retained\n${d.changedParagraphs} paragraph(s) differ from the initial\n${d.added??'—'} words added · ${d.removed??'—'} removed\n${branch.text===result.initialText?'Same final text as initial':'Final text differs from initial'}`,'branch-stats'));
    if(branch.text!==result.initialText&&branch.finalScore===result.initialScore)card.append(element('p','Writing changed; the absolute score stayed flat. Inspect paired reviews and highlighted edits.','branch-flat-note'));
    if(method==='memory')card.append(element('p',memorySummary(branch),'branch-memory-note'));
    const button=element('button','Inspect edits','button secondary');button.type='button';button.addEventListener('click',()=>{selectedRound='final';displayBranch(method);$('edit-panel').scrollIntoView?.({behavior:'smooth',block:'start'});});card.append(button);summary.append(card);
  }
  const present=methods.filter(m=>branches[m]);const pairs=[];for(let i=0;i<present.length;i++)for(let j=i+1;j<present.length;j++)if(branches[present[i]].text===branches[present[j]].text)pairs.push(`${names[present[i]]} and ${names[present[j]]}`);
  $('comparison-summary').textContent=present.length<3?(draftOnly?'Draft-only mode: no revision route has run yet. You can compare this same draft below.':'Route comparisons appear as the first reviewed round completes.'):pairs.length===3?'All three routes retained identical text. No distinct Memory benefit is demonstrated in these outputs. Inspect the candidates to see whether edits were the same, rejected, or not attempted.':pairs.length?`Identical final text: ${pairs.join('; ')}. Different scores are not required for texts to differ, and different texts are not proof of improvement.`:'The three retained texts are different. Inspect the edits and reviewer evidence; difference alone does not establish a benefit from Memory.';
  $('score-chart').replaceChildren(present.length?drawChart(branches):element('p',Number.isFinite(result.initialScore)?`Initial problem score: ${score(result.initialScore)} / 20.`:'The initial review is pending.'));$('round-table').replaceChildren(scoreTable(branches));
  const tabs=$('branch-tabs');tabs.replaceChildren();
  for(const method of ['initial',...present]){const b=element('button',names[method]);b.type='button';b.id=`branch-tab-${method}`;b.dataset.branch=method;b.setAttribute('role','tab');b.setAttribute('aria-controls','manuscript');b.addEventListener('click',()=>displayBranch(method));b.addEventListener('keydown',e=>{const all=[...tabs.children],idx=all.indexOf(b);let next;if(e.key==='ArrowRight')next=(idx+1)%all.length;if(e.key==='ArrowLeft')next=(idx-1+all.length)%all.length;if(e.key==='Home')next=0;if(e.key==='End')next=all.length-1;if(next!==undefined){e.preventDefault();displayBranch(all[next].dataset.branch);all[next].focus?.();}});tabs.append(b);}
  if(selected!=='initial'&&!branches[selected])selected='initial';displayBranch(selected);markdownText($('initial-manuscript'),result.initialText||'The initial draft has not finished.');
  const decisions=$('decision-log'),memory=$('memory-log');decisions.replaceChildren();memory.replaceChildren();
  if(branches.memory)memory.append(element('p',memorySummary(branches.memory),'memory-summary'));
  for(const [method,branch] of Object.entries(branches))for(const r of branch.rounds.filter(r=>r.round>0)){
    const item=element('details');item.append(element('summary',`${names[method]} · R${r.round} · ${isFailure(r)?'failed':r.route==='stop'?'no candidate':r.accepted?'retained':'rejected'} · candidate ${score(r.candidateScore)} · kept ${score(r.retainedScore)}`),element('p',r.reason||'No explanation recorded.'));
    if(r.pairwiseReview)item.append(element('p',`Blind comparison: ${r.pairwiseReview.verdict}. ${r.pairwiseReview.reason}`));
    for(const quote of r.pairwiseReview?.evidence||[])item.append(element('p',quote,'review-evidence'));
    if(r.audit?.preservation?.issues?.length)item.append(element('p',r.audit.preservation.issues.join(' '),'failure-note'));
    if(r.candidateText){const detail=element('details');detail.append(element('summary','Read the candidate, including rejected writing'));const body=element('div');markdownText(body,r.candidateText);detail.append(body);item.append(detail);}decisions.append(item);
    if(method==='memory'){const entry=element('div');entry.append(element('strong',`Round ${r.round}: ${(r.memoryApplications||[]).length?'card application recorded':'no historical card applied'}`),element('p',r.reason));for(const a of r.memoryApplications||[])entry.append(element('p',`${a.cardId} → ${(a.paragraphIds||[]).join(', ')}. ${a.reason}`),element('blockquote',a.conditionEvidence));memory.append(entry);}
  }
  if(!decisions.children.length)decisions.append(element('p','Reviewed candidates will appear here.'));
  if(!memory.children.length)memory.append(element('p','Memory use will be shown with its actual applicability evidence, not assumed from a branch label.'));
  const cards=element('details');cards.append(element('summary','Inspect the frozen editing cards'));for(const card of session?.snapshot.cards||defaults.catalog.cards){const section=element('div');section.append(element('h4',card.id.replaceAll('_',' ')),element('p',card.operation));for(const c of card.conditions||[])section.append(element('p',`${c.kind}: ${c.text}`));cards.append(section);}memory.append(cards);
}
function invalidateStage(stage,reason='') {if(!session)return;for(const [key,value]of session.cache)if(value.stage===stage){value.invalidated=true;value.invalidationReason=reason;value.invalidatedAt=new Date().toISOString();session.cache.delete(key);}logicalDone.delete(stage);}
function onProgress(event) {
  if(event.phase==='complete')return;events.push(event);$('status-message').textContent=event.message;
  if(['invalidated','error'].includes(event.phase)){invalidateStage(event.stage,event.message||'Response validation failed.');statuses.set(event.stage,{...event,phase:'invalidated'});renderStages();metrics();}
  if(event.phase==='calling'&&!statuses.has(event.stage)){statuses.set(event.stage,{...event,phase:'requesting'});renderStages();}
  if(event.stage==='ideation'&&event.phase==='completed'&&result)result.outline=event.detail.outline;
  if(event.phase==='drafted'||event.phase==='draft') {result={...result,initialText:event.detail.initialText,initialScore:event.detail.initialScore??null,initialAudit:event.detail.audit??null,initialGuard:event.detail.guard??null,branches:{}};displayResults();}
  if(event.phase==='candidate')$('status-message').textContent=`${names[event.detail.branch]} round ${event.detail.round}: ${event.detail.edits?.length||0} paragraph edit(s) prepared; awaiting the common blind review.`;
  if(event.phase==='round'&&result){const {branch,record}=event.detail;const b=result.branches[branch]||={text:result.initialText,rounds:[{round:0,retainedScore:result.initialScore,candidateScore:result.initialScore}],finalScore:result.initialScore};b.rounds=b.rounds.filter(r=>r.round!==record.round);b.rounds.push(record);b.text=record.text;b.finalScore=record.retainedScore;if(branch==='memory'&&selected==='initial'){selected='memory';selectedRound=String(record.round);}displayResults();}
}
function download(name,content,type='text/plain') {const url=URL.createObjectURL(new Blob([content],{type}));const a=element('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);}
function manuscriptText() {const body=selected==='initial'?result.initialText:currentBranch()?.text;const refs=(session?.snapshot.sources||[]).map(s=>`[${s.id}] ${s.title}${s.authors?` — ${s.authors.join(', ')}`:''}${s.url?`\n${s.url}`:''}${s.license?`\nSource excerpt license: ${s.license} (${s.license_url})`:''}`).join('\n\n');return `${body}\n\n## Supplied sources\n\n${refs}\n\n---\nGenerated research proposal; experiments are planned. Run status: ${result.status}.\n`;}
async function execute(testOnly=false,resuming=false,extending=false) {
  if(running||!defaults)return;$('error-panel').hidden=true;let startedRun=false;
  try {
    if(!$('consent').checked)throw new Error('Confirm the selected provider and API usage before starting.');
    const config={base:$('api-base').value,model:$('api-model').value,key:$('api-key').value};let snapshot;
    if(resuming||extending){if(resuming&&!canResume())throw new Error('There is no interrupted run in this tab.');if(extending&&!canCompare())throw new Error('Finish a draft-only run before continuing its comparison.');snapshot={...session.snapshot,mode:extending?'compare':session.snapshot.mode};if(providerEndpoint(config.base)!==snapshot.endpoint||config.model.trim()!==snapshot.model)throw new Error('Continue with the original provider endpoint and model. Restore those settings and enter that provider’s key.');}
    else if(!testOnly){const topic=$('topic').value.trim();if(topic.length<10||topic.length>1600)throw new Error('Enter a topic of 10–1,600 characters.');snapshot={base:config.base,endpoint:providerEndpoint(config.base),model:config.model.trim(),topic,sources:sourceInput(),mode:$('generation-mode').value,cards:structuredClone(defaults.catalog.cards),sourceCatalogSHA256:defaults.source_catalog_sha256};}
    client=createModelClient(config,{onUsage:u=>{usage.push(u);metrics();},onStatus:statusEvent});
    if(!testOnly){
      if(!resuming&&!extending&&session?.responses.length&&!window.confirm('Start a new run? This replaces the current workspace. Cancel to download a checkpoint first.'))return;
      startedRun=true;if(!resuming&&!extending){session={snapshot,cache:new Map(),responses:[],usage:[],events:[],attemptCount:0,attempts:[],createdAt:new Date().toISOString()};importedRun=false;result={schema:'proseledger-browser-2',status:'incomplete',initialText:null,initialScore:null,branches:{}};$('results-panel').hidden=true;}else{session.snapshot=snapshot;result.status='incomplete';}
      pendingComparison=false;$('topic').value=snapshot.topic;$('source-notes').value=serializeSources(snapshot.sources);$('generation-mode').value=snapshot.mode;usage=session.usage;attempts=session.attemptCount;events=[];selected='initial';selectedRound='final';generating=true;
    }
    else {usage=[];events=[];attempts=0;}
    controller=new AbortController();busy(true);started=performance.now();statuses=new Map();logicalDone=new Set();cacheHits=0;
    $('status-panel').hidden=false;$('status-title').textContent=testOnly?'Testing your model connection':resuming?'Resuming the saved run':extending?'Comparing the same saved draft':snapshot.mode==='draft'?'Generating and reviewing your draft':'Generating a new proposal and actual revisions';$('progress-bar').max=testOnly?1:snapshot.mode==='draft'?2:14;renderStages();metrics();ticker=setInterval(metrics,1000);
    $('status-panel').scrollIntoView?.({behavior:'smooth',block:'start'});
    if(testOnly){$('status-message').textContent='Sending one short request directly to the selected provider.';await client.callModel([{role:'user',content:'Reply with OK only.'}],{signal:controller.signal,stage:'connection_test',maxTokens:256});logicalDone.add('connection_test');$('connection-status').textContent='Connected. Ready to generate with this model.';$('status-title').textContent='Connection verified';$('status-message').textContent='The provider returned text. Your key remains in this form until you generate, clear it, or leave the page.';}
    else {
      const cachedModel=async(messages,options={})=>{const key=JSON.stringify([snapshot.endpoint,snapshot.model,messages,options.maxTokens??2500]);const cached=session.cache.get(key);if(cached){if(options.signal?.aborted)throw new DOMException('Generation cancelled.','AbortError');cacheHits++;logicalDone.add(options.stage);statuses.set(options.stage,{stage:options.stage,phase:'cached'});renderStages();metrics();return cached.response;}
        const response=await client.callModel(messages,options);const record={stage:options.stage,response,model:snapshot.model,maxTokens:options.maxTokens??2500,receivedAt:new Date().toISOString(),invalidated:false};session.responses.push(record);for(const[oldKey,old]of session.cache)if(old.stage===options.stage)session.cache.delete(oldKey);session.cache.set(key,record);logicalDone.add(options.stage);metrics();return response;};
      const complete=await runProposal({topic:snapshot.topic,sources:snapshot.sources,cards:snapshot.cards||defaults.catalog.cards,mode:snapshot.mode,callModel:cachedModel,signal:controller.signal,onProgress});result=complete;
      if(failedCount()&&result.status==='completed')result.status='completed_with_errors';if(result.branches?.memory){selected='memory';selectedRound='final';}displayResults();
      const failures=failedCount();$('status-title').textContent=failures?`Finished with ${failures} invalid / unreviewed candidate(s)`:'Generation completed';$('status-message').textContent=failures?'Valid outputs are retained. Failed stages are recorded; re-enter your key to resume without repeating successful requests.':snapshot.mode==='draft'?'Draft and initial review are ready. Download the proposal or compare revision routes using this same draft. Your key has been cleared.':'Inspect the actual edits and reviewer reasons, then download the retained writing. The key has been cleared.';
      if(!failures)$('progress-bar').max=Math.max(1,logicalDone.size);
    }
  } catch(error) {
    if(startedRun&&result){result.status=error.name==='AbortError'?'cancelled':'incomplete';displayResults();}
    if(error.name==='AbortError'){$('status-title').textContent='Generation stopped';$('status-message').textContent='Successful responses remain in this tab. Enter the same provider/model key to resume. In-flight requests may still be billed.';}
    else {showError(error.message);if(startedRun||testOnly){$('status-title').textContent='Run stopped';$('status-message').textContent='No saved evaluation was substituted. Any completed draft remains visible; enter your key and resume to retry the missing work.';}}
  } finally {
    clearInterval(ticker);if(startedRun&&session){session.attemptCount=attempts;session.events.push(...events);session.attempts.push({endedAt:new Date().toISOString(),status:result?.status,result:structuredClone(result)});}if(started)metrics();if(startedRun)clearSecret();else client?.clear();client=null;controller=null;generating=false;busy(false);if(startedRun&&result)displayResults();
  }
}
$('generation-form').addEventListener('submit',e=>{e.preventDefault();execute(false,false,pendingComparison);});$('test-connection').addEventListener('click',()=>execute(true));$('resume').addEventListener('click',()=>execute(false,true));$('cancel').addEventListener('click',()=>controller?.abort());
$('clear-key').addEventListener('click',()=>{controller?.abort();clearSecret();$('connection-status').textContent='API key cleared.';});
$('provider-preset').addEventListener('change',()=>{const preset=PRESETS[$('provider-preset').value];$('api-base').value=preset?.base||'';$('api-model').value=preset?.model||'';changeConnection();});$('api-base').addEventListener('input',changeConnection);$('api-model').addEventListener('change',()=>{$('consent').checked=false;updateReadiness();});$('reset-inputs').addEventListener('click',()=>{pendingComparison=false;loadExample();});
for(const id of ['api-key','consent','topic','source-notes','generation-mode'])$(id).addEventListener(id==='consent'||id==='generation-mode'?'change':'input',()=>{if(['topic','source-notes','generation-mode'].includes(id))pendingComparison=false;updateReadiness();});
$('source-upload').addEventListener('change',async e=>{const file=e.target.files[0];if(!file)return;try{if(file.size>100000||!/\.(txt|md)$/i.test(file.name))throw new Error('Import a TXT or Markdown file smaller than 100 KB.');const imported=await file.text();if(!running){$('source-notes').value=imported;pendingComparison=false;updateReadiness();}}catch(error){showError(error.message);}finally{e.target.value='';}});
$('compare-draft').addEventListener('click',()=>{
  if(running||!canCompare())return;pendingComparison=true;
  const saved=session.snapshot;let sameConnection=false;try{sameConnection=providerEndpoint($('api-base').value)===saved.endpoint&&$('api-model').value.trim()===saved.model;}catch{}
  if(!sameConnection){clearSecret();$('consent').checked=false;}
  $('provider-preset').value=Object.entries(PRESETS).find(([,p])=>p.base===saved.base)?.[0]||'custom';$('api-base').value=saved.base;$('api-model').value=saved.model;$('topic').value=saved.topic;$('source-notes').value=serializeSources(saved.sources);$('generation-mode').value='compare';
  $('connection-destination').textContent=saved.endpoint;updateReadiness();
  if($('api-key').value.trim()&&$('consent').checked)execute(false,false,true);
  else{$('readiness-summary').textContent='Continue this exact draft: re-enter your API key, confirm API usage, then choose Compare this saved draft. The initial draft and review will be reused.';$('api-key').scrollIntoView?.({behavior:'smooth',block:'center'});$('api-key').focus?.();}
});
$('download-checkpoint').addEventListener('click',()=>{if(!session||!result)return;try{const saved=createCheckpoint({...session,attemptCount:generating?attempts:session.attemptCount,events:generating?[...session.events,...events]:session.events},result);download('proseledger_checkpoint.json',JSON.stringify(saved),'application/json');}catch(error){showError(`Checkpoint not saved: ${error.message}`);}});
$('restore-run').addEventListener('change',async e=>{
  const file=e.target.files[0];if(!file||running)return;
  try{
    if(file.size>CHECKPOINT_MAX_BYTES)throw new Error('The checkpoint exceeds the 8 MB limit.');
    const saved=restoreCheckpoint(await file.text());if(!saved.result)throw new Error('This checkpoint has no run result to open.');
    if(session?.responses.length&&!window.confirm('Open this checkpoint and replace the current workspace? Cancel to save your current record first.'))return;
    clearSecret();session=saved.session;result=saved.result;importedRun=true;pendingComparison=false;
    const snapshot=session.snapshot;$('provider-preset').value=Object.entries(PRESETS).find(([,p])=>p.base===snapshot.base)?.[0]||'custom';$('api-base').value=snapshot.base;$('api-model').value=snapshot.model;changeConnection();$('topic').value=snapshot.topic;$('source-notes').value=serializeSources(snapshot.sources);$('generation-mode').value=snapshot.mode;
    usage=session.usage;events=[];attempts=session.attemptCount;cacheHits=0;started=null;statuses=new Map();logicalDone=new Set();selected=result.branches?.memory?'memory':'initial';selectedRound='final';$('status-panel').hidden=true;$('error-panel').hidden=true;busy(false);displayResults();$('results-panel').scrollIntoView?.({behavior:'smooth',block:'start'});
  }catch(error){showError(`Cannot open this checkpoint: ${error.message}`);}finally{e.target.value='';}
});
$('round-select').addEventListener('change',()=>{selectedRound=$('round-select').value;renderEdit();});
$('zoom-scores').addEventListener('change',()=>{if(result)$('score-chart').replaceChildren(drawChart(result.branches||{}));});
$('download-manuscript').addEventListener('click',()=>{if(result?.initialText)download(`proseledger_${selected}.md`,manuscriptText(),'text/markdown');});
$('copy-manuscript').addEventListener('click',async()=>{if(!result?.initialText)return;try{await navigator.clipboard.writeText(manuscriptText());$('copy-manuscript').textContent='Copied';setTimeout(()=>{$('copy-manuscript').textContent='Copy text';},2200);}catch{showError('Clipboard access was blocked. Use Download manuscript instead.');}});
$('download-json').addEventListener('click',()=>{if(result&&session)download('proseledger_run.json',JSON.stringify({result,metadata:{...session.snapshot,sources:undefined,sourceCatalogSHA256:session.snapshot.sourceCatalogSHA256,startedAt:session.createdAt,protocol:'proseledger-browser-2'},inputProvenance:session.snapshot.sources,usage:session.usage,events:generating?[...session.events,...events]:session.events,attempts:session.attempts,rawModelResponses:session.responses},null,2),'application/json');});
$('download-csv').addEventListener('click',()=>{if(!result)return;const rows=[['Branch','Round','Candidate score','Retained score','Accepted','Pairwise verdict','Route','Outcome','Card IDs','Exact text changed']];for(const[name,b]of Object.entries(result.branches||{}))for(const r of b.rounds)rows.push([names[name],r.round,r.candidateScore??'',r.retainedScore,r.accepted??'',r.pairwise??'',r.route??'initial',r.outcome??'',(r.cardIds||[]).join('; '),r.changed??false]);if(rows.length===1)rows.push(['Initial',0,result.initialScore??'',result.initialScore??'','','','initial','initial','',false]);download('proseledger_round_scores.csv',rows.map(row=>row.map(x=>`"${String(x).replaceAll('"','""')}"`).join(',')).join('\r\n'),'text/csv');});
window.addEventListener('pagehide',()=>{controller?.abort();clearSecret();});window.addEventListener('beforeunload',e=>{if(running){e.preventDefault();e.returnValue='';}});
async function initialize() { $('generate').disabled=true;$('test-connection').disabled=true;$('restore-run').disabled=true;try{const response=await fetch('./live-inputs.json',{credentials:'omit',cache:'no-store'});if(!response.ok)throw new Error();defaults=await response.json();$('provider-preset').value='openai';$('api-base').value=PRESETS.openai.base;$('api-model').value=PRESETS.openai.model;changeConnection();loadExample();$('generate').disabled=false;$('test-connection').disabled=false;$('restore-run').disabled=false;$('resume').hidden=true;updateReadiness();}catch{showError('The source bundle did not load. Reload this HTTPS page before starting.');}}
initialize();
