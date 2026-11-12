"""Offline contract tests; synthetic model outputs are not experimental results."""
import copy
import json
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from pathlib import Path
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'app'))
from core import HEADINGS, RevisionRun, bounded_patches, guard, numbers, split_sections, validate_sources, Cancelled
from server import make_server
from transport import Client

SOURCES = [{'id': 'S1', 'title': 'One', 'excerpt': 'This source describes how a proposed editing procedure preserves evidence.'},
           {'id': 'S2', 'title': 'Two', 'excerpt': 'This source describes checking proposed changes before retaining a manuscript.'}]
DRAFT = '# A proposal\n\n'+'\n\n'.join('## '+h+'\n\nThe planned tool checks evidence before retaining an edit [S1]. It may preserve uncertainty when editing a proposal, but this requires evaluation [S2].' for h in HEADINGS)
urlopen = build_opener(ProxyHandler({})).open


class FakeClient:
    def __init__(self, fail_stage=None, full_issues=False):
        self.calls=[]; self.fail_stage=fail_stage; self.full_issues=full_issues
    def public_config(self): return {'mode':'test','model':'synthetic-fixture'}
    def safe_error(self,e): return str(e)
    def call(self,messages,cancel,stage):
        self.calls.append(stage)
        if stage==self.fail_stage: raise ValueError('synthetic interruption')
        payload=json.loads(messages[-1]['content'].split('\nINPUT DATA:\n')[1])
        if stage=='generate_initial_proposal':
            value={'title':'A generated fixture','sections':[{'heading':h,'text':split_sections(DRAFT)[1][i]['original']} for i,h in enumerate(HEADINGS)]}
        elif stage.startswith('rewrite_section_'):
            value={'text':payload['section']['original'].replace('planned tool','proposed tool')}
        elif stage=='audit_sections':
            value={'reviews':[{'id':i,'approve':True,'issues':[],'readability':'similar'} for i in range(6)]}
        elif stage.startswith('repair_'):
            value={'sections':[{'id':x['id'],'patches':[],'reason':'No bounded patch'} for x in payload['sections']]}
        else:
            value={'contentPreserved':not self.full_issues,'issues':[{'section':'Abstract','originalQuote':'planned','revisedQuote':'proposed','problem':'Synthetic finding'}] if self.full_issues else [],'readability':'similar','reason':'Synthetic audit'}
        return {'text':json.dumps(value),'usage':{},'model':'synthetic-fixture'}


