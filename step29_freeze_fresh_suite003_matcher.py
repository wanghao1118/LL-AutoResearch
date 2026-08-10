#!/usr/bin/env python3
"""Freeze the round-2 matcher before selecting fresh holdout suite 003."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SUITE_DIR = ROOT / "assets/input/fresh_holdout_suite_003"


def main() -> int:
    """Record the exact matcher file set and catalog size before paper selection."""

    SUITE_DIR.mkdir(parents=True, exist_ok=True)
    selection_path = SUITE_DIR / "paper_selection.json"
    if selection_path.exists():
        raise ValueError("suite003 paper selection already exists; matcher freeze must come first")

    frozen_paths = sorted((ROOT / "autobench").glob("*.py"))
    frozen_paths.extend(
        [
            ROOT / "configs/benchmark_catalog.json",
            ROOT / "step2_run_blind_matching.py",
        ]
    )
    missing = [path.as_posix() for path in frozen_paths if not path.is_file()]
    if missing:
        raise ValueError(f"missing matcher files: {missing}")

    relative_paths = [path.relative_to(ROOT).as_posix() for path in frozen_paths]
    patch = subprocess.run(
        ["git", "diff", "HEAD", "--", *relative_paths],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    patch_path = SUITE_DIR / "matcher_freeze.patch"
    patch_path.write_text(patch, encoding="utf-8")

    catalog = json.loads((ROOT / "configs/benchmark_catalog.json").read_text(encoding="utf-8"))
    payload = {
        "schema_version": "1.0",
        "suite_id": "fresh_holdout_suite_003",
        "frozen_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "validation_mode": "automatic_post_match_literature_comparison",
        "human_submission_required": False,
        "matcher_frozen_before_final_paper_selection": True,
        "paper_selection_exists_at_freeze": False,
        "source_experiment_sections_inspected": False,
        "gold_revealed": False,
        "matcher_change_policy": (
            "run all selected papers once before opening experiment/evaluation sections; "
            "post-gold changes are feedback regression only"
        ),
        "frozen_files": [
            {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size}
            for path in frozen_paths
        ],
        "matcher_patch": patch_path.relative_to(ROOT).as_posix(),
        "catalog_ids": [item["benchmark_id"] for item in catalog["benchmarks"]],
    }
    manifest_path = SUITE_DIR / "freeze_manifest.json"
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    reopened = json.loads(manifest_path.read_text(encoding="utf-8"))
    if reopened["paper_selection_exists_at_freeze"] is not False:
        raise ValueError("suite003 freeze readback failed")
    print(
        json.dumps(
            {
                "suite_id": payload["suite_id"],
                "frozen_file_count": len(frozen_paths),
                "catalog_count": len(payload["catalog_ids"]),
                "paper_selection_exists_at_freeze": False,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
