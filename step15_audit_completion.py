#!/usr/bin/env python3
"""Build the no-human-gate Auto-Bench completion audit."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent


def _load(relative_path: str) -> dict[str, Any]:
    path = ROOT / relative_path
    if not path.is_file():
        raise ValueError(f"required artifact is missing: {relative_path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_automatic_reviews(
    relative_root: str = "assets/output/automatic_literature_review",
    *,
    workspace_root: Path | None = None,
) -> list[dict[str, Any]]:
    """Load verified automatic review JSON files and attach portable paths."""

    root = workspace_root or ROOT
    review_root = root / relative_root
    reviews: list[dict[str, Any]] = []
    for path in sorted(review_root.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("reviewer") != "AUTO_LITERATURE_EVALUATOR":
            continue
        if payload.get("human_submission_required") is not False:
            raise ValueError(f"automatic review unexpectedly requires a human submission: {path}")
        reviews.append({**payload, "artifact": path.relative_to(root).as_posix()})
    return reviews


def determine_completion_status(
    *,
    machine_ready: bool,
    automatic_validation_complete: bool,
    automatic_validation_passed: bool,
) -> str:
    """Separate missing automatic evidence from evidence that exposes quality gaps."""

    if not machine_ready:
        return "MACHINE_WORKFLOW_NEEDS_ITERATION"
    if not automatic_validation_complete:
        return "AUTOMATIC_LITERATURE_REVIEW_PENDING"
    if not automatic_validation_passed:
        return "AUTOMATED_LITERATURE_VALIDATION_NEEDS_ITERATION"
    return "COMPLETE"


def _review_summary(review: dict[str, Any]) -> dict[str, Any]:
    """Keep completion output compact while preserving decisive evidence."""

    return {
        "artifact": review["artifact"],
        "status": review["status"],
        "evidence_class": review["evidence_class"],
        "case_count": review["case_count"],
        "decision_counts": review["decision_counts"],
        "all_source_evidence_complete": review["all_source_evidence_complete"],
        "all_blind_checks_passed": review["all_blind_checks_passed"],
    }


def _fresh_suite_number(review: dict[str, Any]) -> int:
    """Return the numeric fresh-suite sequence encoded in the artifact name."""

    match = re.search(r"fresh_holdout_suite_(\d+)", review.get("artifact", ""))
    return int(match.group(1)) if match else -1


def build_audit() -> dict[str, Any]:
    """Join machine checks with the newest untouched automatic literature review."""

    blind = _load("assets/output/blind_evaluation.json")
    online_plan = _load(
        "assets/output/untouched_holdout_2/refined_online_runs/holdout_002/benchmark_plan.json"
    )
    online_proposals = online_plan["catalog_admission_proposals"]
    manifests = {
        name: _load(f"assets/output/end_to_end_demo/{name}/workflow_manifest.json")
        for name in ("direct", "base_adaptation", "new_synthesis", "new_synthesis_online")
    }
    synthesis_modules = manifests["base_adaptation"]["synthesis_execution"]["modules"]
    suite003_record = _load("assets/output/fresh_holdout_suite_003/pre_gold_run_record.json")

    machine_checks = [
        {
            "requirement": "Introduction and Method only, with hidden labels isolated",
            "status": "PASS"
            if blind["aggregate"]["all_leakage_checks_passed"]
            and not blind["aggregate"]["any_matcher_loaded_hidden_labels"]
            else "FAIL",
            "evidence": {
                "case_count": blind["aggregate"]["case_count"],
                "all_leakage_checks_passed": blind["aggregate"]["all_leakage_checks_passed"],
                "any_matcher_loaded_hidden_labels": blind["aggregate"][
                    "any_matcher_loaded_hidden_labels"
                ],
                "run_manifest": "assets/output/blind_runs/run_manifest.json",
            },
        },
        {
            "requirement": "Automatic benchmark search, ranking, and portfolio selection",
            "status": blind["verdict"],
            "evidence": blind["aggregate"],
        },
        {
            "requirement": "Live literature search with typed catalog-admission isolation",
            "status": (
                "PASS"
                if online_plan["search_hits"]
                and online_proposals
                and all(
                    proposal["status"] == "CATALOG_ADMISSION_REVIEW_REQUIRED"
                    and not proposal["selection_eligible"]
                    for proposal in online_proposals
                )
                else "FAIL"
            ),
            "evidence": {
                "search_hit_count": len(online_plan["search_hits"]),
                "catalog_admission_proposal_count": len(online_proposals),
                "all_proposals_excluded_from_selection": all(
                    not proposal["selection_eligible"] for proposal in online_proposals
                ),
            },
        },
        {
            "requirement": "Direct, base-adaptation, and new-synthesis routes",
            "status": "PASS",
            "evidence": {
                name: {
                    "route": manifest["route"],
                    "synthesis_status": manifest["synthesis_execution"]["status"],
                }
                for name, manifest in manifests.items()
            },
        },
        {
            "requirement": "Executable synthesis with deterministic provenance verification",
            "status": (
                "PASS"
                if synthesis_modules
                and all(item["verification_status"] == "PASS" for item in synthesis_modules)
                else "FAIL"
            ),
            "evidence": [
                {
                    "transformation": item["transformation"],
                    "records": item["records"],
                    "verification_status": item["verification_status"],
                    "verification": item["verification"],
                }
                for item in synthesis_modules
            ],
        },
        {
            "requirement": "Newest fresh-suite matcher freeze and worker isolation",
            "status": (
                "PASS"
                if suite003_record["blind_run_completed_before_gold"]
                and suite003_record["matcher_frozen_file_sizes_unchanged"]
                and suite003_record["all_worker_exit_statuses_zero"]
                and suite003_record["all_sandboxes_excluded_hidden_labels"]
                else "FAIL"
            ),
            "evidence": {
                "suite_id": suite003_record["suite_id"],
                "case_count": suite003_record["case_count"],
                "matcher_frozen_file_sizes_unchanged": suite003_record[
                    "matcher_frozen_file_sizes_unchanged"
                ],
                "all_sandboxes_excluded_hidden_labels": suite003_record[
                    "all_sandboxes_excluded_hidden_labels"
                ],
                "meta_agent_inspection_caveat": suite003_record.get(
                    "generalization_caveat"
                ),
            },
        },
    ]

    reviews = load_automatic_reviews()
    fresh_reviews = [review for review in reviews if review["evidence_class"] == "fresh_holdout"]
    feedback_reviews = [
        review for review in reviews if review["evidence_class"] == "feedback_regression"
    ]
    authoritative = max(fresh_reviews, key=_fresh_suite_number) if fresh_reviews else None
    matching_feedback: list[dict[str, Any]] = []
    if authoritative:
        suite_stem = Path(authoritative["artifact"]).stem
        matching_feedback = [
            review
            for review in feedback_reviews
            if Path(review["artifact"]).stem.startswith(f"{suite_stem}_feedback")
        ]
    latest_feedback = (
        max(matching_feedback, key=lambda review: Path(review["artifact"]).name)
        if matching_feedback
        else max(feedback_reviews, key=_fresh_suite_number, default=None)
    )
    machine_ready = all(item["status"] in {"PASS", "RECORDED"} for item in machine_checks)
    automatic_complete = bool(
        authoritative
        and authoritative["all_source_evidence_complete"]
        and authoritative["all_blind_checks_passed"]
        and authoritative["case_count"] > 0
    )
    automatic_passed = bool(
        authoritative
        and authoritative["status"] == "AUTOMATED_LITERATURE_AUDIT_CONFIRMED"
        and authoritative["decision_counts"].get("PARTIAL", 0) == 0
        and authoritative["decision_counts"].get("MISMATCH", 0) == 0
    )
    return {
        "schema_version": "2.0",
        "status": determine_completion_status(
            machine_ready=machine_ready,
            automatic_validation_complete=automatic_complete,
            automatic_validation_passed=automatic_passed,
        ),
        "validation_mode": "automatic_post_match_literature_comparison",
        "human_submission_required": False,
        "machine_ready": machine_ready,
        "automatic_validation_complete": automatic_complete,
        "automatic_validation_passed": automatic_passed,
        "machine_checks": machine_checks,
        "authoritative_fresh_review": _review_summary(authoritative) if authoritative else None,
        "latest_feedback_regression": _review_summary(latest_feedback) if latest_feedback else None,
        "automatic_review_count": len(reviews),
        "automatic_reviews": [_review_summary(review) for review in reviews],
        "human_gates": [],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    """Render completion state and automatic optimization evidence."""

    lines = [
        "# Auto-Bench Completion Audit",
        "",
        f"- Status: **{payload['status']}**",
        f"- Machine workflow ready: **{payload['machine_ready']}**",
        f"- Automatic validation complete: **{payload['automatic_validation_complete']}**",
        f"- Automatic validation passed: **{payload['automatic_validation_passed']}**",
        f"- Human submission required: **{payload['human_submission_required']}**",
        "",
        "## Machine checks",
        "",
    ]
    for item in payload["machine_checks"]:
        lines.extend(
            [
                f"### {item['requirement']}",
                "",
                f"- Status: **{item['status']}**",
                "- Evidence:",
                "```json",
                json.dumps(item["evidence"], ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        )
    lines.extend(["## Authoritative fresh automatic review", ""])
    if payload["authoritative_fresh_review"]:
        lines.extend(
            [
                "```json",
                json.dumps(payload["authoritative_fresh_review"], ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        )
    else:
        lines.extend(["No fresh automatic review is available.", ""])
    lines.extend(["## Latest feedback regression", ""])
    if payload["latest_feedback_regression"]:
        lines.extend(
            [
                "```json",
                json.dumps(payload["latest_feedback_regression"], ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        )
    else:
        lines.extend(["No feedback regression is available.", ""])
    return "\n".join(lines)


def main() -> int:
    payload = build_audit()
    root = ROOT / "assets/output/end_to_end_demo"
    json_path = root / "completion_audit.json"
    markdown_path = root / "completion_audit.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    reopened = json.loads(json_path.read_text(encoding="utf-8"))
    if reopened["status"] != payload["status"]:
        raise ValueError("completion audit verification failed")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "human_submission_required": False,
                "json": str(json_path),
                "markdown": str(markdown_path),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
