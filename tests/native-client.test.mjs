import test from 'node:test';
import assert from 'node:assert/strict';
import {createNativeClient,validateNativeConfig} from '../docs/assets/native-client.js';

const token='fixture-pair-code-not-an-account-token';
const config={base:'http://127.0.0.1:11437',token,model:'account-default'};
const messages=[{role:'system',content:'Return JSON.'},{role:'user',content:'Review this section.'}];
const status=()=>new Response(JSON.stringify({ready:true,authenticated:true,model:'account-default'}));
function answer(options,extra={}) {return new Response(JSON.stringify({requestId:JSON.parse(options.body).requestId,text:'{"findings":[]}',model:'account-default',usage:{input_tokens:10,output_tokens:5},...extra}));}

test('only explicit loopback connector address and valid model IDs are accepted',()=>{
 assert.equal(validateNativeConfig({...config,base:'http://localhost:11437/',model:''}).model,'account-default');
 for(const base of ['https://localhost:11437','http://127.1:11437','http://2130706433:11437','http://0.0.0.0:11437','http://192.168.0.1:11437','http://localhost:11434','http://user:pw@localhost:11437','http://localhost:11437/status','http://localhost:11437?token=x','http://localhost.example.com:11437'])assert.throws(()=>validateNativeConfig({...config,base}));
 for(const model of ['--model', '../file', 'bad\nmodel', 'x'.repeat(161), token])assert.throws(()=>validateNativeConfig({...config,model}));
 assert.throws(()=>validateNativeConfig({...config,token:'short'}));
});
test('pair code is confined to header and never exported through client state or usage',async()=>{
 const usage=[],events=[];
 const client=createNativeClient(config,{onUsage:u=>usage.push(u),onStatus:e=>events.push(e),fetchImpl:async(url,options)=>{
  assert.ok(url.startsWith(config.base+'/'));assert.equal(options.headers['X-ProseLedger-Token'],token);
  assert.equal(options.headers.Authorization,undefined);assert.equal(options.credentials,'omit');assert.equal(options.redirect,'error');assert.equal(options.referrerPolicy,'no-referrer');
  assert.ok(!url.includes(token));assert.ok(!String(options.body).includes(token));
  return url.endsWith('/status')?status():answer(options);
 }});
 await client.probe();assert.equal(await client.callModel(messages,{stage:'audit_sections'}),'{"findings":[]}');
 assert.equal(usage[0].totalTokens,15);assert.equal(usage[0].backend,'codex-account');
 for(const data of [client,usage,events])assert.ok(!JSON.stringify(data).includes(token));
});
test('writer stage, unknown roles and token-bearing input never trigger requests',async()=>{
 const client=createNativeClient(config,{fetchImpl:()=>assert.fail('No request allowed')});
 for(const stage of ['rewrite_section_1','test_connection','audit_repaired_full_3',''])await assert.rejects(client.callModel(messages,{stage}),/only/);
 for(const input of [[{role:'assistant',content:'x'}],[{role:'user',content:token}],[{role:'user',content:'x',tools:[]}],[]])await assert.rejects(client.callModel(input,{stage:'audit_sections'}));
 await assert.rejects(client.callModel([{role:'user',content:'é'.repeat(100000)}],{stage:'audit_sections'}),/size limit/);
});
test('bad auth state and response secrets are rejected without echoing provider data',async()=>{
 for(const result of [{ready:true,authenticated:false},{ready:false,authenticated:false},{ready:true,authenticated:true,extra:token}]){
  const c=createNativeClient(config,{fetchImpl:async()=>new Response(JSON.stringify(result))});
  await assert.rejects(c.probe(),e=>!e.message.includes(token));
 }
 const c=createNativeClient(config,{fetchImpl:async()=>new Response('provider-private-detail',{status:502})});
 await assert.rejects(c.probe(),e=>!e.message.includes('provider-private-detail'));
});
test('result requires correct request ID and non-empty complete text',async()=>{
 for(const extra of [{requestId:'different-request'},{text:''},{text:'x'.repeat(100001)},{text:token}]){
  const c=createNativeClient(config,{fetchImpl:async(_url,options)=>answer(options,extra)});
  await assert.rejects(c.callModel(messages,{stage:'audit_sections'}));
 }
});
test('pre-aborted calls do not contact the local runtime',async()=>{
 const controller=new AbortController();controller.abort();const c=createNativeClient(config,{fetchImpl:()=>assert.fail('No request allowed')});
 await assert.rejects(c.callModel(messages,{stage:'audit_sections',signal:controller.signal}),{name:'AbortError'});
});
test('abort terminates even an uncooperative fetch and sends scoped cancellation',async()=>{
 const controller=new AbortController(),seen=[];let begin;const ready=new Promise(r=>begin=r);
 const c=createNativeClient(config,{fetchImpl:(url,options)=>{seen.push({url,options});if(url.endsWith('/cancel'))return Promise.resolve(new Response('{}'));begin();return new Promise(()=>{});}});
 const pending=c.callModel(messages,{stage:'audit_sections',signal:controller.signal});await ready;controller.abort();await assert.rejects(pending,{name:'AbortError'});
 assert.equal(seen.length,2);assert.ok(seen[1].url.endsWith('/cancel'));
 assert.deepEqual(JSON.parse(seen[1].options.body),{requestId:JSON.parse(seen[0].options.body).requestId});
 assert.equal(seen[1].options.headers['X-ProseLedger-Token'],token);
});
test('deadline cancels the account request without waiting for an ignored abort signal',async()=>{
 const seen=[];const c=createNativeClient(config,{timeoutMs:15,fetchImpl:(url,options)=>{seen.push(url);return url.endsWith('/cancel')?Promise.resolve(new Response('{}')):new Promise(()=>{});}});
 await assert.rejects(c.callModel(messages,{stage:'audit_sections'}),/timed out/);assert.equal(seen.length,2);
});
test('abort during a stalled response body never adopts its partial output',async()=>{
 const controller=new AbortController();let start;const ready=new Promise(r=>start=r);let cancelled=false;
 const c=createNativeClient(config,{fetchImpl:async(url)=>url.endsWith('/cancel')?new Response('{}'):new Response(new ReadableStream({start(stream){stream.enqueue(new TextEncoder().encode('{"text":"partial'));start();},cancel(){cancelled=true;}}))});
 const pending=c.callModel(messages,{stage:'audit_sections',signal:controller.signal});await ready;controller.abort();await assert.rejects(pending,{name:'AbortError'});assert.ok(cancelled);
});
test('clear stops pending requests, removes access and prevents future calls',async()=>{
 let start;const ready=new Promise(r=>start=r);const c=createNativeClient(config,{fetchImpl:(url)=>url.endsWith('/cancel')?Promise.resolve(new Response('{}')):(start(),new Promise(()=>{}))});
 const pending=c.callModel(messages,{stage:'audit_sections'});await ready;c.clear();await assert.rejects(pending,{name:'AbortError'});await assert.rejects(c.probe(),/Reconnect/);assert.ok(!JSON.stringify(c).includes(token));
});
test('invalid JSON and oversized bodies are bounded and safely reported',async()=>{
 for(const body of ['[]','not JSON',' '.repeat(2000001)]){
  const c=createNativeClient(config,{fetchImpl:async()=>new Response(body)});await assert.rejects(c.probe());
 }
});
test('network failures provide actionable local-network instructions',async()=>{
 const c=createNativeClient(config,{fetchImpl:async()=>{throw new TypeError('private socket data');}});await assert.rejects(c.probe(),e=>/local-network/.test(e.message)&&!e.message.includes('private socket'));
});
