from __future__ import annotations

from pathlib import Path

from ..utils import slugify
from .schema import BenchCard, BenchEvidenceBlock, BenchMOC, BenchMOCReviewPacket

VERDICT_ZH = {
    "sufficient": "基本可用",
    "partial": "部分相关",
    "insufficient": "不足以验证",
}

REQUIREMENT_ZH = {
    "medical": "医学领域",
    "VLM / multimodal evaluation": "VLM / 多模态评估",
    "lesion-level evidence": "病灶级证据",
    "temporal / change evaluation": "时序 / 变化评估",
    "GUI agent evaluation": "GUI Agent 评估",
    "failure / recovery diagnosis": "失败 / 恢复诊断",
    "cross-benchmark comparability": "跨 Bench 可比性",
    "finance domain": "金融领域",
    "real-world workflow": "真实工作流",
    "reproducible scoring": "可复现评分",
    "target capability evaluation": "目标能力评估",
}

SOURCE_TYPE_ZH = {
    "dataset": "数据集",
    "leaderboard": "榜单",
    "official": "官方",
    "paper": "论文",
    "project": "项目",
}

STATUS_ZH = {
    "seed": "种子库记录",
}

CONFIDENCE_ZH = {
    "high": "高",
    "medium": "中",
    "low": "低",
}


def render_bench_evidence_markdown(block: BenchEvidenceBlock) -> str:
    lines = [
        f"# Bench 证据块：{block.research_weakness}",
        "",
        "## 结论",
        "",
        f"- 是否需要新 benchmark：{'是' if block.need_new_benchmark else '不一定'}",
        f"- 剩余评估缺口：{_translate_requirement_text(block.remaining_evaluation_gap)}",
        f"- 推荐方向：{_translate_requirement_text(block.recommended_benchmark_direction)}",
        "",
        "## 相关 Bench",
        "",
    ]
    for index, item in enumerate(block.related_benches, start=1):
        lines.extend(
            [
                f"### {index}. {item.bench_name}",
                "",
                f"- 判断：{VERDICT_ZH.get(item.verdict, item.verdict)}",
                f"- 相关性分数：{item.relevance_score}",
                f"- 命中关键词：{_join(item.matched_terms)}",
                f"- 已覆盖需求：{_join_requirements(item.covered_requirements)}",
                f"- 缺失需求：{_join_requirements(item.missing_requirements)}",
                f"- 判断理由：{_translate_requirement_text(item.rationale)}",
                f"- 来源：{_join(item.source_urls)}",
                "",
                "Bench 自身弱点:",
                "",
                *[f"- {weakness}" for weakness in item.bench_weaknesses[:6]],
                "",
            ]
        )
    lines.extend(
        [
            "## 分类列表",
            "",
            f"- 基本可用：{_join(block.sufficient_benches)}",
            f"- 部分相关：{_join(block.partial_benches)}",
            f"- 不足以验证：{_join(block.insufficient_benches)}",
            "",
            "## 备注",
            "",
            *[f"- {note}" for note in block.notes],
            "",
        ]
    )
    return "\n".join(lines)


def write_bench_evidence_block(
    block: BenchEvidenceBlock,
    output_root: Path = Path("outputs"),
) -> tuple[Path, Path]:
    output_dir = output_root / f"bench-match-{slugify(block.research_weakness)}"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "bench_evidence_block.json"
    md_path = output_dir / "bench_evidence_block.md"
    json_path.write_text(block.model_dump_json(indent=2), encoding="utf-8")
    md_path.write_text(render_bench_evidence_markdown(block), encoding="utf-8")
    return json_path, md_path


def render_bench_card_markdown(bench: BenchCard) -> str:
    source_types = sorted({source.source_type for source in bench.source_urls})
    keywords = _dedupe([*bench.keywords, *bench.tags])[:24]
    lines = [
        f"# Bench 理解报告：{bench.bench_name}",
        "",
        "## 1. 核心定位",
        "",
        f"- 别名：{_join(bench.aliases)}",
        f"- 领域：{_join(bench.domain)}",
        f"- 关键词 / 标签：{_join(keywords)}",
        f"- 来源类型：{_join([SOURCE_TYPE_ZH.get(value, value) for value in source_types])}",
        f"- 理解状态：{STATUS_ZH.get(bench.understanding_status, bench.understanding_status)}",
        f"- 来源可信度：{CONFIDENCE_ZH.get(bench.source_confidence, bench.source_confidence)}",
        "",
        "## 2. 它具体测什么",
        "",
        f"- 评估能力：{_join(bench.evaluated_capabilities)}",
        f"- 任务目标：{bench.task_goal or '待从论文或数据集说明中补充'}",
        f"- 任务形式：{bench.task_format or '待补充'}",
        f"- 输入模态：{_join(bench.input_modalities)}",
        f"- 输出形式：{bench.output_format or '待补充'}",
        "",
        "## 3. Case 和数据结构",
        "",
        "典型 case:",
        "",
        *_bullet_lines(bench.case_examples, empty="当前 seed card 尚未记录具体 case，需要后续从 HF datasets 或论文 appendix 抽样。"),
        "",
        "数据字段:",
        "",
        *_dict_lines(bench.dataset_schema, empty="当前 seed card 尚未记录字段 schema。"),
        "",
        "## 4. 指标、评分和 judge",
        "",
        f"- 指标：{_join(bench.metrics)}",
        f"- 评分协议：{bench.scoring_protocol or '待补充'}",
        f"- Judge 类型：{bench.judge_type or '待补充'}",
        "",
        "## 5. 被哪些基座模型 / 组织打过",
        "",
        *_model_result_lines(bench),
        "",
        "## 6. 对 AutoResearch 的作用",
        "",
        "适合验证的 weakness:",
        "",
        *_bullet_lines(bench.suitable_for),
        "",
        "不适合直接验证的 weakness:",
        "",
        *_bullet_lines(bench.not_suitable_for),
        "",
        "Bench 自身 weakness:",
        "",
        *_bullet_lines(bench.weaknesses),
        "",
        "## 7. 来源",
        "",
        *_source_lines(bench),
        "",
    ]
    return "\n".join(lines)


