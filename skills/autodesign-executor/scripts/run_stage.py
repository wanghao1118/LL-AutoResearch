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


def read_plan(run_dir: Path) -> dict:
    path = run_dir / "command_plan.json"
    if not path.is_file():
        raise RuntimeError(
            "command_plan.json is required before execution; "
            "run the autodesign-implementer Skill"
        )
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"command_plan.json is unreadable: {error}") from error
    if not isinstance(value, dict):
        raise TypeError("command_plan.json must contain an object")
    return value


def successful_prefix(record: dict, target: str, plan: dict) -> list[dict]:
    commands = [item for item in record.get("commands", []) if isinstance(item, dict)]
    kept: list[dict] = []
    for stage in STAGES[: STAGES.index(target)]:
        group = [item for item in commands if item.get("stage") == stage]
        if not group or any(item.get("exit_status") != 0 for item in group):
            raise RuntimeError(f"prerequisite stage is missing or failed: {stage}")
        if [item.get("command") for item in group] != plan.get(stage):
            raise RuntimeError(f"prerequisite stage is stale under command_plan.json: {stage}")
        kept.extend(group)
    target_group = [item for item in commands if item.get("stage") == target]
    target_successes: list[dict] = []
    for item in target_group:
        if item.get("exit_status") != 0:
            break
        target_successes.append(item)
    planned = plan.get(target)
    actual = [item.get("command") for item in target_successes]
    if not isinstance(planned, list) or actual != planned[: len(actual)]:
        target_successes = []
    kept.extend(target_successes)
    return kept


def execution_progress(records: list[dict], plan: dict) -> tuple[list[str], bool, str | None]:
    completed: list[str] = []
    for stage in STAGES:
        group = [item for item in records if item.get("stage") == stage]
        if not group or any(item.get("exit_status") != 0 for item in group):
            break
        planned = plan.get(stage)
        if not isinstance(planned, list) or [item.get("command") for item in group] != planned:
            break
        completed.append(stage)
    workflow_complete = tuple(completed) == STAGES
    return completed, workflow_complete, None if workflow_complete else STAGES[len(completed)]


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
        plan = read_plan(run_dir)
        records = successful_prefix(prior, args.stage, plan)
    except (RuntimeError, TypeError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, ensure_ascii=False))
        return 3

    cwd = (args.cwd or (run_dir / "generated_project")).resolve()
    started_at = datetime.now(timezone.utc).isoformat()
    command_text = command[0] if len(command) == 1 else shlex.join(command)
    target_prefix = [item for item in records if item.get("stage") == args.stage]
    planned = plan.get(args.stage)
    if not isinstance(planned, list) or not planned:
        print(
            json.dumps(
                {"status": "FAIL", "error": f"command_plan.{args.stage} is missing or invalid"},
                ensure_ascii=False,
            )
        )
        return 3
    command_index = len(target_prefix)
    if command_index == len(planned) and command_text == planned[0]:
        records = [item for item in records if item.get("stage") != args.stage]
        target_prefix = []
        command_index = 0
    if command_index >= len(planned) or planned[command_index] != command_text:
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "error": (
                        f"command does not match command_plan.{args.stage}[{command_index}]"
                    ),
                },
                ensure_ascii=False,
            )
        )
        return 3
    if not cwd.is_dir():
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "error": (
                        f"execution cwd is missing or not a directory: {cwd}; "
                        "run the autodesign-implementer Skill"
                    ),
                },
                ensure_ascii=False,
            )
        )
        return 3
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
            "command_index": len(target_prefix) + 1,
            "command": command_text,
            "cwd": str(cwd),
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "exit_status": completed.returncode,
        }
    )
    completed_stages, workflow_complete, next_stage = execution_progress(records, plan)
    record = {
        "schema_version": "1.0",
        "executor": "local",
        "execution_mode": args.execution_mode,
        "source_results": args.source_results,
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "completed_stages": completed_stages,
        "workflow_complete": workflow_complete,
        "next_stage": next_stage,
        "commands": records,
    }
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
