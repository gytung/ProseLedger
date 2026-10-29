import { PRESETS, providerEndpoint, createModelClient } from './api-client.js';
import { runProposal } from './browser-engine.js';

const $ = id => document.getElementById(id);
const names = { initial: 'Initial draft', targeted: 'Targeted', planner: 'Planner-only', memory: 'Memory' };
const colors = { targeted: '#6c98af', planner: '#7e9874', memory: '#9b76ba' };
let defaults, result, controller, client, ticker, started, selected = 'initial';
let running = false, usage = [], events = [], inputProvenance = [], metadata = {};
let exportUsage = [], exportEvents = [];
let generating = false;

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function showError(message) {
  $('error-panel').hidden = false;
  $('error-message').textContent = message;
}

function changeConnection() {
  if (running) return;
  $('api-key').value = '';
  $('consent').checked = false;
  $('connection-status').textContent = 'A connection test makes one small API call.';
  try { $('connection-destination').textContent = providerEndpoint($('api-base').value); }
  catch { $('connection-destination').textContent = 'Enter a valid public HTTPS API URL.'; }
}

function clearSecret() {
  client?.clear();
  $('api-key').value = '';
}

function serializeSources(sources) {
  return sources.map(s => `[${s.id}] ${s.title}\n${s.excerpt}`).join('\n\n');
}

function sourceInput() {
  const notes = $('source-notes').value.trim();
  if (notes.length > 31000) throw new Error('Source notes are too long. Keep excerpt content within 24,000 characters.');
  const markers = [...notes.matchAll(/^\[(S\d+)\]\s+(.+)$/gm)];
  if (markers.length < 2 || markers.length > 10 || markers[0]?.index !== 0) {
    throw new Error('Supply 2–10 source notes, each beginning with [S1] Title, [S2] Title, and so on.');
  }
  const sources = markers.map((m,i) => {
    const excerpt = notes.slice(m.index + m[0].length, markers[i+1]?.index ?? notes.length).trim();
    const original = defaults.sources.find(s => s.id === m[1] && s.title === m[2].trim() && s.excerpt === excerpt);
    return original ? structuredClone(original) : { id:m[1], title:m[2].trim(), excerpt, provenance:'Visitor-supplied source note; not independently verified.' };
  });
  if (new Set(sources.map(s=>s.id)).size !== sources.length) throw new Error('Each source needs a unique [S#] ID.');
  if (sources.some(s=>s.excerpt.length < 80 || s.excerpt.length > 4000)) throw new Error('Each source excerpt must contain 80–4,000 characters.');
  if (sources.reduce((n,s)=>n+s.excerpt.length,0)>24000) throw new Error('The combined source excerpts exceed 24,000 characters.');
  return sources;
}

function loadExample() {
  if (!defaults || running) return;
  $('topic').value = defaults.topic;
  $('source-notes').value = serializeSources(defaults.sources);
}

function busy(value) {
  running = value;
  for (const id of ['provider-preset','api-base','api-model','api-key','topic','source-notes','source-upload','reset-inputs','generation-mode','consent','generate','test-connection']) $(id).disabled = value;
  $('cancel').disabled = !value;
}

function metrics() {
  $('call-count').textContent = String(usage.length);
  const known = usage.filter(u=>u.totalTokens !== null);
  const tokens = known.reduce((n,u)=>n+u.totalTokens,0);
  $('token-count').textContent = known.length ? `${tokens.toLocaleString()}${known.length < usage.length ? ' (partial)' : ''}` : 'Not reported';
  const seconds = Math.floor((performance.now()-started)/1000);
  $('elapsed-time').textContent = `${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,'0')}`;
  $('progress-bar').value = usage.length;
}

