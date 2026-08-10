"""Compare two blind-matching iterations after a completed human audit."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any


def _case_metrics(case: dict[str, Any]) -> dict[str, Any]:
    """Derive portfolio recovery metrics for old and new result schemas."""

    selected = case["selected"]
    admitted_gold = [
        item["benchmark_id"]
        for item in case.get("admitted_gold", [])
        if item.get("benchmark_id")
    ]
    modeled_gold = [*case["primary_gold"], *case["secondary_gold"], *admitted_gold]
    matches = [benchmark_id for benchmark_id in selected if benchmark_id in modeled_gold]
    extras = [benchmark_id for benchmark_id in selected if benchmark_id not in modeled_gold]
    missing = [benchmark_id for benchmark_id in modeled_gold if benchmark_id not in selected]
    return {
        "selected": selected,
        "modeled_gold": modeled_gold,
        "selected_matches": matches,
        "selected_missing": missing,
        "selected_extras": extras,
        "selected_modeled_recall": len(matches) / len(modeled_gold) if modeled_gold else 1.0,
        "selected_actual_precision": len(matches) / len(selected) if selected else 0.0,
        "rank_by_modeled_gold": {
            benchmark_id: (
                case["top_6"].index(benchmark_id) + 1 if benchmark_id in case["top_6"] else None
            )
            for benchmark_id in modeled_gold
        },
    }


def compare_iterations(
    previous_evaluation: dict[str, Any],
    current_evaluation: dict[str, Any],
    previous_verdict: dict[str, Any],
    *,
    previous_iteration: int = 1,
    current_iteration: int = 2,
) -> dict[str, Any]:
    """Join human feedback with before/after portfolios and metric changes."""

    if previous_iteration >= current_iteration:
        raise ValueError("current_iteration must be greater than previous_iteration")

    previous_cases = {case["case_id"]: case for case in previous_evaluation["cases"]}
    current_cases = {case["case_id"]: case for case in current_evaluation["cases"]}
    review_items = {item["case_id"]: item for item in previous_verdict.get("items", [])}
    if set(previous_cases) != set(current_cases):
        raise ValueError("previous and current evaluations must contain the same case IDs")

    rows = []
    for case_id in sorted(current_cases):
        previous = previous_cases[case_id]
        current = current_cases[case_id]
        before = _case_metrics(previous)
        after = _case_metrics(current)
        previous_unmodeled = previous.get("unmodeled_gold", [])
        current_unmodeled = current.get("unmodeled_gold", [])
        rows.append(
            {
                "case_id": case_id,
                "source_title": current["source_title"],
                "source_url": current["source_url"],
                "previous_human_decision": review_items.get(case_id, {}).get("status"),
                "previous_human_notes": review_items.get(case_id, {}).get("notes"),
                "before": before,
                "after": after,
                "delta": {
                    "selected_modeled_recall": (
                        after["selected_modeled_recall"] - before["selected_modeled_recall"]
                    ),
                    "selected_actual_precision": (
                        after["selected_actual_precision"] - before["selected_actual_precision"]
                    ),
                },
                "newly_selected": [item for item in after["selected"] if item not in before["selected"]],
                "removed_selected": [item for item in before["selected"] if item not in after["selected"]],
                "previous_unmodeled_gold": previous_unmodeled,
                "resolved_unmodeled_gold": [
                    item for item in previous_unmodeled if item not in current_unmodeled
                ],
                "unmodeled_gold": current_unmodeled,
            }
        )

    before_recall = mean(row["before"]["selected_modeled_recall"] for row in rows)
    after_recall = mean(row["after"]["selected_modeled_recall"] for row in rows)
    before_precision = mean(row["before"]["selected_actual_precision"] for row in rows)
    after_precision = mean(row["after"]["selected_actual_precision"] for row in rows)
    previous_aggregate = previous_evaluation["aggregate"]
    current_aggregate = current_evaluation["aggregate"]
    aggregate = {
        "previous_human_status": previous_verdict["status"],
        "before": {
            "mean_primary_recall_at_5": previous_aggregate["mean_primary_recall_at_5"],
            "mean_primary_recall_at_6": previous_aggregate["mean_primary_recall_at_6"],
            "mean_primary_mrr": previous_aggregate["mean_primary_mrr"],
            "mean_selected_modeled_recall": before_recall,
            "mean_selected_actual_precision": before_precision,
        },
        "after": {
            "mean_primary_recall_at_5": current_aggregate["mean_primary_recall_at_5"],
            "mean_primary_recall_at_6": current_aggregate["mean_primary_recall_at_6"],
            "mean_primary_mrr": current_aggregate["mean_primary_mrr"],
            "mean_selected_modeled_recall": after_recall,
            "mean_selected_actual_precision": after_precision,
        },
    }
    aggregate["delta"] = {
        key: aggregate["after"][key] - aggregate["before"][key]
        for key in aggregate["before"]
    }
    return {
        "schema_version": "1.0",
        "comparison": f"literature_audit_round_{previous_iteration}_to_round_{current_iteration}",
        "previous_iteration": previous_iteration,
        "current_iteration": current_iteration,
        "interpretation": (
            f"Round {current_iteration} is a feedback-driven regression on the same papers, "
            "not a new untouched holdout. "
            "A fresh-paper audit is still needed for an unbiased generalization estimate."
        ),
        "aggregate": aggregate,
        "cases": rows,
    }


def render_iteration_markdown(payload: dict[str, Any]) -> str:
    """Render the complete feedback-to-change trace without hiding misses."""

    aggregate = payload["aggregate"]
    previous_iteration = int(payload.get("previous_iteration", 1))
    current_iteration = int(payload.get("current_iteration", 2))
    lines = [
        f"# Auto-Bench Literature Audit: Round {previous_iteration} → Round {current_iteration}",
        "",
        f"- Round {previous_iteration} human status: **{aggregate['previous_human_status']}**",
        f"- Interpretation: {payload['interpretation']}",
        "",
        "## Aggregate change",
        "",
        f"| Metric | Round {previous_iteration} | Round {current_iteration} | Delta |",
        "|---|---:|---:|---:|",
    ]
    for key, label in (
        ("mean_primary_recall_at_5", "Mean primary Recall@5"),
        ("mean_primary_recall_at_6", "Mean primary Recall@6"),
        ("mean_primary_mrr", "Mean primary MRR"),
        ("mean_selected_modeled_recall", "Mean selected modeled recall"),
        ("mean_selected_actual_precision", "Mean selected actual precision"),
    ):
        lines.append(
            f"| {label} | {aggregate['before'][key]:.4f} | "
            f"{aggregate['after'][key]:.4f} | {aggregate['delta'][key]:+.4f} |"
        )
    for case in payload["cases"]:
        before = case["before"]
        after = case["after"]
        lines.extend(
            [
                "",
                f"## {case['case_id']} — {case['source_title']}",
                "",
                f"- Previous human judgement: **{case['previous_human_decision']}**",
                f"- Previous human note: {case['previous_human_notes']}",
                f"- Selected before: `{before['selected']}`",
                f"- Selected after: `{after['selected']}`",
                f"- Newly selected: `{case['newly_selected']}`",
                f"- Removed from selection: `{case['removed_selected']}`",
                f"- Modeled matches before: `{before['selected_matches']}`",
                f"- Modeled matches after: `{after['selected_matches']}`",
                f"- Modeled misses before: `{before['selected_missing']}`",
                f"- Modeled misses after: `{after['selected_missing']}`",
                f"- Selected modeled recall: {before['selected_modeled_recall']:.4f} → "
                f"{after['selected_modeled_recall']:.4f}",
                f"- Selected actual precision: {before['selected_actual_precision']:.4f} → "
                f"{after['selected_actual_precision']:.4f}",
                f"- Modeled-gold ranks before: `{before['rank_by_modeled_gold']}`",
                f"- Modeled-gold ranks after: `{after['rank_by_modeled_gold']}`",
                f"- Paper choices newly added to the catalog: `{case['resolved_unmodeled_gold']}`",
                f"- Paper choices still outside the catalog: `{case['unmodeled_gold']}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Reading rule",
            "",
            "Selected modeled recall excludes paper choices that remain outside the public catalog. "
            "Those choices stay visible above and must be considered in the human MATCH/PARTIAL/MISMATCH decision.",
            "",
        ]
    )
    return "\n".join(lines)


def write_iteration_report(
    previous_evaluation_path: str | Path,
    current_evaluation_path: str | Path,
    previous_verdict_path: str | Path,
    output_json_path: str | Path,
    output_markdown_path: str | Path,
    *,
    previous_iteration: int = 1,
    current_iteration: int = 2,
) -> dict[str, Any]:
    """Read, compare, write, and reopen both iteration-report artifacts."""

    previous_evaluation = json.loads(Path(previous_evaluation_path).read_text(encoding="utf-8"))
    current_evaluation = json.loads(Path(current_evaluation_path).read_text(encoding="utf-8"))
    previous_verdict = json.loads(Path(previous_verdict_path).read_text(encoding="utf-8"))
    payload = compare_iterations(
        previous_evaluation,
        current_evaluation,
        previous_verdict,
        previous_iteration=previous_iteration,
        current_iteration=current_iteration,
    )
    output_json = Path(output_json_path)
    output_markdown = Path(output_markdown_path)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_markdown.write_text(render_iteration_markdown(payload), encoding="utf-8")
    json.loads(output_json.read_text(encoding="utf-8"))
    marker = f"Round {previous_iteration} → Round {current_iteration}"
    if marker not in output_markdown.read_text(encoding="utf-8"):
        raise ValueError("iteration Markdown verification failed")
    return payload
