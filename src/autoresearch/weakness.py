from __future__ import annotations

from .schema import (
    ComparisonMatrix,
    DomainProfile,
    FullTextRecord,
    GapEvidence,
    SearchArtifacts,
    SourceStatus,
    TopicMOC,
    WeaknessCard,
)


def _unique(values: list[str], limit: int = 8) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = value.strip()
        if not cleaned or cleaned in seen:
            continue
        result.append(cleaned)
        seen.add(cleaned)
        if len(result) >= limit:
            break
    return result


def _checked_sources(statuses: list[SourceStatus]) -> int:
    return len({status.source for status in statuses if status.status == "ok" and status.raw_count > 0})


def _checked_sections(full_texts: list[FullTextRecord]) -> list[str]:
    sections: list[str] = []
    for record in full_texts:
        if record.status != "ok":
            continue
        for section in record.sections:
            heading = section.heading.strip() or "body"
            sections.append(heading.lower())
    return _unique(sections, limit=12)


def _checked_full_texts(full_texts: list[FullTextRecord]) -> int:
    return sum(1 for record in full_texts if record.status == "ok")


def _evidence_quality(
    gap: GapEvidence,
    *,
    checked_full_texts: int,
    checked_sources: int,
) -> tuple[str, list[str]]:
    reasons = [
        f"checked_papers={gap.total_papers}",
        f"support={gap.support_count}",
        f"counter={gap.counter_count}",
        f"full_texts={checked_full_texts}",
        f"sources={checked_sources}",
    ]
    if gap.total_papers >= 20 and checked_full_texts >= 5 and checked_sources >= 3:
        return "strong", reasons
    if gap.total_papers >= 8 and checked_sources >= 2 and checked_full_texts >= 2:
        return "medium", reasons
    return "weak", reasons


def _verdict(gap: GapEvidence, quality: str) -> str:
    if gap.counter_ratio >= 0.65 and gap.support_count <= 1:
        return "already_covered"
    if gap.support_count >= 2 and gap.counter_count >= 1:
        return "partially_valid"
    if gap.support_count >= 2 and gap.counter_count == 0 and quality in {"medium", "strong"}:
        return "valid"
    return "insufficient_evidence"


def _support_papers(gap: GapEvidence) -> list[str]:
    return _unique(
        [step.paper_title for step in gap.evidence_chain if step.role == "support"],
        limit=8,
    )


def _counter_papers(gap: GapEvidence) -> list[str]:
    return _unique(
        [step.paper_title for step in gap.evidence_chain if step.role == "counter"],
        limit=8,
    )


def _unclear_papers(gap: GapEvidence) -> list[str]:
    return _unique(
        [
            judgment.paper_title
            for judgment in gap.paper_judgments
            if judgment.role == "unclear"
        ],
        limit=8,
    )


def _missing_parts(gap: GapEvidence) -> list[str]:
    parts: list[str] = []
    for judgment in gap.paper_judgments:
        if judgment.role != "support":
            continue
        parts.extend(judgment.missing_evidence)
    for step in gap.evidence_chain:
        if step.role == "support":
            parts.extend(step.missing_dimensions)
    return _unique(parts, limit=8)


def _covered_parts(gap: GapEvidence) -> list[str]:
    parts: list[str] = []
    for judgment in gap.paper_judgments:
        if judgment.role != "counter":
            continue
        if judgment.evidence:
            parts.append(judgment.evidence.claim)
        elif judgment.rationale:
            parts.append(judgment.rationale)
    for evidence in gap.counter_evidence:
        parts.append(evidence.claim)
    return _unique(parts, limit=6)


def _moc_origin(
    gap: GapEvidence,
    topic_moc: TopicMOC | None,
    comparison: ComparisonMatrix | None,
) -> list[str]:
    support_titles = set(_support_papers(gap))
    counter_titles = set(_counter_papers(gap))
    origins: list[str] = []
    if topic_moc:
        for group in topic_moc.problem_spaces:
            titles = set(group.representative_papers)
            if titles & support_titles or titles & counter_titles:
                origins.append(
                    f"{group.name}: covers={'; '.join(group.covered_capabilities[:3]) or 'not explicit'}; "
                    f"missing={'; '.join(group.missing_capabilities[:3]) or 'not explicit'}"
                )
    if not origins and comparison:
        for row in comparison.rows[:4]:
            origins.append(
                f"{row.group}: solves={'; '.join(row.solves[:2])}; missing={'; '.join(row.missing[:2])}"
            )
    return _unique(origins, limit=5)