function markdownText(container, text) {
  container.replaceChildren();
  for (const block of String(text || '').split(/\n\s*\n/)) {
    const heading = /^(#{1,3})\s+(.+)$/.exec(block);
    const node = element(heading ? `h${Math.min(heading[1].length+1,4)}` : 'p', heading ? heading[2] : block);
    container.append(node);
  }
}

function scoreTable(branches) {
  const table = element('table');
  const head = element('thead'), row = element('tr');
  ['Retained score','R0','R1','R2','R3'].forEach(x=>row.append(element('th',x)));
  head.append(row); table.append(head);
  const body = element('tbody');
  for (const [method,branch] of Object.entries(branches)) {
    const r = element('tr'); r.append(element('th',names[method]));
    for (let k=0;k<=3;k++) {
      const record=branch.rounds.find(v=>v.round===k);
      r.append(element('td',record ? String(record.retainedScore) : '—'));
    }
    body.append(r);
  }
  table.append(body); return table;
}

function drawChart(branches) {
  const ns='http://www.w3.org/2000/svg';
  const svg=document.createElementNS(ns,'svg');
  svg.setAttribute('viewBox','0 0 610 280'); svg.setAttribute('role','img');
  svg.setAttribute('aria-label','Retained problem scores from initial draft through all three revision rounds');
  const add=(tag,attrs,text)=>{const n=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;svg.append(n);return n;};
  const x=k=>45+k*177,y=v=>230-v*9.5;
  for(const v of [0,5,10,15,20]) {
    add('line',{x1:45,y1:y(v),x2:580,y2:y(v),stroke:'#ece6f0'});
    add('text',{x:33,y:y(v)+4,'text-anchor':'end',fill:'#75677d','font-size':12},v);
  }
  for(let k=0;k<=3;k++)add('text',{x:x(k),y:252,'text-anchor':'middle',fill:'#75677d','font-size':12},`R${k}`);
  Object.entries(branches).forEach(([method,branch],index)=>{
    const path=branch.rounds.map((r,i)=>`${i?'L':'M'}${x(r.round)},${y(r.retainedScore)}`).join(' ');
    add('path',{d:path,fill:'none',stroke:colors[method],'stroke-width':2.5,'stroke-dasharray':index===1?'7 4':index===2?'2 4':'none'});
    branch.rounds.forEach(r=>{
      const circle=add('circle',{cx:x(r.round),cy:y(r.retainedScore),r:5-index,fill:'white',stroke:colors[method],'stroke-width':2});
      const title=document.createElementNS(ns,'title');title.textContent=`${names[method]} R${r.round}: ${r.retainedScore}`;circle.append(title);
    });
    add('text',{x:45+index*180,y:20,fill:colors[method],'font-size':13,'font-weight':'bold'},names[method]);
  });
  return svg;
}

function displayBranch(method) {
  selected=method;
  const text=method==='initial' ? result.initialText : result.branches[method].text;
  markdownText($('manuscript'),text);
  for(const button of $('branch-tabs').children) {
    button.setAttribute('aria-selected',String(button.dataset.branch===method));
    button.tabIndex=button.dataset.branch===method?0:-1;
  }
  $('manuscript').setAttribute('aria-labelledby',`branch-${method}`);
}

function displayResults() {
  if (!result) return;
  $('results-panel').hidden=false;
  $('results-heading').textContent=result.status==='completed'?'Your proposal and revision record.':result.initialText?'Draft available · comparison not complete':'Partial run record · draft pending';
  $('download-manuscript').disabled=!result.initialText;
  const branches=result.branches || {};
  $('score-chart').replaceChildren(Object.keys(branches).length ? drawChart(branches) : element('p',result.initialScore === null ? 'Initial audit has not completed.' : `Initial problem score: ${result.initialScore} / 20. No revision scores yet.`));
  $('round-table').replaceChildren(scoreTable(branches));
  $('branch-tabs').replaceChildren();
  for (const method of ['initial',...Object.keys(branches)]) {
    const b=element('button',names[method]); b.type='button';b.dataset.branch=method;b.setAttribute('role','tab');
    b.id=`branch-${method}`;b.setAttribute('aria-controls','manuscript');
    b.addEventListener('click',()=>displayBranch(method));$('branch-tabs').append(b);
  }
  if(selected!=='initial' && !branches[selected])selected='initial';
  displayBranch(selected);
  markdownText($('initial-manuscript'),result.initialText || 'The initial draft has not been generated. The JSON download preserves the completed planning records.');
  const decisions=$('decision-log');decisions.replaceChildren();
  const memory=$('memory-log');memory.replaceChildren();
  for (const [method,branch] of Object.entries(branches)) {
    for(const r of branch.rounds.filter(r=>r.round>0)) {
      const item=element('details');
      const label=r.route==='stop'?'No new candidate':r.accepted?'Retained':'Rejected';
      item.append(element('summary',`${names[method]} · R${r.round} · ${label} · ${r.candidateScore ?? '—'} → ${r.retainedScore}`));
      item.append(element('p',`${r.shared?'Shared first revision. ':''}${r.reason}`));
      item.append(element('p',`Route: ${r.route}. Outcome: ${r.outcome}. ${r.cardIds.length?`Cards: ${r.cardIds.join(', ')}.`:'No historical card selected.'}`));
      if(r.plan)item.append(element('p',`Plan: ${r.plan.reason} ${r.plan.applicability}`));
      if(r.audit?.preservation.issues.length)item.append(element('p',r.audit.preservation.issues.join(' ')));
      if(r.candidateText) {const candidate=element('details');candidate.append(element('summary','Read this candidate'));const p=element('div');markdownText(p,r.candidateText);candidate.append(p);item.append(candidate);}
      decisions.append(item);
      if(method==='memory') {
        const entry=element('p',`R${r.round}: ${r.cardIds.length?r.cardIds.join(', '):'No historical card applied'}. ${label}. ${r.plan?.applicability || (r.shared?'The first revision is shared with both controls.':r.reason)}`);
        memory.append(entry);
      }
    }
  }
  if(!decisions.children.length)decisions.append(element('p','Revision decisions appear as the comparison progresses.'));
  if(!memory.children.length)memory.append(element('p','Five frozen development cards are available for the Memory route. They are conditional advice, not proven improvements on your draft.'));
  const cardDetails=element('details');cardDetails.append(element('summary','Inspect the frozen editing cards'));
  for(const card of defaults.catalog.cards) {
    const section=element('div');section.append(element('h4',card.id.replaceAll('_',' ')),element('p',card.operation));
    for(const c of card.conditions || [])section.append(element('p',`${c.kind}: ${c.text}`));
    cardDetails.append(section);
  }
  memory.append(cardDetails);
}

function onProgress(event) {
  if(event.phase==='complete')return;
  events.push(event);
  $('status-message').textContent=event.message;
  if(event.phase==='calling') {
    $('stage-list').append(element('li',event.stage.replaceAll('_',' ')));
  }
  if(event.stage==='ideation' && event.phase==='completed' && result) { result.outline=event.detail.outline;displayResults(); }
  if(event.phase==='drafted' || event.phase==='draft') {
    result={...result,schema:'proseledger-browser-1',status:'incomplete',initialText:event.detail.initialText,
      initialScore:event.detail.initialScore ?? null,initialAudit:event.detail.audit ?? null,initialGuard:event.detail.guard ?? null,branches:{}};
    displayResults();
  }
  if(event.phase==='round' && result) {
    const {branch,record}=event.detail;
    const targets=branch==='shared'?['targeted','planner','memory']:[branch];
    for(const name of targets) {
      const b=result.branches[name] ||= {text:result.initialText,rounds:[{round:0,retainedScore:result.initialScore,candidateScore:result.initialScore}],finalScore:result.initialScore};
      b.rounds.push({...record,shared:branch==='shared'});b.text=record.text;b.finalScore=record.retainedScore;
    }
    displayResults();
  }
}

function download(name,content,type='text/plain') {
  const url=URL.createObjectURL(new Blob([content],{type}));
  const link=element('a');link.href=url;link.download=name;document.body.append(link);link.click();link.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1500);
}

