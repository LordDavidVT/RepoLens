import hashlib
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.check_release import ROOT, png_metadata_errors, release_files, validate_tree


class ReleaseTests(unittest.TestCase):
    def test_public_tree_validates(self):
        files = validate_tree()
        self.assertTrue(files)
        self.assertIn(ROOT / "docs/images/demo-dashboard.png", files)

    def test_ignored_runtime_data_is_not_included(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "app.py").write_text("# source\n")
            (root / ".cache").mkdir()
            (root / ".cache/private-history").write_text("must not ship")
            (root / "node_modules").mkdir()
            (root / "node_modules/tool.js").write_text("must not ship")
            self.assertEqual(list(release_files(root)), [root / "app.py"])
            (root / "notes.txt").write_text("unexpected local note")
            with self.assertRaises(ValueError):
                list(release_files(root))

    def test_png_metadata_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "example.png"
            signature = b"\x89PNG\r\n\x1a\n"
            text_chunk = struct.pack(">I", 4) + b"tEXt" + b"text" + bytes(4)
            end_chunk = struct.pack(">I", 0) + b"IEND" + bytes(4)
            path.write_bytes(signature + text_chunk + end_chunk)
            self.assertIn("PNG contains text or EXIF metadata", png_metadata_errors(path))

    def test_build_is_clean_and_reproducible(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            command = [sys.executable, "-B", "scripts/build_release.py", "--output", str(output)]
            subprocess.run(command, cwd=ROOT, check=True, capture_output=True)
            version = (ROOT / "VERSION").read_text().strip()
            name = f"repolens-{version}"
            archive = output / f"{name}.zip"
            initial = archive.read_bytes()
            digest = hashlib.sha256(initial).hexdigest()
            self.assertEqual(
                (output / f"{name}.zip.sha256").read_text().strip(), f"{digest}  {name}.zip"
            )
            with zipfile.ZipFile(archive) as release:
                names = release.namelist()
                self.assertIn(f"{name}/README.md", names)
                self.assertIn(f"{name}/docs/images/demo-dashboard.png", names)
                self.assertTrue(all(item.startswith(f"{name}/") for item in names))
                self.assertFalse(
                    any(
                        ".cache/" in item or "node_modules/" in item or "__pycache__/" in item
                        for item in names
                    )
                )
            subprocess.run(command, cwd=ROOT, check=True, capture_output=True)
            self.assertEqual(initial, archive.read_bytes())


if __name__ == "__main__":
    unittest.main()
