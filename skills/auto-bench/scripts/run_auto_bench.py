#!/usr/bin/env python3
"""Portable command runner bundled with the Auto-Bench Codex Skill."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
DEFAULT_CATALOG = SKILL_ROOT / "assets/benchmark_catalog.json"
sys.path.insert(0, str(SCRIPT_DIR))

from autobench.models import MethodInput  # noqa: E402
from autobench.pipeline import AutoBenchPipeline  # noqa: E402
from autobench.workflow import SYNTHESIS_TRANSFORMATIONS, run_workflow  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    """Create a small portable CLI for the two skill execution modes."""

    parser = argparse.ArgumentParser(
        description="Generate or execute an Introduction/Method-only Auto-Bench plan."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    match = subparsers.add_parser("match", help="generate a benchmark portfolio and route")
    match.add_argument("--input", required=True, help="matcher-visible JSON input")
    match.add_argument("--output", required=True, help="output directory")
    match.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    match.add_argument("--online", action="store_true", help="query official arXiv metadata")

    run = subparsers.add_parser(
        "run",
        help="generate the plan and execute adaptation/synthesis when source records are supplied",
    )
    run.add_argument("--input", required=True)
    run.add_argument("--output", required=True)
    run.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    run.add_argument("--online", action="store_true")
    run.add_argument("--base-records", help="train/development JSONL source records")
    run.add_argument("--source-benchmark")
    run.add_argument("--source-split")
    run.add_argument(
        "--transformation",
        action="append",
        choices=SYNTHESIS_TRANSFORMATIONS,
        help="repeat to execute multiple synthesis modules",
    )
    return parser


def load_input(path: str | Path) -> MethodInput:
    """Load and validate the strict matcher-visible input record."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return MethodInput.from_dict(payload)


def main(argv: list[str] | None = None) -> int:
    """Run the requested Skill operation and emit a compact machine-readable summary."""

    args = build_parser().parse_args(argv)
    method_input = load_input(args.input)
    if args.command == "match":
        pipeline = AutoBenchPipeline(args.catalog)
        plan = pipeline.run(method_input, online_search=args.online)
        paths = pipeline.write_outputs(plan, args.output)
        print(
            json.dumps(
                {
                    "case_id": plan.case_id,
                    "status": plan.status,
                    "route": plan.route,
                    "coverage_ratio": plan.coverage_ratio,
                    "selected_benchmarks": plan.selected_benchmarks,
                    "uncovered_task_families": plan.profile.uncovered_task_families,
                    "human_submission_required": False,
                    "outputs": {key: str(value.resolve()) for key, value in paths.items()},
                },
                ensure_ascii=False,
            )
        )
        return 0

    manifest = run_workflow(
        method_input,
        args.catalog,
        args.output,
        online_search=args.online,
        base_records_path=args.base_records,
        source_benchmark=args.source_benchmark,
        source_split=args.source_split,
        transformations=args.transformation,
    )
    print(json.dumps(manifest, ensure_ascii=False))
    return 2 if manifest["synthesis_execution"]["status"] == "BASE_RECORDS_REQUIRED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
