from pathlib import Path

from typer.testing import CliRunner

from autoresearch.bench.matcher import infer_requirements, match_benchmarks
from autoresearch.bench.report import write_bench_card_report, write_bench_evidence_block
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
