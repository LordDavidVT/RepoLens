# Architecture

RepoLens intentionally avoids a framework, database, and runtime package manager.

## Components

| Component               | Responsibility                                                                                  |
| ----------------------- | ----------------------------------------------------------------------------------------------- |
| `app.py`                | Loopback HTTP server, input validation, job lifecycle, API, static routes                       |
| `repolens/sources.py`   | URL/host checks, credential helper, Git cloning/cache, commit/tree reading, provider metadata   |
| `repolens/analytics.py` | UTC normalization, filtering, zero-filled time buckets, contributors, heatmaps, file categories |
| `static/index.html`     | Semantic dashboard markup and inline SVG symbols                                                |
| `static/styles.css`     | Responsive dark theme and reduced-motion support                                                |
| `static/app.js`         | UI state, asynchronous polling, SVG charts, filters, demo data, CSV downloads                   |
| `tests/`                | Offline Python integration/unit tests and optional Chromium UI tests                            |
| `scripts/`              | Distribution checks, ZIP/checksum builds, browser lifecycle, screenshot generation              |

## Analysis flow

```text
Repository form
  → POST /api/analyze
  → background worker (maximum three)
  → validate public HTTPS host
  → repository lock → clone or refresh bare Git cache
  → git log + git ls-tree
  → optional provider metadata
  → build_report
  → browser polls job → renders dashboard

Filter change
  → POST /api/filter
  → rebuild report from retained in-memory source
  → no Git download or provider API request
```

The first clone uses `--bare --filter=blob:none --single-branch`; there is no checkout. Hosts without blob filtering can still transfer complete repository data. Refreshes fetch the remote HEAD into a dedicated local analysis reference. Cache reads handle both loose and packed references.

## State and concurrency

`JOBS` is protected by a lock. Public job responses omit internal keys such as `_source`, which contains raw commits and grouping identities. `ThreadPoolExecutor` limits analysis workers to three. Repository-specific locks prevent simultaneous writes to the same cache. Filters run in HTTP request threads and rebuild from read-only source data.

The cache key hashes repository URL plus token. In-memory source/report retention is bounded approximately by completed job count and age at new-job submission. No database persistence, cancellation endpoint, disk quota, or authentication is provided.

## Frontend

Charts are SVG, file categories use a donut, and activity uses a 7×24 CSS grid. External data is escaped before insertion into markup. Tooltips use pointer events and chart keyboard navigation. View changes reuse the current report. Demo data uses a seeded generator with a rolling 18-month span; the screenshot tool fixes time for reproducibility.

See [Local API](api.md), [Analytics definitions](analytics.md), and [Privacy](privacy.md) for the details of each boundary.
