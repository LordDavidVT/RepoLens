#!/usr/bin/env python3
"""Validate the public source tree and its allowlisted distribution files."""

import json
import re
import struct
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {
    "app.py",
    "README.md",
    "LICENSE",
    "VERSION",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "SUPPORT.md",
    "requirements-dev.txt",
    "pyproject.toml",
    "package.json",
    "package-lock.json",
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    ".prettierrc.json",
    ".prettierignore",
}
SOURCE_DIRS = {"repolens", "static", "tests", "scripts", "docs", ".github"}
EXTENSIONS = {".py", ".mjs", ".js", ".html", ".css", ".md", ".yml", ".yaml", ".json", ".png"}
IGNORED_DIRS = {
    ".git",
    ".cache",
    ".venv",
    "venv",
    "__pycache__",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "playwright-report",
    "test-results",
    ".idea",
    ".vscode",
}
LEAK_PATTERNS = [
    ("personal home path", re.compile(r"(?i)/(?:home|Users)/[^\s/]+/")),
    ("Windows home path", re.compile(r"(?i)[a-z]:[\\/]+Users[\\/]+[^\s\\/]+")),
    ("temporary machine path", re.compile(r"/(?:tmp|var/tmp)/[a-zA-Z0-9_.-]+")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{30,}\b")),
    ("GitLab token", re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}\b")),
    ("credential-bearing HTTPS URL", re.compile(r"https://[^\s/]+:[^\s/]+@")),
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]


def release_files(root=ROOT):
    """Yield known source files only; never follow symlinks or collect runtime state."""
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in IGNORED_DIRS for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError(f"Symlinks are not release files: {relative.as_posix()}")
        if path.is_dir():
            continue
        if len(relative.parts) == 1 and relative.name in ROOT_FILES:
            yield path
        elif relative.parts[0] in SOURCE_DIRS and path.suffix in EXTENSIONS:
            if any(part.startswith(".") for part in relative.parts[1:]):
                raise ValueError(f"Unexpected hidden file: {relative.as_posix()}")
            yield path
        else:
            raise ValueError(f"Unexpected file in source tree: {relative.as_posix()}")


def png_metadata_errors(path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return ["Invalid PNG signature"]
    errors, offset = [], 8
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        if kind in (b"tEXt", b"zTXt", b"iTXt", b"eXIf"):
            errors.append("PNG contains text or EXIF metadata")
        offset += length + 12
        if offset > len(data):
            errors.append("Truncated PNG")
            break
        if kind == b"IEND":
            if offset != len(data):
                errors.append("PNG has trailing data")
            break
    else:
        errors.append("PNG is missing its end chunk")
    return errors


def validate_tree(root=ROOT):
    files = list(release_files(root))
    errors = []
    for required in ROOT_FILES | {"docs/images/demo-dashboard.png", ".github/workflows/ci.yml"}:
        if not (root / required).is_file():
            errors.append(f"Missing release file: {required}")
    for path in files:
        relative = path.relative_to(root).as_posix()
        if path.suffix == ".png":
            errors.extend(f"{relative}: {error}" for error in png_metadata_errors(path))
            continue
        text = path.read_text(encoding="utf-8")
        for description, pattern in LEAK_PATTERNS:
            # URL-rejection tests intentionally contain fictional credentials.
            if description == "credential-bearing HTTPS URL" and relative.startswith("tests/"):
                continue
            if pattern.search(text):
                errors.append(f"{relative}: possible {description}")
        if path.suffix == ".md":
            for target in re.findall(r"\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", text):
                if ":" in target or target.startswith("#"):
                    continue
                linked = path.parent / unquote(target.split("#", 1)[0])
                if not linked.exists():
                    errors.append(f"{relative}: broken local link {target}")
    version = (root / "VERSION").read_text().strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        errors.append("VERSION must be a three-part stable semantic version")
    package = json.loads((root / "package.json").read_text())
    lock = json.loads((root / "package-lock.json").read_text())
    if (
        package["version"] != version
        or lock.get("version") != version
        or lock.get("packages", {}).get("", {}).get("version") != version
    ):
        errors.append("VERSION, package.json, and package-lock.json versions differ")
    if errors:
        raise ValueError("\n".join(errors))
    return files


def main():
    try:
        files = validate_tree()
    except (ValueError, OSError) as exc:
        print(f"Release checks failed:\n{exc}", file=sys.stderr)
        return 1
    print(
        f"Release checks passed: {len(files)} files; local links, versions, common leaks, and PNG metadata checked."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
