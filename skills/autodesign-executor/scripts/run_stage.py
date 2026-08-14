#!/usr/bin/env python3
"""Run one ordered AutoDesign stage and record literal command evidence."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path

STAGES = ("preflight", "smoke", "experiment", "aggregate", "collect")


def read_record(path: Path) -> dict:
    if not path.is_file():
        return {"schema_version": "1.0", "executor": "local", "commands": []}
    return json.loads(path.read_text(encoding="utf-8"))


def successful_prefix(record: dict, target: str) -> list[dict]:
    commands = [item for item in record.get("commands", []) if isinstance(item, dict)]
    kept: list[dict] = []
    for stage in STAGES[: STAGES.index(target)]:
        group = [item for item in commands if item.get("stage") == stage]
        if not group or any(item.get("exit_status") != 0 for item in group):
            raise RuntimeError(f"prerequisite stage is missing or failed: {stage}")
        kept.extend(group)
    return kept


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--stage", choices=STAGES, required=True)
    parser.add_argument("--cwd", type=Path)
    parser.add_argument(
        "--execution-mode",
        choices=("fresh_experiment", "provenance_replay"),
        default="fresh_experiment",
    )
    parser.add_argument("--source-results")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("a command is required after --")

    run_dir = args.run_dir.resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    record_path = run_dir / "execution_record.json"
    prior = read_record(record_path)
    try:
        records = successful_prefix(prior, args.stage) if args.stage != STAGES[0] else []
    except RuntimeError as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, ensure_ascii=False))
        return 3

    cwd = (args.cwd or (run_dir / "generated_project")).resolve()
    started_at = datetime.now(timezone.utc).isoformat()
    command_text = command[0] if len(command) == 1 else shlex.join(command)
    completed = subprocess.run(
        ["/bin/bash", "-lc", command_text],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    records.append(
        {
            "stage": args.stage,
            "command": command_text,
            "cwd": str(cwd),
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "exit_status": completed.returncode,
        }
    )
    completed_stages = []
    for stage in STAGES:
        group = [item for item in records if item.get("stage") == stage]
        if not group or any(item.get("exit_status") != 0 for item in group):
            break
        completed_stages.append(stage)
    workflow_complete = tuple(completed_stages) == STAGES
    record = {
        "schema_version": "1.0",
        "executor": "local",
        "execution_mode": args.execution_mode,
        "source_results": args.source_results,
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "completed_stages": completed_stages,
        "workflow_complete": workflow_complete,
        "next_stage": None if workflow_complete else STAGES[len(completed_stages)],
        "commands": records,
    }
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
