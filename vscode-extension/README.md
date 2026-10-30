# EZ8 Linux Toolchain

Public release **0.4.0** for Linux-native eZ8/Z8F0822 assembly.
Extension identifier: `ai-now.ez8-extension`. Requires VS Code `^1.80.0`.

## Install

Download the VSIX from [GitHub Releases](https://github.com/johntsaiainow/ez8-linux-native/releases/tag/v0.4.0):

```sh
code --install-extension ./ez8-extension-0.4.0.vsix
```

Alternatively, use **Extensions: Install from VSIX...**. The CLI must be
installed separately using the Debian package or Python wheel. Marketplace
publication is not part of this GitHub release.

## Commands

- **EZ8: Run Native Tool** runs `ez8 --help`.
- **EZ8: Assemble Active File** saves a modified local file, asks where to write
  Intel HEX, and runs `ez8 asm INPUT -o OUTPUT`.

Output and process errors appear in **EZ8 Native Output**. The workspace must
be trusted. Paths are passed as separate process arguments without a shell.
This command handles a single assembly file; relocatable multi-file firmware
builds use the CLI's object/link/firmware commands.

## Configuration

`ez8.toolPath` defaults to `ez8` on PATH. For a virtual environment:

```json
{
  "ez8.toolPath": "/absolute/path/to/project/.venv/bin/ez8"
}
```

Do not put additional arguments in this setting. Missing executables are
reported with guidance to install the CLI or change the setting. The extension
provides no language server, syntax grammar, debug adapter, or hardware commands.

## Development

Use Node.js 24 and npm. In this directory:

```sh
npm ci --ignore-scripts
npm test
npm run watch
```

`npm test` compiles TypeScript and exercises the command handlers with mocked
VS Code APIs and process spawning. It is not an interactive extension-host test.
To open a development window, run from the repository root:

```sh
code --extensionDevelopmentPath="$PWD/vscode-extension" .
```

Build all release packages with `bash tools/build-release.sh` from the repository
root (or `bash vscode-extension/build-all.sh`). The packager excludes node_modules,
source maps, tests, and previous VSIX files, and includes README and Apache-2.0
LICENSE. Packaging uses Microsoft's [vsce tool](https://code.visualstudio.com/api/working-with-extensions/publishing-extension).
