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


class BenchProblemSpace(BaseModel):
    space_id: str
    name: str
    description: str = ""
    core_benches: list[str] = Field(default_factory=list)
    adjacent_benches: list[str] = Field(default_factory=list)
    out_of_scope_benches: list[str] = Field(default_factory=list)
    shared_capabilities: list[str] = Field(default_factory=list)
    shared_metrics: list[str] = Field(default_factory=list)
    common_weaknesses: list[str] = Field(default_factory=list)
    evidence_fields: list[str] = Field(default_factory=list)
    confidence: str = "medium"


class BenchRelation(BaseModel):
    source_bench: str
    target_bench: str
    relation_type: str
    rationale: str = ""
    evidence: list[str] = Field(default_factory=list)
    confidence: str = "medium"


class BenchmarkLevelWeakness(BaseModel):
    claim: str
    weakness_type: str = ""
    involved_benches: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    counter_evidence: list[str] = Field(default_factory=list)
    severity: str = "medium"
    review_status: str = "rule-generated"


class BenchMOC(BaseModel):
    title: str = "Bench MOC"
    generation_status: str = "rule-generated"
    problem_spaces: list[BenchProblemSpace] = Field(default_factory=list)
    relations: list[BenchRelation] = Field(default_factory=list)
    benchmark_level_weaknesses: list[BenchmarkLevelWeakness] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    review_summary: str = ""


class BenchMOCReviewPacket(BaseModel):
    moc: BenchMOC
    review_questions: list[str] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)
    result_template: dict = Field(default_factory=dict)


class BenchProblemSpaceReview(BaseModel):
    space_id: str
    verdict: str = "keep"
    rename_to: str = ""
    reason: str = ""
    core_benches: list[str] = Field(default_factory=list)
    adjacent_benches: list[str] = Field(default_factory=list)
    remove_benches: list[str] = Field(default_factory=list)


class BenchRelationReview(BaseModel):
    source_bench: str
    target_bench: str
    verdict: str = "keep"
    relation_type: str = ""
    reason: str = ""
    confidence: str = "medium"


class BenchmarkWeaknessReview(BaseModel):
    claim: str
    verdict: str = "keep"
    revision: str = ""
    reason: str = ""
    evidence: list[str] = Field(default_factory=list)
    confidence: str = "medium"


class BenchMOCReviewResult(BaseModel):
    reviewer: str = "Codex Review"
    overall_verdict: str = "needs-review"
    summary: str = ""
    problem_space_reviews: list[BenchProblemSpaceReview] = Field(default_factory=list)
    relation_reviews: list[BenchRelationReview] = Field(default_factory=list)
    weakness_reviews: list[BenchmarkWeaknessReview] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
