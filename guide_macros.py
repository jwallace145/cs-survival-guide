"""Macros available to guide pages that set `render_macros: true`.

Loaded by Zensical's macros plugin (see `[project.plugins.macros]` in
zensical.toml). The one macro so far, `benchmark`, renders results that ship
inside the installed cs-survival-kit, so the numbers on a page always belong
to the library version pinned in kit-version.txt and are never typed by hand.
"""

from __future__ import annotations

import html
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
RESULTS_FILE = ROOT / "lib" / "cs_survival_kit" / "_data" / "benchmarks.json"
SCHEMA_VERSION = 1
VIEWS = ("both", "total", "per_item")

# A chart tells its series apart by colour and marker shape. The four colours
# in docs/stylesheets/benchmarks.css were measured as a set, every pair, for
# colour-blind and normal vision on both the light and dark page backgrounds.
# That is why a chart is limited to four cases: no fifth colour passes.
MAX_CHART_CASES = 4
MARKERS = (
    "M-4.5,0a4.5,4.5 0 1,0 9,0a4.5,4.5 0 1,0 -9,0Z",  # circle
    "M-4,-4H4V4H-4Z",  # square
    "M0,-5.2L5,3.8H-5Z",  # triangle
    "M0,-5.4L5.4,0L0,5.4L-5.4,0Z",  # diamond
)

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
        name: str,
        view: str = "both",
        cases: list[str] | None = None,
        chart: bool = True,
    ) -> str:
        """Render the stored results of one benchmark as charts and tables.

        Args:
            name: The benchmark's name, such as `dynamic_array.append`.
            view: `"total"` for time per run, `"per_item"` for time divided
                by the input size, or `"both"` (the default) for the two in
                tabs. `"both"` falls back to `"total"` for a benchmark whose
                runs are not `n` operations.
            cases: Labels of the cases to show, in order. Defaults to all.
            chart: Draw a log-log line chart above each table. A chart shows
                at most four cases; pass `cases` to choose them, or
                `chart=False` for tables only.
        """
        return benchmark_or_warning(RESULTS_FILE, name, view, cases, chart)


def benchmark_or_warning(
    results_file: Path,
    name: str,
    view: str = "both",
    cases: list[str] | None = None,
    chart: bool = True,
) -> str:
    """Render a benchmark, or a warning box if its results are unavailable."""
    try:
        return render_benchmark(load_results(results_file), name, view, cases, chart)
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
    chart: bool = True,
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

    if chart and len(selected) > MAX_CHART_CASES:
        raise BenchmarkError(
            f"a chart shows at most {MAX_CHART_CASES} cases and this has "
            f"{len(selected)}; choose some with cases=[...] or pass chart=False"
        )

    def section(per_item: bool) -> str:
        table = _table(selected, per_item=per_item)
        if not chart:
            return table
        return f"{render_chart(entry, selected, per_item=per_item)}\n\n{table}"

    total = section(per_item=False)
    caption = _caption(entry)
    if view == "total" or (view == "both" and not per_item_available):
        return f"{total}\n\n{caption}\n"
    per_item = section(per_item=True)
    if view == "per_item":
        return f"{per_item}\n\n{caption}\n"
    return (
        f'=== "Time per operation"\n\n{_indent(per_item)}\n\n'
        f'=== "Total time"\n\n{_indent(total)}\n\n'
        f"{caption}\n"
    )


def _table(cases: list[dict[str, Any]], *, per_item: bool) -> str:
    sizes = sorted({n for case in cases for n in case["sizes"]})
    header = ["n", *(_header_label(case["label"]) for case in cases)]
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


def _header_label(label: str) -> str:
    """Format a case label for a table header.

    A long label such as `DynamicArray(geometric(1.5))` may wrap, but only
    after its first opening parenthesis, never in the middle of a word.
    """
    text = html.escape(label).replace("|", "&#124;")
    return f"<code>{text.replace('(', '(<wbr>', 1)}</code>"


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
        "about 2 is quadratic. Both chart axes are logarithmic, so a power "
        "law is a straight line and its steepness is that slope.</small>"
    )


