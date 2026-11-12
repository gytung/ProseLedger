"""Local writer routing, bounded streaming and explicit failure contracts."""
import json
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'app'))
from core import Cancelled
from transport import (Client, LOCAL_QWEN_DIGEST, LOCAL_QWEN_MODEL,
                       local_qwen_chat, local_qwen_status)


class FakeSocket:
    def __init__(self):self.closed = threading.Event()
    def shutdown(self, *_):self.closed.set()


class FakeResponse:
    status = 200
    def __init__(self, events):self.lines = iter([json.dumps(x).encode()+b'\n' for x in events])
    def readline(self, _):return next(self.lines, b'')


class FakeConnection:
    def __init__(self, events):self.sock=FakeSocket();self.events=events;self.request_data=None
    def request(self,*args):self.request_data=args
    def getresponse(self):return FakeResponse(self.events)
    def close(self):self.sock.closed.set()


def complete_events(reason='stop'):
    return [{'message': {'content': '{"text":"A clearer '}, 'done': False},
            {'model': LOCAL_QWEN_MODEL, 'message': {'content': 'sentence."}'}, 'done': True,
             'done_reason': reason, 'prompt_eval_count': 123, 'eval_count': 12, 'total_duration': 250000000}]


class LocalWriter(unittest.TestCase):
    def client(self):
        return Client({'mode':'responses','model':'review-fixture','key':'synthetic-secret',
                       'writerMode':'local_qwen'}, Path('.'))

    def test_only_six_section_stages_use_local_qwen(self):
        client=self.client()
        with patch('transport.local_qwen_status',return_value={'digest':LOCAL_QWEN_DIGEST}), \
             patch('transport.local_qwen_chat',return_value={'text':'{"text":"Changed."}','model':LOCAL_QWEN_MODEL}) as local, \
             patch.object(client,'api',return_value={'text':'{"ok":true}','model':'review-fixture'}) as hosted:
            for section in range(1,7):
                result=client.call([],threading.Event(),'rewrite_section_'+str(section))
                self.assertEqual(result['backend'],'local_qwen')
                self.assertEqual(local.call_args.args[2],41+section)
            for stage in ['generate_initial_proposal','audit_sections','repair_section_findings','audit_full_revision','connection_test']:
                result=client.call([],threading.Event(),stage)
                self.assertEqual(result['backend'],'hosted')
            self.assertEqual(local.call_count,6);self.assertEqual(hosted.call_count,5)
            config=client.public_config()
            self.assertEqual(config['writer']['modelDigest'],LOCAL_QWEN_DIGEST)
            self.assertNotIn('synthetic-secret',json.dumps(config))

    def test_local_failure_never_falls_back_to_hosted_writer(self):
        client=self.client()
        with patch('transport.local_qwen_status',return_value={'digest':LOCAL_QWEN_DIGEST}), \
             patch('transport.local_qwen_chat',side_effect=ValueError('local unavailable')), \
             patch.object(client,'api') as hosted:
            with self.assertRaisesRegex(ValueError,'local unavailable'):
                client.call([],threading.Event(),'rewrite_section_1')
            hosted.assert_not_called()

    def test_hosted_only_config_remains_explicit_and_compatible(self):
        client=Client({'mode':'responses','model':'review-fixture','key':'synthetic-secret','writerMode':'hosted'},Path('.'))
        with patch('transport.local_qwen_chat') as local, patch.object(client,'api',return_value={'text':'{"text":"Changed."}'}) as hosted:
            client.call([],threading.Event(),'rewrite_section_1')
            local.assert_not_called();hosted.assert_called_once()
            self.assertNotIn('writer',client.public_config())

    def test_readiness_rejects_missing_or_different_model(self):
        with patch('transport.request_json',return_value={'models':[]}):
            with self.assertRaisesRegex(ValueError,'missing'):local_qwen_status()
        with patch('transport.request_json',return_value={'models':[{'name':LOCAL_QWEN_MODEL,'digest':'0'*64}]}):
            with self.assertRaisesRegex(ValueError,'do not match'):local_qwen_status()
        with patch('transport.request_json',return_value={'models':[{'name':LOCAL_QWEN_MODEL,'digest':LOCAL_QWEN_DIGEST,'size':4700000000}]}):
            self.assertTrue(local_qwen_status()['ready'])

    def test_stream_json_schema_seed_and_usage(self):
        connection=FakeConnection(complete_events())
        with patch('transport.http.client.HTTPConnection',return_value=connection):
            result=local_qwen_chat([{'role':'user','content':'Rewrite the section.'}],threading.Event(),44)
        self.assertEqual(json.loads(result['text']),{'text':'A clearer sentence.'})
        self.assertEqual(result['usage']['input_tokens'],123)
        body=json.loads(connection.request_data[2])
        self.assertTrue(body['stream']);self.assertEqual(body['format']['required'],['text'])
        self.assertEqual(body['options']['seed'],44);self.assertEqual(body['options']['num_ctx'],8192)
        self.assertNotIn('Authorization',connection.request_data[3])

    def test_incomplete_and_context_limited_output_rejected(self):
        for events in [complete_events('length'),[{'message':{'content':'partial'},'done':False}],
                       [{**complete_events()[-1],'prompt_eval_count':8192}]]:
            with self.subTest(events=events), patch('transport.http.client.HTTPConnection',return_value=FakeConnection(events)):
                with self.assertRaises(ValueError):local_qwen_chat([],threading.Event(),42)
        with patch('transport.http.client.HTTPConnection') as connection:
            with self.assertRaisesRegex(ValueError,'too large'):
                local_qwen_chat([{'role':'user','content':'a'*28001}],threading.Event(),42)
            connection.assert_not_called()

    def test_cancel_interrupts_local_socket_and_discards_partial_output(self):
        cancel=threading.Event();connection=FakeConnection([])
        class WaitingResponse:
            status=200
            def readline(self,_):connection.sock.closed.wait(3);return b''
        connection.getresponse=lambda:WaitingResponse()
        timer=threading.Timer(.05,cancel.set);timer.start();began=time.monotonic()
        try:
            with patch('transport.http.client.HTTPConnection',return_value=connection):
                with self.assertRaises(Cancelled):local_qwen_chat([],cancel,42)
            self.assertTrue(connection.sock.closed.is_set())
            self.assertLess(time.monotonic()-began,1)
        finally:timer.cancel()


if __name__=='__main__':unittest.main()
