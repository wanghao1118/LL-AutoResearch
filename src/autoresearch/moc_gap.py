from __future__ import annotations

from .schema import (
    DomainProfile,
    EvidenceSnippet,
    GapEvidence,
    GapEvidenceStep,
    GapPaperJudgment,
    MOCGapCandidate,
    MOCGroup,
    PaperCard,
    TopicMOC,
)
from .utils import clean_text, slugify

FULL_TEXT_SECTIONS = {
    "methods",
    "method",
    "materials and methods",
    "experiments",
    "experimental setup",
    "evaluation",
    "results",
    "discussion",
    "limitations",
    "limitation",
    "body",
}

TAG_KEYWORDS = {
    "temporal_or_change": [
        "temporal",
        "change",
        "longitudinal",
        "follow-up",
        "follow up",
        "paired",
        "time",
    ],
    "lesion_or_localization": [
        "lesion",
        "localization",
        "localisation",
        "mask",
        "region",
        "grounding",
        "finding-level",
        "location",
        "tracking",
    ],
    "benchmark_or_evaluation": [
        "benchmark",
        "evaluation",
        "protocol",
        "baseline",
        "workflow",
    ],
    "dataset_explicit": [
        "dataset",
        "data",
        "cohort",
    ],
    "metric_explicit": [
        "metric",
        "score",
        "accuracy",
        "consistency",
        "bert",
        "rouge",
        "auc",
    ],
}


def _unique(values: list[str], limit: int = 8) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = value.strip()
        if not cleaned or cleaned == "not explicit" or cleaned in seen:
            continue
        result.append(cleaned)
        seen.add(cleaned)
        if len(result) >= limit:
            break
    return result


def _has_tag(card: PaperCard, tag: str) -> bool:
    return tag in card.coverage_tags


def _first_evidence(card: PaperCard, claim: str) -> EvidenceSnippet:
    if card.evidence_snippets:
        snippet = card.evidence_snippets[0]
        return EvidenceSnippet(
            paper_title=card.title,
            source_url=card.url or snippet.source_url,
            claim=claim,
            snippet=snippet.snippet,
            section=snippet.section,
        )
    snippet = card.claimed_contribution or card.problem or card.task or card.method
    return EvidenceSnippet(
        paper_title=card.title,
        source_url=card.url,
        claim=claim,
        snippet=clean_text(snippet, 260),
        section="metadata",
    )


def _full_text_count(snippets: list[EvidenceSnippet]) -> int:
    return sum(1 for snippet in snippets if snippet.section.lower() in FULL_TEXT_SECTIONS)


def _required_tags(group: MOCGroup, profile: DomainProfile | None) -> list[str]:
    text = " ".join(
        [
            group.name,
            group.problem_space,
            *group.missing_capabilities,
            *group.open_questions,
            *group.possible_experiments,
        ]
    ).lower()
    tags: list[str] = []
    for tag, keywords in TAG_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            tags.append(tag)
    if profile:
        for dimension in profile.capability_dimensions:
            name = dimension.name.lower()
            if name and name in text:
                tags.append(f"capability:{slugify(dimension.name)}")
    return _unique(tags, limit=6)


def _supports_missing(card: PaperCard, required_tags: list[str]) -> bool:
    if not required_tags:
        return bool(card.missing_capability or card.gap_hint)
    return any(not _has_tag(card, tag) for tag in required_tags)


def _counters_missing(card: PaperCard, required_tags: list[str]) -> bool:
    if not required_tags:
        return False
    return all(_has_tag(card, tag) for tag in required_tags)


def _candidate_statement(group: MOCGroup) -> str:
    missing = group.missing_capabilities[0] if group.missing_capabilities else "target capability"
    return (
        f"MOC problem space '{group.problem_space or group.name}' still leaves this weakness: "
        f"{missing}"
    )


