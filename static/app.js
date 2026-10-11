"use strict";

const $ = (id) => document.getElementById(id);
const number = new Intl.NumberFormat("en-US");
const compact = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 });
const colors = ["#a6e5b9", "#91b9e8", "#b9a0df", "#e1bd7e", "#7ecac3", "#7e8c95", "#c9a29d"];
const weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const state = {
  demo: true,
  view: "overview",
  period: "all",
  chart: "area",
  busy: false,
  jobId: null,
  report: null,
};

function escapeHtml(value) {
  return String(value ?? "").replace(
    /[&<>"']/g,
    (character) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character],
  );
}

function isoDay(date) {
  return date.toISOString().slice(0, 10);
}
function utcDate(day) {
  return new Date(`${day}T00:00:00Z`);
}
function prettyDate(day, options = {}) {
  return utcDate(day).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
    ...options,
  });
}
function bucket(day, group) {
  const date = utcDate(day);
  if (group === "month") date.setUTCDate(1);
  if (group === "week") date.setUTCDate(date.getUTCDate() - ((date.getUTCDay() + 6) % 7));
  return isoDay(date);
}
function advance(day, group) {
  const date = utcDate(day);
  if (group === "month") date.setUTCMonth(date.getUTCMonth() + 1);
  else date.setUTCDate(date.getUTCDate() + (group === "week" ? 7 : 1));
  return isoDay(date);
}

// Deliberately synthetic data for an immediately explorable, clearly labeled preview.
function makeDemo() {
  const names = [
    "Alex Morgan",
    "Sam Rivera",
    "Jamie Chen",
    "Taylor Kim",
    "Jordan Ellis",
    "Robin Patel",
    "Casey Walker",
    "Drew Park",
  ];
  const commits = [];
  const today = utcDate(isoDay(new Date()));
  const first = new Date(today);
  first.setUTCMonth(first.getUTCMonth() - 18);
  first.setUTCDate(1);
  let seed = 42;
  const random = () => {
    seed = (seed * 16807) % 2147483647;
    return seed / 2147483647;
  };
  for (let day = new Date(first); day <= today; day.setUTCDate(day.getUTCDate() + 1)) {
    const trend = 1.1 + ((day - first) / (today - first)) * 1.9;
    const count = Math.floor(random() * 5 * trend * ([0, 6].includes(day.getUTCDay()) ? 0.25 : 1));
    for (let index = 0; index < count; index++) {
      const timestamp = new Date(day);
      timestamp.setUTCHours(8 + Math.floor(random() * 13));
      commits.push({
        date: timestamp.toISOString(),
        author: names[Math.floor(random() ** 2 * names.length)],
        merge: random() < 0.13,
      });
    }
  }
  return { commits, first: isoDay(first), last: isoDay(today) };
}
const demo = makeDemo();

