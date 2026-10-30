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

test('429 and transient server failures receive at most one retry and respect Retry-After', async () => {
  for(const code of [429,500,502,503,504]) {
    const status=[];let calls=0;
    const client=createModelClient(config,{maxRetryAfterMs:2,retryDelayMs:0,onStatus:x=>status.push(x),fetchImpl:async()=>{
      calls++;return calls===1?new Response(config.key,{status:code,headers:{'Retry-After':'0.002'}}):finished('recovered');
    }});
    assert.equal(await client.callModel([]),'recovered');assert.equal(calls,2);
    assert.equal(status.find(x=>x.phase==='retrying').retryDelayMs,2);
    assert.equal(JSON.stringify(status).includes(config.key),false);
  }
});

test('a long Retry-After is not shortened into an early retry', async () => {
  const status=[];let calls=0;
  const client=createModelClient(config,{maxRetryAfterMs:10,onStatus:s=>status.push(s),fetchImpl:async()=>{
    calls++;return new Response('{}',{status:429,headers:{'Retry-After':'90'}});
  }});
  await assert.rejects(client.callModel([]),/requested retry pause is longer/);
  assert.equal(calls,1);
  assert.equal(status.filter(s=>s.phase==='retrying').length,0);
  await assert.rejects(client.callModel([]),/longer rate-limit pause/);
  assert.equal(calls,1);
});

test('exhausted API credits are not retried as a temporary rate limit', async () => {
  let calls=0;
  const client=createModelClient(config,{retryDelayMs:0,fetchImpl:async()=>{
    calls++;return new Response(JSON.stringify({error:{code:'insufficient_quota',message:config.key}}),{status:429});
  }});
  await assert.rejects(client.callModel([]),error=>/no available quota/.test(error.message)&&!error.message.includes(config.key));
  assert.equal(calls,1);
});

test('reasoning activity prevents a false first-token timeout without becoming answer text', async () => {
  const status=[];let calls=0;
  const client=createModelClient(config,{timeoutMs:1000,firstTokenTimeoutMs:30,idleTimeoutMs:100,onStatus:s=>status.push(s),fetchImpl:async()=>{
    calls++;
    return new Response(new ReadableStream({start(controller){
      controller.enqueue(encoder.encode(event({choices:[{index:0,delta:{reasoning:'private provider reasoning'},finish_reason:null}]})));
      setTimeout(()=>{
        controller.enqueue(encoder.encode(event(delta('final answer','stop'))+event('[DONE]')));
        controller.close();
      },60);
    }}),{headers:{'Content-Type':'text/event-stream'}});
  }});
  assert.equal(await client.callModel([]),'final answer');
  assert.equal(calls,1);
  assert.ok(!JSON.stringify(status).includes('private provider reasoning'));
  assert.equal(status.at(-1).outputCharacters,'final answer'.length);
});

test('a reasoning-only truncated answer explains the shared token budget', async () => {
  const client=createModelClient(config,{fetchImpl:async()=>sse(event({choices:[{index:0,delta:{reasoning:'hidden'},finish_reason:'length'}]}))});
  await assert.rejects(client.callModel([]),/token limit includes reasoning/);
});

test('three branch calls are queued with at most two in flight', async () => {
  const status=[],pending=[];let calls=0;
  const client=createModelClient(config,{onStatus:s=>status.push(s),fetchImpl:async()=>{
    calls++;return new Promise(resolve=>pending.push(resolve));
  }});
  const a=client.callModel([],{stage:'a'}),b=client.callModel([],{stage:'b'}),c=client.callModel([],{stage:'c'});
  assert.equal(calls,2);
  assert.ok(status.some(s=>s.stage==='c'&&s.phase==='queued'));
  pending.shift()(finished('a'));assert.equal(await a,'a');
  assert.equal(calls,3);
  pending.shift()(finished('b'));pending.shift()(finished('c'));
  assert.deepEqual(await Promise.all([b,c]),['b','c']);
});

test('a queued branch can be cancelled without sending a request or blocking later calls', async () => {
  const pending=[];let calls=0;
  const client=createModelClient(config,{maxConcurrent:1,fetchImpl:async()=>{calls++;return new Promise(resolve=>pending.push(resolve));}});
  const a=client.callModel([]);
  const controller=new AbortController();
  const b=client.callModel([],{signal:controller.signal});controller.abort();
  await assert.rejects(b,{name:'AbortError'});assert.equal(calls,1);
  pending.shift()(finished('a'));await a;
  const c=client.callModel([]);assert.equal(calls,2);
  pending.shift()(finished('c'));assert.equal(await c,'c');
});

test('new requests share a provider rate-limit cooldown instead of immediately retrying it', async () => {
  let client,other,limitedAt=0;
  const fetched=[];
  client=createModelClient(config,{maxRetryAfterMs:100,onStatus:s=>{
    if(s.stage==='first'&&s.phase==='retrying'&&!other) other=client.callModel([],{stage:'other'});
  },fetchImpl:async()=>{
    fetched.push(Date.now());
    if(fetched.length===1){limitedAt=Date.now();return new Response('{}',{status:429,headers:{'Retry-After':'0.03'}});}
    return finished('complete');
  }});
  assert.equal(await client.callModel([],{stage:'first'}),'complete');
  assert.equal(await other,'complete');
  assert.equal(fetched.length,3);
  assert.ok(fetched.slice(1).every(time=>time-limitedAt>=25),'Both follow-up requests must respect the cooldown.');
});

test('clearing credentials cancels queued as well as active requests', async () => {
  let calls=0;
  const client=createModelClient(config,{maxConcurrent:1,fetchImpl:async()=>{calls++;return new Promise(()=>{});}});
  const a=client.callModel([]),b=client.callModel([]),c=client.callModel([]);
  client.clear();
  const settled=await Promise.allSettled([a,b,c]);
  assert.equal(calls,1);
  assert.ok(settled.every(item=>item.status==='rejected'&&item.reason.name==='AbortError'));
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
