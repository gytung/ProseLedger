"""Offline launcher contracts. No downloads, model inference or account access."""
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'local_connector'))
import start as setup


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_zip_rejects_parent_and_windows_drive_paths_before_extracting(self):
        for index, name in enumerate(('../escape', '..\\escape', '/absolute', 'C:\\escape', 'folder/file:stream')):
            archive = self.root / f'{index}.zip'
            target = self.root / f'out{index}'
            with zipfile.ZipFile(archive, 'w') as writer:
                writer.writestr('safe.txt', 'safe')
                writer.writestr(name, 'bad')
            with self.assertRaisesRegex(RuntimeError, 'Unsafe archive'):
                setup.extract(archive, target)
            self.assertFalse((target / 'safe.txt').exists())
        self.assertFalse((self.root / 'escape').exists())

    @unittest.skipIf(os.name == 'nt', 'Creating the symlink fixture requires Windows developer mode.')
    def test_zip_rejects_symlinks_and_existing_parent_escape(self):
        archive = self.root / 'links.zip'
        with zipfile.ZipFile(archive, 'w') as writer:
            item = zipfile.ZipInfo('link')
            item.create_system = 3
            item.external_attr = 0o120777 << 16
            writer.writestr(item, '../outside')
        with self.assertRaisesRegex(RuntimeError, 'symlink'):
            setup.extract(archive, self.root / 'out')
        target = self.root / 'out2'
        target.mkdir()
        outside = self.root / 'outside'
        outside.mkdir()
        (target / 'linked').symlink_to(outside, target_is_directory=True)
        archive = self.root / 'existing.zip'
        with zipfile.ZipFile(archive, 'w') as writer:
            writer.writestr('linked/file.txt', 'must not escape')
        with self.assertRaisesRegex(RuntimeError, 'Unsafe archive'):
            setup.extract(archive, target)
        self.assertFalse((outside / 'file.txt').exists())

    def test_tar_rejects_escaping_symlink_and_special_file(self):
        for index, kind in enumerate((tarfile.SYMTYPE, tarfile.FIFOTYPE)):
            archive = self.root / f'malicious{index}.tar'
            with tarfile.open(archive, 'w') as writer:
                item = tarfile.TarInfo('entry')
                item.type = kind
                if kind == tarfile.SYMTYPE:
                    item.linkname = '../outside'
                writer.addfile(item)
            with self.assertRaises(RuntimeError):
                setup.extract(archive, self.root / f'out{index}')

    @unittest.skipIf(os.name == 'nt', 'The internal tar symlink fixture targets the macOS runtime archive.')
    def test_normal_zip_and_internal_tar_symlink_are_preserved(self):
        archive = self.root / 'normal.zip'
        with zipfile.ZipFile(archive, 'w') as writer:
            writer.writestr('bin/runtime', 'binary')
        setup.extract(archive, self.root / 'zipout')
        self.assertEqual((self.root / 'zipout/bin/runtime').read_text(), 'binary')
        archive = self.root / 'normal.tar'
        with tarfile.open(archive, 'w') as writer:
            item = tarfile.TarInfo('bin/runtime')
            item.size = 6
            writer.addfile(item, io.BytesIO(b'binary'))
            item = tarfile.TarInfo('bin/link')
            item.type = tarfile.SYMTYPE
            item.linkname = 'runtime'
            writer.addfile(item)
        setup.extract(archive, self.root / 'tarout')
        self.assertEqual((self.root / 'tarout/bin/link').read_text(), 'binary')


class ModelAndRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def store(self, root):
        data = b'model-fixture'
        digest = hashlib.sha256(data).hexdigest()
        blob = root / 'blobs' / ('sha256-' + digest)
        blob.parent.mkdir(parents=True, exist_ok=True)
        blob.write_bytes(data)
        record = {'config': {'digest': 'sha256:' + digest, 'size': len(data)}, 'layers': []}
        raw = json.dumps(record).encode()
        manifest = root / 'manifests/registry.ollama.ai/library/qwen2.5/7b-instruct-q4_K_M'
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_bytes(raw)
        return hashlib.sha256(raw).hexdigest(), blob

    def test_model_store_requires_pinned_manifest_and_complete_blobs(self):
        root = self.root / 'models'
        digest, blob = self.store(root)
        with patch.object(setup, 'DIGEST', digest):
            self.assertTrue(setup.valid_model_store(root))
            blob.write_bytes(b'truncated')
            self.assertFalse(setup.valid_model_store(root))
        with patch.object(setup, 'DIGEST', 'f' * 64):
            self.assertFalse(setup.valid_model_store(root))

    def wrapped_store(self):
        store = self.root / 'wrapped'
        digest, blob = self.store(store)
        manifest = store / 'manifests/registry.ollama.ai/library/qwen2.5/7b-instruct-q4_K_M'
        canonical = manifest.read_bytes()
        original = store / 'blobs' / ('sha256-' + digest)
        original.write_bytes(canonical)
        record = json.loads(canonical)
        record['layers'].append({'mediaType': 'application/vnd.docker.distribution.manifest.v2+json', 'digest': 'sha256:' + digest, 'size': len(canonical)})
        manifest.write_text(json.dumps(record))
        return store, digest, blob, manifest, original

    def test_modern_wrapper_reuses_verified_original_manifest(self):
        store, digest, blob, manifest, original = self.wrapped_store()
        self.assertNotEqual(hashlib.sha256(manifest.read_bytes()).hexdigest(), digest)
        with patch.object(setup, 'DIGEST', digest):
            self.assertTrue(setup.valid_model_store(store))
            blob.write_bytes(b'incomplete')
            self.assertFalse(setup.valid_model_store(store))

    def test_wrapper_rejects_tampered_canonical_manifest_even_with_same_size(self):
        store, digest, blob, manifest, original = self.wrapped_store()
        data = original.read_bytes()
        original.write_bytes(b'X' + data[1:])
        with patch.object(setup, 'DIGEST', digest):
            self.assertFalse(setup.valid_model_store(store))

    def test_wrapper_cannot_change_config_or_add_other_layers(self):
        store, digest, blob, manifest, original = self.wrapped_store()
        record = json.loads(manifest.read_text())
        record['config']['mediaType'] = 'changed-config'
        manifest.write_text(json.dumps(record))
        with patch.object(setup, 'DIGEST', digest):
            self.assertFalse(setup.valid_model_store(store))
        record['config'].pop('mediaType')
        record['layers'].append(dict(record['config']))
        manifest.write_text(json.dumps(record))
        with patch.object(setup, 'DIGEST', digest):
            self.assertFalse(setup.valid_model_store(store))

    def test_explicit_complete_store_wins_and_incomplete_store_is_not_reused(self):
        store = self.root / 'existing'
        digest, blob = self.store(store)
        connector = self.root / 'connector'
        with patch.object(setup, 'ROOT', connector), patch.object(setup, 'DIGEST', digest), patch.object(setup, 'project_roots', return_value=[connector]), patch.dict(os.environ, {'OLLAMA_MODELS': str(store)}), patch.object(setup.Path, 'home', return_value=self.root / 'home'):
            self.assertEqual(setup.model_directory(), store.resolve())
            blob.unlink()
            self.assertEqual(setup.model_directory(), connector / 'runtime/models')

    def test_adjacent_project_root_can_be_explicit_without_duplicate_roots(self):
        connector = self.root / 'connector'
        with patch.object(setup, 'ROOT', connector), patch.dict(os.environ, {'PROSELEDGER_PROJECT': str(self.root)}):
            paths = setup.project_roots()
            self.assertEqual(paths[0], self.root.resolve())
            self.assertEqual(len(paths), len(set(paths)))
            self.assertIn((self.root / 'ProseLedger').resolve(), paths)

    def test_old_codex_without_required_exec_flags_is_rejected(self):
        binary = self.root / 'codex'
        binary.write_text('fixture')
        with patch.object(setup, 'valid_binary', return_value=True), patch.object(setup.subprocess, 'run', return_value=Mock(returncode=0, stdout=b'--sandbox --ephemeral')):
            self.assertFalse(setup.valid_codex(binary))
        with patch.object(setup, 'valid_binary', return_value=True), patch.object(setup.subprocess, 'run', return_value=Mock(returncode=0, stdout=b'--sandbox --ephemeral --ignore-user-config --skip-git-repo-check')):
            self.assertTrue(setup.valid_codex(binary))

    def test_partial_windows_runtime_requires_both_helpers(self):
        binary = self.root / 'runtime/codex/codex.exe'
        binary.parent.mkdir(parents=True)
        binary.write_text('fixture')
        with patch.object(setup, 'ROOT', self.root), patch.object(setup.platform, 'system', return_value='Windows'):
            self.assertFalse(setup.bundled_codex_complete(binary))
            for kind in ('service', 'setup'):
                (binary.parent / f'codex-windows-sandbox-{kind}.exe').write_text('fixture')
            self.assertTrue(setup.bundled_codex_complete(binary))
            self.assertTrue(setup.bundled_codex_complete(self.root / 'external/codex.exe'))

    def test_codex_reuses_compatible_runtime_without_downloading(self):
        binary = self.root / 'codex'
        with patch.object(setup.native_runtime, 'executable', return_value=str(binary)), patch.object(setup, 'valid_codex', return_value=True), patch.object(setup, 'bundled_codex_complete', return_value=True), patch.object(setup, 'download') as download:
            self.assertEqual(setup.codex_binary(), binary)
            download.assert_not_called()


