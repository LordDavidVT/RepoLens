# Contributing

Thank you for helping improve RepoLens. Small, focused pull requests are easier to review and maintain.

## Before starting

- Search existing issues and pull requests before opening another.
- For significant changes, first explain the problem and proposed approach in an issue.
- Follow the [code of conduct](CODE_OF_CONDUCT.md) and [coding standard](docs/coding-standard.md).
- Do not include tokens, private repository history, personal paths, or unredacted logs/screenshots.

## Development workflow

1. Fork the repository and create a descriptive branch.
2. Set up the optional tools described in [Development](docs/development.md).
3. Make a focused change and add regression tests for behavior changes.
4. Run the tests, format checks, and release checks.
5. Update documentation when behavior, configuration, or public API changes.
6. Open a pull request explaining the problem, solution, and verification. Include synthetic screenshots for visible UI changes.

Required checks:

```bash
python -B -m unittest discover -s tests -v
python -B scripts/check_release.py
ruff check .
ruff format --check .
npm run check:format
npm run check:js
npm run test:ui
```

Tests should be offline and deterministic. Do not introduce a network requirement for the default test suite. New runtime dependencies need a clear justification; preserving dependency-free startup is a project goal.

Use concise, descriptive commit messages. No particular commit-message prefix or signed-off-by convention is required. By contributing, you agree that your contributions are distributed under the project’s GNU Affero General Public License, version 3 only (`AGPL-3.0-only`), as provided in [LICENSE](LICENSE).

## Reporting bugs

Use the bug-report template. Include the application version, OS, Python/Git versions, exact steps, expected behavior, and actual behavior. Redact private data before sharing logs. Report security vulnerabilities using [SECURITY.md](SECURITY.md).
