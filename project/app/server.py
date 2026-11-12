"""Loopback-only desktop interface. Model credentials remain in process memory."""
from __future__ import annotations
import argparse
import datetime
import io
import json
import os
import re
import secrets
import shutil
import sys
import threading
import time
import webbrowser
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import RevisionRun, Cancelled, digest, validate_sources, split_sections, write_json, PROTOCOL, RULES
from transport import Client, detect, local_qwen_status
from run_import import read_completed_archive, MAX_ARCHIVE


class State:
    def __init__(self, package):
        self.package = Path(package).resolve()
        self.runs = self.package/'runs'
        self.runs.mkdir(exist_ok=True)
        self.lock = threading.Lock()
        self.thread = None
        self.current = None
        self.cancel = threading.Event()
        self.busy = False
        self.token = secrets.token_urlsafe(32)
        for f in self.runs.glob('*/run.json'):
            try:
                data = json.loads(f.read_text(encoding='utf-8'))
                if data.get('status') == 'running':
                    data.update(status='interrupted', error='The application closed before completion. Resume this run.')
                    write_json(f, data)
            except (ValueError, OSError):
                pass

    def folder(self, runid):
        if not isinstance(runid, str) or not re.fullmatch(r'run_\d{8}_\d{6}_[a-f0-9]{6}', runid):
            raise ValueError('Invalid run identifier.')
        folder = self.runs/runid
        if not folder.is_dir() or folder.is_symlink():
            raise ValueError('Run not found.')
        return folder

    def history(self):
        items = []
        for f in sorted(self.runs.glob('*/run.json'), reverse=True):
            try:
                items.append({'id': f.parent.name, **json.loads(f.read_text(encoding='utf-8'))})
            except (ValueError, OSError):
                continue
        return items

    def result(self, runid):
        folder = self.folder(runid)
        result = {'id': runid}
        for name in ['run.json', 'checks.json', 'revision_ledger.json', 'input.json', 'gptzero.json', 'import.json']:
            f = folder/name
            if f.exists():
                result[name.removesuffix('.json')] = json.loads(f.read_text(encoding='utf-8'))
        for name in ['initial.md', 'candidate.md', 'proposal.md']:
            f = folder/name
            if f.exists():
                result[name.removesuffix('.md')] = f.read_text(encoding='utf-8')
        return result

    def import_completed(self, payload):
        records, provenance = read_completed_archive(payload)
        with self.lock:
            if self.busy or (self.thread and self.thread.is_alive()):
                raise ValueError('Wait for the current operation before importing a run.')
            runid = datetime.datetime.now().strftime('run_%Y%m%d_%H%M%S_') + secrets.token_hex(3)
            stage = self.runs/('.import-' + secrets.token_hex(8))
            stage.mkdir()
            try:
                for name, value in records.items():
                    (stage/name).write_bytes(value)
                provenance['importedAtUTC'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                write_json(stage/'import.json', provenance)
                stage.rename(self.runs/runid)
            except Exception:
                shutil.rmtree(stage, ignore_errors=True)
                raise
            self.current = runid
            return {'id': runid, 'sourceRunId': provenance['sourceRunId'], 'imported': True}

    def start(self, payload, resume=False):
        client = Client(payload.get('connection', {}), self.package)
        client.prepare()
        with self.lock:
            if self.busy or (self.thread and self.thread.is_alive()):
                raise ValueError('Another operation is still running. Wait or cancel it first.')
            if resume:
                folder = self.folder(payload.get('runId'))
                if (folder/'import.json').exists():
                    raise ValueError('Imported runs are review records and cannot resume model execution.')
                info = json.loads((folder/'run.json').read_text(encoding='utf-8'))
                if info['status'] == 'completed':
                    raise ValueError('This run is complete. Start a new run for a fresh generation.')
                if info['model'] != client.public_config():
                    raise ValueError('Resume with the same connection type, API base and Model ID.')
                supplied = json.loads((folder/'input.json').read_text(encoding='utf-8'))
            else:
                supplied = {k: payload.get(k) for k in ('topic', 'draft', 'sources', 'policy')}
                supplied['sources'] = validate_sources(supplied['sources'])
                supplied['draft'] = str(supplied.get('draft') or '').replace('\r\n', '\n').strip()
                supplied['topic'] = str(supplied.get('topic') or '').strip()
                supplied['policy'] = supplied.get('policy') or 'section'
                if supplied['policy'] not in ('section', 'full-audit'):
                    raise ValueError('Unknown policy.')
                if supplied['draft']:
                    if not 300 <= len(supplied['draft']) <= 18000:
                        raise ValueError('The supplied draft must contain 300–18,000 characters.')
                    split_sections(supplied['draft'])
                elif not 10 <= len(supplied['topic']) <= 1600:
                    raise ValueError('Enter a topic with at least 10 characters, or paste a draft.')
                runid = datetime.datetime.now().strftime('run_%Y%m%d_%H%M%S_') + secrets.token_hex(3)
                folder = self.runs/runid
                folder.mkdir()
            self.cancel = threading.Event()
            self.current = folder.name
            runner = RevisionRun(folder, client, self.cancel)
            runner.checkpoint()
            def work():
                try:
                    runner.execute(supplied)
                except Exception:
                    pass  # run.json contains a safe error and original-text fallback.
                finally:
                    client.key = ''
            self.thread = threading.Thread(target=work, daemon=True)
            self.thread.start()
            return {'id': folder.name}


def make_server(package, port=0):
    state = State(package)
    static = Path(__file__).resolve().parent/'web'
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, data, kind='application/json; charset=utf-8', status=200, filename=None):
            if isinstance(data, (dict, list)):
                data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            elif isinstance(data, str):
                data = data.encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            if filename:
                self.send_header('Content-Disposition', 'attachment; filename="'+filename+'"')
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def authorised(self, api=False):
            expected = '127.0.0.1:'+str(self.server.server_port)
            if self.headers.get('Host') != expected:
                self.send({'error': 'Local host mismatch.'}, status=403)
                return False
            origin = self.headers.get('Origin')
            if origin and origin != 'http://'+expected:
                self.send({'error': 'Cross-origin requests are not permitted.'}, status=403)
                return False
            if api and not secrets.compare_digest(self.headers.get('X-ProseLedger-Token', ''), state.token):
                self.send({'error': 'Session expired. Reload the page.'}, status=403)
                return False
            return True

        def do_GET(self):
            path = urlsplit(self.path).path
            if not self.authorised(path.startswith('/api/')):
                return
            try:
                if path == '/':
                    return self.send((static/'index.html').read_text(encoding='utf-8').replace('__TOKEN__', state.token), 'text/html; charset=utf-8')
                if path in ('/app.js', '/style.css'):
                    return self.send((static/path[1:]).read_bytes(), 'text/javascript; charset=utf-8' if path.endswith('.js') else 'text/css; charset=utf-8')
                if path == '/api/state':
                    return self.send({'history': state.history(), 'current': state.current,
                        'busy': state.busy or bool(state.thread and state.thread.is_alive()), 'protocol': PROTOCOL,
                        'rules': RULES})
                if path == '/api/example':
                    return self.send(json.loads((state.package/'examples/example.json').read_text(encoding='utf-8')))
                if path == '/api/local-status':
                    return self.send(local_qwen_status())
                if path.startswith('/api/result/'):
                    return self.send(state.result(path.split('/')[-1]))
                if path.startswith('/api/download/'):
                    _, _, _, runid, filename = path.split('/')
                    folder = state.folder(runid)
                    if filename == 'all.zip':
                        stream = io.BytesIO()
                        with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
                            for f in sorted(folder.iterdir()):
                                if f.is_file() and not f.is_symlink() and f.suffix in ('.json', '.md'):
                                    archive.writestr(runid+'/'+f.name, f.read_bytes())
                        return self.send(stream.getvalue(), 'application/zip', filename=runid+'.zip')
                    if filename not in ('proposal.md', 'initial.md', 'candidate.md', 'revision_ledger.json', 'run.json', 'gptzero.json'):
                        raise ValueError('Download not supported.')
                    return self.send((folder/filename).read_bytes(), 'application/octet-stream', filename=filename)
                return self.send({'error': 'Not found.'}, status=404)
            except (ValueError, OSError, KeyError):
                self.send({'error': 'Requested result is unavailable.'}, status=400)

        def do_POST(self):
            if not self.authorised(True):
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if urlsplit(self.path).path == '/api/import':
                    if not 1 <= length <= MAX_ARCHIVE:
                        raise ValueError('Choose a completed-run ZIP no larger than 5 MB.')
                    return self.send(state.import_completed(self.rfile.read(length)))
                if not 1 <= length <= 160000:
                    raise ValueError('Request is empty or too large.')
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise ValueError('Invalid request.')
                path = urlsplit(self.path).path
                if path == '/api/start':
                    return self.send(state.start(payload))
                if path == '/api/resume':
                    return self.send(state.start(payload, True))
                if path == '/api/cancel':
                    state.cancel.set()
                    return self.send({'message': 'Cancellation requested. An in-flight HTTP call may take up to its timeout to end.'})
                if path == '/api/test':
                    with state.lock:
                        if state.busy or (state.thread and state.thread.is_alive()):
                            raise ValueError('Wait for the current operation before testing a connection.')
                        state.busy = True
                    try:
                        client = Client(payload.get('connection', {}), state.package)
                        client.prepare()
                        result = client.call([{'role': 'user', 'content': 'Return exactly the JSON object {"ok":true}. No tools.'}], threading.Event(), 'connection_test')
                        from core import parse_object
                        if parse_object(result['text']).get('ok') is not True:
                            raise ValueError('The model answered but did not follow the JSON format.')
                        return self.send({'ok': True, 'seconds': result['elapsedSeconds'], 'model': result['model'],
                                          'usage': result['usage'], 'configuration': client.public_config()})
                    finally:
                        if 'client' in locals():
                            client.key = ''
                        state.busy = False
                if path == '/api/detect':
                    with state.lock:
                        if state.busy or (state.thread and state.thread.is_alive()):
                            raise ValueError('Wait for writing to finish before running detection.')
                        state.busy = True
                    try:
                        folder = state.folder(payload.get('runId'))
                        info = json.loads((folder/'run.json').read_text(encoding='utf-8'))
                        if info['status'] != 'completed':
                            raise ValueError('Only completed runs can be compared with GPTZero.')
                        key = payload.get('key', '')
                        scans = {'metric': 'document class probabilities, not AI-authored-word percentage',
                                 'detectorUsedForSelection': False, 'scans': {}, 'createdAtUTC': datetime.datetime.now(datetime.timezone.utc).isoformat()}
                        for name in ('initial', 'proposal'):
                            text = (folder/(name+'.md')).read_text(encoding='utf-8')
                            fingerprint = digest(text)
                            previous = scans['scans'].get('initial')
                            if previous and previous['textSHA256'] == fingerprint:
                                scans['scans'][name] = {**previous, 'reusedSameTextScan': True}
                            else:
                                scans['scans'][name] = {'textSHA256': fingerprint, 'text': text, 'raw': detect(text, key)}
                            write_json(folder/'gptzero.json', scans)
                        return self.send(scans)
                    finally:
                        payload['key'] = ''
                        key = ''
                        state.busy = False
                self.send({'error': 'Not found.'}, status=404)
            except (ValueError, KeyError, OSError) as e:
                # Provider errors have already been reduced to safe fixed messages.
                self.send({'error': str(e)[:500]}, status=400)
            except Exception:
                self.send({'error': 'The operation could not complete. Check the saved run status and retry.'}, status=500)

    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.daemon_threads = True
    server.state = state
    return server


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    server = make_server(args.package, args.port)
    url = 'http://127.0.0.1:'+str(server.server_port)+'/'
    print('ProseLedger is running at '+url, flush=True)
    print('Keep this window open while writing. Results are saved in '+str(server.state.runs), flush=True)
    if not args.no_browser:
        threading.Timer(.7, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.state.cancel.set()
        if server.state.thread:
            server.state.thread.join(timeout=3)
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
