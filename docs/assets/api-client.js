/** Direct, session-only access to a visitor-selected model provider. */
export const PRESETS = Object.freeze({
  openrouter: { base: 'https://openrouter.ai/api/v1', model: 'openai/gpt-4.1-mini' },
  openai: { base: 'https://api.openai.com/v1', model: 'gpt-4.1-mini' },
});

export function providerEndpoint(base) {
  let url;
  try { url = new URL(String(base).trim()); } catch { throw new Error('Enter a valid HTTPS API base URL.'); }
  if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash) {
    throw new Error('Use an HTTPS API base URL without credentials, a query, or a fragment.');
  }
  const host = url.hostname.toLowerCase();
  if (host === 'localhost' || host.endsWith('.localhost') || host.endsWith('.local') ||
      /^[\d.]+$/.test(host) || host.includes(':') || host.startsWith('[')) {
    throw new Error('Use a public HTTPS model-provider hostname.');
  }
  url.pathname = url.pathname.replace(/\/+$/, '');
  if (!url.pathname.endsWith('/chat/completions')) url.pathname += '/chat/completions';
  return url.href;
}

export function validateConnection({ base, model, key }) {
  const endpoint = providerEndpoint(base);
  if (typeof model !== 'string' || !model.trim() || model.length > 160 || /[\r\n]/.test(model)) {
    throw new Error('Enter the model ID from your provider.');
  }
  if (typeof key !== 'string' || key.trim().length < 8 || key.length > 1024 || /\s/.test(key.trim())) {
    throw new Error('Enter a valid API key. A ChatGPT subscription is not an API key.');
  }
  if (model.includes(key.trim())) throw new Error('The model ID must not contain an API key.');
  return { endpoint, model: model.trim(), key: key.trim() };
}

const HTTP_ERRORS = {
  400: 'The provider rejected the request. Check the model ID and Chat Completions support.',
  401: 'Authentication failed. Check the API key for this provider.',
  402: 'The provider reports insufficient credits.',
  403: 'The provider denied access. Check model permissions and account restrictions.',
  404: 'The endpoint or model was not found. Check the API base URL and model ID.',
  413: 'The request is too large. Shorten the supplied source notes.',
  429: 'The provider rate or usage limit was reached. Check your account limits or try later.',
};
const TRANSIENT = new Set([429, 500, 502, 503, 504]);
const MAX_BYTES = 2_000_000;
const MAX_TEXT = 100_000;
const MAX_ATTEMPTS = 2;
const number = value => Number.isFinite(value) && value >= 0 ? value : null;
const aborted = () => new DOMException('Generation cancelled.', 'AbortError');

class ProviderFailure extends Error {
  constructor(message, { retryable = false, streamUnsupported = false, retryAfter = null } = {}) {
    super(message);
    this.retryable = retryable;
    this.streamUnsupported = streamUnsupported;
    this.retryAfter = retryAfter;
  }
}

function raceAbort(promise, signal) {
  if (signal.aborted) return Promise.reject(aborted());
  return new Promise((resolve, reject) => {
    const abort = () => { signal.removeEventListener('abort', abort); reject(aborted()); };
    signal.addEventListener('abort', abort, { once: true });
    Promise.resolve(promise).then(
      value => { signal.removeEventListener('abort', abort); resolve(value); },
      error => { signal.removeEventListener('abort', abort); reject(error); },
    );
  });
}

function wait(delay, signal) {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) { reject(aborted()); return; }
    const timer = setTimeout(() => { signal?.removeEventListener('abort', abort); resolve(); }, delay);
    const abort = () => { clearTimeout(timer); signal.removeEventListener('abort', abort); reject(aborted()); };
    signal?.addEventListener('abort', abort, { once: true });
  });
}

function retryAfterMs(value, maximum) {
  if (!value) return null;
  const seconds = Number(value);
  const delay = Number.isFinite(seconds) ? seconds * 1000 : Date.parse(value) - Date.now();
  return Number.isFinite(delay) ? Math.min(maximum, Math.max(0, delay)) : null;
}

/** Read a bounded response with cancellation, including providers returning JSON. */
async function readBody(response, { signal, maximum = MAX_BYTES, onChunk = () => {} }) {
  const reader = response.body?.getReader();
  if (!reader) {
    const text = await raceAbort(response.text(), signal);
    const bytes = new TextEncoder().encode(text);
    if (bytes.length > maximum) throw new ProviderFailure('The provider response exceeded the demo size limit.');
    onChunk(bytes);
    return;
  }
  let size = 0, completed = false;
  try {
    while (true) {
      const { value, done } = await raceAbort(reader.read(), signal);
      if (done) { completed = true; break; }
      size += value.byteLength;
      if (size > maximum) throw new ProviderFailure('The provider response exceeded the demo size limit.');
      if (onChunk(value) === false) break;
    }
  } finally {
    if (!completed) {
      // Cancellation must not wait indefinitely for a provider stream to close.
      Promise.resolve(reader.cancel()).catch(() => {});
    }
    reader.releaseLock();
  }
}

