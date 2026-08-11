from pathlib import Path

from typer.testing import CliRunner

from autoresearch.bench.matcher import infer_requirements, match_benchmarks
from autoresearch.bench.moc import (
    apply_bench_moc_review,
    build_bench_moc_review_packet,
    generate_bench_moc,
)
from autoresearch.bench.report import (
    write_bench_card_report,
    write_bench_evidence_block,
    write_bench_moc,
    write_bench_moc_review_packet,
)
from autoresearch.bench.schema import (
    BenchmarkWeaknessReview,
    BenchMOCReviewResult,
    BenchProblemSpaceReview,
)
from autoresearch.bench.understand import search_benchmarks, understand_benchmark
from autoresearch.cli import app


def test_medical_temporal_weakness_matches_partial_benches_and_needs_new_benchmark():
    block = match_benchmarks(
        "medical VLM lacks lesion-level temporal reasoning",
        limit=5,
    )

    names = [item.bench_name for item in block.related_benches]

    assert "DeepLesion" in names
    assert "MIMIC-CXR" in names or "RadGraph" in names
    assert block.need_new_benchmark is True
    assert "temporal / change evaluation" in block.remaining_evaluation_gap

    deeplesion = next(item for item in block.related_benches if item.bench_name == "DeepLesion")
    assert deeplesion.verdict == "partial"
    assert "lesion-level evidence" in deeplesion.covered_requirements
    assert "temporal / change evaluation" in deeplesion.missing_requirements


def test_gui_failure_weakness_surfaces_robustness_and_comparability_benches():
    block = match_benchmarks(
        "GUI agent lacks cross-benchmark failure diagnostic evaluation",
        limit=6,
    )

    names = [item.bench_name for item in block.related_benches]

    assert "GUI-RobustEval" in names
    assert "BrowserGym" in names
    assert block.need_new_benchmark is True

    robust = next(item for item in block.related_benches if item.bench_name == "GUI-RobustEval")
    assert robust.verdict == "partial"
    assert "failure / recovery diagnosis" in robust.covered_requirements
    assert "cross-benchmark comparability" in robust.missing_requirements


def test_finance_workflow_weakness_matches_fab_and_gdpval():
    block = match_benchmarks(
        "finance agent benchmarks lack reproducible real-world workflow scoring",
        limit=6,
    )

    names = [item.bench_name for item in block.related_benches]

    assert "FAB" in names
    assert "GDPval" in names
    assert block.need_new_benchmark is True
    assert any("复现" in weakness for item in block.related_benches for weakness in item.bench_weaknesses)


def test_requirement_inference():
    requirements = infer_requirements("medical VLM lesion temporal benchmark")

    assert "medical" in requirements
    assert "VLM / multimodal evaluation" in requirements
    assert "lesion-level evidence" in requirements
    assert "temporal / change evaluation" in requirements


def test_write_bench_evidence_block(tmp_path: Path):
    block = match_benchmarks("medical VLM lacks lesion-level temporal reasoning", limit=3)

    json_path, md_path = write_bench_evidence_block(block, output_root=tmp_path)

    assert json_path.exists()
    assert md_path.exists()
    assert "Bench 证据块" in md_path.read_text(encoding="utf-8")
    assert "是否需要新 benchmark" in md_path.read_text(encoding="utf-8")


def test_understand_seed_benchmark_enriches_tags_and_sources():
    bench = understand_benchmark("GDPval")

    assert bench.bench_name == "GDPval"
    assert "official" in bench.tags
    assert bench.task_goal
    assert bench.source_urls


def test_write_bench_card_report(tmp_path: Path):
    bench = understand_benchmark("FAB")

    json_path, md_path = write_bench_card_report(bench, output_root=tmp_path)
    text = md_path.read_text(encoding="utf-8")

    assert json_path.exists()
    assert md_path.exists()
    assert "Bench 理解报告" in text
    assert "被哪些基座模型" in text
    assert "适合验证的 weakness" in text


def test_search_benchmarks_by_keyword():
    results = search_benchmarks("openai workflow", limit=5)
    names = [item.bench_name for item in results]

    assert "GDPval" in names
    assert any("openai" in item.matched_keywords for item in results)


def test_generate_bench_moc_contains_problem_spaces_and_weaknesses():
    moc = generate_bench_moc()
    space_names = [space.name for space in moc.problem_spaces]
    weakness_claims = [weakness.claim for weakness in moc.benchmark_level_weaknesses]

    assert "真实工作流评估" in space_names
    assert "GUI Agent 任务完成评估" in space_names
    assert any("跨 Bench 分数不能直接横向比较" in claim for claim in weakness_claims)
    assert any("失败" in claim for claim in weakness_claims)


