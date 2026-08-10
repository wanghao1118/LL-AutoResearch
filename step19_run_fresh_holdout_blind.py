#!/usr/bin/env python3
"""Run the frozen five-paper suite once while experiment gold is absent."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SUITE_ROOT = ROOT / "assets/input/fresh_holdout_suite"
CASES_DIR = SUITE_ROOT / "cases"
GOLD_DIR = SUITE_ROOT / "gold"
RUNS_DIR = ROOT / "assets/output/fresh_holdout_suite/blind_runs"


def main() -> int:
    freeze = json.loads((SUITE_ROOT / "freeze_manifest.json").read_text())
    if freeze["gold_revealed"] or GOLD_DIR.exists():
        raise ValueError("fresh-suite gold was revealed before the first blind run")
    changed_sizes = []
    for item in freeze["frozen_files"]:
        path = ROOT / item["path"]
        current = path.stat().st_size
        if current != item["bytes"]:
            changed_sizes.append({"path": item["path"], "frozen": item["bytes"], "current": current})
    if changed_sizes:
        raise ValueError(f"frozen matcher files changed: {changed_sizes}")
    command = [
        "python3",
        "step2_run_blind_matching.py",
        "--cases-dir",
        str(CASES_DIR.relative_to(ROOT)),
        "--case-pattern",
        "fresh_*.json",
        "--output-dir",
        str(RUNS_DIR.relative_to(ROOT)),
    ]
    manifest_path = RUNS_DIR / "run_manifest.json"
    reused_completed_run = manifest_path.is_file()
    if reused_completed_run:
        manifest = json.loads(manifest_path.read_text())
        process_returncode = 0
    else:
        completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        if completed.stdout:
            print(completed.stdout, end="")
        if completed.stderr:
            print(completed.stderr, end="")
        if completed.returncode != 0:
            return completed.returncode
        process_returncode = completed.returncode
        manifest = json.loads(manifest_path.read_text())
    if any(case["hidden_labels_present_in_sandbox"] for case in manifest["cases"]):
        raise ValueError("hidden labels appeared in a fresh-suite matcher sandbox")
    record = {
        "schema_version": "1.0",
        "suite_id": freeze["suite_id"],
        "command": command,
        "exit_status": process_returncode,
        "reused_completed_blind_run_for_record_repair": reused_completed_run,
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
        "run_manifest": "assets/output/fresh_holdout_suite/blind_runs/run_manifest.json",
    }
    path = ROOT / "assets/output/fresh_holdout_suite/pre_gold_run_record.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    json.loads(path.read_text())
    print(json.dumps(record, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
