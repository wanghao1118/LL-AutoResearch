"""Load ordinary prompt files and inject the active run's paths."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

from .codex_runner import MODULE_ROOT


def tool_command() -> str:
    parts = [sys.executable, str(MODULE_ROOT / "__main__.py")]
    return subprocess.list2cmdline(parts) if os.name == "nt" else shlex.join(parts)


def build_prompt(task: dict, action: str) -> str:
    workspace = Path(task["workspace"])
    run_dir = Path(task["run_dir"])
    instruction_files = [Path.home() / ".codex" / "AGENTS.md"]
    for directory in (*reversed(workspace.parents), workspace):
        instruction_files.extend(directory / name for name in ("AGENTS.md", "CLAUDE.md"))
    context = {
        "action": action,
        "scope": task["scope"],
        "workspace": str(workspace),
        "run_dir": str(run_dir),
        "input": str(run_dir / "input_brief.md"),
        "pause_file": str(run_dir / "pause_requested.json"),
        "tool_command": tool_command(),
        "resume": bool(task.get("attempts")),
        "instruction_files": [str(p) for p in instruction_files if p.is_file()],
        "last_summary": task.get("summary", ""),
        "previous_error": task.get("previous_error"),
        "recovery_note": task.get("recovery_note", ""),
        "references": str(MODULE_ROOT / "prompts" / "references"),
        "stage_recorder": str(MODULE_ROOT / "scripts" / "run_stage.py"),
    }
    role = "design" if action == "revision" else action
    sections = []
    for name in ("workflow", role, "action"):
        content = (MODULE_ROOT / "prompts" / f"{name}.md").read_text(encoding="utf-8")
        content = content.replace(
            "auto_design/prompts/references/", str(MODULE_ROOT / "prompts" / "references") + "/"
        )
        content = content.replace("auto_design/scripts/run_stage.py", context["stage_recorder"])
        content = content.replace("python3 -m auto_design", context["tool_command"])
        sections.append(content)
    sections.append("TASK_CONTEXT_JSON=\n" + json.dumps(context, ensure_ascii=False, indent=2))
    return "\n\n".join(sections)
