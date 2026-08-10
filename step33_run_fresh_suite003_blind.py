#!/usr/bin/env python3
"""Run frozen fresh suite 003 once before opening experiment evidence."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SUITE_ROOT = ROOT / "assets/input/fresh_holdout_suite_003"
CASES_DIR = SUITE_ROOT / "cases"
GOLD_DIR = SUITE_ROOT / "gold"
RUNS_DIR = ROOT / "assets/output/fresh_holdout_suite_003/blind_runs"
RECORD_PATH = ROOT / "assets/output/fresh_holdout_suite_003/pre_gold_run_record.json"


def main() -> int:
    """Verify freeze invariants, run gold-free workers, and seal their manifest."""

    freeze = json.loads((SUITE_ROOT / "freeze_manifest.json").read_text(encoding="utf-8"))
    cases_freeze = json.loads((CASES_DIR / "freeze_manifest.json").read_text(encoding="utf-8"))
    if freeze.get("gold_revealed") or GOLD_DIR.exists():
        raise ValueError("suite003 gold was revealed before the first blind run")
    if cases_freeze.get("gold_directory_exists") is not False:
        raise ValueError("suite003 case manifest does not confirm absent gold")
    changed_sizes = []
    for item in freeze["frozen_files"]:
        path = ROOT / item["path"]
        current = path.stat().st_size
        if current != item["bytes"]:
            changed_sizes.append({"path": item["path"], "frozen": item["bytes"], "current": current})
    if changed_sizes:
        raise ValueError(f"frozen suite003 matcher files changed: {changed_sizes}")

    command = [
        "python3",
        "step2_run_blind_matching.py",
        "--cases-dir",
        str(CASES_DIR.relative_to(ROOT)),
        "--case-pattern",
        "fresh3_*.json",
        "--output-dir",
        str(RUNS_DIR.relative_to(ROOT)),
    ]
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="")
    if completed.returncode != 0:
        return completed.returncode

    manifest_path = RUNS_DIR / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if any(case["hidden_labels_present_in_sandbox"] for case in manifest["cases"]):
        raise ValueError("hidden labels appeared in a suite003 matcher sandbox")
    case_ids = [case["case_id"] for case in manifest["cases"]]
    if case_ids != sorted(cases_freeze["case_ids"]):
        raise ValueError(f"suite003 run case mismatch: {case_ids}")

    record = {
        "schema_version": "1.0",
        "suite_id": freeze["suite_id"],
        "command": command,
        "exit_status": completed.returncode,
        "blind_run_completed_before_gold": True,
        "matcher_frozen_file_sizes_unchanged": True,
        "gold_directory_existed_during_run": False,
        "case_count": len(manifest["cases"]),
        "all_worker_exit_statuses_zero": all(
            case["worker_exit_status"] == 0 for case in manifest["cases"]
        ),
        "all_sandboxes_excluded_hidden_labels": all(
            not case["hidden_labels_present_in_sandbox"] for case in manifest["cases"]
        ),
        "run_manifest": manifest_path.relative_to(ROOT).as_posix(),
        "matcher_and_paper_selection_frozen_before_source_method_reading": True,
        "source_experiment_content_inspected_before_run": False,
        "worker_visible_fields": ["case_id", "introduction", "method", "constraints"],
    }
    RECORD_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECORD_PATH.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    json.loads(RECORD_PATH.read_text(encoding="utf-8"))
    print(json.dumps(record, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
