from __future__ import annotations

import re
from pathlib import Path

from .schema import (
    AutoBenchReport,
    BenchmarkCandidateEvidence,
    EvidenceSnippet,
    GapEvidence,
    PaperCard,
    SearchArtifacts,
    WeaknessBenchmarkAssessment,
    WeaknessCard,
)

_EMPTY_VALUES = {"", "n/a", "na", "none", "not explicit", "not available", "unknown"}
_SECTION_MARKERS = ("introduction", "intro", "method", "approach", "methodology")
_GENERIC_TERMS = {
    "benchmark",
    "capability",
    "dataset",
    "evaluation",
    "explicit",
    "method",
    "metric",
    "missing",
    "paper",
    "performance",
    "system",
    "task",
    "with",
    "without",
}


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = value.strip()
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


def _is_explicit(value: str) -> bool:
    return value.strip().casefold() not in _EMPTY_VALUES


def _terms(value: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]+", value.casefold())
    return {token for token in tokens if len(token) > 2 and token not in _GENERIC_TERMS}


def _dimension_matches(dimension: str, candidate_text: str) -> bool:
    normalized_dimension = " ".join(re.findall(r"[a-z0-9\u4e00-\u9fff]+", dimension.casefold()))
    normalized_candidate = " ".join(
        re.findall(r"[a-z0-9\u4e00-\u9fff]+", candidate_text.casefold())
    )
    if normalized_dimension and normalized_dimension in normalized_candidate:
        return True
    required = _terms(dimension)
    offered = _terms(candidate_text)
    if not required or not offered:
        return False
    overlap = required & offered
    minimum_hits = 1 if len(required) <= 2 else 2
    return len(overlap) >= minimum_hits and len(overlap) / len(required) >= 0.34


def _split_metrics(value: str) -> list[str]:
    if not _is_explicit(value):
        return []
    return _unique(re.split(r"\s*(?:,|;|\|| / )\s*", value))


def _relevant_evidence(card: PaperCard) -> tuple[list[EvidenceSnippet], list[str], str]:
    evidence = [*card.field_evidence.values(), *card.evidence_snippets]
    deduplicated: list[EvidenceSnippet] = []
    seen: set[tuple[str, str, str]] = set()
    for snippet in evidence:
        key = (snippet.paper_title, snippet.section, snippet.snippet)
        if key not in seen:
            seen.add(key)
            deduplicated.append(snippet)

    intro_method = [
        snippet
        for snippet in deduplicated
        if any(marker in snippet.section.casefold() for marker in _SECTION_MARKERS)
    ]
    if intro_method:
        selected = intro_method[:6]
        return (
            selected,
            _unique([row.section or "introduction_or_method" for row in selected]),
            "introduction_method",
        )
    if deduplicated:
        selected = deduplicated[:4]
        return (
            selected,
            _unique([row.section or "unspecified_section" for row in selected]),
            "other_paper_section",
        )
    return [], ["structured_paper_card"], "structured_paper_card"


def _benchmark_candidate(
    card: PaperCard, dimensions: list[str]
) -> BenchmarkCandidateEvidence | None:
    dataset = card.dataset.strip() if _is_explicit(card.dataset) else ""
    title_signal = bool(
        re.search(r"\b(?:benchmark|dataset|suite|evaluation)\b", card.title, re.IGNORECASE)
    )
    tag_signal = any(
        "benchmark" in tag.casefold() or "evaluation" in tag.casefold()
        for tag in card.coverage_tags
    )
    if not dataset and not title_signal and not tag_signal:
        return None

    snippets, sections, evidence_status = _relevant_evidence(card)
    metrics = _split_metrics(card.metrics)
    candidate_text = " ".join(
        [
            card.title,
            card.problem,
            card.task,
            card.method,
            card.dataset,
            card.metrics,
            card.claimed_contribution,
            card.relation_to_topic,
            " ".join(card.coverage_tags),
            " ".join(f"{row.claim} {row.snippet}" for row in snippets),
        ]
    )
    covered = [
        dimension for dimension in dimensions if _dimension_matches(dimension, candidate_text)
    ]
    if not covered:
        return None

    ratio = len(covered) / max(len(dimensions), 1)
    benchmark_name = dataset or card.title
    reason = f"覆盖 {len(covered)}/{len(dimensions)} 个 Weakness 评估维度"
    if metrics:
        reason += f"；论文卡片给出指标：{', '.join(metrics)}"
    return BenchmarkCandidateEvidence(
        benchmark_name=benchmark_name,
        source_paper=card.title,
        source_url=card.url,
        dataset=dataset,
        task=card.task,
        metrics=metrics,
        covered_dimensions=covered,
        source_sections=sections,
        source_evidence_status=evidence_status,
        evidence_snippets=snippets,
        coverage_ratio=round(ratio, 4),
        coverage_reason=reason,
    )


