"""Thin CLI for Skill-first AutoDesign state, execution, and result facts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .effects import check_design, compare_effects
from .runner import STAGE_ORDER, run_local_commands
from .skillflow import (
    advance_skill_run,
    initialize_skill_run,
    repair_skill_state,
)
from .skillresults import ingest_skill_results


def _print(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="autodesign")
    subparsers = parser.add_subparsers(dest="command", required=True)

    skill_init = subparsers.add_parser("skill-init", help="Initialize a Skill-first run")
    skill_init.add_argument("input", type=Path)
    skill_init.add_argument("--output", type=Path, required=True)

    for name, help_text in (
        ("skill-repair-state", "Canonicalize and refresh AUTODESIGN_STATE.md"),
        ("skill-check-design", "Validate the structural experiment-design contract"),
        ("skill-compare-effects", "Compare observed results against simulated targets"),
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

    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "skill-init":
            result = initialize_skill_run(args.input, args.output)
        elif args.command == "skill-repair-state":
            result = repair_skill_state(args.run_dir)
        elif args.command == "skill-check-design":
            result = check_design(args.run_dir)
        elif args.command == "skill-compare-effects":
            result = compare_effects(args.run_dir)
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
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        result = {"status": "FAIL", "error": str(error)}
    _print(result)
    if result.get("status") == "FAIL":
        raise SystemExit(2)
