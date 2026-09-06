from __future__ import annotations

from copy import deepcopy
from typing import Any


_TABLE_TYPES: dict[str, dict[str, Any]] = {
    "main_benchmark": {
        "description": "Core comparison of the focal method and baselines across benchmarks.",
        "strategy": {
            "emphasis": {"best": "bold", "second": "underline"},
            "style": {"fit_width": True, "font_size": "scriptsize"},
        },
    },
    "main_tradeoff": {
        "description": "Claim-bearing quality, efficiency, cost, or robustness trade-off.",
        "strategy": {
            "emphasis": {"best": "bold", "second": "underline"},
            "style": {"fit_width": True, "font_size": "scriptsize"},
        },
    },
    "ablation": {
        "description": "Reference configuration compared with controlled component or axis changes.",
        "strategy": {
            "emphasis": {},
            "style": {"row_group_style": "none", "row_separator_style": "space"},
        },
    },
    "analysis": {
        "description": "Mechanism, error, sensitivity, failure, or other explanatory evidence.",
        "strategy": {
            "emphasis": {},
            "style": {"row_group_style": "none"},
        },
    },
    "diagnostic": {
        "description": "Incomplete, non-claim-bearing, or protocol-diagnostic evidence.",
        "strategy": {
            "emphasis": {},
            "style": {"row_group_style": "none", "fit_width": False},
        },
    },
    "simple_comparison": {
        "description": "Small direct comparison where clarity matters more than visual density.",
        "strategy": {
            "emphasis": {},
            "style": {"row_group_style": "none", "fit_width": False},
        },
    },
}


def available_table_types() -> list[dict[str, str]]:
    return [
        {"id": key, "description": value["description"]}
        for key, value in _TABLE_TYPES.items()
    ]


def table_type_strategy(name: str) -> dict[str, Any]:
    if name not in _TABLE_TYPES:
        choices = ", ".join(_TABLE_TYPES)
        raise ValueError(f"unknown table_type {name!r}; available: {choices}")
    return deepcopy(_TABLE_TYPES[name]["strategy"])
