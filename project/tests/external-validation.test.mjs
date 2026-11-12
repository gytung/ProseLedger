import test from 'node:test';
import assert from 'node:assert/strict';
import {checkWithGPTZero, parseDetectorResponse, textFingerprint, GPTZERO_ENDPOINT} from '../docs/assets/external-validation.js';

const text='A proposal will test whether clear language preserves the scope of the original claims. '.repeat(5);
const raw={documents:[{predicted_class:'mixed',class_probabilities:{human:0.1,mixed:0.7,ai:0.2},confidence_category:'high'}],version:'test-version'};
test('detector scan uses the fixed GPTZero destination and binds observations to exact manuscript bytes',async()=>{
  let called;
  const result=await checkWithGPTZero({text,key:'test-gptzero-key',fetchImpl:async(url,options)=>{called={url,options};return {ok:true,json:async()=>raw};}});
  assert.equal(called.url,GPTZERO_ENDPOINT);assert.equal(called.options.credentials,'omit');assert.equal(called.options.redirect,'error');
  assert.deepEqual(JSON.parse(called.options.body),{document:text});assert.equal(called.options.headers['x-api-key'],'test-gptzero-key');
  assert.equal(result.textSHA256,await textFingerprint(text));assert.equal(result.predictedClass,'mixed');
  assert.equal(JSON.stringify(result).includes('test-gptzero-key'),false);assert.equal('score'in result,false);
});
test('unrecognised or invalid detector output is rejected rather than replaced with a default score',()=>{
  for(const value of [{}, {documents:[{}]}, {...raw,documents:[{...raw.documents[0],predicted_class:'unknown'}]}, {...raw,documents:[{...raw.documents[0],class_probabilities:{human:1,mixed:1,ai:1}}]}])assert.throws(()=>parseDetectorResponse(value));
});
test('authentication and usage failures make no automatic paid retries',async()=>{
  for(const status of [400,401,403,429,500]){let calls=0;await assert.rejects(()=>checkWithGPTZero({text,key:'key',fetchImpl:async()=>{calls++;return {ok:false,status};}}));assert.equal(calls,1);}
});
test('bad inputs are stopped before any network request',async()=>{
  for(const options of [{text:'short',key:'key'},{text,key:''},{text,key:'bad\nheader'}])await assert.rejects(()=>checkWithGPTZero({...options,fetchImpl:()=>{throw new Error('Network should not run');}}),error=>!error.message.includes('Network should not run'));
});
test('abort and timeout are bounded and preserve the distinction from a completed scan',async()=>{
  const pending=async(_,{signal})=>new Promise((_,reject)=>{if(signal.aborted)reject(new DOMException('Aborted','AbortError'));else signal.addEventListener('abort',()=>reject(new DOMException('Aborted','AbortError')));});
  await assert.rejects(()=>checkWithGPTZero({text,key:'key',fetchImpl:pending,timeoutMs:5}),/timed out/);
  const controller=new AbortController();controller.abort();await assert.rejects(()=>checkWithGPTZero({text,key:'key',fetchImpl:pending,signal:controller.signal}),{name:'AbortError'});
});
test('legacy uppercase document classes are normalized without altering their probabilities',()=>{
  const result=parseDetectorResponse({documents:[{document_classification:'HUMAN_ONLY',class_probabilities:{human:.8,mixed:.1,ai:.1}}]});
  assert.equal(result.predictedClass,'human');assert.equal(result.probabilities.human,.8);assert.equal(result.detectorVersion,'not reported');
});

test('403 guidance covers an unrecognised key rather than requiring a new paid plan',async()=>{
 await assert.rejects(()=>checkWithGPTZero({text,key:'key',fetchImpl:async()=>({ok:false,status:403})}),/Check that the API key is recognised/);
});

