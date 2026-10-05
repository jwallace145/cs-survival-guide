"""Macros available to guide pages that set `render_macros: true`.

Loaded by Zensical's macros plugin (see `[project.plugins.macros]` in
zensical.toml). The one macro so far, `benchmark`, renders results that ship
inside the installed cs-survival-kit, so the numbers on a page always belong
to the library version pinned in kit-version.txt and are never typed by hand.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
RESULTS_FILE = ROOT / "lib" / "cs_survival_kit" / "_data" / "benchmarks.json"
SCHEMA_VERSION = 1
VIEWS = ("both", "total", "per_item")

# Set in CI so that, when the library is installed, a page naming a benchmark
# or case it does not have fails the build instead of publishing a warning
# box. Without the library the macro always degrades to a warning box, so the
# site still builds before a release exists or without running install-kit.sh.
STRICT_ENV = "GUIDE_BENCHMARKS_STRICT"


class BenchmarkError(Exception):
    """A page asked for benchmark results that cannot be rendered."""


def define_env(env: Any) -> None:
    """Register the guide's macros with the macros plugin."""

    @env.macro
    def benchmark(
        name: str, view: str = "both", cases: list[str] | None = None
    ) -> str:
        """Render the stored results of one benchmark as markdown tables.

        Args:
            name: The benchmark's name, such as `dynamic_array.append`.
            view: `"total"` for time per run, `"per_item"` for time divided
                by the input size, or `"both"` (the default) for the two in
                tabs. `"both"` falls back to `"total"` for a benchmark whose
                runs are not `n` operations.
            cases: Labels of the cases to show, in order. Defaults to all.
        """
        return benchmark_or_warning(RESULTS_FILE, name, view, cases)


def benchmark_or_warning(
    results_file: Path, name: str, view: str = "both", cases: list[str] | None = None
) -> str:
    """Render a benchmark, or a warning box if its results are unavailable."""
    try:
        return render_benchmark(load_results(results_file), name, view, cases)
    except BenchmarkError as error:
        if results_file.is_file() and os.environ.get(STRICT_ENV):
            raise
        print(f"warning: benchmark('{name}'): {error}", file=sys.stderr)
        return (
            '!!! warning "Benchmark results unavailable"\n\n'
            f"    `{name}`: {error}\n"
        )


def load_results(path: Path) -> dict[str, dict[str, Any]]:
    """Read a benchmarks.json file and index its entries by benchmark name."""
    if not path.is_file():
        raise BenchmarkError(
            "cs-survival-kit is not installed under lib/ (run scripts/install-kit.sh)"
        )
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema_version") != SCHEMA_VERSION:
        raise BenchmarkError(
            f"unsupported results schema_version {document.get('schema_version')!r}"
        )
    return {entry["name"]: entry for entry in document["benchmarks"]}


def render_benchmark(
    results: dict[str, dict[str, Any]],
    name: str,
    view: str = "both",
    cases: list[str] | None = None,
) -> str:
    """Render one benchmark entry as markdown."""
    if view not in VIEWS:
        raise BenchmarkError(f"view must be one of {', '.join(VIEWS)}; got {view!r}")
    if name not in results:
        available = ", ".join(sorted(results)) or "none"
        raise BenchmarkError(
            f"the installed cs-survival-kit has no such benchmark (available: {available})"
        )
    entry = results[name]
    by_label = {case["label"]: case for case in entry["cases"]}
    if cases is None:
        selected = list(entry["cases"])
    else:
        unknown = [label for label in cases if label not in by_label]
        if unknown:
            raise BenchmarkError(
                f"no such case(s): {', '.join(unknown)} "
                f"(available: {', '.join(by_label)})"
            )
        selected = [by_label[label] for label in cases]

    per_item_available = bool(entry.get("per_item"))
    if view == "per_item" and not per_item_available:
        raise BenchmarkError("this benchmark has no per-item view")

    total = _table(selected, per_item=False)
    caption = _caption(entry)
    if view == "total" or (view == "both" and not per_item_available):
        return f"{total}\n\n{caption}\n"
    per_item = _table(selected, per_item=True)
    if view == "per_item":
        return f"{per_item}\n\n{caption}\n"
    return (
        f'=== "Time per operation"\n\n{_indent(per_item)}\n\n'
        f'=== "Total time"\n\n{_indent(total)}\n\n'
        f"{caption}\n"
    )


def _table(cases: list[dict[str, Any]], *, per_item: bool) -> str:
    sizes = sorted({n for case in cases for n in case["sizes"]})
    header = ["n", *(f"`{case['label']}`" for case in cases)]
    rows = [header, ["---:"] * len(header)]
    timings = [dict(zip(case["sizes"], case["seconds"], strict=True)) for case in cases]
    for n in sizes:
        row = [f"{n:,}"]
        for times in timings:
            if n not in times:
                row.append("")
            else:
                row.append(format_seconds(times[n] / n if per_item else times[n]))
        rows.append(row)
    if not per_item:
        rows.append(["**slope**", *(_slope(case) for case in cases)])
    return "\n".join("| " + " | ".join(row) + " |" for row in rows)


def _slope(case: dict[str, Any]) -> str:
    if case["status"] != "ok":
        return f"*{case['status']}*"
    if case["slope"] is None:
        return ""
    return f"**{case['slope']:.2f}**"


def _caption(entry: dict[str, Any]) -> str:
    environment = entry.get("environment", {})
    system = environment.get("platform", "").split("-")[0]
    parts = [
        f"cs-survival-kit {entry['package_version']}",
        " ".join(
            part
            for part in (
                environment.get("implementation", ""),
                environment.get("python_version", ""),
            )
            if part
        ),
        " ".join(part for part in (system, environment.get("machine", "")) if part),
        entry["run_at"][:10],
    ]
    measured = " · ".join(part for part in parts if part)
    return (
        f"<small>Measured on {measured}. Each time is the best of five runs. "
        "The slope is fitted on a log-log scale: about 1 is linear, "
        "about 2 is quadratic.</small>"
    )


def format_seconds(seconds: float) -> str:
    """Format a duration with a unit that keeps it readable."""
    for unit, scale in (("s", 1.0), ("ms", 1e-3), ("µs", 1e-6)):
        if seconds >= scale:
            return f"{seconds / scale:.3g} {unit}"
    return f"{seconds / 1e-9:.3g} ns"


def _indent(text: str) -> str:
    return "\n".join(f"    {line}" if line else "" for line in text.splitlines())
