/** DOM-free integration tests for browser application state and downloads.
 * The application, engine and HTTP client execute unchanged; only browser DOM,
 * downloads and network responses are supplied by bounded in-memory doubles.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFile} from 'node:fs/promises';

const asset = name => new URL(`../docs/assets/${name}`, import.meta.url);
const importAsset = async name => import(`data:text/javascript;base64,${Buffer.from(await readFile(asset(name), 'utf8')).toString('base64')}`);
const api = await importAsset('api-client.js');
const engine = await importAsset('browser-engine.js');
const app = (await readFile(asset('create-app.js'), 'utf8')).replace(/^import .*;\n/gm, '');

const sources = [
  {id:'S1', title:'Evidence and editing', authors:['Example Author'], license:'CC BY 4.0', license_url:'https://creativecommons.org/licenses/by/4.0/', excerpt:'This supplied source discusses how language models may revise supported passages while retaining their original attribution. Its findings do not validate a new proposal.'},
  {id:'S2', title:'Conditional experience', excerpt:'This supplied source discusses storing conditional editing experiences and reviewing whether their preconditions apply to a later task. It establishes no universal benefit.'},
];
const draft = '# Evidence-Preserving Revision\n\n' + engine.HEADINGS.map((heading, index) =>
  `## ${heading}\n\nThe proposed study will examine whether revision preserves supported claims and uncertainty [S${index % 2 + 1}]. Its evaluation remains planned, and no improvement has been observed in this proposed study.`,
).join('\n\n');
const outline = {
  ideas:['A conditional revision study.', 'A supported claims study.', 'An editing control study.'], selectedIdea:0,
  outline:engine.HEADINGS.map(heading=>({heading,plan:'Describe the proposed component and its limitations.'})),
};
const audit = {
  dimensions:Object.fromEntries(engine.DIMENSIONS.map(name=>[name,{score:0,reason:'No identified expression issue.',quote:''}])),
  preservation:{passed:true,issues:[]},
};
const defaults = {
  topic:'Conditional experience for evidence-preserving academic proposal revision',
  sources, catalog:{cards:[]}, source_catalog_sha256:'public-evidence-catalog-hash',
};

class NodeDouble {
  constructor(tag='div') {
    this.tagName=tag;this.children=[];this.listeners={};this.dataset={};this.attributes={};
    this.value='';this.checked=false;this.disabled=false;this.hidden=true;this.content='';
  }
  set textContent(value) {this.content=String(value);this.children=[];}
  get textContent() {return this.content+this.children.map(child=>child.textContent).join('');}
  append(...children) {this.children.push(...children);for(const child of children)child.parent=this;}
  replaceChildren(...children) {this.children=[];this.content='';this.append(...children);}
  setAttribute(name,value) {this.attributes[name]=String(value);}
  addEventListener(name,listener) {(this.listeners[name] ||= []).push(listener);}
  dispatch(name,event={}) {for(const listener of this.listeners[name]||[])listener({preventDefault(){},target:this,...event});}
  click() {this.dispatch('click');}
  remove() {if(this.parent)this.parent.children=this.parent.children.filter(child=>child!==this);}
}

async function waitFor(condition, label) {
  for(let attempt=0;attempt<300;attempt++) {
    if(condition())return;
    await new Promise(resolve=>setTimeout(resolve,2));
  }
  throw new Error(`UI did not settle: ${label}`);
}

async function harness({failDraft=false}={}) {
  const nodes=new Map(), downloads=[], requests=[], blobs=new Map();
  const get=id=>{if(!nodes.has(id))nodes.set(id,new NodeDouble());return nodes.get(id);};
  const document={getElementById:get,createElement:tag=>new NodeDouble(tag),createElementNS:(_ns,tag)=>new NodeDouble(tag),body:new NodeDouble('body')};
  const create=document.createElement;
  document.createElement=tag=>{
    const node=create(tag);
    if(tag==='a')node.click=()=>downloads.push({name:node.download,blob:blobs.get(node.href)});
    return node;
  };
  class URLDouble extends URL {
    static createObjectURL(blob) {const id=`blob:test-${blobs.size}`;blobs.set(id,blob);return id;}
    static revokeObjectURL() {}
  }
  const fetchMock=async (url,options={})=>{
    if(url==='./live-inputs.json')return Response.json(structuredClone(defaults));
    requests.push({url,options});
    const body=JSON.parse(options.body);
    const instruction=body.messages.at(-1).content;
    if(instruction==='Reply with OK only.')return Response.json({model:'test-model',choices:[{message:{content:'OK'},finish_reason:'stop'}],usage:{prompt_tokens:2,completion_tokens:1,total_tokens:3}});
    let content;
    if(instruction.startsWith('Suggest three'))content=outline;
    else if(instruction.startsWith('Write a self-contained')) {
      if(failDraft)return new Response('',{status:503});
      content={text:draft};
    } else if(instruction.startsWith('Audit the candidate'))content=audit;
    else throw new Error(`Unexpected model request: ${instruction.slice(0,40)}`);
    return Response.json({model:'test-model',choices:[{message:{content:JSON.stringify(content)},finish_reason:'stop'}],usage:{prompt_tokens:7,completion_tokens:3,total_tokens:10}});
  };
  const context=vm.createContext({
    document, window:{addEventListener(){}}, URL:URLDouble, Blob, AbortController,
    structuredClone, performance, Date, console, fetch:fetchMock,
    PRESETS:api.PRESETS, providerEndpoint:api.providerEndpoint,
    createModelClient:(config,options)=>api.createModelClient(config,{...options,fetchImpl:fetchMock}),
    runProposal:engine.runProposal,
    setInterval:()=>0,clearInterval(){},setTimeout:()=>0,
  });
  vm.runInContext(app,context,{filename:'create-app.js'});
  await waitFor(()=>!get('generate').disabled,'default loading');
  const credentials=()=>{get('api-key').value='visitor-key-for-tests';get('consent').checked=true;get('generation-mode').value='draft';};
  const generate=async()=>{
    get('generation-form').dispatch('submit');
    await waitFor(()=>!get('generate').disabled && get('api-key').value==='','generation completion');
  };
  const jsonExport=async()=>{
    get('download-json').click();
    const saved=downloads.at(-1);
    assert.equal(saved.name,'proseledger_run.json');
    return JSON.parse(await saved.blob.text());
  };
  return {get,downloads,requests,credentials,generate,jsonExport};
}

test('the browser app loads supplied evidence and produces a downloadable real-engine draft',async()=>{
  const h=await harness();
  assert.equal(h.get('topic').value,defaults.topic);
  assert.ok(h.get('source-notes').value.includes('[S1] Evidence and editing'));
  assert.equal(h.get('provider-preset').value,'openrouter');
  h.credentials();await h.generate();
  assert.equal(h.requests.length,3);
  assert.equal(h.get('api-key').value,'');
  assert.equal(h.get('status-title').textContent,'Generation completed');
  assert.equal(h.get('call-count').textContent,'3');
  assert.equal(h.get('token-count').textContent,'30');
  const saved=await h.jsonExport();
  assert.equal(saved.result.status,'completed');
  assert.equal(saved.result.initialText,draft);
  assert.equal(saved.result.initialScore,0);
  assert.equal(saved.usage.length,3);
  assert.equal(saved.usage.reduce((sum,row)=>sum+row.totalTokens,0),30);
  assert.equal(saved.inputProvenance[0].license,'CC BY 4.0');
  assert.equal(JSON.stringify(saved).includes('visitor-key-for-tests'),false);
  h.get('download-manuscript').click();
  assert.equal(h.downloads.at(-1).name,'proseledger_initial.md');
  assert.ok((await h.downloads.at(-1).blob.text()).includes('Source excerpt license: CC BY 4.0'));
});

test('a preflight error does not relabel or overwrite a previous completed result',async()=>{
  const h=await harness();h.credentials();await h.generate();
  const before=await h.jsonExport();
  h.get('consent').checked=false;
  h.get('generation-form').dispatch('submit');
  await waitFor(()=>!h.get('error-panel').hidden,'preflight error');
  const after=await h.jsonExport();
  assert.equal(h.requests.length,3);
  assert.equal(after.result.status,'completed');
  assert.deepEqual(after,before);
});

test('a later connection test cannot replace exported generation usage or result state',async()=>{
  const h=await harness();h.credentials();await h.generate();
  const before=await h.jsonExport();
  h.credentials();h.get('test-connection').click();
  await waitFor(()=>h.get('status-title').textContent==='Connection verified' && !h.get('generate').disabled,'connection test');
  assert.equal(h.requests.length,4);
  assert.equal(h.get('api-key').value,'');
  assert.equal(h.get('call-count').textContent,'1');
  const after=await h.jsonExport();
  assert.equal(after.result.status,'completed');
  assert.deepEqual(after,before);
  assert.equal(after.usage.length,3);
});

test('a provider failure after ideation preserves a truthful partial outline export',async()=>{
  const h=await harness({failDraft:true});h.credentials();await h.generate();
  assert.equal(h.requests.length,2);
  assert.equal(h.get('status-title').textContent,'Run stopped');
  assert.equal(h.get('api-key').value,'');
  assert.equal(h.get('download-manuscript').disabled,true);
  const saved=await h.jsonExport();
  assert.equal(saved.result.status,'incomplete');
  assert.equal(saved.result.initialText,null);
  assert.deepEqual(saved.result.outline,outline);
  assert.equal(saved.usage.length,1);
  assert.ok(saved.events.some(event=>event.stage==='draft' && event.phase==='error'));
  assert.deepEqual(saved.result.branches,{});
});
