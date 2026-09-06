from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

from .model import Observation, ReportedSummary

_IDENTITY_KEYS = {
    "method", "model", "system", "approach", "dataset", "benchmark", "task",
    "setting", "split", "seed", "run", "run_id", "fold", "group", "family",
    "metric", "value", "mean", "sd", "std", "sample_sd", "source", "epoch", "step", "n", "backbone",
    "pretrain_data", "training_data", "trainable_params", "params", "depth",
    "regime", "protocol", "source_type", "extra_data",
}
_METHOD_KEYS = ("method", "model", "system", "approach")
_DATASET_KEYS = ("dataset", "benchmark", "task")
_RUN_KEYS = ("run", "run_id", "seed", "fold")
_DESCRIPTOR_KEYS = (
    "model", "backbone", "pretrain_data", "training_data", "trainable_params",
    "params", "depth", "regime", "protocol", "source_type", "extra_data",
)


class InputError(ValueError):
    pass


def _first(row: dict[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return default


def _first_item(row: dict[str, Any], keys: Iterable[str]) -> tuple[str, Any] | None:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return key, row[key]
    return None


def _number(value: Any, *, field: str) -> float:
    if isinstance(value, bool):
        raise InputError(f"{field} must be numeric, not boolean")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise InputError(f"{field}={value!r} is not numeric") from exc


def _read(path: Path) -> Any:
    suffix = path.suffix.lower()
    if suffix in {".csv", ".tsv"}:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            return list(csv.DictReader(handle, delimiter="\t" if suffix == ".tsv" else ","))
    if suffix == ".jsonl":
        with path.open(encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]
    if suffix == ".json":
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    raise InputError(f"unsupported input type: {path}; use CSV, TSV, JSON, or JSONL")


def _row_observations(
    rows: list[dict[str, Any]], source: str, config: dict[str, Any]
) -> list[Observation | ReportedSummary]:
    metric_keys = config.get("input", {}).get("metric_columns")
    layout = config.get("layout", {})
    field_defs = list(layout.get("row_fields", [])) + list(layout.get("column_fields", []))
    field_keys = [item if isinstance(item, str) else item["key"] for item in field_defs]
    if layout.get("column_group_field"):
        field_keys.append(layout["column_group_field"])
    field_keys += list(config.get("input", {}).get("dimensions", []))
    observations: list[Observation | ReportedSummary] = []
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise InputError(f"{source}: row {index} is not an object")
        configured_method_field = config.get("input", {}).get("method_field")
        if configured_method_field:
            method_item = _first_item(row, (str(configured_method_field),))
            if method_item is None:
                raise InputError(
                    f"{source}: row {index} has no value in configured method field "
                    f"{configured_method_field!r}"
                )
        else:
            method_item = _first_item(row, _METHOD_KEYS)
        if method_item is None:
            raise InputError(f"{source}: row {index} has no method/model/system/approach field")
        method_source_field, method = method_item
        dimensions = {
            key: str(row[key]) for key in dict.fromkeys((*_DESCRIPTOR_KEYS, *field_keys))
            if key != "method" and row.get(key) not in (None, "")
            and not (key == "model" and "method" not in row)
        }
        run = str(_first(row, _RUN_KEYS)) if _first(row, _RUN_KEYS) is not None else None
        common = {
            "method": str(method),
            "method_source_field": method_source_field,
            "dataset": str(_first(row, _DATASET_KEYS, "Overall")),
            "setting": str(row["setting"]) if row.get("setting") not in (None, "") else None,
            "group": str(_first(row, ("group", "family"))) if _first(row, ("group", "family")) is not None else None,
            "source": source,
            "dimensions": dimensions,
        }
        # Long format: one metric/value pair per row.
        if row.get("metric") not in (None, "") and _first(row, ("value", "score")) is not None:
            if row.get("mean") not in (None, ""):
                raise InputError(f"{source}: row {index} cannot contain both value and mean")
            observations.append(Observation(
                metric=str(row["metric"]),
                value=_number(_first(row, ("value", "score")), field=f"{source}:{index}.value"),
                run=run,
                **common,
            ))
            continue

        # Pre-aggregated long format: preserve reported mean/SD/n without inventing runs.
        if row.get("metric") not in (None, "") and row.get("mean") not in (None, ""):
            if run is not None:
                raise InputError(f"{source}: row {index} reported summary cannot also declare a run ID")
            raw_n = row.get("n", 1)
            numeric_n = _number(raw_n, field=f"{source}:{index}.n")
            if numeric_n < 1 or not numeric_n.is_integer():
                raise InputError(f"{source}:{index}.n must be a positive integer")
            raw_sd = _first(row, ("sd", "std", "sample_sd"))
            sd = _number(raw_sd, field=f"{source}:{index}.sd") if raw_sd is not None else None
            if sd is not None and sd < 0:
                raise InputError(f"{source}:{index}.sd must be non-negative")
            if sd is not None and int(numeric_n) < 2:
                raise InputError(f"{source}:{index}.sd requires n >= 2")
            observations.append(ReportedSummary(
                metric=str(row["metric"]),
                mean=_number(row["mean"], field=f"{source}:{index}.mean"),
                sd=sd,
                n=int(numeric_n),
                **common,
            ))
            continue

        # Wide format: every selected numeric column is a metric.
        candidates = metric_keys or [
            key for key, value in row.items()
            if key.lower() not in _IDENTITY_KEYS and value not in (None, "")
            and _looks_numeric(value)
        ]
        if not candidates:
            raise InputError(
                f"{source}: row {index} has no metric columns; set input.metric_columns in config"
            )
        for metric in candidates:
            if metric not in row or row[metric] in (None, ""):
                continue
            observations.append(Observation(
                metric=str(metric),
                value=_number(row[metric], field=f"{source}:{index}.{metric}"),
                run=run,
                **common,
            ))
    return observations


def _looks_numeric(value: Any) -> bool:
    try:
        float(value)
        return not isinstance(value, bool)
    except (TypeError, ValueError):
        return False


def _nested_observations(data: dict[str, Any], source: str) -> list[Observation]:
    """Parse method -> dataset -> metric -> scalar/list JSON."""
    observations: list[Observation] = []
    for method, datasets in data.items():
        if not isinstance(datasets, dict):
            raise InputError(f"{source}: expected object below method {method!r}")
        for dataset, metrics in datasets.items():
            if not isinstance(metrics, dict):
                raise InputError(f"{source}: expected object below dataset {dataset!r}")
            for metric, value in metrics.items():
                values = value if isinstance(value, list) else [value]
                for run_index, item in enumerate(values, 1):
                    observations.append(Observation(
                        method=str(method), method_source_field="json_object_key",
                        dataset=str(dataset), metric=str(metric),
                        value=_number(item, field=f"{source}.{method}.{dataset}.{metric}"),
                        run=str(run_index) if isinstance(value, list) else None,
                        source=source,
                    ))
    return observations


def load_inputs(
    paths: list[str | Path], config: dict[str, Any] | None = None
) -> list[Observation | ReportedSummary]:
    config = config or {}
    all_observations: list[Observation | ReportedSummary] = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.is_file():
            raise InputError(f"input does not exist: {path}")
        data = _read(path)
        source = str(path)
        if isinstance(data, dict) and isinstance(data.get("results"), list):
            data = data["results"]
        if isinstance(data, list):
            all_observations.extend(_row_observations(data, source, config))
        elif isinstance(data, dict):
            all_observations.extend(_nested_observations(data, source))
        else:
            raise InputError(f"{source}: root must be an array or object")
    if not all_observations:
        raise InputError("no observations found")
    return all_observations
