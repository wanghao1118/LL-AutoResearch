"""Agent 7: mandatory human suitability review and acceptance gate."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Iterable


RUBRIC_GUIDANCE = {
    "construct_alignment": "Success measures the capability claimed by the method rather than a proxy.",
    "task_representativeness": "Tasks cover the intended use, difficulty range, and important failure modes.",
    "metric_validity": "Metrics are meaningful, reproducible, and separate official from adapted results.",
    "data_quality": "Labels, splits, and any synthetic transformations have auditable quality.",
    "leakage_control": "Hidden labels and test examples stay isolated from matching, synthesis, and tuning.",
    "execution_feasibility": "The full protocol can run with the stated tools, data access, and compute.",
}
RUBRIC_DIMENSIONS = tuple(RUBRIC_GUIDANCE)
REVIEWER_SLOTS = ("REVIEWER_1", "REVIEWER_2")
_PLACEHOLDER_REVIEWER_IDS = {
    "reviewer_1",
    "reviewer_2",
    "reviewer1",
    "reviewer2",
    "r1",
    "r2",
    "anonymous",
    "anon",
    "placeholder",
}


def initial_review_state() -> dict[str, Any]:
    """Return validation tracks without conflating two different human tasks.

    Existing-paper recovery is checked after matching by revealing the source
    paper and comparing against its experiment-derived benchmark list. A truly
    new method has no such literature gold, so its proposed portfolio instead
    enters the independent construct-suitability gate defined below.
    """

    return {
        "status": "HUMAN_REVIEW_REQUIRED",
        "validation_tracks": {
            "literature_recovery": {
                "timing": "post_match_only",
                "input": "revealed source paper, actual benchmarks, Selected, and Top-6",
                "decision_values": ["MATCH", "PARTIAL", "MISMATCH"],
            },
            "new_method_suitability": {
                "timing": "before_research_use",
                "input": "method text, candidate evidence, metrics, adaptation, and synthesis plan",
                "decision_values": ["APPROVE", "REJECT"],
            },
        },
        "required_reviewer_slots": list(REVIEWER_SLOTS),
        "minimum_reviewers": 2,
        "rubric_dimensions": list(RUBRIC_DIMENSIONS),
        "rubric_guidance": RUBRIC_GUIDANCE,
        "score_range": [1, 5],
        "acceptance_rules": {
            "mean_score_at_least": 4.0,
            "every_dimension_at_least": 3.0,
            "provenance_confirmed_by_all": True,
            "independence_attested_by_all": True,
            "explicit_approval_by_all": True,
            "nonempty_justification_by_all": True,
            "maximum_pairwise_dimension_gap": 1.0,
        },
        "reviews": [],
    }


def write_review_packet(path: str | Path, plan: dict[str, Any]) -> None:
    """Write a CSV packet that reviewers can fill independently."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "case_id",
                "benchmark_id",
                "reviewer_slot",
                "reviewer_id",
                *RUBRIC_DIMENSIONS,
                "provenance_confirmed",
                "independence_attested",
                "decision",
                "notes",
            ]
        )
        for benchmark_id in plan["selected_benchmarks"] or ["NO_DIRECT_MATCH"]:
            for reviewer_slot in REVIEWER_SLOTS:
                writer.writerow(
                    [
                        plan["case_id"],
                        benchmark_id,
                        reviewer_slot,
                        "",
                        *([""] * len(RUBRIC_DIMENSIONS)),
                        "",
                        "",
                        "",
                        "",
                    ]
                )


def _pending(reason: str) -> dict[str, Any]:
    return {"status": "HUMAN_REVIEW_REQUIRED", "reason": reason}


def _reviewer_id(review: dict[str, Any]) -> str:
    return str(review.get("reviewer_id", "")).strip()


def _is_placeholder_reviewer_id(reviewer_id: str) -> bool:
    return reviewer_id.casefold().replace("-", "_").replace(" ", "_") in _PLACEHOLDER_REVIEWER_IDS


def _normalize_decision(value: Any) -> str | None:
    normalized = str(value or "").strip().casefold()
    if normalized in {"approve", "approved", "accept", "accepted", "yes"}:
        return "APPROVE"
    if normalized in {"reject", "rejected", "decline", "declined", "no"}:
        return "REJECT"
    return None


