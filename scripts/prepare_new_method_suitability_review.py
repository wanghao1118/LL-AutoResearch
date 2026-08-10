#!/usr/bin/env python3
"""Prepare independent construct-suitability review for a new method plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from autobench.review_workflow import prepare_review_bundle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--plan",
        action="append",
        required=True,
        help="benchmark_plan.json; repeat to review multiple plans in one frozen scope",
    )
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def main() -> int:
    """Freeze the supplied plan scope and create two isolated reviewer packets."""

    args = parse_args()
    plan_paths = [ROOT / path for path in args.plan]
    missing = [path.as_posix() for path in plan_paths if not path.is_file()]
    if missing:
        raise ValueError(f"benchmark plans are missing: {missing}")
    result = prepare_review_bundle(plan_paths, ROOT / args.output_dir)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
