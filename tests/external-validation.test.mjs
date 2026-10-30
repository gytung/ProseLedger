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
