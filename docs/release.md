# Release guide

## Source distribution

RepoLens runs directly from its source directory. There is no compiled frontend, standalone executable, wheel, container image, or hosted service in this release process.

```bash
python -B scripts/check_release.py
python -B scripts/build_release.py
```

The builder reads `VERSION`, validates included files, and writes:

```text
dist/repolens-1.0.0.zip
dist/repolens-1.0.0.zip.sha256
```

The ZIP contains a single top-level `repolens-1.0.0/` directory. Extract it and run `python app.py --open`. The checksum covers the ZIP bytes; compare it with `sha256sum` on Linux, `shasum -a 256` on macOS, or `Get-FileHash -Algorithm SHA256` in PowerShell.

Custom output directory:

```bash
python scripts/build_release.py --output dist
```

The build is standard-library-only and makes no network requests. ZIP timestamps and entry ordering are fixed for reproducibility on unchanged source. Included files follow an explicit file/directory allowlist and supported extension set; symlinks, runtime data, bytecode, developer dependencies, and caches are rejected or excluded. Unexpected files in the source tree are flagged by the hygiene checker rather than silently shipped.

## Maintainer checklist

1. Update `VERSION`, `package.json`, and `package-lock.json` together. Record user-facing changes in `CHANGELOG.md`.
2. Run the full checks in [Development](development.md), including browser tests.
3. Regenerate the synthetic screenshot if the interface changes.
4. Run the release checker and build the archive.
5. Extract the archive into a clean directory; run tests and launch the app from that copy.
6. Review included filenames, docs links, screenshot content, and checksum. Never include `.cache/`, logs, tokens, raw repository data, or personal local paths.
7. Commit only source/release documentation. `dist/` is deliberately gitignored; release ZIPs can be attached to a release later if desired.

These scripts and CI **never upload or publish**. Pushing source or publishing an archive is a separate maintainer action. There are no account names, repository-owner placeholders, personal contact addresses, funding links, or publishing credentials to configure in the source.
