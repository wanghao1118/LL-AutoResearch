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


def _all_families() -> dict:
    """Effects covering all four families, so a test can isolate one gate at a time."""

    return _effects(
        _entry("m", family="main"),
        _entry("ab", family="ablation", variant_id="no-oracle"),
        _entry(
            "cs",
            family="case_study",
            variant_id="cases",
            simulated_target=None,
            required_categories={"recovered": 4, "unrecovered": 4},
        ),
        _entry(
            "an",
            family="analysis",
            variant_id="budget",
            simulated_target=None,
            expected_shape="saturating",
        ),
    )


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
    _write_design(tmp_path, _all_families(), design_text)
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


def test_families_are_reported_and_absence_needs_a_written_justification(tmp_path: Path) -> None:
    """An absent family is a blocker unless the design says why it is absent.

    The contract allows "populated or justified", so the machine enforces the half it can
    check — that a justification exists — and leaves whether the justification is sound to
    the design Skill and the auditor.
    """

    _write_design(tmp_path, _effects(_entry("a")))
    result = check_design(tmp_path)
    assert result["status"] == "FAIL"
    assert result["families_present"] == ["main"]
    assert sorted(result["missing_families"]) == ["ablation", "analysis", "case_study"]
    assert sorted(result["unjustified_missing_families"]) == ["ablation", "analysis", "case_study"]
    assert any("ablation family is absent" in error for error in result["errors"])


JUSTIFIED_ABSENCES = [
    (
        "chinese",
        "## Absent families\n\n"
        "- ablation: 本贡献是失效规律发现，无自有模块可供拆解\n"
        "- case_study: 主张为总体分布性质，单例无法承载\n"
        "- analysis: 唯一自变量已在主实验中扫描完毕\n",
    ),
    (
        "english",
        "## Absent families\n\n"
        "- ablation: the contribution has no internal modules to remove\n"
        "- case_study: the claim is distributional, no single trace can carry it\n"
        "- analysis: the only free axis is already swept in the main experiment\n",
    ),
    (
        "bold-titlecase",
        "## Absent Families\n\n"
        "- **Ablation**: 本贡献无自有模块可供拆解\n"
        "- **Case Study**: 主张为总体分布性质，单例无法承载\n"
        "- **Analysis**: 唯一自变量已在主实验中扫描完毕\n",
    ),
]


@pytest.mark.parametrize("label,absent_section", JUSTIFIED_ABSENCES)
def test_justified_absent_families_pass(tmp_path: Path, label: str, absent_section: str) -> None:
    _write_design(
        tmp_path,
        _effects(_entry("a")),
        "## Coverage audit\n\nVerdict: PASS\n\n" + absent_section,
    )
    result = check_design(tmp_path)
    assert result["status"] == "PASS", result["errors"]
    assert result["unjustified_missing_families"] == []
    assert set(result["absent_family_justifications"]) == {"ablation", "case_study", "analysis"}


NON_JUSTIFICATIONS = [
    ("empty-values", "## Absent families\n\n- ablation:\n- case_study:\n- analysis:\n"),
    ("prose-without-labels", "## Absent families\n\n没有做 ablation case_study analysis 这几类。\n"),
    ("wrong-section", "## Notes\n\n- ablation: 无自有模块可供拆解，因此不做本类实验\n"),
]


@pytest.mark.parametrize("label,absent_section", NON_JUSTIFICATIONS)
def test_absences_without_a_written_reason_are_rejected(
    tmp_path: Path, label: str, absent_section: str
) -> None:
    """A family name alone, or prose outside the section, leaves the reason unwritten."""

    _write_design(
        tmp_path,
        _effects(_entry("a")),
        "## Coverage audit\n\nVerdict: PASS\n\n" + absent_section,
    )
    result = check_design(tmp_path)
    assert result["status"] == "FAIL"
    assert sorted(result["unjustified_missing_families"]) == ["ablation", "analysis", "case_study"]


THIN_REASONS = [
    ("english-placeholders", "## Absent families\n\n- ablation: n/a\n- case_study: TBD\n- analysis: none\n"),
    ("chinese-placeholders", "## Absent families\n\n- ablation: 无\n- case_study: 待定\n- analysis: 不适用\n"),
    ("too-short", "## Absent families\n\n- ablation: no need\n- case_study: 不做\n- analysis: skip it\n"),
]


@pytest.mark.parametrize("label,absent_section", THIN_REASONS)
def test_thin_reasons_pass_the_machine_gate_and_reach_the_auditor(
    tmp_path: Path, label: str, absent_section: str
) -> None:
    """`n/a` clears the machine gate on purpose — scoring a reason is not a machine job.

    Judging whether ``n/a`` is an adequate reason requires reading it against the
    contributions, which the design Skill and ``autodesign-integrity-auditor`` do and the gate
    cannot. An earlier version scored substance by CJK-character and Latin-word counts, which
    put the machine in the business of grading scientific arguments by length. The gate now
    checks only that a reason was written, and hands the text over verbatim so the auditor can
    reject it.
    """

    _write_design(
        tmp_path,
        _effects(_entry("a")),
        "## Coverage audit\n\nVerdict: PASS\n\n" + absent_section,
    )
    result = check_design(tmp_path)
    assert result["status"] == "PASS", result["errors"]
    assert result["unjustified_missing_families"] == []
    assert set(result["absent_family_justifications"]) == {"ablation", "case_study", "analysis"}
    # The verbatim text has to survive, or the auditor has nothing to judge.
    assert all(result["absent_family_justifications"].values())


def test_an_empty_value_cannot_borrow_the_next_bullet(tmp_path: Path) -> None:
    """`- ablation:` followed by `- case_study: ...` must not read the next line as its reason."""

    _write_design(
        tmp_path,
        _effects(_entry("a")),
        "## Coverage audit\n\nVerdict: PASS\n\n"
        "## Absent families\n\n"
        "- ablation:\n"
        "- case_study: 主张为总体分布性质，单例无法承载\n"
        "- analysis: 唯一自变量已在主实验中扫描完毕\n",
    )
    result = check_design(tmp_path)
    assert result["status"] == "FAIL"
    assert result["unjustified_missing_families"] == ["ablation"]
    assert "ablation" not in result["absent_family_justifications"]


def test_partially_justified_absences_report_only_the_gaps(tmp_path: Path) -> None:
    _write_design(
        tmp_path,
        _effects(_entry("a")),
        "## Coverage audit\n\nVerdict: PASS\n\n"
        "## Absent families\n\n- ablation: 本贡献无自有模块可供拆解\n",
    )
    result = check_design(tmp_path)
    assert result["status"] == "FAIL"
    assert sorted(result["unjustified_missing_families"]) == ["analysis", "case_study"]
    assert set(result["absent_family_justifications"]) == {"ablation"}


def test_all_four_families_present_needs_no_justification(tmp_path: Path) -> None:
    _write_design(tmp_path, _all_families())
    result = check_design(tmp_path)
    assert result["status"] == "PASS", result["errors"]
    assert result["missing_families"] == []
    assert result["unjustified_missing_families"] == []
    assert result["absent_family_justifications"] == {}


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
