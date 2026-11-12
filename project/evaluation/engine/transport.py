"""Credential-free records and bounded native/API model transport."""
import json
import http.client
import os
import re
import shutil
import signal
import socket
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler
from urllib.error import HTTPError, URLError
from core import Cancelled

LOCAL_QWEN_BASE = 'http://127.0.0.1:11436'
LOCAL_QWEN_MODEL = 'qwen2.5:7b-instruct-q4_K_M'
LOCAL_QWEN_DIGEST = '845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e'
LOCAL_CONTEXT_TOKENS = 8192
LOCAL_CALL_TIMEOUT = 600


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Redirect refused. Enter the final API base URL explicitly.')


def request_json(url, body, headers, timeout=180):
    request = Request(url, data=None if body is None else json.dumps(body).encode('utf-8'), headers=headers)
    handlers = [NoRedirect()]
    if urlsplit(url).hostname in ('127.0.0.1', 'localhost', '::1'):
        handlers.append(ProxyHandler({}))
    with build_opener(*handlers).open(request, timeout=timeout) as response:
        data = response.read(2_000_001)
    if len(data) > 2_000_000:
        raise ValueError('The service response exceeded the supported size.')
    return json.loads(data)


def local_qwen_status():
    """Confirm the private loopback service has the selected model, without inference."""
    try:
        result = request_json(LOCAL_QWEN_BASE+'/api/tags', None,
                              {'User-Agent': 'ProseLedger-Desktop/1'}, 5)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        raise ValueError('The private local model service is not ready. Run 01_Install and reopen the app; Local Qwen never falls back to a cloud writer.') from None
    models = result.get('models', []) if isinstance(result, dict) else []
    for model in models:
        if not isinstance(model, dict):
            continue
        if str(model.get('name') or model.get('model', '')).lower() == LOCAL_QWEN_MODEL.lower():
            digest = model.get('digest')
            if not isinstance(digest, str) or not re.fullmatch(r'(?:sha256:)?[a-f0-9]{64}', digest):
                raise ValueError('The local model returned no valid weight digest. Check the local runtime installation.')
            if digest.removeprefix('sha256:') != LOCAL_QWEN_DIGEST:
                raise ValueError('The installed Qwen weights do not match this release. Run 01_Install to restore the pinned model.')
            return {'ready': True, 'model': LOCAL_QWEN_MODEL, 'base': LOCAL_QWEN_BASE,
                    'digest': digest, 'bytes': model.get('size'), 'contextTokens': LOCAL_CONTEXT_TOKENS}
    raise ValueError('The selected local Qwen model is missing. Run 01_Install to finish the model download; no cloud fallback will be used.')


