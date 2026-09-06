from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .aggregate import aggregate
from .caption import build_caption, build_description
from .ingest import load_inputs
from .model import Observation, ReportedSummary
from .planner import plan_main_table
from .render import render_html, render_latex, render_preview_document
from .templates import resolve_config
from .verify import verify_spec


def _dump(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def generate(
    inputs: list[str | Path], output_dir: str | Path, config: dict[str, Any] | None = None,
    template: str | None = None,
) -> dict[str, Any]:
    config = resolve_config(config, template)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    observations = load_inputs(inputs, config)
    aggregates = aggregate(observations)
    spec = plan_main_table(aggregates, config)
    caption = build_caption(spec)
    spec["caption"] = caption
    description = build_description(spec)
    spec["description"] = description
    verification = verify_spec(spec)
    if not verification["valid"]:
        raise ValueError("invalid table spec: " + "; ".join(verification["errors"]))

    _dump(output / "observations.json", [item.to_dict() for item in observations])
    _dump(output / "aggregates.json", [item.to_dict() for item in aggregates])
    _dump(output / "table-spec.json", spec)
    (output / "caption.txt").write_text(caption + "\n", encoding="utf-8")
    (output / "description.txt").write_text(description + "\n", encoding="utf-8")
    latex = render_latex(spec, caption)
    html = render_html(spec, caption)
    (output / "table.tex").write_text(latex, encoding="utf-8")
    (output / "table.html").write_text(html, encoding="utf-8")
    (output / "preview.tex").write_text(render_preview_document(), encoding="utf-8")

    planned = sum(cell is not None for row in spec["rows"] for cell in row["cells"])
    method_identity = []
    for method in dict.fromkeys(item.method for item in observations):
        matching = [item for item in observations if item.method == method]
        method_identity.append({
            "method": method,
            "input_fields": list(dict.fromkeys(item.method_source_field for item in matching)),
            "sources": list(dict.fromkeys(item.source for item in matching if item.source)),
        })
    manifest = {
        "schema_version": "paper-table-manifest-v3",
        "inputs": [str(Path(path)) for path in inputs],
        "input_record_count": len(observations),
        "observation_count": sum(isinstance(item, Observation) for item in observations),
        "reported_summary_count": sum(isinstance(item, ReportedSummary) for item in observations),
        "represented_run_count": sum(
            item.n if isinstance(item, ReportedSummary) else 1 for item in observations
        ),
        "aggregate_count": len(aggregates),
        "displayed_cell_count": planned,
        "method_count": len(spec["methods"]),
        "displayed_system_count": len(spec["rows"]) if spec["orientation"] == "methods_rows" else len(spec["columns"]),
        "column_count": len(spec["columns"]),
        "template_id": spec["template_id"],
        "table_type": spec["table_type"],
        "focal_methods": spec.get("focal_methods", []),
        "orientation": spec["orientation"],
        "ranking_scope": spec.get("comparison", {}).get("rank_scope_label", "all displayed systems"),
        "auxiliary_display": list(spec.get("auxiliary", {})),
        "omitted_columns": spec["omitted_columns"],
        "warnings": spec["warnings"],
        "verification": verification,
        "method_identity_policy": "verbatim_from_input",
        "method_identity": method_identity,
        "context_notes": spec.get("context_notes", []),
        "deliverables": ["caption.txt", "description.txt", "table.tex", "table.html"],
        "audit_artifacts": ["observations.json", "aggregates.json", "table-spec.json", "manifest.json", "preview.tex"],
    }
    _dump(output / "manifest.json", manifest)
    return manifest
