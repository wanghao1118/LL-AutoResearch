from __future__ import annotations

import re

from .catalog import list_seed_benches
from .schema import BenchCard, BenchEvidenceBlock, BenchSuitability

TOKEN_RE = re.compile(r"[a-z0-9]+")

REQUIREMENT_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("medical", ("medical", "radiology", "clinical", "ct", "cxr", "mri")),
    ("VLM / multimodal evaluation", ("vlm", "vision-language", "multimodal")),
    ("lesion-level evidence", ("lesion", "finding", "localization", "grounding")),
    ("temporal / change evaluation", ("temporal", "longitudinal", "follow-up", "change", "paired-study")),
    ("GUI agent evaluation", ("gui", "computer-use", "desktop", "mobile", "android", "web")),
    ("failure / recovery diagnosis", ("failure", "error", "recovery", "robustness", "diagnostic")),
    ("cross-benchmark comparability", ("cross-benchmark", "comparable", "comparability", "unified")),
    ("finance domain", ("finance", "financial", "filing", "sec", "edgar")),
    ("real-world workflow", ("real-world", "workflow", "professional", "business")),
    ("reproducible scoring", ("reproducible", "public", "scoring", "leaderboard")),
)


def _tokens(value: str) -> set[str]:
    return set(TOKEN_RE.findall(value.lower()))


def _text_for_bench(bench: BenchCard) -> str:
    return " ".join(
        [
            bench.bench_name,
            " ".join(bench.aliases),
            " ".join(bench.domain),
            " ".join(bench.keywords),
            " ".join(bench.evaluated_capabilities),
            bench.task_format,
            " ".join(bench.metrics),
            bench.scoring_protocol,
            " ".join(bench.suitable_for),
            " ".join(bench.not_suitable_for),
            " ".join(bench.strengths),
            " ".join(bench.weaknesses),
        ]
    ).lower()


def _coverage_text_for_bench(bench: BenchCard) -> str:
    """Positive evidence text only; excludes fields that describe benchmark gaps."""
    return " ".join(
        [
            bench.bench_name,
            " ".join(bench.aliases),
            " ".join(bench.domain),
            " ".join(bench.keywords),
            " ".join(bench.evaluated_capabilities),
            bench.task_format,
            " ".join(bench.metrics),
            bench.scoring_protocol,
            " ".join(bench.suitable_for),
            " ".join(bench.strengths),
        ]
    ).lower()


def infer_requirements(weakness: str) -> list[str]:
    lowered = weakness.lower()
    requirements = []
    for label, keywords in REQUIREMENT_RULES:
        if any(keyword in lowered for keyword in keywords):
            requirements.append(label)
    if not requirements:
        requirements.append("target capability evaluation")
    return requirements


def _requirement_covered(requirement: str, bench_text: str) -> bool:
    keywords = dict(REQUIREMENT_RULES).get(requirement, ())
    if not keywords:
        return False
    text_tokens = _tokens(bench_text)
    return any(_contains_keyword(bench_text, text_tokens, keyword) for keyword in keywords)


def _contains_keyword(text: str, text_tokens: set[str], keyword: str) -> bool:
    if not keyword:
        return False
    if re.search(r"[^a-z0-9]", keyword):
        return keyword in text
    return keyword in text_tokens


def _matched_terms(weakness: str, bench: BenchCard) -> list[str]:
    weakness_tokens = _tokens(weakness)
    bench_tokens = _tokens(_coverage_text_for_bench(bench))
    stop = {
        "the",
        "and",
        "for",
        "with",
        "lacks",
        "lack",
        "missing",
        "evaluation",
        "benchmark",
        "benchmarks",
        "level",
        "reasoning",
    }
    matches = sorted(token for token in weakness_tokens & bench_tokens if len(token) > 2 and token not in stop)
    return matches[:12]


def score_bench_for_weakness(weakness: str, bench: BenchCard) -> BenchSuitability:
    requirements = infer_requirements(weakness)
    bench_text = _coverage_text_for_bench(bench)
    matched = _matched_terms(weakness, bench)
    covered = [requirement for requirement in requirements if _requirement_covered(requirement, bench_text)]
    missing = [requirement for requirement in requirements if requirement not in covered]
    coverage_ratio = len(covered) / len(requirements) if requirements else 0.0
    lexical_bonus = min(len(matched) * 0.04, 0.2)
    score = round(min(1.0, coverage_ratio * 0.8 + lexical_bonus), 2)

    if coverage_ratio >= 0.8 and len(missing) <= 1:
        verdict = "sufficient"
    elif coverage_ratio >= 0.35 or len(matched) >= 2:
        verdict = "partial"
    else:
        verdict = "insufficient"

    if verdict == "sufficient" and bench.weaknesses:
        verdict = "partial"

    rationale = _rationale(bench, verdict, covered, missing)
    return BenchSuitability(
        bench_name=bench.bench_name,
        verdict=verdict,
        relevance_score=score,
        matched_terms=matched,
        covered_requirements=covered,
        missing_requirements=missing,
        rationale=rationale,
        bench_weaknesses=bench.weaknesses,
        source_urls=[source.url for source in bench.source_urls],
    )


