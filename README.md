# eZ8 Linux Native

Linux-native assembler, linker, and firmware tools for Zilog eZ8 / Z8F0822.

**Public release: 0.4.0.** Download assets from
[GitHub Releases](https://github.com/johntsaiainow/ez8-linux-native/releases/tag/v0.4.0).
This early public release supports the verified instruction subset described
below; it is not a complete replacement for ZDS II.

## Install

Python 3.10+ is required. Choose one installation route.

### Debian / Ubuntu

Download `ez8-linux-native_0.4.0_all.deb`, then:

```sh
sudo apt install ./ez8-linux-native_0.4.0_all.deb
ez8 --help
```

The architecture-independent package installs `ez8` and the compatibility
launcher `ez8-native`. See [Debian packaging](docs/DEBIAN-PACKAGE.md).

### Python wheel or source checkout

```sh
python3 -m venv .venv
.venv/bin/python -m pip install ./ez8_linux_native-0.4.0-py3-none-any.whl
.venv/bin/ez8 --help
```

For a checkout, use `.venv/bin/python -m pip install -e .` instead. Source
builds require setuptools 78+. Build dependencies must be available locally
when using `--no-index --no-build-isolation`.

### VS Code

Download `ez8-extension-0.4.0.vsix`, then:

```sh
code --install-extension ./ez8-extension-0.4.0.vsix
```

The extension requires VS Code `^1.80.0`. Install the CLI separately, then use
**EZ8: Run Native Tool** for help or **EZ8: Assemble Active File** to choose
an Intel HEX output file. Set `ez8.toolPath` to an absolute executable path
when using a virtual environment. See the [extension guide](vscode-extension/README.md).

## Features and scope

- Pure Python native assembler with data directives, labels, verified register
  operands, conditional branches, and extended immediate instruction forms.
- Native EZO objects, relocations, linker, Intel HEX checksums and bounds checks,
  Z8F0822 vector ownership validation, and startup code.
- CLI commands: `ez8 asm`, `ez8 object`, `ez8 link`, `ez8 firmware`, and
  `ez8 debug-mock`. Each accepts `--help`.
- Hardware evidence includes serial Smart Cable identification, DEBUG-mode
  Flash backup, page-0 erase/write/read-back, and native firmware execution.
  The G3.9 three-LED sequencer was observed on the documented evaluation board.

The unified CLI and extension expose **offline tools only**. Physical programmer
and debugger Python APIs remain specialized and require explicit opt-in;
packaging them does not make them general-purpose hardware tools. The extension
has no language server, syntax grammar, breakpoint debugger, or Flash command.

The full eZ8 instruction set and a native C compiler are not implemented.
`.dw` is a big-endian data convention; strict firmware/vector checks must be
used for boot headers. The data smoke sample is not executable firmware and
must not be flashed. Any new hardware image requires its own validation.

## Example

```sh
ez8 asm tests/golden/reference/instructions.asm -o build/instructions.hex
ez8 object --help
ez8 firmware --help
```

For a checkout-only data sample, run `make smoke`. For firmware reconstruction,
see the [CLI guide](docs/G4.0-CLI-USER-GUIDE.md),
[hardware validation](docs/hardware/G3.9-FINAL-HARDWARE-VALIDATION.md).

## Development and release builds

Runtime: Python 3.10+. Release build host: Python 3.11+ with setuptools 78+,
wheel, build, and pytest; Node.js 24 with npm; and dpkg-deb.

```sh
python3 -m pip install 'setuptools>=78' wheel build pytest
npm --prefix vscode-extension ci --ignore-scripts
make test
bash tools/build-release.sh
```

The release script runs the full Python regression and extension tests, builds
the wheel, source archive, Debian package, and VSIX, then checks extracted
packages and an isolated wheel installation. Assets, `SHA256SUMS`, and
`release-validation.json` are written to `dist/`. Vendor PDFs, device backups,
dependency trees, and old binary packages are excluded.

See [release notes](docs/RELEASE-0.4.0.md), [changelog](CHANGELOG.md), and
[release readiness](docs/G4.0-RELEASE-READINESS.md). Builds do not publish assets;
publication is a separate GitHub release step.
See [upload exclusions](docs/UPLOAD-POLICY.md) for files that must remain local.

## License and support

Apache-2.0; see [LICENSE](LICENSE). Report reproducible problems through
[GitHub Issues](https://github.com/johntsaiainow/ez8-linux-native/issues).
Zilog's proprietary tools are not redistributed. Vendor manuals are linked,
not included. This project is not affiliated with Zilog.