def _required_dimensions(
    weakness: WeaknessCard,
    gap: GapEvidence | None,
    artifacts: SearchArtifacts,
) -> list[str]:
    dimensions = list(weakness.missing_parts)
    if gap:
        for step in gap.evidence_chain:
            dimensions.extend(step.missing_dimensions)

    weakness_text = " ".join(
        [weakness.weakness_statement, weakness.remaining_weakness, *weakness.missing_parts]
    )
    if artifacts.domain_profile:
        for capability in artifacts.domain_profile.capability_dimensions:
            capability_text = " ".join([capability.name, *capability.keywords])
            if _terms(weakness_text) & _terms(capability_text):
                dimensions.append(capability.name)

    if not dimensions:
        dimensions.append(
            weakness.remaining_weakness or weakness.weakness_statement or weakness.broad_problem
        )
    return _unique(dimensions)


def _construction_plan(route: str, missing: list[str]) -> list[str]:
    if route == "direct_benchmark_reuse":
        return [
            "复用候选论文给出的官方任务、数据划分与指标定义。",
            "逐项报告每个 Benchmark 覆盖的 Weakness 维度，避免只汇报聚合分数。",
            "保留论文来源、URL 和 Introduction/Method 证据位置以便复核。",
        ]
    if route == "base_benchmark_adaptation":
        return [
            "保留最接近候选 Benchmark 的原始任务语义和官方指标作为基线。",
            "把缺失维度加入独立 challenge split 或评估 wrapper：" + "；".join(missing),
            "冻结新划分并分别报告官方分数与新增维度分数。",
            "加入原 Benchmark、改造版本和目标方法之间的成对对比。",
        ]
    return [
        "把每个缺失评估维度定义为可观测变量：" + "；".join(missing),
        "从已有论文任务中抽取输入、输出、环境和失败条件，形成样本设计矩阵。",
        "建立数据构造、标注、泄漏检查、难度分层与冻结测试集流程。",
        "同时报告任务成功、维度专用指标、鲁棒性和失败类型分布。",
    ]