function demoReport(filters = {}) {
  let start = filters.start || demo.first;
  let end = filters.end || demo.last;
  if (start > end) {
    if (filters.start) end = start;
    else start = end;
  }
  const group = filters.granularity || "month";
  const selected = demo.commits.filter(
    (c) =>
      c.date.slice(0, 10) >= start &&
      c.date.slice(0, 10) <= end &&
      !(filters.exclude_merges && c.merge),
  );
  const counts = new Map(),
    authors = new Map(),
    daily = new Map();
  const heatmap = Array.from({ length: 7 }, () => Array(24).fill(0));
  for (const c of selected) {
    const day = c.date.slice(0, 10),
      key = bucket(day, group),
      time = new Date(c.date);
    counts.set(key, (counts.get(key) || 0) + 1);
    authors.set(c.author, (authors.get(c.author) || 0) + 1);
    daily.set(day, (daily.get(day) || 0) + 1);
    heatmap[(time.getUTCDay() + 6) % 7][time.getUTCHours()]++;
  }
  const series = [];
  for (let day = bucket(start, group); day <= end; day = advance(day, group))
    series.push({ date: day, count: counts.get(day) || 0 });
  return {
    repository: {
      name: "demo-project",
      namespace: "repolens",
      provider: "demo",
      url: "https://github.com",
      description:
        "A synthetic preview of your next repository deep dive. Your real data is one link away.",
      stars: null,
      forks: null,
      default_branch: "main",
      license: "Demo",
      open_issues: null,
    },
    range: { start, end, granularity: group, exclude_merges: Boolean(filters.exclude_merges) },
    history: { first: demo.first, last: demo.last, total_commits: demo.commits.length },
    stats: {
      commits: selected.length,
      contributors: authors.size,
      active_days: daily.size,
      commits_per_day:
        Math.round((selected.length / ((utcDate(end) - utcDate(start)) / 86400000 + 1)) * 10) / 10,
      merges: selected.filter((c) => c.merge).length,
      files: 428,
      peak: series.reduce((best, row) => (!best || row.count > best.count ? row : best), null),
    },
    series,
    heatmap,
    weekdays: heatmap.map((row) => row.reduce((sum, count) => sum + count, 0)),
    contributors: [...authors.entries()]
      .sort((a, b) => b[1] - a[1])
      .map(([name, commits]) => ({
        name,
        commits,
        share: Math.round((commits / selected.length) * 1000) / 10,
      })),
    file_types: [
      { name: "TypeScript", count: 189 },
      { name: "JavaScript", count: 81 },
      { name: "Stylesheets", count: 56 },
      { name: "Documentation", count: 42 },
      { name: "Configuration", count: 38 },
      { name: "Other", count: 22 },
    ],
    generated_at: new Date().toISOString(),
    notes: ["Synthetic demonstration data. Not a real repository."],
  };
}

function render(report) {
  state.report = report;
  const repo = report.repository;
  $("repo-namespace").textContent = `${repo.namespace} / `;
  $("repo-name").textContent = repo.name;
  $("repo-name").href = repo.url;
  $("repo-avatar").textContent = repo.name.slice(0, 1).toLowerCase();
  $("repo-description").textContent =
    repo.description || "Repository history, from the first commit to the latest.";
  $("provider-badge").textContent = repo.provider.toUpperCase();
  $("repo-stars").textContent = repo.stars == null ? "—" : compact.format(repo.stars);
  $("repo-forks").textContent = repo.forks == null ? "—" : compact.format(repo.forks);
  $("repo-branch").textContent = repo.default_branch || "default";
  $("stat-commits").textContent = number.format(report.stats.commits);
  $("stat-contributors").textContent = number.format(report.stats.contributors);
  $("stat-days").textContent = number.format(report.stats.active_days);
  $("stat-average").textContent = number.format(report.stats.commits_per_day);
  $("commit-caption").textContent = report.range.exclude_merges
    ? "Merge commits excluded"
    : "In the selected period";
  $("start-date").value = report.range.start;
  $("end-date").value = report.range.end;
  $("granularity").value = report.range.granularity;
  const peak = report.stats.peak;
  $("peak-caption").textContent = peak?.count
    ? `Peak: ${number.format(peak.count)} · ${prettyDate(peak.date, { day: undefined })}`
    : "No commits in this period";
  $("file-caption").textContent = `${number.format(report.stats.files)} files`;
  $("scope-note").textContent =
    `${state.demo ? "Synthetic demo" : "Default-branch history"} · ${prettyDate(report.range.start)} – ${prettyDate(report.range.end)} · UTC`;
  renderCommitChart();
  renderContributors();
  renderHeatmap();
  renderFiles();
  renderWeekdays();
  renderDetails();
  updateView();
}

