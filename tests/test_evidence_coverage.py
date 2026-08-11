from autoresearch.evidence_coverage import build_evidence_coverage, build_provider_health
from autoresearch.schema import (
    FullTextRecord,
    FullTextResolutionRecord,
    OpenAccessRecord,
    SourceStatus,
    TextSection,
    WeaknessCard,
)


def test_evidence_coverage_marks_ready_when_support_full_text_has_core_sections():
    card = WeaknessCard(
        weakness_statement="Metric coverage is weak.",
        evidence_quality="medium",
        checked_papers=8,
        support_papers=["Paper A", "Paper B"],
    )
    full_texts = [
        FullTextRecord(
            title="Paper A",
            status="ok",
            sections=[
                TextSection(heading="Methods", text="method"),
                TextSection(heading="Evaluation", text="metric"),
            ],
        ),
        FullTextRecord(
            title="Paper B",
            status="ok",
            sections=[
                TextSection(heading="Experiments", text="experiment"),
                TextSection(heading="Dataset", text="data"),
            ],
        ),
    ]

    [coverage] = build_evidence_coverage([card], full_texts)

    assert coverage.status == "ready_to_state_narrowly"
    assert coverage.support_full_text_papers == ["Paper A", "Paper B"]
    assert coverage.method_sections == 1
    assert coverage.experiment_sections == 2
    assert coverage.dataset_metric_sections == 2


def test_evidence_coverage_requires_targeted_support_full_text():
    card = WeaknessCard(
        weakness_statement="Temporal reasoning is weak.",
        evidence_quality="medium",
        checked_papers=8,
        support_papers=["Support Paper"],
    )
    full_texts = [
        FullTextRecord(title="Counter Paper", status="ok", sections=[TextSection(heading="Methods", text="x")]),
        FullTextRecord(title="Dataset Paper", status="ok", sections=[TextSection(heading="Results", text="x")]),
    ]

    [coverage] = build_evidence_coverage([card], full_texts)

    assert coverage.status == "needs_targeted_full_text"
    assert coverage.support_full_text_papers == []
    assert coverage.missing_support_full_text_papers == ["Support Paper"]


def test_provider_health_reports_configured_unpaywall_without_email(monkeypatch):
    monkeypatch.setenv("UNPAYWALL_EMAIL", "person@example.com")

    health = build_provider_health(
        source_statuses=[SourceStatus(source="openalex", query="q", status="failed", error="429")],
        full_text_resolutions=[
            FullTextResolutionRecord(
                title="Paper",
                status="ok",
                resolved_by=["europepmc_xml", "arxiv_source"],
                candidate_count=2,
            )
        ],
        full_texts=[FullTextRecord(title="Paper", status="ok", provider="europepmc_xml")],
        open_access_records=[OpenAccessRecord(title="Paper", status="ok", is_open_access=True)],
    )

    by_provider = {row.provider: row for row in health}
    assert by_provider["unpaywall"].status == "configured"
    assert "person@example.com" not in by_provider["unpaywall"].summary
    assert by_provider["openalex"].status == "limited"
