import test from 'node:test';
import assert from 'node:assert/strict';
import { createModelClient, providerEndpoint } from '../docs/assets/api-client.js';

const config = { base: 'https://example.com/v1', model: 'test-model', key: 'test-only-not-a-real-key' };

test('reject unsafe destination forms before sending a key', () => {
  for (const url of ['http://example.com/v1', 'https://u:p@example.com/v1', 'https://example.com/v1?key=x',
    'https://example.com/v1#x', 'https://localhost/v1', 'https://127.0.0.1/v1', 'https://[::1]/v1']) {
    assert.throws(() => providerEndpoint(url));
  }
  assert.equal(providerEndpoint('https://example.com/v1/'), 'https://example.com/v1/chat/completions');
  assert.equal(providerEndpoint('https://example.com/v1/chat/completions'), 'https://example.com/v1/chat/completions');
});

test('key travels only in Authorization and cannot be reused after clearing', async () => {
  const usages = [];
  const client = createModelClient(config, {
    onUsage: u => usages.push(u), fetchImpl: async (url, options) => {
      assert.equal(url, 'https://example.com/v1/chat/completions');
      assert.equal(options.headers.Authorization, `Bearer ${config.key}`);
      assert.equal(options.body.includes(config.key), false);
      assert.equal(options.credentials, 'omit');
      assert.equal(options.redirect, 'error');
      assert.equal(options.referrerPolicy, 'no-referrer');
      return new Response(JSON.stringify({ choices:[{message:{content:'done'}}], usage:{total_tokens:8} }));
    },
  });
  assert.equal(await client.callModel([{role:'user',content:'hello'}]), 'done');
  assert.equal(usages[0].totalTokens, 8);
  assert.equal(JSON.stringify(client).includes(config.key), false);
  client.clear();
  await assert.rejects(client.callModel([]), /cleared/);
});

test('provider errors do not expose echoed keys and are never auto-retried', async () => {
  let calls = 0;
  const client = createModelClient(config, {fetchImpl: async () => {
    calls += 1;
    return new Response(config.key, {status:401});
  }});
  await assert.rejects(client.callModel([]), error => {
    assert.match(error.message, /Authentication failed/);
    assert.equal(error.message.includes(config.key), false);
    return true;
  });
  assert.equal(calls, 1);
});

test('cancelled runs send no further requests', async () => {
  const abort = new AbortController();
  abort.abort();
  const client = createModelClient(config, {fetchImpl: async () => assert.fail('Request should not be sent')});
  await assert.rejects(client.callModel([], {signal:abort.signal}), {name:'AbortError'});
});

test('CORS failures are explained without including raw error details', async () => {
  const client = createModelClient(config, {fetchImpl: async () => {throw new TypeError(config.key);}});
  await assert.rejects(client.callModel([]), /CORS support/);
});

test('truncated model outputs and missing text are rejected', async () => {
  for (const choice of [{finish_reason:'length',message:{content:'incomplete'}},{message:{content:null}}]) {
    const client=createModelClient(config,{fetchImpl:async()=>new Response(JSON.stringify({choices:[choice]}))});
    await assert.rejects(client.callModel([]));
  }
});

const encoder = new TextEncoder();
const event = value => `data: ${typeof value === 'string' ? value : JSON.stringify(value)}\r\n\r\n`;
const delta = (text, finish = null) => ({choices:[{index:0,delta:{content:text},finish_reason:finish}]});
function sse(text, split = 0) {
  const bytes = encoder.encode(text);
  let offset = 0;
  return new Response(new ReadableStream({pull(controller) {
    if (offset >= bytes.length) {controller.close();return;}
    const end = Math.min(bytes.length, offset + (split || bytes.length));
    controller.enqueue(bytes.slice(offset,end));offset=end;
  }}), {headers:{'Content-Type':'text/event-stream'}});
}
const finished = text => sse(event(delta(text)) + event(delta('', 'stop')) + event('[DONE]'));

test('SSE preserves split UTF-8 and accepts comments, repeated finish, and usage-only events', async () => {
  const status=[],usage=[];
  const response = ': OPENROUTER PROCESSING\r\n\r\n' + event(delta('Hello \u4f60\u597d ')) +
    event(delta('world', 'stop')) + event({choices:[{index:0,delta:{},finish_reason:'stop'}]}) +
    event({choices:[],usage:{prompt_tokens:11,completion_tokens:7,total_tokens:18},model:'verified-model'}) + event('[DONE]');
  const client=createModelClient({...config,base:'https://openrouter.ai/api/v1'}, {
    onStatus:x=>status.push(x),onUsage:x=>usage.push(x),fetchImpl:async(url,options)=>{
      const body=JSON.parse(options.body);
      assert.equal(body.stream,true);assert.deepEqual(body.stream_options,{include_usage:true});
      assert.equal(body.max_tokens,1200);
      return sse(response,1);
    },
  });
  assert.equal(await client.callModel([],{stage:'rewrite_memory_2',maxTokens:1200}), 'Hello \u4f60\u597d world');
  assert.equal(usage.length,1);assert.equal(usage[0].totalTokens,18);assert.equal(usage[0].model,'verified-model');
  assert.equal(status.at(-1).phase,'completed');assert.ok(status.at(-1).receivedBytes>0);
  assert.equal(status.at(-1).outputCharacters,'Hello \u4f60\u597d world'.length);
  assert.ok(!JSON.stringify({status,usage}).includes(config.key));
});

