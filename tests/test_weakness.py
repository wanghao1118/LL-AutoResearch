from autoresearch.schema import (
    EvidenceSnippet,
    GapEvidence,
    GapEvidenceStep,
    SourceStatus,
)
from autoresearch.weakness import build_weakness_cards


def test_build_weakness_cards_narrows_when_counter_evidence_exists():
    gap = GapEvidence(
        gap="Medical VLM: lesion-level temporal reasoning is weakly covered.",
        support_count=2,
        counter_count=1,
        unclear_count=0,
        total_papers=3,
        counter_ratio=1 / 3,
        evidence=[
            EvidenceSnippet(
                paper_title="Static Medical VLM",
                source_url="https://example.com/static",
                claim="candidate work does not clearly combine temporal/change reasoning with lesion-level localization",
                snippet="We evaluate single-image medical VQA.",
                section="abstract",
            )
        ],
        counter_evidence=[
            EvidenceSnippet(
                paper_title="Longitudinal Lesion Model",
                source_url="https://example.com/longitudinal",
                claim="paper contains both temporal/change and lesion/localization signals",
                snippet="We track lesions across follow-up scans.",
                section="abstract",
            )
        ],
        evidence_chain=[
            GapEvidenceStep(
                paper_title="Static Medical VLM",
                role="support",
                claim="missing temporal lesion evidence",
                missing_dimensions=["no explicit temporal/change signal"],
            ),
            GapEvidenceStep(
                paper_title="Longitudinal Lesion Model",
                role="counter",
                claim="paper contains temporal lesion evidence",
            ),
        ],
    )

    cards = build_weakness_cards(
        topic="medical VLM temporal lesion change analysis",
        gaps=[gap],
        topic_moc=None,
        comparison=None,
        full_texts=[],
        source_statuses=[
            SourceStatus(source="openalex", query="medical VLM", status="ok", raw_count=2),
            SourceStatus(source="pubmed", query="medical VLM", status="ok", raw_count=1),
        ],
        profile=None,
    )

    card = cards[0]

    assert card.verdict == "partially_valid"
    assert card.support_papers == ["Static Medical VLM"]
    assert card.counter_papers == ["Longitudinal Lesion Model"]
    assert "no explicit temporal/change signal" in card.missing_parts
    assert card.covered_parts
    assert "partially covered" in card.remaining_weakness
