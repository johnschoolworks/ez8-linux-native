# Debian package — 0.4.0

The public release provides `ez8-linux-native_0.4.0_all.deb`. This is a direct
GitHub download; no APT repository is published.

| Field | Value |
|---|---|
| Package / version | `ez8-linux-native` / `0.4.0` |
| Architecture | `all` (Python source, no native machine code) |
| Runtime dependency | `python3 (>= 3.10)` |
| Launchers | `/usr/bin/ez8`, `/usr/bin/ez8-native` |
| Private application code | `/usr/lib/ez8-linux-native/ez8native/` |
| License and README | `/usr/share/doc/ez8-linux-native/` |
| Control template | `packaging/debian/control` |

## Install and remove

```sh
sudo apt install ./ez8-linux-native_0.4.0_all.deb
ez8 --help
sudo apt remove ez8-linux-native
```

The package uses the system Python and an explicit private import path; it does
not use pip or an installation-time script. Both launchers call
`ez8native.cli:main`. Physical programming is not exposed by the unified CLI.

## Build and inspect

From a checkout, with Python 3.11+, pytest, and dpkg-deb available:

```sh
bash build-deb.sh
dpkg-deb --info dist/ez8-linux-native_0.4.0_all.deb
dpkg-deb --contents dist/ez8-linux-native_0.4.0_all.deb
```

The build reads the version from `pyproject.toml`, uses a fresh temporary
staging tree, excludes Python caches, normalizes permissions, and records root
ownership with `dpkg-deb --root-owner-group`. No root privileges are needed to
build. `bash tools/build-release.sh` also produces the other release assets.

The package integration test extracts the archive into a temporary directory,
checks ownership and permissions, and invokes both launchers from outside the
checkout. It also assembles a file whose path contains spaces. A root-level
installation/uninstallation test is not part of this validation.

The old root-level 0.1.0 amd64 package and generated `debian/` tree are legacy
local artifacts. They are not release inputs. Their missing `ez8native.main`
entrypoint, import path, dependencies, and version mismatch are fixed in the
0.4.0 build; use the new `dist/` artifact.

The packaging approach follows [Debian control-field documentation](https://www.debian.org/doc/debian-policy/ch-controlfields.html)
and [dpkg-deb's archive ownership support](https://dyn.manpages.debian.org/bookworm/dpkg/dpkg-deb.1.en.html).