test('OpenAI receives per-stage max_completion_tokens with stream usage enabled', async () => {
  const client=createModelClient({...config,base:'https://api.openai.com/v1'}, {fetchImpl:async(url,options)=>{
    const body=JSON.parse(options.body);assert.equal(body.max_completion_tokens,2200);
    assert.equal(body.max_tokens,undefined);assert.equal(body.stream,true);
    assert.deepEqual(body.stream_options,{include_usage:true});return finished('ok');
  }});
  assert.equal(await client.callModel([],{maxTokens:2200}),'ok');
});

test('DONE completes a response without waiting for a provider to close its socket', async () => {
  let cancelled=false;
  const body=new ReadableStream({start(controller){controller.enqueue(encoder.encode(event(delta('complete','stop'))+event('[DONE]')));},
    cancel(){cancelled=true;}});
  const client=createModelClient(config,{fetchImpl:async()=>new Response(body,{headers:{'Content-Type':'text/event-stream'}})});
  assert.equal(await client.callModel([]),'complete');assert.equal(cancelled,true);
});

test('JSON remains compatible when a provider ignores the streaming request', async () => {
  const client=createModelClient(config,{fetchImpl:async()=>new Response(JSON.stringify({choices:[{message:{content:'plain JSON'},finish_reason:'stop'}]}))});
  assert.equal(await client.callModel([]),'plain JSON');
});

test('stream truncation and malformed events fail without substituting partial text', async () => {
  for(const response of [event(delta('partial','length')),event(delta('partial'))+event('not-json'),event(delta('partial','error'))]) {
    let calls=0,usages=0;
    const client=createModelClient(config,{fetchImpl:async()=>{calls++;return sse(response);},onUsage:()=>usages++});
    await assert.rejects(client.callModel([],{stage:'draft'}),/draft:/);
    assert.equal(calls,1);assert.equal(usages,0);
  }
});

test('an interrupted stream is retried once and a failed second attempt never becomes a result', async () => {
  let calls=0,usages=0;
  const client=createModelClient(config,{retryDelayMs:0,onUsage:()=>usages++,fetchImpl:async()=>{calls++;return sse(event(delta('partial')));}});
  await assert.rejects(client.callModel([]),/stream ended before completion.*Both allowed attempts/);
  assert.equal(calls,2);assert.equal(usages,0);
});

test('explicit unsupported streaming falls back once and is remembered only for this client', async () => {
  const requests=[];
  const client=createModelClient(config,{fetchImpl:async(url,options)=>{
    const body=JSON.parse(options.body);requests.push(body);
    if(requests.length===1)return new Response(JSON.stringify({error:{param:'stream',message:'Streaming is not supported by this model.'}}),{status:400});
    return new Response(JSON.stringify({choices:[{message:{content:'standard answer'},finish_reason:'stop'}]}));
  }});
  assert.equal(await client.callModel([]),'standard answer');
  assert.equal(await client.callModel([]),'standard answer');
  assert.deepEqual(requests.map(r=>r.stream),[true,false,false]);
});

test('a generic 400 is not mistaken for unsupported streaming', async () => {
  let calls=0;
  const client=createModelClient(config,{fetchImpl:async()=>{calls++;return new Response(JSON.stringify({error:{message:`Invalid model ${config.key}`}}),{status:400});}});
  await assert.rejects(client.callModel([]),error=>!error.message.includes(config.key)&&/rejected the request/.test(error.message));
  assert.equal(calls,1);
});

test('429 and transient server failures receive at most one retry, with Retry-After capped', async () => {
  for(const code of [429,500,502,503,504]) {
    const status=[];let calls=0;
    const client=createModelClient(config,{maxRetryAfterMs:2,retryDelayMs:0,onStatus:x=>status.push(x),fetchImpl:async()=>{
      calls++;return calls===1?new Response(config.key,{status:code,headers:{'Retry-After':'999999'}}):finished('recovered');
    }});
    assert.equal(await client.callModel([]),'recovered');assert.equal(calls,2);
    assert.equal(status.find(x=>x.phase==='retrying').retryDelayMs,2);
    assert.equal(JSON.stringify(status).includes(config.key),false);
  }
});

