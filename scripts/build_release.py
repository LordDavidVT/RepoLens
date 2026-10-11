#!/usr/bin/env python3
"""Create a clean, reproducible source ZIP and checksum; never publish it."""

import argparse
import hashlib
import zipfile
from pathlib import Path

from check_release import ROOT, validate_tree


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "dist", help="Output directory (default: dist)"
    )
    args = parser.parse_args()
    files = validate_tree()
    version = (ROOT / "VERSION").read_text().strip()
    name = f"repolens-{version}"
    args.output.mkdir(parents=True, exist_ok=True)
    archive = args.output / f"{name}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for path in files:
            entry = zipfile.ZipInfo(
                f"{name}/{path.relative_to(ROOT).as_posix()}", date_time=(2026, 1, 1, 0, 0, 0)
            )
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            output.writestr(entry, path.read_bytes())
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(".zip.sha256").write_text(f"{checksum}  {archive.name}\n", encoding="ascii")
    print(
        f"Built {archive.name}: {len(files)} files. SHA-256 checksum written. Nothing was uploaded."
    )


if __name__ == "__main__":
    main()
