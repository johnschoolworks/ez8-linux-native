"""Inspect distribution contents and smoke-test an isolated wheel install."""
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
VERSION = tomllib.loads((ROOT / 'pyproject.toml').read_text())['project']['version']

def verify():
    wheel = DIST / f'ez8_linux_native-{VERSION}-py3-none-any.whl'
    source = DIST / f'ez8_linux_native-{VERSION}.tar.gz'
    debian = DIST / f'ez8-linux-native_{VERSION}_all.deb'
    vsix = DIST / f'ez8-extension-{VERSION}.vsix'
    assets = [wheel, source, debian, vsix]
    for artifact in assets:
        if not artifact.is_file():
            raise RuntimeError(f'Missing release asset: {artifact}')
    with zipfile.ZipFile(wheel) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert any(name.endswith('/licenses/LICENSE') for name in names)
        assert not any(name.endswith(('.pdf', '.dll', '.pyc', '.bin')) for name in names)
    with tarfile.open(source) as archive:
        assert not any('/node_modules/' in name or '/backups/' in name or name.endswith(('.pdf', '.dll', '.bin')) for name in archive.getnames())
    with zipfile.ZipFile(vsix) as archive:
        assert archive.testzip() is None
        manifest = json.loads(archive.read('extension/package.json'))
        assert manifest['version'] == VERSION
        assert manifest['publisher'] == 'ai-now'
        assert 'extension/out/extension.js' in archive.namelist()
        assert any(name.lower() == 'extension/readme.md' for name in archive.namelist())
        assert any(name.lower() in ('extension/license', 'extension/license.txt') for name in archive.namelist())
        assert not any('/node_modules/' in name or name.endswith('.map') for name in archive.namelist())
    fields = subprocess.check_output(['dpkg-deb', '--field', str(debian)], text=True)
    assert f'Version: {VERSION}' in fields and 'Architecture: all' in fields
    with tempfile.TemporaryDirectory(prefix='ez8-release-check-') as temporary:
        temporary = Path(temporary)
        env = temporary / 'venv'
        subprocess.run([sys.executable, '-m', 'venv', str(env)], check=True)
        subprocess.run([str(env / 'bin/python'), '-m', 'pip', 'install', '--no-index', '--no-deps', str(wheel)], check=True)
        executable = env / 'bin/ez8'
        subprocess.run([str(executable), '--help'], cwd=temporary, check=True, stdout=subprocess.DEVNULL)
        input_file = temporary / 'source with spaces.asm'
        input_file.write_text('NOP\nLD R0, #0x2A\n')
        output = temporary / 'sample.hex'
        subprocess.run([str(executable), 'asm', str(input_file), '-o', str(output)], cwd=temporary, check=True)
        assert output.read_text().startswith(':030000000F0C2AB8')
        extracted = temporary / 'debian-root'
        subprocess.run(['dpkg-deb', '-x', str(debian), str(extracted)], check=True)
        for name in ('ez8', 'ez8-native'):
            subprocess.run([str(extracted / 'usr/bin' / name), '--help'], cwd=temporary, check=True, stdout=subprocess.DEVNULL)
    checksums = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in assets}
    (DIST / 'SHA256SUMS').write_text(''.join(f'{value}  {name}\n' for name, value in checksums.items()))
    report = dict(version=VERSION, status='local_validation_passed', published=False,
                  asset_sha256=checksums, wheel_install_python=sys.version.split()[0],
                  debian_extracted_launchers='passed', vsix_integrity='passed',
                  limitations=['No interactive VS Code extension-host test.', 'No root-level Debian installation test.',
                               'No new hardware validation performed for this packaging release.'])
    for filename, key, pattern in (
        ('python-tests.log', 'python_tests_passed', r'(\d+) passed'),
        ('python-tests.log', 'python_subtests_passed', r'(\d+) subtests passed'),
        ('extension-tests.log', 'extension_tests_passed', r'tests (\d+)')):
        log = DIST / filename
        match = re.search(pattern, log.read_text()) if log.exists() else None
        if match:
            report[key] = int(match.group(1))
    commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True)
    if commit.returncode == 0:
        report['source_commit'] = commit.stdout.strip()
    (DIST / 'release-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return report

if __name__ == '__main__':
    verify()