def local_qwen_chat(messages, cancel, seed):
    """Stream a bounded JSON answer and close the local request when cancelled."""
    if sum(len(str(m.get('content', '')).encode('utf-8')) for m in messages) > 28000:
        raise ValueError('This input is too large for the configured local Qwen context. Shorten source excerpts or the proposal; no automatic truncation or cloud fallback is used.')
    body = {'model': LOCAL_QWEN_MODEL, 'messages': messages, 'stream': True,
            'format': {'type': 'object', 'properties': {'text': {'type': 'string'}},
                       'required': ['text'], 'additionalProperties': False},
            'options': {'num_ctx': LOCAL_CONTEXT_TOKENS, 'num_predict': 2200,
                        'temperature': 0.2, 'seed': seed}, 'keep_alive': '5m'}
    connection = http.client.HTTPConnection('127.0.0.1', 11436, timeout=LOCAL_CALL_TIMEOUT)
    complete, result = threading.Event(), {}
    holder = {}

    def disconnect():
        sock = holder.get('socket')
        if sock:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        try:
            connection.close()
        except OSError:
            pass

    def work():
        try:
            if cancel.is_set():
                raise Cancelled('Local generation cancelled before it started.')
            connection.request('POST', '/api/chat', json.dumps(body).encode('utf-8'),
                               {'Content-Type': 'application/json', 'User-Agent': 'ProseLedger-Desktop/1'})
            holder['socket'] = connection.sock
            response = connection.getresponse()
            if response.status != 200:
                raise ValueError('Local Qwen returned HTTP '+str(response.status)+'. Check the local runtime and available memory; no cloud writer was called.')
            chunks, total_bytes, final = [], 0, None
            while True:
                if cancel.is_set():
                    raise Cancelled('Local generation cancelled; no partial rewrite was retained.')
                line = response.readline(200001)
                if not line:
                    break
                total_bytes += len(line)
                if len(line) > 200000 or total_bytes > 2000000:
                    raise ValueError('The local model response exceeded the supported size.')
                event = json.loads(line)
                if not isinstance(event, dict) or event.get('error'):
                    raise ValueError('Local Qwen could not complete the request. Check available memory and local runtime logs.')
                content = event.get('message', {}).get('content', '')
                if not isinstance(content, str):
                    raise ValueError('The local model returned unsupported content.')
                chunks.append(content)
                if event.get('done') is True:
                    final = event
                    break
            text = ''.join(chunks)
            if not final or final.get('done_reason') == 'length' or not text.strip() or len(text) > 100000:
                raise ValueError('Local Qwen did not finish a complete answer. No partial rewrite was retained.')
            if final.get('prompt_eval_count', 0) >= LOCAL_CONTEXT_TOKENS-256:
                raise ValueError('The local prompt reached its context limit. Shorten the input before resuming; this candidate was not retained.')
            result['value'] = {'text': text, 'model': final.get('model', LOCAL_QWEN_MODEL),
                'usage': {'input_tokens': final.get('prompt_eval_count', 0),
                          'output_tokens': final.get('eval_count', 0)},
                'localDurationSeconds': round(final.get('total_duration', 0)/1e9, 3),
                'sectionSeed': seed}
        except (TimeoutError, OSError, http.client.HTTPException):
            result['error'] = ValueError('Local Qwen disconnected or exceeded its 600-second call limit. Completed stages are saved. Close memory-heavy apps and resume; no cloud fallback was used.')
        except (ValueError, Cancelled) as exc:
            result['error'] = exc
        finally:
            disconnect()
            complete.set()

    thread = threading.Thread(target=work, daemon=True)
    thread.start()
    start = time.monotonic()
    while not complete.wait(.2):
        if cancel.is_set():
            disconnect()
            raise Cancelled('Local generation cancelled; no partial rewrite was retained.')
        if time.monotonic()-start > LOCAL_CALL_TIMEOUT:
            disconnect()
            raise ValueError('Local Qwen exceeded its 600-second call limit. Completed stages are saved; no cloud fallback was used.')
    if cancel.is_set():
        raise Cancelled('Local generation cancelled; no partial rewrite was retained.')
    if 'error' in result:
        raise result['error']
    if 'value' not in result:
        raise ValueError('Local Qwen returned no completed answer.')
    return result['value']


