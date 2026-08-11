from __future__ import annotations

import os

from .schema import (
    EvidenceCoverageRecord,
    FullTextRecord,
    FullTextResolutionRecord,
    OpenAccessRecord,
    ProviderHealthCheck,
    SourceStatus,
    WeaknessCard,
)

METHOD_TERMS = ("method", "methods", "materials", "approach", "model", "training")
EXPERIMENT_TERMS = ("experiment", "experiments", "results", "evaluation", "benchmark")
DATASET_METRIC_TERMS = ("dataset", "data", "metric", "metrics", "evaluation", "benchmark")


def _count_status(rows: list, status: str) -> int:
    return sum(1 for row in rows if getattr(row, "status", "") == status)


def _has_provider(rows: list[FullTextResolutionRecord], provider: str) -> int:
    return sum(1 for row in rows if provider in row.resolved_by)


def _full_text_provider_count(rows: list[FullTextRecord], provider: str, status: str = "ok") -> int:
    return sum(1 for row in rows if row.provider == provider and row.status == status)


def build_provider_health(
    *,
    source_statuses: list[SourceStatus],
    full_text_resolutions: list[FullTextResolutionRecord],
    full_texts: list[FullTextRecord],
    open_access_records: list[OpenAccessRecord],
) -> list[ProviderHealthCheck]:
    email_configured = bool(os.getenv("UNPAYWALL_EMAIL", "").strip())
    oa_ok = _count_status(open_access_records, "ok")
    oa_attempted = len(open_access_records)
    unpaywall_notes = sum(
        1
        for row in full_text_resolutions
        for note in row.notes
        if "Unpaywall skipped" in note
    )
    health = [
        ProviderHealthCheck(
            provider="unpaywall",
            status="configured" if email_configured else "not_configured",
            summary=(
                f"已配置；OA enrichment 成功 {oa_ok}/{oa_attempted}"
                if email_configured
                else "未配置 UNPAYWALL_EMAIL，DOI 开放全文入口会少一层 fallback"
            ),
            details=[
                f"open_access_records={oa_attempted}",
                f"open_access_ok={oa_ok}",
                f"resolver_unpaywall_skipped_notes={unpaywall_notes}",
            ],
        )
    ]

    europepmc_candidates = _has_provider(full_text_resolutions, "europepmc_xml")
    europepmc_success = _full_text_provider_count(full_texts, "europepmc_xml")
    health.append(
        ProviderHealthCheck(
            provider="europepmc_xml",
            status="ok" if europepmc_success else "candidate_only" if europepmc_candidates else "not_attempted",
            summary=f"Europe PMC XML 候选 {europepmc_candidates} 篇，成功解析 {europepmc_success} 篇",
            details=[
                "适合医学 / 生物医学 PMC 开放全文",
                "优先级高于 PMC HTML 和 PDF",
            ],
        )
    )

    arxiv_candidates = _has_provider(full_text_resolutions, "arxiv_source")
    arxiv_success = sum(
        1 for row in full_texts if row.status == "ok" and row.provider in {"arxiv_source", "arxiv_pdf"}
    )
    arxiv_failures = sum(
        1
        for row in full_texts
        if any(provider.startswith("arxiv_") for provider in row.attempted_providers)
        and row.status != "ok"
    )
    if arxiv_success and arxiv_failures:
        arxiv_status = "degraded"
    elif arxiv_success:
        arxiv_status = "ok"
    elif arxiv_failures:
        arxiv_status = "failed"
    elif arxiv_candidates:
        arxiv_status = "candidate_only"
    else:
        arxiv_status = "not_attempted"
    health.append(
        ProviderHealthCheck(
            provider="arxiv_source",
            status=arxiv_status,
            summary=f"arXiv source/PDF 候选 {arxiv_candidates} 篇，成功 {arxiv_success} 篇，失败/超时 {arxiv_failures} 篇",
            details=[
                "已启用 arXiv source、export source、src、PDF fallback 和本地缓存",
                "若仍失败，通常意味着当前网络下载 source/PDF 超时，不等于论文没有全文",
            ],
        )
    )

    openalex_rows = [row for row in source_statuses if row.source == "openalex"]
    openalex_429 = sum(1 for row in openalex_rows if "429" in row.error)
    openalex_ok = _count_status(openalex_rows, "ok")
    openalex_failed = sum(1 for row in openalex_rows if row.status == "failed")
    health.append(
        ProviderHealthCheck(
            provider="openalex",
            status="limited" if openalex_429 else "ok" if openalex_ok else "not_attempted",
            summary=f"OpenAlex 成功 {openalex_ok} 次，失败 {openalex_failed} 次，429 限流 {openalex_429} 次",
            details=["OpenAlex 负责补通用学术元数据；429 时需要缓存和限速"],
        )
    )

    full_text_ok = _count_status(full_texts, "ok")
    full_text_total = len(full_texts)
    ratio = full_text_ok / full_text_total if full_text_total else 0.0
    health.append(
        ProviderHealthCheck(
            provider="full_text_fetch",
            status="ok" if ratio >= 0.7 else "partial" if full_text_ok else "not_attempted",
            summary=f"全文解析成功 {full_text_ok}/{full_text_total}",
            details=[
                "这个指标决定 Weakness 证据是否停留在摘要层",
                "目标是每个核心 Weakness 至少读到 2 篇支持论文全文",
            ],
        )
    )
    return health


