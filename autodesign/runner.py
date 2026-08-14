"""Local command-plan execution and execution-record validation."""

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
    for stage, group in groups:
        if stage not in STAGE_ORDER:
            continue
        planned = command_plan.get(stage)
        if not isinstance(planned, list):
            errors.append(f"command_plan.{stage} must be a list")
            continue
        expected_commands = planned
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
) -> tuple[list[dict[str, Any]], list[str], str | None, str | None, dict[str, Any] | None]:
    """Load a valid local prefix or explain which prerequisite must be rerun."""

    record_path = run_path / "execution_record.json"
    if not record_path.is_file():
        missing = STAGE_ORDER[0] if target_stage != STAGE_ORDER[0] else None
        return [], [], None, missing, None
    existing = read_json(record_path)
    if not isinstance(existing, dict) or existing.get("executor") != "local":
        missing = STAGE_ORDER[0] if target_stage != STAGE_ORDER[0] else None
        return [], [], None, missing, existing if isinstance(existing, dict) else None
    groups = _group_commands(
        [record for record in existing.get("commands", []) if isinstance(record, dict)]
    )
    kept: list[dict[str, Any]] = []
    completed: list[str] = []
    target_index = STAGE_ORDER.index(target_stage)
    for index, required_stage in enumerate(STAGE_ORDER[:target_index]):
        if index >= len(groups) or groups[index][0] != required_stage:
            return kept, completed, existing.get("started_at"), required_stage, existing
        group = groups[index][1]
        if [record.get("command") for record in group] != command_plan.get(required_stage):
            return kept, completed, existing.get("started_at"), required_stage, existing
        if any(record.get("exit_status") != 0 for record in group):
            return kept, completed, existing.get("started_at"), required_stage, existing
        kept.extend(group)
        completed.append(required_stage)
    return kept, completed, existing.get("started_at"), None, existing


def _resume_all_prefix(
    run_path: Path, command_plan: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[str], str | None, dict[str, Any] | None]:
    """Keep the unchanged successful prefix and return the first stage to rerun."""

    record_path = run_path / "execution_record.json"
    if not record_path.is_file():
        return [], [], None, None
    existing = read_json(record_path)
    if not isinstance(existing, dict) or existing.get("executor") != "local":
        return [], [], None, existing if isinstance(existing, dict) else None
    groups = _group_commands(
        [record for record in existing.get("commands", []) if isinstance(record, dict)]
    )
    kept: list[dict[str, Any]] = []
    completed: list[str] = []
    for index, required_stage in enumerate(STAGE_ORDER):
        if index >= len(groups) or groups[index][0] != required_stage:
            break
        group = groups[index][1]
        planned = command_plan.get(required_stage)
        if not isinstance(planned, list):
            break
        if [record.get("command") for record in group] != planned:
            break
        if any(record.get("exit_status") != 0 for record in group):
            break
        kept.extend(group)
        completed.append(required_stage)
    return kept, completed, existing.get("started_at"), existing


def run_local_commands(run_dir: str | Path, stage: str = "all") -> dict[str, Any]:
    run_path = Path(run_dir)
    project_dir = run_path / "generated_project"
    if not project_dir.is_dir():
        raise ValueError(
            "generated_project is missing: "
            f"{project_dir}; run the autodesign-implementer Skill before run-local"
        )
    command_plan = read_json(run_path / "command_plan.json")
    if not isinstance(command_plan, dict):
        raise TypeError("command_plan.json must contain an object")
    (run_path / "logs").mkdir(parents=True, exist_ok=True)
    stage_order = list(STAGE_ORDER) if stage == "all" else [stage]
    if any(item not in STAGE_ORDER for item in stage_order):
        raise ValueError(f"Unknown execution stage: {stage}")

    now = datetime.now(timezone.utc).isoformat()
    records: list[dict[str, Any]] = []
    reused_stages: list[str] = []
    errors: list[str] = []
    overall_status = "PASS"
    previous_started_at: str | None = None
    existing: dict[str, Any] | None = None
    if stage == "all":
        records, reused_stages, previous_started_at, existing = _resume_all_prefix(
            run_path, command_plan
        )
        stage_order = list(STAGE_ORDER[len(reused_stages) :])
        if not stage_order and existing is not None:
            return {
                **existing,
                "stage": "all",
                "reused_stages": reused_stages,
                "reused_existing_run": True,
                "record_preserved": True,
            }
    else:
        (
            records,
            reused_stages,
            previous_started_at,
            missing_prerequisite,
            existing,
        ) = _resume_prefix(run_path, command_plan, stage)
        if missing_prerequisite is not None:
            error = (
                f"Cannot run {stage}: prerequisite {missing_prerequisite} is missing, "
                "failed, or stale under the current command plan"
            )
            preserved_commands = (
                [item for item in existing.get("commands", []) if isinstance(item, dict)]
                if isinstance(existing, dict)
                else []
            )
            return {
                "status": "FAIL",
                "executor": "local",
                "stage": stage,
                "started_at": (
                    existing.get("started_at") if isinstance(existing, dict) else now
                ),
                "finished_at": now,
                "commands": preserved_commands,
                "errors": [error],
                "reused_stages": reused_stages,
                "record_preserved": (run_path / "execution_record.json").is_file(),
                **execution_progress(preserved_commands),
            }
    invalid_stage = next(
        (
            stage_name
            for stage_name in stage_order
            if not isinstance(command_plan.get(stage_name), list)
            or not command_plan[stage_name]
            or not all(
                isinstance(command, str) and command.strip()
                for command in command_plan[stage_name]
            )
        ),
        None,
    )
    if invalid_stage is not None:
        preserved_commands = (
            [item for item in existing.get("commands", []) if isinstance(item, dict)]
            if isinstance(existing, dict)
            else []
        )
        return {
            "status": "FAIL",
            "executor": "local",
            "stage": stage,
            "started_at": existing.get("started_at") if isinstance(existing, dict) else now,
            "finished_at": now,
            "commands": preserved_commands,
            "errors": [f"No valid commands configured for stage: {invalid_stage}"],
            "reused_stages": reused_stages,
            "record_preserved": (run_path / "execution_record.json").is_file(),
            **execution_progress(preserved_commands),
        }
    started_at = previous_started_at or now
    for stage_name in stage_order:
        stage_commands = command_plan.get(stage_name)
        assert isinstance(stage_commands, list)
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
        "reused_stages": reused_stages,
        "record_preserved": False,
        **progress,
    }
    write_json(run_path / "execution_record.json", record)
    return record
