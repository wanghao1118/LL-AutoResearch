#!/usr/bin/env python3
"""Construct suite003 literature gold after its sealed blind run."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SUITE_DIR = ROOT / "assets/input/fresh_holdout_suite_003"
GOLD_DIR = SUITE_DIR / "gold"
PRE_GOLD = ROOT / "assets/output/fresh_holdout_suite_003/pre_gold_run_record.json"
FREEZE = SUITE_DIR / "freeze_manifest.json"
SELECTION = SUITE_DIR / "paper_selection.json"


def ev(
    section: str,
    task_family: str,
    *,
    benchmark_id: str | None = None,
    benchmark_name: str | None = None,
) -> dict[str, str]:
    """Create one catalog-modeled or outside-catalog evidence record."""

    item = {
        "role": "primary" if benchmark_id else "unmodeled",
        "evidence_section": section,
        "task_family": task_family,
    }
    if benchmark_id:
        item["benchmark_id"] = benchmark_id
    elif benchmark_name:
        item["benchmark_name"] = benchmark_name
    else:
        raise ValueError("benchmark evidence requires id or name")
    return item


SPECS: list[dict[str, Any]] = [
    {
        "case_id": "fresh3_001",
        "source_arxiv_id": "2302.04761",
        "source_title": "Toolformer: Language Models Can Teach Themselves to Use Tools",
        "source_url": "https://arxiv.org/abs/2302.04761",
        "source_input_sections": {
            "introduction": ["Introduction"],
            "method": ["Approach", "Tools"],
        },
        "primary_benchmark_ids": ["svamp", "triviaqa"],
        "secondary_benchmark_ids": [],
        "unmodeled_benchmarks": [
            "SQuAD subset of LAMA",
            "Google-RE subset of LAMA",
            "T-REx subset of LAMA",
            "ASDiv",
            "MAWPS",
            "Web Questions",
            "Natural Questions",
            "MLQA",
            "TempLAMA",
            "Dateset",
            "WikiText",
            "CCNet language-modeling subset",
        ],
        "expected_route": "base_benchmark_adaptation",
        "gold_evidence_sections": [
            "Experiments / Downstream Tasks / LAMA",
            "Experiments / Math Datasets",
            "Experiments / Question Answering",
            "Experiments / Multilingual Question Answering",
            "Experiments / Temporal Datasets",
            "Experiments / Language Modeling",
        ],
        "benchmark_evidence": [
            ev("Math Datasets", "math_reasoning", benchmark_id="svamp"),
            ev("Question Answering", "tool_augmented_nlp", benchmark_id="triviaqa"),
            *[
                ev("LAMA", "tool_augmented_nlp", benchmark_name=name)
                for name in (
                    "SQuAD subset of LAMA",
                    "Google-RE subset of LAMA",
                    "T-REx subset of LAMA",
                )
            ],
            *[
                ev("Math Datasets", "math_reasoning", benchmark_name=name)
                for name in ("ASDiv", "MAWPS")
            ],
            *[
                ev("Question Answering", "tool_augmented_nlp", benchmark_name=name)
                for name in ("Web Questions", "Natural Questions")
            ],
            ev("Multilingual Question Answering", "tool_augmented_nlp", benchmark_name="MLQA"),
            ev("Temporal Datasets", "tool_augmented_nlp", benchmark_name="TempLAMA"),
            ev("Temporal Datasets", "tool_augmented_nlp", benchmark_name="Dateset"),
            ev("Language Modeling", "language_modeling", benchmark_name="WikiText"),
            ev(
                "Language Modeling",
                "language_modeling",
                benchmark_name="CCNet language-modeling subset",
            ),
        ],
        "evidence_files": ["assets/input/source_papers/extracted/2302.04761/main.tex"],
        "required_terms": [
            "SQuAD, Google-RE and T-REx subsets",
            "ASDiv",
            "SVAMP",
            "MAWPS",
            "Web Questions",
            "Natural Questions",
            "TriviaQA",
            "MLQA",
            "TempLAMA",
            "Dateset",
            "WikiText",
            "CCNet",
        ],
    },
    {
        "case_id": "fresh3_002",
        "source_arxiv_id": "2209.11302",
        "source_title": "ProgPrompt: Generating Situated Robot Task Plans using Large Language Models",
        "source_url": "https://arxiv.org/abs/2209.11302",
        "source_input_sections": {
            "introduction": ["Introduction"],
            "method": ["Our Method: ProgPrompt"],
        },
        "primary_benchmark_ids": [],
        "secondary_benchmark_ids": [],
        "unmodeled_benchmarks": [
            "VirtualHome Household Task Set",
            "Physical Robot Tabletop Task Set",
        ],
        "expected_route": "base_benchmark_adaptation",
        "gold_evidence_sections": [
            "Experiments / Simulation Experiments",
            "Experiments / Real-Robot Experiments",
        ],
        "benchmark_evidence": [
            ev(
                "Simulation Experiments",
                "embodied_household",
                benchmark_name="VirtualHome Household Task Set",
            ),
            ev(
                "Real-Robot Experiments",
                "robot_manipulation",
                benchmark_name="Physical Robot Tabletop Task Set",
            ),
        ],
        "evidence_files": ["assets/input/source_papers/extracted/2209.11302/main.tex"],
        "required_terms": [
            "Virtual Home (VH) Environment",
            "dataset of 70 household tasks",
            "physical robot manipulator",
            "We evaluate on 4 tasks",
        ],
    },
    {
        "case_id": "fresh3_003",
        "source_arxiv_id": "2211.11559",
        "source_title": "Visual Programming: Compositional visual reasoning without training",
        "source_url": "https://arxiv.org/abs/2211.11559",
        "source_input_sections": {
            "introduction": ["Introduction"],
            "method": ["Visual Programming"],
        },
        "primary_benchmark_ids": [],
        "secondary_benchmark_ids": [],
        "unmodeled_benchmarks": [
            "GQA",
            "NLVRv2",
            "Factual Knowledge Object Tagging",
            "Language-Guided Image Editing",
        ],
        "expected_route": "new_benchmark_synthesis",
        "gold_evidence_sections": [
            "Tasks / Compositional Visual Question Answering",
            "Tasks / Zero-Shot Reasoning on Image Pairs",
            "Tasks / Factual Knowledge Object Tagging",
            "Tasks / Image Editing with Natural Language",
        ],
        "benchmark_evidence": [
            ev("Compositional Visual Question Answering", "visual_reasoning", benchmark_name="GQA"),
            ev("Zero-Shot Reasoning on Image Pairs", "visual_reasoning", benchmark_name="NLVRv2"),
            ev(
                "Factual Knowledge Object Tagging",
                "visual_reasoning",
                benchmark_name="Factual Knowledge Object Tagging",
            ),
            ev(
                "Image Editing with Natural Language",
                "image_editing",
                benchmark_name="Language-Guided Image Editing",
            ),
        ],
        "evidence_files": [
            "assets/input/source_papers/extracted/2211.11559/PaperForReview.tex"
        ],
        "required_terms": [
            "Compositional Visual Question Answering",
            "GQA task",
            "NLVR",
            "Factual Knowledge Object Tagging",
            "Image Editing with Natural Language",
        ],
    },
    {
        "case_id": "fresh3_004",
        "source_arxiv_id": "2211.12588",
        "source_title": (
            "Program of Thoughts Prompting: Disentangling Computation from Reasoning "
            "for Numerical Reasoning Tasks"
        ),
        "source_url": "https://arxiv.org/abs/2211.12588",
        "source_input_sections": {
            "introduction": ["Introduction"],
            "method": ["Program of Thoughts"],
        },
        "primary_benchmark_ids": ["gsm8k", "svamp", "tabmwp"],
        "secondary_benchmark_ids": [],
        "unmodeled_benchmarks": ["AQuA", "MultiArith", "FinQA", "ConvFinQA", "TATQA"],
        "expected_route": "base_benchmark_adaptation",
        "gold_evidence_sections": ["Experiments / Experimental Setup / Datasets"],
        "benchmark_evidence": [
            ev("Datasets", "math_reasoning", benchmark_id="gsm8k"),
            ev("Datasets", "math_reasoning", benchmark_id="svamp"),
            ev("Datasets", "tabular_math_reasoning", benchmark_id="tabmwp"),
            ev("Datasets", "math_reasoning", benchmark_name="AQuA"),
            ev("Datasets", "math_reasoning", benchmark_name="MultiArith"),
            *[
                ev("Datasets", "financial_numerical_qa", benchmark_name=name)
                for name in ("FinQA", "ConvFinQA", "TATQA")
            ],
        ],
        "evidence_files": [
            "assets/input/source_papers/extracted/2211.12588/sections/experiment.tex"
        ],
        "required_terms": [
            "GSM8K",
            "AQuA",
            "SVAMP",
            "MultiArith",
            "TabMWP",
            "FinQA",
            "ConvFinQA",
            "TATQA",
        ],
    },
    {
        "case_id": "fresh3_005",
        "source_arxiv_id": "2305.10601",
        "source_title": "Tree of Thoughts: Deliberate Problem Solving with Large Language Models",
        "source_url": "https://arxiv.org/abs/2305.10601",
        "source_input_sections": {
            "introduction": ["Introduction"],
            "method": ["Tree of Thoughts: Deliberate Problem Solving with LM"],
        },
        "primary_benchmark_ids": ["game_of_24"],
        "secondary_benchmark_ids": [],
        "unmodeled_benchmarks": ["Creative Writing", "5x5 Mini Crosswords"],
        "expected_route": "base_benchmark_adaptation",
        "gold_evidence_sections": [
            "Experiments / Game of 24",
            "Experiments / Creative Writing",
            "Experiments / Mini Crosswords",
        ],
        "benchmark_evidence": [
            ev("Game of 24", "math_reasoning", benchmark_id="game_of_24"),
            ev("Creative Writing", "creative_writing", benchmark_name="Creative Writing"),
            ev("Mini Crosswords", "word_puzzle", benchmark_name="5x5 Mini Crosswords"),
        ],
        "evidence_files": ["assets/input/source_papers/extracted/2305.10601/main.tex"],
        "required_terms": [
            "Game of 24",
            "Creative Writing",
            "5x5 Crosswords",
            "We propose three tasks",
        ],
    },
]


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_pre_gold() -> dict[str, bool]:
    """Verify worker isolation and matcher freeze before writing gold."""

    record = load(PRE_GOLD)
    checks = {
        "blind_run_completed_before_gold": record.get("blind_run_completed_before_gold") is True,
        "gold_absent_during_run": record.get("gold_directory_existed_during_run") is False,
        "five_cases": record.get("case_count") == len(SPECS),
        "workers_succeeded": record.get("all_worker_exit_statuses_zero") is True,
        "sandboxes_clean": record.get("all_sandboxes_excluded_hidden_labels") is True,
        "matcher_unchanged": record.get("matcher_frozen_file_sizes_unchanged") is True,
        "workers_intro_method_only": record.get("worker_sandboxes_remained_introduction_method_only")
        is True,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError(f"suite003 gold blocked by pre-run checks: {failed}")
    return checks


def verify_terms(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Require every benchmark name to occur literally in cited source files."""

    paths = [ROOT / item for item in spec["evidence_files"]]
    text_by_path = {path: path.read_text(encoding="utf-8", errors="replace") for path in paths}
    records = []
    for term in spec["required_terms"]:
        matched = [path for path, text in text_by_path.items() if term in text]
        if not matched:
            raise ValueError(f"source term absent for {spec['case_id']}: {term!r}")
        records.append(
            {
                "term": term,
                "source_files": [path.relative_to(ROOT).as_posix() for path in matched],
            }
        )
    return records


