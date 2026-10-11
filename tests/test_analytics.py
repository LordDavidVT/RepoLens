import unittest
from datetime import date

from repolens.analytics import bucket_start, build_report

REPO = {"url": "https://github.com/test/example", "name": "example"}


def commit(day, name="Ada", email="ada@example.org", merge=False):
    return {"sha": "abc", "date": day, "author": name, "identity": email, "merge": merge}


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.commits = [
            commit("2024-01-01T10:00:00+00:00"),
            commit("2024-01-31T23:00:00-02:00"),
            commit("2024-03-03T12:00:00+00:00", "Grace", "grace@example.org", True),
        ]

    def report(self, **kwargs):
        return build_report(
            REPO, self.commits, ["main.py", "test.py", "README.md", "image.png"], {}, **kwargs
        )

    def test_full_monthly_history(self):
        result = self.report()
        self.assertEqual(
            result["series"],
            [
                {"date": "2024-01-01", "count": 1},
                {"date": "2024-02-01", "count": 1},
                {"date": "2024-03-01", "count": 1},
            ],
        )
        self.assertEqual(result["stats"]["contributors"], 2)
        self.assertEqual(result["stats"]["files"], 4)
        self.assertEqual(result["stats"]["merges"], 1)
        self.assertEqual(result["file_types"][0], {"name": "Python", "count": 2})

    def test_inclusive_dates_and_utc(self):
        result = self.report(start="2024-02-01", end="2024-02-01", granularity="day")
        self.assertEqual(result["stats"]["commits"], 1)
        self.assertEqual(result["heatmap"][3][1], 1)
        self.assertEqual(result["stats"]["commits_per_day"], 1)

    def test_zero_buckets(self):
        result = self.report(start="2024-04-01", end="2024-06-30")
        self.assertEqual([row["count"] for row in result["series"]], [0, 0, 0])
        self.assertEqual(result["stats"]["contributors"], 0)

    def test_exclude_merge(self):
        result = self.report(exclude_merges=True)
        self.assertEqual(result["stats"]["commits"], 2)
        self.assertEqual(result["stats"]["merges"], 0)

    def test_week_starts_monday(self):
        self.assertEqual(bucket_start(date(2024, 1, 7), "week"), date(2024, 1, 1))
        result = self.report(start="2024-01-01", end="2024-01-14", granularity="week")
        self.assertEqual([row["count"] for row in result["series"]], [1, 0])

    def test_invalid_range_and_granularity(self):
        with self.assertRaises(ValueError):
            self.report(start="2024-02-01", end="2024-01-01")
        with self.assertRaises(ValueError):
            self.report(granularity="year")
        with self.assertRaises(ValueError):
            self.report(start="2000-01-01", end="2024-01-01", granularity="day")

    def test_empty_repository(self):
        result = build_report(REPO, [], [], {}, start="2024-01-01", end="2024-01-31")
        self.assertEqual(result["stats"]["commits"], 0)
        self.assertIsNone(result["history"]["first"])

    def test_no_email_addresses_exposed(self):
        result = self.report()
        self.assertNotIn("identity", result["contributors"][0])
        self.assertNotIn("email", result["contributors"][0])


if __name__ == "__main__":
    unittest.main()
