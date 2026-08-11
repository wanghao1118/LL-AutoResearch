from autoresearch.schema import (
    EvidenceCoverageRecord,
    FullTextRecord,
    RankedPaper,
    TextSection,
    WeaknessCard,
)
from autoresearch.targeted_fulltext import (
    build_targeted_full_text_targets,
    mark_targeted_full_text_statuses,
    ranked_papers_for_targets,
)


def _ranked(title: str, score: float, **paper_fields) -> RankedPaper:
    return RankedPaper(
        paper={"title": title, **paper_fields},
        relevance_score=score,
    )


def test_targeted_full_text_prefers_missing_support_paper_over_top_ranked():
    ranked = [
        _ranked("Top Ranked Background Paper", 0.95),
        _ranked("Temporal Support Paper", 0.72, arxiv_id="2601.00001"),
    ]
    weakness = WeaknessCard(
        weakness_statement="Lesion temporal reasoning is weak.",
        evidence_quality="medium",
        support_papers=["Temporal Support Paper"],
    )
    coverage = EvidenceCoverageRecord(
        weakness_statement=weakness.weakness_statement,
        status="needs_targeted_full_text",
        support_papers=["Temporal Support Paper"],
        missing_support_full_text_papers=["Temporal Support Paper"],
    )
    full_texts = [
        FullTextRecord(
            title="Top Ranked Background Paper",
            status="ok",
            sections=[TextSection(heading="Methods", text="method")],
        )
    ]

    targets = build_targeted_full_text_targets(
        weakness_cards=[weakness],
        evidence_coverage=[coverage],
        ranked=ranked,
        full_texts=full_texts,
        limit=3,
        per_weakness_limit=2,
    )

    assert [target.paper_title for target in targets] == ["Temporal Support Paper"]
    assert targets[0].rank == 2
    assert targets[0].evidence_coverage_status == "needs_targeted_full_text"
    assert "experiment" in targets[0].expected_gain


def test_ranked_papers_for_targets_deduplicates_shared_support_papers():
    ranked = [_ranked("Shared Support Paper", 0.8, doi="10.0000/example")]
    weaknesses = [
        WeaknessCard(
            weakness_statement="Weakness A",
            evidence_quality="medium",
            support_papers=["Shared Support Paper"],
        ),
        WeaknessCard(
            weakness_statement="Weakness B",
            evidence_quality="medium",
            support_papers=["Shared Support Paper"],
        ),
    ]
    coverages = [
        EvidenceCoverageRecord(
            weakness_statement=card.weakness_statement,
            status="needs_targeted_full_text",
            support_papers=["Shared Support Paper"],
            missing_support_full_text_papers=["Shared Support Paper"],
        )
        for card in weaknesses
    ]

    targets = build_targeted_full_text_targets(
        weakness_cards=weaknesses,
        evidence_coverage=coverages,
        ranked=ranked,
        full_texts=[],
        limit=5,
        per_weakness_limit=1,
    )
    selected = ranked_papers_for_targets(targets, ranked)

    assert len(targets) == 2
    assert len(selected) == 1
    assert selected[0].paper.title == "Shared Support Paper"
    assert targets[0].shared_weakness_count == 2


def test_mark_targeted_full_text_statuses_records_fetch_result():
    ranked = [_ranked("Support Paper", 0.8)]
    weakness = WeaknessCard(
        weakness_statement="Weakness",
        evidence_quality="medium",
        support_papers=["Support Paper"],
    )
    coverage = EvidenceCoverageRecord(
        weakness_statement="Weakness",
        status="needs_targeted_full_text",
        support_papers=["Support Paper"],
        missing_support_full_text_papers=["Support Paper"],
    )
    targets = build_targeted_full_text_targets(
        weakness_cards=[weakness],
        evidence_coverage=[coverage],
        ranked=ranked,
        full_texts=[],
        limit=1,
        per_weakness_limit=1,
    )
    fetched = {"Support Paper": FullTextRecord(title="Support Paper", status="failed", error="timeout")}

    [updated] = mark_targeted_full_text_statuses(targets, fetched, list(fetched.values()))

    assert updated.status == "fetch_failed"
    assert updated.reason == "timeout"
