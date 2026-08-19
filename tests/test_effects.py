"""Contract tests for design-time validation and observed-versus-target comparison.

These tests pin the two gates that sit on the design → run boundary. The coverage-verdict
cases exist because an earlier implementation accepted any design containing the substring
``PASS``, which let a blocked design (``Verdict: FAIL - cannot PASS until baselines land``)
through the gate. Presence of a token is not a verdict, so each rejection case below asserts
a specific reason string rather than only a FAIL status.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from autodesign.effects import check_design, compare_effects, validate_expected_effects


def _entry(
    entry_id: str,
    *,
    experiment_id: str = "E1",
    family: str = "main",
    variant_id: str = "ours",
    metric: str = "pass@1",
    simulated_target: float | None = 29.1,
    decision_threshold: str = ">= 20.0",
    evidence_class: str = "CLAIM_BEARING",
    reference: str | None = None,
    **extra: object,
) -> dict:
    entry = {
        "entry_id": entry_id,
        "experiment_id": experiment_id,
        "family": family,
        "evidence_class": evidence_class,
        "claim_ids": ["C1"],
        "variant_id": variant_id,
        "benchmark_task_id": "tb-1.0",
        "metric": metric,
        "simulated_target": simulated_target,
        "target_basis": "handoff_reported",
        "decision_threshold": decision_threshold,
        "on_miss": "iteration",
        "observed_value": None,
        "observed_status": "NOT_EXECUTED",
    }
    if reference is not None:
        entry["threshold_reference_variant"] = reference
    entry.update(extra)
    return entry


def _effects(*entries: dict) -> dict:
    return {
        "schema_version": "1.0",
        "value_status": "SIMULATED_TARGET",
        "generated_by": "autodesign-experiment-design",
        "entries": list(entries),
    }


def _write_design(run_dir: Path, effects: dict, design_text: str = "## Coverage audit\n\nVerdict: PASS\n") -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "experiment_design.md").write_text(design_text, encoding="utf-8")
    (run_dir / "expected_effects.json").write_text(json.dumps(effects, indent=2), encoding="utf-8")


def _write_summary(run_dir: Path, aggregates: list[dict]) -> None:
    (run_dir / "result_summary.json").write_text(
        json.dumps({"status": "READY_FOR_GPT_DIAGNOSIS", "aggregates": aggregates}, indent=2),
        encoding="utf-8",
    )


def _aggregate(experiment_id: str, variant_id: str, mean: float, metric: str = "pass@1") -> dict:
    return {
        "experiment_id": experiment_id,
        "variant_id": variant_id,
        "benchmark_task_id": "tb-1.0",
        "metric": metric,
        "n": 2,
        "mean": mean,
        "sample_std": 0.5,
        "min": mean - 0.5,
        "max": mean + 0.5,
        "values": [mean - 0.5, mean + 0.5],
    }


AFFIRMATIVE_VERDICTS = [
    "## Coverage audit\n\nVerdict: PASS\n",
    "## Coverage audit\n\n**Verdict:** **PASS**\n",
    "## Coverage audit\n\n- Verdict: PASS\n",
    "## Coverage audit\n\nVerdict: `PASS`\n",
    "## Coverage audit\n\nVerdict：PASS\n",
    "## Coverage audit: PASS\n\nAll families populated.\n",
    "## Coverage audit\n\nEvery claim has a falsifier.\n\nVerdict: PASS\n",
]

BLOCKING_VERDICTS = [
    ("## Coverage audit\n\nVerdict: FAIL\n", "FAIL"),
    ("## Coverage audit\n\nVerdict: FAIL - cannot PASS until baselines land\n", "FAIL"),
    ("## Coverage audit\n\nVerdict: BLOCKED\n\nBlockers:\n- no PASS possible yet\n", "BLOCKED"),
    ("## Coverage audit\n\nVerdict: PASS pending baseline rerun\n", "PENDING"),
    ("## Coverage audit\n\nVerdict: TODO\n", "TODO"),
]

NON_VERDICTS = [
    "## Coverage audit\n\nWe are PASSING seeds through.\n",
    "## Coverage audit\n\nLooks fine to me.\n",
    "# Design\n\nThe coverage audit will PASS once seeds are locked.\n",
]


@pytest.mark.parametrize("design_text", AFFIRMATIVE_VERDICTS)
def test_affirmative_coverage_verdict_passes(tmp_path: Path, design_text: str) -> None:
    _write_design(tmp_path, _effects(_entry("a")), design_text)
    result = check_design(tmp_path)
    assert result["status"] == "PASS", result["errors"]
    assert result["coverage_audit_pass"] is True


@pytest.mark.parametrize("design_text,token", BLOCKING_VERDICTS)
def test_blocking_verdict_is_rejected(tmp_path: Path, design_text: str, token: str) -> None:
    """A blocked design must fail even when the word PASS appears on the verdict line."""

    _write_design(tmp_path, _effects(_entry("a")), design_text)
    result = check_design(tmp_path)
    assert result["status"] == "FAIL"
    assert result["coverage_audit_pass"] is False
    assert token in result["coverage_audit_verdict"]


@pytest.mark.parametrize("design_text", NON_VERDICTS)
def test_prose_mentioning_pass_is_not_a_verdict(tmp_path: Path, design_text: str) -> None:
    _write_design(tmp_path, _effects(_entry("a")), design_text)
    result = check_design(tmp_path)
    assert result["status"] == "FAIL"
    assert "no `Verdict:` line" in result["coverage_audit_verdict"]


def test_lowercase_pass_is_not_a_verdict(tmp_path: Path) -> None:
    _write_design(tmp_path, _effects(_entry("a")), "## Coverage audit\n\nVerdict: pass\n")
    assert check_design(tmp_path)["status"] == "FAIL"


def test_pass_outside_the_coverage_section_is_ignored(tmp_path: Path) -> None:
    """Only the coverage-audit section decides the gate."""

    _write_design(
        tmp_path,
        _effects(_entry("a")),
        "## Coverage audit\n\nVerdict: BLOCKED\n\n## Notes\n\nVerdict: PASS\n",
    )
    result = check_design(tmp_path)
    assert result["status"] == "FAIL"
    assert "BLOCKED" in result["coverage_audit_verdict"]


def test_missing_artifacts_name_their_owner_skill(tmp_path: Path) -> None:
    tmp_path.mkdir(exist_ok=True)
    result = check_design(tmp_path)
    assert result["status"] == "FAIL"
    assert any("experiment_design.md is missing" in error for error in result["errors"])
    assert any("autodesign-experiment-design" in error for error in result["errors"])


def test_claim_bearing_entry_is_required(tmp_path: Path) -> None:
    _write_design(tmp_path, _effects(_entry("a", evidence_class="ENGINEERING_SMOKE")))
    result = check_design(tmp_path)
    assert result["status"] == "FAIL"
    assert any("CLAIM_BEARING" in error for error in result["errors"])


def test_scheduled_cell_without_an_entry_fails(tmp_path: Path) -> None:
    _write_design(tmp_path, _effects(_entry("a")))
    (tmp_path / "experiment_schedule.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "cells": [
                    {
                        "experiment_id": "E2",
                        "variant_id": "unplanned",
                        "benchmark_task_id": "tb-1.0",
                        "seed": 1,
                        "metrics": ["pass@1"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    result = check_design(tmp_path)
    assert result["status"] == "FAIL"
    assert result["uncovered_scheduled_cells"] == [["E2", "unplanned", "tb-1.0"]]


def test_families_are_reported_but_absence_is_not_a_machine_failure(tmp_path: Path) -> None:
    """Family completeness is an LLM judgement ("populated or justified"), so it is
    reported for the auditor rather than enforced here."""

    _write_design(tmp_path, _effects(_entry("a")))
    result = check_design(tmp_path)
    assert result["status"] == "PASS"
    assert result["families_present"] == ["main"]
    assert sorted(result["missing_families"]) == ["ablation", "analysis", "case_study"]


@pytest.mark.parametrize(
    "mutation,expected",
    [
        ({"schema_version": "2.0"}, "schema_version must be 1.0"),
        ({"value_status": "OBSERVED"}, "value_status must be SIMULATED_TARGET"),
        ({"entries": []}, "entries must be a non-empty list"),
    ],
)
def test_envelope_contract_violations(mutation: dict, expected: str) -> None:
    effects = _effects(_entry("a"))
    effects.update(mutation)
    assert any(expected in error for error in validate_expected_effects(effects))


@pytest.mark.parametrize(
    "kwargs,expected",
    [
        ({"family": "misc"}, "family must be one of"),
        ({"evidence_class": "GUESS"}, "evidence_class must be one of"),
        ({"on_miss": "ignore"}, "on_miss must be one of"),
        ({"target_basis": "vibes"}, "target_basis must be one of"),
        ({"decision_threshold": ""}, "decision_threshold must be a literal string"),
        ({"simulated_target": None}, "simulated_target must be a number"),
        ({"acceptable_range": [32.0, 26.0]}, "ordered [low, high] number pair"),
        ({"claim_ids": []}, "claim_ids must be a non-empty list"),
        ({"decision_threshold": ">= reference + 2.0"}, "must name threshold_reference_variant"),
        ({"family": "case_study"}, "needs required_categories counts"),
        (
            {"family": "case_study", "required_categories": {"recovered": 0}},
            "required_categories values must be positive integers",
        ),
        ({"expected_shape": "wiggly"}, "expected_shape must be one of"),
    ],
)
def test_entry_contract_violations(kwargs: dict, expected: str) -> None:
    errors = validate_expected_effects(_effects(_entry("a", **kwargs)))
    assert any(expected in error for error in errors), errors


def test_duplicate_entry_ids_are_rejected() -> None:
    errors = validate_expected_effects(_effects(_entry("dup"), _entry("dup", variant_id="other")))
    assert any("Duplicate entry_id: dup" in error for error in errors)


def test_compare_effects_covers_every_threshold_outcome(tmp_path: Path) -> None:
    """One run exercising MET, MISSED, and all three NOT_EVALUABLE routes."""

    effects = _effects(
        _entry("met-abs", variant_id="ours", decision_threshold=">= 20.0"),
        _entry("met-rel", variant_id="ours-b", decision_threshold=">= reference + 2.0", reference="base"),
        _entry("missed", variant_id="ours-c", decision_threshold="<= 27.0"),
        _entry("no-reference", variant_id="ours-d", decision_threshold=">= reference + 2.0", reference="absent"),
        _entry(
            "case",
            family="case_study",
            variant_id="ours-e",
            simulated_target=None,
            required_categories={"recovered": 4, "unrecovered": 4},
        ),
        _entry("shape", family="analysis", variant_id="ours-f", simulated_target=None, expected_shape="saturating", decision_threshold="saturates by 8k"),
        _entry("not-executed", variant_id="never-ran", decision_threshold=">= 26.0"),
    )
    _write_design(tmp_path, effects)
    _write_summary(
        tmp_path,
        [
            _aggregate("E1", "ours", 29.0),
            _aggregate("E1", "ours-b", 29.0),
            _aggregate("E1", "base", 24.5),
            _aggregate("E1", "ours-c", 28.5),
            _aggregate("E1", "ours-d", 27.0),
            _aggregate("E1", "ours-e", 29.0),
            _aggregate("E1", "ours-f", 26.0),
        ],
    )

    result = compare_effects(tmp_path)
    assert result["status"] == "PASS", result["errors"]
    outcomes = {row["entry_id"]: row["threshold_outcome"] for row in result["rows"]}
    assert outcomes == {
        "met-abs": "MET",
        "met-rel": "MET",
        "missed": "MISSED",
        "no-reference": "NOT_EVALUABLE",
        "case": "NOT_EVALUABLE",
        "shape": "NOT_EVALUABLE",
        "not-executed": "NOT_EVALUABLE",
    }
    assert result["met_count"] == 2
    assert result["missed_count"] == 1
    assert result["not_evaluable_count"] == 4

    details = {row["entry_id"]: row["threshold_detail"] for row in result["rows"]}
    assert "24.5 + 2.0 = 26.5" in details["met-rel"]
    assert "'absent' has no observed aggregate" in details["no-reference"]
    assert "manual category counting" in details["case"]
    assert "manual curve inspection" in details["shape"]
    assert "no observed aggregate for this cell" in details["not-executed"]

    report = (tmp_path / "effect_comparison.md").read_text(encoding="utf-8")
    assert "| MISSED |" in report
    assert "route `iteration`" in report
    assert "Do not edit `simulated_target` values." in report


def test_compare_effects_writes_observations_without_touching_targets(tmp_path: Path) -> None:
    """Observed values are written back; simulated targets must survive byte-for-byte."""

    effects = _effects(
        _entry("observed", variant_id="ours", simulated_target=29.1),
        _entry("deferred", variant_id="never-ran", simulated_target=30.0),
    )
    _write_design(tmp_path, effects)
    _write_summary(tmp_path, [_aggregate("E1", "ours", 29.0)])

    compare_effects(tmp_path)
    compare_effects(tmp_path)  # idempotent: a rerun must not drift the targets

    stored = json.loads((tmp_path / "expected_effects.json").read_text(encoding="utf-8"))
    assert stored["value_status"] == "SIMULATED_TARGET"
    by_id = {entry["entry_id"]: entry for entry in stored["entries"]}
    assert by_id["observed"]["simulated_target"] == 29.1
    assert by_id["observed"]["observed_value"] == 29.0
    assert by_id["observed"]["observed_status"] == "OBSERVED"
    assert by_id["deferred"]["simulated_target"] == 30.0
    assert by_id["deferred"]["observed_value"] is None
    assert by_id["deferred"]["observed_status"] == "NOT_EXECUTED"


def test_compare_effects_requires_ingested_results(tmp_path: Path) -> None:
    _write_design(tmp_path, _effects(_entry("a")))
    with pytest.raises(ValueError, match="result_summary.json"):
        compare_effects(tmp_path)


def test_compare_effects_refuses_a_contract_violating_design(tmp_path: Path) -> None:
    effects = _effects(_entry("a"))
    effects["value_status"] = "OBSERVED"
    _write_design(tmp_path, effects)
    _write_summary(tmp_path, [_aggregate("E1", "ours", 29.0)])
    result = compare_effects(tmp_path)
    assert result["status"] == "FAIL"
    assert not (tmp_path / "effect_comparison.md").exists()