def evaluate_reviews(review_payloads: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate one case/benchmark pair using explicit human thresholds.

    Each generated pair has one row for each independent reviewer slot. The
    gate checks identity, independence, completeness, explicit decisions,
    provenance, score validity, disagreement, and acceptance thresholds in
    that order. A malformed or unfinished form stays pending instead of being
    interpreted as evidence about benchmark quality.
    """

    if not review_payloads:
        return _pending("no human reviews were submitted")

    reviewer_ids = [_reviewer_id(review) for review in review_payloads]
    if any(not reviewer_id for reviewer_id in reviewer_ids):
        return _pending("reviewer identity is incomplete")
    if any(_is_placeholder_reviewer_id(reviewer_id) for reviewer_id in reviewer_ids):
        return _pending("placeholder reviewer identity must be replaced")
    if len(set(reviewer_ids)) < 2:
        return _pending("fewer than two distinct reviewers")
    if len(reviewer_ids) != len(set(reviewer_ids)):
        return _pending("a reviewer has duplicate rows for the same item")

    supplied_slots = [str(review.get("reviewer_slot", "")).strip().upper() for review in review_payloads]
    if any(supplied_slots):
        if any(not slot for slot in supplied_slots):
            return _pending("reviewer slot is incomplete")
        if set(supplied_slots) != set(REVIEWER_SLOTS) or len(supplied_slots) != len(REVIEWER_SLOTS):
            return _pending("both reviewer slots must submit exactly one review")

    dimension_values: dict[str, list[float]] = {name: [] for name in RUBRIC_DIMENSIONS}
    decisions: list[str] = []
    for review in review_payloads:
        if review.get("independence_attested") is not True:
            return _pending("independence attestation is incomplete or false")
        notes = str(review.get("notes", "")).strip()
        if not notes:
            return _pending("review justification is incomplete")
        decision = _normalize_decision(review.get("decision"))
        if decision is None:
            return _pending("review decision is incomplete or invalid")
        decisions.append(decision)

        scores = review.get("scores", {})
        for dimension in RUBRIC_DIMENSIONS:
            raw_value = scores.get(dimension)
            if raw_value in (None, ""):
                return _pending(f"incomplete score for {dimension}")
            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                return _pending(f"non-numeric score for {dimension}")
            if value < 1 or value > 5:
                return {"status": "REJECTED", "reason": f"invalid score for {dimension}"}
            dimension_values[dimension].append(value)

        if review.get("provenance_confirmed") in (None, ""):
            return _pending("provenance confirmation is incomplete")
        if review.get("provenance_confirmed") is not True:
            return {"status": "REJECTED", "reason": "provenance not confirmed by every reviewer"}

    dimension_means = {name: mean(values) for name, values in dimension_values.items()}
    gaps = {name: max(values) - min(values) for name, values in dimension_values.items()}
    overall = mean(dimension_means.values())
    evidence = {
        "dimension_means": dimension_means,
        "dimension_gaps": gaps,
        "overall_mean": overall,
        "reviewer_ids": sorted(set(reviewer_ids)),
    }
    if "REJECT" in decisions:
        return {"status": "REJECTED", "reason": "at least one reviewer explicitly rejected the proposal", **evidence}
    if max(gaps.values()) > 1.0:
        return {
            "status": "ADJUDICATION_REQUIRED",
            "reason": "reviewer disagreement exceeds one point",
            **evidence,
        }
    if overall < 4.0 or min(dimension_means.values()) < 3.0:
        return {
            "status": "REJECTED",
            "reason": "suitability scores do not meet acceptance thresholds",
            **evidence,
        }
    return {"status": "APPROVED", "reason": "all human suitability gates passed", **evidence}


def _normalize_expected_pairs(expected_pairs: Iterable[Any] | None) -> set[tuple[str, str]] | None:
    if expected_pairs is None:
        return None
    normalized: set[tuple[str, str]] = set()
    for item in expected_pairs:
        if isinstance(item, dict):
            case_id = str(item.get("case_id", "")).strip()
            benchmark_id = str(item.get("benchmark_id", "")).strip()
        else:
            case_id, benchmark_id = item
            case_id = str(case_id).strip()
            benchmark_id = str(benchmark_id).strip()
        if not case_id or not benchmark_id:
            raise ValueError("expected review scope contains an empty case_id or benchmark_id")
        normalized.add((case_id, benchmark_id))
    return normalized


def evaluate_review_matrix(
    review_payloads: list[dict[str, Any]],
    *,
    expected_pairs: Iterable[Any] | None = None,
) -> dict[str, Any]:
    """Evaluate the frozen review scope and derive one conservative verdict."""

    expected = _normalize_expected_pairs(expected_pairs)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for review in review_payloads:
        case_id = str(review.get("case_id", "")).strip()
        benchmark_id = str(review.get("benchmark_id", "")).strip()
        if not case_id or not benchmark_id:
            return {
                "status": "HUMAN_REVIEW_REQUIRED",
                "reason": "case_id or benchmark_id is missing",
                "items": [],
            }
        grouped[(case_id, benchmark_id)].append(review)

    if expected is None and not grouped:
        return {"status": "HUMAN_REVIEW_REQUIRED", "reason": "review matrix is empty", "items": []}

    actual_pairs = set(grouped)
    scope_pairs = expected if expected is not None else actual_pairs
    unexpected_pairs = sorted(actual_pairs - scope_pairs)
    pairs = sorted(scope_pairs | actual_pairs)

    items: list[dict[str, Any]] = []
    for case_id, benchmark_id in pairs:
        if (case_id, benchmark_id) in unexpected_pairs:
            verdict = _pending("submission item is outside the frozen review scope")
        elif (case_id, benchmark_id) not in grouped:
            verdict = _pending("review rows are missing for this frozen-scope item")
        else:
            verdict = evaluate_reviews(grouped[(case_id, benchmark_id)])
        items.append({"case_id": case_id, "benchmark_id": benchmark_id, **verdict})

    slot_to_ids: dict[str, set[str]] = defaultdict(set)
    for review in review_payloads:
        slot = str(review.get("reviewer_slot", "")).strip().upper()
        reviewer_id = _reviewer_id(review)
        if slot in REVIEWER_SLOTS and reviewer_id and not _is_placeholder_reviewer_id(reviewer_id):
            slot_to_ids[slot].add(reviewer_id)
    inconsistent_slots = {slot: sorted(ids) for slot, ids in slot_to_ids.items() if len(ids) > 1}
    cross_slot_ids = slot_to_ids.get(REVIEWER_SLOTS[0], set()) & slot_to_ids.get(REVIEWER_SLOTS[1], set())
    if inconsistent_slots or cross_slot_ids:
        return {
            "status": "HUMAN_REVIEW_REQUIRED",
            "reason": "reviewer identities are inconsistent across the frozen matrix",
            "items": items,
            "reviewer_identity_audit": {
                "inconsistent_slots": inconsistent_slots,
                "cross_slot_ids": sorted(cross_slot_ids),
            },
        }

    statuses = {item["status"] for item in items}
    if "REJECTED" in statuses:
        status = "REJECTED"
        reason = "at least one case/benchmark pair failed suitability review"
    elif "ADJUDICATION_REQUIRED" in statuses:
        status = "ADJUDICATION_REQUIRED"
        reason = "at least one case/benchmark pair requires reviewer adjudication"
    elif "HUMAN_REVIEW_REQUIRED" in statuses:
        status = "HUMAN_REVIEW_REQUIRED"
        reason = "at least one case/benchmark pair has incomplete independent review"
    else:
        status = "APPROVED"
        reason = "every frozen-scope case/benchmark pair passed independent human review"
    return {
        "status": status,
        "reason": reason,
        "expected_item_count": len(scope_pairs),
        "submitted_item_count": len(actual_pairs & scope_pairs),
        "items": items,
    }


def _parse_optional_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    normalized = str(value or "").strip().casefold()
    if normalized in {"true", "yes", "1"}:
        return True
    if normalized in {"false", "no", "0"}:
        return False
    return None


def load_reviews(path: str | Path) -> list[dict[str, Any]]:
    """Load completed human review forms from JSON or the generated CSV."""

    source = Path(path)
    if source.suffix.casefold() == ".csv":
        reviews: list[dict[str, Any]] = []
        with source.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                scores = {
                    dimension: (float(row[dimension]) if str(row.get(dimension, "")).strip() else None)
                    for dimension in RUBRIC_DIMENSIONS
                }
                reviews.append(
                    {
                        "case_id": row.get("case_id", ""),
                        "benchmark_id": row.get("benchmark_id", ""),
                        "reviewer_slot": row.get("reviewer_slot", ""),
                        "reviewer_id": row.get("reviewer_id", ""),
                        "scores": scores,
                        "provenance_confirmed": _parse_optional_bool(row.get("provenance_confirmed")),
                        "independence_attested": _parse_optional_bool(row.get("independence_attested")),
                        "decision": row.get("decision", ""),
                        "notes": row.get("notes", ""),
                    }
                )
        return reviews
    payload = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("reviews"), list):
        payload = payload["reviews"]
    if not isinstance(payload, list):
        raise ValueError("human review file must contain a list or an object with a reviews list")
    return payload


def load_review_scope(path: str | Path) -> set[tuple[str, str]]:
    """Load the immutable set of case/benchmark pairs prepared for review."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("pairs"), list):
        return _normalize_expected_pairs(payload["pairs"]) or set()
    if isinstance(payload, list):
        pairs: list[dict[str, str]] = []
        for plan in payload:
            benchmark_ids = plan.get("selected_benchmarks") or ["NO_DIRECT_MATCH"]
            pairs.extend(
                {"case_id": plan.get("case_id", ""), "benchmark_id": benchmark_id}
                for benchmark_id in benchmark_ids
            )
        return _normalize_expected_pairs(pairs) or set()
    raise ValueError("review scope must contain a pairs list")


def write_review_report(path: str | Path, verdict: dict[str, Any]) -> None:
    """Write a human-readable matrix verdict beside the machine-readable JSON."""

    lines = [
        "# Auto-Bench Human Suitability Verdict",
        "",
        f"- Status: **{verdict['status']}**",
        f"- Reason: {verdict['reason']}",
        f"- Expected items: {verdict.get('expected_item_count', len(verdict.get('items', [])))}",
        f"- Submitted items: {verdict.get('submitted_item_count', 0)}",
        "",
        "## Item Verdicts",
        "",
        "| Case | Benchmark | Status | Overall mean | Reason |",
        "|---|---|---:|---:|---|",
    ]
    for item in verdict.get("items", []):
        overall = item.get("overall_mean")
        overall_text = f"{overall:.3f}" if isinstance(overall, (int, float)) else "pending"
        reason = str(item.get("reason", "")).replace("|", "\\|")
        lines.append(
            f"| {item['case_id']} | {item['benchmark_id']} | {item['status']} | {overall_text} | {reason} |"
        )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
