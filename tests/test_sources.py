import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import validate_options
from repolens.sources import (
    RepositoryError,
    parse_repository,
    read_commits,
    read_files,
    validate_public_host,
)


class SourceTests(unittest.TestCase):
    def test_github_url(self):
        result = parse_repository(" github.com/octocat/Hello-World.git ")
        self.assertEqual(result["provider"], "github")
        self.assertEqual(result["clone_url"], "https://github.com/octocat/Hello-World.git")

    def test_nested_gitlab(self):
        result = parse_repository("https://gitlab.com/team/subgroup/project/")
        self.assertEqual(result["namespace"], "team/subgroup")
        self.assertEqual(result["provider"], "gitlab")

    def test_public_self_hosted_gitlab(self):
        self.assertEqual(
            parse_repository("https://git.example.org/group/project")["host"], "git.example.org"
        )

    def test_reject_invalid_urls(self):
        for url in [
            "http://github.com/a/b",
            "https://user:secret@github.com/a/b",
            "https://github.com/a/b/tree/main",
            "https://github.com/a",
            "https://github.com/a/../b",
            "https://github.com:8888/a/b",
            "file:///example/repository",
        ]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                parse_repository(url)

    def test_reject_private_hosts(self):
        with patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("127.0.0.1", 443))]):
            with self.assertRaises(RepositoryError):
                validate_public_host("localhost")

    def test_validate_payload(self):
        validate_options({"url": "https://github.com/a/b", "start": "2024-01-01"})
        for payload in [
            [],
            {"url": 3},
            {"url": "github.com/a/b", "token": "bad\nheader"},
            {"url": "github.com/a/b", "refresh": "yes"},
            {"url": "github.com/a/b", "start": 123},
        ]:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                validate_options(payload)

    def test_git_reads_root_and_unicode_commits(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            env = os.environ.copy()
            env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})
            env.update(
                {
                    "GIT_AUTHOR_NAME": "Zoë Chen",
                    "GIT_AUTHOR_EMAIL": "zoe@example.org",
                    "GIT_COMMITTER_NAME": "Zoë Chen",
                    "GIT_COMMITTER_EMAIL": "zoe@example.org",
                    "GIT_AUTHOR_DATE": "2024-01-01T12:00:00+00:00",
                    "GIT_COMMITTER_DATE": "2024-01-01T12:00:00+00:00",
                }
            )

            def git(*args):
                return subprocess.run(
                    ["git", "-c", f"core.hooksPath={os.devnull}", *args],
                    cwd=repo,
                    env=env,
                    check=True,
                    capture_output=True,
                )

            git("init", "--initial-branch=main")
            (repo / "hello.py").write_text("print('hello')\n")
            git("add", "hello.py")
            git("commit", "-m", "Root commit")
            git("commit", "--allow-empty", "-m", "Second commit")
            commits = read_commits(repo / ".git")
            self.assertEqual(len(commits), 2)
            self.assertEqual(commits[0]["author"], "Zoë Chen")
            self.assertFalse(commits[1]["merge"])
            self.assertEqual(read_files(repo / ".git"), ["hello.py"])


if __name__ == "__main__":
    unittest.main()
