"""Automatic post-match comparison against literature-derived benchmark gold.

The blind matcher exits before this module opens source identity or benchmark
labels. This module then treats the paper evidence recorded in the evaluator as
the reference, assigns a deterministic MATCH/PARTIAL/MISMATCH decision, and
turns every miss, extra, catalog gap, or route error into an optimization
signal. It replaces the former researcher-submission gate while preserving the
same source-versus-recommendation comparison contract.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


AUTO_DECISIONS = ("MATCH", "PARTIAL", "MISMATCH")


def initial_automatic_review_state() -> dict[str, Any]:
    """Return the post-match source-comparison state without a user gate."""

    return {
        "status": "AUTOMATIC_LITERATURE_CHECK_PENDING",
        "validation_mode": "post_match_source_comparison",
        "human_submission_required": False,
        "trigger": "after blind matching, load source-paper benchmark evidence in the evaluator process",
        "decisions": list(AUTO_DECISIONS),
    }


def _case_decision(case: dict[str, Any]) -> dict[str, Any]:
    """Classify one post-run paper comparison and expose actionable causes."""

    comparison = case["comparison"]
    missing = [
        *comparison["primary_missing_from_selected"],
        *comparison["secondary_missing_from_selected"],
        *comparison.get("admitted_missing_from_selected", []),
    ]
    extras = comparison["selected_not_used_in_paper"]
    unmodeled = case.get("unmodeled_gold", [])
    selected_matches = [
        *comparison["selected_primary_matches"],
        *comparison["selected_secondary_matches"],
        *comparison.get("selected_admitted_matches", []),
    ]
    profile = case.get("profile", {})
    inferred_known = set(profile.get("task_families", []))
    inferred_uncovered = set(profile.get("uncovered_task_families", []))
    inferred_task_families = inferred_known | inferred_uncovered
    actual_unmodeled_families = {
        item["task_family"]
        for item in case.get("actual_benchmarks", [])
        if item.get("role") == "unmodeled" and item.get("task_family")
    }
    matched_unmodeled_families = sorted(actual_unmodeled_families & inferred_task_families)
    missing_unmodeled_families = sorted(actual_unmodeled_families - inferred_task_families)
    uncovered_family_recall = (
        len(matched_unmodeled_families) / len(actual_unmodeled_families)
        if actual_unmodeled_families
        else 1.0
    )
    error_types: list[str] = []
    feedback: list[str] = []

    if not case["leakage_passed"] or case["matcher_loaded_hidden_labels"]:
        error_types.append("BLIND_PROTOCOL_FAILURE")
        feedback.append("restore matcher isolation before interpreting benchmark quality")
    if unmodeled:
        error_types.append("CATALOG_GAP")
        feedback.append("verify and type the paper-backed benchmarks that remain outside the catalog")
    if missing_unmodeled_families:
        error_types.append("UNMODELED_TASK_INFERENCE_GAP")
        feedback.append("expand task-family inference for paper benchmarks outside the current catalog")
    if missing:
        error_types.append("PORTFOLIO_RECALL_GAP")
        feedback.append("improve task, modality, environment, or suite-breadth inference for missed paper choices")
    if extras:
        error_types.append("PORTFOLIO_PRECISION_GAP")
        feedback.append("tighten specialization and environment gates for paper-external selections")
    if not case["route_correct"]:
        error_types.append("ROUTE_ERROR")
        feedback.append("align direct reuse versus adaptation/synthesis with uncovered task families")

    evidence_complete = bool(
        case.get("source_url")
        and case.get("source_input_sections")
        and case.get("gold_evidence_sections")
        and case.get("actual_benchmarks")
    )
    protocol_clean = case["leakage_passed"] and not case["matcher_loaded_hidden_labels"]
    quality_errors = [
        item
        for item in error_types
        if item not in {"CATALOG_GAP"}
    ]
    exact = not quality_errors and evidence_complete and protocol_clean
    if exact:
        decision = "MATCH"
    elif (selected_matches or matched_unmodeled_families) and protocol_clean:
        decision = "PARTIAL"
    else:
        decision = "MISMATCH"
    return {
        "case_id": case["case_id"],
        "source_title": case["source_title"],
        "source_url": case["source_url"],
        "source_input_sections": case["source_input_sections"],
        "gold_evidence_sections": case["gold_evidence_sections"],
        "source_evidence_complete": evidence_complete,
        "decision": decision,
        "selected": case["selected"],
        "actual_benchmarks": [
            {
                "benchmark_id": item.get("benchmark_id"),
                "benchmark_name": item["benchmark_name"],
                "evidence_section": item["evidence_section"],
                "role": item["role"],
                "task_family": item.get("task_family"),
            }
            for item in case["actual_benchmarks"]
        ],
        "selected_matches": selected_matches,
        "missing": missing,
        "extras": extras,
        "unmodeled": unmodeled,
        "actual_unmodeled_task_families": sorted(actual_unmodeled_families),
        "inferred_task_families": sorted(inferred_task_families),
        "inferred_uncovered_task_families": sorted(inferred_uncovered),
        "matched_unmodeled_task_families": matched_unmodeled_families,
        "missing_unmodeled_task_families": missing_unmodeled_families,
        "unmodeled_task_family_recall": uncovered_family_recall,
        "route": case["route"],
        "expected_route": case["expected_route"],
        "route_correct": case["route_correct"],
        "selected_modeled_recall": case["selected_modeled_recall"],
        "selected_actual_precision": comparison["selected_actual_precision"],
        "error_types": error_types,
        "optimization_feedback": feedback,
    }


def review_evaluation(
    evaluation: dict[str, Any],
    *,
    evidence_class: str,
) -> dict[str, Any]:
    """Review every evaluated paper and aggregate strict exact-match quality."""

    cases = [_case_decision(case) for case in evaluation["cases"]]
    decisions = [case["decision"] for case in cases]
    if "MISMATCH" in decisions:
        status = "AUTOMATED_LITERATURE_AUDIT_MISMATCH"
    elif "PARTIAL" in decisions:
        status = "AUTOMATED_LITERATURE_AUDIT_PARTIAL"
    else:
        status = "AUTOMATED_LITERATURE_AUDIT_CONFIRMED"
    return {
        "schema_version": "1.0",
        "reviewer": "AUTO_LITERATURE_EVALUATOR",
        "validation_mode": "post_match_source_comparison",
        "human_submission_required": False,
        "evidence_class": evidence_class,
        "status": status,
        "case_count": len(cases),
        "decision_counts": {
            decision: sum(item == decision for item in decisions)
            for decision in AUTO_DECISIONS
        },
        "all_source_evidence_complete": all(case["source_evidence_complete"] for case in cases),
        "all_blind_checks_passed": evaluation["aggregate"]["all_leakage_checks_passed"]
        and not evaluation["aggregate"]["any_matcher_loaded_hidden_labels"],
        "aggregate": evaluation["aggregate"],
        "cases": cases,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    """Render source evidence, exact comparison, and optimization feedback."""

    lines = [
        "# Auto-Bench Automatic Literature Review",
        "",
        f"- Status: **{payload['status']}**",
        f"- Evidence class: **{payload['evidence_class']}**",
        f"- Reviewer: **{payload['reviewer']}**",
        f"- Human submission required: **{payload['human_submission_required']}**",
        f"- Blind checks passed: **{payload['all_blind_checks_passed']}**",
        "",
    ]
    for case in payload["cases"]:
        lines.extend(
            [
                f"## {case['case_id']} — {case['source_title']}",
                "",
                f"- Source: {case['source_url']}",
                f"- Source sections: `{case['source_input_sections']}`",
                f"- Gold evidence sections: `{case['gold_evidence_sections']}`",
                f"- Decision: **{case['decision']}**",
                f"- Selected: `{case['selected']}`",
                f"- Matches: `{case['selected_matches']}`",
                f"- Missing: `{case['missing']}`",
                f"- Extras: `{case['extras']}`",
                f"- Outside catalog: `{case['unmodeled']}`",
                f"- Outside-catalog task-family recall: `{case['unmodeled_task_family_recall']:.4f}`",
                f"- All inferred task families: `{case['inferred_task_families']}`",
                f"- Matched outside-catalog task families: `{case['matched_unmodeled_task_families']}`",
                f"- Missing outside-catalog task families: `{case['missing_unmodeled_task_families']}`",
                f"- Route: `{case['route']}`; expected `{case['expected_route']}`",
                f"- Selected recall: `{case['selected_modeled_recall']:.4f}`",
                f"- Selected precision: `{case['selected_actual_precision']:.4f}`",
                f"- Error types: `{case['error_types']}`",
                f"- Optimization feedback: `{case['optimization_feedback']}`",
                "",
            ]
        )
    return "\n".join(lines)


def write_review(
    evaluation_path: str | Path,
    output_json_path: str | Path,
    output_markdown_path: str | Path,
    *,
    evidence_class: str,
) -> dict[str, Any]:
    """Read an evaluation, write both review artifacts, and verify readback."""

    evaluation = json.loads(Path(evaluation_path).read_text(encoding="utf-8"))
    payload = review_evaluation(evaluation, evidence_class=evidence_class)
    json_path = Path(output_json_path)
    markdown_path = Path(output_markdown_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    reopened = json.loads(json_path.read_text(encoding="utf-8"))
    if reopened["status"] != payload["status"]:
        raise ValueError("automatic literature review readback failed")
    if payload["status"] not in markdown_path.read_text(encoding="utf-8"):
        raise ValueError("automatic literature review Markdown verification failed")
    return payload