function renderCommitChart() {
  const element = $("commit-chart"),
    series = state.report.series;
  if (!series.length || !state.report.stats.commits) {
    element.innerHTML =
      '<div class="empty-chart">No commits in this period.<br>Try a wider date range or include merge commits.</div>';
    return;
  }
  const width = 760,
    height = 260,
    left = 44,
    right = 14,
    top = 15,
    bottom = 33;
  const plotW = width - left - right,
    plotH = height - top - bottom;
  const maximum = series.reduce((max, row) => Math.max(max, row.count), 1);
  const magnitude = 10 ** Math.floor(Math.log10(maximum));
  const step = Math.max(1, Math.ceil(maximum / magnitude / 4) * magnitude);
  const ceiling = Math.ceil(maximum / step) * step;
  const x = (index) => left + ((index + 0.5) / series.length) * plotW;
  const y = (count) => top + plotH * (1 - count / ceiling);
  const groupingLabel = { day: "Daily", week: "Weekly", month: "Monthly" }[
    state.report.range.granularity
  ];
  let markup = `<svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" role="img" aria-label="${groupingLabel} commits, ${number.format(state.report.stats.commits)} total"><defs><linearGradient id="area-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#9fe6c0" stop-opacity=".23"/><stop offset="100%" stop-color="#9fe6c0" stop-opacity="0"/></linearGradient></defs>`;
  const gridCount = Math.min(4, ceiling);
  for (let i = 0; i <= gridCount; i++) {
    const value = Math.round((ceiling * i) / gridCount),
      py = y(value);
    markup += `<line x1="${left}" x2="${width - right}" y1="${py}" y2="${py}" class="chart-gridline"/><text x="${left - 12}" y="${py + 4}" text-anchor="end" class="chart-text">${compact.format(value)}</text>`;
  }
  if (state.chart === "area") {
    const points = series
      .map((row, index) => `${x(index).toFixed(2)},${y(row.count).toFixed(2)}`)
      .join(" L ");
    markup += `<path d="M ${x(0)},${y(0)} L ${points} L ${x(series.length - 1)},${y(0)} Z" fill="url(#area-fill)"/><path d="M ${points}" class="chart-line"/>`;
    if (series.length === 1)
      markup += `<circle cx="${x(0)}" cy="${y(series[0].count)}" r="4" fill="#9fe6c0"/>`;
  } else {
    const barWidth = Math.max(0.2, (plotW / series.length) * 0.65);
    for (let i = 0; i < series.length; i++)
      markup += `<rect x="${x(i) - barWidth / 2}" y="${y(series[i].count)}" width="${barWidth}" height="${plotH - (y(series[i].count) - top)}" rx="${Math.min(2, barWidth / 3)}" class="chart-bar"/>`;
  }
  const labelIndices = new Set([0, series.length - 1]);
  for (let i = 1; i < 6; i++) labelIndices.add(Math.floor(((series.length - 1) * i) / 6));
  for (const i of [...labelIndices].sort((a, b) => a - b)) {
    // Short series can show all labels. For long series, keep the final label clear.
    if (series.length > 7 && i !== series.length - 1 && i > series.length - 1 - series.length / 12)
      continue;
    const spansYears = series[0].date.slice(0, 4) !== series[series.length - 1].date.slice(0, 4);
    const label = prettyDate(
      series[i].date,
      state.report.range.granularity === "month" || spansYears
        ? { day: undefined, year: "2-digit" }
        : { year: undefined },
    );
    markup += `<text x="${x(i)}" y="${height - 6}" text-anchor="middle" class="chart-text">${escapeHtml(label)}</text>`;
  }
  for (let i = 0; i < series.length; i++)
    markup += `<rect x="${left + (i / series.length) * plotW}" y="${top}" width="${plotW / series.length}" height="${plotH}" class="chart-hit" data-index="${i}"><title>${escapeHtml(series[i].date)}: ${number.format(series[i].count)} commits</title></rect>`;
  element.innerHTML = markup + '</svg><div class="chart-tooltip" hidden></div>';
  element.dataset.focusIndex = "-1";
  const tooltip = element.querySelector(".chart-tooltip");
  element.addEventListener("pointermove", chartPointerMove);
  element.onpointerleave = () => {
    tooltip.hidden = true;
  };
  element.onblur = () => {
    tooltip.hidden = true;
  };
}

