"""Typed records shared by the Auto-Bench agents.

The workflow keeps paper inputs, benchmark evidence, and automatic decisions
in separate records. The matcher receives only :class:`MethodInput` and the
public catalog; source-paper labels are opened later by the automatic reviewer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class MethodInput:
    """Introduction and method text supplied to the matching workflow."""

    case_id: str
    introduction: str
    method: str
    constraints: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MethodInput":
        allowed = {"case_id", "introduction", "method", "constraints"}
        unexpected = sorted(set(payload) - allowed)
        if unexpected:
            raise ValueError(f"unexpected input fields: {unexpected}")
        for key in ("case_id", "introduction", "method"):
            if not isinstance(payload.get(key), str) or not payload[key].strip():
                raise ValueError(f"{key} must be a non-empty string")
        constraints = payload.get("constraints", {})
        if not isinstance(constraints, dict):
            raise ValueError("constraints must be an object")
        return cls(
            case_id=payload["case_id"].strip(),
            introduction=payload["introduction"].strip(),
            method=payload["method"].strip(),
            constraints=constraints,
        )


@dataclass(frozen=True)
class CapabilityProfile:
    """Evaluation requirements inferred only from introduction and method."""

    task_families: list[str]
    task_benchmark_counts: dict[str, int]
    uncovered_task_families: list[str]
    modalities: list[str]
    interactions: list[str]
    output_types: list[str]
    environments: list[str]
    capabilities: list[str]
    suggested_metrics: list[str]
    evidence_terms: dict[str, list[str]]
    declared_evaluation_breadth: int = 0


@dataclass(frozen=True)
class BenchmarkRecord:
    """One literature-grounded benchmark in the public candidate catalog."""

    benchmark_id: str
    name: str
    aliases: list[str]
    year: int
    task_families: list[str]
    modalities: list[str]
    interactions: list[str]
    output_types: list[str]
    environments: list[str]
    capabilities: list[str]
    metrics: list[str]
    keywords: list[str]
    access: str
    license_note: str
    source_title: str
    source_url: str
    adaptation_hooks: list[str]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BenchmarkRecord":
        required = {
            "benchmark_id",
            "name",
            "aliases",
            "year",
            "task_families",
            "modalities",
            "interactions",
            "output_types",
            "environments",
            "capabilities",
            "metrics",
            "keywords",
            "access",
            "license_note",
            "source_title",
            "source_url",
            "adaptation_hooks",
        }
        missing = sorted(required - set(payload))
        if missing:
            raise ValueError(f"benchmark record missing fields: {missing}")
        return cls(**{key: payload[key] for key in required})


@dataclass(frozen=True)
class SearchHit:
    """A paper found by the optional live literature-search agent."""

    title: str
    summary: str
    url: str
    query: str


@dataclass(frozen=True)
class CatalogAdmissionProposal:
    """Incomplete online benchmark lead awaiting catalog-level verification."""

    proposal_id: str
    title: str
    source_url: str
    source_query: str
    benchmark_likelihood: float
    matched_task_families: list[str]
    evidence_terms: list[str]
    proposed_record: dict[str, Any]
    missing_required_fields: list[str]
    selection_eligible: bool
    status: str


@dataclass(frozen=True)
class ScoredCandidate:
    """Compatibility judgement with inspectable component scores."""

    benchmark_id: str
    name: str
    score: float
    component_scores: dict[str, float]
    matched_requirements: dict[str, list[str]]
    hard_mismatches: list[str]
    evidence: list[str]
    source_url: str
    metrics: list[str]
    adaptation_hooks: list[str]


@dataclass
class BenchmarkPlan:
    """Complete matcher output before automatic source-paper comparison."""

    case_id: str
    status: str
    visible_input: dict[str, Any]
    profile: CapabilityProfile
    search_queries: list[str]
    search_hits: list[SearchHit]
    catalog_admission_proposals: list[CatalogAdmissionProposal]
    ranked_candidates: list[ScoredCandidate]
    selected_benchmarks: list[str]
    portfolio_roles: dict[str, str]
    coverage_ratio: float
    route: str
    route_reason: str
    metric_plan: list[dict[str, Any]]
    adaptation_plan: dict[str, Any]
    synthesis_plan: dict[str, Any]
    automatic_review: dict[str, Any]
    human_review: dict[str, Any]
    provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
