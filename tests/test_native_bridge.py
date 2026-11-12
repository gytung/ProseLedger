"""Loopback bridge contracts, with a fake runtime and no model-account calls."""
import http.client
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'local_connector'))
import bridge
import native_runtime

PAIR = 'fixture-pair-code-not-an-account-token'


class Runtime:
    def __init__(self):
        self.calls = []
        self.started = threading.Event()

    def login_status(self):
        return {'ready': True, 'authenticated': True, 'model': 'account-default'}

    def call(self, messages, model, cancel):
        self.calls.append((messages, model))
        if messages[0]['content'] == 'wait':
            self.started.set()
            if cancel.wait(5):
                raise native_runtime.NativeCancelled('Stopped.')
        if messages[0]['content'] == 'echo':
            return {'text': PAIR, 'model': model}
        return {'text': '{"ok":true}', 'model': model, 'usage': {'input_tokens': 5, 'output_tokens': 4}, 'elapsedSeconds': .1}


class BridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_port = bridge.PORT
        bridge.PORT = 0
        cls.runtime = Runtime()
        cls.server = bridge.BridgeServer(token=PAIR, runtime=cls.runtime)
        bridge.PORT = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
        bridge.PORT = cls.original_port

    def request(self, method='GET', path='/status', value=None, headers=None, raw=None):
        connection = http.client.HTTPConnection('127.0.0.1', bridge.PORT, timeout=8)
        base = {'Origin': bridge.ORIGIN, 'X-ProseLedger-Token': PAIR}
        if value is not None:
            raw = json.dumps(value).encode()
            base['Content-Type'] = 'application/json'
        base.update(headers or {})
        connection.request(method, path, raw, base)
        response = connection.getresponse()
        data = response.read()
        result = (response.status, dict(response.headers), json.loads(data) if data else None)
        connection.close()
        return result

    def call(self, content='hello', **extra):
        return {'requestId': 'test-request-123456', 'stage': 'audit_sections', 'model': 'account-default', 'messages': [{'role': 'user', 'content': content}], **extra}

    def test_status_is_paired_and_contains_no_pair_code(self):
        status, headers, body = self.request()
        self.assertEqual(status, 200)
        self.assertTrue(body['authenticated'])
        self.assertEqual(headers['Access-Control-Allow-Origin'], bridge.ORIGIN)
        self.assertNotIn(PAIR, json.dumps(body))
        self.assertEqual(headers['Cache-Control'], 'no-store')

    def test_wrong_token_origin_and_host_do_not_execute(self):
        before = len(self.runtime.calls)
        for headers in [{'X-ProseLedger-Token': 'wrong'}, {'Origin': 'https://unrelated.example'}, {'Host': 'evil.example:11437'}, {'Origin': 'null'}]:
            status, _, _ = self.request('POST', '/call', self.call(), headers)
            self.assertIn(status, (401, 403))
        self.assertEqual(len(self.runtime.calls), before)

    def test_preflight_is_exact_origin_only(self):
        status, headers, _ = self.request('OPTIONS', '/call', headers={'X-ProseLedger-Token': '', 'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'content-type,x-proseledger-token'})
        self.assertEqual(status, 204)
        self.assertEqual(headers['Access-Control-Allow-Origin'], bridge.ORIGIN)
        status, _, _ = self.request('OPTIONS', '/call', headers={'Origin': 'https://unrelated.example', 'Access-Control-Request-Method': 'POST'})
        self.assertEqual(status, 403)

    def test_stages_roles_fields_and_models_are_bounded(self):
        for change in [{'stage': 'rewrite_section_1'}, {'model': '--dangerously-bypass-approvals-and-sandbox'}, {'messages': [{'role': 'assistant', 'content': 'hello'}]}, {'executable': '/some/program'}]:
            status, _, _ = self.request('POST', '/call', self.call(**change))
            self.assertEqual(status, 400)
        status, _, _ = self.request('POST', '/call', self.call(), {'Content-Length': '180001'}, raw=b'')
        self.assertEqual(status, 413)

    def test_valid_call_runs_only_requested_text_and_sanitizes_echo(self):
        status, _, body = self.request('POST', '/call', self.call())
        self.assertEqual(status, 200)
        self.assertEqual(body['text'], '{"ok":true}')
        self.assertEqual(body['requestId'], 'test-request-123456')
        status, _, body = self.request('POST', '/call', self.call('echo'))
        self.assertEqual(status, 502)
        self.assertNotIn(PAIR, json.dumps(body))
        status, _, _ = self.request('POST', '/call', self.call(PAIR))
        self.assertEqual(status, 400)

    def test_cancel_and_single_active_request(self):
        self.runtime.started.clear()
        result = []
        worker = threading.Thread(target=lambda: result.append(self.request('POST', '/call', self.call('wait'))))
        worker.start()
        self.assertTrue(self.runtime.started.wait(2))
        status, _, _ = self.request('POST', '/call', self.call(requestId='another-request-123'))
        self.assertEqual(status, 409)
        status, _, body = self.request('POST', '/cancel', {'requestId': 'test-request-123456'})
        self.assertEqual(status, 200)
        self.assertTrue(body['cancelled'])
        worker.join(timeout=3)
        self.assertEqual(result[0][0], 409)

    def test_unknown_route_and_query_token_rejected(self):
        for path in ['/unknown', '/status?token=x']:
            status, _, _ = self.request(path=path)
            self.assertEqual(status, 404)


class RuntimeContracts(unittest.TestCase):
    def test_request_validation_strips_no_hidden_execution_fields(self):
        value = {'stage': 'generate_initial_proposal', 'model': '', 'messages': [{'role': 'user', 'content': 'Draft a proposal.'}]}
        self.assertEqual(native_runtime.validate_call(value)['model'], 'account-default')
        for bad in [dict(value, cwd='/tmp'), dict(value, messages=[{'role': 'user', 'content': 'x' * 180001}]), dict(value, messages=[{'role': 'tool', 'content': 'x'}])]:
            with self.assertRaises(native_runtime.NativeError):
                native_runtime.validate_call(bad)


class ShutdownTests(unittest.TestCase):
    def test_close_waits_for_active_runtime_cleanup(self):
        original = bridge.PORT
        bridge.PORT = 0
        cleaned, entered = threading.Event(), threading.Event()

        class SlowCleanup(Runtime):
            def call(self, messages, model, cancel):
                entered.set()
                if cancel.wait(5):
                    time.sleep(.1)
                    cleaned.set()
                    raise native_runtime.NativeCancelled('Stopped after runtime cleanup.')
                raise AssertionError('Shutdown did not cancel the runtime.')

        server = bridge.BridgeServer(token=PAIR, runtime=SlowCleanup())
        bridge.PORT = server.server_address[1]
        serving = threading.Thread(target=server.serve_forever, daemon=True)
        serving.start()
        result = []

        def request():
            conn = http.client.HTTPConnection('127.0.0.1', server.server_address[1], timeout=5)
            body = {'requestId':'shutdown-request-123','stage':'audit_sections','messages':[{'role':'user','content':'wait'}]}
            conn.request('POST','/call',json.dumps(body),{'Origin':bridge.ORIGIN,'X-ProseLedger-Token':PAIR,'Content-Type':'application/json'})
            response = conn.getresponse()
            result.append((response.status,response.read()))
            conn.close()

        client = threading.Thread(target=request)
        client.start()
        try:
            self.assertTrue(entered.wait(2))
            self.assertFalse(server.daemon_threads)
            server.shutdown()
            server.server_close()
            self.assertTrue(cleaned.is_set(), 'server_close returned before native cleanup')
            self.assertFalse(server.active)
            self.assertFalse(server.workers)
            client.join(timeout=2)
            self.assertEqual(result[0][0],409)
        finally:
            server.shutdown()
            server.server_close()
            serving.join(timeout=2)
            client.join(timeout=2)
            bridge.PORT = original


@unittest.skipIf(os.name == 'nt', 'POSIX fixture; native Windows job cleanup requires a Windows host.')
class RuntimeProcesses(unittest.TestCase):
    """Exercise real process pipes and deadlines without accessing a model account."""
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(prefix='proseledger-runtime-test-')
        self.binary = Path(self.folder.name) / 'fixture-cli'
        self.binary.write_text('#!' + sys.executable + '\n' + '''
import json, os, sys, time
raw = sys.stdin.read()
message = json.loads(raw[raw.index('[{'):])[0]['content']
if message in ('wait', 'cancel'):
    time.sleep(10)
if message == 'tool':
    print(json.dumps({'type':'item.started','item':{'type':'command_execution','command':'blocked'}}), flush=True)
    time.sleep(10)
if message == 'invalid':
    print('[]', flush=True)
if message == 'notice':
    print(json.dumps({'type':'item.completed','item':{'type':'error','message':'fixture feature notice'}}), flush=True)
if message == 'partial':
    print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'partial'}}), flush=True)
    sys.exit(0)
if message == 'oversize':
    print('x' * 200001, flush=True)
    sys.exit(0)
sys.stderr.write('fixture-provider-secret-must-not-be-forwarded')
answer = json.dumps({'api_key_inherited': 'OPENAI_API_KEY' in os.environ, 'args': sys.argv[1:]})
print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':answer}}), flush=True)
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':12,'output_tokens':8,'cached_input_tokens':4,'secret':'discarded'}}), flush=True)
''')
        self.binary.chmod(0o700)
        self.patch = patch.object(native_runtime, 'executable', return_value=str(self.binary))
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.folder.cleanup()

    def run_call(self, content, cancel=None, timeout=4):
        return native_runtime.call([{'role': 'user', 'content': content}], 'account-default', cancel or threading.Event(), timeout=timeout)

    def test_complete_response_and_fixed_cli_contract(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'fixture-api-key'}):
            result = self.run_call('complete')
        body = json.loads(result['text'])
        self.assertFalse(body['api_key_inherited'])
        self.assertIn('--ignore-user-config', body['args'])
        self.assertIn('read-only', body['args'])
        self.assertNotIn('--model', body['args'])
        self.assertEqual(result['usage'], {'input_tokens': 12, 'output_tokens': 8, 'cached_input_tokens': 4})
        self.assertNotIn('fixture-provider-secret', json.dumps(result))

    def test_partial_nontext_invalid_and_oversized_answers_are_rejected(self):
        for text in ('partial', 'tool', 'invalid', 'oversize'):
            with self.subTest(text=text), self.assertRaises(native_runtime.NativeError):
                self.run_call(text)

    def test_cli_notice_does_not_replace_required_successful_completion(self):
        result = self.run_call('notice')
        self.assertEqual(json.loads(result['text'])['api_key_inherited'], False)

    def test_cancel_and_deadline_terminate_the_runtime(self):
        cancel = threading.Event()
        timer = threading.Timer(.15, cancel.set)
        timer.start()
        started = time.monotonic()
        with self.assertRaises(native_runtime.NativeCancelled):
            self.run_call('cancel', cancel=cancel)
        timer.join()
        self.assertLess(time.monotonic() - started, 2)
        with self.assertRaises(native_runtime.NativeError):
            self.run_call('wait', timeout=1)


if __name__ == '__main__':
    unittest.main()
