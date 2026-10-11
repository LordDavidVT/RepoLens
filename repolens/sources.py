"""Safe remote repository access, without third-party dependencies."""

import hashlib
import ipaddress
import json
import os
import re
import socket
import subprocess
import tempfile
import threading
from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener


class RepositoryError(ValueError):
    pass


def parse_repository(value):
    value = value.strip()
    if "://" not in value:
        value = "https://" + value
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise RepositoryError(
            "Enter an HTTPS GitHub or GitLab repository link, without credentials."
        )
    if parsed.port not in (None, 443):
        raise RepositoryError("Only the standard HTTPS port is supported.")
    host = parsed.hostname.lower()
    path = parsed.path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    parts = path.split("/")
    if len(parts) < 2 or any(
        not re.fullmatch(r"[\w.-]+", p, flags=re.ASCII) or p in (".", "..") for p in parts
    ):
        raise RepositoryError(
            "Use the repository's main page, for example https://github.com/owner/repo."
        )
    if host in ("github.com", "www.github.com"):
        host = "github.com"
        if len(parts) != 2:
            raise RepositoryError(
                "Use the GitHub repository root, not a branch, file, or issue link."
            )
        provider = "github"
    else:
        # GitLab supports nested namespaces and public self-hosted instances.
        if host in ("api.github.com", "gist.github.com"):
            raise RepositoryError("Use a GitHub repository link, not an API or gist link.")
        provider = "gitlab"
    return {
        "host": host,
        "path": path,
        "name": parts[-1],
        "namespace": "/".join(parts[:-1]),
        "provider": provider,
        "url": f"https://{host}/{path}",
        "clone_url": f"https://{host}/{path}.git",
    }


def validate_public_host(host):
    try:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise RepositoryError(
            "Could not resolve the repository host. Check the link and your connection."
        ) from exc
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise RepositoryError(
            "For safety, local and private-network repository hosts are not supported."
        )


_locks = {}
_lock_guard = threading.Lock()


def _repository_lock(key):
    with _lock_guard:
        return _locks.setdefault(key, threading.Lock())


def git_environment(token, provider, askpass):
    env = os.environ.copy()
    # Ignore user/global git hooks, helpers, URL rewriting, and proxy configuration.
    for key in list(env):
        if key.startswith("GIT_"):
            del env[key]
    env.update(
        {
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_ASKPASS": str(askpass),
            "REPOLENS_TOKEN": token,
            "REPOLENS_USERNAME": "oauth2" if provider == "gitlab" else "x-access-token",
        }
    )
    return env


