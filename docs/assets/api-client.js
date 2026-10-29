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
  return { endpoint, model: model.trim(), key: key.trim() };
}

const HTTP_ERRORS = {
  400: 'The provider rejected the request. Check the model ID and Chat Completions support.',
  401: 'Authentication failed. Check the API key for this provider.',
  402: 'The provider reports insufficient credits.',
  403: 'The provider denied access. Check model permissions and account restrictions.',
  404: 'The endpoint or model was not found. Check the API base URL and model ID.',
  413: 'The request is too large. Shorten the supplied source notes.',
  429: 'The provider rate or usage limit was reached. Try later; no automatic retry was made.',
};

async function boundedResponse(response) {
  const reader = response.body?.getReader();
  if (!reader) return response.text();
  const decoder = new TextDecoder();
  let size = 0, text = '';
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > 2_000_000) {
        await reader.cancel();
        throw new Error('The provider response exceeded the demo size limit.');
      }
      text += decoder.decode(value, { stream: true });
    }
    return text + decoder.decode();
  } finally { reader.releaseLock(); }
}

export function createModelClient(config, { onUsage = () => {}, fetchImpl = fetch, timeoutMs = 180000 } = {}) {
  const connection = validateConnection(config);
  let secret = connection.key;
  delete connection.key;
  const callModel = async (messages, { signal, stage = 'model' } = {}) => {
    if (!secret) throw new Error('The API key has been cleared. Enter it again for a new run.');
    signal?.throwIfAborted();
    const controller = new AbortController();
    const abort = () => controller.abort(signal?.reason);
    signal?.addEventListener('abort', abort, { once: true });
    let timedOut = false;
    const timer = setTimeout(() => { timedOut = true; controller.abort(); }, timeoutMs);
    const body = { model: connection.model, messages, stream: false };
    if (new URL(connection.endpoint).hostname === 'api.openai.com') body.max_completion_tokens = 5000;
    else body.max_tokens = 5000;
    try {
      const response = await fetchImpl(connection.endpoint, {
        method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${secret}` },
        body: JSON.stringify(body), signal: controller.signal, credentials: 'omit',
        cache: 'no-store', redirect: 'error', referrerPolicy: 'no-referrer',
      });
      if (!response.ok) {
        await response.body?.cancel();
        throw new Error(HTTP_ERRORS[response.status] || `The model service returned HTTP ${response.status}. Try again later.`);
      }
      let json;
      try { json = JSON.parse(await boundedResponse(response)); }
      catch (error) {
        if (error.name === 'AbortError') throw error;
        throw new Error('The provider returned an unreadable or oversized response.');
      }
      const choice = json.choices?.[0];
      if (choice?.finish_reason === 'length') throw new Error('The model output was truncated. Use a model with adequate output capacity.');
      const content = choice?.message?.content;
      if (typeof content !== 'string' || !content.trim()) throw new Error('The provider returned no text. Check Chat Completions compatibility.');
      if (content.includes(secret)) throw new Error('The provider echoed credential material. The response was discarded.');
      const usage = json.usage || {};
      const count = value => Number.isFinite(value) && value >= 0 ? value : null;
      onUsage({ stage, inputTokens: count(usage.prompt_tokens), outputTokens: count(usage.completion_tokens),
        totalTokens: count(usage.total_tokens), model: typeof json.model === 'string' && !json.model.includes(secret) ? json.model : connection.model });
      return content;
    } catch (error) {
      if (timedOut) throw new Error('This model call timed out after three minutes. No automatic retry was made.');
      if (signal?.aborted) throw new DOMException('Generation cancelled.', 'AbortError');
      if (error instanceof TypeError) throw new Error('Cannot reach this provider from the browser. Check the network and browser CORS support; no proxy is used.');
      throw error;
    } finally {
      clearTimeout(timer);
      signal?.removeEventListener('abort', abort);
    }
  };
  return { callModel, clear() { secret = ''; }, endpoint: connection.endpoint, model: connection.model };
}
