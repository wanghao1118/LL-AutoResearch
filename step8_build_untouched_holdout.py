#!/usr/bin/env python3
"""Freeze one new paper fixture before its first Auto-Bench matching run."""

from __future__ import annotations

import json
from pathlib import Path

from autobench.catalog import load_catalog
from step1_build_blind_fixtures import build_fixture


ROOT = Path(__file__).resolve().parent
CATALOG_PATH = ROOT / "configs/benchmark_catalog.json"
CASES_DIR = ROOT / "assets/input/untouched_holdout_cases"
GOLD_DIR = ROOT / "assets/input/untouched_holdout_gold"


HOLDOUT_SPEC = {
    "case_id": "holdout_001",
    "introduction_files": ["assets/input/source_papers/extracted/2310.04406/main.tex"],
    "introduction_slice": (r"\\section\{Introduction\}", r"\\section\{Related Work\}"),
    "method_files": ["assets/input/source_papers/extracted/2310.04406/main.tex"],
    "method_slice": (
        r"\\section\{Unifying Reasoning, Acting, and Planning\}",
        r"\\section\{Experiments\}",
    ),
    "identity_markers": [
        "Language Agent Tree Search",
        "LATS",
        "Zhou et al.",
    ],
    "hidden_benchmark_aliases": ["Game of 24", "Game 24"],
    "identity_replacements": {
        "Language Agent Tree Search": "METHOD_X",
        "LATS": "METHOD_X",
    },
    "gold": {
        "source_arxiv_id": "2310.04406",
        "source_title": "Language Agent Tree Search Unifies Reasoning Acting and Planning in Language Models",
        "source_url": "https://arxiv.org/abs/2310.04406",
        "source_input_sections": {
            "introduction": ["Introduction"],
            "method": ["Unifying Reasoning, Acting, and Planning"],
        },
        "primary_benchmark_ids": ["hotpotqa", "humaneval", "mbpp", "webshop"],
        "secondary_benchmark_ids": [],
        "unmodeled_benchmarks": ["Game of 24"],
        "expected_route": "direct_portfolio",
        "gold_evidence_sections": ["HotPotQA", "Programming", "WebShop", "Ablation Study and Additional Analysis"],
        "benchmark_evidence": [
            {"benchmark_id": "hotpotqa", "role": "primary", "evidence_section": "HotPotQA"},
            {"benchmark_id": "humaneval", "role": "primary", "evidence_section": "Programming"},
            {"benchmark_id": "mbpp", "role": "primary", "evidence_section": "Programming"},
            {"benchmark_id": "webshop", "role": "primary", "evidence_section": "WebShop"},
            {"benchmark_name": "Game of 24", "role": "unmodeled", "evidence_section": "Ablation Study and Additional Analysis"},
        ],
    },
}


def main() -> int:
    """Write the matcher input, separate gold, and pre-run freeze declaration."""

    catalog = load_catalog(CATALOG_PATH)
    aliases = [alias for record in catalog for alias in [record.name, *record.aliases]]
    payload, gold = build_fixture(HOLDOUT_SPEC, aliases, CATALOG_PATH)
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    case_path = CASES_DIR / "holdout_001.json"
    gold_path = GOLD_DIR / "holdout_001.gold.json"
    case_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    gold_path.write_text(json.dumps(gold, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": "1.0",
        "case_ids": ["holdout_001"],
        "paper_selected_before_matching": True,
        "fixture_frozen_before_first_matching": True,
        "gold_directory_passed_to_matcher": False,
        "matcher_change_policy": "record the first run before any holdout-driven matcher change",
        "visible_fields": ["case_id", "introduction", "method", "constraints"],
    }
    (CASES_DIR / "freeze_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "case_id": payload["case_id"],
                "visible_chars": len(payload["introduction"]) + len(payload["method"]),
                "leakage_passed": gold["leakage_scan"]["passed"],
                "fixture_frozen_before_first_matching": True,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
