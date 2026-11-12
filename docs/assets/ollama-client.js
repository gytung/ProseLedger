/** A credential-free, loopback-only section writer for the pinned desktop model. */
import {OLLAMA_MODEL, OLLAMA_DIGEST, validateOllamaConfig} from './local-model-identity.js?v=20261113d';
export {OLLAMA_MODEL, OLLAMA_DIGEST, validateOllamaConfig};
const CONTEXT = 8192;
const MAX_BYTES = 2_000_000;
const MAX_TEXT = 100_000;
const aborted = () => new DOMException('Local writing cancelled. Completed stages remain available.', 'AbortError');
const CONNECTION_HELP = 'Cannot reach local Ollama. Start it on the selected loopback port, allow this site with OLLAMA_ORIGINS=https://gytung.github.io, and allow local-network access if your browser asks. No cloud fallback was used.';


function raceAbort(promise, signal) {
  if (signal.aborted) return Promise.reject(aborted());
  return new Promise((resolve, reject) => {
    const abort = () => { signal.removeEventListener('abort', abort); reject(aborted()); };
    signal.addEventListener('abort', abort, {once: true});
    Promise.resolve(promise).then(value => { signal.removeEventListener('abort', abort); resolve(value); }, error => { signal.removeEventListener('abort', abort); reject(error); });
  });
}

async function readBody(response, signal, maximum, onChunk) {
  const reader = response.body?.getReader();
  if (!reader) {
    const bytes = new TextEncoder().encode(await raceAbort(response.text(), signal));
    if (bytes.length > maximum) throw new Error('Local Ollama returned an oversized response.');
    onChunk(bytes); return;
  }
  let size = 0, complete = false;
  try {
    while (true) {
      const {value, done} = await raceAbort(reader.read(), signal);
      if (done) { complete = true; break; }
      size += value.byteLength;
      if (size > maximum) throw new Error('Local Ollama returned an oversized response.');
      if (onChunk(value) === false) break;
    }
  } finally {
    if (!complete) Promise.resolve(reader.cancel()).catch(() => {});
    reader.releaseLock();
  }
}

function json(text) {
  try { return JSON.parse(text); }
  catch { throw new Error('Local Ollama returned invalid JSON. No partial rewrite was kept.'); }
}
const count = value => Number.isInteger(value) && value >= 0 ? value : null;

