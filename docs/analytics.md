# Analytics definitions

## History scope

Git reads every commit reachable from the analyzed default branch. That includes root commits and commits brought in by merges, but not unmerged branches, unrelated branches, tags alone, or deleted unreachable history. A refresh follows the remote’s current default branch; a non-refresh analysis uses the last cached revision.

This is not an all-branches audit, a provider contribution-calendar replica, or a measure of code quality/productivity. Commits alone do not describe review effort, complexity, or impact.

## Time and filters

- Commit timestamps use **committer dates**, not author dates, normalized to **UTC**.
- Start/end dates are inclusive calendar days.
- Monthly buckets start on the first of a month; weekly buckets start Monday; daily buckets start at UTC midnight.
- The first/last bucket may be partial. Its count includes only commits inside the requested range.
- Quiet buckets are retained with zero counts.
- Merge exclusion removes commits with more than one parent, not the non-merge commits brought in by that merge.
- The full-history count and history boundaries are independent of date/merge filters.

Daily grouping accepts at most `366 × 10` days. Any grouping accepts at most `366 × 200` days. These are practical chart-size guards, not promises of unlimited memory or repository size.

## Statistics

| Statistic     | Definition                                                         |
| ------------- | ------------------------------------------------------------------ |
| Total commits | Number of selected reachable commits after filters                 |
| Contributors  | Unique author identities in the selected commits                   |
| Active days   | Number of UTC days with one or more selected commits               |
| Daily average | Selected commits / inclusive calendar days, rounded to one decimal |
| Merge commits | Selected commits with two or more parents                          |
| Peak bucket   | Highest-count bucket; ties use the first bucket chronologically    |

Contributor identities use lowercased author email, or author name if email is empty. Git’s `%aN`/`%aE` mailmap behavior is applied where available. The most recently seen display name is shown for an identity. Only names/counts/shares reach the dashboard; raw identity emails remain server-side. Contributor rows are limited to the top 50, but the statistic counts every identity.

## Activity

Heatmap cells aggregate selected commits by Monday-through-Sunday and UTC hour. Weekday totals sum across each row. Heatmap colors use relative, square-root-scaled intensity, so colors are not comparable across different selected periods.

## File types

File types classify the latest analyzed tracked-file tree by extension. Related extensions share a category; documentation and configuration files have explicit categories; unknown/no-extension files are Other. A tracked Git submodule tree entry can also be counted as an entry. Categories do not measure bytes or lines of code and are not historical snapshots of the chosen dates.

## Provider metadata

GitHub/GitLab APIs supply description, stars, forks, default-branch name, and issue count where available. GitHub may also supply a license identifier; GitLab license is currently unavailable. GitHub’s issue count includes pull requests. Metadata errors, permission gaps, or API rate limits leave unavailable values blank/marked unavailable without preventing Git-based charts.
