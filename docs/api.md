# Local API

The API is internal to the local dashboard. It is not an authenticated public service. Requests must use the actual loopback server port; POST requests need `Content-Type: application/json`. Request bodies are limited to 16 KiB. No CORS access is granted.

## `POST /api/analyze`

Starts a background analysis. Required: `url`. Optional fields:

| Field            | Default            | Meaning                                |
| ---------------- | ------------------ | -------------------------------------- |
| `token`          | Empty              | Optional read-only provider token      |
| `refresh`        | `true`             | Refresh an existing cached repository  |
| `start`, `end`   | History boundaries | Inclusive ISO `YYYY-MM-DD` dates       |
| `granularity`    | `month`            | `day`, `week`, or `month`              |
| `exclude_merges` | `false`            | Omit commits with more than one parent |

```json
{
  "url": "https://github.com/octocat/Hello-World",
  "refresh": true,
  "granularity": "month",
  "exclude_merges": false
}
```

Returns **202** with `{"job_id": "…"}`. IDs are opaque, randomly generated values. Keep them private when they refer to private-repository reports. **429** means three analyses are already running.

## `GET /api/jobs/{job_id}`

Returns **200** with one of:

- `status: "running"`, `stage`, `detail`, and `created` (Unix seconds).
- `status: "complete"`, `report`, and job progress/creation fields.
- `status: "error"`, `error`, and job progress/creation fields.

Missing/evicted IDs return **404**. Failed background work is indicated in the JSON status, not a non-200 polling response. Internal source data and credentials are excluded.

## `POST /api/filter`

Rebuilds a report synchronously from a completed job’s retained source. Required: `job_id`; optional `start`, `end`, `granularity`, and `exclude_merges`.

```json
{
  "job_id": "…",
  "start": "2011-01-01",
  "end": "2012-12-31",
  "granularity": "month",
  "exclude_merges": true
}
```

Returns **200** with a report. It does not contact the repository provider, create another background job, or replace the original job’s report. **404** means the source expired, was evicted, or is not complete; analyze again.

## Report shape

| Key            | Contents                                                                        |
| -------------- | ------------------------------------------------------------------------------- |
| `repository`   | Parsed provider/host/path/name/URL plus available metadata                      |
| `range`        | Effective start/end, grouping, merge flag                                       |
| `history`      | Full-history first/last dates and total commits                                 |
| `stats`        | Selected totals, unique contributors, active days, average, merges, files, peak |
| `series`       | Ordered `{date, count}` buckets, including zeroes                               |
| `contributors` | Up to 50 `{name, commits, share}` rows                                          |
| `heatmap`      | Seven Monday-first rows, each with 24 UTC hour counts                           |
| `weekdays`     | Seven Monday-first totals                                                       |
| `file_types`   | Descending `{name, count}` categories                                           |
| `daily`        | Non-empty selected days as `{date, count}`                                      |
| `generated_at` | ISO UTC timestamp                                                               |
| `notes`        | Methodology explanations                                                        |

Empty repositories have null `history.first`/`history.last` and zero statistics. Unavailable metadata may be absent rather than explicitly null. Do not assume a provider API call always succeeds.

## Errors and static routes

Error bodies are `{"error": "human-readable message"}`. Common statuses: **400** invalid input/range, **403** Host/Origin rejection, **404** missing route/source, **415** incorrect media type, **429** worker capacity.

Static routes are `/`, `/app.js`, and `/styles.css`. Other filesystem paths are not served. Responses use `Cache-Control: no-store`; job IDs and browser assets should not be treated as public cacheable resources.
