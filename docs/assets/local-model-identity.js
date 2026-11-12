/** Pure metadata validation for archived local-model records; no transport or model calls. */
export const OLLAMA_MODEL = 'qwen2.5:7b-instruct-q4_K_M';
export const OLLAMA_DIGEST = '845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e';

export function validateOllamaConfig({base = 'http://127.0.0.1:11434', model = OLLAMA_MODEL} = {}) {
  if (typeof base !== 'string' || !/^http:\/\/(?:127\.0\.0\.1|localhost):(?:11434|11436)\/?$/i.test(base.trim())) {
    throw new Error('Use http://127.0.0.1:11434 for your Ollama installation, or http://127.0.0.1:11436 for the project runtime. Other network destinations are not permitted.');
  }
  if (model !== OLLAMA_MODEL) throw new Error('Use the pinned local model tag: ' + OLLAMA_MODEL + '.');
  return {base: new URL(base.trim()).origin, model};
}
