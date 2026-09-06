from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Observation:
    method: str
    method_source_field: str
    metric: str
    value: float
    dataset: str = "Overall"
    run: str | None = None
    setting: str | None = None
    group: str | None = None
    source: str | None = None
    dimensions: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReportedSummary:
    """A published aggregate whose underlying run-level values are unavailable."""

    method: str
    method_source_field: str
    metric: str
    mean: float
    sd: float | None
    n: int
    dataset: str = "Overall"
    setting: str | None = None
    group: str | None = None
    source: str | None = None
    dimensions: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Aggregate:
    method: str
    method_source_fields: tuple[str, ...]
    metric: str
    dataset: str
    setting: str | None
    group: str | None
    dimensions: dict[str, str]
    mean: float
    sd: float | None
    n: int
    values: tuple[float, ...]
    run_ids: tuple[str, ...]
    sources: tuple[str, ...]
    aggregation_source: str = "observations"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["values"] = list(self.values)
        data["run_ids"] = list(self.run_ids)
        data["sources"] = list(self.sources)
        data["method_source_fields"] = list(self.method_source_fields)
        return data