function manuscriptText() {
  const body=selected==='initial'?result.initialText:result.branches[selected].text;
  const refs=inputProvenance.map(s=>`[${s.id}] ${s.title}${s.authors?` — ${s.authors.join(', ')}`:''}${s.url?`\n${s.url}`:''}${s.license?`\nSource excerpt license: ${s.license} (${s.license_url})`:''}`).join('\n\n');
  return `${body}\n\n## Supplied sources\n\n${refs}\n\n---\nGenerated research proposal; experiments are planned. ${result.status==='completed'?'Run completed.':'Incomplete run; this draft requires review.'}\n`;
}

async function execute(testOnly=false) {
  if(running || !defaults)return;
  $('error-panel').hidden=true;
  let newRunStarted=false;
  try {
    if(!$('consent').checked)throw new Error('Confirm the selected provider and API usage before starting.');
    const sources=testOnly?[]:sourceInput();
    const topic=$('topic').value.trim();
    if(!testOnly && (topic.length<10 || topic.length>1600))throw new Error('Enter a topic of 10–1,600 characters.');
    client=createModelClient({base:$('api-base').value,model:$('api-model').value,key:$('api-key').value},
      {onUsage:u=>{usage.push(u);metrics();}});
    controller=new AbortController();busy(true);started=performance.now();usage=[];events=[];
    $('status-panel').hidden=false;$('status-title').textContent=testOnly?'Testing your model connection':'Generating a new research proposal';
    $('stage-list').replaceChildren();$('progress-bar').max=testOnly?1:$('generation-mode').value==='draft'?3:21;
    metrics();ticker=setInterval(metrics,1000);
    if(testOnly) {
      $('status-message').textContent='Sending one short request directly to your selected model provider.';
      await client.callModel([{role:'user',content:'Reply with OK only.'}],{signal:controller.signal,stage:'connection_test'});
      $('connection-status').textContent='Connected. Enter the key again to generate a proposal.';
      $('status-title').textContent='Connection verified';$('status-message').textContent='The model returned text successfully. The API key has been cleared.';
    } else {
      newRunStarted=true;
      generating=true;
      result={schema:'proseledger-browser-1',status:'incomplete',initialText:null,initialScore:null,branches:{}};
      selected='initial';inputProvenance=sources;
      metadata={endpoint:client.endpoint,requestedModel:client.model,sourceCatalogSHA256:defaults.source_catalog_sha256,mode:$('generation-mode').value,
        topic,startedAt:new Date().toISOString(),protocol:'proseledger-browser-1'};
      $('results-panel').hidden=true;
      const complete=await runProposal({topic,sources,cards:defaults.catalog.cards,mode:metadata.mode,
        callModel:client.callModel,signal:controller.signal,onProgress});
      result={...complete,status:'completed'};displayResults();
      $('status-title').textContent='Generation completed';$('status-message').textContent='Download your manuscripts and run record below. The API key has been cleared.';
      $('progress-bar').max=Math.max(1,usage.length);
    }
  } catch(error) {
    if(result && newRunStarted) {result.status=error.name==='AbortError'?'cancelled':'incomplete';displayResults();}
    if(error.name==='AbortError') {
      $('status-title').textContent='Generation cancelled';$('status-message').textContent='No further requests will be sent. Any completed draft and records remain downloadable.';
    } else {
      showError(error.message);$('status-title').textContent='Run stopped';
      $('status-message').textContent='No result was substituted. Any completed draft remains below; an incomplete comparison has no final winner.';
    }
  } finally {
    if(newRunStarted && result) { exportUsage=structuredClone(usage);exportEvents=structuredClone(events); }
    clearInterval(ticker);if(started)metrics();clearSecret();client=null;controller=null;generating=false;busy(false);
  }
}

