# User guide

## Dashboard views

**Overview** presents total selected commits, all unique authors, active days, daily average, commit trends, top six authors, the weekly/hourly heatmap, and a file-type snapshot.

**Contributors** expands the ranking to at most 50 authors. Each row shows commits and percentage of selected activity; the bar is relative to the leading author. Different people with identical display names can appear as separate rows when their author identities differ.

**Activity** combines the trend chart, UTC hour/day heatmap, and weekday totals. Heatmap intensity is relative to the busiest hour/day cell in the selected period.

**File explorer** shows all file-type categories, the tracked-file total, and repository details. This is a classification of the current tree, not a directory browser or source-code viewer.

## Dates and grouping

- **All history** uses the earliest and latest default-branch commits.
- **3 months / 6 months / 1 year** end today in UTC and subtract the corresponding calendar months. Month-end dates are clamped when necessary.
- **Custom** lets you edit either endpoint. Press **Apply** to update the report; an empty endpoint uses the repository’s history boundary.
- **Monthly / Weekly / Daily** determines the time buckets. Weeks start Monday; dates are inclusive.
- Use the chart-style buttons to switch between an area and a bar chart. On narrow displays the style switch may be hidden to preserve space.
- Hover the chart for exact counts. Focus it and use left/right arrow keys to explore buckets.

An empty range is valid and shows zero commits. It does not mean the repository is empty. A range outside history with just one endpoint is normalized to an empty single-day range when the inferred endpoints would otherwise be reversed.

## Access and options

**Read-only access token** is optional for public repositories. For private repositories, use GitHub repository access with Contents read permission, or GitLab `read_repository`; GitLab `read_api` also enables private metadata. Organization SSO requirements still apply.

**Refresh cached history** fetches the current default branch when starting an analysis. Disable it to reuse the downloaded snapshot. Repository metadata is still requested from the provider API.

**Exclude merge commits** affects commit counts, contributors, averages, and activity charts. It does not change the file snapshot or full-history total.

The token field is cleared when a job is accepted. Re-enter it for a new private-repository analysis. Date/grouping changes use the existing report source and need no token or remote request.

## CSV export

The **Export data** button downloads data for the currently selected view:

| View          | Export columns                                                              |
| ------------- | --------------------------------------------------------------------------- |
| Overview      | Bucket start in UTC, count, grouping, range endpoints, merge-exclusion flag |
| Contributors  | Display name, count, share percentage; up to 50 authors                     |
| Activity      | Weekday, UTC hour, count; all 168 cells                                     |
| File explorer | File-type category, tracked-file count                                      |

Exports use quoted UTF-8 CSV, a byte-order mark for spreadsheet compatibility, and CRLF rows. Potential formula-like text is prefixed with an apostrophe. Demo exports are marked `DEMO-` in the filename. Repository/author display names may be sensitive even though email addresses are not exported.

## Demo and methodology

The initial synthetic demo can be explored without contacting a repository host. The banner, provider badge, footer, and exported filenames identify it as demo data. **How we count** opens a brief explanation of the calculations. See [Analytics definitions](analytics.md) for the complete reference.
