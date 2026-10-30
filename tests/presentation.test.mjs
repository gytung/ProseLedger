import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';

const read=path=>readFile(new URL('../'+path,import.meta.url),'utf8');
const html=await read('docs/presentation.html');
const source=JSON.parse(await read('docs/evidence.json'));
const dataText=html.match(/<script id="recorded-data" type="application\/json">([\s\S]*?)<\/script>/)[1];
const data=JSON.parse(dataText);
const app=html.match(/<script>\s*('use strict';[\s\S]*?)<\/script>/)[1];
const routes=['targeted','planner','memory'];
const sha=text=>createHash('sha256').update(text,'utf8').digest('hex');
const expectedFinals=[[9.1,9.1,9.1],[6.3,6.3,7],[5.6,6.3,6.3],[7,7,7],[7,7,7],[6.3,6.3,6.3]];

class NodeDouble {
  constructor(tag='div',attributes={}) {
    this.tagName=tag.toUpperCase();this.attributes={...attributes};this.dataset={};
    for(const [k,v] of Object.entries(attributes))if(k.startsWith('data-'))this.dataset[k.slice(5)]=v;
    this.children=[];this.listeners={};this.style={};this.disabled=false;this.content='';
    this.classes=new Set((attributes.class||'').split(/\s+/).filter(Boolean));
    this.classList={toggle:(name,on)=>{if(on===undefined)on=!this.classes.has(name);if(on)this.classes.add(name);else this.classes.delete(name);return on;},contains:name=>this.classes.has(name)};
  }
  set textContent(v){this.content=String(v);this.children=[];}
  get textContent(){return this.content+this.children.map(c=>c.textContent).join('');}
  append(...children){this.children.push(...children);children.forEach(c=>c.parent=this);}
  replaceChildren(...children){this.children=[];this.content='';this.append(...children);}
  setAttribute(k,v){this.attributes[k]=String(v);}
  addEventListener(k,fn){(this.listeners[k]||=[]).push(fn);}
  dispatch(k,e={}){for(const fn of this.listeners[k]||[])fn({target:this,preventDefault(){},...e});}
  click(){if(!this.disabled)this.dispatch('click');}
  remove(){if(this.parent)this.parent.children=this.parent.children.filter(n=>n!==this);}
}

