#!/bin/bash
set -eu
cd -- "$(dirname -- "$0")"
trap 'echo; echo "Connector stopped. You may close this window."; read -r -p "Press Enter to close..." _' EXIT
CONNECTOR_PYTHON=''
CONNECTOR_PATH_PYTHON="$(command -v python3 || true)"
for candidate in "$PWD/runtime/python/bin/python3" "$PWD/../runtime/macos/python/bin/python3" "$CONNECTOR_PATH_PYTHON" /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
  if [ -x "$candidate" ] && "$candidate" -c 'import sys, ssl, ctypes, urllib.request, tarfile, zipfile, http.server; sys.exit(0 if sys.version_info >= (3,12) else 1)' >/dev/null 2>&1; then
    CONNECTOR_PYTHON="$candidate"
    break
  fi
done
if [ -z "$CONNECTOR_PYTHON" ]; then
  echo 'Preparing a private Python runtime (first launch only)...'
  case "$(uname -m)" in
    arm64) archive_name='cpython-3.12.16%2B20261026-aarch64-apple-darwin-install_only.tar.gz'; checksum='fbf4afef53c2a6b72bb741bc06d5671a9dfaf87bd84e5aa73ac9b3d0d589f14e' ;;
    x86_64) archive_name='cpython-3.12.16%2B20261026-x86_64-apple-darwin-install_only.tar.gz'; checksum='a962e47df522889eaa7ff0d6a56203f1079f68aabb65ffdbe8455f362bc769f3' ;;
    *) echo 'This launcher supports Apple Silicon and Intel Macs.'; exit 1 ;;
  esac
  mkdir -p runtime
  curl --fail --location --retry 2 --connect-timeout 30 "https://github.com/astral-sh/python-build-standalone/releases/download/20261026/$archive_name" --output runtime/python.tar.gz
  actual="$(shasum -a 256 runtime/python.tar.gz | cut -d ' ' -f 1)"
  if [ "$actual" != "$checksum" ]; then echo 'Python download fingerprint mismatch. Start again.'; exit 1; fi
  tar -xzf runtime/python.tar.gz -C runtime
  rm runtime/python.tar.gz
  CONNECTOR_PYTHON="$PWD/runtime/python/bin/python3"
fi
"$CONNECTOR_PYTHON" "$PWD/start.py"
