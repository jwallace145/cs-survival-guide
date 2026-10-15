"""Tests for .github/scripts/sync-site.sh. Run with: python -m unittest discover -s tests

The script is run against a stub `aws` that records its arguments, so the
tests check which passes run and how each is configured without touching S3.
"""

import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / ".github" / "scripts" / "sync-site.sh"

STUB = """#!/usr/bin/env bash
printf '%s\\n' "$*" >> "$AWS_CALLS"
"""


class SyncSiteTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir()
        stub = bin_dir / "aws"
        stub.write_text(STUB)
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
        self.calls = self.tmp / "calls.txt"
        self.env = {
            **os.environ,
            "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
            "AWS_CALLS": str(self.calls),
        }

    def run_script(self, *args):
        return subprocess.run(
            ["bash", str(SCRIPT), *args],
            env=self.env,
            capture_output=True,
            text=True,
        )

    def recorded(self):
        return self.calls.read_text().splitlines()

    def test_runs_four_sync_passes_with_delete(self):
        result = self.run_script("site", "s3://bucket/prod", "3600")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.recorded()
        self.assertEqual(len(calls), 4)
        for call in calls:
            self.assertTrue(call.startswith("s3 sync site/ s3://bucket/prod/ --delete"))

    def test_cache_control_per_pass(self):
        self.run_script("site", "s3://bucket/prod/", "3600")
        other, bundles, indexes, html = self.recorded()
        self.assertIn("--cache-control public, max-age=3600", other)
        self.assertIn("immutable", bundles)
        self.assertIn("--include *.min.js", bundles)
        self.assertIn("--include search.json", indexes)
        self.assertIn("--include sitemap.xml", indexes)
        self.assertIn("max-age=0, must-revalidate", indexes)
        self.assertIn("--include *.html", html)
        self.assertIn("--content-type text/html; charset=utf-8", html)

    def test_default_pass_excludes_what_later_passes_own(self):
        self.run_script("site", "s3://bucket/prod", "300")
        other = self.recorded()[0]
        for pattern in ("*.html", "*.min.js", "*.min.css", "search.json", "sitemap.xml"):
            self.assertIn(f"--exclude {pattern}", other)

    def test_extra_arguments_reach_every_pass(self):
        self.run_script("site", "s3://bucket/prod", "300", "--dryrun")
        self.assertEqual(sum(call.endswith("--dryrun") for call in self.recorded()), 4)

    def test_usage_error_without_enough_arguments(self):
        result = self.run_script("site", "s3://bucket/prod")
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)
        self.assertFalse(self.calls.exists())

    def test_failure_of_a_pass_stops_the_script(self):
        failing = self.tmp / "bin" / "aws"
        failing.write_text(STUB + "exit 1\n")
        result = self.run_script("site", "s3://bucket/prod", "300")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(self.recorded()), 1)


if __name__ == "__main__":
    unittest.main()
