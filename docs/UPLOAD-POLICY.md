# Files excluded from upload

Keep these local:

- Credentials and private keys: `.env*`, `.aws/`, `.ssh/`, `.npmrc`, `.pypirc`,
  PEM/key/PKCS files. Sanitized `.env.example` and `.env.sample` may be tracked.
- Local agent/editor settings: `.codex/`, `.agents/`, `.vscode/settings.json`.
- Device backups, local probe scripts, vendor PDFs/binaries, virtual environments,
  Python/Node caches and dependencies, temporary files, logs, and build outputs.

Source-control exclusions live in `.gitignore`. Archive exclusions live in
`.gitattributes` and `MANIFEST.in`. Debian packaging copies non-hidden regular
Python source modules only. VSIX packaging uses an explicit runtime/documentation
file list. Source, tests, dependency lockfiles, examples, licenses, and public
documentation remain versioned.

Generated wheel/source/DEB/VSIX files belong in reviewed GitHub **release assets**,
not Git commits. Only the four named packages, checksums, and validation report
are uploaded by the release process; never upload the whole working directory.

Ignore rules do not unpublish tracked files, alter existing tags, or remove
anything from Git history. Existing v0.4.0 assets remain unchanged. If a credential
has already been published, revoke it and handle removal from history/releases
as a separate incident; adding it to `.gitignore` is insufficient.
