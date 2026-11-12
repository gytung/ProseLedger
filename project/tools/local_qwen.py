"""Private local Qwen runtime setup. Standard library only; no account or API key needed.

--check performs local inspection only. --setup may download the pinned official
runtime and Qwen weights. --serve starts installed assets without downloading.
"""
from __future__ import annotations
import argparse,ctypes,hashlib,http.server,json,os,platform,re,shutil,socket,subprocess,sys,tarfile,tempfile,threading,time,urllib.error,urllib.request,webbrowser,zipfile
from pathlib import Path

ENDPOINT='http://127.0.0.1:11436'
MODEL='qwen2.5:7b-instruct-q4_K_M'
GIB=1024**3
class SetupError(RuntimeError):pass

def root_path(value=None):return Path(value).resolve() if value else Path(__file__).resolve().parents[1]
def sources(root):return json.loads((root/'platform/local_runtime_sources.json').read_text(encoding='utf-8'))
def request_json(path,body=None,timeout=2):
 data=None if body is None else json.dumps(body).encode()
 req=urllib.request.Request(ENDPOINT+path,data=data,headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=timeout) as response:return json.load(response)
def atomic_json(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.tmp')
 tmp.write_text(json.dumps(value,indent=2),encoding='utf-8');tmp.replace(path)
def fingerprint(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def platform_supported():
 system=platform.system();machine=platform.machine().lower()
 if system=='Windows' and machine not in ('amd64','x86_64'):raise SetupError('This Windows package requires an Intel or AMD 64-bit PC.')
 if system=='Windows' and sys.getwindowsversion().build<19045:raise SetupError('Local Qwen requires Windows 10 22H2 (build 19045) or Windows 11.')
 if system=='Darwin' and int(platform.mac_ver()[0].split('.')[0])<14:raise SetupError('The bundled Ollama runtime requires macOS 14 or later.')
 if system not in ('Windows','Darwin'):raise SetupError('Automatic local setup supports Windows and macOS.')
 return system

def hardware(root):
 ram=None
 try:
  if platform.system()=='Windows':
   class Memory(ctypes.Structure):
    _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong),('total',ctypes.c_ulonglong),('available',ctypes.c_ulonglong),('pageTotal',ctypes.c_ulonglong),('pageFree',ctypes.c_ulonglong),('virtualTotal',ctypes.c_ulonglong),('virtualFree',ctypes.c_ulonglong),('extendedFree',ctypes.c_ulonglong)]
   state=Memory();state.length=ctypes.sizeof(state)
   if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(state)):ram=state.total
  elif platform.system()=='Darwin':ram=int(subprocess.check_output(['/usr/sbin/sysctl','-n','hw.memsize'],text=True,stderr=subprocess.DEVNULL).strip())
 except (OSError,ValueError,subprocess.SubprocessError):pass
 return {'platform':platform.system(),'machine':platform.machine(),'ramGiB':round(ram/GIB,1) if ram else None,'freeDiskGiB':round(shutil.disk_usage(root).free/GIB,1),'guidance':'16 GB RAM and 15 GB free disk space recommended. CPU-only inference can take several minutes per section; GPU availability and drivers determine speed.'}