test('midstream provider errors are not ignored or concatenated with a retried answer', async () => {
  let calls=0;
  const client=createModelClient(config,{retryDelayMs:0,fetchImpl:async()=>{
    calls++;return calls===1?sse(event(delta('discard me'))+event({error:{code:503,message:config.key}})):finished('valid answer');
  }});
  assert.equal(await client.callModel([]),'valid answer');assert.equal(calls,2);
});

test('first-response timeout can retry once and is bounded even if fetch ignores cancellation', async () => {
  let calls=0;
  const client=createModelClient(config,{timeoutMs:500,firstTokenTimeoutMs:8,retryDelayMs:0,fetchImpl:async()=>{
    calls++;return calls===1?new Promise(()=>{}):finished('after timeout');
  }});
  assert.equal(await client.callModel([]),'after timeout');assert.equal(calls,2);
});

test('idle stream timeout discards its partial answer before retrying', async () => {
  let calls=0,cancelled=false;
  const client=createModelClient(config,{timeoutMs:500,firstTokenTimeoutMs:100,idleTimeoutMs:8,retryDelayMs:0,fetchImpl:async()=>{
    calls++;
    if(calls>1)return finished('fresh full answer');
    return new Response(new ReadableStream({start(controller){controller.enqueue(encoder.encode(event(delta('discard partial'))));},cancel(){cancelled=true;}}),{headers:{'Content-Type':'text/event-stream'}});
  }});
  assert.equal(await client.callModel([]),'fresh full answer');assert.equal(calls,2);assert.equal(cancelled,true);
});

test('overall call deadline prevents another retry and reports the exact stage', async () => {
  let calls=0;
  const client=createModelClient(config,{timeoutMs:12,firstTokenTimeoutMs:100,retryDelayMs:0,fetchImpl:async()=>{calls++;return new Promise(()=>{});}});
  await assert.rejects(client.callModel([],{stage:'audit_initial'}),/audit_initial:.*deadline/);
  assert.equal(calls,1);
});

test('cancelling during backoff prevents the second request', async () => {
  const controller=new AbortController();let calls=0;
  const client=createModelClient(config,{retryDelayMs:100,onStatus:event=>{if(event.phase==='retrying')controller.abort();},fetchImpl:async()=>{calls++;return new Response('limited',{status:429});}});
  await assert.rejects(client.callModel([],{signal:controller.signal}),{name:'AbortError'});
  assert.equal(calls,1);
});

test('parallel calls sharing an AbortSignal are independently cancelled without retries', async () => {
  const controller=new AbortController();let calls=0;
  const client=createModelClient(config,{fetchImpl:async()=>{calls++;return new Promise(()=>{});}});
  const a=client.callModel([],{stage:'parallel_a',signal:controller.signal});
  const b=client.callModel([],{stage:'parallel_b',signal:controller.signal});
  controller.abort();
  const settled=await Promise.allSettled([a,b]);
  assert.ok(settled.every(x=>x.status==='rejected'&&x.reason.name==='AbortError'));assert.equal(calls,2);
});

test('clearing a key cancels an active stream and does not leak the key into status', async () => {
  const status=[];let client;
  client=createModelClient(config,{onStatus:s=>{status.push(s);if(s.phase==='receiving')client.clear();},fetchImpl:async()=>sse(event(delta('received'))+event('[DONE]'))});
  await assert.rejects(client.callModel([]),{name:'AbortError'});
  assert.ok(!JSON.stringify(status).includes(config.key));
  await assert.rejects(client.callModel([]),/cleared/);
});

test('credential echo across SSE fragments is discarded before exposing response text', async () => {
  const status=[];let usages=0;
  const client=createModelClient(config,{onStatus:s=>status.push(s),onUsage:()=>usages++,fetchImpl:async()=>sse(event(delta(config.key.slice(0,9)))+event(delta(config.key.slice(9),'stop'))+event('[DONE]'),3)});
  await assert.rejects(client.callModel([]),/credential material/);
  assert.equal(usages,0);assert.ok(!JSON.stringify(status).includes(config.key));
});

test('oversized responses and output token limits fail before producing a result', async () => {
  let calls=0;
  const client=createModelClient(config,{fetchImpl:async()=>{calls++;return new Response('x'.repeat(2_000_001));}});
  for(const maxTokens of [0,8001,2.5,NaN])await assert.rejects(client.callModel([],{maxTokens}),/Output limit/);
  assert.equal(calls,0);
  await assert.rejects(client.callModel([]),/size limit/);assert.equal(calls,1);
});

test('a network error after response headers retries without labeling it a CORS failure', async () => {
  let calls=0;
  const client=createModelClient(config,{retryDelayMs:0,fetchImpl:async()=>{
    calls++;
    if(calls>1)return finished('recovered network');
    return new Response(new ReadableStream({pull(controller){controller.error(new TypeError(config.key));}}),{headers:{'Content-Type':'text/event-stream'}});
  }});
  assert.equal(await client.callModel([]),'recovered network');assert.equal(calls,2);
});
