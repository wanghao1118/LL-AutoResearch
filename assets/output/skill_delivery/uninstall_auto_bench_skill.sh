#!/usr/bin/env bash
set -euo pipefail
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
installed="${CODEX_HOME:-$HOME/.codex}/skills/auto-bench"
patch="$repo/assets/output/skill_delivery/auto_bench_skill.patch"
mode="${1:---apply}"
case "$mode" in
  --check)
    test -f "$installed/SKILL.md"
    git -C "$repo" apply --reverse --check "$patch"
    printf 'skill_uninstall_check=PASS\n'
    ;;
  --apply)
    git -C "$repo" apply --reverse "$patch"
    TARGET="$installed" python3 - <<'PY2'
import os, shutil
from pathlib import Path
target=Path(os.environ['TARGET'])
if target.is_dir() and not target.is_symlink():
    shutil.rmtree(target)
elif target.exists() or target.is_symlink():
    target.unlink()
PY2
    printf 'skill_uninstall_apply=PASS\n'
    ;;
  *)
    printf 'usage: %s [--check|--apply]\n' "$0" >&2
    exit 2
    ;;
esac