def build_autobench_report(artifacts: SearchArtifacts) -> AutoBenchReport:
    """Map each AutoSearch weakness to evidence-backed benchmark coverage.

    The module first derives required evaluation dimensions from WeaknessCard and
    its corresponding Gap evidence chain. It then treats only benchmarks or
    datasets named by papers in the current AutoResearch run as candidates,
    records their paper/section provenance, and chooses one of three routes:
    direct reuse, base-benchmark adaptation, or new benchmark construction.
    """

    assessments: list[WeaknessBenchmarkAssessment] = []
    for index, weakness in enumerate(artifacts.weakness_cards):
        gap = artifacts.gaps[index] if index < len(artifacts.gaps) else None
        dimensions = _required_dimensions(weakness, gap, artifacts)
        candidates = [
            candidate
            for card in artifacts.paper_cards
            if (candidate := _benchmark_candidate(card, dimensions)) is not None
        ]
        candidates.sort(
            key=lambda row: (
                -row.coverage_ratio,
                not bool(row.dataset),
                not bool(row.metrics),
                row.benchmark_name.casefold(),
            )
        )
        candidates = candidates[:6]
        proven = _unique(
            [dimension for candidate in candidates for dimension in candidate.covered_dimensions]
        )
        missing = [dimension for dimension in dimensions if dimension not in proven]
        fully_specified = any(
            candidate.dataset and candidate.metrics and candidate.source_url
            for candidate in candidates
        )

        if not missing and candidates and fully_specified:
            decision = "existing_benchmark"
            route = "direct_benchmark_reuse"
            rationale = "现有论文中的 Benchmark 组合覆盖全部所需维度，并给出数据集、指标和来源。"
        elif candidates:
            decision = "partial_benchmark"
            route = "base_benchmark_adaptation"
            rationale = "现有 Benchmark 只能证明部分 Weakness，需要在最接近的基准上补充评估维度。"
        else:
            decision = "no_existing_benchmark"
            route = "new_benchmark_construction"
            rationale = "当前论文证据中没有能覆盖该 Weakness 的现成 Benchmark，需要构造新评估。"

        assessments.append(
            WeaknessBenchmarkAssessment(
                weakness_statement=weakness.weakness_statement,
                decision=decision,
                route=route,
                required_dimensions=dimensions,
                benchmark_candidates=candidates,
                proven_parts=proven,
                missing_evaluation_dimensions=missing,
                requires_benchmark_adaptation=route == "base_benchmark_adaptation",
                requires_new_benchmark=route == "new_benchmark_construction",
                rationale=rationale,
                construction_plan=_construction_plan(route, missing),
            )
        )

    return AutoBenchReport(
        topic=artifacts.topic,
        assessments=assessments,
        existing_count=sum(row.decision == "existing_benchmark" for row in assessments),
        partial_count=sum(row.decision == "partial_benchmark" for row in assessments),
        new_benchmark_count=sum(row.decision == "no_existing_benchmark" for row in assessments),
    )


def ensure_autobench_report(artifacts: SearchArtifacts) -> SearchArtifacts:
    if artifacts.autobench is None:
        artifacts.autobench = build_autobench_report(artifacts)
    return artifacts


def write_autobench_report(report: AutoBenchReport, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# AutoBench Report: {report.topic}",
        "",
        "AutoBench 判断每个 Weakness 是否已有 Benchmark 可证明，并保留来源论文与章节证据。",
        "",
        f"- 现成 Benchmark：{report.existing_count}",
        f"- 部分覆盖、需要改造：{report.partial_count}",
        f"- 无现成 Benchmark、需要新建：{report.new_benchmark_count}",
        f"- 证据范围：`{report.source_scope}`",
        "",
    ]
    for index, assessment in enumerate(report.assessments, start=1):
        lines.extend(
            [
                f"## Weakness {index}: {assessment.weakness_statement}",
                "",
                f"- 判断：`{assessment.decision}`",
                f"- 路由：`{assessment.route}`",
                f"- 原因：{assessment.rationale}",
                f"- 所需评估维度：{'；'.join(assessment.required_dimensions) or '未识别'}",
                f"- 已能证明：{'；'.join(assessment.proven_parts) or '无'}",
                f"- 仍缺维度：{'；'.join(assessment.missing_evaluation_dimensions) or '无'}",
                "",
                "### 可用 Benchmark 与论文依据",
                "",
            ]
        )
        if not assessment.benchmark_candidates:
            lines.append("- 当前论文集合中没有匹配候选。")
        for candidate in assessment.benchmark_candidates:
            lines.extend(
                [
                    f"- **{candidate.benchmark_name}**",
                    f"  - 来源论文：[{candidate.source_paper}]({candidate.source_url})",
                    f"  - 来源章节：{', '.join(candidate.source_sections)}",
                    f"  - 证据状态：`{candidate.source_evidence_status}`",
                    f"  - 任务：{candidate.task or 'not explicit'}",
                    f"  - 指标：{', '.join(candidate.metrics) or 'not explicit'}",
                    f"  - 能证明：{'；'.join(candidate.covered_dimensions)}",
                    f"  - 覆盖说明：{candidate.coverage_reason}",
                ]
            )
        lines.extend(["", "### 下一步", ""])
        lines.extend(
            f"{step}. {item}" for step, item in enumerate(assessment.construction_plan, start=1)
        )
        lines.append("")

    path = output_dir / "autobench.md"
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path