class Contracts(unittest.TestCase):
    def test_patch_rejects_ambiguity_overlap_and_coverage(self):
        self.assertFalse(bounded_patches('a a text',[{'before':'a','after':'b','issueIndex':0}],1)['ok'])
        self.assertEqual(bounded_patches('abcdefghij'*3,[{'before':'abcdefghij'*3,'after':'z','issueIndex':0}],1)['reason'],'coverage')
        self.assertEqual(bounded_patches('abcdefghij other long passage',[{'before':'bcd','after':'x','issueIndex':0},{'before':'cde','after':'y','issueIndex':0}],1)['reason'],'overlap')
    def test_patch_valid_and_issue_index(self):
        result=bounded_patches('One unique phrase in this long sentence.',[{'before':'unique','after':'specific','issueIndex':0}],1)
        self.assertEqual(result['text'],'One specific phrase in this long sentence.')
        self.assertFalse(bounded_patches('abcdefghij',[{'before':'b','after':'z','issueIndex':True}],1)['ok'])
    def test_guard(self):
        self.assertTrue(guard(DRAFT,DRAFT,SOURCES)['passed'])
        self.assertFalse(guard(DRAFT,DRAFT.replace('[S1]','[S3]'),SOURCES)['passed'])
        self.assertFalse(guard(DRAFT,DRAFT+'\nWe achieved 95% accuracy.',SOURCES)['passed'])
        self.assertEqual(numbers('# Heading 99\nThere are 3 tasks [S2] and 4.5%.'),{'3','4.5%'})
    def test_source_validation(self):
        with self.assertRaises(ValueError):validate_sources([SOURCES[0],SOURCES[0]])
    def test_completion_and_ledger(self):
        with tempfile.TemporaryDirectory() as d:
            c=FakeClient();r=RevisionRun(d,c).execute({'draft':DRAFT,'sources':SOURCES,'topic':'Test topic here','policy':'section'})
            self.assertEqual(r['status'],'completed');self.assertTrue(r['newCandidateAccepted'])
            self.assertEqual(len(c.calls),8)
            ledger=json.loads((Path(d)/'revision_ledger.json').read_text())
            self.assertEqual(len(ledger['edits']),6);self.assertEqual(ledger['memoryCardsUsed'],0)
    def test_failure_resume_does_not_repeat_completed_calls(self):
        with tempfile.TemporaryDirectory() as d:
            data={'draft':DRAFT,'sources':SOURCES,'topic':'Test topic here','policy':'section'}
            with self.assertRaises(ValueError): RevisionRun(d,FakeClient('rewrite_section_3')).execute(data)
            self.assertEqual((Path(d)/'proposal.md').read_text(),DRAFT)
            c=FakeClient();r=RevisionRun(d,c).execute(data)
            self.assertNotIn('rewrite_section_1',c.calls);self.assertEqual(r['cachedCalls'],2)
    def test_resume_preserves_attempt_history_and_cumulative_usage(self):
        clock = [100.0]
        class TimedClient(FakeClient):
            def call(self, messages, cancel, stage):
                clock[0] += 3
                response = super().call(messages, cancel, stage)
                response['backend'] = 'local_qwen' if stage.startswith('rewrite_section_') else 'hosted'
                return response
        with tempfile.TemporaryDirectory() as d, patch('core.time.time', side_effect=lambda: clock[0]):
            data={'draft':DRAFT,'sources':SOURCES,'topic':'Test topic here','policy':'section'}
            with self.assertRaises(ValueError):
                RevisionRun(d, TimedClient('rewrite_section_3')).execute(data)
            first=json.loads((Path(d)/'run.json').read_text())
            self.assertEqual(first['totalCompletedCalls'],2)
            self.assertEqual(first['elapsedSeconds'],9)
            clock[0] = 200.0  # Time between attempts is not model execution time.
            r=RevisionRun(d, TimedClient()).execute(data)
            self.assertEqual(r['status'],'completed')
            self.assertEqual(r['attempt'],2)
            self.assertEqual(len(r['attemptHistory']),1)
            self.assertEqual(r['attemptHistory'][0]['status'],'failed')
            self.assertEqual(r['attemptHistory'][0]['error'],'synthetic interruption')
            self.assertEqual(r['attemptHistory'][0]['localWriterCalls'],2)
            self.assertEqual(r['attemptHistory'][0]['elapsedSeconds'],9)
            self.assertEqual(r['completedCalls'],6)
            self.assertEqual(r['cachedCalls'],2)
            self.assertEqual(r['totalCompletedCalls'],8)
            self.assertEqual(r['totalLocalWriterCalls'],6)
            self.assertEqual(r['totalHostedCalls'],2)
            self.assertEqual(r['elapsedSeconds'],18)
            self.assertEqual(r['totalElapsedSeconds'],27)
            self.assertEqual(json.loads((Path(d)/'run.json').read_text())['attemptHistory'],r['attemptHistory'])
    def test_full_audit_failure_retains_original(self):
        with tempfile.TemporaryDirectory() as d:
            r=RevisionRun(d,FakeClient(full_issues=True)).execute({'draft':DRAFT,'sources':SOURCES,'topic':'Test topic here','policy':'full-audit'})
            self.assertFalse(r['newCandidateAccepted']);self.assertEqual((Path(d)/'proposal.md').read_text(),DRAFT)
    def test_cancel(self):
        with tempfile.TemporaryDirectory() as d:
            event=threading.Event();event.set()
            with self.assertRaises(Cancelled): RevisionRun(d,FakeClient(),event).execute({'draft':DRAFT,'sources':SOURCES,'topic':'Test topic here','policy':'section'})
            self.assertEqual(json.loads((Path(d)/'run.json').read_text())['status'],'cancelled')
    def test_generation_path(self):
        with tempfile.TemporaryDirectory() as d:
            r=RevisionRun(d,FakeClient()).execute({'draft':'','sources':SOURCES,'topic':'Evidence-preserving editing','policy':'section'})
            self.assertEqual(r['status'],'completed');self.assertTrue((Path(d)/'initial.md').exists())
    def test_invalid_schema_is_not_cached_forever(self):
        class Invalid(FakeClient):
            def call(self,messages,cancel,stage):
                if stage=='audit_sections':return {'text':'{"reviews":[]}', 'usage':{}}
                return super().call(messages,cancel,stage)
        with tempfile.TemporaryDirectory() as d:
            data={'draft':DRAFT,'sources':SOURCES,'topic':'Test topic here','policy':'section'}
            with self.assertRaises(ValueError):RevisionRun(d,Invalid()).execute(data)
            self.assertFalse((Path(d)/'audit_sections.response.json').exists())
            c=FakeClient();r=RevisionRun(d,c).execute(data)
            self.assertEqual(r['status'],'completed');self.assertIn('audit_sections',c.calls)