def format_seconds(seconds: float) -> str:
    """Format a duration with a unit that keeps it readable."""
    for unit, scale in (("s", 1.0), ("ms", 1e-3), ("µs", 1e-6)):
        if seconds >= scale:
            return f"{seconds / scale:.3g} {unit}"
    return f"{seconds / 1e-9:.3g} ns"


def _indent(text: str) -> str:
    return "\n".join(f"    {line}" if line else "" for line in text.splitlines())


# --- Charts ---------------------------------------------------------------------
#
# Charts are inline SVG generated at build time: no JavaScript and no chart
# library. Colours come from CSS custom properties in
# docs/stylesheets/benchmarks.css so they follow the site's light/dark theme.

CHART_WIDTH, CHART_HEIGHT = 720, 380
MARGIN_LEFT, MARGIN_RIGHT, MARGIN_TOP, MARGIN_BOTTOM = 76, 22, 14, 48


def render_chart(
    entry: dict[str, Any], cases: list[dict[str, Any]], *, per_item: bool
) -> str:
    """Draw time against input size for each case as a log-log line chart.

    Returns a single line of HTML (a legend and an SVG) so that it survives
    being indented inside a content tab.
    """
    all_labels = [case["label"] for case in entry["cases"]]
    series: list[tuple[int, str, list[tuple[int, float]]]] = []
    for position, case in enumerate(cases):
        # Colour follows the case, not its position among the selected cases,
        # whenever the benchmark has few enough cases to give each its own.
        slot = all_labels.index(case["label"]) if len(all_labels) <= 4 else position
        points = [
            (n, seconds / n if per_item else seconds)
            for n, seconds in zip(case["sizes"], case["seconds"], strict=True)
            if seconds > 0
        ]
        if points:
            series.append((slot, case["label"], points))
    if not series:
        return ""

    sizes = [n for _, _, points in series for n, _ in points]
    values = [value for _, _, points in series for _, value in points]
    x_low, x_high = math.log10(min(sizes)), math.log10(max(sizes))
    x_pad = max((x_high - x_low) * 0.03, 0.02)
    x_low, x_high = x_low - x_pad, x_high + x_pad
    y_low, y_high = math.log10(nice_floor(min(values))), math.log10(nice_ceil(max(values)))
    if y_high - y_low < 1e-9:
        y_low, y_high = y_low - 0.3, y_high + 0.3

    plot_width = CHART_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
    plot_height = CHART_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
    bottom = MARGIN_TOP + plot_height

    def x_of(n: float) -> float:
        return MARGIN_LEFT + (math.log10(n) - x_low) / (x_high - x_low) * plot_width

    def y_of(value: float) -> float:
        return bottom - (math.log10(value) - y_low) / (y_high - y_low) * plot_height

    what = "time per operation" if per_item else "total time"
    parts = [
        f'<svg class="bm-plot" viewBox="0 0 {CHART_WIDTH} {CHART_HEIGHT}" role="img" '
        f'aria-label="{html.escape(_describe(entry, series, what))}">'
    ]
    for tick in log_ticks(10**y_low, 10**y_high):
        y = y_of(tick)
        parts.append(
            f'<line class="bm-grid" x1="{MARGIN_LEFT}" x2="{CHART_WIDTH - MARGIN_RIGHT}" '
            f'y1="{y:.1f}" y2="{y:.1f}"/>'
            f'<text class="bm-tick" x="{MARGIN_LEFT - 8}" y="{y:.1f}" dy="0.32em" '
            f'text-anchor="end">{html.escape(format_seconds(tick))}</text>'
        )
    parts.append(
        f'<line class="bm-axis" x1="{MARGIN_LEFT}" x2="{CHART_WIDTH - MARGIN_RIGHT}" '
        f'y1="{bottom}" y2="{bottom}"/>'
    )
    for tick in log_ticks(min(sizes), max(sizes)):
        x = x_of(tick)
        parts.append(
            f'<line class="bm-axis" x1="{x:.1f}" x2="{x:.1f}" y1="{bottom}" y2="{bottom + 5}"/>'
            f'<text class="bm-tick" x="{x:.1f}" y="{bottom + 20}" text-anchor="middle">'
            f"{format_count(tick)}</text>"
        )
    parts.append(
        f'<text class="bm-title" x="{MARGIN_LEFT + plot_width / 2:.0f}" '
        f'y="{CHART_HEIGHT - 6}" text-anchor="middle">n, the input size (log scale)</text>'
        f'<text class="bm-title" transform="translate(14 {MARGIN_TOP + plot_height / 2:.0f}) '
        f'rotate(-90)" text-anchor="middle">{what} (log scale)</text>'
    )
    for slot, _, points in series:
        if len(points) > 1:
            path = " ".join(f"{x_of(n):.1f},{y_of(value):.1f}" for n, value in points)
            parts.append(f'<polyline class="bm-line bm-s{slot}" points="{path}"/>')
    # Markers go on top of every line so a crossing never hides a point.
    for slot, label, points in series:
        for n, value in points:
            tooltip = html.escape(f"{label}, n = {n:,}: {format_seconds(value)}")
            parts.append(
                f'<g class="bm-point bm-s{slot}" transform="translate({x_of(n):.1f} '
                f'{y_of(value):.1f})"><title>{tooltip}</title>'
                f'<circle class="bm-hit" r="13"/><path class="bm-marker" d="{MARKERS[slot]}"/></g>'
            )
    parts.append("</svg>")

    legend = "".join(
        f'<span class="bm-key bm-s{slot}"><svg viewBox="-16 -7 32 14" width="32" height="14" '
        f'aria-hidden="true"><line class="bm-line" x1="-15" x2="15" y1="0" y2="0"/>'
        f'<path class="bm-marker" d="{MARKERS[slot]}"/></svg>'
        f"<code>{html.escape(label)}</code></span>"
        for slot, label, _ in series
    )
    return (
        f'<figure class="bm-chart"><div class="bm-legend">{legend}</div>{"".join(parts)}</figure>'
    )


