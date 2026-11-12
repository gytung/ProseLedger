"""Completed-run imports preserve texts and reject unsafe or incomplete archives."""
import io
import hashlib
import json
import stat
import sys
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'app'))
from core import RevisionRun
from run_import import read_completed_archive, MAX_ARCHIVE
from server import State
from test_workflow import DRAFT, SOURCES, FakeClient

SOURCE_ID = 'run_20261108_120000_abcdef'


class RunImport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as directory:
            RevisionRun(directory, FakeClient()).execute({
                'draft': DRAFT, 'sources': SOURCES, 'topic': 'Evidence-preserving revision', 'policy': 'section'})
            cls.files = {p.name: p.read_bytes() for p in Path(directory).iterdir() if p.is_file()}

    def archive(self, files=None, extras=()):
        buffer = io.BytesIO()
        with warnings.catch_warnings(), zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as z:
            warnings.simplefilter('ignore', UserWarning)
            for name, value in (files or self.files).items():
                z.writestr(SOURCE_ID+'/'+name, value)
            for name, value in extras:
                z.writestr(name, value)
        return buffer.getvalue()

    def changed(self, name, mutate):
        files = dict(self.files)
        data = json.loads(files[name])
        mutate(data)
        files[name] = json.dumps(data).encode()
        return files

    def test_valid_import_preserves_original_and_retained_bytes(self):
        records, provenance = read_completed_archive(self.archive())
        self.assertEqual(records['initial.md'], self.files['initial.md'])
        self.assertEqual(records['proposal.md'], self.files['proposal.md'])
        self.assertEqual(provenance['sourceRunId'], SOURCE_ID)
        self.assertNotIn('audit_sections.response.json', records)
        self.assertEqual(len(provenance['sourceArchiveSHA256']), 64)

    def test_unicode_export_uses_exact_utf8_bytes_and_roundtrips(self):
        draft = DRAFT.replace('# A proposal', '# A proposal — café')
        with tempfile.TemporaryDirectory() as directory:
            result = RevisionRun(directory, FakeClient()).execute({
                'draft': draft, 'sources': SOURCES, 'topic': 'Unicode evidence · review', 'policy': 'section'})
            files = {p.name: p.read_bytes() for p in Path(directory).iterdir() if p.is_file()}
        self.assertEqual(files['initial.md'], draft.encode('utf-8'))
        for name in ('initial.md', 'candidate.md', 'proposal.md', 'run.json', 'input.json', 'revision_ledger.json'):
            self.assertNotIn(b'\r\n', files[name], name)
            files[name].decode('utf-8')
        ledger = json.loads(files['revision_ledger.json'])
        self.assertEqual(ledger['originalSHA256'], hashlib.sha256(files['initial.md']).hexdigest())
        self.assertEqual(ledger['retainedSHA256'], hashlib.sha256(files['proposal.md']).hexdigest())
        self.assertEqual(result['textSHA256'], hashlib.sha256(files['proposal.md']).hexdigest())
        records, provenance = read_completed_archive(self.archive(files))
        self.assertEqual(records['initial.md'], files['initial.md'])
        self.assertEqual(records['proposal.md'], files['proposal.md'])
        self.assertEqual(provenance['retainedSHA256'], result['textSHA256'])

    def test_line_ending_change_after_export_is_not_silently_normalized(self):
        files = dict(self.files)
        files['proposal.md'] = files['proposal.md'].replace(b'\n', b'\r\n')
        with self.assertRaisesRegex(ValueError, 'hashes'):
            read_completed_archive(self.archive(files))

    def test_state_import_creates_review_record_and_blocks_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            state = State(directory)
            imported = state.import_completed(self.archive())
            result = state.result(imported['id'])
            self.assertEqual(result['import']['sourceRunId'], SOURCE_ID)
            self.assertEqual(result['proposal'], self.files['proposal.md'].decode())
            with self.assertRaisesRegex(ValueError, 'cannot resume'):
                state.start({'runId': imported['id'], 'connection': {'mode': 'codex'}}, resume=True)

    def test_reimport_keeps_original_writer_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            state=State(directory)
            first=state.import_completed(self.archive())
            folder=state.folder(first['id'])
            buffer=io.BytesIO()
            with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as archive:
                for file in folder.iterdir():archive.writestr(first['id']+'/'+file.name,file.read_bytes())
            second=state.import_completed(buffer.getvalue())
            provenance=state.result(second['id'])['import']
            self.assertEqual(provenance['sourceRunId'],first['id'])
            self.assertEqual(provenance['originalSourceRunId'],SOURCE_ID)
            self.assertEqual(provenance['importLineage'][0]['sourceRunId'],SOURCE_ID)

    def test_rejects_traversal_and_duplicate_names(self):
        for name in ['../../proposal.md', '/tmp/proposal.md', 'C:/proposal.md', 'a\\proposal.md', SOURCE_ID+'/proposal.md']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                read_completed_archive(self.archive(extras=[(name, b'x')]))

    def test_rejects_symlink(self):
        name = zipfile.ZipInfo(SOURCE_ID+'/linked.md')
        name.create_system = 3
        name.external_attr = (stat.S_IFLNK | 0o777) << 16
        with self.assertRaisesRegex(ValueError, 'Symbolic links'):
            read_completed_archive(self.archive(extras=[(name, b'proposal.md')]))

    def test_rejects_oversize_and_compression_bomb(self):
        with self.assertRaises(ValueError):
            read_completed_archive(b'x'*(MAX_ARCHIVE+1))
        with self.assertRaisesRegex(ValueError, 'compression ratio'):
            read_completed_archive(self.archive(extras=[(SOURCE_ID+'/large.json', json.dumps({'text':'a'*200000}).encode())]))
        with self.assertRaisesRegex(ValueError, 'expanded archive'):
            read_completed_archive(self.archive(extras=[(SOURCE_ID+'/large.json', b'a'*1000001)]))

    def test_rejects_credentials_and_non_finite_numbers(self):
        files = self.changed('input.json', lambda d: d.update(api_key='synthetic-credential-do-not-save'))
        with self.assertRaisesRegex(ValueError, 'credential'):
            read_completed_archive(self.archive(files))
        files = self.changed('checks.json', lambda d: d.update(wordRatio=float('nan')))
        with self.assertRaisesRegex(ValueError, 'non-finite'):
            read_completed_archive(self.archive(files))

    def test_rejects_incomplete_records_and_text_tampering(self):
        incomplete = dict(self.files);incomplete.pop('checks.json')
        with self.assertRaises(ValueError):read_completed_archive(self.archive(incomplete))
        files = self.changed('run.json', lambda d: d.update(status='running'))
        with self.assertRaises(ValueError):read_completed_archive(self.archive(files))
        files = dict(self.files);files['proposal.md'] += b'\nChanged after export.'
        with self.assertRaisesRegex(ValueError, 'match'):
            read_completed_archive(self.archive(files))
        files = self.changed('revision_ledger.json', lambda d: d.update(edits=[]))
        with self.assertRaisesRegex(ValueError, 'ledger'):
            read_completed_archive(self.archive(files))

    def test_rejects_executable_and_multiple_run_folders(self):
        for name in [SOURCE_ID+'/run.exe', 'other_run/cache.json']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                read_completed_archive(self.archive(extras=[(name, b'{}')]))


if __name__ == '__main__':
    unittest.main()
