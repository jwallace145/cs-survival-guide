#!/usr/bin/env bash
# Points lib/cs_survival_kit at a local cs-survival-kit checkout, so
# unreleased docstrings can be previewed with `scripts/zensical.sh serve`.
# Run scripts/install-kit.sh to go back to the pinned release.
#
#   scripts/link-local-kit.sh ../cs-survival-kit
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <path-to-local-kit-repo>" >&2
  exit 2
fi

if [[ ! -d "$1/src/cs_survival_kit" ]]; then
  echo "error: $1/src/cs_survival_kit is not a directory; expected a cs-survival-kit checkout" >&2
  exit 1
fi

# Resolve before changing directory so relative arguments keep working.
source_dir="$(cd "$1/src/cs_survival_kit" && pwd)"

cd "$(dirname "$0")/.."

mkdir -p lib
rm -rf lib/cs_survival_kit lib/cs_survival_kit-*.dist-info
ln -s "$source_dir" lib/cs_survival_kit

echo "lib/cs_survival_kit -> $source_dir"
