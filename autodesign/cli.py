"""Thin CLI for Skill-first AutoDesign state, execution, and result facts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .io import read_json
from .remote_gpu import RemoteGPUController, RemoteGPUError
from .runner import STAGE_ORDER, execution_completion_errors, run_local_commands
from .skillflow import (
    advance_skill_run,
    initialize_skill_run,
    inspect_skill_run,
    verify_skill_run,
)
from .skillresults import ingest_skill_results


def _print(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False))


def _completed_remote_stages(
    run_path: Path, controller: RemoteGPUController
) -> list[str]:
    record_path = run_path / "execution_record.json"
    if not record_path.is_file():
        return []
    execution = read_json(record_path)
    if not isinstance(execution, dict) or execution.get("executor") != "remote_gpu":
        return []
    commands = execution.get("commands") or []
    completed: list[str] = []
    for stage in STAGE_ORDER:
        group = [
            item
            for item in commands
            if isinstance(item, dict) and item.get("stage") == stage
        ]
        if (
            len(group) != 1
            or group[0].get("command")
            != controller.config["run"]["commands"].get(stage)
            or group[0].get("exit_status") != 0
        ):
            break
        completed.append(stage)
    return completed


def _remote_result_path(
    controller: RemoteGPUController, primary_relative: str
) -> Path:
    return (
        controller.repo_root
        / controller.config["local"]["result_dir"]
        / primary_relative
    ).resolve()


def _run_remote_all(
    controller: RemoteGPUController, *, dry_run: bool
) -> dict[str, Any]:
    """Deploy, execute the materialized five-stage plan, collect, and ingest."""

    validation = controller.validate()
    if validation["status"] == "FAIL":
        return {"status": "FAIL", "failed_step": "validate", "validation": validation}
    run_path = (controller.repo_root / controller.config["local"]["run_dir"]).resolve()
    plan = controller.write_plan(run_path / "remote_gpu", command_key="experiment")
    if dry_run:
        return {
            "status": "DRY_RUN",
            "validation": validation,
            "plan": plan,
            "deploy": controller.deploy(dry_run=True),
            "runs": [
                controller.execute("run", command_key=stage, dry_run=True)
                for stage in STAGE_ORDER
            ],
            "collect": controller.collect_results(dry_run=True),
        }
    if validation["status"] != "PASS":
        return {"status": "CONFIG_INCOMPLETE", "validation": validation, "plan": plan}

    command_plan = read_json(run_path / "command_plan.json")
    primary_relative = controller.config["run"]["primary_result_path"]
    result_path = _remote_result_path(controller, primary_relative)
    execution_path = run_path / "execution_record.json"
    result_summary_path = run_path / "result_summary.json"
    if execution_path.is_file() and result_summary_path.is_file() and result_path.is_file():
        execution = read_json(execution_path)
        summary = read_json(result_summary_path)
        if (
            not execution_completion_errors(execution, command_plan)
            and summary.get("status") == "READY_FOR_GPT_DIAGNOSIS"
        ):
            return {
                "status": "PASS",
                "failed_step": None,
                "run_dir": str(run_path),
                "primary_result": str(result_path),
                "reused_existing_run": True,
                "reused_stages": list(STAGE_ORDER),
                "result_summary": summary,
                "plan": plan,
            }

    deploy = controller.deploy()
    if deploy["status"] != "PASS":
        return {"status": "FAIL", "failed_step": "deploy", "deploy": deploy, "plan": plan}

    completed_stages = _completed_remote_stages(run_path, controller)
    runs: list[dict[str, Any]] = []
    for stage in STAGE_ORDER[len(completed_stages) :]:
        record = controller.execute("run", command_key=stage)
        runs.append(record)
        if record["status"] != "PASS":
            return {
                "status": "FAIL",
                "failed_step": stage,
                "deploy": deploy,
                "runs": runs,
                "plan": plan,
            }

    collect = controller.collect_results()
    if collect["status"] != "PASS":
        return {
            "status": "FAIL",
            "failed_step": "transfer_collect",
            "deploy": deploy,
            "runs": runs,
            "collect": collect,
            "plan": plan,
        }
    if not result_path.is_file():
        return {
            "status": "FAIL",
            "failed_step": "locate_primary_result",
            "expected_result_path": str(result_path),
            "deploy": deploy,
            "runs": runs,
            "collect": collect,
            "plan": plan,
        }

    summary = ingest_skill_results(run_path, result_path)
    final_status = "PASS" if summary["status"] == "READY_FOR_GPT_DIAGNOSIS" else "FAIL"
    return {
        "status": final_status,
        "failed_step": None if final_status == "PASS" else "skill_ingest",
        "run_dir": str(run_path),
        "primary_result": str(result_path),
        "deploy": deploy,
        "runs": runs,
        "reused_stages": completed_stages,
        "collect": collect,
        "result_summary": summary,
        "plan": plan,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="autodesign")
    subparsers = parser.add_subparsers(dest="command", required=True)

    skill_init = subparsers.add_parser("skill-init", help="Initialize a Skill-first run")
    skill_init.add_argument("input", type=Path)
    skill_init.add_argument("--output", type=Path, required=True)

    for name, help_text in (
        ("skill-status", "Inspect the current stage and artifacts"),
        ("skill-verify", "Verify current artifacts and execution facts"),
    ):
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument("run_dir", type=Path)

    skill_ingest = subparsers.add_parser(
        "skill-ingest", help="Validate scheduled observed result cells"
    )
    skill_ingest.add_argument("run_dir", type=Path)
    skill_ingest.add_argument("results", type=Path)

    skill_advance = subparsers.add_parser(
        "skill-advance", help="Advance state after required artifacts exist"
    )
    skill_advance.add_argument("run_dir", type=Path)
    skill_advance.add_argument("stage")
    skill_advance.add_argument("--changed-input", required=True)
    skill_advance.add_argument("--literal-result", required=True)

    run_local = subparsers.add_parser(
        "run-local", help="Execute the materialized local command plan"
    )
    run_local.add_argument("run_dir", type=Path)
    run_local.add_argument("--stage", choices=(*STAGE_ORDER, "all"), default="all")

    remote_validate = subparsers.add_parser(
        "remote-validate", help="Validate SSH, environment, GPU, and project facts"
    )
    remote_validate.add_argument("config", type=Path)
    remote_plan = subparsers.add_parser(
        "remote-plan", help="Render remote scripts without connecting"
    )
    remote_plan.add_argument("config", type=Path)
    remote_plan.add_argument("--output", type=Path, required=True)
    remote_plan.add_argument("--command-key", default="experiment")
    for command_name, help_text in (
        ("remote-preflight", "Check remote host tools and GPU indexes"),
        ("remote-sync", "Transfer the control and generated project"),
        ("remote-bootstrap", "Create or update the Conda environment"),
        ("remote-deploy", "Run host preflight, sync, and bootstrap"),
        ("remote-collect", "Collect declared result paths"),
        ("remote-all", "Deploy, run five stages, collect, and ingest"),
    ):
        command = subparsers.add_parser(command_name, help=help_text)
        command.add_argument("config", type=Path)
        command.add_argument("--dry-run", action="store_true")
    remote_run = subparsers.add_parser(
        "remote-run", help="Run one materialized stage on the remote host"
    )
    remote_run.add_argument("config", type=Path)
    remote_run.add_argument("--command-key", choices=STAGE_ORDER, required=True)
    remote_run.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "skill-init":
            result = initialize_skill_run(args.input, args.output)
        elif args.command == "skill-status":
            result = inspect_skill_run(args.run_dir)
        elif args.command == "skill-verify":
            result = verify_skill_run(args.run_dir)
        elif args.command == "skill-ingest":
            result = ingest_skill_results(args.run_dir, args.results)
        elif args.command == "skill-advance":
            result = advance_skill_run(
                args.run_dir,
                args.stage,
                changed_input=args.changed_input,
                literal_result=args.literal_result,
            )
        elif args.command == "run-local":
            result = run_local_commands(args.run_dir, stage=args.stage)
        else:
            controller = RemoteGPUController(args.config)
            if args.command == "remote-validate":
                result = controller.validate()
            elif args.command == "remote-plan":
                result = controller.write_plan(args.output, command_key=args.command_key)
            elif args.command == "remote-preflight":
                result = controller.execute("preflight", dry_run=args.dry_run)
            elif args.command == "remote-sync":
                result = controller.sync(dry_run=args.dry_run)
            elif args.command == "remote-bootstrap":
                result = controller.execute("bootstrap", dry_run=args.dry_run)
            elif args.command == "remote-deploy":
                result = controller.deploy(dry_run=args.dry_run)
            elif args.command == "remote-run":
                result = controller.execute(
                    "run", command_key=args.command_key, dry_run=args.dry_run
                )
            elif args.command == "remote-collect":
                result = controller.collect_results(dry_run=args.dry_run)
            else:
                result = _run_remote_all(controller, dry_run=args.dry_run)
    except (RemoteGPUError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        result = {"status": "FAIL", "error": str(error)}
    _print(result)
    if result.get("status") == "FAIL":
        raise SystemExit(2)