class Client:
    def __init__(self, config, package):
        self.mode = config.get('mode', 'codex')
        self.model = str(config.get('model', '')).strip()[:160]
        self.key = str(config.get('key', '')).strip()
        self.base = str(config.get('base', 'https://api.openai.com/v1')).strip().rstrip('/')
        self.package = Path(package)
        self.writer_mode = config.get('writerMode', 'hosted')
        self.local_digest = None
        if self.writer_mode not in ('local_qwen', 'hosted'):
            raise ValueError('Choose Local Qwen or the hosted writer explicitly.')
        if self.mode not in ('codex', 'responses', 'chat'):
            raise ValueError('Choose Codex login, Responses API or Chat Completions.')
        if self.mode != 'codex':
            parsed = urlsplit(self.base)
            local = parsed.hostname in ('127.0.0.1', 'localhost', '::1')
            if parsed.scheme != 'https' and not (parsed.scheme == 'http' and local):
                raise ValueError('API base URL must use HTTPS, or localhost HTTP.')
            if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
                raise ValueError('API base URL must not contain credentials, a query or a fragment.')
            if not self.model:
                raise ValueError('Enter the exact Model ID supplied by your API provider.')
            if not self.key and not local:
                raise ValueError('Enter your model API key. A ChatGPT subscription is not an API key.')
        if len(self.key) > 2048 or '\n' in self.key or '\r' in self.key:
            raise ValueError('Invalid API key format.')

    def public_config(self):
        result = {'mode': self.mode, 'model': self.model or 'account-default',
                  'base': self.base if self.mode != 'codex' else 'official-native-cli'}
        if self.writer_mode == 'local_qwen':
            result['routing'] = 'local-section-writer; hosted-initial-draft-review-repair'
            result['writer'] = {'backend': 'ollama', 'model': LOCAL_QWEN_MODEL,
                'base': LOCAL_QWEN_BASE, 'modelDigest': self.local_digest,
                'contextTokens': LOCAL_CONTEXT_TOKENS, 'temperature': 0.2,
                'sectionSeeds': list(range(42, 48)), 'maxOutputTokens': 2200}
        return result

    def prepare(self):
        if self.writer_mode == 'local_qwen' and not self.local_digest:
            self.local_digest = local_qwen_status()['digest']

    def stage_backend(self, stage):
        return 'local_qwen' if self.writer_mode == 'local_qwen' and re.fullmatch(r'rewrite_section_[1-6]', stage) else 'hosted'

    def safe_error(self, error):
        text = str(error)
        if self.key:
            text = text.replace(self.key, '[redacted]')
        return text[:500]

    def call(self, messages, cancel, stage):
        if cancel.is_set():
            raise Cancelled('Cancelled before the next model call.')
        start = time.monotonic()
        backend = self.stage_backend(stage)
        if backend == 'local_qwen':
            self.prepare()
            seed = 41 + int(stage.rsplit('_', 1)[-1])
            result = local_qwen_chat(messages, cancel, seed)
            result['modelDigest'] = self.local_digest
        else:
            result = self.cli(messages, cancel) if self.mode == 'codex' else self.api(messages, cancel)
        if cancel.is_set():
            raise Cancelled('Cancelled; the returned candidate was not adopted.')
        if self.key and self.key in result['text']:
            raise ValueError('The provider echoed credential material; its response was discarded.')
        result['elapsedSeconds'] = round(time.monotonic()-start, 2)
        result['backend'] = backend
        return result

    def api(self, messages, cancel):
        if self.mode == 'responses':
            endpoint = self.base + '/responses'
            body = {'model': self.model, 'input': messages, 'max_output_tokens': 7000, 'store': False}
        else:
            endpoint = self.base + '/chat/completions'
            body = {'model': self.model, 'messages': messages, 'stream': False, 'max_tokens': 7000}
        headers = {'Content-Type': 'application/json', 'User-Agent': 'ProseLedger-Desktop/1'}
        if self.key:
            headers['Authorization'] = 'Bearer '+self.key
        for attempt in (1, 2):
            try:
                result = request_json(endpoint, body, headers)
                break
            except HTTPError as e:
                code = e.code
                e.close()
                if code in (429, 500, 502, 503, 504) and attempt == 1:
                    if cancel.wait(2):
                        raise Cancelled('Cancelled during the retry pause.')
                    continue
                messages = {401: 'API authentication failed. Check the key and provider.',
                            403: 'This API account cannot access the selected service or model.',
                            404: 'API endpoint or Model ID was not found.',
                            429: 'The API rate limit or quota was reached. Check billing before resuming.',
                            400: 'The provider rejected the request. Check endpoint compatibility and Model ID.'}
                raise ValueError(messages.get(code, 'Model service returned HTTP '+str(code))) from None
            except (URLError, TimeoutError, OSError):
                raise ValueError('The model connection failed or timed out (180-second limit). Completed stages are saved. Resume after checking the connection.') from None
        if self.mode == 'responses':
            if result.get('status') != 'completed' or result.get('error'):
                raise ValueError('The response was incomplete or refused. No partial candidate was adopted.')
            text = ''.join(c.get('text', '') for item in result.get('output', [])
                           if item.get('type') == 'message' for c in item.get('content', []) if c.get('type') == 'output_text')
        else:
            choices = result.get('choices', [])
            if not choices or choices[0].get('finish_reason') != 'stop':
                raise ValueError('The model did not finish normally. It may have hit its output limit; no partial candidate was adopted.')
            text = choices[0].get('message', {}).get('content')
        if not isinstance(text, str) or not text.strip() or len(text) > 100000:
            raise ValueError('The model returned no supported text answer.')
        return {'text': text, 'model': result.get('model', self.model), 'usage': result.get('usage', {}), 'httpAttempts': attempt}

    def executable(self):
        explicit = os.environ.get('PROSELEDGER_CODEX_PATH')
        candidates = [explicit] if explicit else [str(self.package/'runtime/windows/codex.exe')] if os.name == 'nt' else [
            '/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex',
            '/Applications/Codex.app/Contents/Resources/codex',
            '/opt/homebrew/bin/codex', '/usr/local/bin/codex', shutil.which('codex')]
        for c in candidates:
            if c and Path(c).is_file():
                return str(Path(c).resolve())
        raise ValueError('Native Codex CLI not found. Use the login launcher in your platform folder, install the official CLI on Mac, or choose API mode.')

    def cli(self, messages, cancel):
        args = [self.executable(), 'exec', '--json', '--ephemeral', '--ignore-user-config',
                '--sandbox', 'read-only', '--skip-git-repo-check', '-c', 'approval_policy="never"',
                '-c', 'web_search="disabled"', '-c', 'model_reasoning_effort="low"']
        if self.model:
            args += ['--model', self.model]
        args += ['-']
        prompt = ('Execute the supplied text-only scientific-writing transcript. Do not access files, '
                  'use tools, browse, run commands, invoke skills or external services. Return only the '
                  'JSON requested in the transcript, without commentary.\n' + json.dumps(messages, ensure_ascii=False))
        env = {k: v for k, v in os.environ.items() if k not in
               ('OPENAI_API_KEY', 'CODEX_API_KEY', 'OPENAI_BASE_URL', 'OPENAI_API_BASE', 'OPENAI_MODEL_PROVIDER', 'CODEX_MODEL_PROVIDER')}
        job = None
        kwargs = {'start_new_session': True}
        if os.name == 'nt':
            from windows_job import WindowsJob
            job = WindowsJob()
            kwargs = {'creationflags': subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP | 4}
        proc = None
        def kill():
            if job:
                job.terminate()
            elif proc and proc.poll() is None:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        try:
            with tempfile.TemporaryDirectory(prefix='proseledger-writing-') as cwd:
                proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, encoding='utf-8', errors='replace', cwd=cwd, env=env, **kwargs)
                if job:
                    try:
                        job.attach_and_resume(proc.pid)
                    except Exception:
                        proc.kill()
                        raise
                began = time.monotonic()
                first = True
                while True:
                    if cancel.is_set():
                        kill()
                        raise Cancelled('Cancelled; completed stages remain saved.')
                    if time.monotonic() - began > 240:
                        kill()
                        raise ValueError('Codex call exceeded 240 seconds. Check login/quota and Resume.')
                    try:
                        out, err = proc.communicate(prompt if first else None, timeout=.3)
                        break
                    except subprocess.TimeoutExpired:
                        first = False
                if proc.returncode:
                    raise ValueError('Codex call failed. Run 03_Login_Codex in your platform folder, check model access and quota, then Resume.')
                final, usage, complete = None, {}, False
                for line in out.splitlines():
                    try:
                        event = json.loads(line)
                    except ValueError:
                        continue
                    if event.get('type') in ('error', 'turn.failed'):
                        raise ValueError('Codex reported a failed request. Check model access and quota.')
                    if event.get('type') == 'item.completed':
                        item = event.get('item', {})
                        if item.get('type') == 'agent_message':
                            final = item.get('text')
                        elif item.get('type') not in ('reasoning',):
                            raise ValueError('The model attempted a non-text action; response rejected.')
                    if event.get('type') == 'turn.completed':
                        usage, complete = event.get('usage', {}), True
                if not complete or not final:
                    raise ValueError('Codex returned no completed answer. Completed earlier stages remain saved.')
                return {'text': final, 'model': self.model or 'account-default', 'usage': usage}
        finally:
            if proc and proc.poll() is None:
                kill()
                proc.wait(timeout=5)
            if job:
                job.close()


def detect(text, key):
    if not isinstance(key, str) or not key.strip() or len(key) > 2048 or '\n' in key or '\r' in key:
        raise ValueError('Enter a valid GPTZero API key.')
    try:
        raw = request_json('https://api.gptzero.me/v2/predict/text', {'document': text},
            {'Content-Type': 'application/json', 'x-api-key': key.strip(), 'User-Agent': 'ProseLedger-Desktop/1'}, 90)
    except HTTPError as e:
        code = e.code
        e.close()
        raise ValueError('GPTZero returned HTTP '+str(code)+'. Check your GPTZero API access and quota.') from None
    except (URLError, TimeoutError, OSError):
        raise ValueError('GPTZero connection failed or timed out. Your manuscript is unchanged.') from None
    # Do not retain a credential echo from a third-party response.
    if key.strip() in json.dumps(raw):
        raise ValueError('The service echoed credential material; response discarded.')
    return raw
