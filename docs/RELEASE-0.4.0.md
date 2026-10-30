# eZ8 Linux Native 0.4.0

Public release assets for Linux-native eZ8 / Z8F0822 development.
Repository: https://github.com/johntsaiainow/ez8-linux-native

## Downloads

- `ez8_linux_native-0.4.0-py3-none-any.whl`: Python installation.
- `ez8_linux_native-0.4.0.tar.gz`: Python source distribution.
- `ez8-linux-native_0.4.0_all.deb`: Debian/Ubuntu package.
- `ez8-extension-0.4.0.vsix`: VS Code extension.
- `SHA256SUMS`: SHA-256 checksums for the four packages.
- `release-validation.json`: machine-readable local artifact validation.

After downloading, verify with `sha256sum -c SHA256SUMS` from a directory
containing all four packages. Install the CLI with either the Debian package
or a wheel in a virtual environment, then install the VSIX separately.

## What is supported

Native assembly of the implemented eZ8 subset, relocatable EZO objects, linking,
Intel HEX generation, and Z8F0822 firmware/vector validation. The VS Code
extension offers CLI help and active-file assembly with a configurable tool path.
The Debian package supplies both `ez8` and compatibility `ez8-native` launchers.

The public CLI and extension are offline tools. Specialized physical Python APIs
and the historical Z8F0822 hardware evidence are not a general Flash programmer
or breakpoint debugger. Full ISA coverage, a native C compiler, and a VS Code
language server/debug adapter are outside this release.

## Validation and limits

The release build runs Python regression tests, stateful protocol tests,
Debian extraction/launcher tests, extension command-handler tests, archive
inspection, and a clean wheel installation outside the checkout. See
`release-validation.json` for asset hashes and tested Python version.

No fresh hardware validation, root-level Debian installation test, or
interactive VS Code extension-host test is claimed for this packaging release.
The declared Python minimum is 3.10; clean installs have been tested on the
locally available newer Python, not every supported minor version.

## Publication

The destination is GitHub Releases, tag `v0.4.0`, as a public non-prerelease
release. PyPI and VS Code Marketplace uploads are not included. Older RC notes
are historical; their pending-authorization status does not describe this
user-authorized public-release preparation. Publication is confirmed by the
GitHub release URL after upload, not merely by the presence of this file.
