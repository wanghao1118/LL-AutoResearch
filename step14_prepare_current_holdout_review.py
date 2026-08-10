#!/usr/bin/env python3
"""Build the human audit for the current post-feedback holdout-002 plan."""

from __future__ import annotations

import json
from pathlib import Path

from autobench.iteration_report import write_iteration_report
from autobench.literature_audit import prepare_literature_audit


ROOT = Path(__file__).resolve().parent


def main() -> int:
    output_root = ROOT / "assets/output/untouched_holdout_2"
    audit_root = output_root / "current_human_audit"
    history_root = output_root / "current_human_audit_history/round_1"
    comparison = write_iteration_report(
        history_root / "blind_evaluation.json",
        output_root / "post_admission_evaluation.json",
        history_root / "final_verdict.json",
        audit_root / "iteration_comparison.json",
        audit_root / "iteration_comparison.md",
        previous_iteration=1,
        current_iteration=2,
    )
    for stale_name in (
        "final_verdict.json",
        "literature_audit_submission_holdout_2_current.json",
    ):
        (audit_root / stale_name).unlink(missing_ok=True)
    result = prepare_literature_audit(
        output_root / "post_admission_evaluation.json",
        audit_root,
        workspace_root=ROOT,
        display_label="Auto-Bench Current Holdout 002 Literature Audit — Round 2",
        submission_filename="literature_audit_submission_holdout_2_round_2.json",
        iteration=2,
        iteration_comparison=comparison,
        prior_audit_path=history_root / "literature_audit.json",
        prior_submission_path=history_root / "literature_audit_submission_holdout_2_current.json",
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
