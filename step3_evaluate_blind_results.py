#!/usr/bin/env python3
"""Evaluate completed blind runs against literature-derived hidden labels.

The function first verifies that every worker report exists and declares that no
hidden labels were loaded.  Only after that precondition passes does it open the
separate gold files.  This ordering prevents the matcher and evaluator roles
from being conflated.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any

from autobench.catalog import load_catalog


ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-dir", default="assets/output/blind_runs")
    parser.add_argument("--gold-dir", default="assets/input/blind_gold")
    parser.add_argument("--matcher-cases-dir", default="assets/input/blind_cases")
    parser.add_argument("--catalog", default="configs/benchmark_catalog.json")
    parser.add_argument("--output", default="assets/output/blind_evaluation.json")
    parser.add_argument("--report", default="assets/output/blind_evaluation.md")
    parser.add_argument("--minimum-cases", type=int, default=3)
    return parser.parse_args()


def recall_at_k(ranked_ids: list[str], gold_ids: list[str], k: int) -> float:
    if not gold_ids:
        return 1.0
    return len(set(ranked_ids[:k]) & set(gold_ids)) / len(set(gold_ids))


def reciprocal_rank(ranked_ids: list[str], gold_ids: list[str]) -> float:
    gold = set(gold_ids)
    for index, benchmark_id in enumerate(ranked_ids, start=1):
        if benchmark_id in gold:
            return 1.0 / index
    return 0.0


def evaluate_case(
    plan: dict[str, Any],
    gold: dict[str, Any],
    benchmark_names: dict[str, str],
    benchmark_aliases: dict[str, str] | None = None,
    matcher_visible_input: str | None = None,
) -> dict[str, Any]:
    """Join one blind plan with post-run gold and newly admitted catalog IDs.

    A frozen gold file may name a benchmark that was outside the catalog at
    freeze time. If that exact public name or alias is admitted later, the
    evaluator resolves it only after the matcher has exited. This improves the
    current comparison without changing the preserved first-run artifact or
    exposing the mapping to the matcher.
    """

    ranked = [candidate["benchmark_id"] for candidate in plan["ranked_candidates"]]
    primary = gold["primary_benchmark_ids"]
    secondary = gold["secondary_benchmark_ids"]
    selected = plan["selected_benchmarks"]
    rank_by_id = {benchmark_id: rank for rank, benchmark_id in enumerate(ranked, start=1)}
    alias_to_id = benchmark_aliases or {}
    admitted_ids: list[str] = []
    admitted_gold: list[dict[str, str]] = []

    actual_benchmarks: list[dict[str, Any]] = []
    for evidence in gold["benchmark_evidence"]:
        benchmark_id = evidence.get("benchmark_id")
        original_name = evidence.get("benchmark_name")
        benchmark_name = original_name or benchmark_names.get(
            benchmark_id,
            benchmark_id,
        )
        admitted_after_freeze = False
        if not benchmark_id and benchmark_name:
            benchmark_id = alias_to_id.get(str(benchmark_name).casefold().strip())
            admitted_after_freeze = benchmark_id is not None
        if admitted_after_freeze:
            admitted_ids.append(benchmark_id)
            admitted_gold.append(
                {
                    "benchmark_name": str(benchmark_name),
                    "benchmark_id": benchmark_id,
                }
            )
        actual_benchmarks.append(
            {
                **evidence,
                "benchmark_id": benchmark_id,
                "benchmark_name": benchmark_name,
                "role": "admitted_after_freeze" if admitted_after_freeze else evidence["role"],
                "selected_by_autobench": benchmark_id in selected if benchmark_id else False,
                "rank_in_autobench": rank_by_id.get(benchmark_id) if benchmark_id else None,
            }
        )

    admitted_id_set = set(admitted_ids)
    actual_ids = set(primary) | set(secondary) | admitted_id_set

    def paper_role(benchmark_id: str) -> str:
        if benchmark_id in primary:
            return "primary"
        if benchmark_id in secondary:
            return "secondary"
        if benchmark_id in admitted_id_set:
            return "admitted_after_freeze"
        return "not_used_in_paper"

    selected_recommendations = []
    for benchmark_id in selected:
        candidate = next(item for item in plan["ranked_candidates"] if item["benchmark_id"] == benchmark_id)
        role = paper_role(benchmark_id)
        selected_recommendations.append(
            {
                "benchmark_id": benchmark_id,
                "benchmark_name": benchmark_names.get(benchmark_id, benchmark_id),
                "rank": rank_by_id[benchmark_id],
                "score": candidate["score"],
                "selection_role": plan["portfolio_roles"][benchmark_id],
                "paper_role": role,
                "source_url": candidate["source_url"],
            }
        )

    top_6_details = []
    for benchmark_id in ranked[:6]:
        role = paper_role(benchmark_id)
        top_6_details.append(
            {
                "benchmark_id": benchmark_id,
                "benchmark_name": benchmark_names.get(benchmark_id, benchmark_id),
                "rank": rank_by_id[benchmark_id],
                "selected": benchmark_id in selected,
                "selection_role": plan["portfolio_roles"].get(benchmark_id),
                "paper_role": role,
            }
        )

    selected_actual_matches = [benchmark_id for benchmark_id in selected if benchmark_id in actual_ids]
    selected_extras = [benchmark_id for benchmark_id in selected if benchmark_id not in actual_ids]
    selected_precision = len(selected_actual_matches) / len(selected) if selected else 0.0
    selected_modeled_recall = (
        len(set(selected_actual_matches)) / len(actual_ids) if actual_ids else 1.0
    )
    unresolved_unmodeled = [
        name
        for name in gold["unmodeled_benchmarks"]
        if str(name).casefold().strip() not in alias_to_id
    ]
    expected_route_at_freeze = gold["expected_route"]
    expected_route = expected_route_at_freeze
    if admitted_ids and plan["coverage_ratio"] >= 1.0:
        expected_route = "direct_portfolio"
    return {
        "case_id": gold["case_id"],
        "source_arxiv_id": gold["source_arxiv_id"],
        "source_title": gold["source_title"],
        "source_url": gold["source_url"],
        "source_input_sections": gold["source_input_sections"],
        "matcher_visible_input": matcher_visible_input
        or f"assets/input/blind_cases/{gold['case_id']}.json",
        "gold_evidence_sections": gold["gold_evidence_sections"],
        "actual_benchmarks": actual_benchmarks,
        "primary_gold": primary,
        "secondary_gold": secondary,
        "unmodeled_gold": unresolved_unmodeled,
        "admitted_gold": admitted_gold,
        "top_6": ranked[:6],
        "top_6_details": top_6_details,
        "selected": selected,
        "selected_recommendations": selected_recommendations,
        "profile": plan["profile"],
        "coverage_ratio": plan["coverage_ratio"],
        "route_reason": plan["route_reason"],
        "adaptation_plan": plan["adaptation_plan"],
        "synthesis_plan": plan["synthesis_plan"],
        "catalog_admission_proposals": plan.get("catalog_admission_proposals", []),
        "comparison": {
            "selected_primary_matches": [benchmark_id for benchmark_id in selected if benchmark_id in primary],
            "selected_secondary_matches": [benchmark_id for benchmark_id in selected if benchmark_id in secondary],
            "selected_admitted_matches": [benchmark_id for benchmark_id in selected if benchmark_id in admitted_id_set],
            "primary_missing_from_selected": [benchmark_id for benchmark_id in primary if benchmark_id not in selected],
            "secondary_missing_from_selected": [benchmark_id for benchmark_id in secondary if benchmark_id not in selected],
            "admitted_missing_from_selected": [benchmark_id for benchmark_id in admitted_ids if benchmark_id not in selected],
            "selected_not_used_in_paper": selected_extras,
            "top_6_primary_matches": [benchmark_id for benchmark_id in ranked[:6] if benchmark_id in primary],
            "top_6_secondary_matches": [benchmark_id for benchmark_id in ranked[:6] if benchmark_id in secondary],
            "top_6_admitted_matches": [benchmark_id for benchmark_id in ranked[:6] if benchmark_id in admitted_id_set],
            "top_6_primary_missing": [benchmark_id for benchmark_id in primary if benchmark_id not in ranked[:6]],
            "selected_actual_precision": selected_precision,
        },
        "primary_recall_at_1": recall_at_k(ranked, primary, 1),
        "primary_recall_at_3": recall_at_k(ranked, primary, 3),
        "primary_recall_at_5": recall_at_k(ranked, primary, 5),
        "primary_recall_at_6": recall_at_k(ranked, primary, 6),
        "secondary_recall_at_6": recall_at_k(ranked, secondary, 6),
        "primary_mrr": reciprocal_rank(ranked, primary),
        "selected_primary_recall": recall_at_k(selected, primary, len(selected)),
        "selected_modeled_recall": selected_modeled_recall,
        "route": plan["route"],
        "expected_route": expected_route,
        "expected_route_at_freeze": expected_route_at_freeze,
        "route_correct": plan["route"] == expected_route,
        "leakage_passed": plan["provenance"]["leakage_scan"]["passed"],
        "matcher_loaded_hidden_labels": plan["provenance"]["blind_gold_loaded"],
        "status": plan["status"],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Auto-Bench Blind Evaluation",
        "",
        f"- Verdict: **{payload['verdict']}**",
        f"- Cases: {payload['aggregate']['case_count']}",
        f"- Mean primary Recall@5: {payload['aggregate']['mean_primary_recall_at_5']:.3f}",
        f"- Mean primary Recall@6: {payload['aggregate']['mean_primary_recall_at_6']:.3f}",
        f"- Mean primary MRR: {payload['aggregate']['mean_primary_mrr']:.3f}",
        f"- Mean selected modeled-benchmark recall: {payload['aggregate']['mean_selected_modeled_recall']:.3f}",
        f"- Mean selected actual-benchmark precision: {payload['aggregate']['mean_selected_actual_precision']:.3f}",
        f"- Route accuracy: {payload['aggregate']['route_accuracy']:.3f}",
        "",
        "## Case Results",
        "",
    ]
    for case in payload["cases"]:
        lines.extend(
            [
                f"### {case['case_id']} — {case['source_title']}",
                "",
                f"- Source paper: [{case['source_title']}]({case['source_url']})",
                f"- Introduction source section: {case['source_input_sections']['introduction']}",
                f"- Method source section(s): {case['source_input_sections']['method']}",
                f"- Matcher-visible input: `{case['matcher_visible_input']}`",
                f"- Paper evidence sections: {case['gold_evidence_sections']}",
                "- The source identity and actual benchmarks below were revealed only after matching completed.",
                "",
                "#### Benchmarks Used by the Paper",
                "",
                "| Role | Benchmark | Evidence section | Auto-Bench selected | Auto-Bench rank |",
                "|---|---|---|---:|---:|",
            ]
        )
        for benchmark in case["actual_benchmarks"]:
            rank = benchmark["rank_in_autobench"] if benchmark["rank_in_autobench"] is not None else "outside catalog"
            lines.append(
                f"| {benchmark['role']} | {benchmark['benchmark_name']} | {benchmark['evidence_section']} | "
                f"{benchmark['selected_by_autobench']} | {rank} |"
            )
        lines.extend(
            [
                "",
                "#### Auto-Bench Selected Portfolio",
                "",
                "| Rank | Benchmark | Score | Selection role | Role in source paper |",
                "|---:|---|---:|---|---|",
            ]
        )
        for recommendation in case["selected_recommendations"]:
            lines.append(
                f"| {recommendation['rank']} | {recommendation['benchmark_name']} | "
                f"{recommendation['score']:.3f} | {recommendation['selection_role']} | "
                f"{recommendation['paper_role']} |"
            )
        comparison = case["comparison"]
        lines.extend(
            [
                "",
                "#### Direct Comparison",
                "",
                f"- Selected primary matches: {comparison['selected_primary_matches']}",
                f"- Selected secondary matches: {comparison['selected_secondary_matches']}",
                f"- Selected post-freeze catalog matches: {comparison.get('selected_admitted_matches', [])}",
                f"- Primary benchmarks missing from selected portfolio: {comparison['primary_missing_from_selected']}",
                f"- Secondary benchmarks missing from selected portfolio: {comparison['secondary_missing_from_selected']}",
                f"- Post-freeze catalog benchmarks missing from selected portfolio: "
                f"{comparison.get('admitted_missing_from_selected', [])}",
                f"- Selected recommendations not used by the paper: {comparison['selected_not_used_in_paper']}",
                f"- Top-6 primary matches: {comparison['top_6_primary_matches']}",
                f"- Recall@5 / Recall@6: {case['primary_recall_at_5']:.3f} / {case['primary_recall_at_6']:.3f}",
                f"- Selected modeled-benchmark recall: {case['selected_modeled_recall']:.3f}",
                f"- Selected actual-benchmark precision: {comparison['selected_actual_precision']:.3f}",
                f"- Route: {case['route']} (expected {case['expected_route']})",
                f"- Expected route at original freeze: {case.get('expected_route_at_freeze', case['expected_route'])}",
                f"- Route reason: {case['route_reason']}",
                f"- Inferred task coverage: {case['coverage_ratio']:.3f}",
                f"- Missing task families: {case['adaptation_plan']['missing_task_families']}",
                f"- Synthesis required: {case['synthesis_plan']['required']}",
                f"- Catalog admission proposals: "
                f"{[item['proposal_id'] for item in case['catalog_admission_proposals']]}",
                "",
                "#### Automatic Literature Check",
                "",
                "- Source evidence terms are verified before the gold record is admitted.",
                "- `autobench auto-review` compares paper benchmarks, task families, selected portfolio, and route.",
                "- Output decisions are MATCH / PARTIAL / MISMATCH with typed optimization errors.",
                "- Human submission required: False.",
                "",
            ]
        )
    lines.extend(
        [
            "## Integrity Checks",
            "",
            f"- All input leakage scans passed: {payload['aggregate']['all_leakage_checks_passed']}",
            f"- Matcher loaded hidden labels: {payload['aggregate']['any_matcher_loaded_hidden_labels']}",
            "- Gold labels were opened only by this post-run evaluator.",
            "- This source-revealed report is the input to the automatic literature evaluator.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    runs_dir = ROOT / args.runs_dir
    manifest = json.loads((runs_dir / "run_manifest.json").read_text(encoding="utf-8"))
    run_records = manifest["cases"]
    plans: dict[str, dict[str, Any]] = {}
    for run in run_records:
        if run["worker_exit_status"] != 0 or run["hidden_labels_present_in_sandbox"] is not False:
            raise ValueError(f"blind-run integrity failure for {run['case_id']}")
        plan_path = runs_dir / run["case_id"] / "benchmark_plan.json"
        if not plan_path.is_file():
            raise ValueError(f"missing plan: {plan_path}")
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        if plan["provenance"]["blind_gold_loaded"] is not False:
            raise ValueError(f"matcher declared hidden-label access for {run['case_id']}")
        plans[run["case_id"]] = plan

    gold_dir = ROOT / args.gold_dir
    catalog = load_catalog(ROOT / args.catalog)
    benchmark_names = {record.benchmark_id: record.name for record in catalog}
    benchmark_aliases = {
        alias.casefold().strip(): record.benchmark_id
        for record in catalog
        for alias in [record.name, *record.aliases]
    }
    results: list[dict[str, Any]] = []
    for case_id, plan in sorted(plans.items()):
        gold_path = gold_dir / f"{case_id}.gold.json"
        gold = json.loads(gold_path.read_text(encoding="utf-8"))
        matcher_input = (
            Path(args.matcher_cases_dir) / f"{case_id}.json"
        ).as_posix()
        results.append(
            evaluate_case(
                plan,
                gold,
                benchmark_names,
                benchmark_aliases,
                matcher_input,
            )
        )

    aggregate = {
        "case_count": len(results),
        "mean_primary_recall_at_5": mean(item["primary_recall_at_5"] for item in results),
        "mean_primary_recall_at_6": mean(item["primary_recall_at_6"] for item in results),
        "mean_primary_mrr": mean(item["primary_mrr"] for item in results),
        "mean_selected_modeled_recall": mean(item["selected_modeled_recall"] for item in results),
        "mean_selected_actual_precision": mean(
            item["comparison"]["selected_actual_precision"] for item in results
        ),
        "route_accuracy": mean(float(item["route_correct"]) for item in results),
        "all_leakage_checks_passed": all(item["leakage_passed"] for item in results),
        "any_matcher_loaded_hidden_labels": any(item["matcher_loaded_hidden_labels"] for item in results),
    }
    passed = (
        aggregate["case_count"] >= args.minimum_cases
        and aggregate["mean_primary_recall_at_5"] >= 0.80
        and aggregate["mean_primary_recall_at_6"] >= 0.90
        and aggregate["mean_selected_modeled_recall"] >= 0.85
        and aggregate["mean_selected_actual_precision"] >= 0.60
        and aggregate["route_accuracy"] >= 2 / 3
        and aggregate["all_leakage_checks_passed"]
        and not aggregate["any_matcher_loaded_hidden_labels"]
    )
    payload = {
        "schema_version": "1.0",
        "verdict": "PASS" if passed else "NEEDS_ITERATION",
        "thresholds": {
            "minimum_cases": args.minimum_cases,
            "mean_primary_recall_at_5": 0.80,
            "mean_primary_recall_at_6": 0.90,
            "mean_selected_modeled_recall": 0.85,
            "mean_selected_actual_precision": 0.60,
            "route_accuracy": 2 / 3,
            "all_leakage_checks_passed": True,
            "matcher_hidden_label_access": False,
        },
        "aggregate": aggregate,
        "cases": results,
    }
    output_path = ROOT / args.output
    report_path = ROOT / args.report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"verdict": payload["verdict"], **aggregate}, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
