#!/usr/bin/env python3
"""Prepare the source-revealed human audit after blind matching finishes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from autobench.literature_audit import prepare_literature_audit


ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation", default="assets/output/blind_evaluation.json")
    parser.add_argument("--output-dir", default="assets/output/literature_audit")
    parser.add_argument("--comparison", default="assets/output/literature_audit/iteration_comparison.json")
    parser.add_argument("--iteration", type=int)
    parser.add_argument("--prior-audit")
    parser.add_argument("--prior-submission")
    parser.add_argument("--case-id", action="append", dest="case_ids")
    parser.add_argument("--display-label")
    parser.add_argument("--submission-filename")
    return parser.parse_args()


def _path(raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else ROOT / path


def main() -> int:
    """Reveal paper identity and gold benchmarks only in the post-run audit."""

    args = parse_args()
    evaluation_path = _path(args.evaluation)
    if not evaluation_path.is_file():
        raise ValueError("blind evaluation is missing; run step3_evaluate_blind_results.py first")
    comparison_path = _path(args.comparison)
    comparison = (
        json.loads(comparison_path.read_text(encoding="utf-8"))
        if comparison_path.is_file()
        else None
    )
    iteration = args.iteration or int(comparison.get("current_iteration", 2) if comparison else 1)
    prior_audit_path = _path(args.prior_audit) if args.prior_audit else None
    prior_submission_path = _path(args.prior_submission) if args.prior_submission else None
    if comparison and prior_audit_path is None and prior_submission_path is None:
        previous_iteration = int(comparison.get("previous_iteration", 1))
        history = ROOT / f"assets/output/literature_audit/history/round_{previous_iteration}"
        prior_audit_path = history / "literature_audit.json"
        submissions = sorted(history.glob("literature_audit_submission*.json"))
        if len(submissions) != 1:
            raise ValueError(f"expected one prior submission in {history}, found {len(submissions)}")
        prior_submission_path = submissions[0]
    result = prepare_literature_audit(
        evaluation_path,
        _path(args.output_dir),
        workspace_root=ROOT,
        iteration=iteration,
        iteration_comparison=comparison,
        prior_audit_path=prior_audit_path,
        prior_submission_path=prior_submission_path,
        case_ids=args.case_ids,
        display_label=args.display_label,
        submission_filename=args.submission_filename,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
