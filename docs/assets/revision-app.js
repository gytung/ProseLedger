import {createModelClient, PRESETS, validateConnection, providerEndpoint} from './api-client.js?v=20261113c';
import {createOllamaClient, validateOllamaConfig, OLLAMA_MODEL, OLLAMA_DIGEST} from './ollama-client.js?v=20261113c';
import {createNativeClient, validateNativeConfig} from './native-client.js?v=20261113c';
import * as engine from './revision-engine.js?v=20261113c';
import {mountExternalValidation} from './external-validation.js?v=20261113c';

const $ = id => document.getElementById(id);
const draftPage=document.body.dataset.workspace==='create', handoffKey='proseledger-proposal-handoff-v1';
const node = (tag, text, className) => {const value=document.createElement(tag); if(text!==undefined)value.textContent=String(text); if(className)value.className=className; return value;};
let run=null, running=false, controller=null, clients=[], started=0, ticks=null, usage=[], activity='', manuscriptVersion='retained', imported=false, example=null;
const settingIds=['provider-preset','api-base','api-model','native-base','native-model','native-token','writer-model','writer-backend','ollama-base','test-ollama','api-key','input-mode','topic','source-notes','supplied-draft','policy','consent','load-example','source-upload','draft-upload','restore-run','test-connection'];
const seconds = value => {const n=Math.max(0,Math.round(Number(value)||0)); return `${Math.floor(n/60)}:${String(n%60).padStart(2,'0')}`;};
const wordCount = text => String(text||'').match(/[\p{L}\p{N}]+(?:[-'][\p{L}\p{N}]+)*/gu)?.length||0;
const readable = text => String(text||'').replaceAll('_',' ');
const sourcesToNotes = sources => sources.map(s=>`[${s.id}] ${s.title}\n${s.excerpt}`).join('\n\n');

function showError(error){$('error-message').textContent=error instanceof Error?error.message:String(error);$('error-panel').hidden=false;}
function clearError(){$('error-panel').hidden=true;$('error-message').textContent='';}
function download(name,value,type='application/json'){
  const content=type==='application/json'?JSON.stringify(value,null,2):String(value);
  const url=URL.createObjectURL(new Blob([content],{type})); const link=node('a');link.href=url;link.download=name;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),2000);
}
function exportRun(){if(!run)return;download(`proseledger_${run.id||'run'}.json`,{...run,browserUsage:usage});}
function sourceSummary(){
  try{const sources=engine.parseSources($('source-notes').value);$('source-summary').textContent=`${sources.length} sources · ${sources.reduce((n,s)=>n+s.excerpt.length,0).toLocaleString()} excerpt characters. Only these supplied excerpts are used.`;}
  catch(error){$('source-summary').textContent=error.message;}
}
function inputMode(){
  const existing=!draftPage;$('input-mode').value=existing?'existing':'generate';$('input-mode').disabled=true;
  $('draft-field').hidden=!existing;$('supplied-draft').required=existing;$('topic').required=!existing;
  $('topic').placeholder=existing?'Optional context for your existing proposal':'What do you want to investigate?';
  document.querySelector('label[for=topic]').textContent=existing?'Research question or topic (optional)':'Research question or topic';
  $('generate').textContent=existing?'Revise my proposal →':'Generate proposal →';
}
function updateDestination(){
  try{$('api-destination').textContent=providerEndpoint($('api-base').value);}
  catch{$('api-destination').textContent='Enter a valid public HTTPS endpoint.';}
}
function resetConnection(){
  $('api-key').value='';$('consent').checked=false;$('connection-status').textContent='Connection changed. Enter the matching key and test it before running.';updateDestination();
}
function collectInput(){return engine.validateInput({...(draftPage?{operation:'draft'}:{}),topic:$('topic').value,draft:$('input-mode').value==='existing'?$('supplied-draft').value:'',sources:engine.parseSources($('source-notes').value),policy:$('policy').value});}
function primaryMode(){
  const native=$('provider-preset').value==='codex';
  $('native-settings').hidden=!native;$('cloud-settings').hidden=native;$('cloud-model-field').hidden=native;
  $('api-key').required=!native;$('api-model').required=!native;$('api-base').required=!native;$('native-token').required=native;$('native-model').required=native;
  $('writer-backend').querySelector('option[value=hosted]').disabled=native&&!draftPage;
  if(native&&!draftPage)$('writer-backend').value='ollama';
  $('test-connection').textContent=native?'Test Codex connection':'Test cloud connection';
  $('connection-status').textContent=native?'Checks the local connector and signed-in account status. No writing request is made.':draftPage?'Tests the cloud connection; it uses API credit.':'Tests the cloud connection; it uses API credit. Test local Qwen separately below.';
  writerMode();
}
function writerMode(){
  const local=!draftPage&&$('writer-backend').value==='ollama',native=$('provider-preset').value==='codex';
  $('writer-connection').hidden=draftPage;$('ollama-settings').hidden=!local;$('hosted-writer-settings').hidden=local||draftPage;
  if(draftPage){$('connection-intro').textContent=native?'Generate a proposal through your signed-in Codex account and local connector. This page does not run Qwen or revise the text.':'Generate a proposal through your selected cloud API. This page does not run a section writer or revise the text.';}
  else{
    const reviewer=native?'Codex':'the selected API reviewer',writer=local?'Local Qwen2.5 7B':'The hosted section writer';
    $('workflow-pill').textContent=native?'Codex review · Local Qwen writer':local?'API review · Local Qwen writer':'Hosted writer · Independent review';
    $('connection-intro').textContent=`${writer} rewrites each section. ${native?'Your signed-in Codex account':'Your main API model'} checks meaning and readability, then repairs flagged passages.`;
    $('hero-lead').textContent=`Start from an existing proposal and its source excerpts. ${writer} rewrites each section; ${reviewer} checks the changes and repairs flagged passages.`;
  }
  $('writer-route-help').textContent=local?'Requires Ollama on this computer. No Qwen API key or cloud token purchase is needed.':'The selected API provider performs the section rewrites. Leave the optional writer model blank to use the main cloud model.';
  $('consent-label').textContent=draftPage?(native?'Use my signed-in Codex account through the local connector to generate this proposal. I will keep this tab and the connector open.':'Send my topic and source excerpts to the selected cloud provider using my API credit to generate a proposal.'):native?'Use my signed-in Codex account through the local connector for checking and repair, and local Ollama for section rewrites. I will keep this tab and both local services open.':local?'Use my cloud API credit for checking and repair, and send section rewrites to local Ollama on this computer. I will keep this tab and Ollama open.':'Send my input to the selected cloud provider using my API credit. I will keep this tab open while it runs.';
  $('consent').checked=false;
}
function publicConfig(){
  const native=$('provider-preset').value==='codex';
  let data;
  if(native){
    const config=validateNativeConfig({base:$('native-base').value,model:$('native-model').value,token:$('native-token').value.trim()});
    if(!draftPage&&$('writer-backend').value!=='ollama')throw new Error('Codex account mode uses local Ollama for section rewriting.');
    data={endpoint:config.base,model:config.model,key:config.token};
  }else data=validateConnection({base:$('api-base').value,model:$('api-model').value,key:$('api-key').value});
  let identity;
  if(draftPage){identity=native?{endpoint:data.endpoint,model:data.model,writerModel:'none',writerBackend:'none',primaryBackend:'codex'}:{endpoint:data.endpoint,model:data.model,writerModel:data.model};}
  else if($('writer-backend').value==='ollama'){
    const local=validateOllamaConfig({base:$('ollama-base').value,model:OLLAMA_MODEL});
    identity={endpoint:data.endpoint,model:data.model,writerModel:local.model,writerBackend:'ollama',writerBase:local.base,writerDigest:OLLAMA_DIGEST,...(native?{primaryBackend:'codex'}:{})};
  }else{
    const writerModel=$('writer-model').value.trim()||data.model;
    validateConnection({base:$('api-base').value,model:writerModel,key:$('api-key').value});
    identity={endpoint:data.endpoint,model:data.model,writerModel};
  }
  if(JSON.stringify(identity).includes(data.key))throw new Error('Keep your connection secret only in its masked field, not the endpoint or model settings.');return {data,identity};
}
function busy(value){
  running=value;document.body.classList.toggle('running',value);
  for(const id of settingIds)$(id).disabled=value;inputMode();
  $('generate').disabled=value;$('cancel').disabled=!value;$('clear-key').disabled=value;$('clear-native-token').disabled=value;
  $('resume').disabled=value;$('resume').hidden=!run||run.status==='completed'||!run.responses?.length;
  $('download-checkpoint').disabled=!run;$('download-run').disabled=!run;
  external?.refresh();
}
function activityUpdate(item){
  activity=item.phase==='receiving'?`Receiving ${item.outputCharacters?.toLocaleString()||0} output characters · ${seconds(item.elapsedMs/1000)}`:item.message;
  $('request-activity').textContent=activity;
}
function usageUpdate(item){usage.push(item);const known=usage.filter(x=>Number.isFinite(x.totalTokens));$('token-count').textContent=known.length?known.reduce((n,x)=>n+x.totalTokens,0).toLocaleString():'Not reported';}
function createClients(config,identity,quiet=false){
  const options={timeoutMs:240000,firstTokenTimeoutMs:90000,idleTimeoutMs:60000,maxConcurrent:1,onUsage:quiet?()=>{}:usageUpdate,onStatus:quiet?()=>{}:activityUpdate};
  const native=identity.primaryBackend==='codex';
  const local=identity.writerBackend==='ollama';
  let main,writer;
  try{
  main=native?createNativeClient({base:config.endpoint,model:config.model,token:config.key},options):createModelClient({base:config.endpoint,model:config.model,key:config.key},options);
  writer=identity.writerBackend==='none'?main:local?createOllamaClient({base:identity.writerBase,model:identity.writerModel},{onUsage:options.onUsage,onStatus:options.onStatus}):identity.writerModel===config.model?main:createModelClient({base:config.endpoint,model:identity.writerModel,key:config.key},options);
  }catch(error){main?.clear();writer?.clear();throw error;}
  clients=[...new Set([main,writer])];
  return {
    main, writer, local, native,
    callModel:(messages,options)=>/^rewrite_section_/.test(options?.stage||'')?writer.callModel(messages,options):main.callModel(messages,options),
    prepare:async signal=>{
      if(local){$('ollama-status').textContent='Checking local Ollama and the Qwen model…';try{const ready=await writer.probe({signal});identity.writerDigest=ready.digest;$('ollama-status').textContent='Ready · '+ready.model+' · model weights verified.';$('ollama-status').dataset.ready='true';}catch(error){$('ollama-status').textContent=error.message;$('ollama-status').dataset.ready='false';throw error;}}
      if(native){$('connection-status').textContent='Checking the local Codex connector…';await main.probe({signal});$('connection-status').textContent='Codex connector ready. Requests use your signed-in account.';}
    }
  };
}
function restoreFields(value){
  $('topic').value=value.input.topic||'';$('source-notes').value=sourcesToNotes(value.input.sources||[]);
  $('supplied-draft').value=value.input.draft||'';$('input-mode').value=value.input.draft?'existing':'generate';$('policy').value=value.input.policy||'section';
  const native=value.model.primaryBackend==='codex';$('provider-preset').value=native?'codex':'custom';
  if(native){$('native-base').value=value.model.endpoint;$('native-model').value=value.model.model;}
  else{$('api-base').value=value.model.endpoint;$('api-model').value=value.model.model;$('writer-model').value=value.model.writerModel&&value.model.writerModel!==value.model.model?value.model.writerModel:'';}
  primaryMode();$('writer-backend').value=value.model.writerBackend==='ollama'?'ollama':'hosted';if(value.model.writerBase)$('ollama-base').value=value.model.writerBase;
  $('api-key').value='';$('native-token').value='';$('consent').checked=false;inputMode();writerMode();sourceSummary();updateDestination();
}
async function execute(resume){
  if(running)return;clearError();let input,config;
  try{input=collectInput();config=publicConfig();if(JSON.stringify(input).includes(config.data.key)||(resume&&JSON.stringify(run).includes(config.data.key)))throw new Error('Your connection secret was also found in the research input or checkpoint. Remove it from the document before continuing.');if(!$('consent').checked)throw new Error('Confirm model usage before starting.');}
  catch(error){showError(error);return;}
  if(!resume){run=null;imported=false;manuscriptVersion='retained';$('results-panel').hidden=true;}
  usage=[];controller=new AbortController();let connection;
  started=Date.now();$('progress-panel').hidden=false;$('call-count').textContent='0';$('cache-count').textContent='0';$('token-count').textContent='—';$('request-activity').textContent='Checking your model connections.';$('run-status').textContent='Preparing';$('status-title').textContent='Checking your writing setup.';$('status-message').textContent='No new generation has started yet.';
  busy(true);ticks=setInterval(()=>{$('elapsed').textContent=seconds((Date.now()-started)/1000);},1000);
  try{
    connection=createClients(config.data,config.identity);config.data.key='';
    await connection.prepare(controller.signal);
    const value=await engine.runRevision(input,{callModel:connection.callModel,signal:controller.signal,resume:resume?run:null,model:config.identity,onUpdate:value=>{run=value;renderProgress();renderResults();}});
    run=value;manuscriptVersion='retained';renderProgress();renderResults();$('request-activity').textContent=draftPage?'Your proposal is ready. Download it or continue to the revision workspace.':'All stages completed. Your final draft and revision record are ready.';
    $('results-panel').scrollIntoView({behavior:'smooth',block:'start'});
  }catch(error){
    if(error.run)run=error.run;renderProgress();renderResults();
    if(error.name==='AbortError')showError('Run stopped. Completed stages are saved in this tab; download a checkpoint or resume when ready.');else showError(error);
  }finally{
    config.data.key='';clearInterval(ticks);ticks=null;clients.forEach(client=>client.clear());clients=[];$('api-key').value='';$('native-token').value='';$('consent').checked=false;controller=null;busy(false);
  }
}
function renderProgress(){
  if(!run)return;$('progress-panel').hidden=false;$('download-checkpoint').disabled=false;
  $('run-status').textContent=run.status==='completed'?'Completed':run.status==='running'?'Running':readable(run.status||'Saved');
  $('status-title').textContent=run.status==='completed'?(draftPage?'Your proposal is ready.':'Your revision is complete.'):run.status==='running'?(draftPage?'Generating your proposal.':'Working through your draft.'):'Your progress is preserved.';
  $('status-message').textContent=readable(run.stage||'Preparing');$('call-count').textContent=String(run.completedCalls||0);$('cache-count').textContent=String(run.cachedCalls||0);
  if(!running)$('elapsed').textContent=seconds(run.elapsedSeconds||0);
  const list=$('stage-list');list.replaceChildren();
  for(const step of run.steps||[]){const li=node('li');li.dataset.status=step.status;li.append(node('span',step.status==='completed'||step.status==='cached'?'✓':step.status==='failed'?'!':step.status==='running'?'·':'○','stage-icon'));const copy=node('div',undefined,'stage-copy');copy.append(node('span',step.label||readable(step.id)));if(step.reason)copy.append(node('small',step.reason));else if(step.status==='cached')copy.append(node('small','Reused validated response'));li.append(copy);list.append(li);}
}
function prose(container,text){
  container.replaceChildren();const pieces=String(text||'').split(/\n{2,}/);
  for(const paragraph of pieces){if(!paragraph.trim())continue;let tag='p',value=paragraph;if(/^# /.test(paragraph)){tag='h2';value=paragraph.replace(/^# /,'');}else if(/^## /.test(paragraph)){tag='h3';value=paragraph.replace(/^## /,'');}container.append(node(tag,value));}
}
function renderManuscript(){
  if(!run)return;if(run.input?.operation==='draft'){
    $('manuscript-tabs').replaceChildren();$('manuscript-note').textContent='A newly generated proposal. It has not yet undergone language revision or content verification. Review the claims and supplied sources.';prose($('manuscript-text'),run.initial);return;
  }const choices=[['initial','Original'],['candidate','Candidate'],['retained','Retained']].filter(([key])=>typeof run[key]==='string'&&run[key]&&(key!=='retained'||run.status==='completed'));
  if(!choices.some(([key])=>key===manuscriptVersion))manuscriptVersion=choices[0]?.[0]||'initial';
  $('manuscript-tabs').replaceChildren();
  for(const [key,label] of choices){const tab=node('button',label);tab.type='button';tab.role='tab';tab.setAttribute('aria-selected',String(key===manuscriptVersion));tab.setAttribute('aria-controls','manuscript-text');tab.addEventListener('click',()=>{manuscriptVersion=key;renderManuscript();});$('manuscript-tabs').append(tab);}
  $('manuscript-note').textContent=manuscriptVersion==='initial'?'The starting proposal, preserved without alteration.':manuscriptVersion==='candidate'?'The assembled revision submitted to the final checks. It may differ from the version retained.':'The version selected after checking. If the candidate failed, this is the original proposal.';
  prose($('manuscript-text'),run[manuscriptVersion]||'');
}
function diffWords(original,revised){
  const a=String(original).split(/(\s+)/),b=String(revised).split(/(\s+)/);
  const left=document.createDocumentFragment(),right=document.createDocumentFragment();
  if(a.length*b.length>650000){
    let prefix=0,suffix=0;while(prefix<a.length&&prefix<b.length&&a[prefix]===b[prefix])prefix++;
    while(suffix<a.length-prefix&&suffix<b.length-prefix&&a[a.length-1-suffix]===b[b.length-1-suffix])suffix++;
    const fill=(fragment,words,tag)=>{fragment.append(document.createTextNode(words.slice(0,prefix).join('')));const middle=words.slice(prefix,words.length-suffix).join('');if(middle)fragment.append(node(tag,middle));fragment.append(document.createTextNode(suffix?words.slice(-suffix).join(''):''));};
    fill(left,a,'del');fill(right,b,'ins');return [left,right];
  }
  const width=b.length+1,dp=new Uint16Array((a.length+1)*width);
  for(let i=a.length-1;i>=0;i--)for(let j=b.length-1;j>=0;j--)dp[i*width+j]=a[i]===b[j]?1+dp[(i+1)*width+j+1]:Math.max(dp[(i+1)*width+j],dp[i*width+j+1]);
  let i=0,j=0,deleted='',inserted='';
  const flush=()=>{if(deleted)left.append(node('del',deleted));if(inserted)right.append(node('ins',inserted));deleted='';inserted='';};
  while(i<a.length||j<b.length){
    if(i<a.length&&j<b.length&&a[i]===b[j]){flush();left.append(document.createTextNode(a[i]));right.append(document.createTextNode(b[j]));i++;j++;}
    else if(i<a.length&&(j===b.length||dp[(i+1)*width+j]>=dp[i*width+j+1]))deleted+=a[i++];
    else inserted+=b[j++];
  }
  flush();return [left,right];
}
function findingBlock(label,issue){
  const div=node('div',undefined,'finding');div.append(node('strong',label));if(issue.problem)div.append(node('p',issue.problem));
  if(issue.originalQuote)div.append(node('p','Original quote'),node('blockquote',issue.originalQuote));if(issue.revisedQuote)div.append(node('p','Revised quote'),node('blockquote',issue.revisedQuote));return div;
}
function renderSection(){
  const section=run?.sections?.find(s=>String(s.id)===$('section-select').value);if(!section)return;
  const retained=run.status==='completed'?(typeof section.retained==='string'?section.retained:(run.retained===run.initial?section.original:section.text||section.original)):(section.text||section.candidate||section.original);
  $('edit-retained-label').textContent=run.status==='completed'?'Retained':'Candidate under review';
  const changed=retained!==section.original;
  $('section-decision').textContent=(run.status==='completed'?(changed?'Revised text retained. ':'Original wording retained. '):'Verification in progress. ')+(section.reason||'');
  const [a,b]=diffWords(section.original||'',retained||'');$('edit-original').replaceChildren(a);$('edit-retained').replaceChildren(b);$('edit-candidate').textContent=section.candidate||'No candidate generated for this section yet.';
  const findings=$('edit-findings');findings.replaceChildren();
  if(section.review){findings.append(node('p',`Section review: ${section.review.approve?'approved':'not approved'} · readability ${section.review.readability||'not reported'}.`,'help'));for(const [i,issue] of (section.review.issues||[]).entries())findings.append(findingBlock(`Finding ${i+1}`,issue));}
  if(section.repair?.ok){const repair=node('div',undefined,'finding');repair.append(node('strong','Bounded repair applied'),node('p','Only uniquely matched passages were changed; the rest of the section was preserved.'));for(const patch of section.repair.spans||[])repair.append(node('blockquote',`${patch.before}\n→ ${patch.after}`));findings.append(repair);}
  else if(section.repair?.reason&&!['not_needed_or_not_repairable','not_needed'].includes(section.repair.reason))findings.append(node('p',`Repair not applied: ${readable(section.repair.reason)}.`,'help'));
  if(!section.review)findings.append(node('p','The section-level review has not completed yet.','help'));
}
function renderChecks(){
  const box=$('full-checks');box.replaceChildren();const checks=run?.checks;if(!checks){box.append(node('p','The full-document check has not completed yet.','help'));return;}
  const list=node('ul',undefined,'checks-list');
  list.append(node('li',`Structural and token checks: ${checks.guard?.passed?'passed':'not passed'}.`),node('li',`Model assessment of content preservation: ${checks.audit?.contentPreserved?'yes':'not confirmed'}.`),node('li',`Model assessment of readability: ${checks.audit?.readability||'not reported'}.`));
  if(Number.isFinite(checks.wordRatio))list.append(node('li',`Candidate length: ${(checks.wordRatio*100).toFixed(1)}% of original (required 85–115%).`));
  for(const value of checks.guard?.findings||[])list.append(node('li',value));for(const value of checks.reasons||[])list.append(node('li',value));box.append(list);
  if(checks.audit?.reason)box.append(node('p',checks.audit.reason,'help'));
  for(const issue of checks.audit?.issues||[])box.append(findingBlock(`Full-document finding${issue.section?' · '+issue.section:''}`,issue));
  if(run.ledger?.repairHistory?.length)box.append(node('p',`${run.ledger.repairHistory.length} additional repair cycle(s) recorded in the downloadable ledger.`,'help'));
}
function renderDraftResults(){
  const complete=run.status==='completed';$('results-title').textContent='Your proposal, ready for the next step.';
  const summary=$('result-summary');summary.replaceChildren();const copy=node('div');copy.append(node('h3',complete?'One proposal generated.':'Your proposal is being generated.'),node('p','Built from your topic and supplied source excerpts. Continue to the separate revision workspace when you are ready to refine its language.'));summary.append(copy);
  const stats=node('div',undefined,'result-stats');for(const [value,label] of [[wordCount(run.initial),'proposal words'],[run.input.sources.length,'supplied sources']]){const stat=node('div');stat.append(node('b',value),node('span',label));stats.append(stat);}summary.append(stats);
  $('run-provenance').textContent=`${imported?'Imported record':'This browser run'} · ${run.id||'run ID pending'} · generation model: ${run.model?.model||'not reported'} (${run.model?.primaryBackend==='codex'?'Codex account':'cloud API'}). No Qwen revision or detector validation has run on this page.`;
  $('download-manuscript').disabled=!complete;$('download-run').disabled=false;$('draft-actions').hidden=!complete;$('handoff-note').hidden=!complete;
  $('edit-panel').hidden=true;$('external-validation-panel').hidden=true;$('result-nav').hidden=true;
  renderManuscript();
}
function renderResults(){
  if(!run?.initial)return;$('results-panel').hidden=false;
  if(run.input?.operation==='draft'){renderDraftResults();return;}
  $('draft-actions').hidden=true;$('handoff-note').hidden=true;$('result-nav').hidden=false;$('external-validation-panel').hidden=false;
  const complete=run.status==='completed',changed=complete&&run.retained!==run.initial;
  const summary=$('result-summary');summary.replaceChildren();const description=node('div');description.append(node('h3',complete?(changed?'A revised draft, retained.':'The original draft, retained.'):'Your original draft is ready.'));
  description.append(node('p',complete?(changed?'The candidate passed the configured checks. Review the changes before using it.':run.candidate===run.initial?'No wording change was retained. Your original remains available.':'The assembled candidate did not meet every retention condition. Your original was preserved.'):'The revision is not complete. You can inspect the original and save your progress.'));summary.append(description);
  const stats=node('div',undefined,'result-stats');const changedSections=complete?(run.sections||[]).filter(s=>typeof s.retained==='string'&&s.retained!==s.original).length:0;
  for(const [value,label] of [[wordCount(run.initial),'original words'],[complete?wordCount(run.retained):'—','retained words'],[complete?changedSections:'—','sections changed']]){const stat=node('div');stat.append(node('b',value),node('span',label));stats.append(stat);}summary.append(stats);
  $('run-provenance').textContent=`${imported?'Imported record':'This browser run'} · ${run.id||'run ID pending'} · main model: ${run.model?.model||'not reported'} (${run.model?.primaryBackend==='codex'?'Codex account':'cloud API'}) · writer: ${run.model?.writerModel||run.model?.model||'not reported'} (${run.model?.writerBackend==='ollama'?'local Ollama':'hosted API'}). No historical cards retrieved. Detector scores do not select the draft.`;
  $('download-manuscript').disabled=!complete||!run.retained;$('download-ledger').disabled=!run.ledger;$('download-run').disabled=false;
  const previous=$('section-select').value;$('section-select').replaceChildren();for(const section of run.sections||[]){const option=node('option',section.heading);option.value=String(section.id);$('section-select').append(option);}if([...(run.sections||[])].some(s=>String(s.id)===previous))$('section-select').value=previous;
  $('edit-panel').hidden=!(run.sections||[]).length;renderManuscript();renderSection();renderChecks();external?.refresh();
}
const external=draftPage?null:mountExternalValidation($('external-validation-panel'),{getDocuments:()=>run?.status==='completed'?(run.retained===run.initial?[{id:'initial',label:'Original = final retained proposal',text:run.initial}]:[{id:'initial',label:'Original proposal',text:run.initial},{id:'retained',label:'Final retained proposal',text:run.retained}]):[],getRunId:()=>run?.id||'',isBusy:()=>running});

$('generation-form').addEventListener('submit',event=>{event.preventDefault();execute(false);});
$('resume').addEventListener('click',()=>execute(true));
$('cancel').addEventListener('click',()=>{controller?.abort();$('request-activity').textContent='Stopping after the current request is cancelled…';});
$('clear-key').addEventListener('click',()=>{$('api-key').value='';$('connection-status').textContent='Key cleared from this tab.';});
$('clear-native-token').addEventListener('click',()=>{$('native-token').value='';$('connection-status').textContent='Local pairing code cleared from this tab.';});
$('input-mode').addEventListener('change',inputMode);$('source-notes').addEventListener('input',sourceSummary);
$('provider-preset').addEventListener('change',()=>{const preset=PRESETS[$('provider-preset').value];if(preset){$('api-base').value=preset.base;$('api-model').value=preset.model;$('writer-model').value='';}$('native-token').value='';resetConnection();primaryMode();});
$('native-base').addEventListener('change',()=>{$('native-token').value='';$('consent').checked=false;$('connection-status').textContent='Connector address changed. Enter its pairing code and test again.';});
$('native-model').addEventListener('change',()=>{$('consent').checked=false;$('connection-status').textContent='Codex model changed. The connector will use this model for subsequent requests.';});
$('api-base').addEventListener('change',resetConnection);
$('api-model').addEventListener('change',()=>{$('connection-status').textContent='Model changed. Test the new connection before running.';});
$('writer-model').addEventListener('change',()=>{$('connection-status').textContent='Writer model changed. Test both models before running.';});
$('test-connection').addEventListener('click',async()=>{
  if(running)return;clearError();let config;
  try{config=publicConfig();}catch(error){$('connection-status').textContent=error.message;return;}
  controller=new AbortController();busy(true);$('connection-status').textContent=config.identity.primaryBackend==='codex'?'Checking the Codex connector…':'Testing the cloud model connection…';
  const abort=controller;let connection;
  try{
    connection=createClients(config.data,config.identity,true);config.data.key='';
    if(connection.native){await connection.main.probe({signal:abort.signal});$('connection-status').textContent=draftPage?'Codex connector ready. You can generate your proposal.':'Codex connector ready. Test local Qwen separately below.';}
    else{await connection.main.callModel([{role:'user',content:'Reply with the single word ready.'}],{stage:'connection_test',maxTokens:64,signal:abort.signal});if(!connection.local&&config.identity.writerModel!==config.identity.model)await connection.writer.callModel([{role:'user',content:'Reply with the single word ready.'}],{stage:'connection_test',maxTokens:64,signal:abort.signal});$('connection-status').textContent=connection.local?'Cloud connection ready. Test local Qwen separately below.':'Connected. Your browser can receive complete model responses.';}
  }catch(error){$('connection-status').textContent=error.message;}
  finally{config.data.key='';clients.forEach(client=>client.clear());clients=[];controller=null;busy(false);}
});
$('writer-backend').addEventListener('change',writerMode);
$('ollama-base').addEventListener('change',()=>{$('consent').checked=false;$('ollama-status').textContent='Address changed. Test local Qwen before running.';delete $('ollama-status').dataset.ready;});
$('test-ollama').addEventListener('click',async()=>{
  if(running)return;clearError();let local;
  try{local=createOllamaClient({base:$('ollama-base').value,model:OLLAMA_MODEL});}catch(error){$('ollama-status').textContent=error.message;return;}
  controller=new AbortController();clients=[local];busy(true);$('ollama-status').textContent='Checking Ollama on this computer…';
  try{const ready=await local.probe({signal:controller.signal});$('ollama-status').textContent='Ready · '+ready.model+' · model weights verified.';$('ollama-status').dataset.ready='true';}
  catch(error){$('ollama-status').textContent=error.message;$('ollama-status').dataset.ready='false';}
  finally{local.clear();clients=[];controller=null;busy(false);}
});
$('section-select').addEventListener('change',renderSection);
$('download-manuscript').addEventListener('click',()=>{if(run?.status==='completed')download(draftPage?'ProseLedger_Proposal.md':'ProseLedger_Final_Draft.md',draftPage?run.initial:run.retained,'text/markdown');});
$('download-draft-record').addEventListener('click',exportRun);
$('continue-revision').addEventListener('click',()=>{
  if(run?.status!=='completed'||run.input?.operation!=='draft')return;
  try{sessionStorage.setItem(handoffKey,JSON.stringify({topic:run.input.topic,sources:run.input.sources.map(source=>({id:source.id,title:source.title,excerpt:source.excerpt})),draft:run.initial}));window.location.assign('./revise.html');}
  catch{showError('Your browser could not transfer the proposal. Download it, open Revise proposal, then import the proposal and source excerpts.');}
});
$('download-run').addEventListener('click',exportRun);$('download-checkpoint').addEventListener('click',exportRun);
$('download-ledger').addEventListener('click',()=>{if(run?.ledger)download('ProseLedger_Revision_Ledger.json',run.ledger);});
async function importText(input,target){const file=input.files?.[0];if(!file)return;try{if(file.size>120000)throw new Error('Use a text file smaller than 120 KB.');$(target).value=await file.text();sourceSummary();}catch(error){showError(error);}finally{input.value='';}}
$('source-upload').addEventListener('change',()=>importText($('source-upload'),'source-notes'));
$('draft-upload').addEventListener('change',()=>importText($('draft-upload'),'supplied-draft'));
$('restore-run').addEventListener('change',async()=>{
  if(running)return;const file=$('restore-run').files?.[0];if(!file)return;clearError();
  try{if(file.size>5000000)throw new Error('Checkpoint is too large. Use a ProseLedger run JSON smaller than 5 MB.');const data=JSON.parse(await file.text());const verified=await engine.validateCheckpoint(data);const validated=verified||data;if((validated.input?.operation==='draft')!==draftPage)throw new Error(draftPage?'This is a revision record. Open it on the Revise proposal page.':'This is a generation record. Open it on Generate proposal, then choose Continue to revision.');run=validated;usage=Array.isArray(run.browserUsage)?run.browserUsage:[];imported=true;manuscriptVersion='retained';restoreFields(run);renderProgress();renderResults();busy(false);$('connection-status').textContent=run.status==='completed'?'Completed record opened. No model request was made.':'Checkpoint opened. Re-enter your API key or local pairing code and confirm usage to resume.';}
  catch(error){showError(error);}finally{$('restore-run').value='';}
});
async function loadExample(){
  try{if(!example){const response=await fetch('./revision-example.json?v=20261113c',{cache:'no-cache'});if(!response.ok)throw new Error('The example could not be loaded. Enter your topic and source excerpts to continue.');example=await response.json();}$('topic').value=example.topic;$('source-notes').value=sourcesToNotes(example.sources);$('supplied-draft').value=example.draft||example.text||'';sourceSummary();}
  catch(error){showError(error);}
}
$('load-example').addEventListener('click',loadExample);
$('heading-template').textContent=engine.HEADINGS.map(heading=>'## '+heading).join('\n\n');
for(const rule of engine.RULES){const card=node('div',undefined,'rule');card.append(node('h4',rule.name||rule[0]),node('p',rule.instruction||rule[1]));$('rules').append(card);}
window.addEventListener('beforeunload',event=>{if(running){event.preventDefault();event.returnValue='';}});
window.addEventListener('pagehide',()=>{controller?.abort();clients.forEach(client=>client.clear());clients=[];$('api-key').value='';$('native-token').value='';});
async function initializeInput(){
  if(!draftPage){
    let saved=null;try{saved=sessionStorage.getItem(handoffKey);sessionStorage.removeItem(handoffKey);}catch{}
    if(saved){try{const value=JSON.parse(saved);const input=engine.validateInput({topic:value.topic,draft:value.draft,sources:value.sources,policy:'section'});$('topic').value=input.topic;$('supplied-draft').value=input.draft;$('source-notes').value=sourcesToNotes(input.sources);sourceSummary();$('source-summary').textContent+=' Transferred from Generate proposal; no credentials were transferred.';return;}catch{showError('The transferred proposal was invalid. Load the example or import your proposal and sources.');}}
  }
  await loadExample();
}
inputMode();primaryMode();updateDestination();initializeInput();
