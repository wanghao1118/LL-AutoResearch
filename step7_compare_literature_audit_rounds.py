#!/usr/bin/env python3
"""Write the Round 1 human-feedback to Round 2 matcher-change report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from autobench.iteration_report import write_iteration_report


ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--previous-evaluation",
        default="assets/output/literature_audit/history/round_1/blind_evaluation.json",
    )
    parser.add_argument(
        "--current-evaluation",
        default="assets/output/blind_evaluation.json",
    )
    parser.add_argument(
        "--previous-verdict",
        default="assets/output/literature_audit/history/round_1/final_verdict.json",
    )
    parser.add_argument(
        "--output-json",
        default="assets/output/literature_audit/iteration_comparison.json",
    )
    parser.add_argument(
        "--output-markdown",
        default="assets/output/literature_audit/iteration_comparison.md",
    )
    parser.add_argument("--previous-iteration", type=int, default=1)
    parser.add_argument("--current-iteration", type=int, default=2)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = write_iteration_report(
        ROOT / args.previous_evaluation,
        ROOT / args.current_evaluation,
        ROOT / args.previous_verdict,
        ROOT / args.output_json,
        ROOT / args.output_markdown,
        previous_iteration=args.previous_iteration,
        current_iteration=args.current_iteration,
    )
    print(json.dumps(payload["aggregate"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