def _candidate_confidence(
    *,
    support_count: int,
    counter_count: int,
    total_papers: int,
    full_text_count: int,
) -> tuple[float, str]:
    if total_papers <= 0:
        return 0.0, "insufficient_coverage"
    support_ratio = support_count / total_papers
    counter_ratio = counter_count / total_papers
    confidence = 0.34 + support_ratio * 0.4 - counter_ratio * 0.18 + min(full_text_count, 3) * 0.04
    confidence = max(0.18, min(0.86, confidence))
    if support_count >= 2 and counter_count == 0:
        status = "moc_supported_needs_codex_review"
    elif support_count >= 2 and counter_count > 0:
        status = "moc_partially_supported_needs_codex_review"
    else:
        status = "moc_weak_candidate_needs_codex_review"
    return round(confidence, 2), status


def _candidate_for_group(
    *,
    group: MOCGroup,
    cards_by_title: dict[str, PaperCard],
    all_cards: list[PaperCard],
    profile: DomainProfile | None,
) -> MOCGapCandidate | None:
    group_cards = [
        cards_by_title[title]
        for title in group.representative_papers
        if title in cards_by_title
    ]
    if not group_cards:
        return None

    required_tags = _required_tags(group, profile)
    support_cards = [card for card in group_cards if _supports_missing(card, required_tags)]
    if not support_cards:
        return None

    support_titles = {card.title for card in support_cards}
    counter_cards = [
        card
        for card in all_cards
        if card.title not in support_titles and _counters_missing(card, required_tags)
    ]
    decided_titles = support_titles | {card.title for card in counter_cards}
    unclear_cards = [card for card in all_cards if card.title not in decided_titles]
    missing = _unique(group.missing_capabilities, limit=6) or ["target capability is under-specified"]
    support_claim = (
        f"MOC group '{group.name}' exposes missing capability: {missing[0]}"
    )
    counter_claim = (
        f"Paper has the extracted signals that may counter the MOC weakness: {', '.join(required_tags)}"
        if required_tags
        else "Paper may provide counter-evidence after Codex review"
    )
    support_snippets = [_first_evidence(card, support_claim) for card in support_cards[:5]]
    counter_snippets = [_first_evidence(card, counter_claim) for card in counter_cards[:4]]
    evidence_chain = [
        GapEvidenceStep(
            paper_title=card.title,
            source_url=card.url,
            role="support",
            claim=support_claim,
            missing_dimensions=missing,
            evidence=snippet,
        )
        for card, snippet in zip(support_cards[:5], support_snippets, strict=False)
    ]
    evidence_chain.extend(
        GapEvidenceStep(
            paper_title=card.title,
            source_url=card.url,
            role="counter",
            claim=counter_claim,
            evidence=snippet,
        )
        for card, snippet in zip(counter_cards[:4], counter_snippets, strict=False)
    )
    confidence, status = _candidate_confidence(
        support_count=len(support_cards),
        counter_count=len(counter_cards),
        total_papers=len(all_cards),
        full_text_count=_full_text_count(support_snippets),
    )
    return MOCGapCandidate(
        candidate_id=slugify(f"{group.name}-{missing[0]}")[:72],
        moc_group=group.name,
        problem_space=group.problem_space,
        weakness_statement=_candidate_statement(group),
        rationale=(
            "Generated from MOC-level comparison: the problem space has representative papers, "
            "shared assumptions, and explicit missing capabilities that need support/counter review."
        ),
        missing_capabilities=missing,
        shared_assumptions=_unique(group.shared_assumptions, limit=5),
        covered_capabilities=_unique(group.covered_capabilities, limit=5),
        support_papers=[card.title for card in support_cards[:8]],
        counter_papers=[card.title for card in counter_cards[:6]],
        unclear_papers=[card.title for card in unclear_cards[:6]],
        support_snippets=support_snippets,
        counter_snippets=counter_snippets,
        evidence_chain=evidence_chain,
        confidence=confidence,
        evidence_status=status,
        next_full_text_targets=[card.title for card in support_cards[:5]],
    )


