#!/usr/bin/env python3
"""Freeze a second untouched paper before the holdout-001-driven revision."""

from __future__ import annotations

import json
from pathlib import Path

from autobench.catalog import load_catalog
from step1_build_blind_fixtures import build_fixture


ROOT = Path(__file__).resolve().parent
CATALOG_PATH = ROOT / "configs/benchmark_catalog.json"
CASES_DIR = ROOT / "assets/input/untouched_holdout_2_cases"
GOLD_DIR = ROOT / "assets/input/untouched_holdout_2_gold"


HOLDOUT_SPEC = {
    "case_id": "holdout_002",
    "introduction_files": ["assets/input/source_papers/extracted/2305.11738/sections/1_intro.tex"],
    "method_files": ["assets/input/source_papers/extracted/2305.11738/sections/3_method.tex"],
    "identity_markers": [
        "CRITIC",
        "Self-Correcting with Tool-Interactive Critiquing",
        "Large Language Models Can Self-Correct with Tool-Interactive Critiquing",
        "Gou et al.",
    ],
    "hidden_benchmark_aliases": [
        "AmbigNQ",
        "Ambig NQ",
        "TriviaQA",
        "Trivia QA",
        "SVAMP",
        "TabMWP",
        "Tab MWP",
        "RealToxicityPrompts",
        "Real Toxicity Prompts",
    ],
    "identity_replacements": {
        "\\modelt": "METHOD_X",
        "\\model": "METHOD_X",
        "CRITIC": "METHOD_X",
        "Self-Correcting with Tool-Interactive Critiquing": "METHOD_X",
        "Large Language Models Can Self-Correct with Tool-Interactive Critiquing": "METHOD_X",
    },
    "gold": {
        "source_arxiv_id": "2305.11738",
        "source_title": "CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing",
        "source_url": "https://arxiv.org/abs/2305.11738",
        "source_input_sections": {
            "introduction": ["Introduction"],
            "method": ["CRITIC: Correcting with Tool-Interactive Critiquing"],
        },
        "primary_benchmark_ids": ["hotpotqa", "gsm8k"],
        "secondary_benchmark_ids": [],
        "unmodeled_benchmarks": [
            "AmbigNQ",
            "TriviaQA",
            "SVAMP",
            "TabMWP",
            "RealToxicityPrompts",
        ],
        "expected_route": "base_benchmark_adaptation",
        "gold_evidence_sections": [
            "Free-form Question Answering",
            "Mathematical Program Synthesis",
            "Toxicity Reduction",
        ],
        "benchmark_evidence": [
            {"benchmark_id": "hotpotqa", "role": "primary", "evidence_section": "Free-form Question Answering"},
            {"benchmark_name": "AmbigNQ", "role": "unmodeled", "evidence_section": "Free-form Question Answering"},
            {"benchmark_name": "TriviaQA", "role": "unmodeled", "evidence_section": "Free-form Question Answering"},
            {"benchmark_id": "gsm8k", "role": "primary", "evidence_section": "Mathematical Program Synthesis"},
            {"benchmark_name": "SVAMP", "role": "unmodeled", "evidence_section": "Mathematical Program Synthesis"},
            {"benchmark_name": "TabMWP", "role": "unmodeled", "evidence_section": "Mathematical Program Synthesis"},
            {"benchmark_name": "RealToxicityPrompts", "role": "unmodeled", "evidence_section": "Toxicity Reduction"},
        ],
    },
}


def main() -> int:
    """Write an isolated visible case, gold record, and pre-revision lock."""

    catalog = load_catalog(CATALOG_PATH)
    aliases = [alias for record in catalog for alias in [record.name, *record.aliases]]
    payload, gold = build_fixture(HOLDOUT_SPEC, aliases, CATALOG_PATH)
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    (CASES_DIR / "holdout_002.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (GOLD_DIR / "holdout_002.gold.json").write_text(
        json.dumps(gold, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    freeze = {
        "schema_version": "1.0",
        "case_ids": ["holdout_002"],
        "paper_selected_before_holdout_001_driven_matcher_revision": True,
        "fixture_frozen_before_matcher_revision": True,
        "matcher_has_not_seen_holdout_002_gold": True,
        "gold_directory_passed_to_matcher": False,
        "revision_basis": ["assets/output/untouched_holdout/first_run_evaluation.json"],
        "selection_reason": (
            "tests cross-domain question answering, mathematical reasoning, tool interaction, "
            "and a domain without a current catalog entry"
        ),
        "visible_fields": ["case_id", "introduction", "method", "constraints"],
    }
    (CASES_DIR / "freeze_manifest.json").write_text(
        json.dumps(freeze, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "case_id": payload["case_id"],
                "visible_chars": len(payload["introduction"]) + len(payload["method"]),
                "leakage_passed": gold["leakage_scan"]["passed"],
                "fixture_frozen_before_matcher_revision": True,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