// Isolated browser doubles: no network or account credentials are used here.
import vm from 'node:vm';
import {readFile} from 'node:fs/promises';
const panelCode=(await readFile(new URL('../docs/assets/external-validation.js',import.meta.url),'utf8')).replaceAll('export ','');
class PanelNode {
 constructor(tag){this.tagName=tag;this.children=[];this.listeners={};this.dataset={};this.attributes={};this.value='';this.checked=false;this.disabled=false;this.content='';}
 set textContent(value){this.content=String(value);this.children=[];}get textContent(){return this.content+this.children.map(child=>child.textContent).join('');}
 append(...children){this.children.push(...children);for(const child of children)child.parent=this;}
 replaceChildren(...children){this.children=[];this.content='';this.append(...children);}
 setAttribute(name,value){this.attributes[name]=String(value);}
 addEventListener(name,callback){(this.listeners[name]||=[]).push(callback);}
 async dispatch(name){await Promise.all((this.listeners[name]||[]).map(callback=>callback({target:this})));}
 async click(){if(!this.disabled)await this.dispatch('click');}
 remove(){if(this.parent)this.parent.children=this.parent.children.filter(child=>child!==this);}
}
async function panelHarness({initialDocuments=[],run='run-a',checkText}={}) {
 let documents=initialDocuments,runId=run,busy=false;
 const panel=new PanelNode('div'),downloads=[],blobs=new Map(),calls=[];
 const document={createElement:tag=>new PanelNode(tag),createTextNode:value=>{const node=new PanelNode('#text');node.textContent=value;return node;},body:new PanelNode('body')};
 const create=document.createElement;document.createElement=tag=>{const node=create(tag);if(tag==='a')node.click=()=>downloads.push({name:node.download,blob:blobs.get(node.href)});return node;};
 class TestURL extends URL {static createObjectURL(blob){const name='blob:detector-'+blobs.size;blobs.set(name,blob);return name;}static revokeObjectURL(){}}
 const fakeCheck=async options=>{calls.push(options);return checkText?checkText(options):{...parseDetectorResponse(raw),textSHA256:await textFingerprint(options.text),checkedAt:'2026-10-30T10:00:00Z',source:'GPTZero API'};};
 const context=vm.createContext({document,window:{addEventListener(){}},URL:TestURL,Blob,TextEncoder,crypto:globalThis.crypto,AbortController,DOMException,setTimeout:()=>0,clearTimeout(){},console});
 vm.runInContext(panelCode,context);
 const api=context.mountExternalValidation(panel,{getDocuments:()=>documents,getRunId:()=>runId,isBusy:()=>busy,checkText:fakeCheck});await api.refresh();
 const details=panel.children[0],controls=details.children[2],status=details.children[3],list=details.children[4];
 const [select,key,label,scan,cancel,download]=controls.children,consent=label.children[0];
 return {api,panel,select,key,consent,scan,cancel,download,status,list,calls,downloads,
   update:async(next,nextRun=runId,nextBusy=busy)=>{documents=next;runId=nextRun;busy=nextBusy;await api.refresh();},
   scanNow:async()=>{key.value='test-detector-secret';consent.checked=true;await scan.click();await api.refresh();},
   export:async()=>{await download.click();return JSON.parse(await downloads.at(-1).blob.text());}};
}
const documentA={id:'memory',label:'Memory',text};
test('an already open panel refreshes documents and scan availability after generation or import',async()=>{
 const h=await panelHarness();assert.equal(h.scan.disabled,true);assert.equal(h.select.children.length,0);
 await h.update([documentA],'run-a',true);assert.equal(h.scan.disabled,true);assert.equal(h.select.children[0].textContent,'Memory');
 await h.update([documentA],'run-a',false);assert.equal(h.scan.disabled,false);assert.equal(h.select.value,'memory');
 await h.scanNow();assert.equal(h.calls.length,1);assert.equal(h.key.value,'');assert.equal(h.consent.checked,false);
 assert.match(h.list.textContent,/Matches current text/);assert.equal(h.list.children[0].dataset.match,'current');
});
test('earlier-text and earlier-run observations remain available but cannot masquerade as current results',async()=>{
 const h=await panelHarness({initialDocuments:[documentA]});await h.scanNow();
 const first=await h.export();assert.equal(first.observations[0].runId,'run-a');assert.equal(first.observations[0].currentDocumentMatch,'current');assert.equal(JSON.stringify(first).includes('test-detector-secret'),false);
 h.key.value='unused-detector-secret';h.consent.checked=true;
 await h.update([{...documentA,text:text+' A different retained sentence.'}]);
 assert.equal(h.key.value,'');assert.equal(h.consent.checked,false);assert.equal(h.list.children[0].dataset.match,'earlier_text');assert.match(h.list.textContent,/current version has changed/);
 await h.update([documentA],'run-b');assert.equal(h.list.children[0].dataset.match,'previous_run');assert.match(h.list.textContent,/not a result for the current run/);
 const later=await h.export();assert.equal(later.currentRunId,'run-b');assert.equal(later.observations[0].textSHA256,first.observations[0].textSHA256);assert.equal(later.observations[0].runId,'run-a');assert.equal(later.observations[0].currentDocumentMatch,'previous_run');assert.equal(h.calls.length,1);
});
test('changing workspaces during a scan preserves attribution to the submitted text and run',async()=>{
 let resolveScan;
 const h=await panelHarness({initialDocuments:[documentA],checkText:options=>new Promise(resolve=>{resolveScan=async()=>resolve({...parseDetectorResponse(raw),textSHA256:await textFingerprint(options.text),checkedAt:'2026-10-30T10:00:00Z',source:'GPTZero API'});})});
 h.key.value='test-detector-secret';h.consent.checked=true;const completion=h.scan.click();
 assert.equal(h.calls.length,1);
 await h.update([{...documentA,text:text+' New run content.'}],'run-b');
 await resolveScan();await completion;await h.api.refresh();
 const saved=await h.export();assert.equal(saved.observations[0].runId,'run-a');assert.equal(saved.observations[0].textSHA256,await textFingerprint(text));assert.equal(saved.observations[0].currentDocumentMatch,'previous_run');assert.equal(h.calls.length,1);assert.equal(h.key.value,'');
});
test('switching the selected manuscript requires fresh consent without performing a scan',async()=>{
 const h=await panelHarness({initialDocuments:[documentA,{id:'initial',label:'Initial draft',text:text+' Original.'}]});
 h.key.value='test-detector-secret';h.consent.checked=true;h.select.value='initial';await h.select.dispatch('change');
 assert.equal(h.consent.checked,false);await h.scan.click();assert.equal(h.calls.length,0);assert.match(h.status.textContent,/Confirm the destination/);
});