function chartPointerMove(event) {
  const hit = event.target.closest(".chart-hit");
  const tooltip = $("commit-chart").querySelector(".chart-tooltip");
  if (!tooltip) return;
  if (!hit) {
    tooltip.hidden = true;
    return;
  }
  const row = state.report.series[Number(hit.dataset.index)];
  tooltip.innerHTML = `${escapeHtml(prettyDate(row.date))}<strong>${number.format(row.count)} commits</strong>`;
  tooltip.hidden = false;
  const bounds = $("commit-chart").getBoundingClientRect();
  tooltip.style.left = `${Math.max(0, Math.min(event.clientX - bounds.left + 12, bounds.width - tooltip.offsetWidth))}px`;
  tooltip.style.top = `${Math.max(0, event.clientY - bounds.top - tooltip.offsetHeight - 8)}px`;
}

function renderContributors() {
  const list = state.report.contributors;
  const shown = list.slice(0, state.view === "contributors" ? 50 : 6);
  $("contributor-tag").textContent = `TOP ${shown.length}`;
  $("contributor-caption").textContent =
    state.view === "contributors"
      ? `${list.length === 50 ? "Up to 50" : list.length} authors shown · Ranked by commits`
      : "Ranked by commits";
  if (!shown.length) {
    $("contributor-list").innerHTML =
      '<div class="empty-chart">No contributors in this period.</div>';
    return;
  }
  $("contributor-list").innerHTML = shown
    .map((author) => {
      const initials = author.name
        .split(/\s+/)
        .filter(Boolean)
        .slice(0, 2)
        .map((word) => Array.from(word)[0])
        .join("")
        .toUpperCase();
      return `<div class="contributor-row"><div class="author-avatar" aria-hidden="true">${escapeHtml(initials)}</div><div class="author-info"><span class="author-name" title="${escapeHtml(author.name)}">${escapeHtml(author.name)}</span><span class="author-bar"><span data-width="${(author.commits / list[0].commits) * 100}"></span></span></div><span class="author-count">${number.format(author.commits)}<small>${author.share}%</small></span></div>`;
    })
    .join("");
  setBarWidths($("contributor-list"));
}

function setBarWidths(element) {
  element.querySelectorAll("[data-width]").forEach((bar) => {
    bar.style.width = `${bar.dataset.width}%`;
  });
}

function renderHeatmap() {
  const map = state.report.heatmap;
  const maximum = Math.max(1, ...map.flat());
  let markup = '<div class="heatmap-grid"><span></span>';
  for (let hour = 0; hour < 24; hour++)
    markup += `<span class="heat-hour">${hour % 3 === 0 ? `${String(hour).padStart(2, "0")}` : ""}</span>`;
  map.forEach((row, day) => {
    markup += `<span class="heat-label">${weekdays[day]}</span>`;
    row.forEach((count, hour) => {
      const level = count ? Math.min(4, Math.ceil(Math.sqrt(count / maximum) * 4)) : 0;
      const label = `${weekdays[day]}, ${String(hour).padStart(2, "0")}:00 UTC: ${number.format(count)} commits`;
      markup += `<div class="heat-cell level-${level}" title="${label}" role="img" aria-label="${label}"></div>`;
    });
  });
  $("heatmap").innerHTML = markup + "</div>";
}

function renderFiles() {
  const types = state.report.file_types;
  const shown = state.view === "files" ? types : types.slice(0, 5);
  const rows = [...shown];
  if (shown.length < types.length)
    rows.push({
      name: "Remaining types",
      count: types.slice(5).reduce((sum, row) => sum + row.count, 0),
    });
  const total = state.report.stats.files;
  const radius = 49,
    circumference = 2 * Math.PI * radius;
  let offset = 0;
  let markup =
    '<svg viewBox="0 0 126 126" role="img" aria-label="File type distribution"><circle cx="63" cy="63" r="49" fill="none" stroke="#28362e" stroke-width="11"/>';
  rows.forEach((row, index) => {
    const fraction = total ? row.count / total : 0;
    markup += `<circle cx="63" cy="63" r="${radius}" fill="none" stroke="${colors[index % colors.length]}" stroke-width="11" stroke-dasharray="${Math.max(0, fraction * circumference - (rows.length > 1 ? 3 : 0))} ${circumference}" stroke-dashoffset="${-offset}"><title>${escapeHtml(row.name)}: ${row.count} files</title></circle>`;
    offset += fraction * circumference;
  });
  $("file-donut").innerHTML =
    markup +
    `</svg><div class="donut-label"><strong>${number.format(total)}</strong><span>tracked files</span></div>`;
  $("file-legend").innerHTML =
    rows
      .map(
        (row, index) =>
          `<div class="file-legend-row"><span class="color-dot" data-color="${colors[index % colors.length]}"></span><span title="${escapeHtml(row.name)} · ${number.format(row.count)} files">${escapeHtml(row.name)}</span><small>${total ? ((row.count / total) * 100).toFixed(1) : 0}%</small></div>`,
      )
      .join("") || '<span class="muted">No files found</span>';
  $("file-legend")
    .querySelectorAll("[data-color]")
    .forEach((dot) => {
      dot.style.backgroundColor = dot.dataset.color;
    });
}

