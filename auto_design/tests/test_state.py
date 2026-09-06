"""State-transition tests for accepted versus provisional experiment designs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from auto_design.state import advance_run, initialize_run


def _prepare_design(run_dir: Path, verdict: str, *, with_r0: bool = False) -> None:
    design = (
        "# Experiment Design\n\n"
        "## Coverage audit\n\n"
        f"Verdict: {verdict}\n\n"
        "## Absent families\n\n"
        "- ablation: the claim has no self-owned component\n"
        "- case_study: the claim is distributional\n"
        "- analysis: the main experiment already tests the only axis\n"
    )
    effects = {
        "schema_version": "1.0",
        "value_status": "SIMULATED_TARGET",
        "generated_by": "design",
        "entries": [
            {
                "entry_id": "E1-main",
                "experiment_id": "E1",
                "family": "main",
                "evidence_class": "CLAIM_BEARING",
                "claim_ids": ["C1"],
                "variant_id": "ours",
                "benchmark_task_id": "task-1",
                "metric": "reward",
                "simulated_target": 0.5,
                "target_basis": "design_estimate",
                "decision_threshold": ">= 0.4",
                "on_miss": "iteration",
            }
        ],
    }
    (run_dir / "experiment_design.md").write_text(design, encoding="utf-8")
    (run_dir / "expected_effects.json").write_text(json.dumps(effects, indent=2), encoding="utf-8")
    if with_r0:
        (run_dir / "r0_plan.md").write_text("# R0 Plan\n", encoding="utf-8")


def _initialize(tmp_path: Path) -> Path:
    source = tmp_path / "handoff.json"
    source.write_text(
        json.dumps(
            {
                "motivation": "test motivation",
                "contribution": ["test contribution"],
                "benchmark": {"name": "test benchmark"},
            }
        ),
        encoding="utf-8",
    )
    run_dir = tmp_path / "run"
    initialize_run(source, run_dir)
    return run_dir


def _prepare_method_revision(
    run_dir: Path,
    *,
    revision_id: str = "MR-1",
    decision: str | None = None,
    decision_revision_id: str | None = None,
) -> None:
    (run_dir / "breakpoint_recovery.md").write_text(
        "# Breakpoint Recovery\n\nrecovery_policy: no_fixed_boundary_limit\n",
        encoding="utf-8",
    )
    (run_dir / "method_revision_request.md").write_text(
        "# Method Revision Request\n\nBreakpoint ID: BP-1\n",
        encoding="utf-8",
    )
    (run_dir / "method_revision_proposal.md").write_text(
        f"# Method Revision Proposal\n\nRevision ID: {revision_id}\n",
        encoding="utf-8",
    )
    if decision is not None:
        resolved_id = decision_revision_id or revision_id
        (run_dir / "method_revision_decision.md").write_text(
            f"# Method Revision Decision\n\nRevision ID: {resolved_id}\n\nDecision: {decision}\n",
            encoding="utf-8",
        )


def _advance_to_accepted_design(tmp_path: Path) -> Path:
    run_dir = _initialize(tmp_path)
    _prepare_design(run_dir, "PASS")
    advance_run(
        run_dir,
        "EXPERIMENT_DESIGN_READY",
        changed_input="accepted design",
        literal_result="scientific design pass",
    )
    return run_dir


def test_handoff_without_benchmark_is_accepted_for_design_selection(tmp_path: Path) -> None:
    source = tmp_path / "handoff.json"
    source.write_text(
        json.dumps(
            {
                "motivation": "test motivation",
                "contribution": ["test contribution"],
            }
        ),
        encoding="utf-8",
    )
    run_dir = tmp_path / "run"

    initialize_run(source, run_dir)

    brief = (run_dir / "input_brief.md").read_text(encoding="utf-8")
    assert "## Benchmark input (not supplied)" in brief
    assert "there is no user benchmark lock" in brief


@pytest.mark.parametrize("missing_field", ["motivation", "contribution"])
def test_handoff_still_requires_scientific_intent_fields(
    tmp_path: Path, missing_field: str
) -> None:
    payload = {
        "motivation": "test motivation",
        "contribution": ["test contribution"],
    }
    del payload[missing_field]
    source = tmp_path / "handoff.json"
    source.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=missing_field):
        initialize_run(source, tmp_path / "run")


def test_waiting_for_r0_requires_provisional_verdict_and_keeps_input_as_last_milestone(
    tmp_path: Path,
) -> None:
    run_dir = _initialize(tmp_path)
    _prepare_design(run_dir, "PROVISIONAL_WAITING_FOR_R0", with_r0=True)

    report = advance_run(
        run_dir,
        "WAITING_FOR_R0",
        changed_input="provisional design",
        literal_result="R0 required",
    )

    assert report["status"] == "PASS"
    assert report["validation_scope"] == "ARTIFACT_COMPLETENESS"
    assert report["current_stage"] == "WAITING_FOR_R0"
    state = (run_dir / "AUTODESIGN_STATE.md").read_text(encoding="utf-8")
    assert "| Last completed stage | INPUT_READY |" in state
    assert "| Accepted route | provisional in `experiment_design.md`; awaiting R0 |" in state


def test_provisional_design_cannot_advance_as_experiment_design_ready(tmp_path: Path) -> None:
    run_dir = _initialize(tmp_path)
    _prepare_design(run_dir, "PROVISIONAL_WAITING_FOR_R0", with_r0=True)

    with pytest.raises(ValueError, match="requires coverage-audit Verdict: PASS"):
        advance_run(
            run_dir,
            "EXPERIMENT_DESIGN_READY",
            changed_input="provisional design",
            literal_result="incorrect acceptance",
        )


def test_scientific_pass_advances_to_experiment_design_ready(tmp_path: Path) -> None:
    run_dir = _initialize(tmp_path)
    _prepare_design(run_dir, "PASS")

    report = advance_run(
        run_dir,
        "EXPERIMENT_DESIGN_READY",
        changed_input="accepted design",
        literal_result="scientific design pass",
    )

    assert report["status"] == "PASS"
    assert report["current_stage"] == "EXPERIMENT_DESIGN_READY"
    state = (run_dir / "AUTODESIGN_STATE.md").read_text(encoding="utf-8")
    assert "| Last completed stage | EXPERIMENT_DESIGN_READY |" in state
    assert "| Accepted route | accepted in `experiment_design.md` |" in state


def test_scientific_pass_cannot_enter_waiting_for_r0(tmp_path: Path) -> None:
    run_dir = _initialize(tmp_path)
    _prepare_design(run_dir, "PASS", with_r0=True)

    with pytest.raises(
        ValueError,
        match="requires coverage-audit Verdict: PROVISIONAL_WAITING_FOR_R0",
    ):
        advance_run(
            run_dir,
            "WAITING_FOR_R0",
            changed_input="accepted design",
            literal_result="incorrect provisional state",
        )


def test_execution_breakpoint_waits_for_method_revision_approval(tmp_path: Path) -> None:
    run_dir = _advance_to_accepted_design(tmp_path)
    _prepare_method_revision(run_dir)

    report = advance_run(
        run_dir,
        "WAITING_FOR_METHOD_REVISION_APPROVAL",
        changed_input="no admissible boundary repair remains",
        literal_result="minimal method revision proposed",
    )

    assert report["status"] == "PASS"
    assert report["current_stage"] == "WAITING_FOR_METHOD_REVISION_APPROVAL"
    state = (run_dir / "AUTODESIGN_STATE.md").read_text(encoding="utf-8")
    assert "| Blocking condition | human method-revision decision required |" in state
    assert "| Last completed stage | EXPERIMENT_DESIGN_READY |" in state


def test_method_revision_requires_matching_literal_approval(tmp_path: Path) -> None:
    run_dir = _advance_to_accepted_design(tmp_path)
    _prepare_method_revision(
        run_dir,
        decision="APPROVE_MINIMAL_METHOD_REVISION",
        decision_revision_id="MR-stale",
    )
    advance_run(
        run_dir,
        "WAITING_FOR_METHOD_REVISION_APPROVAL",
        changed_input="no admissible boundary repair remains",
        literal_result="minimal method revision proposed",
    )

    with pytest.raises(ValueError, match="does not match proposal"):
        advance_run(
            run_dir,
            "EXPERIMENT_DESIGN_READY",
            changed_input="method revision",
            literal_result="claimed approval",
        )


@pytest.mark.parametrize(
    "decision",
    ["APPROVE_MINIMAL_METHOD_REVISION", "APPROVE_EXCEPTION_METHOD_REVISION"],
)
def test_matching_method_revision_approval_returns_to_design_ready(
    tmp_path: Path, decision: str
) -> None:
    run_dir = _advance_to_accepted_design(tmp_path)
    _prepare_method_revision(run_dir, decision=decision)
    advance_run(
        run_dir,
        "WAITING_FOR_METHOD_REVISION_APPROVAL",
        changed_input="no admissible boundary repair remains",
        literal_result="minimal method revision proposed",
    )

    report = advance_run(
        run_dir,
        "EXPERIMENT_DESIGN_READY",
        changed_input="approved method revision",
        literal_result=decision,
    )

    assert report["status"] == "PASS"
    assert report["current_stage"] == "EXPERIMENT_DESIGN_READY"


def test_abandon_idea_is_terminal_and_requires_matching_user_decision(
    tmp_path: Path,
) -> None:
    run_dir = _advance_to_accepted_design(tmp_path)
    _prepare_method_revision(run_dir, decision="ABANDON_IDEA")
    advance_run(
        run_dir,
        "WAITING_FOR_METHOD_REVISION_APPROVAL",
        changed_input="method revision limit reached",
        literal_result="approval or abandonment required",
    )
    (run_dir / "idea_abandonment.md").write_text(
        "# Idea Abandonment\n\nUser selected ABANDON_IDEA for MR-1.\n",
        encoding="utf-8",
    )

    report = advance_run(
        run_dir,
        "IDEA_ABANDONED",
        changed_input="method_revision_decision.md",
        literal_result="ABANDON_IDEA",
    )

    assert report["status"] == "PASS"
    assert report["current_stage"] == "IDEA_ABANDONED"
    assert report["next_action"] == "none"
