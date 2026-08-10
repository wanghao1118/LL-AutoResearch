"""Benchmark evidence helpers for AutoResearch."""

from .matcher import match_benchmarks
from .report import write_bench_card_report, write_bench_evidence_block
from .schema import BenchCard, BenchEvidenceBlock, BenchSearchResult, BenchSuitability
from .understand import search_benchmarks, understand_benchmark

__all__ = [
    "BenchCard",
    "BenchEvidenceBlock",
    "BenchSearchResult",
    "BenchSuitability",
    "match_benchmarks",
    "search_benchmarks",
    "understand_benchmark",
    "write_bench_card_report",
    "write_bench_evidence_block",
]
