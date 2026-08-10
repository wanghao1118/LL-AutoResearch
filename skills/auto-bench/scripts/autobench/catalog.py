"""Benchmark catalog loading and validation."""

from __future__ import annotations

import json
from pathlib import Path

from .models import BenchmarkRecord


def load_catalog(path: str | Path) -> list[BenchmarkRecord]:
    """Load a benchmark catalog and enforce provenance-critical invariants."""

    catalog_path = Path(path)
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1.0":
        raise ValueError("benchmark catalog schema_version must be 1.0")
    records = [BenchmarkRecord.from_dict(item) for item in payload.get("benchmarks", [])]
    if not records:
        raise ValueError("benchmark catalog is empty")
    ids = [record.benchmark_id for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("benchmark_id values must be unique")
    aliases: dict[str, str] = {}
    for record in records:
        if not record.source_url.startswith(("https://arxiv.org/", "https://openreview.net/")):
            raise ValueError(f"{record.benchmark_id} lacks a primary paper URL")
        for alias in [record.name, *record.aliases]:
            normalized = alias.casefold().strip()
            owner = aliases.setdefault(normalized, record.benchmark_id)
            if owner != record.benchmark_id:
                raise ValueError(f"alias collision: {alias!r} belongs to {owner} and {record.benchmark_id}")
    return records


def catalog_aliases(records: list[BenchmarkRecord]) -> dict[str, str]:
    """Return normalized benchmark-name/alias to benchmark-id mapping."""

    output: dict[str, str] = {}
    for record in records:
        for alias in [record.name, *record.aliases]:
            output[alias.casefold()] = record.benchmark_id
    return output
