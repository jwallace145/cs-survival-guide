"""Tests for guide_macros.py. Run with: python -m unittest discover -s tests"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import guide_macros  # noqa: E402


def entry(name="demo", per_item=True):
    return {
        "name": name,
        "run_at": "2026-10-05T01:24:30+00:00",
        "package_version": "0.4.0",
        "environment": {
            "python_version": "3.13.16",
            "implementation": "CPython",
            "platform": "Linux-6.17.0-azure-x86_64-with-glibc2.39",
            "machine": "x86_64",
            "processor": "x86_64",
        },
        "per_item": per_item,
        "cases": [
            {
                "label": "fast",
                "status": "ok",
                "sizes": [100, 1000],
                "seconds": [2e-6, 2e-5],
                "slope": 1.0,
            },
            {
                "label": "slow",
                "status": "ok",
                "sizes": [100],
                "seconds": [5e-3],
                "slope": None,
            },
            {
                "label": "stub",
                "status": "not implemented",
                "sizes": [],
                "seconds": [],
                "slope": None,
            },
        ],
    }


def results(*entries):
    return {e["name"]: e for e in (entries or (entry(),))}


def write_results(directory, *entries, schema_version=1):
    path = Path(directory) / "benchmarks.json"
    path.write_text(
        json.dumps({"schema_version": schema_version, "benchmarks": list(entries)})
    )
    return path


class FormatSecondsTest(unittest.TestCase):
    def test_picks_a_readable_unit(self):
        self.assertEqual(guide_macros.format_seconds(2.5), "2.5 s")
        self.assertEqual(guide_macros.format_seconds(0.0123), "12.3 ms")
        self.assertEqual(guide_macros.format_seconds(2.5e-6), "2.5 µs")
        self.assertEqual(guide_macros.format_seconds(5.33e-8), "53.3 ns")


class RenderBenchmarkTest(unittest.TestCase):
    def test_total_view_has_one_row_per_size_and_a_slope_row(self):
        text = guide_macros.render_benchmark(results(), "demo", view="total")
        rows = [line for line in text.splitlines() if line.startswith("|")]

        self.assertEqual(rows[0], "| n | `fast` | `slow` | `stub` |")
        self.assertEqual(rows[1], "| ---: | ---: | ---: | ---: |")
        self.assertEqual(rows[2], "| 100 | 2 µs | 5 ms |  |")
        self.assertEqual(rows[3], "| 1,000 | 20 µs |  |  |")
        self.assertEqual(rows[4], "| **slope** | **1.00** |  | *not implemented* |")
        self.assertEqual(len(rows), 5)

    def test_per_item_view_divides_by_size_and_has_no_slope_row(self):
        text = guide_macros.render_benchmark(results(), "demo", view="per_item")
        rows = [line for line in text.splitlines() if line.startswith("|")]

        self.assertEqual(rows[2], "| 100 | 20 ns | 50 µs |  |")
        self.assertEqual(rows[3], "| 1,000 | 20 ns |  |  |")
        self.assertNotIn("slope**", text.split("<small>")[0])

    def test_both_view_puts_the_two_tables_in_tabs(self):
        text = guide_macros.render_benchmark(results(), "demo")

        self.assertIn('=== "Time per operation"', text)
        self.assertIn('=== "Total time"', text)
        self.assertIn("    | 100 | 20 ns | 50 µs |  |", text)
        self.assertIn("    | 100 | 2 µs | 5 ms |  |", text)

    def test_both_view_falls_back_to_total_without_per_item_data(self):
        text = guide_macros.render_benchmark(results(entry(per_item=False)), "demo")

        self.assertNotIn("===", text)
        self.assertIn("| 100 | 2 µs | 5 ms |  |", text)

    def test_entries_from_before_the_per_item_field_are_supported(self):
        old = entry()
        del old["per_item"]

        self.assertNotIn("===", guide_macros.render_benchmark(results(old), "demo"))

    def test_cases_selects_and_orders_columns(self):
        text = guide_macros.render_benchmark(
            results(), "demo", view="total", cases=["slow", "fast"]
        )

        self.assertIn("| n | `slow` | `fast` |", text)
        self.assertNotIn("stub", text)

    def test_caption_names_version_interpreter_machine_and_date(self):
        text = guide_macros.render_benchmark(results(), "demo")

        self.assertIn(
            "Measured on cs-survival-kit 0.4.0 · CPython 3.13.16 · "
            "Linux x86_64 · 2026-10-05.",
            text,
        )

    def test_errors_name_what_is_available(self):
        cases = [
            (dict(name="nope"), "no such benchmark (available: demo)"),
            (dict(name="demo", cases=["nope"]), "no such case(s): nope"),
            (dict(name="demo", view="chart"), "view must be one of"),
        ]
        for kwargs, message in cases:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(guide_macros.BenchmarkError) as raised:
                    guide_macros.render_benchmark(results(), **kwargs)
                self.assertIn(message, str(raised.exception))

    def test_per_item_view_is_rejected_without_per_item_data(self):
        with self.assertRaises(guide_macros.BenchmarkError):
            guide_macros.render_benchmark(
                results(entry(per_item=False)), "demo", view="per_item"
            )


class LoadResultsTest(unittest.TestCase):
    def test_indexes_entries_by_name(self):
        with tempfile.TemporaryDirectory() as directory:
            path = write_results(directory, entry("a"), entry("b"))

            self.assertEqual(sorted(guide_macros.load_results(path)), ["a", "b"])

    def test_missing_file_and_unknown_schema_are_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(guide_macros.BenchmarkError) as raised:
                guide_macros.load_results(Path(directory) / "missing.json")
            self.assertIn("not installed", str(raised.exception))

            path = write_results(directory, schema_version=99)
            with self.assertRaises(guide_macros.BenchmarkError) as raised:
                guide_macros.load_results(path)
            self.assertIn("schema_version", str(raised.exception))


class BenchmarkOrWarningTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        stderr = mock.patch("sys.stderr")
        stderr.start()
        self.addCleanup(stderr.stop)

    def test_renders_tables_when_results_exist(self):
        path = write_results(self.directory.name, entry())

        self.assertIn("| n |", guide_macros.benchmark_or_warning(path, "demo"))

    def test_unknown_benchmark_is_a_warning_box_by_default(self):
        path = write_results(self.directory.name, entry())

        with mock.patch.dict(os.environ, clear=True):
            text = guide_macros.benchmark_or_warning(path, "nope")

        self.assertTrue(text.startswith('!!! warning "Benchmark results unavailable"'))
        self.assertIn("`nope`", text)

    def test_unknown_benchmark_fails_in_strict_mode(self):
        path = write_results(self.directory.name, entry())

        with mock.patch.dict(os.environ, {guide_macros.STRICT_ENV: "1"}):
            with self.assertRaises(guide_macros.BenchmarkError):
                guide_macros.benchmark_or_warning(path, "nope")

    def test_missing_library_is_a_warning_box_even_in_strict_mode(self):
        missing = Path(self.directory.name) / "missing.json"

        with mock.patch.dict(os.environ, {guide_macros.STRICT_ENV: "1"}):
            text = guide_macros.benchmark_or_warning(missing, "demo")

        self.assertIn("not installed", text)


class DefineEnvTest(unittest.TestCase):
    def test_registers_the_benchmark_macro(self):
        registered = {}

        class Env:
            def macro(self, function):
                registered[function.__name__] = function
                return function

        guide_macros.define_env(Env())

        self.assertEqual(list(registered), ["benchmark"])


if __name__ == "__main__":
    unittest.main()
