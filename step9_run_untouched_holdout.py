#!/usr/bin/env python3
"""Execute and preserve the first frozen holdout result without matcher tuning."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_ROOT = ROOT / "assets/output/untouched_holdout"
FIRST_RUN = OUTPUT_ROOT / "first_run_evaluation.json"


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


def preserve_first_run(evaluation_path: Path, report_path: Path, evaluation_exit_status: int) -> dict:
    """Freeze an already-produced evaluation without invoking the matcher again."""

    payload = json.loads(evaluation_path.read_text(encoding="utf-8"))
    if not FIRST_RUN.exists():
        shutil.copy2(evaluation_path, FIRST_RUN)
        shutil.copy2(report_path, OUTPUT_ROOT / "first_run_evaluation.md")
        record = {
            "schema_version": "1.0",
            "case_ids": [case["case_id"] for case in payload["cases"]],
            "fixture_frozen_before_first_matching": True,
            "matcher_changed_after_gold_reveal": False,
            "evaluation_exit_status": evaluation_exit_status,
            "first_run_verdict": payload["verdict"],
            "first_run_evaluation": "assets/output/untouched_holdout/first_run_evaluation.json",
        }
        (OUTPUT_ROOT / "first_run_record.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return payload


def main() -> int:
    """Run the gold-free worker first, then open gold in the evaluator process."""

    args = parse_args()
    if FIRST_RUN.exists() and not args.replay:
        raise ValueError("first holdout result already exists; use --replay for a non-first-run regression")
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    runs_dir = "assets/output/untouched_holdout/runs"
    evaluation = "assets/output/untouched_holdout/latest_evaluation.json"
    report = "assets/output/untouched_holdout/latest_evaluation.md"
    _run(
        [
            sys.executable,
            "step2_run_blind_matching.py",
            "--cases-dir",
            "assets/input/untouched_holdout_cases",
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
            "assets/input/untouched_holdout_gold",
            "--matcher-cases-dir",
            "assets/input/untouched_holdout_cases",
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
    payload = preserve_first_run(evaluation_path, ROOT / report, evaluation_exit_status)
    print(json.dumps({"first_run_preserved": FIRST_RUN.is_file(), **payload["aggregate"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
