"""End-to-end orchestration for method-only benchmark discovery."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .admission_agent import build_admission_proposals
from .auto_literature_review import initial_automatic_review_state
from .catalog import load_catalog
from .leakage import enforce_blind_input
from .match_agent import rank_candidates, select_portfolio
from .models import BenchmarkPlan, MethodInput
from .profile_agent import build_profile
from .query_agent import build_queries
from .search_agent import search_arxiv
from .synthesis_agent import build_adaptation_plan, build_synthesis_plan, decide_route


def _portable_path(path: Path) -> str:
    """Return a reproducible path label without embedding a local home path."""

    resolved = path.resolve()
    try:
        return resolved.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return f"external:{path.name}"


class AutoBenchPipeline:
    """Run seven inspectable agents while keeping blind labels out of scope."""

    def __init__(self, catalog_path: str | Path):
        self.catalog_path = Path(catalog_path)
        self.catalog = load_catalog(self.catalog_path)

    def run(
        self,
        method_input: MethodInput,
        *,
        online_search: bool = False,
        max_search_queries: int = 8,
    ) -> BenchmarkPlan:
        """Generate a plan pending automatic post-match literature comparison."""

        leakage = enforce_blind_input(method_input, self.catalog)
        profile = build_profile(method_input)
        queries = build_queries(profile, max_queries=max_search_queries)
        hits = search_arxiv(queries) if online_search else []
        admission_proposals = build_admission_proposals(profile, hits)
        ranked = rank_candidates(profile, self.catalog, hits)
        selected, coverage_ratio, portfolio_roles = select_portfolio(profile, ranked)
        route, reason = decide_route(profile, ranked, selected, coverage_ratio)
        adaptation = build_adaptation_plan(profile, ranked, selected)
        synthesis = build_synthesis_plan(profile, adaptation)
        synthesis["catalog_admission_proposals"] = [
            proposal.proposal_id for proposal in admission_proposals
        ]

        selected_records = {record.benchmark_id: record for record in self.catalog if record.benchmark_id in selected}
        metric_plan = [
            {
                "benchmark_id": benchmark_id,
                "official_metrics": selected_records[benchmark_id].metrics,
                "reporting_rule": "report official metrics unchanged; adapted metrics use a separate namespace",
            }
            for benchmark_id in selected
        ]
        automatic_review = initial_automatic_review_state()
        legacy_human_review = {
            "status": "NOT_REQUIRED",
            "required": False,
            "human_submission_required": False,
            "reason": "replaced by automatic post-match source comparison",
        }
        return BenchmarkPlan(
            case_id=method_input.case_id,
            status=automatic_review["status"],
            visible_input={
                "introduction": method_input.introduction,
                "method": method_input.method,
                "constraints": method_input.constraints,
            },
            profile=profile,
            search_queries=queries,
            search_hits=hits,
            catalog_admission_proposals=admission_proposals,
            ranked_candidates=ranked,
            selected_benchmarks=selected,
            portfolio_roles=portfolio_roles,
            coverage_ratio=coverage_ratio,
            route=route,
            route_reason=reason,
            metric_plan=metric_plan,
            adaptation_plan=adaptation,
            synthesis_plan=synthesis,
            automatic_review=automatic_review,
            human_review=legacy_human_review,
            provenance={
                "input_fields": ["introduction", "method", "constraints"],
                "blind_gold_loaded": False,
                "leakage_scan": {
                    "passed": leakage.passed,
                    "benchmark_alias_hits": leakage.benchmark_alias_hits,
                    "identity_hits": leakage.identity_hits,
                    "generic_evaluation_terms": leakage.generic_evaluation_terms,
                },
                "catalog": _portable_path(self.catalog_path),
                "catalog_records": len(self.catalog),
                "online_search": online_search,
                "decision_backend": "deterministic_profile_and_weighted_compatibility_v1",
                "validation_mode": "automatic_post_match_literature_comparison",
                "human_submission_required": False,
            },
        )

    @staticmethod
    def write_outputs(plan: BenchmarkPlan, output_dir: str | Path) -> dict[str, Path]:
        """Write plan artifacts and the input contract for automatic review."""

        root = Path(output_dir)
        root.mkdir(parents=True, exist_ok=True)
        report_json = root / "benchmark_plan.json"
        report_md = root / "benchmark_plan.md"
        automatic_review_input = root / "automatic_review_input.json"
        payload = plan.to_dict()
        report_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report_md.write_text(_render_markdown(payload), encoding="utf-8")
        review_payload = {
            "schema_version": "1.0",
            "case_id": plan.case_id,
            "status": plan.automatic_review["status"],
            "human_submission_required": False,
            "profile": payload["profile"],
            "selected_benchmarks": payload["selected_benchmarks"],
            "top_6": [item["benchmark_id"] for item in payload["ranked_candidates"][:6]],
            "route": payload["route"],
            "blind_gold_loaded": False,
            "next_automatic_step": (
                "evaluate the sealed matcher output against source-paper benchmark evidence, "
                "then call autobench.auto_literature_review.write_review"
            ),
        }
        automatic_review_input.write_text(
            json.dumps(review_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        json.loads(automatic_review_input.read_text(encoding="utf-8"))
        return {
            "json": report_json,
            "markdown": report_md,
            "automatic_review_input": automatic_review_input,
        }


def _render_markdown(plan: dict[str, Any]) -> str:
    """Render a compact report without hiding scores, gaps, or review status."""

    lines = [
        f"# Auto-Bench Plan: {plan['case_id']}",
        "",
        f"- Status: **{plan['status']}**",
        f"- Route: **{plan['route']}**",
        f"- Task-family coverage: **{plan['coverage_ratio']:.1%}**",
        f"- Decision: {plan['route_reason']}",
        "",
        "## Matcher-Visible Paper Input",
        "",
        "### Introduction",
        "",
        plan["visible_input"]["introduction"],
        "",
        "### Method",
        "",
        plan["visible_input"]["method"],
        "",
        "## Inferred Evaluation Profile",
        "",
        f"- Tasks: {', '.join(plan['profile']['task_families']) or 'none'}",
        f"- Explicit benchmark counts: {plan['profile']['task_benchmark_counts']}",
        f"- Declared total evaluation breadth: {plan['profile']['declared_evaluation_breadth']}",
        f"- Uncovered tasks: {', '.join(plan['profile']['uncovered_task_families']) or 'none'}",
        f"- Modalities: {', '.join(plan['profile']['modalities'])}",
        f"- Interactions: {', '.join(plan['profile']['interactions'])}",
        f"- Outputs: {', '.join(plan['profile']['output_types'])}",
        f"- Capabilities: {', '.join(plan['profile']['capabilities']) or 'none'}",
        "",
        "## Selected Benchmark Portfolio",
        "",
    ]
    if plan["selected_benchmarks"]:
        for benchmark_id in plan["selected_benchmarks"]:
            candidate = next(item for item in plan["ranked_candidates"] if item["benchmark_id"] == benchmark_id)
            lines.append(
                f"- **{candidate['name']}** (`{benchmark_id}`): score={candidate['score']:.3f}; "
                f"role={plan['portfolio_roles'][benchmark_id]}; source={candidate['source_url']}"
            )
    else:
        lines.append("- No existing benchmark passed the portfolio threshold.")
    lines.extend(["", "## Top Candidates", ""])
    for rank, candidate in enumerate(plan["ranked_candidates"][:10], start=1):
        lines.append(
            f"{rank}. **{candidate['name']}** (`{candidate['benchmark_id']}`) — "
            f"{candidate['score']:.3f}; tasks={candidate['matched_requirements']['task_families']}"
        )
    lines.extend(["", "## Online Literature Leads", ""])
    if plan["search_hits"]:
        for hit in plan["search_hits"]:
            lines.append(f"- [{hit['title']}]({hit['url']}) — query: `{hit['query']}`")
        lines.append(
            "- A task-topical hit may corroborate catalog fit; admission as a new benchmark still requires "
            "a complete task, metric, access, license, and source record."
        )
    else:
        lines.append("- Online search was disabled or returned no relevant arXiv metadata hits.")
    lines.extend(["", "## Catalog Admission Proposals", ""])
    if plan["catalog_admission_proposals"]:
        for proposal in plan["catalog_admission_proposals"]:
            lines.append(
                f"- [{proposal['title']}]({proposal['source_url']}) — "
                f"likelihood={proposal['benchmark_likelihood']:.2f}; "
                f"tasks={proposal['matched_task_families']}; status={proposal['status']}; "
                f"missing={proposal['missing_required_fields']}"
            )
        lines.append(
            "- Proposals remain outside ranking until every required catalog field is verified."
        )
    else:
        lines.append("- No benchmark-like online hit met the proposal threshold.")
    lines.extend(
        [
            "",
            "## Adaptation and Synthesis",
            "",
            f"- Missing task families: {plan['adaptation_plan']['missing_task_families']}",
            f"- Synthesis required: {plan['synthesis_plan']['required']}",
            "- Official and adapted metrics must be reported separately.",
            "- Test examples stay frozen and never seed synthetic records.",
            "",
            "## Automatic Literature Validation",
            "",
            f"Current status: **{plan['automatic_review']['status']}**.",
            "- Existing-paper blind test: after matching, reveal the source paper and compare its actual benchmarks "
            "with Selected and Top-6 using MATCH / PARTIAL / MISMATCH.",
            "- The source comparison runs in a separate evaluator process; the matcher never receives paper identity, "
            "experiment sections, or benchmark labels.",
            "- Every mismatch, missing benchmark, extra benchmark, catalog gap, and route error becomes machine-readable "
            "optimization feedback; no user submission is required.",
            "",
        ]
    )
    execution = plan["synthesis_plan"].get("execution")
    if execution:
        lines.extend(
            [
                f"- Synthesis execution: **{execution['status']}**",
                f"- Executed modules: {[item['transformation'] for item in execution.get('modules', [])]}",
                "",
            ]
        )
    return "\n".join(lines)