def _describe(
    entry: dict[str, Any], series: list[tuple[int, str, list[tuple[int, float]]]], what: str
) -> str:
    labels = ", ".join(label for _, label, _ in series)
    return (
        f"Line chart of {what} against input size for the {entry['name']} "
        f"benchmark, on logarithmic axes. Series: {labels}. "
        "The table below has the same values."
    )


def nice_floor(value: float) -> float:
    """Return the largest of 1, 2, 5 times a power of ten that is <= value."""
    exponent = math.floor(math.log10(value))
    for step in (5, 2, 1):
        candidate = step * 10.0**exponent
        if candidate <= value * (1 + 1e-9):
            return candidate
    return 10.0**exponent


def nice_ceil(value: float) -> float:
    """Return the smallest of 1, 2, 5 times a power of ten that is >= value."""
    exponent = math.floor(math.log10(value))
    for step in (1, 2, 5, 10):
        candidate = step * 10.0**exponent
        if candidate >= value * (1 - 1e-9):
            return candidate
    return 10.0 ** (exponent + 1)


def log_ticks(low: float, high: float, limit: int = 7) -> list[float]:
    """Choose readable tick values for a logarithmic axis from low to high.

    Uses 1, 2 and 5 times each power of ten when the range is short, powers
    of ten when it is long, and every second or third power when it is very
    long, so the axis never carries more than `limit` labels.
    """
    first, last = math.floor(math.log10(low)), math.ceil(math.log10(high))
    inside = lambda value: low * (1 - 1e-9) <= value <= high * (1 + 1e-9)  # noqa: E731
    fine = [
        step * 10.0**exponent
        for exponent in range(first, last + 1)
        for step in (1, 2, 5)
        if inside(step * 10.0**exponent)
    ]
    if len(fine) <= limit:
        return fine
    decades = [10.0**exponent for exponent in range(first, last + 1) if inside(10.0**exponent)]
    stride = 1
    while len(decades[::stride]) > limit:
        stride += 1
    return decades[::stride]


def format_count(value: float) -> str:
    """Format an input size compactly: 100, 1K, 20K, 1M."""
    for suffix, scale in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if value >= scale:
            return f"{value / scale:.3g}{suffix}"
    return f"{value:.3g}"
