from autoresearch.autobench import build_autobench_report, write_autobench_report
from autoresearch.dashboard import write_dashboard
from autoresearch.schema import (
    EvidenceSnippet,
    FieldMap,
    GapEvidence,
    GapEvidenceStep,
    PaperCard,
    QueryPlan,
    SearchArtifacts,
    SourceStatus,
    WeaknessCard,
)


def _artifact(missing_dimensions: list[str], paper_cards: list[PaperCard]) -> SearchArtifacts:
    weakness = WeaknessCard(
        weakness_statement="The method is not evaluated under failure recovery conditions.",
        remaining_weakness="Failure-conditioned evaluation remains incomplete.",
        missing_parts=missing_dimensions,
    )
    return SearchArtifacts(
        topic="GUI agent failure recovery",
        query_plan=QueryPlan(
            topic="GUI agent failure recovery",
            queries=["GUI agent failure recovery benchmark"],
            perspectives=["benchmark"],
        ),
        source_statuses=[SourceStatus(source="arxiv", query="recovery", status="ok")],
        ranked_papers=[],
        paper_cards=paper_cards,
        field_map=FieldMap(),
        gaps=[
            GapEvidence(
                gap=weakness.weakness_statement,
                evidence_chain=[
                    GapEvidenceStep(
                        paper_title="RecoveryBench Paper",
                        missing_dimensions=missing_dimensions,
                    )
                ],
            )
        ],
        weakness_cards=[weakness],
    )


def _recovery_benchmark() -> PaperCard:
    evidence = EvidenceSnippet(
        paper_title="RecoveryBench Paper",
        source_url="https://example.com/recoverybench",
        claim="benchmark protocol",
        snippet="The method evaluates failure recovery with recovery success rate.",
        section="Methods",
    )
    return PaperCard(
        title="RecoveryBench Paper",
        url="https://example.com/recoverybench",
        task="failure recovery",
        method="replay failed GUI actions and measure recovery",
        dataset="RecoveryBench",
        metrics="recovery success rate",
        field_evidence={"dataset": evidence, "metrics": evidence},
        coverage_tags=["benchmark_or_evaluation"],
    )


def test_autobench_selects_existing_benchmark_with_paper_provenance():
    artifacts = _artifact(["failure recovery success rate"], [_recovery_benchmark()])

    report = build_autobench_report(artifacts)
    assessment = report.assessments[0]
    candidate = assessment.benchmark_candidates[0]

    assert assessment.decision == "existing_benchmark"
    assert assessment.route == "direct_benchmark_reuse"
    assert assessment.missing_evaluation_dimensions == []
    assert candidate.benchmark_name == "RecoveryBench"
    assert candidate.source_paper == "RecoveryBench Paper"
    assert candidate.source_evidence_status == "introduction_method"
    assert candidate.source_sections == ["Methods"]
    assert candidate.metrics == ["recovery success rate"]


def test_autobench_uses_base_adaptation_for_partial_coverage():
    artifacts = _artifact(
        ["failure recovery success rate", "unseen environment transfer"],
        [_recovery_benchmark()],
    )

    assessment = build_autobench_report(artifacts).assessments[0]

    assert assessment.decision == "partial_benchmark"
    assert assessment.route == "base_benchmark_adaptation"
    assert assessment.requires_benchmark_adaptation
    assert assessment.missing_evaluation_dimensions == ["unseen environment transfer"]
    assert "failure recovery success rate" in assessment.proven_parts


def test_autobench_requests_new_benchmark_when_no_paper_matches():
    artifacts = _artifact(["spatial audio harmony preservation"], [_recovery_benchmark()])

    assessment = build_autobench_report(artifacts).assessments[0]

    assert assessment.decision == "no_existing_benchmark"
    assert assessment.route == "new_benchmark_construction"
    assert assessment.requires_new_benchmark
    assert assessment.benchmark_candidates == []
    assert assessment.missing_evaluation_dimensions == ["spatial audio harmony preservation"]


def test_autobench_writes_json_markdown_and_dashboard(tmp_path):
    artifacts = _artifact(["failure recovery success rate"], [_recovery_benchmark()])
    artifacts.autobench = build_autobench_report(artifacts)

    artifacts.write_json(tmp_path)
    markdown_path = write_autobench_report(artifacts.autobench, tmp_path)
    dashboard_path = write_dashboard(artifacts, tmp_path)

    assert (tmp_path / "autobench.json").exists()
    assert "RecoveryBench Paper" in markdown_path.read_text(encoding="utf-8")
    assert "Weakness → Benchmark" in dashboard_path.read_text(encoding="utf-8")