def _rationale(
    bench: BenchCard,
    verdict: str,
    covered: list[str],
    missing: list[str],
) -> str:
    if verdict == "sufficient":
        return (
            f"{bench.bench_name} 基本覆盖这个 weakness 所需的评估维度："
            f"{', '.join(covered) or '未显式覆盖'}。"
        )
    if verdict == "partial":
        return (
            f"{bench.bench_name} 与该 weakness 有关，但不能单独完成验证。已覆盖："
            f"{', '.join(covered) or '未显式覆盖'}；仍缺："
            f"{', '.join(missing) or '未显式缺失'}。"
        )
    return (
        f"{bench.bench_name} 与该 weakness 的重合度较弱。主要缺少："
        f"{', '.join(missing) or '目标能力相关证据'}。"
    )


def match_benchmarks(
    weakness: str,
    *,
    benches: list[BenchCard] | None = None,
    limit: int = 6,
) -> BenchEvidenceBlock:
    candidates = benches or list_seed_benches()
    scored = [score_bench_for_weakness(weakness, bench) for bench in candidates]
    scored = sorted(
        scored,
        key=lambda item: (
            {"sufficient": 3, "partial": 2, "insufficient": 1}.get(item.verdict, 0),
            item.relevance_score,
            len(item.matched_terms),
        ),
        reverse=True,
    )
    positive = [item for item in scored if item.relevance_score > 0]
    scored = (positive or scored)[:limit]
    sufficient = [item.bench_name for item in scored if item.verdict == "sufficient"]
    partial = [item.bench_name for item in scored if item.verdict == "partial"]
    insufficient = [item.bench_name for item in scored if item.verdict == "insufficient"]
    remaining_gap, recommendation = _remaining_gap(weakness, scored)
    return BenchEvidenceBlock(
        research_weakness=weakness,
        related_benches=scored,
        sufficient_benches=sufficient,
        partial_benches=partial,
        insufficient_benches=insufficient,
        remaining_evaluation_gap=remaining_gap,
        need_new_benchmark=not sufficient,
        recommended_benchmark_direction=recommendation,
        notes=[
            "当前 MVP 使用本地种子 Bench 库和规则匹配，适合作为第一轮筛选。",
            "这些判断还不是最终结论；后续需要从论文、数据集和榜单中抽取 source-level BenchCard 来增强证据。",
        ],
    )


def _remaining_gap(weakness: str, scored: list[BenchSuitability]) -> tuple[str, str]:
    requirements = infer_requirements(weakness)
    covered_by_any: list[str] = []
    for item in scored:
        if item.relevance_score < 0.2:
            continue
        for requirement in item.covered_requirements:
            if requirement not in covered_by_any:
                covered_by_any.append(requirement)
    missing = [requirement for requirement in requirements if requirement not in covered_by_any]
    if not scored:
        return (
            "当前种子库里没有找到相关 benchmark。",
            f"围绕这个 weakness 构造专门 benchmark：{weakness}",
        )
    if any(item.verdict == "sufficient" for item in scored):
        return (
            (
                "至少有一个种子 benchmark 看起来能覆盖主要评估需求，但仍需要检查它自己的局限、"
                "评分协议和数据可得性。"
            ),
            "优先复用已有 benchmark，再审查评分方式、数据访问和已测模型覆盖。",
        )
    if missing:
        return (
            "现有种子 benchmark 只能部分对齐。剩余评估缺口是："
            + ", ".join(missing[:5])
            + "。",
            (
                "设计一个能直接覆盖缺失需求的 benchmark slice，并把数据集、指标、评分方式和 baseline "
                "全部写清楚。"
            ),
        )
    return (
        (
            "相关评估需求可以被多个 seed benchmark 分散覆盖，但还缺一个统一证据链来说明："
            "哪个 benchmark 支撑哪一部分、哪些分数不能直接横向比较、benchmark 自身 weakness 是否会影响结论。"
        ),
        "先建立 Bench MOC 和 source-level BenchCard；如果现有 Bench 无法形成闭环，再构造新的 benchmark slice。",
    )