function harness() {
  const nodes=new Map(),all=[],downloads=[],blobs=new Map(),frames=new Map();let now=0,nextFrame=0,networkCalls=0;
  for(const m of html.matchAll(/<(section|button|div|span|p|table|i|nav|main|footer|script)\b([^>]*)>/g)) {
    const attributes=Object.fromEntries([...m[2].matchAll(/([\w-]+)="([^"]*)"/g)].map(a=>[a[1],a[2]]));
    const n=new NodeDouble(m[1],attributes);all.push(n);if(attributes.id)nodes.set(attributes.id,n);
  }
  nodes.get('recorded-data').textContent=dataText;
  const get=id=>{assert.ok(nodes.has(id),'Known DOM id: '+id);return nodes.get(id);};
  const document=new NodeDouble('document');
  Object.assign(document,{hidden:false,activeElement:null,body:new NodeDouble('body'),documentElement:{},getElementById:get,
    querySelectorAll:selector=>all.filter(n=>selector==='.scene'?n.classes.has('scene'):selector==='[data-route]'?Object.hasOwn(n.dataset,'route'):selector==='[data-step]'?Object.hasOwn(n.dataset,'step'):false),
    createElement:tag=>{const n=new NodeDouble(tag);if(tag==='a')n.click=()=>downloads.push({name:n.download,blob:blobs.get(n.href)});return n;},
    createElementNS:(_ns,tag)=>new NodeDouble(tag)});
  class TestURL {static createObjectURL(blob){const id='blob:recording-'+blobs.size;blobs.set(id,blob);return id;}static revokeObjectURL(){}}
  const context=vm.createContext({document,URL:TestURL,Blob,console,performance:{now:()=>now},setTimeout:()=>0,
    requestAnimationFrame:fn=>{const id=++nextFrame;frames.set(id,fn);return id;},cancelAnimationFrame:id=>frames.delete(id),
    fetch:()=>{networkCalls++;throw new Error('The recording view must not fetch.');},XMLHttpRequest:class{constructor(){networkCalls++;throw new Error('No runtime network');}}});
  vm.runInContext(app,context,{filename:'presentation.html'});
  const advance=seconds=>{now+=seconds*1000;const callbacks=[...frames.values()];frames.clear();callbacks.forEach(fn=>fn(now));};
  const select=(kind,value)=>document.querySelectorAll('[data-'+kind+']').find(n=>n.dataset[kind]===String(value));
  const active=()=>document.querySelectorAll('.scene').findIndex(n=>n.classes.has('active'));
  return {get,document,downloads,advance,select,active,networkCalls:()=>networkCalls};
}

test('the recording payload and generated HTML exactly preserve the frozen source',async()=>{
  assert.deepEqual(data.case,source.cases[1]);assert.deepEqual(data.card,source.cards.find(c=>c.id==='existing_comparison'));
  assert.deepEqual(data.summary,source.summary);assert.deepEqual(data.protocol,source.protocol);
  assert.equal(data.source_contract_hash,source.source_contract_hash);
  for(const [i,c] of data.cases.entries()){
    const s=source.cases[i];assert.equal(c.id,s.id);assert.equal(c.theme,s.theme);assert.equal(c.initial,s.initial.score);
    assert.deepEqual(routes.map(k=>c.finals[k]),expectedFinals[i]);
    routes.forEach(k=>assert.deepEqual(c.rounds[k],[s.initial.score,...s.branches[k].rounds.map(r=>r.retained_score)]));
  }
  const template=await read('scripts/presentation.template.html');
  assert.equal(html,template.replace('__EVIDENCE_JSON__',dataText));
  assert.equal(sha(data.case.initial.text),data.case.initial.text_sha256);
  for(const b of Object.values(data.case.branches))assert.equal(sha(b.text),b.text_sha256);
});

test('six-case means, all 54 decisions and all wins/ties/losses are independently recomputed',()=>{
  assert.equal(data.cases.length,6);assert.equal(source.cases.flatMap(c=>Object.values(c.branches).flatMap(b=>b.rounds)).length,54);
  routes.forEach(k=>assert.ok(Math.abs(data.cases.reduce((sum,c)=>sum+c.finals[k],0)/6-data.summary.means[k])<1e-12));
  const wdl={wins:0,ties:0,losses:0};for(const c of data.cases)wdl[c.finals.memory<c.finals.targeted?'wins':c.finals.memory===c.finals.targeted?'ties':'losses']++;
  assert.deepEqual(wdl,{wins:0,ties:4,losses:2});assert.deepEqual(wdl,data.summary.memory_vs_targeted);
});

test('Memory round 2 is a real retained card edit with no score gain; round 3 stops',()=>{
  const [first,second,third]=data.case.branches.memory.rounds;
  assert.equal(first.route,'shared_targeted');assert.deepEqual(first.historical_card_ids,[]);
  assert.equal(second.route,'local_edit');assert.deepEqual(second.historical_card_ids,['existing_comparison']);
  assert.equal(second.accepted,true);assert.equal(second.changed,true);assert.equal(second.guard_passed,true);
  assert.equal(second.semantic_verdict,'preserved');assert.notEqual(second.before_text,second.candidate_text);
  assert.equal(first.retained_score,7);assert.equal(second.candidate_score,7);assert.equal(second.retained_score,7);
  assert.equal(third.route,'stop');assert.equal(third.changed,false);assert.equal(third.retained_score,7);
  assert.match(third.plan.abstention_reason,/specifications absent from the manuscript/);
  assert.match(html,/Score 7\.0 → 7\.0 · unchanged/);assert.match(html,/no incremental score improvement here/);
});

test('the recording is explicitly labelled and has no runtime external dependency',()=>{
  assert.match(html,/Recorded model run · Same evidence as the slides/);
  assert.match(html,/Saved outputs · No new model calls during this walkthrough/);
  assert.match(html,/connect-src 'none'/);assert.match(html,/default-src 'none'/);
  assert.equal(/<script[^>]+src\s*=/i.test(html),false);assert.equal(/<link[^>]+href\s*=/i.test(html),false);
  assert.equal(/<img[^>]+src\s*=["']https?:/i.test(html),false);
  assert.equal(/\bfetch\s*\(|\bXMLHttpRequest\b|\bWebSocket\b|\bimport\s*\(/.test(app),false);
  assert.equal(dataText.includes('<'),false);assert.equal(html.includes('__EVIDENCE_JSON__'),false);
  const h=harness();assert.equal(h.networkCalls(),0);assert.equal(h.active(),0);
});

test('all three-round means and six case scores render directly from evidence',()=>{
  const h=harness();assert.equal(h.get('initial-score').textContent,'9.1');
  const roundRows=h.get('round-table').children[1].children;assert.equal(roundRows.length,3);
  routes.forEach((k,i)=>assert.deepEqual(roundRows[i].children.slice(1).map(c=>c.textContent),[0,1,2,3].map(n=>(data.cases.reduce((s,c)=>s+c.rounds[k][n],0)/6).toFixed(4))));
  const caseRows=h.get('case-table').children[1].children;assert.equal(caseRows.length,6);
  caseRows.forEach((r,i)=>assert.deepEqual(r.children.slice(1,4).map(n=>n.textContent),expectedFinals[i].map(n=>n.toFixed(1))));
  assert.equal(h.get('mean-chart').children[0].children.filter(n=>n.tagName==='CIRCLE').length,12);
  assert.match(h.get('memory-before').textContent,/providing bounded evidence/);
  assert.doesNotMatch(h.get('memory-after').textContent,/providing bounded evidence/);
  assert.match(h.get('memory-after').textContent,/workload when merging and renumbering citations/);
});

test('the complete two-minute tour progresses through all five chapters and replays',()=>{
  const h=harness();h.get('play').click();assert.equal(h.get('play').textContent,'Pause tour');
  for(const [seconds,scene,time] of [[20,1,'0:20'],[20,2,'0:40'],[36,3,'1:16'],[28,4,'1:44'],[16,4,'2:00']]){
    h.advance(seconds);assert.equal(h.active(),scene);assert.equal(h.get('time').textContent,time+' / 2:00');
  }
  assert.equal(h.get('timeline').style.width,'100%');assert.equal(h.get('play').textContent,'Replay 2-minute tour');
  h.get('play').click();assert.equal(h.active(),0);h.advance(1);assert.equal(h.get('time').textContent,'0:01 / 2:00');
  h.get('play').click();h.advance(20);assert.equal(h.get('time').textContent,'0:01 / 2:00');
  assert.equal(h.networkCalls(),0);
});

test('manual navigation, tab hiding and restart never advance or overwrite results unexpectedly',()=>{
  const h=harness();assert.equal(h.get('previous').disabled,true);h.get('next').click();assert.equal(h.active(),1);
  h.select('step',3).click();assert.equal(h.active(),3);assert.equal(h.get('time').textContent,'1:16 / 2:00');
  h.get('play').click();h.document.hidden=true;h.document.dispatch('visibilitychange');h.advance(20);assert.equal(h.active(),3);
  assert.match(h.get('notice').textContent,/paused while the tab was hidden/);
  h.select('route','targeted').click();assert.match(h.get('output-score').textContent,/Targeted · Final score 6\.3/);
  h.get('restart').click();assert.equal(h.active(),0);assert.equal(h.get('time').textContent,'0:00 / 2:00');
  assert.match(h.get('output-score').textContent,/Memory · Final score 7\.0/);
  h.document.dispatch('keydown',{key:'ArrowRight'});assert.equal(h.active(),1);
  h.document.dispatch('keydown',{key:'ArrowLeft'});assert.equal(h.active(),0);
});

test('all manuscript downloads, complete case record and 72 trajectory rows preserve source values',async()=>{
  const h=harness();
  for(const k of routes){h.select('route',k).click();h.get('download-draft').click();const d=h.downloads.at(-1);assert.equal(d.name,'ProseLedger_Case02_'+k+'.md');assert.equal(await d.blob.text(),data.case.branches[k].text);}
  h.get('download-record').click();assert.deepEqual(JSON.parse(await h.downloads.at(-1).blob.text()),data);
  h.get('download-scores').click();const rows=(await h.downloads.at(-1).blob.text()).split('\r\n').map(r=>r.split(',').map(v=>v.slice(1,-1)));
  assert.equal(rows.length,73);let i=1;
  for(const c of data.cases)for(const k of routes)for(let n=0;n<4;n++)assert.deepEqual(rows[i++],[c.id,c.theme,k,String(n),String(c.rounds[k][n])]);
  assert.equal(h.networkCalls(),0);
});
