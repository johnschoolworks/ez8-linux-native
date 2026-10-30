#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
ez8_python="${EZ8_BUILD_PYTHON:-python3}"
ez8_version="$("$ez8_python" -c 'import pathlib,tomllib; print(tomllib.loads(pathlib.Path("pyproject.toml").read_text())["project"]["version"])')"
mkdir -p dist
"$ez8_python" -m pytest -q | tee dist/python-tests.log
"$ez8_python" -m build --no-isolation
"$ez8_python" tools/build_deb.py
(
  cd vscode-extension
  npm test | tee ../dist/extension-tests.log
  ./node_modules/.bin/vsce package --no-dependencies \
    --baseContentUrl "https://github.com/johntsaiainow/ez8-linux-native/blob/v${ez8_version}/vscode-extension" \
    --baseImagesUrl "https://github.com/johntsaiainow/ez8-linux-native/raw/v${ez8_version}/vscode-extension" \
    --out "../dist/ez8-extension-${ez8_version}.vsix"
)
"$ez8_python" tools/verify_release.py
