#!/usr/bin/env python3
"""Run frozen fresh suite 002 once before constructing literature gold."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SUITE_ROOT = ROOT / "assets/input/fresh_holdout_suite_002"
CASES_DIR = SUITE_ROOT / "cases"
GOLD_DIR = SUITE_ROOT / "gold"
RUNS_DIR = ROOT / "assets/output/fresh_holdout_suite_002/blind_runs"
RECORD_PATH = ROOT / "assets/output/fresh_holdout_suite_002/pre_gold_run_record.json"


def main() -> int:
    freeze = json.loads((SUITE_ROOT / "freeze_manifest.json").read_text(encoding="utf-8"))
    cases_freeze = json.loads((CASES_DIR / "freeze_manifest.json").read_text(encoding="utf-8"))
    if freeze.get("gold_revealed") or GOLD_DIR.exists():
        raise ValueError("suite002 gold was revealed before the first blind run")
    if cases_freeze.get("gold_directory_exists") is not False:
        raise ValueError("suite002 case manifest does not confirm absent gold")
    changed_sizes = []
    for item in freeze["frozen_files"]:
        path = ROOT / item["path"]
        current = path.stat().st_size
        if current != item["bytes"]:
            changed_sizes.append({"path": item["path"], "frozen": item["bytes"], "current": current})
    if changed_sizes:
        raise ValueError(f"frozen suite002 matcher files changed: {changed_sizes}")

    command = [
        "python3",
        "step2_run_blind_matching.py",
        "--cases-dir",
        str(CASES_DIR.relative_to(ROOT)),
        "--case-pattern",
        "fresh2_*.json",
        "--output-dir",
        str(RUNS_DIR.relative_to(ROOT)),
    ]
    manifest_path = RUNS_DIR / "run_manifest.json"
    reused_completed_run = manifest_path.is_file()
    if reused_completed_run:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
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
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if any(case["hidden_labels_present_in_sandbox"] for case in manifest["cases"]):
        raise ValueError("hidden labels appeared in a suite002 matcher sandbox")
    case_ids = [case["case_id"] for case in manifest["cases"]]
    if case_ids != sorted(cases_freeze["case_ids"]):
        raise ValueError(f"suite002 run case mismatch: {case_ids}")

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
        "run_manifest": manifest_path.relative_to(ROOT).as_posix(),
        "meta_agent_had_seen_some_experiment_text_before_run": True,
        "matcher_and_selection_were_frozen_before_that_inspection": True,
        "worker_visible_fields": ["case_id", "introduction", "method", "constraints"],
    }
    RECORD_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECORD_PATH.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    json.loads(RECORD_PATH.read_text())
    print(json.dumps(record, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
