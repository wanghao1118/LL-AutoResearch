#!/usr/bin/env python3
"""Create a separate source-revealed audit for the untouched holdout."""

from __future__ import annotations

import json
from pathlib import Path

from autobench.iteration_report import write_iteration_report
from autobench.literature_audit import prepare_literature_audit


ROOT = Path(__file__).resolve().parent


def main() -> int:
    output_root = ROOT / "assets/output/untouched_holdout"
    audit_root = output_root / "human_audit"
    history_root = output_root / "human_audit_history/round_1"
    comparison = write_iteration_report(
        history_root / "blind_evaluation.json",
        output_root / "latest_evaluation.json",
        history_root / "final_verdict.json",
        audit_root / "iteration_comparison.json",
        audit_root / "iteration_comparison.md",
        previous_iteration=1,
        current_iteration=2,
    )
    for stale_name in (
        "final_verdict.json",
        "literature_audit_submission_holdout_1.json",
    ):
        (audit_root / stale_name).unlink(missing_ok=True)
    result = prepare_literature_audit(
        output_root / "latest_evaluation.json",
        audit_root,
        workspace_root=ROOT,
        display_label="Auto-Bench Untouched Holdout Literature Audit — Round 2",
        submission_filename="literature_audit_submission_holdout_1_round_2.json",
        iteration=2,
        iteration_comparison=comparison,
        prior_audit_path=history_root / "literature_audit.json",
        prior_submission_path=history_root / "literature_audit_submission_holdout_1.json",
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
