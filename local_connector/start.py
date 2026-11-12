"""Prepare private runtimes and serve a paired, loopback-only writing workspace."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import platform
import shutil
import signal
import ssl
import re
import socket
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
import webbrowser
import zipfile

# Private embedded Python may omit the script directory from its search path.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import bridge
import native_runtime
ASSETS = json.loads((ROOT / 'runtime_sources.json').read_text())
ORIGIN = 'https://gytung.github.io'
OLLAMA = 'http://127.0.0.1:11436'
MODEL = 'qwen2.5:7b-instruct-q4_K_M'
DIGEST = ASSETS['modelDigest']


def progress(message):
    print(message, flush=True)


def fingerprint(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def download(asset):
    cache = ROOT / 'runtime/downloads'
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / asset['url'].rsplit('/', 1)[-1]
    if target.exists() and fingerprint(target) == asset['sha256']:
        return target
    part = target.with_name(target.name + '.part')
    for attempt in range(3):
        try:
            offset = part.stat().st_size if part.exists() else 0
            headers = {'User-Agent': 'ProseLedger-Connector/1'}
            if offset:
                headers['Range'] = f'bytes={offset}-'
            progress('Downloading ' + target.name + ' (first installation only)...')
            with urllib.request.urlopen(urllib.request.Request(asset['url'], headers=headers), timeout=60) as response:
                if response.status != 206:
                    offset = 0
                with part.open('ab' if offset else 'wb') as output:
                    last = time.monotonic()
                    count = offset
                    while True:
                        block = response.read(1024 * 1024)
                        if not block:
                            break
                        output.write(block)
                        count += len(block)
                        if time.monotonic() - last > 5:
                            progress(f'  {count / 1e6:.0f} MB received')
                            last = time.monotonic()
            if fingerprint(part) != asset['sha256']:
                part.unlink()
                raise RuntimeError('Download fingerprint mismatch. Please start again.')
            part.replace(target)
            return target
        except (OSError, urllib.error.URLError):
            if attempt == 2:
                raise RuntimeError('Download interrupted. Start again to resume the partial download.') from None
            time.sleep(2)


def extract(archive, target):
    target.mkdir(parents=True, exist_ok=True)
    def inside(name):
        win = PureWindowsPath(name)
        if win.drive or win.is_absolute() or PurePosixPath(name).is_absolute() or '..' in win.parts or ':' in name:
            raise RuntimeError('Unsafe archive path.')
        path = (target / name).resolve()
        if path != target.resolve() and target.resolve() not in path.parents:
            raise RuntimeError('Unsafe archive path.')
        return path
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as source:
            for item in source.infolist():
                inside(item.filename)
                if (item.external_attr >> 16) & 0o170000 == 0o120000:
                    raise RuntimeError('Unexpected archive symlink.')
            source.extractall(target)
    else:
        with tarfile.open(archive) as source:
            for item in source.getmembers():
                out = inside(item.name)
                if item.issym():
                    link = (out.parent / item.linkname).resolve()
                    if link != target.resolve() and target.resolve() not in link.parents:
                        raise RuntimeError('Unsafe archive link.')
                if item.islnk():
                    inside(item.linkname)
                if not (item.isfile() or item.isdir() or item.issym() or item.islnk()):
                    raise RuntimeError('Unexpected archive entry.')
            source.extractall(target, filter='data')


def project_roots():
    # A connector extracted inside or next to the desktop package reuses its assets.
    roots = [ROOT, ROOT.parent, ROOT.parent / 'ProseLedger', ROOT.parent / 'Project']
    external = os.environ.get('PROSELEDGER_PROJECT')
    if external:
        roots.insert(0, Path(external).expanduser().resolve())
    return list(dict.fromkeys(path.resolve() for path in roots))


def valid_binary(path):
    if not path or not Path(path).is_file():
        return False
    try:
        result = subprocess.run([str(path), '--version'], capture_output=True, timeout=12)
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def valid_codex(path):
    if not valid_binary(path):
        return False
    try:
        result = subprocess.run([str(path), 'exec', '--help'], capture_output=True, timeout=12)
        text = result.stdout.decode('utf-8', 'replace')
        return result.returncode == 0 and all(flag in text for flag in ('--ignore-user-config', '--ephemeral', '--sandbox', '--skip-git-repo-check'))
    except (OSError, subprocess.SubprocessError):
        return False


def bundled_codex_complete(path):
    if platform.system() != 'Windows' or path.resolve().parent != (ROOT / 'runtime/codex').resolve():
        return True
    return all((path.parent / f'codex-windows-sandbox-{kind}.exe').is_file() for kind in ('service', 'setup'))

def codex_binary():
    candidates = []
    try:
        candidates.append(native_runtime.executable())
    except native_runtime.NativeError:
        pass
    for root in project_roots():
        candidates += [root / 'runtime/windows/codex.exe', root / 'runtime/macos/codex', root / 'runtime/codex/codex.exe', root / 'runtime/codex/codex']
    for path in candidates:
        if valid_codex(path) and bundled_codex_complete(Path(path)):
            return Path(path)
    system = platform.system()
    key = 'Windows' if system == 'Windows' else 'Darwin-' + platform.machine().lower()
    target = ROOT / 'runtime/codex'
    archive = download(ASSETS['codex'][key])
    extract(archive, target)
    name = 'codex.exe' if system == 'Windows' else 'codex'
    found = [p for p in target.rglob('*') if p.is_file() and (p.name == name or p.name.startswith('codex-')) and 'sandbox' not in p.name]
    if not found:
        raise RuntimeError('Official account runtime executable was not found in its archive.')
    destination = target / name
    if found[0].resolve() != destination.resolve():
        shutil.copy2(found[0], destination)
    if system == 'Windows':
        for kind in ['service', 'setup']:
            part = target / kind
            extract(download(ASSETS['codex']['Windows-' + kind]), part)
            binary = next(part.rglob('*.exe'))
            shutil.copy2(binary, target / f'codex-windows-sandbox-{kind}.exe')
    else:
        destination.chmod(0o755)
    if not valid_codex(destination):
        raise RuntimeError('The installed account runtime could not start with the required text-only features on this computer.')
    return destination


def ollama_binary():
    exe = 'ollama.exe' if os.name == 'nt' else 'ollama'
    candidates = [shutil.which(exe)]
    for root in project_roots():
        location = root / 'runtime/ollama'
        if location.is_dir():
            candidates += list(location.rglob(exe))
    candidates += [Path('/Applications/Ollama.app/Contents/Resources/ollama'), Path(os.environ.get('LOCALAPPDATA', '.')) / 'Programs/Ollama/ollama.exe']
    for path in candidates:
        if valid_binary(path):
            return Path(path)
    target = ROOT / 'runtime/ollama'
    extract(download(ASSETS['runtimes'][platform.system()]), target)
    binary = next(p for p in target.rglob(exe) if p.is_file())
    if os.name != 'nt':
        binary.chmod(0o755)
    if not valid_binary(binary):
        raise RuntimeError('The installed Ollama runtime could not start.')
    return binary


def valid_model_store(path):
    manifest = path / 'manifests/registry.ollama.ai/library/qwen2.5/7b-instruct-q4_K_M'
    manifest_type = 'application/vnd.docker.distribution.manifest.v2+json'

    def complete(record):
        if not isinstance(record, dict) or not isinstance(record.get('config'), dict) or not isinstance(record.get('layers'), list):
            return False
        for blob in [record['config'], *record['layers']]:
            if not isinstance(blob, dict):
                return False
            digest, size = blob.get('digest', ''), blob.get('size')
            if not isinstance(digest, str) or not re.fullmatch(r'sha256:[a-f0-9]{64}', digest) or type(size) is not int or size < 0:
                return False
            item = path / 'blobs' / digest.replace(':', '-')
            if not item.is_file() or item.stat().st_size != size:
                return False
        return True

    try:
        if not manifest.is_file() or manifest.stat().st_size > 1024 * 1024:
            return False
        raw = manifest.read_bytes()
        record = json.loads(raw)
        if not complete(record):
            return False
        if hashlib.sha256(raw).hexdigest() == DIGEST:
            return True
        # Newer Ollama stores the original registry manifest as an extra layer.
        links = [blob for blob in record['layers'] if blob.get('mediaType') == manifest_type]
        if len(links) != 1 or links[0].get('digest') != 'sha256:' + DIGEST or links[0]['size'] > 1024 * 1024:
            return False
        original = path / 'blobs' / ('sha256-' + DIGEST)
        canonical_raw = original.read_bytes()
        if hashlib.sha256(canonical_raw).hexdigest() != DIGEST:
            return False
        canonical = json.loads(canonical_raw)
        if not complete(canonical):
            return False
        remaining = [blob for blob in record['layers'] if blob is not links[0]]
        return (record.get('schemaVersion') == canonical.get('schemaVersion')
                and record.get('mediaType') == canonical.get('mediaType')
                and record['config'] == canonical['config']
                and remaining == canonical['layers'])
    except (OSError, ValueError, KeyError, TypeError):
        return False


def model_directory():
    candidates = [Path(os.environ['OLLAMA_MODELS']).expanduser()] if os.environ.get('OLLAMA_MODELS') else []
    candidates += [p / 'runtime/models' for p in project_roots()]
    candidates += [Path.home() / '.ollama/models']
    for path in candidates:
        if valid_model_store(path):
            progress('Reusing the existing pinned Qwen model files.')
            return path.resolve()
    return ROOT / 'runtime/models'


def launch_ollama(binary, env, log_path):
    """Own only this launcher-created server and its descendants."""
    job = None
    kwargs = {'start_new_session': True}
    if os.name == 'nt':
        from windows_job import WindowsJob
        job = WindowsJob()
        kwargs = {'creationflags': subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP | 4}
    process = None
    try:
        with log_path.open('ab') as log:
            process = subprocess.Popen([str(binary), 'serve'], env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=log, **kwargs)
        if job:
            job.attach_and_resume(process.pid)
        return process, job
    except BaseException:
        if job:
            job.terminate()
        if process and process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        raise


def stop_owned(owned):
    for process, job in reversed(owned):
        if job:
            job.terminate()
        else:
            # Every POSIX service was launched with its own session/process group.
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            if job:
                job.terminate()
            else:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            process.wait(timeout=5)


def request_json(route):
    request = urllib.request.Request(OLLAMA + route, headers={'Origin': ORIGIN})
    with urllib.request.urlopen(request, timeout=5) as response:
        if response.headers.get('Access-Control-Allow-Origin') != ORIGIN:
            raise RuntimeError('An existing service on port 11436 does not allow this website. Close its launcher and restart this connector; no existing service was changed.')
        return json.load(response)


def check_model():
    record = next((x for x in request_json('/api/tags').get('models', []) if x.get('name') == MODEL or x.get('model') == MODEL), None)
    if record and record.get('digest', '').removeprefix('sha256:') != DIGEST:
        raise RuntimeError('The model tag has a different fingerprint. It was not replaced. Use the required Qwen2.5 7B model.')
    return bool(record)


def prepare_ollama(owned):
    models = None
    with socket.socket() as probe:
        occupied = probe.connect_ex(('127.0.0.1', 11436)) == 0
    if occupied:
        request_json('/api/version')
        progress('Using the existing website-enabled private Ollama service.')
    else:
        binary = ollama_binary()
        models = model_directory()
        models.mkdir(parents=True, exist_ok=True)
        env = {**os.environ, 'OLLAMA_HOST': '127.0.0.1:11436', 'OLLAMA_ORIGINS': ORIGIN, 'OLLAMA_MODELS': str(models), 'OLLAMA_CONTEXT_LENGTH': '8192', 'OLLAMA_NUM_PARALLEL': '1', 'OLLAMA_MAX_LOADED_MODELS': '1', 'OLLAMA_KEEP_ALIVE': '5m', 'OLLAMA_NO_CLOUD': '1'}
        log_path = ROOT / 'runtime/ollama-service.log'
        log_path.parent.mkdir(parents=True, exist_ok=True)
        process, job = launch_ollama(binary, env, log_path)
        owned.append((process, job))
        for _ in range(60):
            if process.poll() is not None:
                raise RuntimeError('Ollama stopped. Check runtime/ollama-service.log.')
            try:
                request_json('/api/version')
                break
            except (OSError, urllib.error.URLError):
                time.sleep(.5)
        else:
            raise RuntimeError('Ollama did not start within 30 seconds.')
    model_present = check_model()
    if not model_present or (models is not None and not valid_model_store(models)):
        if shutil.disk_usage(ROOT).free < 6 * 1024 ** 3:
            raise RuntimeError('Allow at least 6 GB free disk space for the model, and 15 GB for a fresh installation.')
        progress('Downloading Qwen2.5 7B (approximately 4.7 GB). Interrupted model downloads can resume.')
        req = urllib.request.Request(OLLAMA + '/api/pull', data=json.dumps({'model': MODEL, 'stream': True}).encode(), headers={'Content-Type': 'application/json', 'Origin': ORIGIN})
        with urllib.request.urlopen(req, timeout=900) as response:
            last = 0
            for line in response:
                item = json.loads(line)
                if item.get('error'):
                    raise RuntimeError('Model download failed. Start again to resume; check your network and free disk space.')
                if time.monotonic() - last > 3:
                    total = item.get('total', 0)
                    suffix = f" {100 * item.get('completed', 0) / total:.0f}%" if total else ''
                    progress('  ' + item.get('status', 'Downloading') + suffix)
                    last = time.monotonic()
        if not check_model():
            raise RuntimeError('The model is not ready. Restart the connector to resume setup.')
    progress('Qwen2.5 7B is ready at ' + OLLAMA)


def main():
    if sys.version_info < (3, 12):
        raise RuntimeError('Python 3.12 or newer is required. Use the supplied launcher to prepare it.')
    if platform.system() == 'Darwin' and not os.environ.get('SSL_CERT_FILE') and not os.environ.get('SSL_CERT_DIR') and ssl.get_default_verify_paths().cafile is None and Path('/etc/ssl/cert.pem').is_file():
        os.environ['SSL_CERT_FILE'] = '/etc/ssl/cert.pem'
    if platform.system() not in ('Windows', 'Darwin'):
        raise RuntimeError('The automatic launcher supports Windows and macOS.')
    if platform.system() == 'Windows' and platform.machine().lower() not in ('amd64', 'x86_64'):
        raise RuntimeError('This installer requires a 64-bit Intel/AMD Windows computer.')
    progress('ProseLedger local connector\n1. Full workflow: Codex + local Qwen 7B (recommended)\n2. Proposal generation only: Codex')
    full = '--draft-only' not in sys.argv and input('Press Enter for full setup, or type 2 for proposal only: ').strip() != '2'
    owned = []
    server = None
    try:
        # Reserve the account port before preparing models or changing runtime state.
        server = bridge.BridgeServer()
        binary = codex_binary()
        os.environ['PROSELEDGER_CODEX_PATH'] = str(binary)
        if not native_runtime.login_status()['authenticated']:
            progress('Sign in using your own account in the official login window.')
            result = subprocess.run([str(binary), 'login'], env=native_runtime.safe_environment())
            if result.returncode or not native_runtime.login_status()['authenticated']:
                raise RuntimeError('Sign-in was not completed. Restart the connector after signing in.')
        if full:
            prepare_ollama(owned)
        progress('\nREADY. Keep this window open while using the website.')
        progress('Account connector: http://127.0.0.1:11437')
        progress('Pair code (paste into the website on this computer):\n' + server.token)
        progress('Proposal: https://gytung.github.io/ProseLedger/create.html')
        progress('Revision: https://gytung.github.io/ProseLedger/revise.html')
        progress('Allow the website to connect to this computer when your browser asks. Ctrl+C stops this session.')
        webbrowser.open(ORIGIN + '/ProseLedger/create.html')
        server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt:
        progress('\nStopping this connector session.')
    finally:
        if server:
            server.server_close()
        stop_owned(owned)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        progress('Setup stopped: ' + str(error))
        progress('Your documents and account login were not deleted. Correct the issue above, then launch again.')
        raise SystemExit(1)
