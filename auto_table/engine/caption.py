from __future__ import annotations

from typing import Any


def build_caption(spec: dict[str, Any]) -> str:
    """Return one identifying sentence; experimental detail belongs in the paper body."""
    caption = str(spec.get("caption") or spec.get("title") or "Results").strip()
    if caption and caption[-1] not in ".!?":
        caption += "."
    return caption


def build_description(spec: dict[str, Any]) -> str:
    """Return a standalone explanation of the table's content and paper role."""
    configured = str(spec.get("description") or "").strip()
    if configured:
        return configured

    system_count = len(spec.get("rows", [])) if spec.get("orientation") == "methods_rows" else len(spec.get("columns", []))
    datasets = [str(item) for item in spec.get("datasets", [])]
    metric_labels = [str(item.get("label", key)) for key, item in spec.get("metrics", {}).items()]
    dataset_text = ", ".join(datasets) if datasets else "the selected evaluation scope"
    metric_text = ", ".join(metric_labels) if metric_labels else "the reported metrics"
    title = str(spec.get("title") or "the reported results").strip()
    return (
        f"This table compares {system_count} displayed systems across {dataset_text} using {metric_text}. "
        f"Its purpose is to provide the quantitative evidence summarized by {title}."
    )
