import http.client
import json
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import app


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_port

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, method, path, data=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        body = json.dumps(data) if data is not None else None
        connection.request(
            method, path, body, headers={"Content-Type": "application/json", **(headers or {})}
        )
        response = connection.getresponse()
        status, content_type = response.status, response.getheader("Content-Type")
        raw = response.read()
        connection.close()
        return status, json.loads(raw) if content_type.startswith("application/json") else raw

    def test_static_routes_and_path_traversal(self):
        status, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"RepoLens", body)
        self.assertEqual(self.request("GET", "/../app.py")[0], 404)

    def test_reject_cross_origin_and_invalid_host(self):
        self.assertEqual(
            self.request(
                "POST", "/api/analyze", {"url": "github.com/a/b"}, {"Origin": "https://example.com"}
            )[0],
            403,
        )
        self.assertEqual(self.request("GET", "/", headers={"Host": "evil.example"})[0], 403)
        self.assertEqual(
            self.request("POST", "/api/analyze", {}, {"Content-Type": "text/plain"})[0], 415
        )

    def test_invalid_input(self):
        self.assertEqual(
            self.request("POST", "/api/analyze", {"url": "http://github.com/a/b"})[0], 400
        )
        self.assertEqual(self.request("POST", "/api/filter", {"job_id": "nonexistent"})[0], 404)

    def test_job_and_filters_do_not_expose_source_or_token(self):
        commits = [
            {
                "sha": "first",
                "date": "2024-01-01T12:00:00+00:00",
                "author": "Ada",
                "identity": "private@example.org",
                "merge": False,
            },
            {
                "sha": "second",
                "date": "2024-02-01T12:00:00+00:00",
                "author": "Ada",
                "identity": "private@example.org",
                "merge": True,
            },
        ]
        with patch(
            "app.load_repository", return_value=(commits, ["hello.py"], {"default_branch": "main"})
        ):
            status, data = self.request(
                "POST", "/api/analyze", {"url": "https://github.com/a/b", "token": "fake-secret"}
            )
            self.assertEqual(status, 202)
            job_id = data["job_id"]
            for _ in range(100):
                status, result = self.request("GET", f"/api/jobs/{job_id}")
                if result["status"] != "running":
                    break
                time.sleep(0.01)
            self.assertEqual(result["status"], "complete")
            self.assertEqual(result["report"]["stats"]["commits"], 2)
            self.assertNotIn("_source", result)
            self.assertNotIn("private@example.org", json.dumps(result))
            self.assertNotIn("fake-secret", json.dumps(result))
            status, filtered = self.request(
                "POST",
                "/api/filter",
                {
                    "job_id": job_id,
                    "start": "2024-01-01",
                    "end": "2024-01-01",
                    "granularity": "day",
                    "exclude_merges": True,
                },
            )
            self.assertEqual(status, 200)
            self.assertEqual(filtered["stats"]["commits"], 1)
            self.assertEqual(filtered["range"]["granularity"], "day")
            self.assertEqual(
                self.request(
                    "POST",
                    "/api/filter",
                    {"job_id": job_id, "start": "2024-02-01", "end": "2024-01-01"},
                )[0],
                400,
            )
        with app.JOBS_LOCK:
            app.JOBS.pop(job_id, None)


if __name__ == "__main__":
    unittest.main()