$('generation-form').addEventListener('submit',event=>{event.preventDefault();execute();});
$('branch-tabs').addEventListener('keydown',event=>{
  if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
  const buttons=[...$('branch-tabs').children];
  if(!buttons.length)return;
  const index=buttons.findIndex(b=>b.dataset.branch===selected);
  const next=event.key==='Home'?0:event.key==='End'?buttons.length-1:(index+(event.key==='ArrowRight'?1:-1)+buttons.length)%buttons.length;
  event.preventDefault();displayBranch(buttons[next].dataset.branch);buttons[next].focus();
});
$('test-connection').addEventListener('click',()=>execute(true));
$('cancel').addEventListener('click',()=>controller?.abort());
$('clear-key').addEventListener('click',()=>{controller?.abort();clearSecret();$('connection-status').textContent='API key cleared.';});
$('provider-preset').addEventListener('change',()=>{
  const preset=PRESETS[$('provider-preset').value];
  $('api-base').value=preset?.base || ''; $('api-model').value=preset?.model || '';changeConnection();
});
$('api-base').addEventListener('input',changeConnection);
$('api-model').addEventListener('change',()=>{$('consent').checked=false;});
$('reset-inputs').addEventListener('click',loadExample);
$('source-upload').addEventListener('change',async event=>{
  const file=event.target.files[0];if(!file)return;
  if(file.size>100000 || !/\.(txt|md)$/i.test(file.name)){showError('Import a TXT or Markdown file smaller than 100 KB.');return;}
  $('source-notes').value=await file.text();event.target.value='';
});
$('download-manuscript').addEventListener('click',()=>{if(result?.initialText)download(`proseledger_${selected}.md`,manuscriptText(),'text/markdown');});
$('download-json').addEventListener('click',()=>{
  if(result)download('proseledger_run.json',JSON.stringify({result,metadata,inputProvenance,usage:generating?usage:exportUsage,events:generating?events:exportEvents},null,2),'application/json');
});
$('download-csv').addEventListener('click',()=>{
  if(!result)return;
  const rows=[['Branch','Round','Candidate score','Retained score','Accepted','Route','Card IDs']];
  for(const [name,b] of Object.entries(result.branches || {}))for(const r of b.rounds) rows.push([names[name],r.round,r.candidateScore??'',r.retainedScore,r.accepted??'',r.route??'initial',(r.cardIds||[]).join('; ')]);
  if(rows.length===1)rows.push(['Initial',0,result.initialScore??'',result.initialScore??'','','initial','']);
  download('proseledger_round_scores.csv',rows.map(row=>row.map(x=>`"${String(x).replaceAll('"','""')}"`).join(',')).join('\r\n'),'text/csv');
});
window.addEventListener('pagehide',()=>{controller?.abort();clearSecret();});
window.addEventListener('beforeunload',event=>{if(running){event.preventDefault();event.returnValue='';}});

async function initialize() {
  $('generate').disabled=true;$('test-connection').disabled=true;
  try {
    const response=await fetch('./live-inputs.json',{credentials:'omit',cache:'no-store'});
    if(!response.ok)throw new Error();
    defaults=await response.json();
    $('provider-preset').value='openrouter';$('api-base').value=PRESETS.openrouter.base;$('api-model').value=PRESETS.openrouter.model;
    changeConnection();loadExample();$('generate').disabled=false;$('test-connection').disabled=false;
  } catch {showError('The example-source bundle did not load. Reload this HTTPS page before starting.');}
}
initialize();
