"""Build the public connector ZIP from an explicit source-only file list."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = ['Start_Windows.bat', 'bootstrap_windows.ps1', 'Start_Mac.command', 'start.py',
         'bridge.py', 'native_runtime.py', 'windows_job.py', 'runtime_sources.json', 'README.md']
TARGET = ROOT / 'docs/local/ProseLedger_Local_Connector.zip'


def build():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in FILES:
            content = (ROOT / 'local_connector' / name).read_bytes()
            if name.endswith(('.bat', '.ps1')):
                content = content.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            info = zipfile.ZipInfo('ProseLedger_Local_Connector/' + name, (2026, 11, 13, 0, 0, 0))
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = ((0o100755 if name.endswith('.command') else 0o100644) << 16)
            archive.writestr(info, content)
    return stream.getvalue()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = build()
    if args.check:
        if not TARGET.is_file() or TARGET.read_bytes() != data:
            raise SystemExit('Connector ZIP differs from its source files. Run scripts/package_connector.py.')
    else:
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        TARGET.write_bytes(data)
    print(json.dumps({'files': len(FILES), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}))


if __name__ == '__main__':
    main()
