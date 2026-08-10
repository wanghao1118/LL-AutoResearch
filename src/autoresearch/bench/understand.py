from __future__ import annotations

import re

from .catalog import list_seed_benches
from .schema import BenchCard, BenchSearchResult

TOKEN_RE = re.compile(r"[a-z0-9]+")


def understand_benchmark(
    bench_name: str,
    *,
    benches: list[BenchCard] | None = None,
) -> BenchCard:
    candidates = benches or list_seed_benches()
    normalized_name = _normalize_name(bench_name)
    for bench in candidates:
        names = [bench.bench_name, *bench.aliases]
        if normalized_name in {_normalize_name(name) for name in names}:
            return enrich_bench_card(bench)
    search_results = search_benchmarks(bench_name, benches=candidates, limit=3)
    suggestions = ", ".join(item.bench_name for item in search_results) or "无"
    raise ValueError(f"没有在种子 Bench 库里找到 `{bench_name}`。相近候选：{suggestions}")


def search_benchmarks(
    query: str,
    *,
    benches: list[BenchCard] | None = None,
    limit: int = 20,
) -> list[BenchSearchResult]:
    candidates = benches or list_seed_benches()
    query_terms = _query_terms(query)
    results = [_score_search_result(bench, query_terms) for bench in candidates]
    positives = [result for result in results if result.relevance_score > 0]
    ranked = sorted(
        positives or results,
        key=lambda item: (item.relevance_score, len(item.matched_keywords), item.bench_name.lower()),
        reverse=True,
    )
    return ranked[:limit]


def enrich_bench_card(bench: BenchCard) -> BenchCard:
    updates: dict[str, object] = {}
    paper_urls = [source.url for source in bench.source_urls if source.source_type == "paper"]
    leaderboard_urls = [source.url for source in bench.source_urls if source.source_type == "leaderboard"]
    source_types = sorted({source.source_type for source in bench.source_urls})
    if not bench.paper_urls and paper_urls:
        updates["paper_urls"] = paper_urls
    if not bench.leaderboard_urls and leaderboard_urls:
        updates["leaderboard_urls"] = leaderboard_urls
    if not bench.tags:
        updates["tags"] = derive_bench_tags(bench, extra_terms=source_types)
    if not bench.task_goal and bench.evaluated_capabilities:
        updates["task_goal"] = " / ".join(bench.evaluated_capabilities[:3])
    if not bench.output_format and bench.metrics:
        updates["output_format"] = "评估输出通常由指标刻画：" + ", ".join(bench.metrics[:4])
    if not updates:
        return bench
    return bench.model_copy(update=updates)


def derive_bench_tags(bench: BenchCard, *, extra_terms: list[str] | None = None) -> list[str]:
    raw_terms: list[str] = []
    raw_terms.extend(bench.domain)
    raw_terms.extend(bench.keywords)
    raw_terms.extend(bench.evaluated_capabilities)
    raw_terms.extend(bench.metrics)
    raw_terms.extend(source.source_type for source in bench.source_urls)
    raw_terms.extend(result.organization for result in bench.model_results)
    raw_terms.extend(result.model for result in bench.model_results)
    raw_terms.extend(extra_terms or [])
    tags: list[str] = []
    seen: set[str] = set()
    for term in raw_terms:
        for token in _tag_terms(term):
            if token and token not in seen:
                seen.add(token)
                tags.append(token)
    return tags[:32]


def _score_search_result(bench: BenchCard, query_terms: list[str]) -> BenchSearchResult:
    enriched = enrich_bench_card(bench)
    searchable_text = _searchable_text(enriched)
    searchable_tokens = set(TOKEN_RE.findall(searchable_text))
    matched: list[str] = []
    for term in query_terms:
        if _term_matches(term, searchable_text, searchable_tokens):
            matched.append(term)
    score = 0.0
    if query_terms:
        score = round(len(matched) / len(query_terms), 2)
    source_types = sorted({source.source_type for source in enriched.source_urls})
    return BenchSearchResult(
        bench_name=enriched.bench_name,
        relevance_score=score,
        matched_keywords=matched,
        domain=enriched.domain,
        evaluated_capabilities=enriched.evaluated_capabilities,
        source_types=source_types,
        source_urls=[source.url for source in enriched.source_urls],
    )


def _searchable_text(bench: BenchCard) -> str:
    values = [
        bench.bench_name,
        " ".join(bench.aliases),
        bench.benchmark_family,
        " ".join(bench.domain),
        " ".join(bench.keywords),
        " ".join(bench.tags),
        " ".join(bench.hf_dataset_ids),
        " ".join(source.source_type for source in bench.source_urls),
        " ".join(source.title for source in bench.source_urls),
        " ".join(source.note for source in bench.source_urls),
        " ".join(bench.evaluated_capabilities),
        bench.task_goal,
        bench.task_format,
        " ".join(bench.input_modalities),
        bench.output_format,
        " ".join(bench.metrics),
        bench.scoring_protocol,
        bench.judge_type,
        " ".join(result.model for result in bench.model_results),
        " ".join(result.organization for result in bench.model_results),
        " ".join(bench.strengths),
        " ".join(bench.weaknesses),
        " ".join(bench.suitable_for),
        " ".join(bench.not_suitable_for),
    ]
    return " ".join(values).lower()


def _query_terms(query: str) -> list[str]:
    parts = re.split(r"[,，\s]+", query.strip().lower())
    return [part for part in parts if part]


def _tag_terms(value: str) -> list[str]:
    normalized = value.strip().lower()
    if not normalized:
        return []
    compact = re.sub(r"\s+", "-", normalized)
    tokens = TOKEN_RE.findall(normalized)
    return [compact, *tokens]


def _term_matches(term: str, text: str, tokens: set[str]) -> bool:
    if re.search(r"[^a-z0-9]", term):
        return term in text
    return term in tokens


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())