def run_git(args, env=None, timeout=180):
    try:
        process = subprocess.run(
            [
                "git",
                "-c",
                f"core.hooksPath={os.devnull}",
                "-c",
                "protocol.file.allow=never",
                "-c",
                "http.followRedirects=false",
                *args,
            ],
            env=env,
            capture_output=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise RepositoryError("Git is not installed. Install Git and restart RepoLens.") from exc
    except subprocess.TimeoutExpired as exc:
        raise RepositoryError(
            "The repository operation timed out. Try a smaller repository or try again later."
        ) from exc
    if process.returncode:
        # Do not surface raw stderr: remote servers may include credentials in it.
        stderr = process.stderr.decode("utf-8", "replace").lower()
        if (
            "authentication" in stderr
            or "could not read" in stderr
            or "not found" in stderr
            or "403" in stderr
        ):
            raise RepositoryError(
                "Repository not found or access denied. Check the URL and provide a read-only token if it is private."
            )
        raise RepositoryError(
            "Git could not read this repository. Check its URL, permissions, and your network connection."
        )
    return process.stdout


def read_commits(repository_path, revision="HEAD", env=None):
    raw = run_git(
        [
            "--git-dir",
            str(repository_path),
            "log",
            revision,
            "--no-show-signature",
            "--format=%H%x1f%aN%x1f%aE%x1f%cI%x1f%P%x1e",
        ],
        env=env,
    )
    commits = []
    for record in raw.decode("utf-8", "replace").split("\x1e"):
        # Generic strip() also removes ASCII unit separators, losing root commits
        # whose parent field is empty.
        fields = record.strip("\r\n").split("\x1f")
        if len(fields) != 5:
            continue
        sha, name, email, timestamp, parents = fields
        commits.append(
            {
                "sha": sha,
                "author": name or "Unknown",
                "identity": (email or name).lower(),
                "date": timestamp,
                "merge": len(parents.split()) > 1,
            }
        )
    return commits


def read_files(repository_path, revision="HEAD", env=None):
    raw = run_git(
        ["--git-dir", str(repository_path), "ls-tree", "-r", "--name-only", "-z", revision], env=env
    )
    return [name.decode("utf-8", "replace") for name in raw.split(b"\0") if name]


def fetch_metadata(repo, token):
    headers = {"User-Agent": "RepoLens/1.0", "Accept": "application/json"}
    if repo["provider"] == "github":
        url = f"https://api.github.com/repos/{quote(repo['path'], safe='/')}"
        if token:
            headers["Authorization"] = f"Bearer {token}"
    else:
        url = f"https://{repo['host']}/api/v4/projects/{quote(repo['path'], safe='')}"
        if token:
            headers["PRIVATE-TOKEN"] = token
    try:

        class NoRedirects(HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None

        with build_opener(NoRedirects).open(Request(url, headers=headers), timeout=15) as response:
            data = json.loads(response.read(2_000_000))
        if repo["provider"] == "github":
            return {
                "description": data.get("description") or "",
                "stars": data.get("stargazers_count"),
                "forks": data.get("forks_count"),
                "open_issues": data.get("open_issues_count"),
                "default_branch": data.get("default_branch"),
                "license": (data.get("license") or {}).get("spdx_id"),
            }
        return {
            "description": data.get("description") or "",
            "stars": data.get("star_count"),
            "forks": data.get("forks_count"),
            "open_issues": data.get("open_issues_count"),
            "default_branch": data.get("default_branch"),
            "license": None,
        }
    except Exception:
        return {"description": "", "metadata_unavailable": True}


def load_repository(repo, token, cache_dir, refresh, progress):
    validate_public_host(repo["host"])
    key = hashlib.sha256((repo["url"] + "\0" + token).encode()).hexdigest()
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    destination = cache_dir / key
    with (
        _repository_lock(key),
        tempfile.TemporaryDirectory(prefix="credentials-", dir=cache_dir) as credential_dir,
    ):
        askpass = Path(credential_dir) / "askpass"
        askpass.write_text(
            '#!/bin/sh\ncase "$1" in\n  *sername*) printf "%s\\n" "$REPOLENS_USERNAME" ;;\n  *) printf "%s\\n" "$REPOLENS_TOKEN" ;;\nesac\n'
        )
        askpass.chmod(0o700)
        env = git_environment(token, repo["provider"], askpass)
        revision = "HEAD"
        if not destination.exists():
            progress(
                "Downloading commit history",
                "The first analysis can take a few minutes for a large repository.",
            )
            with tempfile.TemporaryDirectory(prefix="clone-", dir=cache_dir) as staging:
                staged_repo = Path(staging) / "repository.git"
                run_git(
                    [
                        "clone",
                        "--bare",
                        "--filter=blob:none",
                        "--single-branch",
                        "--",
                        repo["clone_url"],
                        str(staged_repo),
                    ],
                    env,
                    timeout=900,
                )
                staged_repo.rename(destination)
        elif refresh:
            progress("Refreshing repository", "Checking the remote default branch for new commits.")
            # Empty repositories have no remote HEAD to fetch.
            remote_head = run_git(
                ["--git-dir", str(destination), "ls-remote", "origin", "HEAD"], env
            )
            if remote_head.strip():
                run_git(
                    [
                        "--git-dir",
                        str(destination),
                        "fetch",
                        "--filter=blob:none",
                        "origin",
                        "+HEAD:refs/heads/repolens-analysis",
                    ],
                    env,
                    timeout=900,
                )
                revision = "refs/heads/repolens-analysis"
        else:
            cached_revision = run_git(
                [
                    "--git-dir",
                    str(destination),
                    "for-each-ref",
                    "--format=%(refname)",
                    "refs/heads/repolens-analysis",
                ],
                env,
            )
            if cached_revision.strip():
                revision = "refs/heads/repolens-analysis"
        progress(
            "Building your dashboard",
            "Reading commits and the latest file tree without checking out source files.",
        )
        heads = run_git(
            ["--git-dir", str(destination), "for-each-ref", "--format=%(objectname)", "refs/heads"],
            env,
        )
        commits = read_commits(destination, revision, env) if heads.strip() else []
        files = read_files(destination, revision, env) if heads.strip() else []
        branch = (
            run_git(["--git-dir", str(destination), "symbolic-ref", "--short", "HEAD"], env)
            .decode()
            .strip()
        )
    progress(
        "Fetching repository details",
        "Adding stars, forks, and repository information where available.",
    )
    metadata = fetch_metadata(repo, token)
    if not metadata.get("default_branch"):
        metadata["default_branch"] = branch
    return commits, files, metadata
