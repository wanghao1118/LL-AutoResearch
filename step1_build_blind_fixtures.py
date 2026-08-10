#!/usr/bin/env python3
"""Build blind paper fixtures from official arXiv source packages.

Overall logic:
1. Read only the source files that implement the Introduction and Method
   sections for each selected paper.
2. Remove LaTeX markup, comments, citations, result-heavy sentences, paper
   titles, method names, and every benchmark alias in the public catalog.
3. Write neutral ``case_NNN`` inputs that contain no paper identifier, source
   path, title, author, benchmark label, experiment section, or gold metadata.
4. Write literature-derived benchmark labels to a physically separate gold
   directory used only by the post-run evaluator.

The script is deterministic and exits when its own leakage scan finds a hidden
benchmark name or a paper-identity marker in matcher-visible text.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from autobench.catalog import load_catalog
from autobench.leakage import enforce_blind_input
from autobench.models import MethodInput


ROOT = Path(__file__).resolve().parent


CASE_SPECS = [
    {
        "case_id": "case_001",
        "introduction_files": [
            "assets/input/source_papers/extracted/2210.03629/iclr2023/text/intro.tex",
        ],
        "method_files": [
            "assets/input/source_papers/extracted/2210.03629/iclr2023/text/method.tex",
        ],
        "identity_markers": ["ReAct", "Synergizing Reasoning and Acting", "Yao et al."],
        "identity_replacements": {
            "ReAct": "METHOD_X",
            "\\model{}": "METHOD_X",
            "\\model": "METHOD_X",
            "\\reason{}": "REASONING_BASELINE",
            "\\reason": "REASONING_BASELINE",
            "\\act{}": "ACTION_BASELINE",
            "\\act": "ACTION_BASELINE",
        },
        "gold": {
            "source_arxiv_id": "2210.03629",
            "source_title": "ReAct: Synergizing Reasoning and Acting in Language Models",
            "source_url": "https://arxiv.org/abs/2210.03629",
            "source_input_sections": {
                "introduction": ["Introduction"],
                "method": ["ReAct: Synergizing Reasoning + Acting"],
            },
            "primary_benchmark_ids": ["hotpotqa", "fever", "alfworld", "webshop"],
            "secondary_benchmark_ids": [],
            "unmodeled_benchmarks": [],
            "expected_route": "direct_portfolio",
            "gold_evidence_sections": ["Knowledge-Intensive Reasoning Tasks", "Decision Making Tasks"],
            "benchmark_evidence": [
                {
                    "benchmark_id": "hotpotqa",
                    "role": "primary",
                    "evidence_section": "Knowledge-Intensive Reasoning Tasks",
                },
                {
                    "benchmark_id": "fever",
                    "role": "primary",
                    "evidence_section": "Knowledge-Intensive Reasoning Tasks",
                },
                {
                    "benchmark_id": "alfworld",
                    "role": "primary",
                    "evidence_section": "Decision Making Tasks",
                },
                {
                    "benchmark_id": "webshop",
                    "role": "primary",
                    "evidence_section": "Decision Making Tasks",
                },
            ],
        },
    },
    {
        "case_id": "case_002",
        "introduction_files": ["assets/input/source_papers/extracted/2303.11366/main.tex"],
        "introduction_slice": (r"\\section\{Introduction\}", r"\\section\{Related work\}"),
        "method_files": ["assets/input/source_papers/extracted/2303.11366/main.tex"],
        "method_slice": (
            r"\\section\{Reflexion: reinforcement via verbal reflection\}",
            r"\\section\{Experiments\}",
        ),
        "identity_markers": ["Reflexion", "Shinn et al."],
        "hidden_benchmark_aliases": ["LeetcodeHardGym", "LeetcodeHard", "MultiPL-E"],
        "identity_replacements": {"Reflexion": "METHOD_X"},
        "gold": {
            "source_arxiv_id": "2303.11366",
            "source_title": "Reflexion: Language Agents with Verbal Reinforcement Learning",
            "source_url": "https://arxiv.org/abs/2303.11366",
            "source_input_sections": {
                "introduction": ["Introduction"],
                "method": ["Reflexion: reinforcement via verbal reflection"],
            },
            "primary_benchmark_ids": [
                "alfworld",
                "hotpotqa",
                "humaneval",
                "leetcodehardgym",
            ],
            "secondary_benchmark_ids": ["mbpp", "multipl_e"],
            "unmodeled_benchmarks": [],
            "expected_route": "direct_portfolio",
            "gold_evidence_sections": [
                "Sequential decision making: ALFWorld",
                "Reasoning: HotpotQA",
                "Programming",
            ],
            "benchmark_evidence": [
                {
                    "benchmark_id": "alfworld",
                    "role": "primary",
                    "evidence_section": "Sequential decision making: ALFWorld",
                },
                {
                    "benchmark_id": "hotpotqa",
                    "role": "primary",
                    "evidence_section": "Reasoning: HotpotQA",
                },
                {
                    "benchmark_id": "humaneval",
                    "role": "primary",
                    "evidence_section": "Programming",
                },
                {
                    "benchmark_id": "mbpp",
                    "role": "secondary",
                    "evidence_section": "Programming",
                },
                {
                    "benchmark_id": "leetcodehardgym",
                    "role": "primary",
                    "evidence_section": "Programming",
                },
                {
                    "benchmark_id": "multipl_e",
                    "role": "secondary",
                    "evidence_section": "Programming",
                },
            ],
        },
    },
    {
        "case_id": "case_003",
        "introduction_files": [
            "assets/input/source_papers/extracted/2405.15793/sections/01_intro.tex",
        ],
        "method_files": [
            "assets/input/source_papers/extracted/2405.15793/sections/02_aci.tex",
            "assets/input/source_papers/extracted/2405.15793/sections/03_sweagent.tex",
        ],
        "identity_markers": ["SWE-agent", "Agent-Computer Interface", "ACI", "Yang et al."],
        "identity_replacements": {
            "SWE-agent": "METHOD_X",
            "SWE Agent": "METHOD_X",
            "Agent-Computer Interface": "specialized computer interaction interface",
            "agent-computer interface": "specialized computer interaction interface",
            "ACI": "INTERFACE_X",
        },
        "gold": {
            "source_arxiv_id": "2405.15793",
            "source_title": "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering",
            "source_url": "https://arxiv.org/abs/2405.15793",
            "source_input_sections": {
                "introduction": ["Introduction"],
                "method": [
                    "The Agent-Computer Interface",
                    "SWE-agent: Designing an ACI for Software Engineering",
                ],
            },
            "primary_benchmark_ids": ["swe_bench"],
            "secondary_benchmark_ids": ["humanevalfix"],
            "unmodeled_benchmarks": [],
            "expected_route": "direct_portfolio",
            "gold_evidence_sections": ["Experimental Setup"],
            "benchmark_evidence": [
                {
                    "benchmark_id": "swe_bench",
                    "role": "primary",
                    "evidence_section": "Experimental Setup",
                },
                {
                    "benchmark_id": "humanevalfix",
                    "role": "secondary",
                    "evidence_section": "Experimental Setup",
                },
            ],
        },
    },
]


RESULT_PHRASES = (
    "outperform",
    "state-of-the-art",
    "improvement of",
    "improvement over",
    "achieves improvements",
    "we report our main",
    "we perform an ablation",
    "we conduct empirical evaluations",
    "we perform experiments",
    "we evaluate on",
    "we primarily evaluate",
)


def _read_files(paths: Iterable[str]) -> str:
    return "\n".join((ROOT / path).read_text(encoding="utf-8", errors="replace") for path in paths)


def _slice_section(text: str, markers: tuple[str, str] | None) -> str:
    if markers is None:
        return text
    start_match = re.search(markers[0], text)
    end_match = re.search(markers[1], text)
    if start_match is None or end_match is None or end_match.start() <= start_match.end():
        raise ValueError(f"section markers not found or reversed: {markers}")
    return text[start_match.end() : end_match.start()]


def _strip_comments(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        kept: list[str] = []
        escaped = False
        for char in line:
            if char == "%" and not escaped:
                break
            kept.append(char)
            escaped = char == "\\" and not escaped
            if char != "\\":
                escaped = False
        lines.append("".join(kept))
    return "\n".join(lines)


def _replace_case_insensitive(text: str, old: str, new: str) -> str:
    escaped = re.escape(old)
    if old and old[0].isalnum() and old[-1].isalnum():
        escaped = rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])"
    return re.sub(escaped, lambda _: new, text, flags=re.IGNORECASE)


def _clean_tex(text: str, replacements: dict[str, str]) -> str:
    text = _strip_comments(text)
    for old, new in sorted(replacements.items(), key=lambda item: -len(item[0])):
        text = _replace_case_insensitive(text, old, new)
    text = re.sub(r"\\(?:cite|citep|citet|citealp|ref|autoref|cref|label)\*?\{[^{}]*\}", " ", text)
    text = re.sub(r"\\(?:input|include)\{[^{}]*\}", " ", text)
    text = re.sub(r"\\(?:begin|end)\{[^{}]*\}", " ", text)
    text = re.sub(r"\\(?:section|subsection|subsubsection|paragraph|myparagraph)\*?\{([^{}]*)\}", r"\n\1.\n", text)
    for _ in range(6):
        updated = re.sub(
            r"\\(?:textbf|textit|emph|texttt|underline|mbox|texorpdfstring)\{([^{}]*)\}",
            r"\1",
            text,
        )
        if updated == text:
            break
        text = updated
    text = re.sub(r"\\[a-zA-Z@]+\*?(?:\[[^\]]*\])?", " ", text)
    text = text.replace("{", " ").replace("}", " ")
    text = re.sub(r"\$[^$]*\$", " ", text)
    text = re.sub(r"~", " ", text)
    text = re.sub(r"\\[%&_#]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _redact_catalog_aliases(text: str, aliases: list[str]) -> str:
    for alias in sorted(aliases, key=lambda item: (-len(item), item.casefold())):
        if len(alias.strip()) < 4:
            continue
        pattern = r"(?<![A-Za-z0-9])" + re.escape(alias) + r"(?![A-Za-z0-9])"
        text = re.sub(pattern, "[REDACTED_BENCHMARK]", text, flags=re.IGNORECASE)
    return text


def _drop_result_sentences(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    kept: list[str] = []
    for sentence in sentences:
        folded = sentence.casefold()
        if any(phrase in folded for phrase in RESULT_PHRASES):
            continue
        if re.search(r"\b\d+(?:\.\d+)?\s*%", sentence):
            continue
        kept.append(sentence.strip())
    return " ".join(sentence for sentence in kept if sentence)


def build_fixture(spec: dict, aliases: list[str], catalog_path: Path) -> tuple[dict, dict]:
    intro_raw = _read_files(spec["introduction_files"])
    method_raw = _read_files(spec["method_files"])
    intro_raw = _slice_section(intro_raw, spec.get("introduction_slice"))
    method_raw = _slice_section(method_raw, spec.get("method_slice"))
    introduction = _clean_tex(intro_raw, spec["identity_replacements"])
    method = _clean_tex(method_raw, spec["identity_replacements"])
    for old, new in sorted(spec["identity_replacements"].items(), key=lambda item: -len(item[0])):
        introduction = _replace_case_insensitive(introduction, old, new)
        method = _replace_case_insensitive(method, old, new)
    hidden_benchmark_aliases = spec.get("hidden_benchmark_aliases", [])
    redaction_aliases = [*aliases, *hidden_benchmark_aliases]
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
        },
    }
    method_input = MethodInput.from_dict(payload)
    catalog = load_catalog(catalog_path)
    report = enforce_blind_input(
        method_input,
        catalog,
        [*spec["identity_markers"], *hidden_benchmark_aliases],
    )
    gold = {
        "case_id": spec["case_id"],
        **spec["gold"],
        "matcher_visible": False,
        "leakage_scan": asdict(report),
    }
    return payload, gold


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default="configs/benchmark_catalog.json")
    parser.add_argument("--cases-dir", default="assets/input/blind_cases")
    parser.add_argument("--gold-dir", default="assets/input/blind_gold")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    catalog_path = ROOT / args.catalog
    catalog = load_catalog(catalog_path)
    aliases = [alias for record in catalog for alias in [record.name, *record.aliases]]
    cases_dir = ROOT / args.cases_dir
    gold_dir = ROOT / args.gold_dir
    cases_dir.mkdir(parents=True, exist_ok=True)
    gold_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "schema_version": "1.0",
        "case_ids": [],
        "visible_fields": ["case_id", "introduction", "method", "constraints"],
        "gold_directory_passed_to_matcher": False,
    }
    for spec in CASE_SPECS:
        payload, gold = build_fixture(spec, aliases, catalog_path)
        case_path = cases_dir / f"{spec['case_id']}.json"
        gold_path = gold_dir / f"{spec['case_id']}.gold.json"
        case_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        gold_path.write_text(json.dumps(gold, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        manifest["case_ids"].append(spec["case_id"])
        print(
            json.dumps(
                {
                    "case_id": spec["case_id"],
                    "visible_chars": len(payload["introduction"]) + len(payload["method"]),
                    "leakage_passed": gold["leakage_scan"]["passed"],
                },
                ensure_ascii=False,
            )
        )
    (cases_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
