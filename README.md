# ez8-linux-toolchain — experimental native Linux tooling

Target: Zilog eZ8 / Z8F0822. This repository begins the *native* replacement path for the ZDS II tooling.

## Current status (G4.0 / Package 0.4.0)

- Pure Python, no Wine required for the native prototype.
- Two-pass assembler with a verified subset of eZ8 instructions, data directives,
  labels, register operands, conditional branches, and extended immediate forms.
- Native objects, relocations, linker, Z8F0822 vector validation, and startup code,
  with tests against Zilog reference output. The full eZ8 instruction set is not
  implemented.
- Intel HEX output with checksums, sparse address support, overlap and bounds checks.
- Unit tests and VS Code tasks.
- Smart Cable identification, target revision/status/control reads, and repeated
  8 KiB Flash capture in DEBUG mode have been exercised on hardware.
- Page-0 erase/write/read-back and reset/run/single-step have been exercised
  with the native counter example. Programming support remains limited to this
  observed workflow; no native C compiler is implemented.
- `.dw` emits big-endian data as a provisional *tool convention*; do not interpret it as verified Z8F0822 vector layout.
- **DO NOT FLASH** the data smoke sample: it is not executable firmware.
  Other generated images also require image-specific validation and a verified
  programming procedure before hardware use.

See [Flash backup](docs/hardware/flash-backup.md) and
[programming readiness](docs/hardware/programming-readiness.md) for current
hardware evidence and remaining work. The original roadmap below records the
project's development sequence; several stages now have implementations.

## Try it

```sh
cd ez8-linux-toolchain
make test
make smoke
cat build/data_smoke.hex
```

## Development roadmap

1. Acquire and verify official eZ8 instruction encoding reference, addressing modes, memory layout, and vector format.
2. Create opcode-by-opcode golden tests using Zilog `ez8asm.exe` under Wine (reference only).
3. Implement native eZ8 instruction encoder and symbolic operands.
4. Implement relocatable object representation and linker with verified Z8F0822 memory map.
5. Explore existing open-source C frontends/backends before attempting a new eZ8 C backend.
6. Independently research and test Serial SmartCable protocol / native programming.

The Zilog toolchain is not redistributed. This project is not affiliated with Zilog.


## G4.0 — Unified Linux-native CLI

G4.0 introduces the installable `ez8` command-line interface.

### Local installation

Requires Python 3.10+ and setuptools 78+ for source builds. Clean Wheel installation has been validated on Python 3.14.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
source .venv/bin/activate
ez8 --help
```

For offline development, use a locally available build backend
with `--no-index --no-build-isolation --no-deps`.

### Available commands

- `ez8 asm` — native assembler
- `ez8 object` — experimental EZO object assembler
- `ez8 link` — native linker
- `ez8 firmware` — Z8F0822 firmware builder
- `ez8 debug-mock` — mock-only debugger interface

The unified CLI does not expose physical hardware programming.

See [G4.0 CLI User Guide](docs/G4.0-CLI-USER-GUIDE.md)
and [G4.0 Release Readiness](docs/G4.0-RELEASE-READINESS.md).

### Verified engineering baseline

- 397 pytest tests passed, with 24 subtests passed.
- G3.9 three-LED sequencer was validated on physical Z8F0822 hardware.
- G4.0 installed CLI reproduced the G3.9 Intel HEX byte-for-byte.
- Full eZ8 ISA coverage and a native C compiler are not implemented.