class OwnershipTests(unittest.TestCase):
    def test_existing_private_service_is_not_registered_as_owned(self):
        socket = Mock()
        socket.connect_ex.return_value = 0
        manager = Mock()
        manager.__enter__ = Mock(return_value=socket)
        manager.__exit__ = Mock(return_value=False)
        owned = []
        with patch.object(setup.socket, 'socket', return_value=manager), patch.object(setup, 'request_json', return_value={'version': 'fixture'}), patch.object(setup, 'check_model', return_value=True), patch.object(setup, 'launch_ollama') as launch:
            setup.prepare_ollama(owned)
        self.assertEqual(owned, [])
        launch.assert_not_called()

    @unittest.skipIf(os.name == 'nt', 'POSIX process groups; Windows uses its owned Job Object.')
    def test_cleanup_terminates_only_recorded_process_group(self):
        process = Mock(pid=43210)
        with patch.object(setup.os, 'killpg', create=True) as kill:
            setup.stop_owned([(process, None)])
        kill.assert_called_once_with(43210, signal.SIGTERM)
        process.wait.assert_called_once_with(timeout=10)

    def test_windows_cleanup_uses_owned_job_not_global_process_names(self):
        process, job = Mock(pid=99), Mock()
        with patch.object(setup.os, 'killpg', create=True) as kill:
            setup.stop_owned([(process, job)])
        job.terminate.assert_called_once_with()
        kill.assert_not_called()

    @unittest.skipIf(os.name == 'nt', 'POSIX process groups; Windows uses its owned Job Object.')
    def test_cleanup_escalates_only_its_own_timed_out_group(self):
        process = Mock(pid=43211)
        process.wait.side_effect = [subprocess.TimeoutExpired('ollama', 10), 0]
        with patch.object(setup.os, 'killpg', create=True) as kill:
            setup.stop_owned([(process, None)])
        self.assertEqual([call.args for call in kill.call_args_list], [(43211, signal.SIGTERM), (43211, signal.SIGKILL)])


if __name__ == '__main__':
    unittest.main()