def main() -> int:
    """Write five verified gold records and mark the suite as revealed."""

    checks = verify_pre_gold()
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for spec in SPECS:
        term_checks = verify_terms(spec)
        payload = {
            key: value
            for key, value in spec.items()
            if key not in {"evidence_files", "required_terms"}
        }
        payload.update(
            {
                "matcher_visible": False,
                "gold_constructed_after_blind_run": True,
                "pre_gold_run_record": PRE_GOLD.relative_to(ROOT).as_posix(),
                "source_evidence_checks": term_checks,
            }
        )
        path = GOLD_DIR / f"{spec['case_id']}.gold.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        load(path)
        written.append(path.relative_to(ROOT).as_posix())
        print(
            json.dumps(
                {
                    "case_id": spec["case_id"],
                    "modeled": len(spec["primary_benchmark_ids"]),
                    "unmodeled": len(spec["unmodeled_benchmarks"]),
                    "expected_route": spec["expected_route"],
                    "source_terms_verified": len(term_checks),
                },
                ensure_ascii=False,
            )
        )

    freeze = load(FREEZE)
    freeze.update(
        {
            "gold_revealed": True,
            "gold_constructed_after_blind_run": True,
            "gold_files": written,
            "gold_construction_preconditions": checks,
            "pre_gold_run_record": PRE_GOLD.relative_to(ROOT).as_posix(),
            "meta_agent_experiment_line_caveat_recorded": True,
        }
    )
    FREEZE.write_text(json.dumps(freeze, ensure_ascii=False, indent=2) + "\n")
    selection = load(SELECTION)
    selection["gold_state"] = "REVEALED_AFTER_SEALED_BLIND_RUN"
    selection["gold_files"] = written
    SELECTION.write_text(json.dumps(selection, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"gold_files": written, "human_submission_required": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