def _section_count(records: list[FullTextRecord], terms: tuple[str, ...]) -> int:
    count = 0
    for record in records:
        for section in record.sections:
            heading = section.heading.lower()
            if any(term in heading for term in terms):
                count += 1
    return count


def build_evidence_coverage(
    weakness_cards: list[WeaknessCard],
    full_texts: list[FullTextRecord],
) -> list[EvidenceCoverageRecord]:
    full_text_by_title = {row.title: row for row in full_texts if row.status == "ok"}
    full_text_successes = len(full_text_by_title)
    records: list[EvidenceCoverageRecord] = []
    for card in weakness_cards:
        support = card.support_papers
        support_full_texts = [title for title in support if title in full_text_by_title]
        missing_support = [title for title in support if title not in full_text_by_title]
        scoped_records = [full_text_by_title[title] for title in support_full_texts]
        method_sections = _section_count(scoped_records, METHOD_TERMS)
        experiment_sections = _section_count(scoped_records, EXPERIMENT_TERMS)
        dataset_metric_sections = _section_count(scoped_records, DATASET_METRIC_TERMS)
        reasons = [
            f"support_full_texts={len(support_full_texts)}/{len(support)}",
            f"method_sections={method_sections}",
            f"experiment_sections={experiment_sections}",
            f"dataset_metric_sections={dataset_metric_sections}",
            f"overall_full_text_successes={full_text_successes}",
        ]
        has_core_sections = method_sections > 0 and experiment_sections > 0 and dataset_metric_sections > 0
        if card.evidence_quality in {"medium", "strong"} and len(support_full_texts) >= 2 and has_core_sections:
            status = "ready_to_state_narrowly"
        elif card.evidence_quality in {"medium", "strong"} and full_text_successes >= 2:
            status = "needs_targeted_full_text"
        else:
            status = "insufficient_coverage"
        records.append(
            EvidenceCoverageRecord(
                weakness_statement=card.weakness_statement,
                status=status,
                checked_papers=card.checked_papers,
                support_papers=support,
                support_full_text_papers=support_full_texts,
                missing_support_full_text_papers=missing_support,
                full_text_successes=full_text_successes,
                method_sections=method_sections,
                experiment_sections=experiment_sections,
                dataset_metric_sections=dataset_metric_sections,
                reasons=reasons,
            )
        )
    return records
