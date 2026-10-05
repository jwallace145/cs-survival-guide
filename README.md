# CS Survival Guide

A field guide to computer science fundamentals — algorithms, data structures,
system design, distributed systems, databases, networking, operating systems,
concurrency, and AI.

The guide is published with [Zensical](https://zensical.org) to GitHub Pages:
**https://jwallace145.github.io/cs-survival-guide/**

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

scripts/install-kit.sh             # install the pinned library into lib/
scripts/zensical.sh serve          # live-reloading dev server
scripts/zensical.sh build --clean  # static build into site/
```

`scripts/zensical.sh` passes its arguments to `zensical` and adds the
Reference section when the library is present under `lib/`. Plain
`zensical serve` and `zensical build` still work without the library; they
just render the site without the Reference section.

## API reference

The Reference section is generated from the docstrings of
[`cs-survival-kit`](https://github.com/jwallace145/cs-survival-kit), the
library that accompanies the guide — no reference markdown is written by hand.

- **`kit-version.txt`** is the single source of truth for which library
  version the site documents.
- **`scripts/install-kit.sh`** installs that version from PyPI into `lib/`
  (git-ignored). If the pinned version is not on PyPI it warns and skips the
  install, and the site builds without a Reference section.
- **`scripts/zensical.sh`** builds the site. When `lib/cs_survival_kit`
  exists it appends `zensical.reference.toml` to `zensical.toml` (as the
  git-ignored `zensical.generated.toml`) so that mkdocstrings and api-autonav
  render the Reference section, titled with the installed version.

CI runs the same two scripts, on pull requests (`Build Docs`) and on deploy.

## Benchmark results

Guide pages show benchmark tables without containing any numbers. Each
release of `cs-survival-kit` ships its results, measured on a GitHub-hosted
runner when the release was built, in `cs_survival_kit/_data/benchmarks.json`.
`guide_macros.py` reads that file from `lib/` at build time, so the tables
always describe the library version pinned in `kit-version.txt` and update
when that pin is bumped.

A page opts in with front matter and then calls the `benchmark` macro:

```markdown
---
render_macros: true
---

{{ benchmark("dynamic_array.append") }}
{{ benchmark("dynamic_array.append", view="total") }}
{{ benchmark("dynamic_array.append", view="per_item", cases=["list"]) }}
```

- `view` is `"total"` (time per run, with the fitted slope), `"per_item"`
  (time divided by the input size) or `"both"`, the default, which shows the
  two in tabs.
- `cases` picks and orders the columns; the default is every case.
- Each table has a line chart above it, with both axes logarithmic, so a
  power law is a straight line and its steepness is the complexity: constant
  cost is flat, linear rises at one decade per decade, quadratic at two. Pass
  `chart=False` for tables only.

The charts are inline SVG generated at build time, with no JavaScript and no
chart library. Their colours live in `docs/stylesheets/benchmarks.css` and
follow the light/dark theme. A chart shows at most four cases, because the
four colours were measured as a set to be distinguishable from one another,
including for colour-blind readers; with more cases, choose four with `cases`.
Each series also has its own marker shape, and hovering a point shows its
value.
- Write prose around what is stable (the shape of the curve), not around a
  particular number, because the numbers change with every library release.

If the library is not installed under `lib/`, the macro renders a warning box
and the site still builds. With the library installed, CI treats an unknown
benchmark or case name as a build failure; locally it is a warning box, so a
page can be drafted against a local checkout whose results file is empty.

The macros have unit tests: `python -m unittest discover -s tests`.

### Previewing unreleased docstrings

To preview docstrings from a local checkout of the library before a release:

```bash
scripts/link-local-kit.sh ../cs-survival-kit   # symlink lib/cs_survival_kit
scripts/zensical.sh serve                      # reloads as the sources change

scripts/install-kit.sh                         # back to the pinned version
```

Restart `scripts/zensical.sh serve` after switching between the two, or after
editing `zensical.toml`: the generated config is assembled once at startup.

### How a library release reaches the site

1. `cs-survival-kit` publishes a release to PyPI and sends a `kit-released`
   `repository_dispatch` to this repository.
2. The `Bump Kit` workflow validates the version, waits for it to appear on
   PyPI, and opens a `fix(deps): bump cs-survival-kit to X.Y.Z` PR that
   updates `kit-version.txt`. It never merges on its own.
3. Merging that PR redeploys the site with the new Reference section and,
   being a `fix`, adds a patch release to the Release Please PR.
4. Merging the Release Please PR tags the new version of the guide.

`Bump Kit` can also be run manually from the Actions tab with a `version`
input, to retry a missed release or pin back to an earlier one.

## Releases

CS Survival Guide is treated as a versioned software artifact. It uses
[Conventional Commits](https://www.conventionalcommits.org) and
[Semantic Versioning](https://semver.org), starting in the `0.x` development
lifecycle.

```text
feat:                      -> minor release (0.1.0 -> 0.2.0)
fix:                       -> patch release (0.2.0 -> 0.2.1)
feat!: (breaking change)   -> while in 0.x, also bumps the minor version
```

[Release Please](https://github.com/googleapis/release-please) watches `main`
and automatically maintains a release PR that accumulates changes. Merging
that PR:

- updates `version.txt` (the version source of truth) and the footer version
  in `zensical.toml`
- updates [`CHANGELOG.md`](CHANGELOG.md)
- creates the SemVer git tag (e.g. `v0.4.0`)
- creates the corresponding GitHub Release

`v1.0.0` is a deliberate milestone, not an automatic one: while the project is
in `0.x`, breaking changes bump the minor version. When the guide reaches a
meaningful level of maturity, `1.0.0` can be released explicitly by adding a
`Release-As: 1.0.0` footer to a commit.

### Commit examples

```text
feat(algorithms): add sliding window guide
feat(system-design): add consistent hashing guide
fix(databases): correct transaction isolation explanation
docs(networking): clarify TCP handshake explanation
refactor(site): reorganize system design navigation
chore(deps): update Zensical
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full convention and suggested
scopes. Commits are validated in CI; no local tooling is required.

## Changelog

[`CHANGELOG.md`](CHANGELOG.md) is the single canonical changelog, generated by
Release Please. The website's [Changelog
page](https://jwallace145.github.io/cs-survival-guide/changelog/) renders the
same file at build time (via the `pymdownx.snippets` include in
`docs/changelog.md`) — nothing is maintained twice.
