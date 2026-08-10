#!/usr/bin/env python3
"""Run automatic source-paper benchmark comparison after blind evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from autobench.auto_literature_review import write_review


ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-markdown", required=True)
    parser.add_argument(
        "--evidence-class",
        choices=("feedback_regression", "untouched_holdout", "fresh_holdout"),
        required=True,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = write_review(
        ROOT / args.evaluation,
        ROOT / args.output_json,
        ROOT / args.output_markdown,
        evidence_class=args.evidence_class,
    )
    print(
        json.dumps(
            {
                "status": payload["status"],
                "case_count": payload["case_count"],
                "decision_counts": payload["decision_counts"],
                "human_submission_required": False,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