class APIContracts(unittest.TestCase):
    def test_openai_response_and_credentials_not_in_metadata(self):
        client=Client({'mode':'responses','model':'fixture','key':'synthetic-secret'},Path('.'))
        response={'status':'completed','model':'fixture','output':[{'type':'message','content':[{'type':'output_text','text':'{"ok":true}'}]}],'usage':{'input_tokens':1}}
        with patch('transport.request_json',return_value=response) as request:
            output=client.call([],threading.Event(),'fixture')
            self.assertEqual(output['text'],'{"ok":true}')
            self.assertEqual(request.call_args.args[0],'https://api.openai.com/v1/responses')
            self.assertFalse(request.call_args.args[1]['store'])
        self.assertNotIn('synthetic-secret',json.dumps(client.public_config()))
    def test_truncation_rejected(self):
        client=Client({'mode':'chat','model':'fixture','base':'http://127.0.0.1:9999/v1'},Path('.'))
        with patch('transport.request_json',return_value={'choices':[{'finish_reason':'length','message':{'content':'{"ok":true}'}}]}):
            with self.assertRaises(ValueError):client.call([],threading.Event(),'fixture')
    def test_credential_echo_rejected(self):
        client=Client({'mode':'chat','model':'fixture','key':'synthetic-secret'},Path('.'))
        with patch('transport.request_json',return_value={'choices':[{'finish_reason':'stop','message':{'content':'synthetic-secret'}}]}):
            with self.assertRaises(ValueError):client.call([],threading.Event(),'fixture')


class LocalHTTP(unittest.TestCase):
    def test_cross_origin_and_secret_token(self):
        with tempfile.TemporaryDirectory() as d:
            server=make_server(d);t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
            url='http://127.0.0.1:'+str(server.server_port)
            try:
                with urlopen(url) as r:self.assertIn(b'ProseLedger',r.read())
                with self.assertRaises(HTTPError) as e:urlopen(url+'/api/state')
                self.assertEqual(e.exception.code,403)
                req=Request(url+'/api/state',headers={'X-ProseLedger-Token':server.state.token})
                with urlopen(req) as r:self.assertEqual(json.load(r)['history'],[])
                req=Request(url+'/api/state',headers={'X-ProseLedger-Token':server.state.token,'Origin':'https://other.example'})
                with self.assertRaises(HTTPError):urlopen(req)
            finally:server.shutdown();server.server_close()


if __name__=='__main__':unittest.main()
