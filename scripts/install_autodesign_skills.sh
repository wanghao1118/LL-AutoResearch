#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_HOME="${CODEX_HOME:-$HOME/.codex}/skills"
VALIDATOR="$SKILLS_HOME/.system/skill-creator/scripts/quick_validate.py"
SKILLS=(
  run-autodesign
  autodesign-method-router
  autodesign-evidence-designer
  autodesign-implementer
  autodesign-executor
  autodesign-result-scientist
  autodesign-integrity-auditor
)

mkdir -p "$SKILLS_HOME"
if [[ ! -f "$VALIDATOR" ]]; then
  printf 'ERROR: Codex Skill validator not found: %s\n' "$VALIDATOR" >&2
  exit 1
fi

for skill in "${SKILLS[@]}"; do
  source_dir="$ROOT/skills/$skill"
  target_dir="$SKILLS_HOME/$skill"
  if [[ ! -f "$source_dir/SKILL.md" || ! -f "$source_dir/agents/openai.yaml" ]]; then
    printf 'ERROR: incomplete source Skill: %s\n' "$source_dir" >&2
    exit 1
  fi
  python3 "$VALIDATOR" "$source_dir"
  python3 - "$source_dir" "$target_dir" <<'PY'
from pathlib import Path
import shutil
import sys
source = Path(sys.argv[1])
target = Path(sys.argv[2])
if target.exists():
    shutil.rmtree(target)
shutil.copytree(source, target)
PY
  python3 "$VALIDATOR" "$target_dir"
  printf 'SKILL_INSTALL_PASS name=%s path=%s\n' "$skill" "$target_dir"
done
printf 'AUTODESIGN_SKILL_SUITE_INSTALL_PASS count=%s\n' "${#SKILLS[@]}"
