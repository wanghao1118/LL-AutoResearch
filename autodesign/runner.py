"""Local command executor. GPU scheduling is intentionally an adapter boundary."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .io import read_json, write_json, write_text

STAGE_ORDER = ("preflight", "smoke", "experiment", "aggregate", "collect")


def _group_commands(commands: list[dict[str, Any]]) -> list[tuple[str, list[dict[str, Any]]]]:
    groups: list[tuple[str, list[dict[str, Any]]]] = []
    for record in commands:
        stage = str(record.get("stage") or "")
        if groups and groups[-1][0] == stage:
            groups[-1][1].append(record)
        else:
            groups.append((stage, [record]))
    return groups


def execution_progress(commands: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the successful ordered stage prefix represented by command records."""

    completed: list[str] = []
    groups = _group_commands(commands)
    for expected_stage, group in zip(STAGE_ORDER, groups):
        if expected_stage != group[0] or not group or any(
            record.get("exit_status") != 0 for record in group[1]
        ):
            break
        completed.append(expected_stage)
    workflow_complete = tuple(completed) == STAGE_ORDER and len(groups) == len(STAGE_ORDER)
    return {
        "completed_stages": completed,
        "workflow_complete": workflow_complete,
        "next_stage": None if workflow_complete else STAGE_ORDER[len(completed)],
    }


def execution_completion_errors(
    execution: Any, command_plan: Any
) -> list[str]:
    """Validate the complete current execution sequence against its command plan."""

    if not isinstance(execution, dict):
        return ["execution_record.json must contain an object"]
    errors: list[str] = []
    if execution.get("status") != "PASS":
        errors.append("execution_record.status must be PASS before result ingestion")
    commands = execution.get("commands")
    if not isinstance(commands, list):
        return [*errors, "execution_record.commands must be a list"]
    if not isinstance(command_plan, dict):
        return [*errors, "command_plan.json must contain an object"]

    groups = _group_commands(
        [record for record in commands if isinstance(record, dict)]
    )
    observed_order = [stage for stage, _ in groups]
    if observed_order != list(STAGE_ORDER):
        errors.append(
            "execution_record must contain the ordered stages preflight, smoke, "
            "experiment, aggregate, collect; "
            f"observed {observed_order}"
        )
    executor = execution.get("executor")
    for stage, group in groups:
        if stage not in STAGE_ORDER:
            continue
        planned = command_plan.get(stage)
        if not isinstance(planned, list):
            errors.append(f"command_plan.{stage} must be a list")
            continue
        expected_commands = (
            [" && ".join(planned)] if executor == "remote_gpu" else planned
        )
        actual_commands = [record.get("command") for record in group]
        if actual_commands != expected_commands:
            errors.append(
                f"execution_record {stage} commands do not match the current command plan"
            )
        if any(record.get("exit_status") != 0 for record in group):
            errors.append(f"execution_record {stage} has a non-zero exit status")
    return errors


def _resume_prefix(
    run_path: Path, command_plan: dict[str, Any], target_stage: str
) -> tuple[list[dict[str, Any]], str | None, str | None]:
    """Load a valid local prefix or explain which prerequisite must be rerun."""

    record_path = run_path / "execution_record.json"
    if not record_path.is_file():
        missing = STAGE_ORDER[0] if target_stage != STAGE_ORDER[0] else None
        return [], None, missing
    existing = read_json(record_path)
    if not isinstance(existing, dict) or existing.get("executor") != "local":
        missing = STAGE_ORDER[0] if target_stage != STAGE_ORDER[0] else None
        return [], None, missing
    groups = _group_commands(
        [record for record in existing.get("commands", []) if isinstance(record, dict)]
    )
    kept: list[dict[str, Any]] = []
    target_index = STAGE_ORDER.index(target_stage)
    for index, required_stage in enumerate(STAGE_ORDER[:target_index]):
        if index >= len(groups) or groups[index][0] != required_stage:
            return kept, existing.get("started_at"), required_stage
        group = groups[index][1]
        if [record.get("command") for record in group] != command_plan.get(required_stage):
            return kept, existing.get("started_at"), required_stage
        if any(record.get("exit_status") != 0 for record in group):
            return kept, existing.get("started_at"), required_stage
        kept.extend(group)
    return kept, existing.get("started_at"), None


def run_local_commands(run_dir: str | Path, stage: str = "all") -> dict[str, Any]:
    run_path = Path(run_dir)
    project_dir = run_path / "generated_project"
    command_plan = read_json(run_path / "command_plan.json")
    if not isinstance(command_plan, dict):
        raise TypeError("command_plan.json must contain an object")
    (run_path / "logs").mkdir(parents=True, exist_ok=True)
    stage_order = list(STAGE_ORDER) if stage == "all" else [stage]
    if any(item not in STAGE_ORDER for item in stage_order):
        raise ValueError(f"Unknown execution stage: {stage}")

    now = datetime.now(timezone.utc).isoformat()
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    overall_status = "PASS"
    previous_started_at: str | None = None
    if stage != "all":
        records, previous_started_at, missing_prerequisite = _resume_prefix(
            run_path, command_plan, stage
        )
        if missing_prerequisite is not None:
            overall_status = "FAIL"
            errors.append(
                f"Cannot run {stage}: prerequisite {missing_prerequisite} is missing, "
                "failed, or stale under the current command plan"
            )
            stage_order = []
    started_at = previous_started_at or now
    for stage_name in stage_order:
        stage_commands = command_plan.get(stage_name)
        if not isinstance(stage_commands, list) or not stage_commands or not all(
            isinstance(command, str) and command.strip() for command in stage_commands
        ):
            overall_status = "FAIL"
            errors.append(f"No valid commands configured for stage: {stage_name}")
            break
        for command_index, command in enumerate(stage_commands, start=1):
            completed = subprocess.run(
                ["/bin/bash", "-lc", command],
                cwd=project_dir,
                text=True,
                capture_output=True,
                check=False,
            )
            record = {
                "stage": stage_name,
                "command_index": command_index,
                "command": command,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "exit_status": completed.returncode,
            }
            records.append(record)
            write_text(
                run_path / "logs" / f"{stage_name}_{command_index}.log",
                (
                    f"COMMAND: {command}\n"
                    f"EXIT_STATUS: {completed.returncode}\n"
                    f"STDOUT:\n{completed.stdout}\n"
                    f"STDERR:\n{completed.stderr}"
                ),
            )
            if completed.returncode != 0:
                overall_status = "FAIL"
                break
        if overall_status == "FAIL":
            break

    progress = execution_progress(records)
    record = {
        "status": overall_status,
        "executor": "local",
        "stage": stage,
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "commands": records,
        "errors": errors,
        **progress,
    }
    write_json(run_path / "execution_record.json", record)
    return record
