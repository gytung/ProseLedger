"""Paired loopback bridge from the public workspace to an official account login."""
from __future__ import annotations
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import re
import secrets
import select
import socket
import threading
import time
from urllib.parse import urlsplit
try:
    from . import native_runtime
except ImportError:
    import native_runtime

HOST = '127.0.0.1'
PORT = 11437
ORIGIN = 'https://gytung.github.io'
MAX_BODY = native_runtime.MAX_BODY
REQUEST_ID = re.compile(r'[a-zA-Z0-9_-]{8,80}\Z')


class BridgeServer(ThreadingHTTPServer):
    # Runtime cleanup must finish before Python can exit. The explicit bounded
    # join below avoids relying on ThreadingMixIn's unbounded server_close join.
    daemon_threads = False
    block_on_close = False
    allow_reuse_address = True

    def __init__(self, token=None, runtime=None):
        self.token = token or secrets.token_urlsafe(24)
        self.runtime = runtime or native_runtime
        self.active = {}
        self.active_lock = threading.Lock()
        self.closing = False
        self.workers = set()
        super().__init__((HOST, PORT), Handler)

    def process_request_thread(self, request, client_address):
        worker = threading.current_thread()
        with self.active_lock:
            self.workers.add(worker)
        try:
            super().process_request_thread(request, client_address)
        finally:
            with self.active_lock:
                self.workers.discard(worker)

    def server_close(self):
        with self.active_lock:
            self.closing = True
            for event in self.active.values():
                event.set()
            workers = tuple(self.workers)
        super().server_close()
        deadline = time.monotonic() + 15
        for worker in workers:
            if worker is not threading.current_thread():
                worker.join(timeout=max(0, deadline - time.monotonic()))


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    server_version = 'ProseLedgerLocal/1'
    sys_version = ''

    def log_message(self, *_):
        # Pair codes, manuscript bodies and account output never enter HTTP logs.
        pass

    def setup(self):
        super().setup()
        self.connection.settimeout(12)

    def allowed_origin(self):
        return self.headers.get_all('Origin', []) == [ORIGIN]

    def destination_allowed(self):
        hosts = self.headers.get_all('Host', [])
        return len(hosts) == 1 and hosts[0].lower() in (f'{HOST}:{PORT}', f'localhost:{PORT}') and self.allowed_origin()

    def reply(self, status, value):
        body = json.dumps(value, ensure_ascii=False).encode('utf-8')
        try:
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Connection', 'close')
            if self.allowed_origin():
                self.send_header('Access-Control-Allow-Origin', ORIGIN)
                self.send_header('Vary', 'Origin')
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        self.close_connection = True

    def reject(self, status, message):
        self.reply(status, {'error': message})
        return False

    def authorize(self):
        if self.server.closing:
            return self.reject(503, 'The local connector is shutting down.')
        if not self.destination_allowed():
            return self.reject(403, 'This connector accepts only the paired ProseLedger website on loopback.')
        tokens = self.headers.get_all('X-ProseLedger-Token', [])
        if len(tokens) != 1 or not secrets.compare_digest(tokens[0].encode('utf-8'), self.server.token.encode('utf-8')):
            return self.reject(401, 'Enter the current pair code displayed by your local connector.')
        path = urlsplit(self.path)
        if path.query or path.fragment or path.path not in ('/status', '/call', '/cancel'):
            return self.reject(404, 'Unknown connector route.')
        return True

    def do_OPTIONS(self):
        if not self.destination_allowed():
            self.reject(403, 'Origin or host not permitted.'); return
        if urlsplit(self.path).path not in ('/status', '/call', '/cancel'):
            self.reject(404, 'Unknown connector route.'); return
        method = self.headers.get('Access-Control-Request-Method', '').upper()
        requested = {item.strip().lower() for item in self.headers.get('Access-Control-Request-Headers', '').split(',') if item.strip()}
        if method not in ('GET', 'POST') or requested - {'content-type', 'x-proseledger-token'}:
            self.reject(403, 'Preflight method or headers not permitted.'); return
        self.send_response(204)
        self.send_header('Content-Length', '0')
        self.send_header('Access-Control-Allow-Origin', ORIGIN)
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-ProseLedger-Token')
        self.send_header('Access-Control-Allow-Private-Network', 'true')
        self.send_header('Access-Control-Max-Age', '600')
        self.send_header('Vary', 'Origin')
        self.send_header('Connection', 'close')
        self.end_headers()
        self.close_connection = True

    def do_GET(self):
        if not self.authorize():
            return
        if self.path != '/status':
            self.reject(405, 'Use POST for this route.'); return
        status = self.server.runtime.login_status()
        self.reply(200, {'protocol': 'proseledger-account-bridge-1', **status})

    def body(self):
        if self.headers.get('Transfer-Encoding'):
            self.reject(400, 'Chunked input is not supported.'); return None
        lengths = self.headers.get_all('Content-Length', [])
        if len(lengths) != 1 or not lengths[0].isdigit():
            self.reject(411, 'A bounded Content-Length is required.'); return None
        length = int(lengths[0])
        if not 1 <= length <= MAX_BODY:
            self.reject(413, 'The connector input limit is 180 KB.'); return None
        if self.headers.get_content_type() != 'application/json':
            self.reject(415, 'Use a JSON request.'); return None
        try:
            data = self.rfile.read(length)
            if len(data) != length:
                raise ValueError
            value = json.loads(data)
            if not isinstance(value, dict):
                raise ValueError
            return value
        except (ValueError, UnicodeError, TimeoutError, OSError):
            self.reject(400, 'The connector request is incomplete or invalid JSON.'); return None

    def do_POST(self):
        if not self.authorize():
            return
        if self.path not in ('/call', '/cancel'):
            self.reject(405, 'Use GET for this route.'); return
        value = self.body()
        if value is None:
            return
        request_id = value.get('requestId')
        if not isinstance(request_id, str) or not REQUEST_ID.fullmatch(request_id):
            self.reject(400, 'Supply a valid request ID.'); return
        if self.path == '/cancel':
            if set(value) != {'requestId'}:
                self.reject(400, 'Cancel accepts only a request ID.'); return
            with self.server.active_lock:
                event = self.server.active.get(request_id)
                if event:
                    event.set()
            self.reply(200, {'requestId': request_id, 'cancelled': event is not None})
            return
        try:
            call = native_runtime.validate_call(value)
        except native_runtime.NativeError as error:
            self.reject(400, str(error)); return
        if self.server.token in json.dumps(call):
            self.reject(400, 'Keep the pair code out of research input and model settings.'); return
        with self.server.active_lock:
            if self.server.closing:
                self.reject(503, 'The local connector is shutting down.'); return
            if self.server.active:
                self.reject(409, 'One account request is already running. Wait for it or stop it before starting another.'); return
            cancel = threading.Event()
            self.server.active[request_id] = cancel
        complete = threading.Event()

        def watch_disconnect():
            while not complete.wait(.2):
                try:
                    readable, _, _ = select.select([self.connection], [], [], 0)
                    if readable and not self.connection.recv(1, socket.MSG_PEEK):
                        cancel.set(); return
                except (OSError, ValueError):
                    cancel.set(); return

        watcher = threading.Thread(target=watch_disconnect, daemon=True)
        watcher.start()
        try:
            result = self.server.runtime.call(call['messages'], call['model'], cancel)
            if self.server.token in json.dumps(result):
                self.reject(502, 'The model echoed pairing material. The response was discarded.'); return
            if not isinstance(result, dict) or not isinstance(result.get('text'), str) or len(result['text']) > 100000:
                self.reject(502, 'The account runtime returned an invalid result.'); return
            self.reply(200, {'requestId': request_id, **result})
        except native_runtime.NativeCancelled as error:
            self.reject(409, str(error))
        except native_runtime.NativeError as error:
            self.reject(502, str(error))
        except Exception:
            self.reject(502, 'The local account call failed. Check the connector and official account login, then Resume.')
        finally:
            complete.set()
            with self.server.active_lock:
                self.server.active.pop(request_id, None)


def main():
    try:
        server = BridgeServer()
    except OSError:
        print('Port 11437 is busy. Close the earlier ProseLedger connector, then try again.')
        return 1
    print('ProseLedger local account connector', flush=True)
    print('Website: https://gytung.github.io/ProseLedger/create.html', flush=True)
    print('Local address: http://127.0.0.1:11437', flush=True)
    print('Pair code (paste only into that website): ' + server.token, flush=True)
    print('Keep this window open. Ctrl+C stops the connector. No API key is required here.', flush=True)
    try:
        server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt:
        print('\nStopping the connector.', flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
