#!/usr/bin/env python3
"""Build suite002 Introduction/Method cases while gold remains absent."""

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
SUITE_DIR = ROOT / "assets/input/fresh_holdout_suite_002"
CASES_DIR = SUITE_DIR / "cases"
GOLD_DIR = SUITE_DIR / "gold"
CATALOG_PATH = ROOT / "configs/benchmark_catalog.json"


VISIBLE_SPECS = [
    {
        "case_id": "fresh2_001",
        "introduction_files": ["assets/input/source_papers/extracted/2211.10435/sections/intro.tex"],
        "method_files": ["assets/input/source_papers/extracted/2211.10435/sections/method.tex"],
        "identity_markers": ["Program-aided Language Models", "Program-Aided Language Models", "PAL"],
        "hidden_benchmark_aliases": ["BIG-Bench Hard", "BIG Bench Hard", "BBH"],
        "identity_replacements": {
            "Program-aided Language Models": "METHOD_X",
            "Program-Aided Language Models": "METHOD_X",
            "\\ours": "METHOD_X",
            "PAL": "METHOD_X",
        },
    },
    {
        "case_id": "fresh2_002",
        "introduction_files": [
            "assets/input/source_papers/extracted/2305.18323/sections/_s1_introduction.tex"
        ],
        "method_files": ["assets/input/source_papers/extracted/2305.18323/sections/_s3_method.tex"],
        "identity_markers": ["ReWOO", "Reasoning WithOut Observation"],
        "hidden_benchmark_aliases": [
            "StrategyQA",
            "PhysicsQuestion",
            "Sports Understanding",
            "SOTUQA",
        ],
        "identity_replacements": {
            "Reasoning WithOut Observation": "METHOD_X",
            "ReWOO": "METHOD_X",
            "\\texttt{ReWOO}": "METHOD_X",
        },
    },
    {
        "case_id": "fresh2_003",
        "introduction_files": ["assets/input/source_papers/extracted/2207.05608/main.tex"],
        "introduction_slice": (r"\\section\{Introduction\}", r"\\section\{Related Work\}"),
        "method_files": ["assets/input/source_papers/extracted/2207.05608/main.tex"],
        "method_slice": (
            r"\\section\{Leveraging Embodied Language Feedback",
            r"\\section\{Experimental Results\}",
        ),
        "identity_markers": ["Inner Monologue"],
        "hidden_benchmark_aliases": ["Ravens"],
        "identity_replacements": {"Inner Monologue": "METHOD_X", "\\algname": "METHOD_X"},
    },
    {
        "case_id": "fresh2_004",
        "introduction_files": ["assets/input/source_papers/extracted/2304.11477/contents/intro.tex"],
        "method_files": ["assets/input/source_papers/extracted/2304.11477/contents/method.tex"],
        "identity_markers": ["LLM+P", "Large Language Model + Classical Planner"],
        "hidden_benchmark_aliases": ["Blocksworld", "Tyreworld", "Grippers"],
        "identity_replacements": {
            "Large Language Model + Classical Planner": "METHOD_X",
            "LLM+P": "METHOD_X",
            "\\lmp": "METHOD_X",
        },
    },
    {
        "case_id": "fresh2_005",
        "introduction_files": ["assets/input/source_papers/extracted/2303.08128/egpaper_final.tex"],
        "introduction_slice": (r"\\section\{Introduction\}", r"\\section\{Related Work\}"),
        "method_files": ["assets/input/source_papers/extracted/2303.08128/egpaper_final.tex"],
        "method_slice": (r"\\section\{Method\}", r"\\section\{Evaluation\}"),
        "identity_markers": ["ViperGPT"],
        "hidden_benchmark_aliases": ["GQA", "VQAv2", "OK-VQA", "RefCOCO", "NExT-QA"],
        "identity_replacements": {
            "ViperGPT": "METHOD_X",
            "\\methodname": "METHOD_X",
            "GQA": "[REDACTED_BENCHMARK]",
        },
    },
]


def build_visible(spec: dict, aliases: list[str]) -> tuple[dict, dict]:
    """Clean one Introduction/Method range and verify benchmark isolation."""

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
            "fresh_suite": "fresh_holdout_suite_002",
        },
    }
    method_input = MethodInput.from_dict(payload)
    report = enforce_blind_input(
        method_input,
        load_catalog(CATALOG_PATH),
        [*spec["identity_markers"], *spec["hidden_benchmark_aliases"]],
    )
    if not report.passed:
        raise ValueError(f"suite002 leakage failure for {spec['case_id']}: {report.violations}")
    return payload, {
        "case_id": spec["case_id"],
        "visible_chars": len(introduction) + len(method),
        "leakage_passed": report.passed,
        "source_files": [*spec["introduction_files"], *spec["method_files"]],
    }


def main() -> int:
    if GOLD_DIR.exists():
        raise ValueError("suite002 gold directory exists before blind matching")
    selection = json.loads((SUITE_DIR / "paper_selection.json").read_text(encoding="utf-8"))
    if selection.get("gold_state") != "SEALED_NOT_CONSTRUCTED":
        raise ValueError("suite002 gold is not sealed")
    catalog = load_catalog(CATALOG_PATH)
    aliases = [alias for record in catalog for alias in [record.name, *record.aliases]]
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    for spec in VISIBLE_SPECS:
        payload, record = build_visible(spec, aliases)
        path = CASES_DIR / f"{spec['case_id']}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        json.loads(path.read_text())
        records.append(record)
        print(json.dumps(record, ensure_ascii=False))
    manifest = {
        "schema_version": "1.0",
        "suite_id": "fresh_holdout_suite_002",
        "case_ids": [item["case_id"] for item in records],
        "fixture_frozen_before_first_matching": True,
        "gold_directory_exists": False,
        "gold_directory_passed_to_matcher": False,
        "matcher_change_after_suite_freeze": False,
        "visible_fields": ["case_id", "introduction", "method", "constraints"],
        "experiment_content_inspected": False,
        "experiment_headings_enumerated_after_selection": True,
        "cases": records,
    }
    path = CASES_DIR / "freeze_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    json.loads(path.read_text())

    freeze_path = SUITE_DIR / "freeze_manifest.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    freeze.update(
        {
            "cases_manifest": path.relative_to(ROOT).as_posix(),
            "experiment_headings_enumerated_after_selection": True,
            "source_experiment_content_inspected": False,
            "gold_revealed": False,
        }
    )
    freeze_path.write_text(json.dumps(freeze, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