function renderWeekdays() {
  const maximum = Math.max(1, ...state.report.weekdays);
  $("weekday-chart").innerHTML = state.report.weekdays
    .map(
      (count, i) =>
        `<div class="weekday-row"><span>${weekdays[i]}</span><span class="author-bar"><span data-width="${(count / maximum) * 100}"></span></span><span>${number.format(count)}</span></div>`,
    )
    .join("");
  setBarWidths($("weekday-chart"));
}

function renderDetails() {
  const { repository: repo, history, stats } = state.report;
  const details = [
    ["Host", repo.provider === "demo" ? "Synthetic preview" : repo.host],
    ["Default branch", repo.default_branch || "—"],
    ["First commit", history.first ? prettyDate(history.first) : "—"],
    ["Latest commit", history.last ? prettyDate(history.last) : "—"],
    ["Full-history commits", number.format(history.total_commits)],
    ["Merge commits in period", number.format(stats.merges)],
    [
      "Open issues (GitHub includes PRs)",
      repo.open_issues == null ? "Unavailable" : number.format(repo.open_issues),
    ],
    ["License", repo.license || "Unavailable"],
    ["Analyzed at", new Date(state.report.generated_at).toLocaleString()],
  ];
  $("repository-details").innerHTML = details
    .map(([key, value]) => `<div><dt>${escapeHtml(key)}</dt><dd>${escapeHtml(value)}</dd></div>`)
    .join("");
}

function updateView() {
  const labels = {
    overview: [
      "Overview",
      "Repository insights",
      "Less guesswork. More perspective on the code you care about.",
    ],
    contributors: [
      "Contributors",
      "People behind the code",
      "Every commit has a person behind it. Meet your repository’s contributors.",
    ],
    activity: [
      "Activity",
      "Find your rhythm",
      "From quiet mornings to busy months. See when your project comes to life.",
    ],
    files: [
      "File explorer",
      "Inside the repository",
      "A snapshot of the files and technologies that make up your project.",
    ],
  };
  const [label, title, subtitle] = labels[state.view];
  $("breadcrumb-view").textContent = label;
  $("page-title").innerHTML = `${title}<span>.</span>`;
  $("page-subtitle").textContent = subtitle;
  $("dashboard").className = `view-${state.view}`;
  document.querySelectorAll(".nav-item").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === state.view);
    if (button.dataset.view === state.view) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  document.querySelectorAll("[data-panel]").forEach((panel) => {
    panel.hidden = !panel.dataset.panel.split(" ").includes(state.view);
  });
  $("view-contributors").hidden = state.view === "contributors";
}

