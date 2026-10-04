#!/usr/bin/env bash
# Validates a cs-survival-kit version and waits until pip can download it
# from PyPI. Used by the bump-kit workflow: a release is announced moments
# after publishing, before every PyPI index has caught up.
#
#   scripts/wait-for-kit.sh 0.1.0
#
# KIT_WAIT_TIMEOUT (seconds, default 600) bounds the total wait.
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <version>" >&2
  exit 2
fi

version="$1"
timeout="${KIT_WAIT_TIMEOUT:-600}"

# Release versions only (MAJOR.MINOR.PATCH, no leading zeros) — this is what
# the library's Release Please setup produces.
semver='^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$'
if [[ ! "$version" =~ $semver ]]; then
  echo "error: '$version' is not a MAJOR.MINOR.PATCH version" >&2
  exit 1
fi

if ! python3 -m pip --version > /dev/null 2>&1; then
  echo "error: pip is required to check PyPI (python3 -m pip)" >&2
  exit 1
fi

download_dir="$(mktemp -d)"
trap 'rm -rf "$download_dir"' EXIT

delay=10
start=$SECONDS
while true; do
  if python3 -m pip download --quiet --no-deps --no-cache-dir \
    --dest "$download_dir" "cs-survival-kit==$version" > "$download_dir/pip.log" 2>&1; then
    echo "cs-survival-kit $version is available on PyPI."
    exit 0
  fi

  elapsed=$((SECONDS - start))
  if ((elapsed + delay > timeout)); then
    echo "error: cs-survival-kit $version did not appear on PyPI within ${timeout}s" >&2
    echo "last pip output:" >&2
    tail -n 5 "$download_dir/pip.log" >&2
    exit 1
  fi

  echo "cs-survival-kit $version is not on PyPI yet; retrying in ${delay}s (${elapsed}s elapsed)."
  sleep "$delay"
  delay=$((delay * 2 > 60 ? 60 : delay * 2))
done
