#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-${AGENT_SKILLS_DIR:-}}"

if [[ -z "$TARGET" || $# -gt 1 ]]; then
  cat >&2 <<'EOF'
Usage: install_autodesign_skills.sh AGENT_SKILLS_DIR
   or: AGENT_SKILLS_DIR=/path/to/skills install_autodesign_skills.sh

The calling agent should supply its own user-level Skills directory.
EOF
  exit 2
fi

python3 - "$ROOT/skills" "$TARGET" <<'PY'
from pathlib import Path
import shutil
import sys

source_root = Path(sys.argv[1])
target_root = Path(sys.argv[2]).expanduser().resolve()
names = (
    "run-autodesign",
    "autodesign-method-router",
    "autodesign-evidence-designer",
    "autodesign-implementer",
    "autodesign-executor",
    "autodesign-result-scientist",
    "autodesign-integrity-auditor",
)
skills = [source_root / name for name in names]
missing = [str(path / "SKILL.md") for path in skills if not (path / "SKILL.md").is_file()]
if missing:
    raise SystemExit("ERROR: missing Skill files: " + ", ".join(missing))

target_root.mkdir(parents=True, exist_ok=True)
for source in skills:
    target = target_root / source.name
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    print(f"SKILL_INSTALL_PASS name={source.name} path={target}")

print(f"AUTODESIGN_SKILL_SUITE_INSTALL_PASS count={len(skills)} path={target_root}")
PY