async function errorResponse(response, signal, streaming, maxRetryAfterMs) {
  let unsupported = false;
  if (streaming && [400, 422].includes(response.status)) {
    let raw = '';
    const decoder = new TextDecoder();
    try {
      await readBody(response, { signal, maximum: 8192, onChunk: chunk => { raw += decoder.decode(chunk, { stream: true }); } });
      raw += decoder.decode();
      const error = JSON.parse(raw).error || {};
      const message = `${typeof error.message === 'string' ? error.message : ''} ${typeof error.code === 'string' ? error.code : ''}`;
      const explicitParam = ['stream', 'stream_options'].includes(error.param);
      unsupported = (explicitParam && /unsupported|not supported|unknown|unrecognized|not allowed|not available/i.test(message)) ||
        /(?:streaming|stream(?:_options)?)\s+(?:is\s+)?(?:not supported|unsupported|not available)/i.test(message) ||
        /(?:does not|doesn't) support\s+stream(?:ing)?/i.test(message);
    } catch (error) {
      if (signal.aborted) throw aborted();
      // Provider error text is used only to recognize a capability mismatch.
      // It is never returned to the page, logs, or downloadable records.
    }
  } else {
    Promise.resolve(response.body?.cancel()).catch(() => {});
  }
  return new ProviderFailure(HTTP_ERRORS[response.status] || `The model service returned HTTP ${response.status}. Try again later.`, {
    retryable: TRANSIENT.has(response.status), streamUnsupported: unsupported,
    retryAfter: retryAfterMs(response.headers.get('retry-after'), maxRetryAfterMs),
  });
}

function parseJSON(text) {
  try { return JSON.parse(text); }
  catch { throw new ProviderFailure('The provider returned unreadable JSON. Check Chat Completions compatibility.'); }
}

function streamError(error) {
  const code = Number(error?.status ?? error?.code);
  const status = Number.isInteger(code) ? code : error?.code === 'rate_limit_exceeded' ? 429 : null;
  return new ProviderFailure('The provider reported an error during generation. Partial output was discarded.', {
    retryable: TRANSIENT.has(status),
  });
}

/** SSE is decoded incrementally. Comments, usage-only events, and split UTF-8 are valid. */
async function completionResponse(response, { signal, key, onBytes, onText }) {
  const decoder = new TextDecoder();
  let format = response.headers.get('content-type')?.includes('text/event-stream') ? 'sse' : null;
  let pending = '', raw = '', content = '', usage = {}, model = null;
  let dataLines = [], doneMarker = false, finishReason = null, sawEvent = false;
  const append = text => {
    if (typeof text !== 'string') throw new ProviderFailure('The provider returned unsupported text content.');
    content += text;
    if (content.length > MAX_TEXT) throw new ProviderFailure('The generated text exceeded the demo size limit.');
    if (content.includes(key)) throw new ProviderFailure('The provider echoed credential material. The response was discarded.');
    if (text) onText(content.length);
  };
  const capture = json => {
    if (!json || typeof json !== 'object' || Array.isArray(json)) throw new ProviderFailure('The provider returned an invalid completion event.');
    if (json.error) throw streamError(json.error);
    if (json.usage && typeof json.usage === 'object') usage = json.usage;
    if (typeof json.model === 'string' && json.model.length <= 160 && !json.model.includes(key)) model = json.model;
    const choice = json.choices?.find(item => item.index === 0) ?? json.choices?.[0];
    if (!choice) return;
    if (choice.finish_reason) {
      finishReason = choice.finish_reason;
      if (!['stop', 'length', 'content_filter', 'tool_calls', 'function_call'].includes(finishReason)) {
        throw new ProviderFailure('The provider ended generation without a successful text completion.');
      }
    }
    if (finishReason === 'length') throw new ProviderFailure('The model output was truncated. Use a model with adequate output capacity or a shorter task.');
    if (['content_filter', 'tool_calls', 'function_call'].includes(finishReason)) {
      throw new ProviderFailure('The provider did not return a complete text answer. Use a compatible text model.');
    }
    const piece = choice.delta?.content ?? choice.message?.content;
    if (piece !== undefined && piece !== null) append(piece);
  };
  const dispatch = () => {
    if (!dataLines.length) return;
    const payload = dataLines.join('\n'); dataLines = [];
    if (!payload.trim()) return;
    sawEvent = true;
    if (payload.trim() === '[DONE]') { doneMarker = true; return; }
    capture(parseJSON(payload));
  };
  const line = value => {
    if (!value) { dispatch(); return; }
    if (value.startsWith(':')) return;
    if (value === 'data') dataLines.push('');
    else if (value.startsWith('data:')) dataLines.push(value.slice(5).replace(/^ /, ''));
  };
  const feed = text => {
    pending += text;
    let end;
    while ((end = pending.indexOf('\n')) >= 0) {
      const next = pending.slice(0, end).replace(/\r$/, '');
      pending = pending.slice(end + 1); line(next);
    }
  };
  await readBody(response, { signal, onChunk: bytes => {
    onBytes(bytes.byteLength);
    const chunk = decoder.decode(bytes, { stream: true });
    if (format === 'sse') { feed(chunk); return !doneMarker; }
    raw += chunk;
    const probe = raw.trimStart();
    if (!format && /^(?:data:|:|event:|id:|retry:)/.test(probe)) {
      format = 'sse'; feed(raw); raw = '';
    } else if (!format && /^(?:\{|\[)/.test(probe)) format = 'json';
    if (format === 'json') onText(0); // A non-streaming provider has started returning its answer.
    return !doneMarker;
  } });
  const tail = decoder.decode();
  if (format === 'sse') {
    feed(tail);
    if (pending) line(pending.replace(/\r$/, ''));
    dispatch();
    if (!sawEvent || (!doneMarker && !finishReason)) {
      throw new ProviderFailure('The model stream ended before completion. Partial output was discarded.', { retryable: true });
    }
  } else {
    capture(parseJSON(raw + tail));
  }
  if (!content.trim()) throw new ProviderFailure('The provider returned no text. Check Chat Completions compatibility.');
  return { content, usage, model };
}

/**
 * callModel(messages, {signal, stage, maxTokens}) returns complete text only.
 * A logical call has at most two HTTP attempts and one overall deadline.
 * Status events contain counters and fixed messages, never output text or keys.
 */
export function createModelClient(config, {
  onUsage = () => {}, onStatus = () => {}, fetchImpl = fetch,
  timeoutMs = 180000, firstTokenTimeoutMs = 60000, idleTimeoutMs = 45000,
  retryDelayMs = 1000, maxRetryAfterMs = 8000,
} = {}) {
  const connection = validateConnection(config);
  let secret = connection.key, streamSupported = true;
  delete connection.key;
  const active = new Set();
  const callModel = async (messages, { signal, stage = 'model', maxTokens = 2500 } = {}) => {
    if (!secret) throw new Error('The API key has been cleared. Enter it again for a new run.');
    if (signal?.aborted) throw aborted();
    if (!Number.isInteger(maxTokens) || maxTokens < 16 || maxTokens > 8000) throw new Error('Output limit must be an integer from 16 to 8,000 tokens.');
    const key = secret;
    const label = typeof stage === 'string' && !stage.includes(key) ? stage.slice(0, 100) : 'model';
    const started = Date.now(), deadline = started + Math.max(1, Math.min(600000, timeoutMs));
    const logical = new AbortController();
    const externalAbort = () => logical.abort();
    signal?.addEventListener('abort', externalAbort, { once: true });
    if (signal?.aborted) logical.abort();
    active.add(logical);
    let attempt = 0, receivedBytes = 0, outputCharacters = 0;
    const status = (phase, message, extra = {}) => onStatus({
      stage: label, phase, attempt, maxAttempts: MAX_ATTEMPTS, elapsedMs: Date.now() - started,
      receivedBytes, outputCharacters, message, ...extra,
    });
    try {
      let failure;
      while (attempt < MAX_ATTEMPTS) {
        if (logical.signal.aborted) throw aborted();
        if (Date.now() >= deadline) throw new ProviderFailure('The total model-call deadline was reached. Save the partial run and try a faster model.');
        attempt += 1; receivedBytes = 0; outputCharacters = 0;
        const request = new AbortController();
        const abortRequest = () => request.abort();
        logical.signal.addEventListener('abort', abortRequest, { once: true });
        if (logical.signal.aborted) request.abort();
        let timeoutKind = null, firstReceived = false, headersReceived = false, idleTimer, lastProgress = 0;
        const expire = kind => { timeoutKind = kind; request.abort(); };
        const overallTimer = setTimeout(() => expire('overall'), Math.max(1, deadline - Date.now()));
        const firstTimer = setTimeout(() => expire('first'), Math.max(1, Math.min(firstTokenTimeoutMs, deadline - Date.now())));
        const armIdle = () => {
          clearTimeout(idleTimer);
          idleTimer = setTimeout(() => expire('idle'), Math.max(1, Math.min(idleTimeoutMs, deadline - Date.now())));
        };
        const progress = () => {
          if (Date.now() - lastProgress >= 200) { lastProgress = Date.now(); status('receiving', 'Receiving model output.'); }
        };
        const body = { model: connection.model, messages, stream: streamSupported };
        const host = new URL(connection.endpoint).hostname;
        if (host === 'api.openai.com') body.max_completion_tokens = maxTokens;
        else body.max_tokens = maxTokens;
        if (body.stream && ['api.openai.com', 'openrouter.ai'].includes(host)) body.stream_options = { include_usage: true };
        status('requesting', `Sending model request (attempt ${attempt} of ${MAX_ATTEMPTS}).`, { streaming: body.stream, maxTokens });
        try {
          const response = await raceAbort(fetchImpl(connection.endpoint, {
            method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${key}` },
            body: JSON.stringify(body), signal: request.signal, credentials: 'omit',
            cache: 'no-store', redirect: 'error', referrerPolicy: 'no-referrer',
          }), request.signal);
          headersReceived = true;
          if (!response.ok) throw await errorResponse(response, request.signal, body.stream, maxRetryAfterMs);
          const answer = await completionResponse(response, {
            signal: request.signal, key,
            onBytes: bytes => { receivedBytes += bytes; if (firstReceived) armIdle(); progress(); },
            onText: count => { outputCharacters = count; if (!firstReceived) { firstReceived = true; clearTimeout(firstTimer); } armIdle(); progress(); },
          });
          if (logical.signal.aborted) throw aborted();
          const usage = { stage: label, attempt, inputTokens: number(answer.usage.prompt_tokens), outputTokens: number(answer.usage.completion_tokens),
            totalTokens: number(answer.usage.total_tokens), model: answer.model || connection.model };
          onUsage(usage);
          status('completed', 'Complete model response received.', usage);
          return answer.content;
        } catch (error) {
          if (logical.signal.aborted) throw aborted();
          if (timeoutKind) {
            const message = timeoutKind === 'first' ? 'No answer arrived before the first-response timeout.'
              : timeoutKind === 'idle' ? 'The model stream stopped responding.' : 'The total model-call deadline was reached.';
            failure = new ProviderFailure(`${message} Try a faster model or check the provider status.`, { retryable: timeoutKind !== 'overall' });
          } else if (error instanceof TypeError) {
            failure = headersReceived
              ? new ProviderFailure('The provider connection was interrupted while receiving the answer. Partial output was discarded.', { retryable: true })
              : new ProviderFailure('Cannot reach this provider from the browser. Check the network and browser CORS support; no proxy is used.');
          } else if (error instanceof ProviderFailure) failure = error;
          else failure = new ProviderFailure('The provider connection failed before a complete answer was received. Check the provider and try again.');
        } finally {
          clearTimeout(overallTimer); clearTimeout(firstTimer); clearTimeout(idleTimer);
          logical.signal.removeEventListener('abort', abortRequest);
        }
        const canRetry = attempt < MAX_ATTEMPTS && (failure.retryable || failure.streamUnsupported);
        const delay = failure.streamUnsupported ? 0 : Math.min(Math.max(0, maxRetryAfterMs), failure.retryAfter ?? Math.max(0, retryDelayMs));
        if (!canRetry || Date.now() + delay >= deadline) throw failure;
        if (failure.streamUnsupported) streamSupported = false;
        status('retrying', failure.streamUnsupported
          ? 'This provider explicitly rejected streaming. Retrying once with a standard response.'
          : 'Temporary provider interruption. Retrying once; the earlier attempt may still be billed.', { retryDelayMs: delay });
        await wait(delay, logical.signal);
      }
      throw failure;
    } catch (error) {
      if (logical.signal.aborted || signal?.aborted) { status('cancelled', 'Model request cancelled.'); throw aborted(); }
      const message = error instanceof ProviderFailure ? error.message : 'The model call failed before completion.';
      status('failed', message);
      throw new Error(`${label}: ${message}${attempt > 1 ? ' Both allowed attempts have been used.' : ''}`);
    } finally {
      signal?.removeEventListener('abort', externalAbort);
      active.delete(logical);
    }
  };
  return { callModel, clear() { secret = ''; for (const controller of active) controller.abort(); }, endpoint: connection.endpoint, model: connection.model };
}