export function createOllamaClient(config, {
  onUsage = () => {}, onStatus = () => {}, fetchImpl = globalThis.fetch, timeoutMs = 600000,
} = {}) {
  const connection = validateOllamaConfig(config);
  const limit = Number.isFinite(timeoutMs) ? Math.min(600000, Math.max(1, timeoutMs)) : 600000;
  let closed = false, readiness = null;
  const active = new Set();

  async function operation(signal, duration, callback) {
    if (closed) throw new Error('The local model connection has been cleared. Test it again before resuming.');
    if (signal?.aborted) throw aborted();
    const controller = new AbortController();
    const abort = () => controller.abort();
    signal?.addEventListener('abort', abort, {once: true});
    active.add(controller);
    let timedOut = false;
    const timer = setTimeout(() => { timedOut = true; controller.abort(); }, duration);
    try {
      return await callback(controller.signal);
    } catch (error) {
      if (timedOut) throw new Error('Local Ollama exceeded its request time limit. Completed stages are saved; resume when it is ready. No cloud fallback was used.');
      if (signal?.aborted || closed || controller.signal.aborted) throw aborted();
      if (error instanceof TypeError) throw new Error(CONNECTION_HELP);
      throw error;
    } finally {
      clearTimeout(timer); signal?.removeEventListener('abort', abort); active.delete(controller);
    }
  }

  async function request(path, options, signal) {
    let response;
    try {
      response = await raceAbort(fetchImpl(connection.base + path, {
        ...options, signal, mode: 'cors', credentials: 'omit', redirect: 'error', cache: 'no-store', referrerPolicy: 'no-referrer',
      }), signal);
    } catch (error) { if (signal.aborted) throw aborted(); throw new Error(CONNECTION_HELP); }
    if (!response.ok) {
      Promise.resolve(response.body?.cancel()).catch(() => {});
      if (response.status === 403) throw new Error('Ollama refused this website origin. Set OLLAMA_ORIGINS=https://gytung.github.io and restart Ollama. Keep the server bound to loopback.');
      if (response.status === 404) throw new Error('The local Ollama endpoint or selected model was not found. Check the port and install ' + OLLAMA_MODEL + '.');
      throw new Error('Local Ollama returned HTTP ' + response.status + '. Check available memory and the local runtime; no cloud writer was called.');
    }
    return response;
  }

  async function probe({signal} = {}) {
    return operation(signal, Math.min(limit, 15000), async localSignal => {
      onStatus({phase: 'requesting', stage: 'ollama_probe', message: 'Checking the local Ollama model; no generation request is made.', local: true});
      const response = await request('/api/tags', {method: 'GET'}, localSignal);
      const decoder = new TextDecoder(); let raw = '';
      await readBody(response, localSignal, 200000, bytes => { raw += decoder.decode(bytes, {stream: true}); }); raw += decoder.decode();
      const data = json(raw);
      if (!Array.isArray(data?.models)) throw new Error('The local service did not return an Ollama model list. Check the selected loopback port.');
      const found = data.models.find(item => item && (item.name || item.model) === connection.model);
      if (!found) throw new Error('The required model is not installed under its exact tag. Run: ollama pull ' + OLLAMA_MODEL + '.');
      const digest = typeof found.digest === 'string' ? found.digest.replace(/^sha256:/, '') : '';
      if (digest !== OLLAMA_DIGEST) throw new Error('The installed Qwen weights differ from the pinned project model. Restore the project model before comparing runs; no other model was substituted.');
      readiness = {ready: true, ...connection, digest, bytes: count(found.size), contextTokens: CONTEXT};
      onStatus({phase: 'completed', stage: 'ollama_probe', message: 'Local Qwen 7B is ready. The model tag and weight digest match.', local: true});
      return {...readiness};
    });
  }

  async function callModel(messages, {stage, signal} = {}) {
    if (!/^rewrite_section_[1-6]$/.test(stage || '')) throw new Error('The local Ollama writer is reserved for the six section-revision stages.');
    if (!Array.isArray(messages) || messages.some(message => !message || !['system', 'user', 'assistant'].includes(message.role) || typeof message.content !== 'string')) throw new Error('The local writing request is malformed.');
    if (messages.reduce((n, message) => n + new TextEncoder().encode(message.content).length, 0) > 28000) throw new Error('This input exceeds the local Qwen context budget. Shorten the source excerpts or proposal; nothing was truncated and no cloud fallback was used.');
    const started = Date.now();
    return operation(signal, limit, async localSignal => {
      if (!readiness) await probe({signal: localSignal});
      if (localSignal.aborted) throw aborted();
      onStatus({phase: 'requesting', stage, message: 'Rewriting this section on your computer with Qwen 7B.', elapsedMs: Date.now() - started, local: true});
      const body = {
        model: connection.model, messages, stream: true,
        format: {type: 'object', properties: {text: {type: 'string'}}, required: ['text'], additionalProperties: false},
        options: {num_ctx: CONTEXT, num_predict: 2200, temperature: 0.2, seed: 41 + Number(stage.slice(-1))}, keep_alive: '5m',
      };
      const response = await request('/api/chat', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)}, localSignal);
      let content = '', pending = '', final = null, lastProgress = 0;
      const decoder = new TextDecoder();
      function event(line) {
        if (!line.trim()) return;
        const value = json(line);
        if (!value || typeof value !== 'object' || Array.isArray(value) || value.error) throw new Error('Local Qwen could not complete this section. Check the local runtime and available memory.');
        if (typeof value.model === 'string' && value.model !== connection.model) throw new Error('The local service answered with a different model. This response was discarded.');
        const piece = value.message?.content ?? '';
        if (typeof piece !== 'string') throw new Error('Local Qwen returned unsupported response content.');
        content += piece;
        if (content.length > MAX_TEXT) throw new Error('Local Qwen exceeded the output size limit. No partial rewrite was kept.');
        if (Date.now() - lastProgress >= 200) { lastProgress = Date.now(); onStatus({phase: 'receiving', stage, message: 'Receiving local Qwen output.', outputCharacters: content.length, elapsedMs: Date.now() - started, local: true}); }
        if (value.done === true) final = value;
      }
      await readBody(response, localSignal, MAX_BYTES, bytes => {
        pending += decoder.decode(bytes, {stream: true});
        let index;
        while ((index = pending.indexOf('\n')) >= 0) {
          const line = pending.slice(0, index); pending = pending.slice(index + 1); event(line);
          if (final) return false;
        }
        if (pending.length > 200000) throw new Error('Local Ollama returned an oversized event.');
      });
      if (!final) { pending += decoder.decode(); if (pending.trim()) event(pending); }
      if (localSignal.aborted) throw aborted();
      if (!final || final.done_reason === 'length' || !content.trim()) throw new Error('Local Qwen did not finish a complete answer. No partial rewrite was kept.');
      if (final.done_reason && !['stop', 'length'].includes(final.done_reason)) throw new Error('Local Qwen stopped without a normal text completion. No partial rewrite was kept.');
      if (Number(final.prompt_eval_count) >= CONTEXT - 256) throw new Error('The local prompt reached its context limit. Shorten the input before resuming; this response was not retained.');
      const inputTokens = count(final.prompt_eval_count), outputTokens = count(final.eval_count);
      onUsage({stage, model: connection.model, inputTokens, outputTokens, totalTokens: inputTokens !== null && outputTokens !== null ? inputTokens + outputTokens : null, local: true});
      onStatus({phase: 'completed', stage, message: 'Complete local Qwen response received.', outputCharacters: content.length, elapsedMs: Date.now() - started, local: true});
      return content;
    });
  }
  return {probe, callModel, base: connection.base, model: connection.model, clear() {closed = true; readiness = null; for (const controller of active) controller.abort();}};
}
