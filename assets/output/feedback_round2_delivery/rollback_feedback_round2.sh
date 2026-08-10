#!/bin/zsh
set -euo pipefail
DEFAULT_ROOT="/Users/yzb/Desktop/research/exp31_autoresearch"
ROOT="${1:-$DEFAULT_ROOT}"
PATCH="${2:-$DEFAULT_ROOT/assets/output/feedback_round2_delivery/auto_bench_feedback_round2.patch}"
if [[ -d "$ROOT/.git" ]]; then
  git -C "$ROOT" apply --check --reverse "$PATCH"
  git -C "$ROOT" apply --reverse "$PATCH"
else
  (cd "$ROOT" && git apply --no-index --check --reverse "$PATCH")
  (cd "$ROOT" && git apply --no-index --reverse "$PATCH")
fi
printf 'ROLLED_BACK feedback_round2 code and documentation delta under %s\n' "$ROOT"