def write_bench_card_report(
    bench: BenchCard,
    output_root: Path = Path("outputs"),
) -> tuple[Path, Path]:
    output_dir = output_root / f"bench-understand-{slugify(bench.bench_name)}"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "bench_card.json"
    md_path = output_dir / "bench_report.md"
    json_path.write_text(bench.model_dump_json(indent=2), encoding="utf-8")
    md_path.write_text(render_bench_card_markdown(bench), encoding="utf-8")
    return json_path, md_path


def render_bench_moc_markdown(moc: BenchMOC) -> str:
    lines = [
        f"# {moc.title}",
        "",
        "## 状态",
        "",
        f"- 生成状态：{moc.generation_status}",
        f"- 问题空间数量：{len(moc.problem_spaces)}",
        f"- Bench 关系数量：{len(moc.relations)}",
        f"- Benchmark-level weakness 数量：{len(moc.benchmark_level_weaknesses)}",
    ]
    if moc.review_summary:
        lines.extend(["", f"- Codex Review 总结：{moc.review_summary}"])
    lines.extend(["", "## 1. 问题空间", ""])
    for index, space in enumerate(moc.problem_spaces, start=1):
        lines.extend(
            [
                f"### {index}. {space.name}",
                "",
                f"- ID：`{space.space_id}`",
                f"- 描述：{space.description}",
                f"- 置信度：{CONFIDENCE_ZH.get(space.confidence, space.confidence)}",
                f"- 核心 Bench：{_join(space.core_benches)}",
                f"- 相邻 Bench：{_join(space.adjacent_benches)}",
                f"- 共享能力：{_join(space.shared_capabilities)}",
                f"- 共享指标：{_join(space.shared_metrics)}",
                "",
                "共同弱点 / 需要核验:",
                "",
                *_bullet_lines(space.common_weaknesses),
                "",
            ]
        )
    lines.extend(["## 2. Bench 关系", ""])
    for relation in moc.relations:
        lines.extend(
            [
                f"### {relation.source_bench} -> {relation.target_bench}",
                "",
                f"- 关系类型：{RELATION_TYPE_ZH.get(relation.relation_type, relation.relation_type)}",
                f"- 置信度：{CONFIDENCE_ZH.get(relation.confidence, relation.confidence)}",
                f"- 判断理由：{relation.rationale}",
                "",
                "证据字段:",
                "",
                *_bullet_lines(relation.evidence),
                "",
            ]
        )
    lines.extend(["## 3. Benchmark-level Weakness", ""])
    for weakness in moc.benchmark_level_weaknesses:
        lines.extend(
            [
                f"### {weakness.claim}",
                "",
                f"- 类型：{WEAKNESS_TYPE_ZH.get(weakness.weakness_type, weakness.weakness_type)}",
                f"- 严重程度：{CONFIDENCE_ZH.get(weakness.severity, weakness.severity)}",
                f"- 审查状态：{weakness.review_status}",
                f"- 涉及 Bench：{_join(weakness.involved_benches)}",
                "",
                "支持证据:",
                "",
                *_bullet_lines(weakness.evidence),
                "",
                "反证 / 限定:",
                "",
                *_bullet_lines(weakness.counter_evidence),
                "",
            ]
        )
    lines.extend(["## 4. 备注", "", *_bullet_lines(moc.notes), ""])
    return "\n".join(lines)


def write_bench_moc(
    moc: BenchMOC,
    output_root: Path = Path("outputs"),
    *,
    reviewed: bool = False,
) -> tuple[Path, Path]:
    output_dir = output_root / "bench-moc"
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = "bench_moc_reviewed" if reviewed else "bench_moc"
    json_path = output_dir / f"{stem}.json"
    md_path = output_dir / f"{stem}.md"
    json_path.write_text(moc.model_dump_json(indent=2), encoding="utf-8")
    md_path.write_text(render_bench_moc_markdown(moc), encoding="utf-8")
    return json_path, md_path


