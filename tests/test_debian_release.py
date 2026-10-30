"""Exercise the built Debian package from an isolated extraction, without sudo."""
import io
from pathlib import Path
import runpy
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]

def test_debian_release_runs_outside_checkout(tmp_path):
    artifact = runpy.run_path(str(ROOT / 'tools/build_deb.py'))['build'](tmp_path / 'artifacts')
    control = subprocess.check_output(['dpkg-deb', '--field', str(artifact)], text=True)
    assert 'Architecture: all' in control
    assert 'Depends: python3 (>= 3.10)' in control
    archive = subprocess.check_output(['dpkg-deb', '--fsys-tarfile', str(artifact)])
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        members = tar.getmembers()
        assert all(m.uid == m.gid == 0 for m in members)
        assert all(not (m.mode & 0o7000) for m in members)
        assert not any('__pycache__' in m.name or m.name.endswith('.pyc') for m in members)
        assert any(m.name.endswith('/copyright') for m in members)
    extracted = tmp_path / 'root'
    subprocess.run(['dpkg-deb', '-x', str(artifact), str(extracted)], check=True)
    for name in ('ez8', 'ez8-native'):
        result = subprocess.run([str(extracted / 'usr/bin' / name), '--help'], cwd=tmp_path,
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        assert 'firmware' in result.stdout
    source = tmp_path / 'source with spaces.asm'
    source.write_text('NOP\nLD R0, #0x2A\n')
    destination = tmp_path / 'output with spaces.hex'
    result = subprocess.run([str(extracted / 'usr/bin/ez8'), 'asm', str(source), '-o', str(destination)],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert destination.read_text().startswith(':030000000F0C2AB8')
