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
