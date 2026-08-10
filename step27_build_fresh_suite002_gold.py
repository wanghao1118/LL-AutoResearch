#!/usr/bin/env python3
"""Construct suite002 literature gold after its sealed blind run."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SUITE_DIR = ROOT / "assets/input/fresh_holdout_suite_002"
GOLD_DIR = SUITE_DIR / "gold"
PRE_GOLD = ROOT / "assets/output/fresh_holdout_suite_002/pre_gold_run_record.json"
FREEZE = SUITE_DIR / "freeze_manifest.json"
SELECTION = SUITE_DIR / "paper_selection.json"


def ev(
    section: str,
    task_family: str,
    *,
    benchmark_id: str | None = None,
    benchmark_name: str | None = None,
) -> dict[str, str]:
    """Create one modeled or outside-catalog benchmark evidence record."""

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
        "case_id": "fresh2_001",
        "source_arxiv_id": "2211.10435",
        "source_title": "PAL: Program-aided Language Models",
        "source_url": "https://arxiv.org/abs/2211.10435",
        "source_input_sections": {
            "introduction": ["Introduction"],
            "method": ["Background: Few-shot Prompting", "Program-aided Language Models"],
        },
        "primary_benchmark_ids": ["gsm8k", "svamp"],
        "secondary_benchmark_ids": [],
        "unmodeled_benchmarks": [
            "ASDiv",
            "SingleOp",
            "SingleEq",
            "AddSub",
            "MultiArith",
            "GSM-Hard",
            "Reasoning about Colored Objects",
            "Penguins in a Table",
            "Date Understanding",
            "Object Counting",
            "Repeat Copy",
        ],
        "expected_route": "base_benchmark_adaptation",
        "gold_evidence_sections": [
            "Experimental Setup",
            "Mathematical Reasoning",
            "Symbolic Reasoning",
            "Algorithmic Tasks",
            "Appendix: Datasets",
        ],
        "benchmark_evidence": [
            ev("Mathematical Reasoning", "math_reasoning", benchmark_id="gsm8k"),
            ev("Mathematical Reasoning", "math_reasoning", benchmark_id="svamp"),
            *[
                ev("Appendix: Datasets", "math_reasoning", benchmark_name=name)
                for name in ("ASDiv", "SingleOp", "SingleEq", "AddSub", "MultiArith", "GSM-Hard")
            ],
            *[
                ev("Symbolic Reasoning", "symbolic_reasoning", benchmark_name=name)
                for name in (
                    "Reasoning about Colored Objects",
                    "Penguins in a Table",
                    "Date Understanding",
                )
            ],
            *[
                ev("Algorithmic Tasks", "symbolic_reasoning", benchmark_name=name)
                for name in ("Object Counting", "Repeat Copy")
            ],
        ],
        "evidence_files": [
            "assets/input/source_papers/extracted/2211.10435/sections/experiments.tex",
            "assets/input/source_papers/extracted/2211.10435/sections/maths.tex",
            "assets/input/source_papers/extracted/2211.10435/sections/symbolic.tex",
            "assets/input/source_papers/extracted/2211.10435/sections/algorithmic.tex",
            "assets/input/source_papers/extracted/2211.10435/sections/appendix.tex",
        ],
        "required_terms": [
            "eight mathematical word problem datasets",
            "\\gsm~",
            "\\svamp~",
            "\\asdiv~",
            "\\singleop~",
            "\\singleeq~",
            "\\addsub~",
            "\\multiarith~",
            "\\gsmhard",
            "Reasoning about Colored Objects",
            "Penguins in a Table",
            "Date Understanding",
            "Object Counting",
            "Repeat Copy",
        ],
    },
    {
        "case_id": "fresh2_002",
        "source_arxiv_id": "2305.18323",
        "source_title": "ReWOO: Decoupling Reasoning from Observations for Efficient Augmented Language Models",
        "source_url": "https://arxiv.org/abs/2305.18323",
        "source_input_sections": {"introduction": ["Introduction"], "method": ["Methodology"]},
        "primary_benchmark_ids": ["hotpotqa", "triviaqa", "gsm8k"],
        "secondary_benchmark_ids": [],
        "unmodeled_benchmarks": [
            "SportsUnderstanding",
            "StrategyQA",
            "PhysicsQuestions",
            "SOTUQA",
            "Curated Real-World ALM Tasks",
        ],
        "expected_route": "base_benchmark_adaptation",
        "gold_evidence_sections": ["Experiments / Setups / Tasks and Datasets"],
        "benchmark_evidence": [
            ev("Tasks and Datasets", "knowledge_intensive_qa", benchmark_id="hotpotqa"),
            ev("Tasks and Datasets", "knowledge_intensive_qa", benchmark_id="triviaqa"),
            ev("Tasks and Datasets", "math_word_problem", benchmark_id="gsm8k"),
            ev("Tasks and Datasets", "tool_augmented_nlp", benchmark_name="SportsUnderstanding"),
            ev("Tasks and Datasets", "tool_augmented_nlp", benchmark_name="StrategyQA"),
            ev("Tasks and Datasets", "tool_augmented_nlp", benchmark_name="PhysicsQuestions"),
            ev("Tasks and Datasets", "tool_augmented_nlp", benchmark_name="SOTUQA"),
            ev(
                "Tasks and Datasets",
                "tool_augmented_nlp",
                benchmark_name="Curated Real-World ALM Tasks",
            ),
        ],
        "evidence_files": [
            "assets/input/source_papers/extracted/2305.18323/sections/_s4_experiments.tex"
        ],
        "required_terms": [
            "HotpotQA",
            "TriviaQA",
            "SportsUnderstanding",
            "StrategyQA",
            "GSM8K",
            "PhysicsQuestions",
            "SOTUQA",
            "real-world ALM applications",
        ],
    },
    {
        "case_id": "fresh2_003",
        "source_arxiv_id": "2207.05608",
        "source_title": "Inner Monologue: Embodied Reasoning through Planning with Language Models",
        "source_url": "https://arxiv.org/abs/2207.05608",
        "source_input_sections": {
            "introduction": ["Introduction"],
            "method": ["Leveraging Embodied Language Feedback", "Problem Statement", "Sources of Feedback"],
        },
        "primary_benchmark_ids": [],
        "secondary_benchmark_ids": [],
        "unmodeled_benchmarks": [
            "Ravens-based Simulated Tabletop Rearrangement",
            "Real-World Tabletop Rearrangement",
            "Real-World Kitchen Mobile Manipulation",
        ],
        "expected_route": "new_benchmark_synthesis",
        "gold_evidence_sections": [
            "Experimental Results",
            "Simulated Tabletop Rearrangement",
            "Real-World Tabletop Rearrangement",
            "Real-World Mobile Manipulator in a Kitchen Setting",
        ],
        "benchmark_evidence": [
            ev(
                "Simulated Tabletop Rearrangement",
                "robot_manipulation",
                benchmark_name="Ravens-based Simulated Tabletop Rearrangement",
            ),
            ev(
                "Real-World Tabletop Rearrangement",
                "robot_manipulation",
                benchmark_name="Real-World Tabletop Rearrangement",
            ),
            ev(
                "Real-World Mobile Manipulator in a Kitchen Setting",
                "robot_manipulation",
                benchmark_name="Real-World Kitchen Mobile Manipulation",
            ),
        ],
        "evidence_files": ["assets/input/source_papers/extracted/2207.05608/main.tex"],
        "required_terms": [
            "three environments",
            "Simulated Tabletop Rearrangement",
            "Real-World Tabletop Rearrangement",
            "Real-World Mobile Manipulator in a Kitchen Setting",
        ],
    },
    {
        "case_id": "fresh2_004",
        "source_arxiv_id": "2304.11477",
        "source_title": "LLM+P: Empowering Large Language Models with Optimal Planning Proficiency",
        "source_url": "https://arxiv.org/abs/2304.11477",
        "source_input_sections": {"introduction": ["Introduction"], "method": ["Method"]},
        "primary_benchmark_ids": [],
        "secondary_benchmark_ids": [],
        "unmodeled_benchmarks": [
            "Blocksworld",
            "Barman",
            "Floortile",
            "Grippers",
            "Storage",
            "Termes",
            "Tyreworld",
        ],
        "expected_route": "new_benchmark_synthesis",
        "gold_evidence_sections": ["Experiments / Benchmark Problems"],
        "benchmark_evidence": [
            ev("Benchmark Problems", "classical_planning", benchmark_name=name)
            for name in (
                "Blocksworld",
                "Barman",
                "Floortile",
                "Grippers",
                "Storage",
                "Termes",
                "Tyreworld",
            )
        ],
        "evidence_files": [
            "assets/input/source_papers/extracted/2304.11477/contents/experiments.tex"
        ],
        "required_terms": [
            "seven robot planning domains",
            "\\blocksworld{}",
            "\\barman{}",
            "\\floortile{}",
            "\\grippers{}",
            "\\storage{}",
            "\\termes{}",
            "\\tyreworld{}",
        ],
    },
    {
        "case_id": "fresh2_005",
        "source_arxiv_id": "2303.08128",
        "source_title": "ViperGPT: Visual Inference via Python Execution for Reasoning",
        "source_url": "https://arxiv.org/abs/2303.08128",
        "source_input_sections": {
            "introduction": ["Introduction"],
            "method": ["Method", "Program Generation", "Modules and Their API", "Program Execution"],
        },
        "primary_benchmark_ids": [],
        "secondary_benchmark_ids": [],
        "unmodeled_benchmarks": ["RefCOCO", "RefCOCO+", "GQA", "OK-VQA", "NExT-QA"],
        "expected_route": "new_benchmark_synthesis",
        "gold_evidence_sections": [
            "Evaluation",
            "Visual Grounding",
            "Compositional Image Question Answering",
            "External Knowledge-dependent Image Question Answering",
            "Video Causal/Temporal Reasoning",
        ],
        "benchmark_evidence": [
            ev("Visual Grounding", "visual_reasoning", benchmark_name="RefCOCO"),
            ev("Visual Grounding", "visual_reasoning", benchmark_name="RefCOCO+"),
            ev(
                "Compositional Image Question Answering",
                "visual_reasoning",
                benchmark_name="GQA",
            ),
            ev(
                "External Knowledge-dependent Image Question Answering",
                "visual_reasoning",
                benchmark_name="OK-VQA",
            ),
            ev("Video Causal/Temporal Reasoning", "visual_reasoning", benchmark_name="NExT-QA"),
        ],
        "evidence_files": [
            "assets/input/source_papers/extracted/2303.08128/egpaper_final.tex"
        ],
        "required_terms": ["RefCOCO", "RefCOCO+", "GQA dataset", "OK-VQA dataset", "NExT-QA dataset"],
    },
]


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_pre_gold() -> dict[str, bool]:
    record = load(PRE_GOLD)
    checks = {
        "blind_run_completed_before_gold": record.get("blind_run_completed_before_gold") is True,
        "gold_absent_during_run": record.get("gold_directory_existed_during_run") is False,
        "five_cases": record.get("case_count") == len(SPECS),
        "workers_succeeded": record.get("all_worker_exit_statuses_zero") is True,
        "sandboxes_clean": record.get("all_sandboxes_excluded_hidden_labels") is True,
        "matcher_unchanged": record.get("matcher_frozen_file_sizes_unchanged") is True,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError(f"suite002 gold blocked by pre-run checks: {failed}")
    return checks


def verify_terms(spec: dict[str, Any]) -> list[dict[str, Any]]:
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
    checks = verify_pre_gold()
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for spec in SPECS:
        term_checks = verify_terms(spec)
        payload = {key: value for key, value in spec.items() if key not in {"evidence_files", "required_terms"}}
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
