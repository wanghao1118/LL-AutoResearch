from __future__ import annotations

import math
from typing import Any


def verify_spec(spec: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    columns = spec.get("columns", [])
    rows = spec.get("rows", [])
    if not columns:
        errors.append("table has no columns")
    if not rows:
        errors.append("table has no rows")
    table_type = spec.get("table_type", "unclassified")
    focal_methods = set(spec.get("focal_methods", []))
    displayed_methods = set(spec.get("methods", []))
    if not focal_methods.issubset(displayed_methods):
        errors.append("focal_methods contains a method that is not displayed")
    if table_type in {"main_benchmark", "main_tradeoff"}:
        if not focal_methods:
            errors.append(f"{table_type} requires at least one focal method")
        if displayed_methods and not (displayed_methods - focal_methods):
            errors.append(f"{table_type} requires at least one non-focal baseline")
    if table_type == "main_benchmark":
        datasets = list(spec.get("datasets", []))
        if len(datasets) < 2:
            errors.append("main_benchmark requires at least two displayed benchmarks")
        if focal_methods and displayed_methods - focal_methods:
            for dataset in datasets:
                focal_evidence = False
                baseline_evidence = False
                for row in rows:
                    for column_index, cell in enumerate(row.get("cells", [])):
                        if cell is None:
                            continue
                        column = columns[column_index]
                        cell_dataset = row.get("dataset") if spec.get("orientation") == "datasets_rows" else column.get("dataset")
                        if cell_dataset != dataset:
                            continue
                        method = cell.get("method")
                        focal_evidence = focal_evidence or method in focal_methods
                        baseline_evidence = baseline_evidence or method in (displayed_methods - focal_methods)
                if not focal_evidence or not baseline_evidence:
                    errors.append(
                        f"main_benchmark dataset {dataset!r} lacks a direct focal-versus-baseline comparison"
                    )
    for row_index, row in enumerate(rows):
        cells = row.get("cells", [])
        if len(cells) != len(columns):
            errors.append(f"row {row_index} has {len(cells)} cells for {len(columns)} columns")
            continue
        for column_index, cell in enumerate(cells):
            if cell is None:
                continue
            if cell.get("n", 0) < 1:
                errors.append(f"cell {row_index},{column_index} has invalid n")
            for field in ("mean", "sd"):
                value = cell.get(field)
                if value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value)):
                    errors.append(f"cell {row_index},{column_index} has non-finite {field}")
            aggregation_source = cell.get("aggregation_source", "observations")
            if aggregation_source == "observations":
                if len(cell.get("values", [])) != cell.get("n"):
                    errors.append(f"cell {row_index},{column_index} loses value lineage")
            elif aggregation_source == "reported_summary":
                if cell.get("values") or cell.get("run_ids") or not cell.get("sources"):
                    errors.append(f"cell {row_index},{column_index} has invalid summary lineage")
                if cell.get("sd") is not None and cell.get("n", 0) < 2:
                    errors.append(f"cell {row_index},{column_index} reports SD with n < 2")
            else:
                errors.append(f"cell {row_index},{column_index} has invalid aggregation source")
            auxiliary = cell.get("auxiliary")
            if auxiliary:
                if auxiliary.get("kind") not in {"absolute", "relative_percent"}:
                    errors.append(f"cell {row_index},{column_index} has invalid auxiliary kind")
                value = auxiliary.get("value")
                if not isinstance(value, (int, float)) or not math.isfinite(value):
                    errors.append(f"cell {row_index},{column_index} has invalid auxiliary value")
            column = columns[column_index]
            if spec.get("orientation") == "datasets_rows":
                matches = (
                    cell.get("method") == column.get("method")
                    and cell.get("metric") == row.get("metric")
                    and cell.get("dataset") == row.get("dataset")
                )
            else:
                matches = cell.get("method") == row.get("method") and cell.get("metric") == column.get("metric")
            if not matches:
                errors.append(f"cell {row_index},{column_index} does not match its row/column")
    return {"valid": not errors, "errors": errors}
