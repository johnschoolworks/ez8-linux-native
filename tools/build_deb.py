"""Build the architecture-independent Debian release without root or network."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]

def build(output=None):
    version = tomllib.loads((ROOT / 'pyproject.toml').read_text())['project']['version']
    output = Path(output or ROOT / 'dist')
    output.mkdir(parents=True, exist_ok=True)
    destination = output.resolve() / f'ez8-linux-native_{version}_all.deb'
    with tempfile.TemporaryDirectory(prefix='ez8-deb-') as temporary:
        stage = Path(temporary)
        control = stage / 'DEBIAN'
        control.mkdir()
        (control / 'control').write_text((ROOT / 'packaging/debian/control').read_text().replace('@VERSION@', version))
        library = stage / 'usr/lib/ez8-linux-native'
        shutil.copytree(ROOT / 'ez8native', library / 'ez8native',
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo'))
        binary = stage / 'usr/bin'
        binary.mkdir(parents=True)
        launcher = '''#!/usr/bin/python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib/ez8-linux-native"))
from ez8native.cli import main
raise SystemExit(main())
'''
        for name in ('ez8', 'ez8-native'):
            (binary / name).write_text(launcher)
        documentation = stage / 'usr/share/doc/ez8-linux-native'
        documentation.mkdir(parents=True)
        shutil.copyfile(ROOT / 'README.md', documentation / 'README.md')
        shutil.copyfile(ROOT / 'LICENSE', documentation / 'copyright')
        for path in (stage, *stage.rglob('*')):
            os.chmod(path, 0o755 if path.is_dir() or path.parent == binary else 0o644)
        subprocess.run(['dpkg-deb', '--root-owner-group', '--build', str(stage), str(destination)], check=True)
    return destination

if __name__ == '__main__':
    print(build())
