#!/usr/bin/env bash
set -euo pipefail
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
patch="$repo/assets/output/automatic_validation_delivery/automatic_validation_changes.patch"
mode="${1:---apply}"
case "$mode" in
  --check)
    git -C "$repo" apply --reverse --check "$patch"
    printf 'rollback_check=PASS\n'
    ;;
  --apply)
    git -C "$repo" apply --reverse "$patch"
    printf 'rollback_apply=PASS\n'
    ;;
  *)
    printf 'usage: %s [--check|--apply]\n' "$0" >&2
    exit 2
    ;;
esac
