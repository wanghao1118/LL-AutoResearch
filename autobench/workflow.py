"""Single-command orchestration for matching, synthesis, and automatic QA."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .models import MethodInput
from .pipeline import AutoBenchPipeline
from .synthesis_agent import synthesize_records, verify_synthetic_records


SYNTHESIS_TRANSFORMATIONS = (
    "interaction_wrapper",
    "compositional_recombination",
    "counterfactual_perturbation",
)


def _portable_path(path: str | Path) -> str:
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return Path(path).name


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    records = [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not records:
        raise ValueError("base-record JSONL must contain at least one record")
    return records


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def _execute_synthesis(
    plan_route: str,
    synthesis_plan: dict[str, Any],
    output_dir: Path,
    *,
    base_records_path: str | Path | None,
    source_benchmark: str | None,
    source_split: str | None,
    transformations: Iterable[str] | None,
) -> dict[str, Any]:
    """Execute requested synthesis modules or emit an explicit input request."""

    if not synthesis_plan["required"]:
        return {
            "status": "NOT_REQUIRED",
            "route": plan_route,
            "reason": "the selected portfolio covers every inferred task family",
            "modules": [],
        }

    chosen = list(dict.fromkeys(transformations or ("interaction_wrapper",)))
    unknown = sorted(set(chosen) - set(SYNTHESIS_TRANSFORMATIONS))
    if unknown:
        raise ValueError(f"unknown synthesis transformations: {unknown}")

    synthesis_root = output_dir / "synthesis"
    if base_records_path is None:
        request = {
            "status": "BASE_RECORDS_REQUIRED",
            "route": plan_route,
            "target_task_families": synthesis_plan["target_task_families"],
            "construct_definition": synthesis_plan["construct_definition"],
            "required_record_fields": ["id", "input", "expected_output"],
            "optional_counterfactual_fields": ["input", "expected_output", "deterministic_check"],
            "allowed_source_splits": ["train", "training", "dev", "development", "validation"],
            "planned_transformations": chosen,
            "source_policy": synthesis_plan["source_policy"],
        }
        request_path = synthesis_root / "synthesis_request.json"
        _write_json(request_path, request)
        return {**request, "request": _portable_path(request_path), "modules": []}

    if not source_benchmark or not source_split:
        raise ValueError("source_benchmark and source_split are required with base_records")
    base_records = _read_jsonl(base_records_path)
    modules: list[dict[str, Any]] = []
    for transformation in chosen:
        drafts = synthesize_records(
            base_records,
            source_benchmark=source_benchmark,
            source_split=source_split,
            transformation=transformation,
        )
        if not drafts:
            raise ValueError(f"{transformation} produced no draft records")
        verification = verify_synthetic_records(
            base_records,
            drafts,
            source_benchmark,
            source_split,
            transformation,
        )
        draft_path = synthesis_root / f"{transformation}.jsonl"
        verification_path = synthesis_root / f"{transformation}.verification.json"
        _write_jsonl(draft_path, drafts)
        _write_json(verification_path, verification)
        modules.append(
            {
                "transformation": transformation,
                "records": len(drafts),
                "drafts": _portable_path(draft_path),
                "verification": _portable_path(verification_path),
                "verification_status": verification["status"],
            }
        )
    return {
        "status": "DRAFTS_READY_FOR_AUTOMATIC_VALIDATION",
        "route": plan_route,
        "source_benchmark": source_benchmark,
        "source_split": source_split,
        "base_records": _portable_path(base_records_path),
        "base_record_count": len(base_records),
        "target_task_families": synthesis_plan["target_task_families"],
        "construct_definition": synthesis_plan["construct_definition"],
        "modules": modules,
    }


def run_workflow(
    method_input: MethodInput,
    catalog_path: str | Path,
    output_dir: str | Path,
    *,
    online_search: bool = False,
    base_records_path: str | Path | None = None,
    source_benchmark: str | None = None,
    source_split: str | None = None,
    transformations: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Run method-only matching through synthesis and automatic QA setup.

    The matcher receives only the typed Introduction/Method input. The route
    then determines whether synthesis is skipped, executed from named source
    records, or left as an explicit data-input request. Every completed run
    writes deterministic verification sidecars and an automatic literature-
    comparison contract. No user review submission is created.
    """

    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    pipeline = AutoBenchPipeline(catalog_path)
    plan = pipeline.run(method_input, online_search=online_search)
    execution = _execute_synthesis(
        plan.route,
        plan.synthesis_plan,
        root,
        base_records_path=base_records_path,
        source_benchmark=source_benchmark,
        source_split=source_split,
        transformations=transformations,
    )
    plan.synthesis_plan["execution"] = execution
    plan_paths = pipeline.write_outputs(plan, root)
    workflow_status = (
        "BASE_RECORDS_REQUIRED"
        if execution["status"] == "BASE_RECORDS_REQUIRED"
        else "AUTOMATIC_LITERATURE_CHECK_PENDING"
    )
    automatic_validation = {
        "status": "AUTOMATIC_LITERATURE_CHECK_PENDING",
        "human_submission_required": False,
        "input": _portable_path(plan_paths["automatic_review_input"]),
        "synthesis_verifications": [
            module["verification"]
            for module in execution.get("modules", [])
            if module.get("verification_status") == "PASS"
        ],
        "next_step": (
            "after the blind matcher exits, load source-paper benchmark evidence and run "
            "the automatic literature evaluator"
        ),
    }
    manifest = {
        "schema_version": 1,
        "case_id": plan.case_id,
        "status": workflow_status,
        "route": plan.route,
        "coverage_ratio": plan.coverage_ratio,
        "blind_input_fields": ["introduction", "method", "constraints"],
        "blind_gold_loaded": False,
        "leakage_scan_passed": plan.provenance["leakage_scan"]["passed"],
        "outputs": {name: _portable_path(path) for name, path in plan_paths.items()},
        "synthesis_execution": execution,
        "automatic_validation": automatic_validation,
        "human_submission_required": False,
        "next_action": (
            "provide named train/development base records, then rerun"
            if execution["status"] == "BASE_RECORDS_REQUIRED"
            else "run automatic post-match source comparison and feed its typed errors into optimization"
        ),
    }
    manifest_path = root / "workflow_manifest.json"
    _write_json(manifest_path, manifest)
    return {**manifest, "manifest": _portable_path(manifest_path)}