def _verification_queries(
    topic: str,
    gap: GapEvidence,
    profile: DomainProfile | None,
) -> list[str]:
    domain = profile.domain_name if profile else topic
    focus_terms = []
    if profile:
        focus_terms.extend(profile.core_concepts[:4])
        focus_terms.extend(profile.benchmark_keywords[:3])
        focus_terms.extend(profile.metric_keywords[:3])
    base = gap.gap.replace(":", " ").replace(".", " ")
    queries = [
        f"{topic} {base} benchmark",
        f"{topic} {base} metric",
        f"{topic} {base} dataset",
        f"{topic} {base} limitation",
        f"{topic} {base} already solved",
        f"{domain} {' '.join(focus_terms[:5])} counter evidence",
    ]
    return _unique(queries, limit=6)


def _remaining_weakness(gap: GapEvidence, covered: list[str], missing: list[str]) -> str:
    if covered and missing:
        return (
            f"The broad problem is partially covered by existing work, but the retrieved support "
            f"papers still leave these dimensions under-specified: {', '.join(missing[:4])}."
        )
    if covered:
        return (
            "The broad problem has visible counter-evidence in the retrieved papers; keep only the "
            "parts not covered by those counter papers after full-text review."
        )
    if missing:
        return f"The remaining weakness is concentrated in: {', '.join(missing[:4])}."
    return gap.gap


def _conclusion(verdict: str, remaining: str) -> str:
    labels = {
        "valid": "This weakness is currently supported by the completed evidence pass.",
        "partially_valid": "This weakness is partially valid and should be stated narrowly.",
        "already_covered": "The broad weakness appears mostly covered by counter-evidence.",
        "insufficient_evidence": "The current run does not provide enough evidence for a final claim.",
    }
    return f"{labels.get(verdict, labels['insufficient_evidence'])} {remaining}"


def build_weakness_cards(
    *,
    topic: str,
    gaps: list[GapEvidence],
    topic_moc: TopicMOC | None,
    comparison: ComparisonMatrix | None,
    full_texts: list[FullTextRecord],
    source_statuses: list[SourceStatus],
    profile: DomainProfile | None,
) -> list[WeaknessCard]:
    checked_full_texts = _checked_full_texts(full_texts)
    checked_sources = _checked_sources(source_statuses)
    checked_sections = _checked_sections(full_texts)
    cards: list[WeaknessCard] = []
    for gap in gaps:
        quality, quality_reasons = _evidence_quality(
            gap,
            checked_full_texts=checked_full_texts,
            checked_sources=checked_sources,
        )
        verdict = _verdict(gap, quality)
        missing = _missing_parts(gap)
        covered = _covered_parts(gap)
        remaining = _remaining_weakness(gap, covered, missing)
        cards.append(
            WeaknessCard(
                weakness_statement=gap.gap,
                broad_problem=gap.gap,
                remaining_weakness=remaining,
                verdict=verdict,
                evidence_quality=quality,
                evidence_quality_reasons=quality_reasons,
                checked_papers=gap.total_papers,
                checked_full_texts=checked_full_texts,
                checked_sources=checked_sources,
                checked_sections=checked_sections,
                support_papers=_support_papers(gap),
                counter_papers=_counter_papers(gap),
                unclear_papers=_unclear_papers(gap),
                support_snippets=gap.evidence[:5],
                counter_snippets=gap.counter_evidence[:5],
                covered_parts=covered,
                partially_solved_parts=covered,
                missing_parts=missing,
                moc_origin=_moc_origin(gap, topic_moc, comparison),
                verification_queries=_verification_queries(topic, gap, profile),
                conclusion=_conclusion(verdict, remaining),
            )
        )
    return cards


def ensure_weakness_cards(artifacts: SearchArtifacts) -> SearchArtifacts:
    if artifacts.weakness_cards:
        return artifacts
    artifacts.weakness_cards = build_weakness_cards(
        topic=artifacts.topic,
        gaps=artifacts.gaps,
        topic_moc=artifacts.topic_moc,
        comparison=artifacts.comparison_matrix,
        full_texts=artifacts.full_texts,
        source_statuses=artifacts.source_statuses,
        profile=artifacts.domain_profile,
    )
    return artifacts
