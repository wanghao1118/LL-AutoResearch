"""Blind-input leakage checks.

Benchmark aliases are forbidden in matcher input. Generic words such as
``benchmark`` or ``evaluation`` are recorded as warnings because they describe
the requested task but do not reveal the hidden label.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import BenchmarkRecord, MethodInput


@dataclass(frozen=True)
class LeakageReport:
    passed: bool
    benchmark_alias_hits: list[str]
    identity_hits: list[str]
    generic_evaluation_terms: list[str]


class LeakageError(ValueError):
    """Raised when a blind input exposes a benchmark or paper identity."""


def _contains(text: str, phrase: str) -> bool:
    pattern = r"(?<![a-z0-9])" + re.escape(phrase.casefold()) + r"(?![a-z0-9])"
    return re.search(pattern, text.casefold()) is not None


def scan_blind_input(
    method_input: MethodInput,
    catalog: list[BenchmarkRecord],
    identity_markers: list[str] | None = None,
) -> LeakageReport:
    """Scan only the payload visible to the matcher."""

    text = f"{method_input.introduction}\n{method_input.method}"
    aliases = sorted(
        {
            alias
            for record in catalog
            for alias in [record.name, *record.aliases]
            if len(alias.strip()) >= 4
        },
        key=lambda item: (-len(item), item.casefold()),
    )
    alias_hits = [alias for alias in aliases if _contains(text, alias)]
    identity_hits = [marker for marker in identity_markers or [] if _contains(text, marker)]
    generic_terms = [
        term
        for term in ("benchmark", "dataset", "evaluation", "experiment")
        if _contains(text, term)
    ]
    return LeakageReport(
        passed=not alias_hits and not identity_hits,
        benchmark_alias_hits=alias_hits,
        identity_hits=identity_hits,
        generic_evaluation_terms=generic_terms,
    )


def enforce_blind_input(
    method_input: MethodInput,
    catalog: list[BenchmarkRecord],
    identity_markers: list[str] | None = None,
) -> LeakageReport:
    """Fail before matching when benchmark or paper identity is visible."""

    report = scan_blind_input(method_input, catalog, identity_markers)
    if not report.passed:
        raise LeakageError(
            "blind input leakage detected: "
            f"benchmark_alias_hits={report.benchmark_alias_hits}, "
            f"identity_hits={report.identity_hits}"
        )
    return report
