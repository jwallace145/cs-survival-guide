#!/usr/bin/env bash
# Installs the cs-survival-kit version pinned in kit-version.txt into lib/,
# where mkdocstrings reads its sources to render the Reference section.
#
# If the pinned version is not on PyPI this is not an error: the install is
# skipped with a warning and the site builds without a Reference section.
set -euo pipefail

cd "$(dirname "$0")/.."

version="$(tr -d '[:space:]' < kit-version.txt)"
if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "error: kit-version.txt does not contain a MAJOR.MINOR.PATCH version: '$version'" >&2
  exit 1
fi

# Start clean so a previous version or a local symlink never lingers.
rm -rf lib/cs_survival_kit lib/cs_survival_kit-*.dist-info

status="$(curl -sS -o /dev/null -w '%{http_code}' \
  "https://pypi.org/pypi/cs-survival-kit/$version/json")" || status="000"

case "$status" in
  200) ;;
  404)
    message="cs-survival-kit $version is not on PyPI; building without the Reference section."
    if [[ -n "${GITHUB_ACTIONS:-}" ]]; then
      echo "::warning title=Reference section skipped::$message"
    else
      echo "warning: $message" >&2
    fi
    exit 0
    ;;
  *)
    echo "error: could not reach PyPI to check cs-survival-kit $version (HTTP $status)" >&2
    exit 1
    ;;
esac

# --no-deps: the library has no runtime dependencies, and mkdocstrings only
# reads the sources. Fall back to uv for virtualenvs created without pip.
if python3 -m pip --version > /dev/null 2>&1; then
  python3 -m pip install --no-deps --target lib "cs-survival-kit==$version"
elif command -v uv > /dev/null 2>&1; then
  uv pip install --no-deps --target lib "cs-survival-kit==$version"
else
  echo "error: neither pip nor uv is available to install cs-survival-kit" >&2
  exit 1
fi
