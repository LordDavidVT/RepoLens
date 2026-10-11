"""Deterministic UTC commit-history aggregation."""

from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import PurePosixPath

FILE_TYPES = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".c": "C / C++",
    ".h": "C / C++",
    ".cpp": "C / C++",
    ".hpp": "C / C++",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".html": "HTML",
    ".css": "Stylesheets",
    ".scss": "Stylesheets",
    ".sass": "Stylesheets",
    ".md": "Documentation",
    ".rst": "Documentation",
    ".txt": "Documentation",
    ".json": "Configuration",
    ".yaml": "Configuration",
    ".yml": "Configuration",
    ".toml": "Configuration",
    ".xml": "Configuration",
    ".sh": "Shell",
    ".bash": "Shell",
    ".sql": "SQL",
}


def bucket_start(day, granularity):
    if granularity == "month":
        return day.replace(day=1)
    if granularity == "week":
        return day - timedelta(days=day.weekday())
    return day


def next_bucket(day, granularity):
    if granularity == "month":
        return date(day.year + (day.month == 12), day.month % 12 + 1, 1)
    return day + timedelta(days=7 if granularity == "week" else 1)


def build_report(
    repo, commits, files, metadata, start=None, end=None, granularity="month", exclude_merges=False
):
    if granularity not in ("day", "week", "month"):
        raise ValueError("Choose daily, weekly, or monthly grouping.")
    start_date = date.fromisoformat(start) if start else None
    end_date = date.fromisoformat(end) if end else None
    if start_date and end_date and start_date > end_date:
        raise ValueError("The start date must be on or before the end date.")
    parsed = [
        (commit, datetime.fromisoformat(commit["date"]).astimezone(timezone.utc))
        for commit in commits
    ]
    parsed.sort(key=lambda entry: entry[1])
    today = datetime.now(timezone.utc).date()
    earliest = parsed[0][1].date() if parsed else today
    latest = parsed[-1][1].date() if parsed else today
    lower, upper = start_date or earliest, end_date or latest
    # A range entirely outside repository history is a valid, empty result.
    if lower > upper:
        if start_date:
            upper = lower
        else:
            lower = upper
    if (upper - lower).days > 366 * 200:
        raise ValueError("Please choose a date range shorter than 200 years.")
    if granularity == "day" and (upper - lower).days > 366 * 10:
        raise ValueError("For ranges longer than 10 years, use weekly or monthly grouping.")
    selected = [
        (c, dt)
        for c, dt in parsed
        if lower <= dt.date() <= upper and not (exclude_merges and c["merge"])
    ]
    bucket_counts = Counter(bucket_start(dt.date(), granularity) for _, dt in selected)
    series = []
    current = bucket_start(lower, granularity)
    while current <= upper:
        series.append({"date": current.isoformat(), "count": bucket_counts[current]})
        current = next_bucket(current, granularity)
    author_counts = Counter(c["identity"] for c, _ in selected)
    names = {c["identity"]: c["author"] for c, _ in selected}
    contributors = [
        {"name": names[key], "commits": count, "share": round(count / len(selected) * 100, 1)}
        for key, count in author_counts.most_common(50)
    ]
    heatmap = [[0] * 24 for _ in range(7)]
    weekdays = [0] * 7
    for _, timestamp in selected:
        heatmap[timestamp.weekday()][timestamp.hour] += 1
        weekdays[timestamp.weekday()] += 1
    daily = Counter(dt.date().isoformat() for _, dt in selected)
    file_types = Counter(
        FILE_TYPES.get(PurePosixPath(path).suffix.lower(), "Other") for path in files
    )
    file_type_rows = [{"name": name, "count": count} for name, count in file_types.most_common()]
    peak = max(series, key=lambda entry: entry["count"]) if series else None
    total = len(selected)
    return {
        "repository": {**repo, **metadata},
        "range": {
            "start": lower.isoformat(),
            "end": upper.isoformat(),
            "granularity": granularity,
            "exclude_merges": exclude_merges,
        },
        "history": {
            "first": earliest.isoformat() if parsed else None,
            "last": latest.isoformat() if parsed else None,
            "total_commits": len(commits),
        },
        "stats": {
            "commits": total,
            "contributors": len(author_counts),
            "active_days": len(daily),
            "commits_per_day": round(total / ((upper - lower).days + 1), 1),
            "merges": sum(c["merge"] for c, _ in selected),
            "files": len(files),
            "peak": peak,
        },
        "series": series,
        "contributors": contributors,
        "heatmap": heatmap,
        "weekdays": weekdays,
        "file_types": file_type_rows,
        "daily": [{"date": day, "count": count} for day, count in sorted(daily.items())],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "notes": [
            "Commit dates use committer timestamps, converted to UTC. Date endpoints are inclusive.",
            "History includes all commits reachable from the default branch, including merged branches.",
            "File types count tracked files at the latest analyzed revision, not lines of code or historical files.",
        ],
    }
