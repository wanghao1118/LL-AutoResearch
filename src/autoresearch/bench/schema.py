from __future__ import annotations

from pydantic import BaseModel, Field


class BenchSource(BaseModel):
    title: str
    url: str
    source_type: str = "project"
    note: str = ""


class BenchModelResult(BaseModel):
    model: str
    organization: str = ""
    metric: str = ""
    score: str = ""
    source_url: str = ""
    status: str = "reported"


class BenchCard(BaseModel):
    bench_name: str
    aliases: list[str] = Field(default_factory=list)
    benchmark_family: str = ""
    domain: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    source_urls: list[BenchSource] = Field(default_factory=list)
    hf_dataset_ids: list[str] = Field(default_factory=list)
    paper_urls: list[str] = Field(default_factory=list)
    leaderboard_urls: list[str] = Field(default_factory=list)
    evaluated_capabilities: list[str] = Field(default_factory=list)
    task_goal: str = ""
    task_format: str = ""
    input_modalities: list[str] = Field(default_factory=list)
    output_format: str = ""
    case_examples: list[str] = Field(default_factory=list)
    dataset_schema: dict[str, str] = Field(default_factory=dict)
    metrics: list[str] = Field(default_factory=list)
    scoring_protocol: str = ""
    judge_type: str = ""
    model_results: list[BenchModelResult] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    suitable_for: list[str] = Field(default_factory=list)
    not_suitable_for: list[str] = Field(default_factory=list)
    evidence_snippets: list[str] = Field(default_factory=list)
    understanding_status: str = "seed"
    source_confidence: str = "medium"


class BenchSearchResult(BaseModel):
    bench_name: str
    relevance_score: float = 0.0
    matched_keywords: list[str] = Field(default_factory=list)
    domain: list[str] = Field(default_factory=list)
    evaluated_capabilities: list[str] = Field(default_factory=list)
    source_types: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)


class BenchSuitability(BaseModel):
    bench_name: str
    verdict: str = "insufficient"
    relevance_score: float = 0.0
    matched_terms: list[str] = Field(default_factory=list)
    covered_requirements: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    rationale: str = ""
    bench_weaknesses: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)


class BenchEvidenceBlock(BaseModel):
    research_weakness: str
    related_benches: list[BenchSuitability] = Field(default_factory=list)
    sufficient_benches: list[str] = Field(default_factory=list)
    partial_benches: list[str] = Field(default_factory=list)
    insufficient_benches: list[str] = Field(default_factory=list)
    remaining_evaluation_gap: str = ""
    need_new_benchmark: bool = False
    recommended_benchmark_direction: str = ""
    notes: list[str] = Field(default_factory=list)
