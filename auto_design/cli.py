"""Thin CLI for prompt-driven AutoDesign state, execution, and result facts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .effects import check_design, compare_effects
from .results import ingest_results
from .runner import STAGE_ORDER, run_local_commands
from .state import (
    advance_run,
    initialize_run,
    repair_state,
)


def _print(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="auto_design")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Initialize a prompt-driven run")
    init.add_argument("input", type=Path)
    init.add_argument("--output", type=Path, required=True)

    for name, help_text in (
        ("repair-state", "Canonicalize and refresh AUTODESIGN_STATE.md"),
        ("check-design", "Validate the structural experiment-design contract"),
        ("compare-effects", "Compare observed results against simulated targets"),
    ):
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument("run_dir", type=Path)

    ingest = subparsers.add_parser("ingest", help="Validate scheduled observed result cells")
    ingest.add_argument("run_dir", type=Path)
    ingest.add_argument("results", type=Path)

    advance = subparsers.add_parser("advance", help="Advance state after required artifacts exist")
    advance.add_argument("run_dir", type=Path)
    advance.add_argument("stage")
    advance.add_argument("--changed-input", required=True)
    advance.add_argument("--literal-result", required=True)

    run_local = subparsers.add_parser(
        "run-local", help="Execute the materialized local command plan"
    )
    run_local.add_argument("run_dir", type=Path)
    run_local.add_argument("--stage", choices=(*STAGE_ORDER, "all"), default="all")

    serve = subparsers.add_parser("serve", help="Start the native HTML/Python workspace")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8767)
    serve.add_argument("--workspace", type=Path, default=Path.cwd())
    serve.add_argument("--data-dir", type=Path)

    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "serve":
        from .web.serve import main as serve_main

        options = [
            "--host",
            args.host,
            "--port",
            str(args.port),
            "--workspace",
            str(args.workspace),
        ]
        if args.data_dir:
            options.extend(["--data-dir", str(args.data_dir)])
        serve_main(options)
        return
    try:
        if args.command == "init":
            result = initialize_run(args.input, args.output)
        elif args.command == "repair-state":
            result = repair_state(args.run_dir)
        elif args.command == "check-design":
            result = check_design(args.run_dir)
        elif args.command == "compare-effects":
            result = compare_effects(args.run_dir)
        elif args.command == "ingest":
            result = ingest_results(args.run_dir, args.results)
        elif args.command == "advance":
            result = advance_run(
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
