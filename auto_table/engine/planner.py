from __future__ import annotations

from typing import Any, Iterable

from .model import Aggregate

_LOWER_IS_BETTER = ("loss", "error", "wer", "perplex", "latency", "time", "memory", "flop", "param")


def _ordered(values: Iterable[str], preferred: list[str] | None = None) -> list[str]:
    seen = list(dict.fromkeys(values))
    if not preferred:
        return seen
    return [x for x in preferred if x in seen] + [x for x in seen if x not in preferred]


def _select(values: Iterable[str], requested: list[str] | None, name: str, warnings: list[str]) -> list[str]:
    available = list(dict.fromkeys(values))
    if requested is None:
        return available
    missing = [value for value in requested if value not in available]
    if missing:
        warnings.append(f"requested {name} not found: {', '.join(missing)}")
    return [value for value in requested if value in available]


def _metric_meta(metric: str, config: dict[str, Any], warnings: list[str]) -> dict[str, Any]:
    configured = config.get("metrics", {}).get(metric, {})
    direction = configured.get("direction")
    if direction not in {"max", "min"}:
        direction = "min" if any(token in metric.lower() for token in _LOWER_IS_BETTER) else "max"
        warnings.append(f"metric direction for {metric!r} was inferred as {direction!r}")
    return {
        "key": metric,
        "label": configured.get("label", metric.replace("_", " ").title()),
        "direction": direction,
        "precision": int(configured.get("precision", 2)),
        "unit": configured.get("unit"),
        "priority": int(configured.get("priority", 100)),
        "show_direction": bool(configured.get("show_direction", True)),
    }


