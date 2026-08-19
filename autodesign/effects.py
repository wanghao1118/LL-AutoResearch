"""Design-time target validation and observed-versus-target comparison.

Two deterministic checks sit on the design → run boundary:

`check_design` validates that `expected_effects.json` is structurally usable before any
expensive implementation starts: schema version, `SIMULATED_TARGET` status, and a literal
threshold, target basis, and miss route on every entry. It deliberately does not judge
whether a target is scientifically sensible — that is the design Skill's job.

`compare_effects` runs after result ingestion. It joins each design entry to the observed
aggregate for its (experiment, variant, task, metric) cell, writes the observed value back
into `expected_effects.json`, and renders `effect_comparison.md`. Thresholds are evaluated
only in the forms the contract allows: an absolute comparison against a literal number, or
a relative comparison against a named reference variant. Anything else is reported as
`NOT_EVALUABLE` with the reason, rather than guessed at. Simulated targets are never
written into observed fields and are never edited here.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .io import read_json, write_json, write_text

VALUE_STATUS = "SIMULATED_TARGET"
FAMILIES = ("main", "ablation", "case_study", "analysis")
EVIDENCE_CLASSES = ("CLAIM_BEARING", "MECHANISM_PILOT", "ENGINEERING_SMOKE")
ON_MISS_ROUTES = ("iteration", "tuning", "stop")
TARGET_BASES = ("handoff_reported", "published_baseline", "design_estimate")
EXPECTED_SHAPES = (
    "monotonic_increasing",
    "monotonic_decreasing",
    "saturating",
    "non_monotonic",
    "flat",
)
ABSOLUTE_THRESHOLD = re.compile(r"^(>=|<=|>|<|==)\s*(-?\d+(?:\.\d+)?)$")
RELATIVE_THRESHOLD = re.compile(
    r"^(>=|<=|>|<)\s*reference\s*([+-])\s*(\d+(?:\.\d+)?)$", re.IGNORECASE
)
COMPARATORS = {
    ">=": lambda observed, bound: observed >= bound,
    "<=": lambda observed, bound: observed <= bound,
    ">": lambda observed, bound: observed > bound,
    "<": lambda observed, bound: observed < bound,
    "==": lambda observed, bound: observed == bound,
}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _entry_errors(index: int, entry: Any) -> list[str]:
    """Validate one expected-effects entry against the design contract."""

    if not isinstance(entry, dict):
        return [f"entries[{index}] must be an object"]
    errors: list[str] = []
    entry_id = entry.get("entry_id")
    if not isinstance(entry_id, str) or not entry_id.strip():
        errors.append(f"entries[{index}].entry_id must be a non-empty string")
    for field in ("experiment_id", "variant_id", "benchmark_task_id", "metric"):
        value = entry.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"entries[{index}].{field} must be a non-empty string")
    if entry.get("family") not in FAMILIES:
        errors.append(f"entries[{index}].family must be one of {list(FAMILIES)}")
    if entry.get("evidence_class") not in EVIDENCE_CLASSES:
        errors.append(
            f"entries[{index}].evidence_class must be one of {list(EVIDENCE_CLASSES)}"
        )
    claim_ids = entry.get("claim_ids")
    if not isinstance(claim_ids, list) or not claim_ids:
        errors.append(f"entries[{index}].claim_ids must be a non-empty list")
    if entry.get("target_basis") not in TARGET_BASES:
        errors.append(f"entries[{index}].target_basis must be one of {list(TARGET_BASES)}")
    if entry.get("on_miss") not in ON_MISS_ROUTES:
        errors.append(f"entries[{index}].on_miss must be one of {list(ON_MISS_ROUTES)}")
    threshold = entry.get("decision_threshold")
    if not isinstance(threshold, str) or not threshold.strip():
        errors.append(f"entries[{index}].decision_threshold must be a literal string")
    elif RELATIVE_THRESHOLD.match(threshold.strip()):
        reference = entry.get("threshold_reference_variant")
        if not isinstance(reference, str) or not reference.strip():
            errors.append(
                f"entries[{index}] uses a relative threshold and must name "
                "threshold_reference_variant"
            )
    family = entry.get("family")
    if family == "case_study":
        categories = entry.get("required_categories")
        if not isinstance(categories, dict) or not categories:
            errors.append(
                f"entries[{index}] is a case_study and needs required_categories counts"
            )
        elif not all(
            isinstance(count, int) and not isinstance(count, bool) and count > 0
            for count in categories.values()
        ):
            errors.append(
                f"entries[{index}].required_categories values must be positive integers"
            )
    else:
        shape = entry.get("expected_shape")
        if shape is None:
            if not _is_number(entry.get("simulated_target")):
                errors.append(f"entries[{index}].simulated_target must be a number")
        elif shape not in EXPECTED_SHAPES:
            errors.append(
                f"entries[{index}].expected_shape must be one of {list(EXPECTED_SHAPES)}"
            )
    bounds = entry.get("acceptable_range")
    if bounds is not None:
        if (
            not isinstance(bounds, list)
            or len(bounds) != 2
            or not all(_is_number(bound) for bound in bounds)
            or bounds[0] > bounds[1]
        ):
            errors.append(
                f"entries[{index}].acceptable_range must be an ordered [low, high] number pair"
            )
    return errors


def validate_expected_effects(effects: Any) -> list[str]:
    """Return every contract violation in an expected_effects.json payload."""

    if not isinstance(effects, dict):
        return ["expected_effects.json must contain an object"]
    errors: list[str] = []
    if effects.get("schema_version") != "1.0":
        errors.append("expected_effects.schema_version must be 1.0")
    if effects.get("value_status") != VALUE_STATUS:
        errors.append(f"expected_effects.value_status must be {VALUE_STATUS}")
    entries = effects.get("entries")
    if not isinstance(entries, list) or not entries:
        return [*errors, "expected_effects.entries must be a non-empty list"]
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        errors.extend(_entry_errors(index, entry))
        if isinstance(entry, dict):
            entry_id = entry.get("entry_id")
            if isinstance(entry_id, str):
                if entry_id in seen:
                    errors.append(f"Duplicate entry_id: {entry_id}")
                seen.add(entry_id)
    return errors


def _schedule_cells(schedule: Any) -> set[tuple[str, str, str]]:
    if not isinstance(schedule, dict):
        return set()
    cells = schedule.get("cells")
    if not isinstance(cells, list):
        return set()
    return {
        (
            str(cell.get("experiment_id") or ""),
            str(cell.get("variant_id") or ""),
            str(cell.get("benchmark_task_id") or ""),
        )
        for cell in cells
        if isinstance(cell, dict)
    }


def _coverage_verdict(design_text: str) -> tuple[bool, str]:
    """Decide whether the design's coverage audit reaches an affirmative PASS.

    The gate must not be satisfied by the mere presence of the token ``PASS`` — a blocked
    design routinely writes prose like ``FAIL - cannot PASS until baselines land``, and a
    substring search would wave it through. So the whole decision rests on an explicit
    verdict line: a line whose leading label is ``Verdict`` (or ``Coverage audit``), read
    only inside the coverage-audit section when that heading exists.

    That verdict line passes only when its value is exactly the uppercase token ``PASS``
    with no negative token (``FAIL``, ``BLOCKED``, ``BLOCKER``, ``PENDING``, ``TODO``)
    anywhere on it — so a hedged or dual-verdict line is a blocker, not a pass. The label
    may be bold, bulleted, backticked, or written straight onto the heading
    (``## Coverage audit: PASS``); when several verdict lines exist the last one wins. A
    design with no verdict line at all fails with that stated as the reason, which keeps
    the failure legible instead of reporting a generic miss.
    """

    section = design_text
    heading = re.search(
        r"^#{1,6}\s*coverage\s+audit\b[^\S\n]*(?:[:：][^\S\n]*(?P<inline>.+?))?[^\S\n]*$",
        design_text,
        re.IGNORECASE | re.MULTILINE,
    )
    inline_verdict = None
    if heading is not None:
        inline_verdict = heading.group("inline")
        rest = design_text[heading.end() :]
        next_heading = re.search(r"^#{1,6}\s+\S", rest, re.MULTILINE)
        section = rest[: next_heading.start()] if next_heading is not None else rest

    verdict_values = [
        match.group(1)
        for match in re.finditer(
            r"^\s*(?:[-*+]\s*)?(?:\*\*)?\s*(?:verdict|coverage\s+audit)\s*(?:\*\*)?\s*[:：]\s*(.+?)\s*$",
            section,
            re.IGNORECASE | re.MULTILINE,
        )
    ]
    if not verdict_values and inline_verdict:
        verdict_values = [inline_verdict]
    if not verdict_values:
        return False, "no `Verdict:` line found in the coverage audit"

    value = verdict_values[-1].strip().strip("*`").strip().strip("*`").strip()
    negatives = [
        token
        for token in ("FAIL", "BLOCKED", "BLOCKER", "PENDING", "TODO")
        if re.search(rf"\b{token}\b", value, re.IGNORECASE)
    ]
    if negatives:
        return False, f"verdict {value!r} carries blocking token(s) {negatives}"
    if re.fullmatch(r"PASS", value) is None:
        return False, f"verdict {value!r} is not the literal token PASS"
    return True, "verdict PASS"


def check_design(run_dir: str | Path) -> dict[str, Any]:
    """Validate the design-phase artifacts before implementation begins."""

    run_path = Path(run_dir)
    errors: list[str] = []
    design_path = run_path / "experiment_design.md"
    effects_path = run_path / "expected_effects.json"
    if not design_path.is_file():
        errors.append(
            "experiment_design.md is missing; produce it with the "
            "autodesign-experiment-design Skill"
        )
    if not effects_path.is_file():
        errors.append(
            "expected_effects.json is missing; produce it with the "
            "autodesign-experiment-design Skill"
        )
    if errors:
        return {"status": "FAIL", "run_dir": str(run_path.resolve()), "errors": errors}

    effects = read_json(effects_path)
    errors.extend(validate_expected_effects(effects))
    entries = effects.get("entries") if isinstance(effects, dict) else None
    entries = entries if isinstance(entries, list) else []

    design_text = design_path.read_text(encoding="utf-8")
    coverage_pass, verdict_detail = _coverage_verdict(design_text)
    if not coverage_pass:
        errors.append(f"experiment_design.md coverage audit is not a literal PASS: {verdict_detail}")
    families_present = {
        entry.get("family")
        for entry in entries
        if isinstance(entry, dict) and entry.get("family") in FAMILIES
    }
    missing_families = [family for family in FAMILIES if family not in families_present]
    if not any(
        isinstance(entry, dict) and entry.get("evidence_class") == "CLAIM_BEARING"
        for entry in entries
    ):
        errors.append("no CLAIM_BEARING entry exists in expected_effects.json")

    schedule_path = run_path / "experiment_schedule.json"
    uncovered_cells: list[list[str]] = []
    if schedule_path.is_file():
        scheduled = _schedule_cells(read_json(schedule_path))
        covered = {
            (
                str(entry.get("experiment_id") or ""),
                str(entry.get("variant_id") or ""),
                str(entry.get("benchmark_task_id") or ""),
            )
            for entry in entries
            if isinstance(entry, dict)
        }
        uncovered_cells = [list(cell) for cell in sorted(scheduled - covered)]
        if uncovered_cells:
            errors.append(
                f"scheduled cells without an expected_effects entry: {uncovered_cells}"
            )

    return {
        "status": "PASS" if not errors else "FAIL",
        "run_dir": str(run_path.resolve()),
        "entry_count": len(entries),
        "families_present": sorted(family for family in families_present if family),
        "missing_families": missing_families,
        "uncovered_scheduled_cells": uncovered_cells,
        "coverage_audit_pass": coverage_pass,
        "coverage_audit_verdict": verdict_detail,
        "errors": errors,
    }


def _aggregate_index(summary: Any) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    if not isinstance(summary, dict):
        return {}
    aggregates = summary.get("aggregates")
    if not isinstance(aggregates, list):
        return {}
    return {
        (
            str(item.get("experiment_id") or ""),
            str(item.get("variant_id") or ""),
            str(item.get("benchmark_task_id") or ""),
            str(item.get("metric") or ""),
        ): item
        for item in aggregates
        if isinstance(item, dict)
    }


def _evaluate_threshold(
    entry: dict[str, Any],
    observed: float | None,
    index: dict[tuple[str, str, str, str], dict[str, Any]],
) -> tuple[str, str]:
    """Return (outcome, detail) for one entry's literal decision threshold."""

    threshold = str(entry.get("decision_threshold") or "").strip()
    if observed is None:
        return "NOT_EVALUABLE", "no observed aggregate for this cell"
    if entry.get("family") == "case_study":
        return "NOT_EVALUABLE", "case-study categories require manual category counting"
    if entry.get("expected_shape") is not None and not ABSOLUTE_THRESHOLD.match(threshold):
        return "NOT_EVALUABLE", "shape prediction requires manual curve inspection"

    absolute = ABSOLUTE_THRESHOLD.match(threshold)
    if absolute:
        operator, bound = absolute.group(1), float(absolute.group(2))
        met = COMPARATORS[operator](observed, bound)
        return ("MET" if met else "MISSED"), f"{observed} {operator} {bound}"

    relative = RELATIVE_THRESHOLD.match(threshold)
    if relative:
        operator, sign, delta = relative.group(1), relative.group(2), float(relative.group(3))
        reference_variant = str(entry.get("threshold_reference_variant") or "")
        reference = index.get(
            (
                str(entry.get("experiment_id") or ""),
                reference_variant,
                str(entry.get("benchmark_task_id") or ""),
                str(entry.get("metric") or ""),
            )
        )
        if reference is None or not _is_number(reference.get("mean")):
            return (
                "NOT_EVALUABLE",
                f"reference variant {reference_variant!r} has no observed aggregate",
            )
        bound = float(reference["mean"]) + (delta if sign == "+" else -delta)
        met = COMPARATORS[operator](observed, bound)
        return (
            ("MET" if met else "MISSED"),
            f"{observed} {operator} {reference['mean']} {sign} {delta} = {bound}",
        )
    return "NOT_EVALUABLE", f"threshold {threshold!r} is not machine-evaluable"


def _comparison_table(rows: list[dict[str, Any]]) -> str:
    header = (
        "| Entry ID | Experiment | Family | Variant | Task | Metric | "
        "Simulated target | Decision threshold | Observed | Threshold outcome | On miss |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
    )
    lines = []
    for row in rows:
        target = row["simulated_target"]
        observed = row["observed_value"]
        lines.append(
            f"| {row['entry_id']} | {row['experiment_id']} | {row['family']} | "
            f"{row['variant_id']} | {row['benchmark_task_id']} | {row['metric']} | "
            f"{'—' if target is None else target} | {row['decision_threshold']} | "
            f"{'—' if observed is None else observed} | {row['threshold_outcome']} | "
            f"{row['on_miss']} |"
        )
    return header + "\n".join(lines) + "\n"


def compare_effects(run_dir: str | Path) -> dict[str, Any]:
    """Join observed aggregates to design targets and write effect_comparison.md."""

    run_path = Path(run_dir)
    effects_path = run_path / "expected_effects.json"
    summary_path = run_path / "result_summary.json"
    for path, owner in (
        (effects_path, "autodesign-experiment-design Skill"),
        (summary_path, "autodesign skill-ingest"),
    ):
        if not path.is_file():
            raise ValueError(f"required artifact is missing: {path}; produce it with {owner}")

    effects = read_json(effects_path)
    contract_errors = validate_expected_effects(effects)
    if contract_errors:
        return {
            "status": "FAIL",
            "run_dir": str(run_path.resolve()),
            "errors": contract_errors,
        }
    summary = read_json(summary_path)
    index = _aggregate_index(summary)

    rows: list[dict[str, Any]] = []
    for entry in effects["entries"]:
        key = (
            str(entry.get("experiment_id") or ""),
            str(entry.get("variant_id") or ""),
            str(entry.get("benchmark_task_id") or ""),
            str(entry.get("metric") or ""),
        )
        aggregate = index.get(key)
        observed = (
            float(aggregate["mean"])
            if aggregate is not None and _is_number(aggregate.get("mean"))
            else None
        )
        outcome, detail = _evaluate_threshold(entry, observed, index)
        entry["observed_value"] = observed
        entry["observed_status"] = "OBSERVED" if observed is not None else "NOT_EXECUTED"
        entry["threshold_outcome"] = outcome
        entry["threshold_detail"] = detail
        rows.append(
            {
                "entry_id": entry.get("entry_id"),
                "experiment_id": key[0],
                "family": entry.get("family"),
                "variant_id": key[1],
                "benchmark_task_id": key[2],
                "metric": key[3],
                "claim_ids": entry.get("claim_ids"),
                "simulated_target": entry.get("simulated_target"),
                "decision_threshold": entry.get("decision_threshold"),
                "observed_value": observed,
                "threshold_outcome": outcome,
                "threshold_detail": detail,
                "on_miss": entry.get("on_miss"),
            }
        )

    write_json(effects_path, effects)
    missed = [row for row in rows if row["threshold_outcome"] == "MISSED"]
    not_evaluable = [row for row in rows if row["threshold_outcome"] == "NOT_EVALUABLE"]
    routing_lines = [
        f"- `{row['entry_id']}` ({row['family']}, claims {row['claim_ids']}): "
        f"{row['threshold_detail']} → route `{row['on_miss']}`"
        for row in missed
    ] or ["- No missed threshold."]
    manual_lines = [
        f"- `{row['entry_id']}` ({row['family']}): {row['threshold_detail']}"
        for row in not_evaluable
    ] or ["- None."]
    write_text(
        run_path / "effect_comparison.md",
        "# Effect Comparison\n\n"
        "Observed values come from `result_summary.json` aggregates. Simulated targets are "
        "design-time hypotheses and are never edited after execution.\n\n"
        "## Per-entry comparison\n\n"
        + _comparison_table(rows)
        + "\n## Routing\n\n"
        + "\n".join(routing_lines)
        + "\n\n## Manual evaluation required\n\n"
        + "\n".join(manual_lines)
        + "\n\n## Target calibration findings\n\n"
        "Record systematic target miscalibration here as a design finding for "
        "`autodesign-experiment-design`. Do not edit `simulated_target` values.\n",
    )
    return {
        "status": "PASS",
        "run_dir": str(run_path.resolve()),
        "entry_count": len(rows),
        "met_count": sum(1 for row in rows if row["threshold_outcome"] == "MET"),
        "missed_count": len(missed),
        "not_evaluable_count": len(not_evaluable),
        "rows": rows,
        "errors": [],
    }
