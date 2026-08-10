#!/usr/bin/env python3
"""Validate the user's completed source-paper benchmark comparison."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from autobench.literature_audit import evaluate_literature_audit


ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="assets/output/literature_audit/literature_audit_submission.json",
    )
    parser.add_argument(
        "--scope",
        default="assets/output/literature_audit/literature_audit.json",
    )
    parser.add_argument(
        "--output",
        default="assets/output/literature_audit/final_verdict.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    submission = json.loads((ROOT / args.input).read_text(encoding="utf-8"))
    scope = json.loads((ROOT / args.scope).read_text(encoding="utf-8"))
    verdict = evaluate_literature_audit(submission, scope)
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(verdict, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(verdict, ensure_ascii=False))
    return 0 if verdict["status"] != "HUMAN_LITERATURE_AUDIT_REQUIRED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
