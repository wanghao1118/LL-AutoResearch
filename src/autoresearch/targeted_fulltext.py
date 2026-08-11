from __future__ import annotations

from collections import Counter

from .schema import (
    EvidenceCoverageRecord,
    FullTextRecord,
    RankedPaper,
    TargetedFullTextTarget,
    WeaknessCard,
)
from .utils import normalize_title


def _title_key(title: str) -> str:
    return normalize_title(title)


def _ranked_lookup(ranked: list[RankedPaper]) -> dict[str, tuple[int, RankedPaper]]:
    return {_title_key(row.paper.title): (index, row) for index, row in enumerate(ranked, start=1)}


def _coverage_lookup(rows: list[EvidenceCoverageRecord]) -> dict[str, EvidenceCoverageRecord]:
    return {row.weakness_statement: row for row in rows}


def _ok_full_text_titles(full_texts: list[FullTextRecord]) -> set[str]:
    return {_title_key(row.title) for row in full_texts if row.status == "ok"}


def _section_gain(coverage: EvidenceCoverageRecord | None) -> list[str]:
    gains = []
    if not coverage or coverage.method_sections == 0:
        gains.append("method")
    if not coverage or coverage.experiment_sections == 0:
        gains.append("experiment")
    if not coverage or coverage.dataset_metric_sections == 0:
        gains.append("dataset/metric")
    return gains


def _fetchability_bonus(row: RankedPaper | None) -> float:
    if not row:
        return 0.0
    paper = row.paper
    bonus = 0.0
    if paper.pdf_url or paper.arxiv_id or paper.pmcid:
        bonus += 8.0
    if paper.doi or paper.pmid:
        bonus += 4.0
    if paper.raw.get("full_text_candidates"):
        bonus += 8.0
    return bonus


def _coverage_bonus(status: str) -> float:
    if status == "needs_targeted_full_text":
        return 55.0
    if status == "insufficient_coverage":
        return 35.0
    if status == "ready_to_state_narrowly":
        return 8.0
    return 20.0


def _quality_bonus(card: WeaknessCard) -> float:
    if card.evidence_quality == "strong":
        return 20.0
    if card.evidence_quality == "medium":
        return 14.0
    if card.evidence_quality == "weak":
        return 5.0
    return 0.0


def build_targeted_full_text_targets(
    *,
    weakness_cards: list[WeaknessCard],
    evidence_coverage: list[EvidenceCoverageRecord],
    ranked: list[RankedPaper],
    full_texts: list[FullTextRecord],
    limit: int = 8,
    per_weakness_limit: int = 2,
) -> list[TargetedFullTextTarget]:
    """Select missing support-paper full texts that would most improve weakness evidence."""
    if limit <= 0 or per_weakness_limit <= 0:
        return []

    ranked_by_title = _ranked_lookup(ranked)
    coverage_by_weakness = _coverage_lookup(evidence_coverage)
    full_text_ok = _ok_full_text_titles(full_texts)
    support_frequency = Counter(
        _title_key(title)
        for card in weakness_cards
        for title in card.support_papers
        if _title_key(title)
    )

    targets: list[TargetedFullTextTarget] = []
    for card in weakness_cards:
        coverage = coverage_by_weakness.get(card.weakness_statement)
        missing_support = (
            coverage.missing_support_full_text_papers
            if coverage
            else [title for title in card.support_papers if _title_key(title) not in full_text_ok]
        )
        for title in missing_support[:per_weakness_limit]:
            title_key = _title_key(title)
            if not title_key or title_key in full_text_ok:
                continue
            rank, ranked_row = ranked_by_title.get(title_key, (0, None))
            rank_bonus = max(0.0, 20.0 - float(rank)) if rank else 0.0
            shared = support_frequency.get(title_key, 1)
            status = coverage.status if coverage else "not_evaluated"
            priority = (
                _coverage_bonus(status)
                + _quality_bonus(card)
                + min(shared, 4) * 7.0
                + rank_bonus
                + _fetchability_bonus(ranked_row)
                + ((ranked_row.relevance_score if ranked_row else 0.0) * 10.0)
            )
            targets.append(
                TargetedFullTextTarget(
                    weakness_statement=card.weakness_statement,
                    paper_title=title,
                    source_url=ranked_row.paper.url if ranked_row else "",
                    rank=rank,
                    priority=round(priority, 2),
                    status="queued" if ranked_row else "not_in_ranked_set",
                    reason=(
                        "This paper is a support paper for a weakness whose evidence gate still "
                        "needs targeted full text."
                    ),
                    evidence_coverage_status=status,
                    support_paper_count=len(card.support_papers),
                    already_has_full_text=False,
                    shared_weakness_count=shared,
                    expected_gain=_section_gain(coverage),
                )
            )

    targets.sort(key=lambda row: (-row.priority, row.rank or 9999, row.paper_title))
    return targets[:limit]


def ranked_papers_for_targets(
    targets: list[TargetedFullTextTarget],
    ranked: list[RankedPaper],
) -> list[RankedPaper]:
    ranked_by_title = _ranked_lookup(ranked)
    selected: list[RankedPaper] = []
    seen: set[str] = set()
    for target in targets:
        title_key = _title_key(target.paper_title)
        if not title_key or title_key in seen:
            continue
        row = ranked_by_title.get(title_key)
        if not row:
            continue
        seen.add(title_key)
        selected.append(row[1])
    return selected


def mark_targeted_full_text_statuses(
    targets: list[TargetedFullTextTarget],
    fetched: dict[str, FullTextRecord],
    all_full_texts: list[FullTextRecord],
) -> list[TargetedFullTextTarget]:
    ok_titles = _ok_full_text_titles(all_full_texts)
    fetched_by_title = {_title_key(title): record for title, record in fetched.items()}
    updated: list[TargetedFullTextTarget] = []
    for target in targets:
        title_key = _title_key(target.paper_title)
        record = fetched_by_title.get(title_key)
        if title_key in ok_titles:
            target.status = "fetched_ok" if record else "already_has_full_text"
            target.already_has_full_text = True
        elif record:
            target.status = "fetch_failed"
            target.reason = record.error or target.reason
        elif target.status != "not_in_ranked_set":
            target.status = "queued"
        updated.append(target)
    return updated


def merge_targeted_full_text_targets(
    first: list[TargetedFullTextTarget],
    second: list[TargetedFullTextTarget],
    *,
    limit: int = 0,
) -> list[TargetedFullTextTarget]:
    merged: list[TargetedFullTextTarget] = []
    seen: set[tuple[str, str]] = set()
    for target in [*first, *second]:
        key = (_title_key(target.weakness_statement), _title_key(target.paper_title))
        if key in seen:
            continue
        seen.add(key)
        merged.append(target)
    if limit > 0:
        return merged[:limit]
    return merged
