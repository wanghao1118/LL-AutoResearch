#!/usr/bin/env python3
"""Automatically compare one sealed Auto-Bench plan with source-paper evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
DEFAULT_CATALOG = SKILL_ROOT / "assets/benchmark_catalog.json"
sys.path.insert(0, str(SCRIPT_DIR))

from autobench.auto_literature_review import render_markdown, review_evaluation  # noqa: E402
from autobench.catalog import load_catalog  # noqa: E402


ROUTES = {"direct_portfolio", "base_benchmark_adaptation", "new_benchmark_synthesis"}
ROLES = {"primary", "secondary", "unmodeled"}


def parse_args() -> argparse.Namespace:
    """Parse portable automatic-comparison arguments."""

    parser = argparse.ArgumentParser(
        description="Compare a sealed benchmark plan with post-match paper evidence."
    )
    parser.add_argument("--plan", required=True)
    parser.add_argument("--paper-evidence", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-markdown", required=True)
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    parser.add_argument(
        "--evidence-class",
        required=True,
        choices=("fresh_holdout", "feedback_regression", "untouched_holdout"),
    )
    return parser.parse_args()


def require_text(payload: dict[str, Any], key: str) -> str:
    """Return one required non-empty string."""

    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"paper evidence field {key} must be a non-empty string")
    return value.strip()


def infer_expected_route(actual_benchmarks: list[dict[str, Any]]) -> str:
    """Infer reuse versus construction from catalog coverage of paper constructs."""

    modeled = sum(item["role"] in {"primary", "secondary"} for item in actual_benchmarks)
    unmodeled = sum(item["role"] == "unmodeled" for item in actual_benchmarks)
    if modeled and not unmodeled:
        return "direct_portfolio"
    if modeled and unmodeled:
        return "base_benchmark_adaptation"
    return "new_benchmark_synthesis"


def validate_evidence(
    evidence: dict[str, Any],
    catalog_ids: set[str],
) -> tuple[list[dict[str, Any]], str]:
    """Validate paper provenance and normalize every benchmark record."""

    require_text(evidence, "case_id")
    require_text(evidence, "source_title")
    require_text(evidence, "source_url")
    for key in ("source_input_sections", "gold_evidence_sections"):
        value = evidence.get(key)
        if not isinstance(value, list) or not value or not all(
            isinstance(item, str) and item.strip() for item in value
        ):
            raise ValueError(f"paper evidence field {key} must be a non-empty string list")
    raw_benchmarks = evidence.get("actual_benchmarks")
    if not isinstance(raw_benchmarks, list) or not raw_benchmarks:
        raise ValueError("actual_benchmarks must be a non-empty list")

    normalized: list[dict[str, Any]] = []
    names: set[str] = set()
    for index, raw in enumerate(raw_benchmarks, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"actual_benchmarks[{index}] must be an object")
        name = require_text(raw, "benchmark_name")
        role = require_text(raw, "role")
        task_family = require_text(raw, "task_family")
        evidence_section = require_text(raw, "evidence_section")
        if role not in ROLES:
            raise ValueError(f"unsupported benchmark role: {role}")
        benchmark_id = raw.get("benchmark_id")
        if benchmark_id is not None:
            if not isinstance(benchmark_id, str) or benchmark_id not in catalog_ids:
                raise ValueError(f"unknown catalog benchmark_id: {benchmark_id}")
            if role == "unmodeled":
                raise ValueError("a catalog benchmark_id cannot use role unmodeled")
        elif role != "unmodeled":
            raise ValueError("primary and secondary paper benchmarks require a catalog benchmark_id")
        key = name.casefold()
        if key in names:
            raise ValueError(f"duplicate benchmark_name: {name}")
        names.add(key)
        normalized.append(
            {
                "benchmark_id": benchmark_id,
                "benchmark_name": name,
                "role": role,
                "task_family": task_family,
                "evidence_section": evidence_section,
                "evidence_locator": str(raw.get("evidence_locator", "")).strip(),
                "evidence_summary": str(raw.get("evidence_summary", "")).strip(),
            }
        )

    expected_route = evidence.get("expected_route") or infer_expected_route(normalized)
    if expected_route not in ROUTES:
        raise ValueError(f"unsupported expected_route: {expected_route}")
    return normalized, expected_route


def reciprocal_rank(top_ids: list[str], gold_ids: set[str]) -> float:
    """Return reciprocal rank for the first matching benchmark."""

    for rank, benchmark_id in enumerate(top_ids, start=1):
        if benchmark_id in gold_ids:
            return 1.0 / rank
    return 0.0


def build_evaluation(
    plan: dict[str, Any],
    evidence: dict[str, Any],
    actual_benchmarks: list[dict[str, Any]],
    expected_route: str,
) -> dict[str, Any]:
    """Construct the evaluator contract consumed by the automatic reviewer."""

    if plan.get("case_id") != evidence.get("case_id"):
        raise ValueError("plan case_id does not match paper evidence case_id")
    selected = list(plan.get("selected_benchmarks", []))
    top_ids = [item["benchmark_id"] for item in plan.get("ranked_candidates", [])[:6]]
    by_role = {
        role: {
            item["benchmark_id"]
            for item in actual_benchmarks
            if item["role"] == role and item["benchmark_id"]
        }
        for role in ("primary", "secondary")
    }
    modeled_ids = by_role["primary"] | by_role["secondary"]
    selected_set = set(selected)
    top_set = set(top_ids)
    selected_primary = sorted(selected_set & by_role["primary"])
    selected_secondary = sorted(selected_set & by_role["secondary"])
    primary_missing = sorted(by_role["primary"] - selected_set)
    secondary_missing = sorted(by_role["secondary"] - selected_set)
    extras = [benchmark_id for benchmark_id in selected if benchmark_id not in modeled_ids]
    selected_matches = len(selected_set & modeled_ids)
    selected_modeled_recall = selected_matches / len(modeled_ids) if modeled_ids else 1.0
    selected_actual_precision = selected_matches / len(selected) if selected else 1.0
    leakage = plan.get("provenance", {}).get("leakage_scan", {})
    leakage_passed = bool(leakage.get("passed", False))
    matcher_loaded_hidden_labels = bool(plan.get("provenance", {}).get("blind_gold_loaded", False))

    enriched_actual = []
    rank_lookup = {benchmark_id: rank for rank, benchmark_id in enumerate(top_ids, start=1)}
    for item in actual_benchmarks:
        enriched_actual.append(
            {
                **item,
                "selected_by_autobench": bool(item["benchmark_id"] in selected_set),
                "rank_in_autobench": rank_lookup.get(item["benchmark_id"]),
            }
        )

    comparison = {
        "selected_primary_matches": selected_primary,
        "selected_secondary_matches": selected_secondary,
        "selected_admitted_matches": [],
        "primary_missing_from_selected": primary_missing,
        "secondary_missing_from_selected": secondary_missing,
        "admitted_missing_from_selected": [],
        "selected_not_used_in_paper": extras,
        "top_6_primary_matches": sorted(top_set & by_role["primary"]),
        "top_6_secondary_matches": sorted(top_set & by_role["secondary"]),
        "top_6_admitted_matches": [],
        "top_6_primary_missing": sorted(by_role["primary"] - top_set),
        "selected_actual_precision": selected_actual_precision,
    }
    case = {
        "case_id": plan["case_id"],
        "source_title": evidence["source_title"],
        "source_url": evidence["source_url"],
        "source_input_sections": evidence["source_input_sections"],
        "gold_evidence_sections": evidence["gold_evidence_sections"],
        "actual_benchmarks": enriched_actual,
        "primary_gold": sorted(by_role["primary"]),
        "secondary_gold": sorted(by_role["secondary"]),
        "unmodeled_gold": [
            item["benchmark_name"] for item in actual_benchmarks if item["role"] == "unmodeled"
        ],
        "admitted_gold": [],
        "top_6": top_ids,
        "selected": selected,
        "profile": plan.get("profile", {}),
        "comparison": comparison,
        "primary_mrr": reciprocal_rank(top_ids, by_role["primary"]),
        "selected_modeled_recall": selected_modeled_recall,
        "route": plan["route"],
        "expected_route": expected_route,
        "route_correct": plan["route"] == expected_route,
        "leakage_passed": leakage_passed,
        "matcher_loaded_hidden_labels": matcher_loaded_hidden_labels,
    }
    aggregate = {
        "case_count": 1,
        "mean_primary_recall_at_5": (
            len(set(top_ids[:5]) & by_role["primary"]) / len(by_role["primary"])
            if by_role["primary"]
            else 1.0
        ),
        "mean_primary_recall_at_6": (
            len(top_set & by_role["primary"]) / len(by_role["primary"])
            if by_role["primary"]
            else 1.0
        ),
        "mean_primary_mrr": case["primary_mrr"],
        "mean_selected_modeled_recall": selected_modeled_recall,
        "mean_selected_actual_precision": selected_actual_precision,
        "route_accuracy": 1.0 if case["route_correct"] else 0.0,
        "all_leakage_checks_passed": leakage_passed,
        "any_matcher_loaded_hidden_labels": matcher_loaded_hidden_labels,
    }
    return {"schema_version": "1.0", "aggregate": aggregate, "cases": [case]}


def main() -> int:
    """Validate inputs, run automatic comparison, and write verified reports."""

    args = parse_args()
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    evidence = json.loads(Path(args.paper_evidence).read_text(encoding="utf-8"))
    catalog_ids = {record.benchmark_id for record in load_catalog(args.catalog)}
    actual_benchmarks, expected_route = validate_evidence(evidence, catalog_ids)
    evaluation = build_evaluation(plan, evidence, actual_benchmarks, expected_route)
    verdict = review_evaluation(evaluation, evidence_class=args.evidence_class)
    verdict["paper_evidence_artifact"] = str(Path(args.paper_evidence).resolve())
    verdict["paper_evidence"] = evidence

    json_path = Path(args.output_json)
    markdown_path = Path(args.output_markdown)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(verdict, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(verdict), encoding="utf-8")
    reopened = json.loads(json_path.read_text(encoding="utf-8"))
    if reopened["decision_counts"] != verdict["decision_counts"]:
        raise ValueError("automatic review readback failed")
    print(
        json.dumps(
            {
                "status": verdict["status"],
                "decision_counts": verdict["decision_counts"],
                "error_types": verdict["cases"][0]["error_types"],
                "human_submission_required": False,
                "output_json": str(json_path.resolve()),
                "output_markdown": str(markdown_path.resolve()),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
