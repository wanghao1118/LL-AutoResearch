"""Convert online benchmark-like papers into reviewable catalog proposals."""

from __future__ import annotations

import re

from .models import CapabilityProfile, CatalogAdmissionProposal, SearchHit
from .query_agent import TASK_SEARCH_ALIASES


RESOURCE_PATTERNS = (
    ("benchmark", r"\bbenchmark\b"),
    ("dataset", r"\bdatasets?\b"),
    ("evaluation suite", r"\bevaluation suite\b"),
    ("evaluation framework", r"\bevaluation framework\b"),
    ("named bench", r"\b[a-z0-9]+-bench\b"),
)
INTRODUCTION_PATTERNS = (
    "we introduce",
    "we present",
    "we propose",
    "we create",
    "we develop",
    "we release",
)
METHOD_OBJECT_PATTERN = re.compile(r"\b(?:method|model|approach|system|framework|algorithm|technique)\b")


def _proposal_id(url: str) -> str:
    match = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", url)
    if match:
        return "arxiv_" + match.group(1).replace(".", "_")
    compact = re.sub(r"[^a-z0-9]+", "_", url.casefold()).strip("_")
    return "lead_" + compact[-48:]


def _matched_tasks(profile: CapabilityProfile, hit: SearchHit) -> list[str]:
    query = " ".join(re.findall(r"[a-z0-9]+", hit.query.casefold()))
    matched = []
    for task in [*profile.task_families, *profile.uncovered_task_families]:
        phrases = [task.replace("_", " "), *TASK_SEARCH_ALIASES.get(task, ())]
        if any(phrase in query for phrase in phrases):
            matched.append(task)
    return matched


def _benchmark_likelihood(hit: SearchHit) -> tuple[float, list[str]]:
    title = hit.title.casefold()
    summary = hit.summary.casefold()
    title_terms = [label for label, pattern in RESOURCE_PATTERNS if re.search(pattern, title)]
    introduction_terms = [term for term in INTRODUCTION_PATTERNS if term in summary]
    introduced_resources: list[str] = []
    for introduction_term in introduction_terms:
        for match in re.finditer(re.escape(introduction_term), summary):
            tail = re.split(r"[.!?]", summary[match.end() :], maxsplit=1)[0][:240]
            resource_matches = [
                (resource_match.start(), label)
                for label, pattern in RESOURCE_PATTERNS
                for resource_match in [re.search(pattern, tail)]
                if resource_match
            ]
            if not resource_matches:
                continue
            resource_position, resource_label = min(resource_matches)
            method_match = METHOD_OBJECT_PATTERN.search(tail)
            if method_match and method_match.start() < resource_position:
                continue
            introduced_resources.append(resource_label)
    evidence = [
        *(f"title:{term}" for term in title_terms),
        *(f"summary:introduced_{term}" for term in sorted(set(introduced_resources))),
    ]
    if title_terms and introduction_terms:
        return 1.0, evidence
    if title_terms:
        return 0.7, evidence
    if introduced_resources:
        return 0.8, evidence
    return 0.0, evidence


def build_admission_proposals(
    profile: CapabilityProfile,
    hits: list[SearchHit],
) -> list[CatalogAdmissionProposal]:
    """Create typed proposals while keeping incomplete leads out of selection.

    An arXiv hit becomes a proposal only when its title or abstract explicitly
    presents a benchmark, dataset, or evaluation resource. The proposal carries
    method-derived task fields, but metrics, split semantics, access, license,
    and a stable artifact URL remain explicit review fields. Consequently a
    raw search hit can guide discovery without masquerading as an admitted
    benchmark.
    """

    proposals: list[CatalogAdmissionProposal] = []
    seen: set[str] = set()
    for hit in hits:
        proposal_id = _proposal_id(hit.url)
        if proposal_id in seen:
            continue
        likelihood, evidence = _benchmark_likelihood(hit)
        matched_tasks = _matched_tasks(profile, hit)
        if likelihood < 0.6 or not matched_tasks:
            continue
        seen.add(proposal_id)
        missing = [
            "benchmark_id",
            "official_metrics",
            "dataset_or_harness_url",
            "split_definition",
            "access",
            "license_note",
        ]
        proposals.append(
            CatalogAdmissionProposal(
                proposal_id=proposal_id,
                title=hit.title,
                source_url=hit.url,
                source_query=hit.query,
                benchmark_likelihood=likelihood,
                matched_task_families=matched_tasks,
                evidence_terms=evidence,
                proposed_record={
                    "benchmark_id": None,
                    "name": hit.title,
                    "task_families": matched_tasks,
                    "modalities": profile.modalities,
                    "interactions": profile.interactions,
                    "output_types": profile.output_types,
                    "environments": profile.environments,
                    "capabilities": profile.capabilities,
                    "official_metrics": [],
                    "dataset_or_harness_url": None,
                    "split_definition": None,
                    "access": None,
                    "license_note": None,
                    "source_title": hit.title,
                    "source_url": hit.url,
                },
                missing_required_fields=missing,
                selection_eligible=False,
                status="CATALOG_ADMISSION_REVIEW_REQUIRED",
            )
        )
    return sorted(proposals, key=lambda item: (-item.benchmark_likelihood, item.proposal_id))
