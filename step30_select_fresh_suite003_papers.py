#!/usr/bin/env python3
"""Finalize fresh suite 003 using official arXiv titles and abstracts only."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SUITE_DIR = ROOT / "assets/input/fresh_holdout_suite_003"
FREEZE_MANIFEST = SUITE_DIR / "freeze_manifest.json"
SELECTION_PATH = SUITE_DIR / "paper_selection.json"


PAPERS = [
    {
        "case_id": "fresh3_001",
        "arxiv_id": "2302.04761",
        "title": "Toolformer: Language Models Can Teach Themselves to Use Tools",
        "source_url": "https://arxiv.org/abs/2302.04761",
        "selection_reason": "self-supervised API use across diverse downstream language tasks",
    },
    {
        "case_id": "fresh3_002",
        "arxiv_id": "2209.11302",
        "title": "ProgPrompt: Generating Situated Robot Task Plans using Large Language Models",
        "source_url": "https://arxiv.org/abs/2209.11302",
        "selection_reason": "programmatic robot planning in simulated household and physical tabletop settings",
    },
    {
        "case_id": "fresh3_003",
        "arxiv_id": "2211.11559",
        "title": "Visual Programming: Compositional visual reasoning without training",
        "source_url": "https://arxiv.org/abs/2211.11559",
        "selection_reason": "program-generated composition for four distinct visual reasoning applications",
    },
    {
        "case_id": "fresh3_004",
        "arxiv_id": "2211.12588",
        "title": "Program of Thoughts Prompting: Disentangling Computation from Reasoning for Numerical Reasoning Tasks",
        "source_url": "https://arxiv.org/abs/2211.12588",
        "selection_reason": "program-executed numerical reasoning over math and financial question answering",
    },
    {
        "case_id": "fresh3_005",
        "arxiv_id": "2305.10601",
        "title": "Tree of Thoughts: Deliberate Problem Solving with Large Language Models",
        "source_url": "https://arxiv.org/abs/2305.10601",
        "selection_reason": "search-based reasoning over planning, puzzle, and creative-generation tasks",
    },
]


def main() -> int:
    """Verify freeze order, write selection, and preserve the sealed-gold state."""

    freeze = json.loads(FREEZE_MANIFEST.read_text(encoding="utf-8"))
    if freeze.get("matcher_frozen_before_final_paper_selection") is not True:
        raise ValueError("matcher freeze is not confirmed")
    if freeze.get("paper_selection_exists_at_freeze") is not False:
        raise ValueError("paper selection did not follow matcher freeze")
    if freeze.get("source_experiment_sections_inspected") is not False:
        raise ValueError("experiment sections were already inspected")
    if SELECTION_PATH.exists():
        raise ValueError("suite003 paper selection already exists")

    payload = {
        "schema_version": "1.0",
        "suite_id": "fresh_holdout_suite_003",
        "selection_finalized_after_matcher_freeze": True,
        "selection_frozen_before_source_experiment_inspection": True,
        "selection_input": ["official arXiv title", "official arXiv abstract"],
        "exclusions": [
            "all suite001 and suite002 papers",
            "papers used in previous holdouts",
            "pure benchmark papers",
            "surveys",
        ],
        "coverage_goal": [
            "tool-augmented language modeling",
            "situated robot planning",
            "visual program execution",
            "numerical program reasoning",
            "search-based general problem solving",
        ],
        "papers": PAPERS,
        "gold_state": "SEALED_NOT_CONSTRUCTED",
    }
    SELECTION_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

    freeze.update(
        {
            "paper_selection": SELECTION_PATH.relative_to(ROOT).as_posix(),
            "paper_selection_finalized_after_freeze": True,
            "paper_ids": [paper["arxiv_id"] for paper in PAPERS],
            "gold_revealed": False,
        }
    )
    FREEZE_MANIFEST.write_text(json.dumps(freeze, ensure_ascii=False, indent=2) + "\n")
    reopened = json.loads(SELECTION_PATH.read_text(encoding="utf-8"))
    if reopened["gold_state"] != "SEALED_NOT_CONSTRUCTED" or len(reopened["papers"]) != 5:
        raise ValueError("suite003 selection readback failed")
    print(
        json.dumps(
            {
                "suite_id": payload["suite_id"],
                "paper_ids": [paper["arxiv_id"] for paper in PAPERS],
                "gold_state": payload["gold_state"],
                "human_submission_required": False,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
