#!/usr/bin/env python3
"""Run and preserve the first post-revision result on holdout 002."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_ROOT = ROOT / "assets/output/untouched_holdout_2"
FIRST_RUN = OUTPUT_ROOT / "first_run_evaluation.json"
FREEZE_MANIFEST = ROOT / "assets/input/untouched_holdout_2_cases/freeze_manifest.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay", action="store_true")
    return parser.parse_args()


def _run(command: list[str], accepted_statuses: tuple[int, ...] = (0,)) -> int:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    if completed.returncode not in accepted_statuses:
        raise RuntimeError(f"holdout command failed with status {completed.returncode}: {command}")
    return completed.returncode


def main() -> int:
    """Execute gold-free matching, reveal gold afterward, and freeze the result."""

    args = parse_args()
    if FIRST_RUN.exists() and not args.replay:
        raise ValueError("second holdout first result already exists; use --replay for regression")
    freeze = json.loads(FREEZE_MANIFEST.read_text(encoding="utf-8"))
    if not freeze["fixture_frozen_before_matcher_revision"]:
        raise ValueError("holdout 002 is not declared frozen before the matcher revision")
    if not freeze["matcher_has_not_seen_holdout_002_gold"] and not args.replay:
        raise ValueError("holdout 002 gold boundary is not intact")

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    runs_dir = "assets/output/untouched_holdout_2/runs"
    evaluation = "assets/output/untouched_holdout_2/latest_evaluation.json"
    report = "assets/output/untouched_holdout_2/latest_evaluation.md"
    _run(
        [
            sys.executable,
            "step2_run_blind_matching.py",
            "--cases-dir",
            "assets/input/untouched_holdout_2_cases",
            "--case-pattern",
            "holdout_*.json",
            "--output-dir",
            runs_dir,
        ]
    )
    evaluation_exit_status = _run(
        [
            sys.executable,
            "step3_evaluate_blind_results.py",
            "--runs-dir",
            runs_dir,
            "--gold-dir",
            "assets/input/untouched_holdout_2_gold",
            "--matcher-cases-dir",
            "assets/input/untouched_holdout_2_cases",
            "--output",
            evaluation,
            "--report",
            report,
            "--minimum-cases",
            "1",
        ],
        accepted_statuses=(0, 1),
    )
    evaluation_path = ROOT / evaluation
    payload = json.loads(evaluation_path.read_text(encoding="utf-8"))
    if not FIRST_RUN.exists():
        shutil.copy2(evaluation_path, FIRST_RUN)
        shutil.copy2(ROOT / report, OUTPUT_ROOT / "first_run_evaluation.md")
        record = {
            "schema_version": "1.0",
            "case_ids": [case["case_id"] for case in payload["cases"]],
            "fixture_frozen_before_matcher_revision": True,
            "matcher_revision_basis": freeze["revision_basis"],
            "matcher_changed_after_holdout_002_gold_reveal": False,
            "evaluation_exit_status": evaluation_exit_status,
            "first_run_verdict": payload["verdict"],
            "first_run_evaluation": "assets/output/untouched_holdout_2/first_run_evaluation.json",
        }
        (OUTPUT_ROOT / "first_run_record.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps({"first_run_preserved": FIRST_RUN.is_file(), **payload["aggregate"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