def build_moc_gap_candidates(
    *,
    topic_moc: TopicMOC | None,
    cards: list[PaperCard],
    profile: DomainProfile | None = None,
    limit: int = 5,
) -> list[MOCGapCandidate]:
    if not topic_moc:
        return []
    cards_by_title = {card.title: card for card in cards}
    candidates: list[MOCGapCandidate] = []
    for group in topic_moc.problem_spaces:
        candidate = _candidate_for_group(
            group=group,
            cards_by_title=cards_by_title,
            all_cards=cards,
            profile=profile,
        )
        if candidate:
            candidates.append(candidate)
    candidates.sort(
        key=lambda item: (
            item.confidence,
            len(item.support_papers),
            -len(item.counter_papers),
        ),
        reverse=True,
    )
    return candidates[:limit]


def moc_candidate_to_gap(candidate: MOCGapCandidate, total_papers: int) -> GapEvidence:
    support_count = len(candidate.support_papers)
    counter_count = len(candidate.counter_papers)
    unclear_count = max(total_papers - support_count - counter_count, 0)
    evidence_by_title = {
        step.paper_title: step.evidence
        for step in candidate.evidence_chain
        if step.evidence is not None
    }
    paper_judgments = [
        GapPaperJudgment(
            paper_title=title,
            source_url=evidence_by_title[title].source_url if title in evidence_by_title else "",
            decision="no",
            role="support",
            rationale="This paper belongs to the MOC problem space that exposes the missing capability.",
            evidence=evidence_by_title.get(title),
            missing_evidence=candidate.missing_capabilities,
        )
        for title in candidate.support_papers
    ]
    paper_judgments.extend(
        GapPaperJudgment(
            paper_title=title,
            source_url=evidence_by_title[title].source_url if title in evidence_by_title else "",
            decision="yes",
            role="counter",
            rationale="This paper has extracted signals that may cover the candidate weakness.",
            evidence=evidence_by_title.get(title),
        )
        for title in candidate.counter_papers
    )
    paper_judgments.extend(
        GapPaperJudgment(
            paper_title=title,
            source_url="",
            decision="unclear",
            role="unclear",
            rationale="This paper needs Codex review or targeted full-text reading before attribution.",
            missing_evidence=candidate.missing_capabilities,
        )
        for title in candidate.unclear_papers
    )
    return GapEvidence(
        gap=candidate.weakness_statement,
        source="moc_gap_candidate",
        moc_candidate_id=candidate.candidate_id,
        moc_group=candidate.moc_group,
        moc_problem_space=candidate.problem_space,
        moc_missing_capabilities=candidate.missing_capabilities,
        moc_shared_assumptions=candidate.shared_assumptions,
        review_status=candidate.review_status,
        evidence=candidate.support_snippets,
        counter_evidence=candidate.counter_snippets,
        evidence_chain=candidate.evidence_chain,
        confidence=candidate.confidence,
        support_count=support_count,
        counter_count=counter_count,
        unclear_count=unclear_count,
        total_papers=total_papers,
        support_ratio=support_count / total_papers if total_papers else 0.0,
        counter_ratio=counter_count / total_papers if total_papers else 0.0,
        full_text_evidence_count=_full_text_count(candidate.support_snippets),
        score_reasons=[
            "generated_from_moc_problem_space",
            f"moc_group={candidate.moc_group}",
            f"support_papers={support_count}",
            f"counter_papers={counter_count}",
            f"evidence_status={candidate.evidence_status}",
        ],
        paper_judgments=paper_judgments,
        why_it_matters=(
            "This weakness matters because it is tied to a MOC problem space rather than an "
            "isolated paper summary; Codex Review should verify whether the missing capability "
            "is real, partially solved, or overclaimed."
        ),
        research_opportunity=(
            "Use the MOC support/counter split to design a targeted validation table, then read "
            "the support papers' Method, Experiment, Dataset, and Metric sections."
        ),
    )


def moc_candidates_to_gaps(
    candidates: list[MOCGapCandidate],
    *,
    total_papers: int,
) -> list[GapEvidence]:
    return [moc_candidate_to_gap(candidate, total_papers) for candidate in candidates]
