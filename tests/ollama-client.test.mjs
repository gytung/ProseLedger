import test from 'node:test';
import assert from 'node:assert/strict';
import {OLLAMA_MODEL, OLLAMA_DIGEST, validateOllamaConfig, createOllamaClient} from '../docs/assets/ollama-client.js';
const config={base:'http://127.0.0.1:11434',model:OLLAMA_MODEL};
const messages=[{role:'system',content:'Return JSON.'},{role:'user',content:'Edit this section.'}];
const tags=(digest=OLLAMA_DIGEST)=>new Response(JSON.stringify({models:[{name:OLLAMA_MODEL,digest,size:4700000000}]}));
function ndjson(events,split=0) {
 const bytes=new TextEncoder().encode(events.map(e=>JSON.stringify(e)).join('\n'));let i=0;
 return new Response(new ReadableStream({pull(controller){if(i===bytes.length){controller.close();return;}const end=Math.min(bytes.length,i+(split||bytes.length));controller.enqueue(bytes.slice(i,end));i=end;}}));
}
function finished(extra={}){return{model:OLLAMA_MODEL,message:{content:'{"text":"A clearer proposal."}'},done:true,done_reason:'stop',prompt_eval_count:100,eval_count:20,...extra};}

test('only explicit loopback ports and pinned model tag are allowed',()=>{
 for(const base of ['http://127.0.0.1:11434','http://localhost:11436/'])assert.match(validateOllamaConfig({base}).base,/1143[46]$/);
 for(const base of ['http://127.1:11434','http://2130706433:11434','http://localhost:80','http://localhost:11434/api/chat','https://localhost:11434','http://0.0.0.0:11434','http://192.168.1.2:11434','http://user:password@localhost:11434','http://localhost:11434?key=x','http://localhost:11434#x','http://localhost.example.com:11434'])assert.throws(()=>validateOllamaConfig({base}));
 assert.throws(()=>validateOllamaConfig({...config,model:'qwen2.5:72b'}));
});
test('probe checks tag and digest without inference or credentials',async()=>{
 const calls=[];const c=createOllamaClient({...config,key:'must-not-travel'},{fetchImpl:async(url,options)=>{calls.push(url);assert.equal(options.method,'GET');assert.equal(options.headers,undefined);assert.equal(options.credentials,'omit');assert.equal(options.redirect,'error');assert.equal(options.referrerPolicy,'no-referrer');return tags('sha256:'+OLLAMA_DIGEST);}});
 assert.equal((await c.probe()).digest,OLLAMA_DIGEST);assert.deepEqual(calls,[config.base+'/api/tags']);assert.ok(!JSON.stringify(c).includes('must-not-travel'));
});
test('probe rejects missing or mismatched model without fallback',async()=>{
 for(const response of [new Response(JSON.stringify({models:[]})),tags('a'.repeat(64)),new Response(JSON.stringify({models:[{name:'qwen2.5:7b',digest:OLLAMA_DIGEST}]}))]){
  let calls=0;const c=createOllamaClient(config,{fetchImpl:async()=>{calls++;return response;}});await assert.rejects(c.probe(),/model|weights/i);assert.equal(calls,1);
 }
});
test('section writer uses fixed local decoding settings and handles split UTF-8',async()=>{
 const usages=[],seen=[];const c=createOllamaClient(config,{onUsage:u=>usages.push(u),fetchImpl:async(url,options)=>{
  seen.push(url);if(url.endsWith('/tags'))return tags();const body=JSON.parse(options.body);assert.deepEqual(body.options,{num_ctx:8192,num_predict:2200,temperature:.2,seed:44});assert.equal(body.model,OLLAMA_MODEL);assert.equal(body.stream,true);assert.equal(body.keep_alive,'5m');assert.deepEqual(options.headers,{'Content-Type':'application/json'});assert.equal(body.format.required[0],'text');
  return ndjson([finished({message:{content:'{"text":"caf\u00e9"}'}})],1);
 }});assert.equal(await c.callModel(messages,{stage:'rewrite_section_3'}),'{'+'"text":"caf\u00e9"}');assert.equal(usages[0].local,true);assert.equal(usages[0].totalTokens,120);assert.equal(seen.length,2);
});
test('initial generation and review cannot accidentally run on local writer',async()=>{
 const c=createOllamaClient(config,{fetchImpl:()=>assert.fail('No request permitted')});
 for(const stage of ['generate_initial_proposal','audit_sections','rewrite_section_7','rewrite_section_connection_test'])await assert.rejects(c.callModel(messages,{stage}),/reserved/);
});
test('oversized prompts are rejected by bytes instead of silently truncated',async()=>{
 const c=createOllamaClient(config,{fetchImpl:()=>assert.fail('No request permitted')});
 await assert.rejects(c.callModel([{role:'user',content:'\u00e9'.repeat(14001)}],{stage:'rewrite_section_1'}),/context budget/);
});
test('unfinished, length-limited and context-overflow streams are rejected',async()=>{
 for(const events of [[{message:{content:'partial'},done:false}],[finished({done_reason:'length'})],[finished({prompt_eval_count:7936})],[finished({model:'other:tag'})],[{error:'sensitive local error detail'}]]){
  const c=createOllamaClient(config,{fetchImpl:async url=>url.endsWith('/tags')?tags():ndjson(events)});
  await assert.rejects(c.callModel(messages,{stage:'rewrite_section_1'}),e=>!e.message.includes('sensitive local error detail'));
 }
});
test('legacy completed events without done_reason remain supported',async()=>{
 const value=finished();delete value.done_reason;const c=createOllamaClient(config,{fetchImpl:async url=>url.endsWith('/tags')?tags():ndjson([value])});assert.match(await c.callModel(messages,{stage:'rewrite_section_1'}),/clearer/);
});
test('CORS and HTTP failures return fixed actionable messages',async()=>{
 for(const [fetchImpl,pattern] of [[async()=>{throw new TypeError('private network detail');},/OLLAMA_ORIGINS/],[async()=>new Response('private server response',{status:403}),/website origin/],[async()=>new Response('private server response',{status:500}),/HTTP 500/]]){
  const c=createOllamaClient(config,{fetchImpl});await assert.rejects(c.probe(),e=>pattern.test(e.message)&&!e.message.includes('private'));
 }
});
test('timeout terminates unresponsive fetch even if fetch ignores its signal',async()=>{
 const c=createOllamaClient(config,{timeoutMs:20,fetchImpl:()=>new Promise(()=>{})});await assert.rejects(c.probe(),/time limit/);
});
test('abort before a call and during a stream never returns partial content',async()=>{
 const abort=new AbortController();abort.abort();const c=createOllamaClient(config,{fetchImpl:()=>assert.fail('No request permitted')});await assert.rejects(c.callModel(messages,{stage:'rewrite_section_1',signal:abort.signal}),{name:'AbortError'});
 const active=new AbortController();let started;const ready=new Promise(r=>started=r);
 const d=createOllamaClient(config,{fetchImpl:async url=>url.endsWith('/tags')?tags():new Response(new ReadableStream({start(controller){controller.enqueue(new TextEncoder().encode(JSON.stringify({message:{content:'partial'},done:false})+'\n'));started();}}))});
 const pending=d.callModel(messages,{stage:'rewrite_section_1',signal:active.signal});await ready;active.abort();await assert.rejects(pending,{name:'AbortError'});
});
test('clear cancels an active connection and prevents future use',async()=>{
 let requested;const ready=new Promise(r=>requested=r);const c=createOllamaClient(config,{fetchImpl:()=>{requested();return new Promise(()=>{});}});const pending=c.probe();await ready;c.clear();await assert.rejects(pending,{name:'AbortError'});await assert.rejects(c.probe(),/cleared/);
});
test('oversized service output is rejected before it enters an export',async()=>{
 const c=createOllamaClient(config,{fetchImpl:async url=>url.endsWith('/tags')?tags():new Response(' '.repeat(2000001))});await assert.rejects(c.callModel(messages,{stage:'rewrite_section_1'}),/oversized/);
});
