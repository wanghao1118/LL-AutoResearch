"""Thin artifact scaffolding and verification for the Skill-first AutoDesign flow."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .io import read_json, write_text

STATE_PATTERN = re.compile(
    r"^\s*\|\s*Current stage\s*\|\s*([A-Z0-9_]+)\s*\|\s*$",
    re.MULTILINE,
)
AUDIT_VERDICT_PATTERN = re.compile(
    r"^\s*Verdict\s*:\s*(PASS|FAIL)\s*$", re.IGNORECASE | re.MULTILINE
)
STAGE_ORDER = (
    "INPUT_READY",
    "EXPERIMENT_DESIGN_READY",
    "IMPLEMENTATION_READY",
    "EXECUTION_COMPLETE",
    "RESULT_DIAGNOSIS_READY",
    "INTEGRITY_AUDIT_PASS",
    "COMPLETE",
)
KNOWN_STAGES = (
    "INPUT_READY",
    "EXPERIMENT_DESIGN_READY",
    "WAITING_FOR_R0",
    "R0_PASSED",
    "R0_FAILED_RETURN_TO_DESIGN",
    "IMPLEMENTATION_READY",
    "EXECUTION_IN_PROGRESS",
    "EXECUTION_COMPLETE",
    "RESULT_DIAGNOSIS_READY",
    "INTEGRITY_AUDIT_PASS",
    "COMPLETE",
)
STAGE_REQUIREMENTS = {
    "INPUT_READY": ("AUTODESIGN_STATE.md", "input_brief.md"),
    "EXPERIMENT_DESIGN_READY": ("experiment_design.md", "expected_effects.json"),
    "IMPLEMENTATION_READY": (
        "implementation_notes.md",
        "generated_project",
        "command_plan.json",
        "experiment_schedule.json",
        "result_contract.json",
    ),
    "EXECUTION_COMPLETE": ("execution_record.json", "effect_comparison.md"),
    "RESULT_DIAGNOSIS_READY": (
        "result_summary.json",
        "result_diagnosis.md",
        "result_route.md",
    ),
    "INTEGRITY_AUDIT_PASS": ("integrity_audit.md",),
    "COMPLETE": (),
}
NEXT_SKILL = {
    "INPUT_READY": "autodesign-experiment-design",
    "EXPERIMENT_DESIGN_READY": "autodesign-experiment-run",
    "WAITING_FOR_R0": "autodesign-experiment-run",
    "R0_PASSED": "autodesign-experiment-design",
    "R0_FAILED_RETURN_TO_DESIGN": "autodesign-experiment-design",
    "IMPLEMENTATION_READY": "autodesign-experiment-run",
    "EXECUTION_IN_PROGRESS": "autodesign-experiment-run",
    "EXECUTION_COMPLETE": "autodesign-result-scientist",
    "RESULT_DIAGNOSIS_READY": "run-autodesign",
    "INTEGRITY_AUDIT_PASS": "run-autodesign",
    "COMPLETE": "none",
}
STATE_ARTIFACTS = (
    ("input_brief.md", "normalized AutoSearch handoff"),
    ("experiment_design.md", "accepted four-family experiment design"),
    ("expected_effects.json", "design-time simulated targets and thresholds"),
    ("r0_plan.md", "optional low-cost gate plan"),
    ("r0_record.json", "optional observed R0 decision"),
    ("implementation_notes.md", "implementation handoff"),
    ("generated_project", "runnable experiment project"),
    ("command_plan.json", "ordered execution commands"),
    ("experiment_schedule.json", "expected result cells"),
    ("result_contract.json", "primary observed result path"),
    ("execution_record.json", "literal execution evidence"),
    ("result_summary.json", "validated result aggregates"),
    ("effect_comparison.md", "observed versus simulated-target outcomes"),
    ("result_diagnosis.md", "scientific interpretation"),
    ("result_route.md", "iteration, tuning, stop, or report dispatch"),
    ("integrity_audit.md", "final claim-evidence audit"),
)

LAST_COMPLETED_STAGE = {
    "WAITING_FOR_R0": "EXPERIMENT_DESIGN_READY",
    "R0_FAILED_RETURN_TO_DESIGN": "EXPERIMENT_DESIGN_READY",
    "EXECUTION_IN_PROGRESS": "IMPLEMENTATION_READY",
}


def _json_block(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def _markdown_table_cell(value: str) -> str:
    """Keep agent-provided text inside one Markdown table cell."""

    return str(value).replace("\r\n", "\n").replace("\r", "\n").replace("|", "&#124;").replace("\n", "<br>")


def _state_field_pattern(field: str) -> re.Pattern[str]:
    return re.compile(
        rf"^\s*\|\s*{re.escape(field)}\s*\|\s*([^|]*?)\s*\|\s*$",
        re.MULTILINE,
    )


def _replace_state_field(text: str, field: str, value: str) -> str:
    pattern = _state_field_pattern(field)
    if not pattern.search(text):
        raise ValueError(
            f"AUTODESIGN_STATE.md is missing the {field!r} row; restore it or run skill-init"
        )
    return pattern.sub(f"| {field} | {value} |", text, count=1)


def _audit_verdict(run_path: Path) -> str | None:
    audit_path = run_path / "integrity_audit.md"
    if not audit_path.is_file():
        return None
    match = AUDIT_VERDICT_PATTERN.search(audit_path.read_text(encoding="utf-8"))
    return match.group(1).upper() if match else None


def _render_input_brief(input_path: Path) -> str:
    """Render input_brief.md from an AutoSearch handoff file.

    Accepts either a JSON handoff object or free-form natural-language text. JSON must
    carry the three required handoff fields (motivation, contribution, benchmark); any
    additional keys are preserved verbatim in an extra section so that upstream schema
    drift never silently drops user-supplied input. Natural-language input is passed
    through untouched for the design Skill to normalize.
    """

    raw = input_path.read_text(encoding="utf-8").strip()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return (
            "# Input Brief\n\n"
            "## Handoff source\n\n"
            f"Channel: natural language file `{input_path.name}`\n\n"
            "## Original natural-language input\n\n"
            f"{raw}\n\n"
            "Normalize this into literal Motivation, Contribution, and Benchmark sections "
            "with the autodesign-experiment-design Skill before designing experiments.\n"
        )
    if not isinstance(payload, dict):
        raise TypeError("AutoSearch handoff JSON must contain an object")
    motivation = payload.get("motivation")
    contribution = payload.get("contribution", payload.get("contributions"))
    benchmark = payload.get("benchmark")
    missing = [
        name
        for name, value in (
            ("motivation", motivation),
            ("contribution", contribution),
            ("benchmark", benchmark),
        )
        if value in (None, "", [], {})
    ]
    if missing:
        raise ValueError(f"AutoSearch handoff is missing: {', '.join(missing)}")
    constraints = benchmark.get("constraints", {}) if isinstance(benchmark, dict) else {}
    extra = {
        key: value
        for key, value in payload.items()
        if key
        not in {"schema_version", "motivation", "contribution", "contributions", "benchmark"}
    }
    extra_section = (
        "## Additional user-supplied input\n\n"
        f"```json\n{_json_block(extra)}\n```\n\n"
        if extra
        else ""
    )
    return (
        "# Input Brief\n\n"
        "## Handoff source\n\n"
        f"Channel: AutoSearch handoff file `{input_path.name}`\n\n"
        "## Motivation (literal)\n\n"
        f"{motivation}\n\n"
        "## Contribution (literal)\n\n"
        f"```json\n{_json_block(contribution)}\n```\n\n"
        "## Benchmark (literal)\n\n"
        f"```json\n{_json_block(benchmark)}\n```\n\n"
        f"{extra_section}"
        "## Explicit user locks\n\n"
        f"```json\n{_json_block(constraints)}\n```\n\n"
        "Defaults not present in the original handoff are autonomous design choices, not locks.\n"
    )


def _render_state(run_name: str) -> str:
    return f"""# AutoDesign State