function showError(message) {
  $("error-notice").textContent = message;
  $("error-notice").hidden = false;
}
function setBusy(busy) {
  state.busy = busy;
  $("dashboard").setAttribute("aria-busy", String(busy));
  ["analyze-button", "apply-dates", "granularity", "exclude-merges"].forEach((id) => {
    $(id).disabled = busy;
  });
  document.querySelectorAll("[data-period]").forEach((button) => {
    button.disabled = busy;
  });
  $("analyze-button").firstChild.textContent = busy ? "Analyzing…" : "Analyze repository";
}
async function request(path, options) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Something went wrong. Please try again.");
  return data;
}
function post(path, data) {
  return request(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}
const sleep = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

async function analyzeRepository(event) {
  event.preventDefault();
  if (state.busy) return;
  $("error-notice").hidden = true;
  $("progress-card").hidden = false;
  $("progress-title").textContent = "Connecting to repository";
  $("progress-detail").textContent = "Validating the link and preparing your analysis…";
  setBusy(true);
  try {
    const data = await post("/api/analyze", {
      url: $("repo-url").value.trim(),
      token: $("access-token").value.trim(),
      refresh: $("refresh-option").checked,
      exclude_merges: $("exclude-merges").checked,
      granularity: $("granularity").value,
    });
    $("access-token").value = "";
    let failures = 0;
    while (true) {
      await sleep(1000);
      let job;
      try {
        job = await request(`/api/jobs/${data.job_id}`);
        failures = 0;
      } catch (error) {
        if (++failures < 4) continue;
        throw error;
      }
      if (job.status === "error") throw new Error(job.error);
      if (job.status === "complete") {
        state.jobId = data.job_id;
        state.demo = false;
        $("demo-notice").hidden = true;
        setPeriod("all");
        render(job.report);
        notify("Your repository’s story is ready.");
        break;
      }
      $("progress-title").textContent = job.stage;
      $("progress-detail").textContent = job.detail;
    }
  } catch (error) {
    showError(
      error.message || "Could not connect to the local server. Is python app.py still running?",
    );
  } finally {
    setBusy(false);
    $("progress-card").hidden = true;
  }
}

function setPeriod(period) {
  state.period = period;
  document.querySelectorAll("[data-period]").forEach((button) => {
    button.classList.toggle("selected", button.dataset.period === period);
  });
}

function monthAgo(day, months) {
  const date = utcDate(day),
    originalDay = date.getUTCDate();
  date.setUTCDate(1);
  date.setUTCMonth(date.getUTCMonth() - months);
  const lastDay = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + 1, 0)).getUTCDate();
  date.setUTCDate(Math.min(originalDay, lastDay));
  return isoDay(date);
}

async function filterReport() {
  if (state.busy) return;
  $("error-notice").hidden = true;
  const filters = {
    start: state.period === "all" ? null : $("start-date").value || null,
    end: state.period === "all" ? null : $("end-date").value || null,
    granularity: $("granularity").value,
    exclude_merges: $("exclude-merges").checked,
  };
  if (filters.start && filters.end && filters.start > filters.end)
    return showError("The start date must be on or before the end date.");
  const rangeStart = filters.start || state.report.history.first,
    rangeEnd = filters.end || state.report.history.last;
  const days = (utcDate(rangeEnd) - utcDate(rangeStart)) / 86400000;
  if (days > 366 * 200) return showError("Choose a date range shorter than 200 years.");
  if (filters.granularity === "day" && days > 366 * 10)
    return showError("For ranges longer than 10 years, use weekly or monthly grouping.");
  setBusy(true);
  try {
    render(
      state.demo
        ? demoReport(filters)
        : await post("/api/filter", { ...filters, job_id: state.jobId }),
    );
  } catch (error) {
    showError(error.message);
  } finally {
    setBusy(false);
  }
}

let toastTimer;
function notify(message) {
  $("toast").textContent = message;
  $("toast").hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    $("toast").hidden = true;
  }, 4000);
}

