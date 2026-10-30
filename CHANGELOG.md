# Changelog

## 0.4.0 — Public release

- Native eZ8 instruction subset, relocatable objects, linker, Intel HEX output,
  and strict Z8F0822 vector validation through the unified `ez8` CLI.
- Architecture-independent Debian package with Python dependency metadata,
  working `ez8` and compatibility `ez8-native` launchers, and license inclusion.
- VS Code extension with configurable `ez8.toolPath`, CLI help, active-file
  assembly, argument-safe process execution, and process error reporting.
- Wheel, source distribution, Debian package, and local VSIX download assets.

The eZ8 ISA is partial. There is no native C compiler, language server, or debug
adapter. Physical debugger/programmer Python APIs remain specialized; the unified
CLI and extension expose offline tooling only. Historical hardware validation
applies to the documented target and firmware, not all devices or workflows.

Publication status and artifact hashes are recorded separately in the release
validation report. This entry does not imply the assets have already been uploaded.
