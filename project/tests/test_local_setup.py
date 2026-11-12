from pathlib import Path
import importlib.util,json,hashlib,os,tarfile,io,tempfile,unittest,zipfile
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('local_qwen',ROOT/'tools/local_qwen.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class LocalSetupTests(unittest.TestCase):
 def test_source_pins(self):
  d=m.sources(ROOT);self.assertEqual(len(d['modelDigest']),64)
  for a in d['runtimes'].values():self.assertTrue(a['url'].startswith('https://github.com/ollama/ollama/'));self.assertEqual(len(a['sha256']),64)
 def test_loopback_endpoint(self):self.assertEqual(m.ENDPOINT,'http://127.0.0.1:11436')
 def test_safe_path(self):
  with tempfile.TemporaryDirectory() as t:self.assertEqual(m.safe_path(Path(t),'lib/file'),Path(t).resolve()/'lib/file')
 def test_parent_traversal(self):
  with tempfile.TemporaryDirectory() as t:
   with self.assertRaises(m.SetupError):m.safe_path(Path(t),'../outside')
 def test_live_lock(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'lock';p.write_text(str(os.getpid()))
   with self.assertRaises(m.SetupError):m.acquire_lock(p)
   self.assertEqual(p.read_text(),str(os.getpid()))
 def test_stale_lock(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'lock';p.write_text('999999999');m.acquire_lock(p);self.assertEqual(p.read_text(),str(os.getpid()))
 def test_zip_traversal(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);z=p/'bad.zip'
   with zipfile.ZipFile(z,'w') as f:f.writestr('../outside','bad')
   with self.assertRaises(m.SetupError):m.extract_runtime(z,p/'runtime')
   self.assertFalse((p.parent/'outside').exists())
 def test_tar_traversal(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);z=p/'bad.tgz'
   with tarfile.open(z,'w:gz') as f:
    n=tarfile.TarInfo('../outside');n.size=1;f.addfile(n,io.BytesIO(b'x'))
   with self.assertRaises(m.SetupError):m.extract_runtime(z,p/'runtime')
 @unittest.skipIf(os.name == 'nt', 'macOS runtime tar fixture')
 def test_valid_tar(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);z=p/'good.tgz'
   with tarfile.open(z,'w:gz') as f:
    n=tarfile.TarInfo('bin/ollama');n.size=3;n.mode=0o755;f.addfile(n,io.BytesIO(b'bin'))
    n=tarfile.TarInfo('ollama');n.type=tarfile.SYMTYPE;n.linkname='bin/ollama';f.addfile(n)
   m.extract_runtime(z,p/'runtime');self.assertEqual((p/'runtime/bin/ollama').read_bytes(),b'bin')
 def test_outside_symlink(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);z=p/'bad.tgz'
   with tarfile.open(z,'w:gz') as f:
    n=tarfile.TarInfo('ollama');n.type=tarfile.SYMTYPE;n.linkname='../../outside';f.addfile(n)
   with self.assertRaises(m.SetupError):m.extract_runtime(z,p/'runtime')
 def test_complete_partial_resumes_without_network(self):
  with tempfile.TemporaryDirectory() as t:
   dest=Path(t)/'file.tgz';dest.with_suffix('.tgz.part').write_bytes(b'complete')
   class Progress:
    def update(self,*a,**k):pass
   with patch.object(m.urllib.request,'urlopen',side_effect=AssertionError('Network not expected')):
    m.download({'bytes':8,'sha256':hashlib.sha256(b'complete').hexdigest(),'url':'https://example.invalid'},dest,Progress())
   self.assertEqual(dest.read_bytes(),b'complete')
 def test_inspect_owned_digest(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/'platform').mkdir();(root/'platform/local_runtime_sources.json').write_text((ROOT/'platform/local_runtime_sources.json').read_text());m.atomic_json(root/'runs/system/local_qwen_server.json',{'package':str(root),'endpoint':m.ENDPOINT,'pid':os.getpid()})
   d=m.sources(root)['modelDigest']
   with patch.object(m,'installed_runtime',return_value=None),patch.object(m,'hardware',return_value={}),patch.object(m,'request_json',side_effect=lambda p:{'version':'0.40.15'} if p=='/api/version' else {'models':[{'name':m.MODEL,'digest':d}]}):self.assertTrue(m.inspect(root)['ready'])
 def test_stale_owner_is_not_trusted(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/'platform').mkdir();(root/'platform/local_runtime_sources.json').write_text((ROOT/'platform/local_runtime_sources.json').read_text());m.atomic_json(root/'runs/system/local_qwen_server.json',{'package':str(root),'endpoint':m.ENDPOINT,'pid':999999999})
   d=m.sources(root)['modelDigest']
   with patch.object(m,'installed_runtime',return_value=None),patch.object(m,'hardware',return_value={}),patch.object(m,'request_json',side_effect=lambda p:{'version':'0.40.15'} if p=='/api/version' else {'models':[{'name':m.MODEL,'digest':d}]}):self.assertFalse(m.inspect(root)['ready'])
 def test_inspect_rejects_changed_model(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/'platform').mkdir();(root/'platform/local_runtime_sources.json').write_text((ROOT/'platform/local_runtime_sources.json').read_text());m.atomic_json(root/'runs/system/local_qwen_server.json',{'package':str(root),'endpoint':m.ENDPOINT,'pid':os.getpid()})
   with patch.object(m,'installed_runtime',return_value=None),patch.object(m,'hardware',return_value={}),patch.object(m,'request_json',side_effect=lambda p:{'version':'0.40.15'} if p=='/api/version' else {'models':[{'name':m.MODEL,'digest':'wrong'}]}):self.assertFalse(m.inspect(root)['ready'])
if __name__=='__main__':unittest.main()
