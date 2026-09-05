"""Deterministic cell completeness for prompt-driven AutoDesign observations."""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from .io import read_json, write_json
from .runner import execution_completion_errors


def _cell_key(record: dict[str, Any]) -> tuple[str, str, str, int] | None:
    seed = record.get("seed")
    if not isinstance(seed, int) or isinstance(seed, bool):
        return None
    return (
        str(record.get("experiment_id") or ""),
        str(record.get("variant_id") or ""),
        str(record.get("benchmark_task_id") or ""),
        seed,
    )


def summarize_results(
    results: Any, schedule: Any, execution_errors: list[str] | None = None
) -> dict[str, Any]:
    errors = list(execution_errors or [])
    if not isinstance(schedule, dict) or schedule.get("schema_version") != "1.0":
        return {"status": "INCOMPLETE", "errors": [*errors, "invalid experiment schedule"]}
    scheduled = schedule.get("cells")
    if not isinstance(scheduled, list) or not scheduled:
        return {"status": "INCOMPLETE", "errors": [*errors, "schedule.cells must be non-empty"]}

    expected: dict[tuple[str, str, str, int], set[str]] = {}
    for index, cell in enumerate(scheduled):
        if not isinstance(cell, dict):
            errors.append(f"schedule.cells[{index}] must be an object")
            continue
        key = _cell_key(cell)
        metrics = cell.get("metrics")
        if key is None or not all(key[:3]):
            errors.append(f"schedule.cells[{index}] has an invalid cell key")
            continue
        if (
            not isinstance(metrics, list)
            or not metrics
            or not all(isinstance(metric, str) and metric.strip() for metric in metrics)
        ):
            errors.append(f"schedule.cells[{index}].metrics must be non-empty strings")
            continue
        if key in expected:
            errors.append(f"Duplicate scheduled cell: {key}")
            continue
        expected[key] = set(metrics)

    runs = results.get("runs") if isinstance(results, dict) else None
    if not isinstance(results, dict) or results.get("schema_version") != "1.0":
        errors.append("results.schema_version must be 1.0")
    if not isinstance(runs, list) or not runs:
        errors.append("results.runs must be a non-empty list")
        runs = []

    observed: set[tuple[str, str, str, int]] = set()
    values: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)
    for index, run in enumerate(runs):
        if not isinstance(run, dict):
            errors.append(f"runs[{index}] must be an object")
            continue
        key = _cell_key(run)
        if key is None or not all(key[:3]):
            errors.append(f"runs[{index}] has an invalid cell key")
            continue
        if key in observed:
            errors.append(f"Duplicate observed cell: {key}")
            continue
        if run.get("status") != "completed":
            errors.append(f"runs[{index}] status is not completed")
            continue
        metrics = run.get("metrics")
        if not isinstance(metrics, dict) or not metrics:
            errors.append(f"runs[{index}].metrics must be a non-empty object")
            continue
        if key not in expected:
            errors.append(f"Unexpected observed cell: {key}")
            observed.add(key)
            continue
        expected_metrics = expected[key]
        actual_metrics = set(metrics)
        if actual_metrics != expected_metrics:
            missing = sorted(expected_metrics - actual_metrics)
            unexpected = sorted(actual_metrics - expected_metrics)
            if missing:
                errors.append(f"runs[{index}] missing planned metrics: {missing}")
            if unexpected:
                errors.append(f"runs[{index}] has unplanned metrics: {unexpected}")
            continue
        valid = True
        for metric, value in metrics.items():
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(value)
            ):
                errors.append(f"runs[{index}] metric {metric} must be a finite number")
                valid = False
        if not valid:
            continue
        observed.add(key)
        for metric, value in metrics.items():
            values[(key[0], key[1], key[2], metric)].append(float(value))

    missing_cells = sorted(set(expected) - observed)
    unexpected_cells = sorted(observed - set(expected))
    if missing_cells:
        errors.append(f"Missing scheduled result cells: {missing_cells}")
    aggregates = []
    for key, metric_values in sorted(values.items()):
        aggregates.append(
            {
                "experiment_id": key[0],
                "variant_id": key[1],
                "benchmark_task_id": key[2],
                "metric": key[3],
                "n": len(metric_values),
                "mean": statistics.fmean(metric_values),
                "sample_std": statistics.stdev(metric_values) if len(metric_values) > 1 else 0.0,
                "min": min(metric_values),
                "max": max(metric_values),
                "values": metric_values,
            }
        )
    return {
        "status": "READY_FOR_GPT_DIAGNOSIS" if not errors else "INCOMPLETE",
        "expected_cell_count": len(expected),
        "observed_cell_count": len(observed & set(expected)),
        "missing_cells": missing_cells,
        "unexpected_cells": unexpected_cells,
        "aggregate_count": len(aggregates),
        "aggregates": aggregates,
        "errors": errors,
        "automatic_claim_verdict": "NOT_ASSIGNED",
    }


def ingest_results(run_dir: str | Path, results_path: str | Path) -> dict[str, Any]:
    run_path = Path(run_dir)
    required = (
        (
            run_path / "experiment_schedule.json",
            "run stage",
        ),
        (run_path / "command_plan.json", "run stage"),
        (run_path / "execution_record.json", "run stage"),
        (Path(results_path), "run stage or remote collect"),
    )
    for path, owner in required:
        if not path.is_file():
            raise ValueError(f"required artifact is missing: {path}; produce it with {owner}")
    schedule = read_json(run_path / "experiment_schedule.json")
    results = read_json(results_path)
    execution = read_json(run_path / "execution_record.json")
    command_plan = read_json(run_path / "command_plan.json")
    summary = summarize_results(
        results,
        schedule,
        execution_completion_errors(execution, command_plan),
    )
    write_json(run_path / "raw_results.json", results)
    write_json(run_path / "result_summary.json", summary)
    return summary