function csvCell(value) {
  let text = String(value ?? "");
  // Prevent spreadsheet formulas when an author/repository name is untrusted.
  if (/^[=+@\-\t\r]/.test(text)) text = "'" + text;
  return `"${text.replace(/"/g, '""')}"`;
}
function download(name, contents, type) {
  const url = URL.createObjectURL(new Blob([contents], { type }));
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function exportData() {
  const report = state.report;
  let rows;
  if (state.view === "contributors")
    rows = [
      ["contributor", "commits", "share_percent"],
      ...report.contributors.map((row) => [row.name, row.commits, row.share]),
    ];
  else if (state.view === "files")
    rows = [["file_type", "file_count"], ...report.file_types.map((row) => [row.name, row.count])];
  else if (state.view === "activity")
    rows = [
      ["day_utc", "hour_utc", "commits"],
      ...report.heatmap.flatMap((row, day) =>
        row.map((count, hour) => [weekdays[day], hour, count]),
      ),
    ];
  else
    rows = [
      [
        "bucket_start_utc",
        "commits",
        "granularity",
        "range_start",
        "range_end",
        "merge_commits_excluded",
      ],
      ...report.series.map((row) => [
        row.date,
        row.count,
        report.range.granularity,
        report.range.start,
        report.range.end,
        report.range.exclude_merges,
      ]),
    ];
  const filename = `${state.demo ? "DEMO-" : ""}${report.repository.name}-${state.view}-${report.range.start}-${report.range.end}.csv`;
  download(
    filename,
    "\uFEFF" + rows.map((row) => row.map(csvCell).join(",")).join("\r\n"),
    "text/csv;charset=utf-8",
  );
  notify(state.demo ? "Synthetic demo data exported as CSV." : "Data exported as CSV.");
}

$("repository-form").addEventListener("submit", analyzeRepository);
$("advanced-toggle").addEventListener("click", () => {
  const expanded = $("advanced-options").hidden;
  $("advanced-options").hidden = !expanded;
  $("advanced-toggle").setAttribute("aria-expanded", String(expanded));
});
$("methodology-toggle").addEventListener("click", () => {
  const expanded = $("methodology").hidden;
  $("methodology").hidden = !expanded;
  $("methodology-toggle").setAttribute("aria-expanded", String(expanded));
});
$("dismiss-demo").addEventListener("click", () => {
  $("demo-notice").hidden = true;
});
$("export-button").addEventListener("click", exportData);
document.querySelectorAll(".nav-item").forEach((button) =>
  button.addEventListener("click", () => {
    state.view = button.dataset.view;
    render(state.report);
  }),
);
$("view-contributors").addEventListener("click", () => {
  state.view = "contributors";
  render(state.report);
});
document.querySelectorAll("[data-period]").forEach((button) =>
  button.addEventListener("click", () => {
    setPeriod(button.dataset.period);
    if (state.period === "custom") {
      $("start-date").focus();
      return;
    }
    if (state.period !== "all") {
      $("end-date").value = isoDay(new Date());
      $("start-date").value = monthAgo($("end-date").value, Number(state.period));
    }
    filterReport();
  }),
);
$("apply-dates").addEventListener("click", () => {
  setPeriod("custom");
  filterReport();
});
["start-date", "end-date"].forEach((id) =>
  $(id).addEventListener("change", () => {
    setPeriod("custom");
  }),
);
$("granularity").addEventListener("change", filterReport);
$("exclude-merges").addEventListener("change", filterReport);
function selectChart(type) {
  state.chart = type;
  ["area", "bar"].forEach((name) => {
    $(`${name}-button`).classList.toggle("selected", name === type);
    $(`${name}-button`).setAttribute("aria-pressed", String(name === type));
  });
  renderCommitChart();
}
$("area-button").addEventListener("click", () => selectChart("area"));
$("bar-button").addEventListener("click", () => selectChart("bar"));
$("commit-chart").addEventListener("keydown", (event) => {
  if (!state.report.series.length || !["ArrowLeft", "ArrowRight"].includes(event.key)) return;
  event.preventDefault();
  const element = $("commit-chart"),
    tooltip = element.querySelector(".chart-tooltip");
  if (!tooltip) return;
  const index = Math.max(
    0,
    Math.min(
      state.report.series.length - 1,
      Number(element.dataset.focusIndex || 0) + (event.key === "ArrowRight" ? 1 : -1),
    ),
  );
  element.dataset.focusIndex = index;
  const row = state.report.series[index];
  tooltip.innerHTML = `${escapeHtml(prettyDate(row.date))}<strong>${number.format(row.count)} commits</strong>`;
  tooltip.hidden = false;
  tooltip.style.left = "45px";
  tooltip.style.top = "10px";
  element.setAttribute(
    "aria-label",
    `${row.date}: ${row.count} commits. Use left and right arrow keys to explore.`,
  );
});

render(demoReport());