def _field_defs(raw: list[Any] | None, default: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not raw:
        return default
    output = []
    for item in raw:
        if isinstance(item, str):
            output.append({"key": item, "label": item.replace("_", " ").title()})
        else:
            output.append({
                "key": item["key"],
                "label": item.get("label", item["key"].replace("_", " ").title()),
                "suppress_repeat": bool(item.get("suppress_repeat", False)),
                "separator": bool(item.get("separator", False)),
            })
    return output


def _values(item: Aggregate) -> dict[str, str | None]:
    return {
        "method": item.method, "group": item.group, "dataset": item.dataset,
        "setting": item.setting, "metric": item.metric, **item.dimensions,
    }


def _entity_key(item: Aggregate, field_defs: list[dict[str, Any]]) -> tuple:
    values = _values(item)
    return (item.method, *(values.get(field["key"]) for field in field_defs))


def _axis_label(axis: str, column: dict[str, Any], metrics: dict[str, Any]) -> str:
    if axis == "metric":
        return metrics[column["metric"]]["label"]
    value = column.get(axis)
    return "" if value is None else str(value)


def _decorate_metric_columns(
    columns: list[dict[str, Any]], column_order: list[str], metrics: dict[str, Any]
) -> list[dict[str, Any]]:
    varying = [axis for axis in column_order if len({column.get(axis) for column in columns}) > 1]
    if not varying:
        varying = ["metric"] if len(metrics) > 1 else [column_order[-1]]
    group_axis = varying[0] if len(varying) > 1 else None
    leaf_axis = varying[-1]
    output = []
    for column in columns:
        decorated = dict(column)
        decorated["group_label"] = _axis_label(group_axis, column, metrics) if group_axis else None
        decorated["label"] = _axis_label(leaf_axis, column, metrics)
        output.append(decorated)
    return output


def _selected_axes(aggregates: list[Aggregate], config: dict[str, Any], warnings: list[str]) -> tuple[list[str], list[str], list[str], list[str | None]]:
    selection = config.get("selection", {})
    if selection.get("methods") is not None:
        methods = _select((x.method for x in aggregates), selection["methods"], "methods", warnings)
    else:
        methods = _ordered((x.method for x in aggregates), config.get("method_order"))
    datasets = _select((x.dataset for x in aggregates), selection.get("datasets"), "datasets", warnings)
    metrics = _select((x.metric for x in aggregates), selection.get("metrics"), "metrics", warnings)
    available_settings = [x.setting for x in aggregates if x.setting is not None]
    settings = _select(available_settings, selection.get("settings"), "settings", warnings)
    return methods, datasets, metrics, settings if settings else [None]


def _apply_column_budget(
    columns: list[dict[str, Any]], config: dict[str, Any], metric_meta: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    max_columns = config.get("selection", {}).get("max_columns")
    if max_columns is None or len(columns) <= int(max_columns):
        return columns, []
    ranked = sorted(
        enumerate(columns),
        key=lambda pair: (metric_meta.get(pair[1].get("metric"), {}).get("priority", 100), pair[0]),
    )
    keep = {index for index, _ in ranked[: int(max_columns)]}
    return (
        [column for index, column in enumerate(columns) if index in keep],
        [column for index, column in enumerate(columns) if index not in keep],
    )


def _row_matches(row: dict[str, Any], selector: dict[str, Any]) -> bool:
    values = {"method": row.get("method"), "group": row.get("group"), **row.get("identity", {})}
    return all(values.get(key) == value for key, value in selector.items())


def _apply_auxiliary_values(
    rows: list[dict[str, Any]], columns: list[dict[str, Any]], config: dict[str, Any],
    orientation: str,
) -> None:
    delta = config.get("auxiliary", {}).get("delta")
    if not delta:
        return
    if orientation != "methods_rows":
        raise ValueError("auxiliary.delta currently requires layout.orientation='methods_rows'")
    baseline_selector = delta.get("baseline")
    target_selectors = delta.get("targets", [])
    if not isinstance(baseline_selector, dict) or not baseline_selector:
        raise ValueError("auxiliary.delta.baseline must be a non-empty identity selector")
    if not target_selectors or not all(isinstance(item, dict) and item for item in target_selectors):
        raise ValueError("auxiliary.delta.targets must contain identity selectors")
    baselines = [row for row in rows if _row_matches(row, baseline_selector)]
    if len(baselines) != 1:
        raise ValueError(f"auxiliary.delta baseline matched {len(baselines)} rows; expected exactly one")
    targets = [row for row in rows if any(_row_matches(row, item) for item in target_selectors)]
    if not targets:
        raise ValueError("auxiliary.delta targets matched no rows")
    kind = delta.get("kind", "absolute")
    if kind not in {"absolute", "relative_percent"}:
        raise ValueError("auxiliary.delta.kind must be 'absolute' or 'relative_percent'")
    precision = int(delta.get("precision", 2))
    baseline = baselines[0]
    for target in targets:
        for column_index, _ in enumerate(columns):
            target_cell = target["cells"][column_index]
            baseline_cell = baseline["cells"][column_index]
            if target_cell is None or baseline_cell is None:
                continue
            difference = target_cell["mean"] - baseline_cell["mean"]
            if kind == "relative_percent":
                if baseline_cell["mean"] == 0:
                    continue
                difference = difference / abs(baseline_cell["mean"]) * 100
            target_cell["auxiliary"] = {
                "kind": kind,
                "value": difference,
                "precision": precision,
                "baseline": baseline.get("method"),
            }


def _plan_methods_rows(
    aggregates: list[Aggregate], methods: list[str], datasets: list[str], metrics: list[str],
    settings: list[str | None], metric_meta: dict[str, Any], config: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    layout = config.get("layout", {})
    identity_columns = _field_defs(layout.get("row_fields"), [{"key": "method", "label": "Method"}])
    if not any(field["key"] == "method" for field in identity_columns):
        identity_columns.append({"key": "method", "label": "Method"})
    filtered = [x for x in aggregates if x.method in methods and x.dataset in datasets and x.metric in metrics and x.setting in settings]
    entities: dict[tuple, Aggregate] = {}
    for item in filtered:
        entities.setdefault(_entity_key(item, identity_columns), item)
    method_rank = {method: index for index, method in enumerate(methods)}
    separator_fields = [field["key"] for field in identity_columns if field.get("separator")]
    separator_ranks: dict[str, dict[str | None, int]] = {}
    for field in separator_fields:
        ordered_values = list(dict.fromkeys(_values(item).get(field) for item in filtered))
        separator_ranks[field] = {value: index for index, value in enumerate(ordered_values)}

    entity_items = sorted(
        entities.items(),
        key=lambda pair: (
            *(separator_ranks[field].get(_values(pair[1]).get(field), 10**6) for field in separator_fields),
            method_rank.get(pair[1].method, 10**6),
        ),
    )

    available = {(x.dataset, x.setting, x.metric) for x in filtered}
    raw_columns = [
        {"dataset": dataset, "setting": setting, "metric": metric}
        for dataset in datasets for setting in settings for metric in metrics
        if (dataset, setting, metric) in available
    ]
    raw_columns, omitted = _apply_column_budget(raw_columns, config, metric_meta)
    columns = _decorate_metric_columns(raw_columns, layout.get("column_order", ["dataset", "metric"]), metric_meta)
    cell_map = {}
    for item in filtered:
        key = (_entity_key(item, identity_columns), item.dataset, item.setting, item.metric)
        if key in cell_map:
            raise ValueError(
                "multiple aggregates collapse into one table cell; add the differing "
                "identity/protocol field to layout.row_fields"
            )
        cell_map[key] = item.to_dict()
    rows = []
    for entity, item in entity_items:
        values = _values(item)
        rows.append({
            "method": item.method,
            "group": item.group,
            "identity": {field["key"]: values.get(field["key"]) for field in identity_columns},
            "cells": [cell_map.get((entity, c["dataset"], c["setting"], c["metric"])) for c in columns],
        })
    return identity_columns, columns, rows, omitted


def _plan_datasets_rows(
    aggregates: list[Aggregate], methods: list[str], datasets: list[str], metrics: list[str],
    settings: list[str | None], metric_meta: dict[str, Any], config: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    layout = config.get("layout", {})
    entity_fields = _field_defs(layout.get("column_fields"), [{"key": "method", "label": "Method"}])
    group_field = layout.get("column_group_field")
    entity_key_fields = list(entity_fields)
    if group_field and not any(field["key"] == group_field for field in entity_key_fields):
        entity_key_fields.append({"key": group_field, "label": group_field})
    filtered = [x for x in aggregates if x.method in methods and x.dataset in datasets and x.metric in metrics and x.setting in settings]
    entities: dict[tuple, Aggregate] = {}
    for item in filtered:
        entities.setdefault(_entity_key(item, entity_key_fields), item)
    method_rank = {method: index for index, method in enumerate(methods)}
    group_rank = {
        value: index
        for index, value in enumerate(
            dict.fromkeys(_values(item).get(group_field) for item in filtered)
        )
    } if group_field else {}
    entity_items = sorted(
        entities.items(),
        key=lambda pair: (
            group_rank.get(_values(pair[1]).get(group_field), 10**6),
            method_rank.get(pair[1].method, 10**6),
        ),
    )
    columns = []
    for entity, item in entity_items:
        values = _values(item)
        label_parts = [str(values.get(field["key"])) for field in entity_fields if values.get(field["key"]) not in (None, "")]
        columns.append({
            "method": item.method, "entity_key": entity,
            "label": " / ".join(label_parts) or item.method,
            "group_label": str(values.get(group_field)) if group_field and values.get(group_field) else None,
        })
    columns, omitted = _apply_column_budget(columns, config, metric_meta)
    row_defaults = [{"key": "dataset", "label": "Benchmark"}]
    if len(metrics) > 1:
        row_defaults.append({"key": "metric", "label": "Metric"})
    identity_columns = _field_defs(layout.get("row_fields"), row_defaults)
    available_rows = {(x.dataset, x.setting, x.metric) for x in filtered}
    row_combos = [
        (dataset, setting, metric) for dataset in datasets for setting in settings for metric in metrics
        if (dataset, setting, metric) in available_rows
    ]
    cell_map = {}
    for item in filtered:
        key = (_entity_key(item, entity_key_fields), item.dataset, item.setting, item.metric)
        if key in cell_map:
            raise ValueError(
                "multiple aggregates collapse into one table cell; add the differing "
                "identity/protocol field to layout.column_fields or column_group_field"
            )
        cell_map[key] = item.to_dict()
    rows = []
    for dataset, setting, metric in row_combos:
        identity_values = {"dataset": dataset, "setting": setting, "metric": metric_meta[metric]["label"]}
        rows.append({
            "dataset": dataset, "setting": setting, "metric": metric, "group": setting,
            "identity": {field["key"]: identity_values.get(field["key"]) for field in identity_columns},
            "cells": [cell_map.get((c["entity_key"], dataset, setting, metric)) for c in columns],
        })
    for column in columns:
        column.pop("entity_key", None)
    return identity_columns, columns, rows, omitted


def plan_main_table(aggregates: list[Aggregate], config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or {}
    warnings: list[str] = []
    methods, datasets, metrics, settings = _selected_axes(aggregates, config, warnings)
    metric_meta = {metric: _metric_meta(metric, config, warnings) for metric in metrics}
    orientation = config.get("layout", {}).get("orientation", "methods_rows")
    if orientation == "methods_rows":
        identity_columns, columns, rows, omitted = _plan_methods_rows(
            aggregates, methods, datasets, metrics, settings, metric_meta, config
        )
    elif orientation == "datasets_rows":
        identity_columns, columns, rows, omitted = _plan_datasets_rows(
            aggregates, methods, datasets, metrics, settings, metric_meta, config
        )
    else:
        raise ValueError(f"unsupported layout.orientation: {orientation}")
    _apply_auxiliary_values(rows, columns, config, orientation)
    if omitted:
        warnings.append(f"{len(omitted)} columns were omitted by selection.max_columns")
    style = dict(config.get("style", {}))
    focal_methods = list(config.get("focal_methods", style.get("highlight_methods", [])))
    if orientation == "methods_rows" and focal_methods and not style.get("highlight_methods"):
        style["highlight_methods"] = focal_methods
    spec = {
        "schema_version": "paper-table-spec-v5", "template_id": config.get("template_id", "custom"),
        "kind": "main", "table_type": config.get("table_type", "unclassified"),
        "orientation": orientation, "title": config.get("title", "Main results"),
        "label": config.get("label", "tab:main-results"), "claim": config.get("claim"),
        "methods": methods, "datasets": datasets, "metrics": metric_meta,
        "identity_columns": identity_columns, "columns": columns, "rows": rows,
        "emphasis": config.get("emphasis", {"best": "bold", "second": "underline"}),
        "comparison": config.get("comparison", {}), "style": style,
        "focal_methods": focal_methods,
        "auxiliary": config.get("auxiliary", {}),
        "caption": config.get("caption"),
        "description": config.get("description"),
        "context_notes": list(config.get("context_notes", config.get("notes", []))),
        "omitted_columns": omitted, "warnings": warnings,
    }
    ranking_entities = rows if orientation == "methods_rows" else columns
    if spec["emphasis"].get("best") and not any(_rank_eligible(entity, spec) for entity in ranking_entities):
        raise ValueError("comparison ranking scope selects no displayed systems")
    return spec


def emphasis_map(spec: dict[str, Any]) -> dict[tuple[int, int], str]:
    output: dict[tuple[int, int], str] = {}
    if spec["orientation"] == "methods_rows":
        for column_index, column in enumerate(spec["columns"]):
            values = [(row_index, row["cells"][column_index]["mean"])
                      for row_index, row in enumerate(spec["rows"])
                      if row["cells"][column_index] is not None and _rank_eligible(row, spec)]
            direction = spec["metrics"][column["metric"]]["direction"]
            _mark_distinct(output, values, direction, spec, lambda index: (index, column_index))
    else:
        for row_index, row in enumerate(spec["rows"]):
            values = [
                (column_index, cell["mean"])
                for column_index, cell in enumerate(row["cells"])
                if cell is not None and _rank_eligible(spec["columns"][column_index], spec)
            ]
            direction = spec["metrics"][row["metric"]]["direction"]
            _mark_distinct(output, values, direction, spec, lambda index: (row_index, index))
    return output


def _rank_eligible(entity: dict[str, Any], spec: dict[str, Any]) -> bool:
    comparison = spec.get("comparison", {})
    group = entity.get("group") or entity.get("group_label")
    method = entity.get("method")
    include_groups = comparison.get("rank_include_groups")
    exclude_groups = comparison.get("rank_exclude_groups", [])
    include_methods = comparison.get("rank_include_methods")
    exclude_methods = comparison.get("rank_exclude_methods", [])
    if include_groups is not None and group not in include_groups:
        return False
    if group in exclude_groups:
        return False
    if include_methods is not None and method not in include_methods:
        return False
    return method not in exclude_methods


def _mark_distinct(
    output: dict[tuple[int, int], str], values: list[tuple[int, float]], direction: str,
    spec: dict[str, Any], key_builder: Any,
) -> None:
    distinct = sorted({value for _, value in values}, reverse=direction == "max")
    if distinct and spec.get("emphasis", {}).get("best"):
        for index, value in values:
            if value == distinct[0]:
                output[key_builder(index)] = spec["emphasis"]["best"]
    if len(distinct) > 1 and spec.get("emphasis", {}).get("second"):
        for index, value in values:
            if value == distinct[1]:
                output[key_builder(index)] = spec["emphasis"]["second"]