def test_bench_moc_relations_capture_gui_and_workflow_links():
    moc = generate_bench_moc()
    relation_keys = {
        (relation.source_bench, relation.target_bench, relation.relation_type) for relation in moc.relations
    }

    assert any(
        {"OSWorld", "AndroidWorld"} == {source, target} and relation_type == "same_capability"
        for source, target, relation_type in relation_keys
    )
    assert any(
        "GUI-RobustEval" in {source, target} and relation_type == "complementary"
        for source, target, relation_type in relation_keys
    )


def test_write_bench_moc_and_review_packet(tmp_path: Path):
    moc = generate_bench_moc()
    moc_json, moc_md = write_bench_moc(moc, output_root=tmp_path)
    packet = build_bench_moc_review_packet(moc)
    packet_md, packet_json, template_json = write_bench_moc_review_packet(packet, output_root=tmp_path)

    assert moc_json.exists()
    assert moc_md.exists()
    assert "Bench MOC" in moc_md.read_text(encoding="utf-8")
    assert packet_md.exists()
    assert packet_json.exists()
    assert template_json.exists()
    assert "problem_space_reviews" in template_json.read_text(encoding="utf-8")


def test_apply_bench_moc_review_refines_problem_space_and_weakness():
    moc = generate_bench_moc()
    original_claim = moc.benchmark_level_weaknesses[0].claim
    review = BenchMOCReviewResult(
        overall_verdict="keep-with-revision",
        summary="MOC 初稿可用，但问题空间命名需要更精确。",
        problem_space_reviews=[
            BenchProblemSpaceReview(
                space_id="real_world_workflow",
                verdict="keep",
                rename_to="真实工作流产物与任务完成评估",
                reason="OSWorld 更偏 GUI 操作，应作为相邻证据阅读。",
            )
        ],
        weakness_reviews=[
            BenchmarkWeaknessReview(
                claim=original_claim,
                verdict="keep",
                revision="跨 workflow Bench 的分数不能直接横向比较，因为任务、指标和 judge 口径不统一。",
                evidence=["metric_mismatch relations"],
                confidence="high",
            )
        ],
    )

    reviewed = apply_bench_moc_review(moc, review)

    assert reviewed.generation_status == "codex-reviewed"
    assert reviewed.review_summary == review.summary
    assert any(space.name == "真实工作流产物与任务完成评估" for space in reviewed.problem_spaces)
    assert reviewed.benchmark_level_weaknesses[0].review_status == "codex-reviewed"


def test_bench_match_cli(tmp_path: Path):
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "bench",
            "match",
            "medical VLM lacks lesion-level temporal reasoning",
            "--output-root",
            str(tmp_path),
            "--limit",
            "3",
        ],
    )

    assert result.exit_code == 0
    assert "Bench evidence block" in result.output
    assert list(tmp_path.glob("bench-match-*/bench_evidence_block.md"))


def test_bench_understand_cli(tmp_path: Path):
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "bench",
            "understand",
            "GDPval",
            "--output-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert "Bench understanding report" in result.output
    assert list(tmp_path.glob("bench-understand-*/bench_report.md"))


def test_bench_search_cli():
    runner = CliRunner()

    result = runner.invoke(app, ["bench", "search", "finance workflow"])

    assert result.exit_code == 0
    assert "Bench search" in result.output
    assert "FAB" in result.output


def test_bench_moc_cli_roundtrip(tmp_path: Path):
    runner = CliRunner()

    moc_result = runner.invoke(app, ["bench", "moc", "--output-root", str(tmp_path)])
    assert moc_result.exit_code == 0
    assert "Bench MOC" in moc_result.output

    packet_result = runner.invoke(app, ["bench", "moc-packet", "--output-root", str(tmp_path)])
    assert packet_result.exit_code == 0
    assert list(tmp_path.glob("bench-moc/bench_moc_review_packet.md"))

    review = BenchMOCReviewResult(
        overall_verdict="keep",
        summary="测试写回。",
        problem_space_reviews=[
            BenchProblemSpaceReview(space_id="real_world_workflow", verdict="keep", rename_to="真实工作流评估")
        ],
    )
    review_path = tmp_path / "bench_moc_review_result.json"
    review_path.write_text(review.model_dump_json(indent=2), encoding="utf-8")

    apply_result = runner.invoke(
        app,
        [
            "bench",
            "moc-apply",
            str(review_path),
            "--output-root",
            str(tmp_path),
        ],
    )

    assert apply_result.exit_code == 0
    assert "applied Bench MOC Codex Review" in apply_result.output
    assert list(tmp_path.glob("bench-moc/bench_moc_reviewed.md"))
