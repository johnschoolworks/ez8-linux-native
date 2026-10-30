#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
ez8_python="${EZ8_BUILD_PYTHON:-python3}"
"$ez8_python" -m pytest -q
"$ez8_python" tools/build_deb.py