def installed_runtime(root):
 names=['ollama.exe'] if platform.system()=='Windows' else ['ollama']
 private=root/'runtime/ollama'
 candidates=[]
 if private.exists():candidates.extend(p for name in names for p in private.rglob(name) if p.is_file())
 found=shutil.which(names[0])
 if found:candidates.append(Path(found))
 if platform.system()=='Darwin':candidates.extend([Path('/Applications/Ollama.app/Contents/Resources/ollama'),Path('/opt/homebrew/bin/ollama'),Path('/usr/local/bin/ollama')])
 elif platform.system()=='Windows':candidates.append(Path(os.environ.get('LOCALAPPDATA',''))/'Programs/Ollama/ollama.exe')
 for p in candidates:
  if not p.is_file():continue
  try:
   opts={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
   result=subprocess.run([str(p),'--version'],capture_output=True,text=True,timeout=10,env={**os.environ,'OLLAMA_HOST':ENDPOINT},**opts)
   output=result.stdout+' '+result.stderr
   if result.returncode==0 and 'ollama' in output.lower():return p.resolve()
  except (OSError,subprocess.TimeoutExpired):pass
 return None

def runtime_version(runtime):
 if not runtime:return None
 try:
  opts={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
  r=subprocess.run([str(runtime),'--version'],capture_output=True,text=True,timeout=10,env={**os.environ,'OLLAMA_HOST':ENDPOINT},**opts)
  found=re.findall(r'\b\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.]+)?',r.stdout+' '+r.stderr)
  return found[-1] if found else None
 except (OSError,subprocess.SubprocessError):return None

def inspect(root):
 runtime=installed_runtime(root);version=None;models=[];error=None
 try:
  version=request_json('/api/version').get('version');models=request_json('/api/tags').get('models',[])
 except Exception as e:error=type(e).__name__
 record=next((x for x in models if x.get('name')==MODEL or x.get('model')==MODEL),None)
 expected=sources(root)['modelDigest'];digest=(record or {}).get('digest','').removeprefix('sha256:')
 owner_path=root/'runs/system/local_qwen_server.json';owner={}
 try:owner=json.loads(owner_path.read_text())
 except (OSError,ValueError):pass
 owned=owner.get('package')==str(root) and owner.get('endpoint')==ENDPOINT and pid_alive(owner.get('pid'))
 return {'endpoint':ENDPOINT,'model':MODEL,'runtime':str(runtime) if runtime else None,'runtimeVersion':runtime_version(runtime),'runtimeSource':'private-download' if runtime and root/'runtime/ollama' in runtime.parents else 'preinstalled' if runtime else None,'pinnedDownloadVersion':sources(root)['ollamaVersion'],'serverVersion':version,'serverOwned':owned,'modelInstalled':bool(record),'modelDigest':digest or None,'expectedModelDigest':expected,'modelDigestMatches':bool(record and digest==expected),'ready':bool(version and owned and record and digest==expected),'hardware':hardware(root),'probeError':error}

class Progress:
 def __init__(self,root):self.root=root;self.state={'stage':'Checking local setup','message':'Inspecting installed assets.','percent':None,'done':False,'error':False};self.lock=threading.Lock();self.server=None
 def update(self,stage,message='',percent=None,done=False,error=False):
  with self.lock:self.state={'stage':stage,'message':message,'percent':percent,'done':done,'error':error,'updatedAt':time.time()}
  print(stage+(': '+message if message else ''),flush=True)
  atomic_json(self.root/'runs/system/local_qwen_status.json',self.state)
 def start_ui(self):
  owner=self
  class Handler(http.server.BaseHTTPRequestHandler):
   def do_GET(self):
    if self.path=='/status':
     with owner.lock:body=json.dumps(owner.state).encode()
     kind='application/json'
    elif self.path in ('/','/index.html'):body=PAGE.encode();kind='text/html; charset=utf-8'
    else:self.send_error(404);return
    self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
   def log_message(self,*args):pass
  self.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
  threading.Thread(target=self.server.serve_forever,daemon=True).start();webbrowser.open(f'http://127.0.0.1:{self.server.server_address[1]}/')
 def close(self):
  if self.server:time.sleep(3);self.server.shutdown();self.server.server_close()
PAGE='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>ProseLedger · Local model setup</title><style>body{background:#fff;color:#4f4058;font:17px/1.6 system-ui;margin:9vh auto;max-width:850px;padding:24px}h1{font:bold italic 44px Georgia,serif}.card{border:1px solid #ddd3e6;border-radius:22px;padding:32px;background:#f8f5fb}progress{width:100%;height:20px;accent-color:#a28ab8}small{color:#786e80}#stage{font-weight:700;font-size:22px}.ok{color:#47734b}.error{color:#a24d62}</style><h1>Prepare your local writing model.</h1><p>ProseLedger installs Qwen2.5 7B on this computer. No model API key is required for local writing.</p><div class="card"><p id="stage">Checking setup…</p><progress id="bar"></progress><p id="message">Please keep the installer window open.</p></div><p><small>The first installation downloads the Ollama runtime and approximately 4.7 GB of model weights. Interrupted downloads can resume. Later launches reuse the installed files. CPU-only generation can be slow; 16 GB RAM and 15 GB free disk space are recommended.</small></p><p id="finish"></p><script>const tick=setInterval(async()=>{try{const r=await fetch('/status',{cache:'no-store'}),s=await r.json();stage.textContent=s.stage;message.textContent=s.message;if(s.percent===null)bar.removeAttribute('value');else{bar.max=100;bar.value=s.percent}if(s.done){clearInterval(tick);finish.className=s.error?'error':'ok';finish.textContent=s.error?'See the installer window for recovery steps. Your saved work is unchanged.':'Ready. You can close this tab and open ProseLedger.';}}catch{}},800);</script></html>'''

def download(asset,destination,progress):
 label=asset.get('label','Ollama');destination.parent.mkdir(parents=True,exist_ok=True);partial=destination.with_suffix(destination.suffix+'.part')
 if destination.exists() and fingerprint(destination)==asset['sha256']:return
 if destination.exists():destination.unlink()
 if partial.exists() and partial.stat().st_size>=asset['bytes']:
  if fingerprint(partial)==asset['sha256']:partial.replace(destination);return
  partial.unlink()
 for attempt in range(1,5):
  try:
   offset=partial.stat().st_size if partial.exists() else 0
   headers={'User-Agent':'ProseLedger-Local-Setup/1.0'}
   if offset:headers['Range']=f'bytes={offset}-'
   req=urllib.request.Request(asset['url'],headers=headers)
   with urllib.request.urlopen(req,timeout=60) as response:
    if offset and response.status!=206:offset=0
    total=int(asset['bytes']);mode='ab' if offset else 'wb';written=offset;last=0
    with partial.open(mode) as out:
     while True:
      chunk=response.read(1024*1024)
      if not chunk:break
      out.write(chunk);written+=len(chunk)
      if time.monotonic()-last>1:progress.update('Downloading '+label,f'{written/1e9:.2f} / {total/1e9:.2f} GB',min(99,100*written/total));last=time.monotonic()
   progress.update('Verifying '+label,'Checking the pinned SHA-256 fingerprint.')
   if fingerprint(partial)!=asset['sha256']:
    partial.unlink();raise SetupError('Runtime checksum mismatch; the incomplete download has been removed.')
   partial.replace(destination);return
  except (OSError,urllib.error.URLError,SetupError) as e:
   if attempt==4:raise SetupError('Runtime download failed after four attempts. Run Install again to resume. '+str(e)) from e
   progress.update('Retrying runtime download',f'Attempt {attempt+1}/4; partial data is retained.');time.sleep(min(2**attempt,8))

def safe_path(base,name):
 path=(base/name).resolve()
 if path!=base.resolve() and base.resolve() not in path.parents:raise SetupError('Unsafe archive path.')
 return path

def extract_runtime(archive,target):
 stage=target.with_name('ollama-extract-'+str(os.getpid()));stage.mkdir(parents=True,exist_ok=False)
 try:
  if archive.suffix=='.zip':
   with zipfile.ZipFile(archive) as z:
    for member in z.infolist():safe_path(stage,member.filename)
    z.extractall(stage)
  else:
   with tarfile.open(archive,'r:gz') as tar:
    for member in tar.getmembers():
     out=safe_path(stage,member.name)
     if member.issym():
      link=(out.parent/member.linkname).resolve()
      if link!=stage.resolve() and stage.resolve() not in link.parents:raise SetupError('Unsafe archive link.')
     if member.islnk():safe_path(stage,member.linkname)
     if not(member.isfile() or member.isdir() or member.issym() or member.islnk()):raise SetupError('Unsupported archive member.')
    if sys.version_info>=(3,12):tar.extractall(stage,filter='data')
    else:tar.extractall(stage)
  bins=list(stage.rglob('ollama.exe' if os.name=='nt' else 'ollama'))
  bins=[p for p in bins if p.is_file()]
  if not bins:raise SetupError('Ollama executable missing from the official archive.')
  if os.name!='nt':
   for binary in bins:binary.chmod(binary.stat().st_mode|0o755)
  if target.exists():raise SetupError('A partial runtime folder exists. Move runtime/ollama aside and retry installation.')
  stage.replace(target)
 finally:
  if stage.exists():shutil.rmtree(stage)

def ensure_runtime(root,allow_download,progress):
 runtime=installed_runtime(root)
 if runtime:return runtime
 if not allow_download:raise SetupError('Local Ollama is not installed. Run 01_Setup_Local_Qwen to download the runtime and model.')
 system=platform_supported();asset=sources(root)['runtimes'][system]
 free=shutil.disk_usage(root).free;minimum=14*GIB if system=='Windows' else 8*GIB
 if free<minimum:raise SetupError(f'At least {minimum/GIB:.0f} GB free disk space is required for first-time local setup. Move this folder to a drive with more space.')
 suffix='.zip' if system=='Windows' else '.tgz';archive=root/'runtime/downloads'/('ollama-'+sources(root)['ollamaVersion']+suffix)
 download(asset,archive,progress);progress.update('Installing runtime','Extracting verified files into this project folder.');extract_runtime(archive,root/'runtime/ollama')
 runtime=installed_runtime(root)
 if not runtime:raise SetupError('The downloaded Ollama executable did not start. Check OS support and security notifications.')
 archive.unlink(missing_ok=True);return runtime

def ensure_server(root,runtime,progress):
 state=inspect(root)
 if state['serverVersion']:
  if not state['serverOwned']:raise SetupError('Port 11436 is used by another Ollama process. Close that process or use a separate project session; no other process was stopped.')
  return
 # Never replace an unidentified listener.
 with socket.socket() as probe:
  if probe.connect_ex(('127.0.0.1',11436))==0:raise SetupError('Port 11436 is already in use. No existing service was changed.')
 progress.update('Starting local server','Ollama listens only on 127.0.0.1:11436.')
 models=root/'runtime/models';models.mkdir(parents=True,exist_ok=True);logs=root/'runs/system';logs.mkdir(parents=True,exist_ok=True)
 env={**os.environ,'OLLAMA_HOST':'127.0.0.1:11436','OLLAMA_MODELS':str(models),'OLLAMA_CONTEXT_LENGTH':'8192','OLLAMA_NUM_PARALLEL':'1','OLLAMA_MAX_LOADED_MODELS':'1','OLLAMA_KEEP_ALIVE':'5m','OLLAMA_DEBUG':'false','OLLAMA_NO_CLOUD':'1'}
 opts={'creationflags':subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.DETACHED_PROCESS} if os.name=='nt' else {'start_new_session':True}
 with (logs/'ollama.log').open('ab') as log:
  process=subprocess.Popen([str(runtime),'serve'],env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=log,**opts)
 atomic_json(logs/'local_qwen_server.json',{'package':str(root),'endpoint':ENDPOINT,'pid':process.pid,'runtime':str(runtime),'models':str(models),'startedAt':time.time()})
 for _ in range(60):
  if process.poll() is not None:raise SetupError('Ollama stopped during startup. See runs/system/ollama.log.')
  try:
   if request_json('/api/version').get('version'):return
  except Exception:pass
  time.sleep(.5)
 raise SetupError('Ollama did not become ready within 30 seconds. See runs/system/ollama.log.')

def ensure_model(root,allow_download,progress):
 state=inspect(root)
 if state['modelInstalled']:
  if not state['modelDigestMatches']:raise SetupError('The installed model tag has a different digest from this release. Do not replace it silently; inspect the recorded model identity.')
  return
 if not allow_download:raise SetupError('Qwen weights are not downloaded. Run 01_Setup_Local_Qwen; approximately 4.7 GB is required.')
 if shutil.disk_usage(root).free<6*GIB:raise SetupError('At least 6 GB free disk space is required for the Qwen model download.')
 for attempt in range(1,4):
  try:
   progress.update('Downloading Qwen2.5 7B','Approximately 4.7 GB. This download can resume after interruption.')
   req=urllib.request.Request(ENDPOINT+'/api/pull',data=json.dumps({'model':MODEL,'stream':True}).encode(),headers={'Content-Type':'application/json'})
   with urllib.request.urlopen(req,timeout=180) as response:
    last=0
    for line in response:
     if not line.strip():continue
     event=json.loads(line)
     if event.get('error'):raise SetupError(event['error'])
     status=event.get('status','Downloading model');total=event.get('total');completed=event.get('completed',0)
     if time.monotonic()-last>.8 or status=='success':
      if total:progress.update('Downloading Qwen2.5 7B',f'{status}: {completed/1e9:.2f} / {total/1e9:.2f} GB',min(99,100*completed/total))
      else:progress.update('Preparing Qwen2.5 7B',status)
      last=time.monotonic()
   state=inspect(root)
   if not state['modelDigestMatches']:raise SetupError('The pulled model digest does not match this release.')
   return
  except (OSError,urllib.error.URLError,ValueError,SetupError) as e:
   if attempt==3:raise SetupError('Qwen download could not finish. Run Install again; Ollama reuses downloaded layers. '+str(e)) from e
   progress.update('Retrying model download',f'Attempt {attempt+1}/3; downloaded layers are retained.');time.sleep(3)

def pid_alive(pid):
 if not isinstance(pid,int) or pid<=0:return False
 if os.name=='nt':
  kernel=ctypes.windll.kernel32;kernel.OpenProcess.restype=ctypes.c_void_p
  handle=kernel.OpenProcess(0x1000,False,pid)
  if not handle:return ctypes.GetLastError()==5
  code=ctypes.c_ulong()
  try:return bool(kernel.GetExitCodeProcess(ctypes.c_void_p(handle),ctypes.byref(code)) and code.value==259)
  finally:kernel.CloseHandle(ctypes.c_void_p(handle))
 try:os.kill(pid,0);return True
 except ProcessLookupError:return False
 except PermissionError:return True

def acquire_lock(lock):
 for attempt in range(3):
  try:
   descriptor=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(descriptor,str(os.getpid()).encode());os.close(descriptor);return
  except FileExistsError:
   try:
    prior=lock.read_bytes();age=time.time()-lock.stat().st_mtime
    try:pid=int(prior.decode().strip())
    except ValueError:pid=None
    if (pid is not None and not pid_alive(pid)) or (pid is None and age>600):
     if lock.exists() and lock.read_bytes()==prior:lock.unlink()
     continue
   except FileNotFoundError:continue
   raise SetupError('Another local-model setup is running. Wait for its progress window to finish, then retry.')
 raise SetupError('Could not acquire the local setup lock. Please retry once.')

def ensure_local(root,allow_download=False,show_ui=False):
 root=root_path(root);platform_supported();initial=inspect(root)
 if initial['ready']:return initial
 if initial['hardware']['ramGiB'] is not None and initial['hardware']['ramGiB']<7.5:raise SetupError('Qwen2.5 7B needs at least 8 GB system RAM; 16 GB is recommended. Use hosted API mode on this computer.')
 progress=Progress(root);lock=root/'runtime/local_qwen_setup.lock';lock.parent.mkdir(parents=True,exist_ok=True)
 acquire_lock(lock)
 try:
  if show_ui:progress.start_ui()
  progress.update('Checking computer',initial['hardware']['guidance'])
  runtime=ensure_runtime(root,allow_download,progress);ensure_server(root,runtime,progress);ensure_model(root,allow_download,progress)
  result=inspect(root)
  if not result['ready']:raise SetupError('Local setup did not pass readiness checks.')
  atomic_json(root/'runs/system/local_qwen_ready.json',result);progress.update('Local Qwen is ready','Model files will be reused on the next launch. No API key is needed for local writing.',100,done=True);return result
 except Exception as e:progress.update('Setup needs attention',str(e),done=True,error=True);raise
 finally:lock.unlink(missing_ok=True);progress.close()

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 group=parser.add_mutually_exclusive_group(required=True);group.add_argument('--check',action='store_true',help='Inspect local runtime, server and model without downloads or starting services');group.add_argument('--setup',action='store_true',help='Install missing runtime/model, with resumable downloads, and start the private service');group.add_argument('--serve',action='store_true',help='Start installed local assets; never download')
 parser.add_argument('--package',type=Path,help='Project folder (detected automatically by default)');parser.add_argument('--ui',action='store_true',help='Show installation progress in a local browser window')
 args=parser.parse_args();root=root_path(args.package)
 try:
  result=inspect(root) if args.check else ensure_local(root,allow_download=args.setup,show_ui=args.ui)
  print(json.dumps(result,indent=2));return 0
 except (SetupError,OSError,ValueError) as e:print('Local setup: '+str(e),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
