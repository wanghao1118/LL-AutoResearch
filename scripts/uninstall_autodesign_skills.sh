#!/usr/bin/env bash
set -euo pipefail

SKILLS_HOME="${CODEX_HOME:-$HOME/.codex}/skills"
SKILLS=(
  run-autodesign
  autodesign-method-router
  autodesign-evidence-designer
  autodesign-implementer
  autodesign-executor
  autodesign-result-scientist
  autodesign-integrity-auditor
)
for skill in "${SKILLS[@]}"; do
  target_dir="$SKILLS_HOME/$skill"
  python3 - "$target_dir" <<'PY'
from pathlib import Path
import shutil
import sys
path = Path(sys.argv[1])
if path.exists():
    shutil.rmtree(path)
PY
  printf 'SKILL_UNINSTALL_PASS name=%s path=%s\n' "$skill" "$target_dir"
done
