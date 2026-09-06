from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .table_types import table_type_strategy


def template_directory() -> Path:
    return Path(__file__).resolve().parents[1] / "templates"


def available_templates() -> list[dict[str, str]]:
    output = []
    for path in sorted(template_directory().glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        output.append({
            "id": data.get("template_id", path.stem),
            "description": data.get("description", ""),
            "path": str(path),
        })
    return output


def load_template(name: str) -> dict[str, Any]:
    path = Path(name)
    if not path.is_file():
        path = template_directory() / f"{name.removesuffix('.json')}.json"
    if not path.is_file():
        choices = ", ".join(item["id"] for item in available_templates())
        raise ValueError(f"unknown template {name!r}; available: {choices}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"template root must be an object: {path}")
    return data


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    output = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(output.get(key), dict):
            output[key] = deep_merge(output[key], value)
        else:
            output[key] = deepcopy(value)
    return output


def resolve_config(config: dict[str, Any] | None, template: str | None = None) -> dict[str, Any]:
    config = config or {}
    selected = template or config.get("template")
    base = load_template(str(selected)) if selected else {}
    table_type = config.get("table_type")
    if table_type:
        base = deep_merge(base, table_type_strategy(str(table_type)))
    if not selected and not table_type:
        return config
    override = {key: value for key, value in config.items() if key != "template"}
    return deep_merge(base, override)