def render_bench_moc_review_packet_markdown(packet: BenchMOCReviewPacket) -> str:
    lines = [
        "# Bench MOC Codex Review Packet",
        "",
        "## 审查说明",
        "",
        *_bullet_lines(packet.instructions),
        "",
        "## 审查问题",
        "",
        *_bullet_lines(packet.review_questions),
        "",
        "## 待审查 MOC 摘要",
        "",
        f"- 标题：{packet.moc.title}",
        f"- 问题空间：{len(packet.moc.problem_spaces)}",
        f"- Bench 关系：{len(packet.moc.relations)}",
        f"- Benchmark-level weakness：{len(packet.moc.benchmark_level_weaknesses)}",
        "",
        "## 问题空间",
        "",
    ]
    for space in packet.moc.problem_spaces:
        lines.extend(
            [
                f"### {space.name} (`{space.space_id}`)",
                "",
                f"- 核心 Bench：{_join(space.core_benches)}",
                f"- 相邻 Bench：{_join(space.adjacent_benches)}",
                f"- 共同弱点：{_join(space.common_weaknesses)}",
                "",
            ]
        )
    lines.extend(["## Benchmark-level Weakness", ""])
    for weakness in packet.moc.benchmark_level_weaknesses:
        lines.extend(
            [
                f"### {weakness.claim}",
                "",
                f"- 涉及 Bench：{_join(weakness.involved_benches)}",
                f"- 证据：{_join(weakness.evidence)}",
                f"- 反证 / 限定：{_join(weakness.counter_evidence)}",
                "",
            ]
        )
    lines.extend(
        [
            "## 输出模板",
            "",
            (
                "请填写同目录下的 `bench_moc_review_result.template.json`，再用 "
                "`autoresearch bench moc-apply <review-result.json>` 写回。"
            ),
            "",
        ]
    )
    return "\n".join(lines)


def write_bench_moc_review_packet(
    packet: BenchMOCReviewPacket,
    output_root: Path = Path("outputs"),
) -> tuple[Path, Path, Path]:
    output_dir = output_root / "bench-moc"
    output_dir.mkdir(parents=True, exist_ok=True)
    packet_json = output_dir / "bench_moc_review_packet.json"
    packet_md = output_dir / "bench_moc_review_packet.md"
    template_json = output_dir / "bench_moc_review_result.template.json"
    packet_json.write_text(packet.model_dump_json(indent=2), encoding="utf-8")
    packet_md.write_text(render_bench_moc_review_packet_markdown(packet), encoding="utf-8")
    template_json.write_text(_json_dump(packet.result_template), encoding="utf-8")
    return packet_md, packet_json, template_json


def _join(values: list[str]) -> str:
    return ", ".join(values) if values else "无"


def _join_requirements(values: list[str]) -> str:
    return ", ".join(REQUIREMENT_ZH.get(value, value) for value in values) if values else "无"


def _translate_requirement_text(value: str) -> str:
    text = value
    for source, target in REQUIREMENT_ZH.items():
        text = text.replace(source, target)
    return text


def _bullet_lines(values: list[str], *, empty: str = "无") -> list[str]:
    if not values:
        return [f"- {empty}"]
    return [f"- {value}" for value in values]


def _dict_lines(values: dict[str, str], *, empty: str = "无") -> list[str]:
    if not values:
        return [f"- {empty}"]
    return [f"- `{key}`：{value}" for key, value in values.items()]


def _model_result_lines(bench: BenchCard) -> list[str]:
    if not bench.model_results:
        return ["- 当前 seed card 尚未记录模型结果，需要后续从 leaderboard 或论文表格抽取。"]
    lines = []
    for result in bench.model_results:
        parts = [result.model]
        if result.organization:
            parts.append(result.organization)
        if result.metric or result.score:
            parts.append(f"{result.metric or 'score'}={result.score or 'reported'}")
        if result.status:
            parts.append(result.status)
        if result.source_url:
            parts.append(result.source_url)
        lines.append("- " + " | ".join(parts))
    return lines


def _source_lines(bench: BenchCard) -> list[str]:
    if not bench.source_urls:
        return ["- 当前 seed card 尚未记录来源。"]
    lines = []
    for source in bench.source_urls:
        source_type = SOURCE_TYPE_ZH.get(source.source_type, source.source_type)
        label = f"{source.title} ({source_type})"
        if source.note:
            lines.append(f"- {label}：{source.note}；{source.url}")
        else:
            lines.append(f"- {label}：{source.url}")
    return lines


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(value)
    return result


RELATION_TYPE_ZH = {
    "same_capability": "相同/相近能力",
    "complementary": "互补",
    "domain_specialization": "领域特化",
    "metric_mismatch": "指标口径不同",
    "reproducibility_risk": "复现风险相关",
    "incomparable": "不可直接比较",
}

WEAKNESS_TYPE_ZH = {
    "coverage_gap": "覆盖缺口",
    "domain_generalization_risk": "领域外推风险",
    "failure_diagnosis_gap": "失败诊断缺口",
    "metric_mismatch": "指标不一致",
    "reproducibility_risk": "复现风险",
}


def _json_dump(value: dict) -> str:
    import json

    return json.dumps(value, ensure_ascii=False, indent=2)
