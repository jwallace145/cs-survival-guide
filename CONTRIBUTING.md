# Contributing

## Commit messages

This repository uses [Conventional Commits](https://www.conventionalcommits.org).
Commit messages drive automated versioning and the changelog via
[Release Please](https://github.com/googleapis/release-please), so commits
reaching `main` must follow the convention.

Pull requests are **squash-merged** (the only merge method enabled), so
`main` stays a linear history with one conventional commit per PR and no
merge commits. The **PR title alone becomes that squash commit's message**,
which means:

- the PR title must be a Conventional Commit header
  (e.g. `feat(algorithms): add sliding window guide`)
- commits *inside* a PR branch can be messy work-in-progress commits —
  they get squashed away
- the PR description is not part of the commit, so it can contain anything:
  code samples, tables, checklists
- a breaking change is marked with `!` in the title (`feat(site)!: ...`)

The description is deliberately kept out of the commit. Release Please parses
every commit message on `main`, and a description line that happens to look
like a commit header (for example a code sample such as `Foo(bar=baz(1))`)
makes the parse fail, which silently drops the commit from the next release.

A GitHub Actions workflow (`Conventional Commits`) validates PR titles on
pull requests — there is nothing to install locally. `main` is protected:
every change lands through a PR, and the `build` and `pr-title` checks must
pass before it can be merged.

### Format

```text
<type>(<optional scope>): <description>
```

### Types and their release impact

| Type | Purpose | Release impact |
|---|---|---|
| `feat` | New guide, section, or capability | minor bump |
| `fix` | Correction to existing content or behavior | patch bump |
| `docs` | Clarification or polish of existing content | none (shown in changelog) |
| `refactor` | Restructuring without changing meaning | none (shown in changelog) |
| `perf` | Performance improvement | none (shown in changelog) |
| `chore` | Maintenance, e.g. `chore(deps): update Zensical` | none (shown in changelog) |
| `build`, `ci`, `test`, `style` | Tooling and infrastructure | none (hidden from changelog) |

A `!` after the type (`feat!:`) marks a breaking change. While the project is
in the `0.x` lifecycle, breaking changes bump the minor version; after `1.0.0`
they bump the major version.

### Suggested scopes

Use a scope when it improves readability. Common scopes:

```text
algorithms, data-structures, system-design, distributed-systems,
databases, networking, operating-systems, concurrency, ai,
site, ci, deps
```

These are suggestions, not an enforced list — any sensible scope is accepted.

### Examples

```text
feat(algorithms): add sliding window guide
feat(ai): add transformer inference overview
fix(algorithms): correct binary search complexity
docs(networking): clarify TCP handshake explanation
refactor(site): reorganize system design navigation
chore(deps): update Zensical
```

> Note: Release Please groups changelog entries by commit *type* (Features,
> Bug Fixes, Documentation, Refactoring, Miscellaneous). Dependency updates
> like `chore(deps): …` appear under *Miscellaneous* with their `deps:` scope
> shown — a dedicated top-level "Dependencies" section is not cleanly
> supported by type-based grouping.

## Release flow

1. Conventional commits land on `main` via squash-merged PRs.
2. Release Please maintains a pending release PR that accumulates those
   changes and previews the next version and changelog.
3. Merging the release PR updates `version.txt`, `CHANGELOG.md`, and the
   footer version in `zensical.toml`, then creates the `vX.Y.Z` tag and the
   GitHub Release.
4. The site redeploys to GitHub Pages on every push to `main`, so the
   Changelog page and footer version update with the release merge.

Before merging, a pull request can be reviewed as a live site: the
`PR Preview` workflow comments a preview link on each pull request.

The current version's source of truth is `version.txt`.
