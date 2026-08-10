#!/usr/bin/env python3
"""Build literature gold only after the sealed fresh blind run has finished.

The five papers were selected before their experiment sections were inspected.
This script enforces that the pre-gold run record is complete, verifies literal
benchmark evidence in the official arXiv sources, and then writes the hidden
comparison files used by the automatic literature reviewer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SUITE_DIR = ROOT / "assets/input/fresh_holdout_suite"
GOLD_DIR = SUITE_DIR / "gold"
PRE_GOLD_RECORD = ROOT / "assets/output/fresh_holdout_suite/pre_gold_run_record.json"
FREEZE_MANIFEST = SUITE_DIR / "freeze_manifest.json"
PAPER_SELECTION = SUITE_DIR / "paper_selection.json"


def evidence(
    benchmark_id: str | None,
    benchmark_name: str | None,
    section: str,
    task_family: str | None = None,
) -> dict[str, str]:
    """Create one benchmark-evidence row with exactly one identity field."""

    item = {"role": "primary" if benchmark_id else "unmodeled", "evidence_section": section}
    if benchmark_id:
        item["benchmark_id"] = benchmark_id
    elif benchmark_name:
        item["benchmark_name"] = benchmark_name
    else:
        raise ValueError("benchmark evidence needs an id or name")
    if task_family:
        item["task_family"] = task_family
    return item


SPECS: list[dict[str, Any]] = [
    {
        "case_id": "fresh_001",
        "source_arxiv_id": "2303.17651",
        "source_title": "Self-Refine: Iterative Refinement with Self-Feedback",
        "source_url": "https://arxiv.org/abs/2303.17651",
        "source_input_sections": {
            "introduction": ["Introduction"],
            "method": ["Method"],
        },
        "primary_benchmark_ids": ["gsm8k"],
        "secondary_benchmark_ids": [],
        "unmodeled_benchmarks": [
            "FED",
            "PIE",
            "Project CodeNet",
            "Sentiment Reversal review-passage set",
            "Acronym Generation paper-curated set",
            "CommonGen-Hard",
        ],
        "expected_route": "new_benchmark_synthesis",
        "gold_evidence_sections": ["Evaluation", "Appendix: Task Details"],
        "benchmark_evidence": [
            evidence(None, "FED", "Dialogue Response Generation / Evaluation", "dialogue_response_generation"),
            evidence(None, "PIE", "Code Optimization", "code_optimization"),
            evidence(None, "Project CodeNet", "Code Readability / Experiments", "code_readability"),
            evidence("gsm8k", None, "Math Reasoning", "math_reasoning"),
            evidence(
                None,
                "Sentiment Reversal review-passage set",
                "Sentiment Reversal",
                "sentiment_reversal",
            ),
            evidence(
                None,
                "Acronym Generation paper-curated set",
                "Acronym Generation",
                "acronym_generation",
            ),
            evidence(None, "CommonGen-Hard", "Constrained Generation", "constrained_generation"),
        ],
        "evidence_files": [
            "assets/input/source_papers/extracted/2303.17651/sections/400_tasks.tex",
            "assets/input/source_papers/extracted/2303.17651/sections/appendix/tasks_table.tex",
            "assets/input/source_papers/extracted/2303.17651/sections/appendix/task_details/responsegen.tex",
            "assets/input/source_papers/extracted/2303.17651/sections/appendix/task_details/pie.tex",
            "assets/input/source_papers/extracted/2303.17651/sections/appendix/task_details/code.tex",
            "assets/input/source_papers/extracted/2303.17651/sections/appendix/task_details/gsm.tex",
            "assets/input/source_papers/extracted/2303.17651/sections/appendix/task_details/acronym.tex",
            "assets/input/source_papers/extracted/2303.17651/sections/appendix/task_details/commongen.tex",
        ],
        "required_terms": [
            "We evaluate \\ours on \\numtasks diverse tasks",
            "FED dataset",
            "Performance-Improving Code Edits or PIE",
            "We use the CodeNet",
            "Grade School Math 8k (GSM-8k)",
            "1000 review passages",
            "generated a list of 250 acronyms",
            "CommonGen-Hard",
        ],
    },
    {
        "case_id": "fresh_002",
        "source_arxiv_id": "2308.09687",
        "source_title": "Graph of Thoughts: Solving Elaborate Problems with Large Language Models",
        "source_url": "https://arxiv.org/abs/2308.09687",
        "source_input_sections": {
            "introduction": ["Introduction"],
            "method": ["Graph of Thoughts", "Architecture"],
        },
        "primary_benchmark_ids": [],
        "secondary_benchmark_ids": [],
        "unmodeled_benchmarks": [
            "Sorting task suite",
            "Set Intersection task suite",
            "Keyword Counting task suite",
            "Document Merging task suite",
        ],
        "expected_route": "new_benchmark_synthesis",
        "gold_evidence_sections": ["Example Use Cases", "Evaluation"],
        "benchmark_evidence": [
            evidence(None, "Sorting task suite", "Example Use Cases / Sorting", "sorting"),
            evidence(
                None,
                "Set Intersection task suite",
                "Example Use Cases / Set Operations",
                "set_intersection",
            ),
            evidence(
                None,
                "Keyword Counting task suite",
                "Example Use Cases / Keyword Counting",
                "keyword_counting",
            ),
            evidence(
                None,
                "Document Merging task suite",
                "Example Use Cases / Document Merging",
                "document_merging",
            ),
        ],
        "evidence_files": [
            "assets/input/source_papers/extracted/2308.09687/cases.tex",
            "assets/input/source_papers/extracted/2308.09687/eval.tex",
        ],
        "required_terms": [
            "\\subsection{Sorting}",
            "set intersection",
            "\\subsection{Keyword Counting}",
            "\\subsection{Document Merging}",
            "results of the analysis are in",
        ],
    },
    {
        "case_id": "fresh_003",
        "source_arxiv_id": "2308.10144",
        "source_title": "ExpeL: LLM Agents Are Experiential Learners",
        "source_url": "https://arxiv.org/abs/2308.10144",
        "source_input_sections": {
            "introduction": ["Introduction"],
            "method": ["ExpeL: An Experiential Learning Agent"],
        },
        "primary_benchmark_ids": ["hotpotqa", "alfworld", "webshop", "fever"],
        "secondary_benchmark_ids": [],
        "unmodeled_benchmarks": [],
        "expected_route": "direct_portfolio",
        "gold_evidence_sections": ["Experiments / Experimental Setup", "Transfer Learning"],
        "benchmark_evidence": [
            evidence("hotpotqa", None, "Experiments / Experimental Setup", "knowledge_intensive_qa"),
            evidence("alfworld", None, "Experiments / Experimental Setup", "embodied_household"),
            evidence("webshop", None, "Experiments / Experimental Setup", "web_navigation"),
            evidence(
                "fever",
                None,
                "Experiments / Experimental Setup and Transfer Learning",
                "fact_verification",
            ),
        ],
        "evidence_files": ["assets/input/source_papers/extracted/2308.10144/main.tex"],
        "required_terms": [
            "four text-based benchmarks: HotpotQA",
            "ALFWorld and WebShop",
            "FEVER",
            "In this experiment, we use the HotpotQA dataset",
        ],
    },
    {
        "case_id": "fresh_004",
        "source_arxiv_id": "2305.14992",
        "source_title": "Reasoning with Language Model is Planning with World Model",
        "source_url": "https://arxiv.org/abs/2305.14992",
        "source_input_sections": {
            "introduction": ["Introduction"],
            "method": ["Reasoning via Planning"],
        },
        "primary_benchmark_ids": ["gsm8k"],
        "secondary_benchmark_ids": [],
        "unmodeled_benchmarks": ["Blocksworld", "PrOntoQA"],
        "expected_route": "base_benchmark_adaptation",
        "gold_evidence_sections": ["Plan Generation", "Math Reasoning", "Logical Reasoning"],
        "benchmark_evidence": [
            evidence(None, "Blocksworld", "Plan Generation", "classical_planning"),
            evidence("gsm8k", None, "Math Reasoning", "math_word_problem"),
            evidence(None, "PrOntoQA", "Logical Reasoning", "logical_reasoning"),
        ],
        "evidence_files": [
            "assets/input/source_papers/extracted/2305.14992/sections/experiment.tex"
        ],
        "required_terms": [
            "test cases from the \\blocksworld dataset",
            "Math reasoning tasks, such as GSM8k",
            "performance of our RAP framework on PrOntoQA",
        ],
    },
    {
        "case_id": "fresh_005",
        "source_arxiv_id": "2304.09842",
        "source_title": "Chameleon: Plug-and-Play Compositional Reasoning with Large Language Models",
        "source_url": "https://arxiv.org/abs/2304.09842",
        "source_input_sections": {
            "introduction": ["Introduction"],
            "method": ["General Framework", "Module Inventory", "Applications"],
        },
        "primary_benchmark_ids": ["tabmwp"],
        "secondary_benchmark_ids": [],
        "unmodeled_benchmarks": ["ScienceQA"],
        "expected_route": "base_benchmark_adaptation",
        "gold_evidence_sections": [
            "Applications of Chameleon",
            "Science Question Answering",
            "Tabular Mathematical Reasoning",
            "Experiments",
        ],
        "benchmark_evidence": [
            evidence(
                None,
                "ScienceQA",
                "Applications / Science Question Answering",
                "multimodal_science_qa",
            ),
            evidence(
                "tabmwp",
                None,
                "Applications / Tabular Mathematical Reasoning",
                "tabular_math_reasoning",
            ),
        ],
        "evidence_files": ["assets/input/source_papers/extracted/2304.09842/body.tex"],
        "required_terms": [
            "two challenging tasks: ScienceQA",
            "and TabMWP",
            "\\section{Experiments}",
        ],
    },
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_pre_gold_record() -> dict[str, Any]:
    """Require a clean five-case run that explicitly predates gold creation."""

    record = load_json(PRE_GOLD_RECORD)
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
        raise ValueError(f"fresh gold construction blocked by pre-run checks: {failed}")
    return {"path": PRE_GOLD_RECORD.relative_to(ROOT).as_posix(), "checks": checks}


def verify_source_terms(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Require every declared evidence phrase in the selected official source files."""

    paths = [ROOT / path for path in spec["evidence_files"]]
    missing_files = [path.as_posix() for path in paths if not path.is_file()]
    if missing_files:
        raise ValueError(f"missing source files for {spec['case_id']}: {missing_files}")
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
    pre_gold = verify_pre_gold_record()
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for spec in SPECS:
        source_checks = verify_source_terms(spec)
        payload = {
            key: value
            for key, value in spec.items()
            if key not in {"evidence_files", "required_terms"}
        }
        payload.update(
            {
                "matcher_visible": False,
                "gold_constructed_after_blind_run": True,
                "pre_gold_run_record": pre_gold["path"],
                "source_evidence_checks": source_checks,
            }
        )
        path = GOLD_DIR / f"{spec['case_id']}.gold.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        load_json(path)
        written.append(path.relative_to(ROOT).as_posix())
        print(
            json.dumps(
                {
                    "case_id": spec["case_id"],
                    "modeled": len(spec["primary_benchmark_ids"]),
                    "unmodeled": len(spec["unmodeled_benchmarks"]),
                    "route": spec["expected_route"],
                    "source_terms_verified": len(source_checks),
                },
                ensure_ascii=False,
            )
        )

    freeze = load_json(FREEZE_MANIFEST)
    freeze.update(
        {
            "gold_revealed": True,
            "gold_constructed_after_blind_run": True,
            "gold_files": written,
            "gold_construction_preconditions": pre_gold["checks"],
        }
    )
    FREEZE_MANIFEST.write_text(
        json.dumps(freeze, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    selection = load_json(PAPER_SELECTION)
    selection["gold_state"] = "REVEALED_AFTER_SEALED_BLIND_RUN"
    selection["gold_files"] = written
    PAPER_SELECTION.write_text(
        json.dumps(selection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"gold_files": written, "human_submission_required": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
