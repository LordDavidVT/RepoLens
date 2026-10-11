# Development

## Environment

Runtime: Python 3.10+ and Git 2.27+. Optional developer tools: Python `venv`/pip and Node.js 20+ with npm. The Python project is run from source; `pyproject.toml` configures Ruff, not an installable Python distribution.

```bash
python -m venv .venv
```

Activate with `source .venv/bin/activate` on macOS/Linux, or `.venv\Scripts\Activate.ps1` in Windows PowerShell. Then install optional tools:

```bash
python -m pip install -r requirements-dev.txt
npm ci
npx playwright install chromium
```

On Linux CI, `npx playwright install --with-deps chromium` can install system browser dependencies too. The first dependency/browser install needs internet access; normal tests do not analyze remote repositories.

## Running and tests

```bash
python app.py --open
python -B -m unittest discover -s tests -v
npm run test:ui
```

Python tests cover aggregation, UTC boundaries, URL/host rejection, actual temporary Git commits including roots, server routes, filtering, and source/token non-disclosure. Browser tests start their own loopback server, exercise the synthetic demo, mock provider report responses, test exports/filters, and check mobile overflow. No token or provider account is required.

## Formatting and validation

```bash
ruff check .
ruff format --check .
npm run check:format
npm run check:js
python -B scripts/check_release.py
```

To apply formatting:

```bash
ruff check --fix .
ruff format .
npm run format
```

Ruff uses a 100-character layout target; Prettier formats JS, CSS, HTML, Markdown, JSON, and YAML. Generated caches, dependencies, and release archives are ignored. `.editorconfig` supplies editor defaults; `.gitattributes` normalizes text line endings.

## Screenshot

```bash
npm run screenshot
```

This starts an isolated local server, fixes the browser clock/locale/timezone, captures only the dashboard with synthetic data, and writes `docs/images/demo-dashboard.png`. It does not capture desktop/browser chrome, analyze a live repository, or include PNG text metadata. The process closes its browser/server automatically.

## CI

The GitHub Actions workflow runs offline Python tests on Linux/macOS/Windows with Python 3.10 and 3.14. A Linux job checks Ruff/Prettier, JavaScript syntax, release hygiene, Chromium interactions, and source-archive creation. It has read-only repository permissions and no publishing step. Optional tools’ versions are pinned in their manifests/lockfile.

For component boundaries, see [Architecture](architecture.md). Before sending changes, follow [CONTRIBUTING.md](../CONTRIBUTING.md).
