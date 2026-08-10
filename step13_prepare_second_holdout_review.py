#!/usr/bin/env python3
"""Build the source-revealed human audit for holdout 002."""

from __future__ import annotations

import json
from pathlib import Path

from autobench.literature_audit import prepare_literature_audit


ROOT = Path(__file__).resolve().parent


def main() -> int:
    result = prepare_literature_audit(
        ROOT / "assets/output/untouched_holdout_2/first_run_evaluation.json",
        ROOT / "assets/output/untouched_holdout_2/human_audit",
        workspace_root=ROOT,
        display_label="Auto-Bench Untouched Holdout 002 Literature Audit",
        submission_filename="literature_audit_submission_holdout_2.json",
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
