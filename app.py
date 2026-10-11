#!/usr/bin/env python3
"""RepoLens local web server. Start with: python app.py"""

import argparse
import json
import secrets
import threading
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from repolens.analytics import build_report
from repolens.sources import load_repository, parse_repository

ROOT = Path(__file__).resolve().parent
JOBS = {}
JOBS_LOCK = threading.Lock()
POOL = ThreadPoolExecutor(max_workers=3)


def analyze(job_id, options):
    def progress(title, detail):
        with JOBS_LOCK:
            JOBS[job_id].update(stage=title, detail=detail)

    try:
        repo = parse_repository(options["url"])
        commits, files, metadata = load_repository(
            repo, options.get("token", ""), ROOT / ".cache", options.get("refresh", True), progress
        )
        report = build_report(
            repo,
            commits,
            files,
            metadata,
            options.get("start"),
            options.get("end"),
            options.get("granularity", "month"),
            options.get("exclude_merges", False),
        )
        with JOBS_LOCK:
            JOBS[job_id].update(
                status="complete", report=report, _source=(repo, commits, files, metadata)
            )
    except Exception as exc:
        message = (
            str(exc)
            if isinstance(exc, ValueError)
            else "Analysis failed unexpectedly. Check your connection and try again."
        )
        with JOBS_LOCK:
            JOBS[job_id].update(status="error", error=message)
    finally:
        options.pop("token", None)


def validate_options(options):
    if not isinstance(options, dict):
        raise ValueError("Expected a JSON object.")
    url = options.get("url")
    if not isinstance(url, str) or len(url) > 2048:
        raise ValueError("Enter a valid repository link.")
    parse_repository(url)
    token = options.get("token", "")
    if not isinstance(token, str) or len(token) > 2048 or any(ord(ch) < 32 for ch in token):
        raise ValueError("Invalid access token.")
    for field in ("start", "end"):
        value = options.get(field)
        if value:
            if not isinstance(value, str):
                raise ValueError("Dates must use YYYY-MM-DD.")
            date.fromisoformat(value)
    if options.get("start") and options.get("end") and options["start"] > options["end"]:
        raise ValueError("The start date must be on or before the end date.")
    if options.get("granularity", "month") not in ("day", "week", "month"):
        raise ValueError("Invalid time grouping.")
    for field in ("refresh", "exclude_merges"):
        if field in options and not isinstance(options[field], bool):
            raise ValueError(f"{field} must be a boolean.")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Only log method/path/status, never tokens or request bodies.
        if not self.path.startswith("/api/jobs/"):
            super().log_message(format, *args)

    def send_content(self, status, body, content_type="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
        )
        self.end_headers()
        self.wfile.write(body)

    def valid_host(self):
        host = self.headers.get("Host", "")
        return host in (
            f"127.0.0.1:{self.server.server_port}",
            f"localhost:{self.server.server_port}",
        )

    def do_GET(self):
        if not self.valid_host():
            return self.send_content(403, {"error": "Invalid host."})
        path = urlparse(self.path).path
        if path.startswith("/api/jobs/"):
            job_id = path.rsplit("/", 1)[-1]
            with JOBS_LOCK:
                job = JOBS.get(job_id)
                result = (
                    {key: value for key, value in job.items() if not key.startswith("_")}
                    if job
                    else None
                )
            return self.send_content(
                200 if result else 404,
                result or {"error": "Analysis not found. Please start again."},
            )
        routes = {
            "/": ("index.html", "text/html; charset=utf-8"),
            "/app.js": ("app.js", "text/javascript; charset=utf-8"),
            "/styles.css": ("styles.css", "text/css; charset=utf-8"),
        }
        if path not in routes:
            return self.send_content(404, {"error": "Not found."})
        name, kind = routes[path]
        self.send_content(200, (ROOT / "static" / name).read_bytes(), kind)

    def do_POST(self):
        if not self.valid_host():
            return self.send_content(403, {"error": "Invalid host."})
        origin = self.headers.get("Origin")
        if origin and origin not in (
            f"http://localhost:{self.server.server_port}",
            f"http://127.0.0.1:{self.server.server_port}",
        ):
            return self.send_content(403, {"error": "Cross-origin requests are not allowed."})
        if self.path not in ("/api/analyze", "/api/filter"):
            return self.send_content(404, {"error": "Not found."})
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self.send_content(415, {"error": "Use application/json."})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 16384:
                raise ValueError("Request is empty or too large.")
            options = json.loads(self.rfile.read(length))
            if self.path == "/api/analyze":
                validate_options(options)
            elif not isinstance(options, dict) or not isinstance(options.get("job_id"), str):
                raise ValueError("Provide the analysis ID to filter.")
        except (ValueError, TypeError) as exc:
            return self.send_content(400, {"error": str(exc)})
        if self.path == "/api/filter":
            with JOBS_LOCK:
                job = JOBS.get(options["job_id"])
                source = job.get("_source") if job else None
            if not source:
                return self.send_content(
                    404, {"error": "This analysis has expired. Analyze the repository again."}
                )
            try:
                validate_options({**options, "url": source[0]["url"]})
                report = build_report(
                    *source,
                    options.get("start"),
                    options.get("end"),
                    options.get("granularity", "month"),
                    options.get("exclude_merges", False),
                )
                return self.send_content(200, report)
            except (ValueError, TypeError) as exc:
                return self.send_content(400, {"error": str(exc)})
        with JOBS_LOCK:
            now = time.time()
            for key in list(JOBS):
                if JOBS[key]["status"] != "running" and now - JOBS[key]["created"] > 3600:
                    del JOBS[key]
            if sum(job["status"] == "running" for job in JOBS.values()) >= 3:
                return self.send_content(
                    429, {"error": "Three analyses are already running. Wait for one to finish."}
                )
            completed = [key for key in JOBS if JOBS[key]["status"] != "running"]
            for key in completed[:-19]:
                del JOBS[key]
            job_id = secrets.token_urlsafe(24)
            JOBS[job_id] = {
                "status": "running",
                "stage": "Connecting to repository",
                "detail": "Validating the URL and preparing the analysis.",
                "created": now,
            }
        POOL.submit(analyze, job_id, options)
        self.send_content(202, {"job_id": job_id})


def main():
    parser = argparse.ArgumentParser(
        description="RepoLens — GitHub and GitLab repository analytics"
    )
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--open", action="store_true", help="Open the dashboard in your browser")
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://localhost:{server.server_port}"
    print(f"\n  RepoLens is ready → {url}\n  Press Ctrl+C to stop.\n", flush=True)
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping RepoLens…", flush=True)
    finally:
        server.server_close()
        POOL.shutdown(wait=True)


if __name__ == "__main__":
    main()
