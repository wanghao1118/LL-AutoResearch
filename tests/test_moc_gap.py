from autoresearch.moc import GROUP_DIAGNOSIS, GROUP_TEMPORAL_LESION
from autoresearch.moc_gap import build_moc_gap_candidates, moc_candidates_to_gaps
from autoresearch.schema import EvidenceSnippet, MOCGroup, PaperCard, TopicMOC


def _snippet(title: str, claim: str) -> EvidenceSnippet:
    return EvidenceSnippet(
        paper_title=title,
        source_url="https://example.com",
        claim=claim,
        snippet=claim,
        section="abstract",
    )


def test_moc_gap_candidate_links_problem_space_to_support_and_counter():
    static_card = PaperCard(
        title="Static diagnosis VLM",
        url="https://example.com/static",
        problem="single-image diagnosis",
        task="diagnosis",
        method="medical VLM",
        missing_capability="temporal/change signal is not explicit; lesion/localization signal is not explicit",
        coverage_tags=["dataset_explicit", "metric_explicit"],
        evidence_snippets=[_snippet("Static diagnosis VLM", "single-image diagnosis evidence")],
    )
    temporal_lesion_card = PaperCard(
        title="Temporal lesion VLM",
        url="https://example.com/temporal",
        problem="lesion-level temporal reasoning",
        task="temporal lesion change",
        method="paired medical VLM",
        coverage_tags=[
            "temporal_or_change",
            "lesion_or_localization",
            "dataset_explicit",
            "metric_explicit",
        ],
        evidence_snippets=[_snippet("Temporal lesion VLM", "temporal lesion evidence")],
    )
    moc = TopicMOC(
        topic="medical VLM temporal lesion",
        paper_groups={
            GROUP_DIAGNOSIS: ["Static diagnosis VLM"],
            GROUP_TEMPORAL_LESION: ["Temporal lesion VLM"],
        },
        problem_spaces=[
            MOCGroup(
                name=GROUP_DIAGNOSIS,
                problem_space="single-study medical VLM diagnosis",
                representative_papers=["Static diagnosis VLM"],
                shared_assumptions=[
                    "single-study recognition performance transfers to paired workflows"
                ],
                covered_capabilities=["single-study image understanding"],
                missing_capabilities=[
                    "Image-level diagnosis/VQA may not test temporal comparison or lesion-level grounding."
                ],
            ),
            MOCGroup(
                name=GROUP_TEMPORAL_LESION,
                problem_space="lesion-level temporal change reasoning",
                representative_papers=["Temporal lesion VLM"],
                shared_assumptions=["temporal and lesion signals are coupled"],
                covered_capabilities=[
                    "temporal or change-oriented signals",
                    "lesion, finding, mask, or localization signals",
                ],
                missing_capabilities=["paired-study benchmark protocol is still under-specified"],
            ),
        ],
    )

    candidates = build_moc_gap_candidates(
        topic_moc=moc,
        cards=[static_card, temporal_lesion_card],
    )
    diagnosis_candidate = next(
        candidate for candidate in candidates if candidate.moc_group == GROUP_DIAGNOSIS
    )

    assert diagnosis_candidate.support_papers == ["Static diagnosis VLM"]
    assert diagnosis_candidate.counter_papers == ["Temporal lesion VLM"]
    assert diagnosis_candidate.missing_capabilities

    [gap] = [
        gap
        for gap in moc_candidates_to_gaps(candidates, total_papers=2)
        if gap.moc_group == GROUP_DIAGNOSIS
    ]
    assert gap.source == "moc_gap_candidate"
    assert gap.moc_candidate_id == diagnosis_candidate.candidate_id
    assert gap.paper_judgments[0].role == "support"
