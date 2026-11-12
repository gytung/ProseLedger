#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if ! command -v python3 >/dev/null 2>&1; then
    printf '%s\n' 'Python 3.10 or later is required. Install Python from python.org.'
    exit 1
fi
python3 launch.py verify
