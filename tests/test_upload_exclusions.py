"""Ensure local-only material cannot leak into source control or Debian payloads."""
import io
from pathlib import Path
import runpy
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]

def test_git_ignores_local_only_paths():
    paths = ['.env', '.env.production', '.aws/credentials', '.ssh/id_rsa',
             '.codex/config.toml', '.agents/local.json', '.pytest_cache/test',
             'backups/flash.bin', 'docs/hardware/vendor/manual.pdf',
             'vscode-extension/node_modules/example.js', 'local.pem', 'local.key',
             'dist/private.tmp', 'g34_identify_probe.py']
    result = subprocess.run(['git', 'check-ignore', '--no-index', '--stdin'],
                            cwd=ROOT, input='\n'.join(paths)+'\n', text=True,
                            capture_output=True, check=True)
    assert set(result.stdout.splitlines()) == set(paths)
    result = subprocess.run(['git', 'check-ignore', '--no-index', '.env.example',
                             'ez8native/cli.py', 'vscode-extension/package-lock.json'],
                            cwd=ROOT, capture_output=True, text=True)
    assert not result.stdout

def test_debian_only_copies_python_sources(tmp_path):
    source = tmp_path / 'source'
    package = source / 'ez8native'
    package.mkdir(parents=True)
    (package / '__init__.py').write_text('')
    for name in ('.env', 'private.key', 'firmware.bin', 'notes.txt'):
        (package / name).write_text('synthetic local-only data')
    hidden = package / '.local'
    hidden.mkdir()
    (hidden / 'private.py').write_text('')
    (package / 'linked.py').symlink_to(hidden / 'private.py')
    (source / 'pyproject.toml').write_text('[project]\nversion="0.4.0"\n')
    (source / 'README.md').write_text('test')
    (source / 'LICENSE').write_text('test')
    control = source / 'packaging/debian'
    control.mkdir(parents=True)
    (control / 'control').write_text((ROOT / 'packaging/debian/control').read_text())
    build = runpy.run_path(str(ROOT / 'tools/build_deb.py'))['build']
    build.__globals__['ROOT'] = source
    artifact = build(tmp_path / 'dist')
    archive = subprocess.check_output(['dpkg-deb', '--fsys-tarfile', str(artifact)])
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        payload = [m.name for m in tar.getmembers() if m.isfile() and '/ez8native/' in m.name]
    assert payload == ['./usr/lib/ez8-linux-native/ez8native/__init__.py']

def test_source_export_excludes_even_tracked_local_files(tmp_path):
    repository = tmp_path / 'repository'
    repository.mkdir()
    subprocess.run(['git', 'init', '-q', str(repository)], check=True)
    (repository / '.gitattributes').write_text((ROOT / '.gitattributes').read_text())
    private = ['.env', '.aws/credentials', '.codex/config.toml', 'backups/flash.bin',
               'docs/hardware/vendor/manual.pdf', 'client.key', 'build/output.hex',
               'vscode-extension/node_modules/dependency.js']
    for name in private + ['.env.example', 'ez8native/cli.py']:
        path = repository / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('synthetic test fixture')
    subprocess.run(['git', 'add', '-f', '.'], cwd=repository, check=True)
    tree = subprocess.check_output(['git', 'write-tree'], cwd=repository, text=True).strip()
    exported = subprocess.check_output(['git', 'archive', tree], cwd=repository)
    with tarfile.open(fileobj=io.BytesIO(exported)) as tar:
        names = set(tar.getnames())
    assert '.env.example' in names and 'ez8native/cli.py' in names
    assert not names.intersection(private)
