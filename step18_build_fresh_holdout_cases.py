#!/usr/bin/env python3
"""Build five matcher-visible Introduction/Method cases without creating gold.

The paper set and matcher were frozen earlier. This step reads only the chosen
Introduction and Method source ranges, removes paper identity and benchmark
labels, and writes isolated case JSON files. Experiment-derived gold remains
absent until the blind workers have completed.
"""

from __future__ import annotations

import json
from pathlib import Path

from autobench.catalog import load_catalog
from autobench.leakage import enforce_blind_input
from autobench.models import MethodInput
from step1_build_blind_fixtures import (
    _clean_tex,
    _drop_result_sentences,
    _read_files,
    _redact_catalog_aliases,
    _replace_case_insensitive,
    _slice_section,
)


ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / "configs/benchmark_catalog.json"
CASES_DIR = ROOT / "assets/input/fresh_holdout_suite/cases"
GOLD_DIR = ROOT / "assets/input/fresh_holdout_suite/gold"


VISIBLE_SPECS = [
    {
        "case_id": "fresh_001",
        "introduction_files": ["assets/input/source_papers/extracted/2303.17651/sections/200_intro.tex"],
        "method_files": ["assets/input/source_papers/extracted/2303.17651/sections/300_method-alt.tex"],
        "identity_markers": ["Self-Refine", "Madaan et al."],
        "hidden_benchmark_aliases": ["CommonGen", "PIE"],
        "identity_replacements": {"Self-Refine": "METHOD_X", "\\ours": "METHOD_X"},
    },
    {
        "case_id": "fresh_002",
        "introduction_files": ["assets/input/source_papers/extracted/2308.09687/introduction.tex"],
        "method_files": [
            "assets/input/source_papers/extracted/2308.09687/scheme.tex",
            "assets/input/source_papers/extracted/2308.09687/arch.tex",
        ],
        "identity_markers": ["Graph of Thoughts", "GoT", "Besta et al."],
        "hidden_benchmark_aliases": [],
        "identity_replacements": {
            "Graph of Thoughts": "METHOD_X",
            "GoT": "METHOD_X",
            "\\nameAS": "METHOD_X",
            "\\nameA": "METHOD_X",
        },
    },
    {
        "case_id": "fresh_003",
        "introduction_files": ["assets/input/source_papers/extracted/2308.10144/main.tex"],
        "introduction_slice": (r"\\section\{Introduction\}", r"\\section\{Related Work\}"),
        "method_files": ["assets/input/source_papers/extracted/2308.10144/main.tex"],
        "method_slice": (
            r"\\section\{ExpeL: An Experiential Learning Agent\}",
            r"\\section\{Experiments\}",
        ),
        "identity_markers": ["ExpeL", "Experiential Learning Agent", "Zhao et al."],
        "hidden_benchmark_aliases": [],
        "identity_replacements": {
            "ExpeL": "METHOD_X",
            "Experiential Learning Agent": "experience-driven language agent",
        },
    },
    {
        "case_id": "fresh_004",
        "introduction_files": ["assets/input/source_papers/extracted/2305.14992/sections/intro.tex"],
        "method_files": ["assets/input/source_papers/extracted/2305.14992/sections/method.tex"],
        "identity_markers": ["Reasoning via Planning", "RAP", "Hao et al."],
        "hidden_benchmark_aliases": ["Blocksworld", "PrOntoQA", "ProntoQA"],
        "identity_replacements": {
            "Reasoning via Planning": "METHOD_X",
            "RAP-Aggregation": "METHOD_X aggregation",
            "RAP": "METHOD_X",
        },
    },
    {
        "case_id": "fresh_005",
        "introduction_files": ["assets/input/source_papers/extracted/2304.09842/body.tex"],
        "introduction_slice": (r"\\section\{Introduction\}", r"\\section\{Related Work\}"),
        "method_files": ["assets/input/source_papers/extracted/2304.09842/body.tex"],
        "method_slice": (r"\\section\{General Framework", r"\\section\{Experiments\}"),
        "identity_markers": ["Chameleon", "Lu et al."],
        "hidden_benchmark_aliases": ["ScienceQA", "Science QA"],
        "identity_replacements": {"Chameleon": "METHOD_X", "\\model": "METHOD_X"},
    },
]


def _build_visible(spec: dict, aliases: list[str]) -> tuple[dict, dict]:
    """Clean one source range and verify identity/benchmark-label isolation."""

    intro_raw = _slice_section(_read_files(spec["introduction_files"]), spec.get("introduction_slice"))
    method_raw = _slice_section(_read_files(spec["method_files"]), spec.get("method_slice"))
    introduction = _clean_tex(intro_raw, spec["identity_replacements"])
    method = _clean_tex(method_raw, spec["identity_replacements"])
    for old, new in sorted(spec["identity_replacements"].items(), key=lambda item: -len(item[0])):
        introduction = _replace_case_insensitive(introduction, old, new)
        method = _replace_case_insensitive(method, old, new)
    redaction_aliases = [*aliases, *spec["hidden_benchmark_aliases"]]
    introduction = _drop_result_sentences(_redact_catalog_aliases(introduction, redaction_aliases))
    method = _drop_result_sentences(_redact_catalog_aliases(method, redaction_aliases))
    payload = {
        "case_id": spec["case_id"],
        "introduction": introduction,
        "method": method,
        "constraints": {
            "input_scope": ["introduction", "method"],
            "paper_identity_hidden": True,
            "benchmark_names_redacted": True,
            "experiment_sections_excluded": True,
            "fresh_suite": "fresh_holdout_suite_001",
        },
    }
    method_input = MethodInput.from_dict(payload)
    report = enforce_blind_input(
        method_input,
        load_catalog(CATALOG),
        [*spec["identity_markers"], *spec["hidden_benchmark_aliases"]],
    )
    if not report.passed:
        raise ValueError(f"fresh case leakage failure for {spec['case_id']}: {report.violations}")
    return payload, {
        "case_id": spec["case_id"],
        "visible_chars": len(introduction) + len(method),
        "leakage_passed": report.passed,
        "source_files": [*spec["introduction_files"], *spec["method_files"]],
    }


def main() -> int:
    if GOLD_DIR.exists():
        raise ValueError("fresh-suite gold directory exists before blind matching")
    catalog = load_catalog(CATALOG)
    aliases = [alias for record in catalog for alias in [record.name, *record.aliases]]
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    for spec in VISIBLE_SPECS:
        payload, record = _build_visible(spec, aliases)
        path = CASES_DIR / f"{spec['case_id']}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        json.loads(path.read_text())
        records.append(record)
        print(json.dumps(record, ensure_ascii=False))
    manifest = {
        "schema_version": "1.0",
        "suite_id": "fresh_holdout_suite_001",
        "case_ids": [item["case_id"] for item in records],
        "fixture_frozen_before_first_matching": True,
        "gold_directory_exists": False,
        "gold_directory_passed_to_matcher": False,
        "matcher_change_after_suite_freeze": False,
        "visible_fields": ["case_id", "introduction", "method", "constraints"],
        "cases": records,
    }
    path = CASES_DIR / "freeze_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    json.loads(path.read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
