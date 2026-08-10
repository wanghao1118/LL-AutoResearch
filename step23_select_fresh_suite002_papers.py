#!/usr/bin/env python3
"""Finalize fresh suite 002 from official titles and abstracts only."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SUITE_DIR = ROOT / "assets/input/fresh_holdout_suite_002"
FREEZE_MANIFEST = SUITE_DIR / "freeze_manifest.json"
SELECTION_PATH = SUITE_DIR / "paper_selection.json"


PAPERS = [
    {
        "case_id": "fresh2_001",
        "arxiv_id": "2211.10435",
        "title": "PAL: Program-aided Language Models",
        "source_url": "https://arxiv.org/abs/2211.10435",
        "selection_reason": "program-execution reasoning across mathematical, symbolic, and algorithmic tasks",
    },
    {
        "case_id": "fresh2_002",
        "arxiv_id": "2305.18323",
        "title": "ReWOO: Decoupling Reasoning from Observations for Efficient Augmented Language Models",
        "source_url": "https://arxiv.org/abs/2305.18323",
        "selection_reason": "tool-augmented language modeling with retrieval, action, efficiency, and tool-failure claims",
    },
    {
        "case_id": "fresh2_003",
        "arxiv_id": "2207.05608",
        "title": "Inner Monologue: Embodied Reasoning through Planning with Language Models",
        "source_url": "https://arxiv.org/abs/2207.05608",
        "selection_reason": "closed-loop language feedback for simulated and real robot manipulation",
    },
    {
        "case_id": "fresh2_004",
        "arxiv_id": "2304.11477",
        "title": "LLM+P: Empowering Large Language Models with Optimal Planning Proficiency",
        "source_url": "https://arxiv.org/abs/2304.11477",
        "selection_reason": "natural-language-to-PDDL planning over diverse classical-planning scenarios",
    },
    {
        "case_id": "fresh2_005",
        "arxiv_id": "2303.08128",
        "title": "ViperGPT: Visual Inference via Python Execution for Reasoning",
        "source_url": "https://arxiv.org/abs/2303.08128",
        "selection_reason": "code-generated composition of vision-language modules for complex visual tasks",
    },
]


def main() -> int:
    freeze = json.loads(FREEZE_MANIFEST.read_text(encoding="utf-8"))
    if freeze.get("matcher_frozen_before_final_paper_selection") is not True:
        raise ValueError("matcher freeze is not confirmed")
    if freeze.get("paper_selection_exists_at_freeze") is not False:
        raise ValueError("paper selection did not follow matcher freeze")
    if freeze.get("source_experiment_sections_inspected") is not False:
        raise ValueError("experiment sections were already inspected")
    if SELECTION_PATH.exists():
        raise ValueError("suite002 paper selection already exists")

    payload = {
        "schema_version": "1.0",
        "suite_id": "fresh_holdout_suite_002",
        "selection_finalized_after_matcher_freeze": True,
        "selection_frozen_before_source_experiment_inspection": True,
        "selection_input": ["official arXiv title", "official arXiv abstract"],
        "abstract_evidence_logs": [
            "assets/log/fresh_suite002_abstract_preselection_html.log",
            "assets/log/fresh_suite002_fifth_candidate_abstract.log",
        ],
        "exclusions": [
            "all suite001 and previous holdout papers",
            "papers used in earlier feedback regression",
            "pure benchmark papers",
            "surveys",
        ],
        "coverage_goal": [
            "program-aided mathematical reasoning",
            "tool-augmented NLP",
            "embodied robotic planning",
            "classical planning",
            "visual program execution",
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
    reopened = json.loads(SELECTION_PATH.read_text())
    if reopened["gold_state"] != "SEALED_NOT_CONSTRUCTED" or len(reopened["papers"]) != 5:
        raise ValueError("suite002 selection readback failed")
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