| Field | Value |
| --- | --- |
| Pipeline | AutoDesign design-then-run v2 |
| Run | {run_name} |
| Current stage | INPUT_READY |
| Last completed stage | INPUT_READY |
| Blocking condition | none |
| Next Skill | autodesign-experiment-design |
| Accepted route | pending |
| Execution target | pending |
| Primary result | pending |

## Accepted inputs

- Input brief: `input_brief.md`
- Explicit locks: copied from the AutoSearch handoff only

## Current artifacts

| Artifact | Status | Decision use |
| --- | --- | --- |
| `input_brief.md` | ready | experiment design input |

## History

| Round | From | To | Changed input | Literal result | Next action |
| ---: | --- | --- | --- | --- | --- |
| 0 | new | INPUT_READY | `input_brief.md` | handoff accepted | run experiment design |
"""


def _refresh_state_snapshot(text: str, run_path: Path, stage: str) -> str:
    """Refresh derived state fields without turning Markdown research into a schema."""

    route = (
        "recorded in `experiment_design.md`"
        if (run_path / "experiment_design.md").is_file()
        else "pending"
    )
    execution_target = (
        "`generated_project/` via `command_plan.json`"
        if (run_path / "generated_project").is_dir()
        and (run_path / "command_plan.json").is_file()
        else "pending"
    )
    primary_result = (
        "recorded in `result_summary.json`"
        if (run_path / "result_summary.json").is_file()
        else "pending"
    )
    blocking = {
        "WAITING_FOR_R0": "observed R0 result required",
        "R0_FAILED_RETURN_TO_DESIGN": "experiment design revision required",
        "EXECUTION_IN_PROGRESS": "remaining command stages required",
    }.get(stage, "none")
    replacements = {
        "Blocking condition": blocking,
        "Accepted route": route,
        "Execution target": execution_target,
        "Primary result": primary_result,
    }
    for field, value in replacements.items():
        text = _replace_state_field(text, field, value)
    rows = [
        f"| `{relative}` | {'ready' if (run_path / relative).exists() else 'pending'} | {purpose} |"
        for relative, purpose in STATE_ARTIFACTS
    ]
    artifact_section = (
        "## Current artifacts\n\n"
        "| Artifact | Status | Decision use |\n"
        "| --- | --- | --- |\n"
        + "\n".join(rows)
        + "\n\n"
    )
    return re.sub(
        r"## Current artifacts\n.*?(?=## History)",
        artifact_section,
        text,
        flags=re.DOTALL,
    )


def initialize_skill_run(input_path: str | Path, run_dir: str | Path) -> dict[str, Any]:
    source = Path(input_path)
    run_path = Path(run_dir)
    run_path.mkdir(parents=True, exist_ok=True)
    brief = _render_input_brief(source)
    brief_path = run_path / "input_brief.md"
    state_path = run_path / "AUTODESIGN_STATE.md"
    if brief_path.is_file() and brief_path.read_text(encoding="utf-8") != brief:
        raise ValueError("input_brief.md already exists with different input; use a new run directory")
    write_text(brief_path, brief)
    if not state_path.is_file():
        write_text(state_path, _render_state(run_path.name))
    return inspect_skill_run(run_path)


def read_current_stage(run_dir: str | Path) -> str:
    state_path = Path(run_dir) / "AUTODESIGN_STATE.md"
    if not state_path.is_file():
        raise ValueError("AUTODESIGN_STATE.md is missing; run skill-init first")
    match = STATE_PATTERN.search(state_path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError("AUTODESIGN_STATE.md has no canonical Current stage row")
    stage = match.group(1)
    if stage not in KNOWN_STAGES:
        raise ValueError(f"Unknown Skill-first stage: {stage}")
    return stage


def repair_skill_state(run_dir: str | Path) -> dict[str, Any]:
    """Canonicalize repairable state-table whitespace and refresh derived rows."""

    run_path = Path(run_dir)
    state_path = run_path / "AUTODESIGN_STATE.md"
    stage = read_current_stage(run_path)
    text = state_path.read_text(encoding="utf-8")
    text = _replace_state_field(text, "Current stage", stage)
    text = _replace_state_field(
        text, "Last completed stage", LAST_COMPLETED_STAGE.get(stage, stage)
    )
    text = _replace_state_field(text, "Next Skill", NEXT_SKILL[stage])
    text = _refresh_state_snapshot(text, run_path, stage)
    state_path.write_text(text, encoding="utf-8")
    return inspect_skill_run(run_path)


def inspect_skill_run(run_dir: str | Path) -> dict[str, Any]:
    run_path = Path(run_dir)
    stage = read_current_stage(run_path)
    artifact_status: dict[str, bool] = {}
    milestone = {
        "WAITING_FOR_R0": "EXPERIMENT_DESIGN_READY",
        "R0_PASSED": "EXPERIMENT_DESIGN_READY",
        "R0_FAILED_RETURN_TO_DESIGN": "EXPERIMENT_DESIGN_READY",
        "EXECUTION_IN_PROGRESS": "IMPLEMENTATION_READY",
    }.get(stage, stage)
    for required_stage in STAGE_ORDER[: STAGE_ORDER.index(milestone) + 1]:
        for relative in STAGE_REQUIREMENTS[required_stage]:
            artifact_status[relative] = (run_path / relative).exists()
    for relative in {
        "WAITING_FOR_R0": ("r0_plan.md",),
        "R0_PASSED": ("r0_record.json",),
        "R0_FAILED_RETURN_TO_DESIGN": ("r0_record.json",),
    }.get(stage, ()):
        artifact_status[relative] = (run_path / relative).exists()
    missing = sorted(path for path, exists in artifact_status.items() if not exists)
    return {
        "status": "PASS" if not missing else "INCOMPLETE",
        "run_dir": str(run_path.resolve()),
        "current_stage": stage,
        "next_skill": NEXT_SKILL[stage],
        "artifacts": artifact_status,
        "missing_artifacts": missing,
    }


def advance_skill_run(
    run_dir: str | Path,
    stage: str,
    *,
    changed_input: str,
    literal_result: str,
) -> dict[str, Any]:
    """Advance the human-readable state after target-stage artifacts exist."""

    if stage not in KNOWN_STAGES:
        raise ValueError(f"Unknown Skill-first stage: {stage}")
    run_path = Path(run_dir)
    current = read_current_stage(run_path)
    if stage == "RESULT_DIAGNOSIS_READY":
        summary_path = run_path / "result_summary.json"
        if not summary_path.is_file():
            raise ValueError(
                "RESULT_DIAGNOSIS_READY requires result_summary.json from skill-ingest"
            )
        summary = read_json(summary_path)
        summary_status = summary.get("status") if isinstance(summary, dict) else None
        if summary_status != "READY_FOR_GPT_DIAGNOSIS":
            raise ValueError(
                "RESULT_DIAGNOSIS_READY requires result_summary.json status "
                f"READY_FOR_GPT_DIAGNOSIS; got {summary_status!r}"
            )
    if stage == "COMPLETE" and current != "INTEGRITY_AUDIT_PASS":
        raise ValueError("COMPLETE requires current stage INTEGRITY_AUDIT_PASS")
    if stage in {"INTEGRITY_AUDIT_PASS", "COMPLETE"} and _audit_verdict(run_path) != "PASS":
        raise ValueError(
            f"{stage} requires integrity_audit.md with literal Verdict: PASS"
        )
    state_path = run_path / "AUTODESIGN_STATE.md"
    text = state_path.read_text(encoding="utf-8")
    original_text = text
    text = _replace_state_field(text, "Current stage", stage)
    text = _replace_state_field(
        text, "Last completed stage", LAST_COMPLETED_STAGE.get(stage, stage)
    )
    text = _replace_state_field(text, "Next Skill", NEXT_SKILL[stage])
    text = _refresh_state_snapshot(text, run_path, stage)
    history_rows = re.findall(r"^\s*\|\s*(\d+)\s*\|", text, flags=re.MULTILINE)
    round_index = max((int(value) for value in history_rows), default=0) + 1
    next_action = "pipeline complete" if stage == "COMPLETE" else f"run {NEXT_SKILL[stage]}"
    text = text.rstrip() + (
        f"\n| {round_index} | {current} | {stage} | "
        f"{_markdown_table_cell(changed_input)} | "
        f"{_markdown_table_cell(literal_result)} | {next_action} |\n"
    )
    state_path.write_text(text, encoding="utf-8")
    report = inspect_skill_run(run_path)
    if report["missing_artifacts"]:
        state_path.write_text(original_text, encoding="utf-8")
        raise ValueError(
            "Cannot accept stage with missing artifacts: "
            + ", ".join(report["missing_artifacts"])
        )
    return report
