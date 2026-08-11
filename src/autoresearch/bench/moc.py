from __future__ import annotations

import re
from collections import Counter
from itertools import combinations

from .catalog import list_seed_benches
from .schema import (
    BenchCard,
    BenchmarkLevelWeakness,
    BenchmarkWeaknessReview,
    BenchMOC,
    BenchMOCReviewPacket,
    BenchMOCReviewResult,
    BenchProblemSpace,
    BenchProblemSpaceReview,
    BenchRelation,
    BenchRelationReview,
)
from .understand import enrich_bench_card

TOKEN_RE = re.compile(r"[a-z0-9]+")

PROBLEM_SPACE_RULES: tuple[dict[str, object], ...] = (
    {
        "space_id": "real_world_workflow",
        "name": "真实工作流评估",
        "description": "评估模型完成真实或近真实工作任务、产物和业务流程的能力。",
        "core": ("real-world", "workflow", "professional", "business", "deliverable", "spreadsheet"),
        "adjacent": ("gui", "agent", "finance", "desktop", "mobile", "web"),
    },
    {
        "space_id": "gui_agent_task_completion",
        "name": "GUI Agent 任务完成评估",
        "description": "评估 agent 在 web、desktop、mobile 等图形界面里完成任务的能力。",
        "core": ("gui", "desktop", "android", "mobile", "web", "browser", "computer-use"),
        "adjacent": ("agent", "workflow", "success", "trajectory", "recovery"),
    },
    {
        "space_id": "failure_recovery_robustness",
        "name": "失败恢复与鲁棒性评估",
        "description": "评估 agent 是否能识别错误、恢复执行，并解释失败类型。",
        "core": ("failure", "error", "recovery", "robustness", "post-error"),
        "adjacent": ("gui", "trajectory", "diagnostic", "success", "agent"),
    },
    {
        "space_id": "finance_agent_workflow",
        "name": "金融 Agent 工作流评估",
        "description": "评估模型在金融检索、公告/报表理解和专业问答中的 agent 能力。",
        "core": ("finance", "financial", "sec", "edgar", "filing"),
        "adjacent": ("workflow", "search", "agent", "leaderboard"),
    },
    {
        "space_id": "reproducible_scoring",
        "name": "可复现评分与榜单可比性",
        "description": "关注 benchmark 的公开性、评分协议、judge 和跨榜单分数可比性。",
        "core": ("reproducible", "public", "leaderboard", "scoring", "rubric", "expert", "preference"),
        "adjacent": ("metric", "score", "accuracy", "success", "win-rate", "private"),
    },
    {
        "space_id": "medical_multimodal_evaluation",
        "name": "医学多模态评估",
        "description": "评估医学图像、报告、病灶定位和医学 VLM 相关能力。",
        "core": ("medical", "radiology", "ct", "cxr", "lesion", "finding"),
        "adjacent": ("vlm", "multimodal", "localization", "report", "temporal"),
    },
)

REVIEW_QUESTIONS = [
    "每个问题空间的命名是否准确？是否需要拆分或合并？",
    "每个核心 Bench 是否真的属于该问题空间？相邻 Bench 是否应降权或移动？",
    "Bench 之间的关系是相似、互补、领域特化、指标不一致、复现风险，还是不可比？",
    "benchmark-level weakness 是否有足够 BenchCard 字段支撑？是否存在过度推断？",
    "哪些判断需要补论文、HF datasets case、leaderboard 或源码证据？",
]


def generate_bench_moc(*, benches: list[BenchCard] | None = None) -> BenchMOC:
    enriched = [enrich_bench_card(bench) for bench in (benches or list_seed_benches())]
    problem_spaces = _build_problem_spaces(enriched)
    relations = _build_relations(enriched)
    weaknesses = _build_benchmark_level_weaknesses(enriched, relations)
    return BenchMOC(
        title="Bench MOC：评估能力地图",
        problem_spaces=problem_spaces,
        relations=relations,
        benchmark_level_weaknesses=weaknesses,
        notes=[
            "当前 MOC 是规则生成的可审查初稿。",
            "问题空间来自 BenchCard 的 domain、keywords、capabilities、metrics、judge 和 weaknesses。",
            "后续需要 Codex Review 检查分组、关系和 weakness 是否过度推断。",
        ],
    )


def build_bench_moc_review_packet(moc: BenchMOC | None = None) -> BenchMOCReviewPacket:
    target = moc or generate_bench_moc()
    return BenchMOCReviewPacket(
        moc=target,
        review_questions=REVIEW_QUESTIONS,
        instructions=[
            "只基于 packet 中的 BenchCard/MOC 字段审查，不凭空新增事实。",
            "如果一个分组只是关键词相似但任务不一致，请标记为 adjacent 或 remove。",
            "如果 benchmark-level weakness 证据不足，请给出 revision 或 drop。",
            "输出必须符合 bench_moc_review_result.template.json 的字段结构。",
        ],
        result_template=_review_result_template(target),
    )


def apply_bench_moc_review(moc: BenchMOC, review: BenchMOCReviewResult) -> BenchMOC:
    spaces = _apply_space_reviews(moc.problem_spaces, review.problem_space_reviews)
    relations = _apply_relation_reviews(moc.relations, review.relation_reviews)
    weaknesses = _apply_weakness_reviews(moc.benchmark_level_weaknesses, review.weakness_reviews)
    return moc.model_copy(
        update={
            "generation_status": "codex-reviewed",
            "problem_spaces": spaces,
            "relations": relations,
            "benchmark_level_weaknesses": weaknesses,
            "review_summary": review.summary,
            "notes": [
                *moc.notes,
                f"Codex Review overall verdict: {review.overall_verdict}",
                *[f"Open question: {question}" for question in review.open_questions],
            ],
        },
    )


def _build_problem_spaces(benches: list[BenchCard]) -> list[BenchProblemSpace]:
    spaces: list[BenchProblemSpace] = []
    for rule in PROBLEM_SPACE_RULES:
        core_terms = tuple(rule["core"])
        adjacent_terms = tuple(rule["adjacent"])
        core: list[BenchCard] = []
        adjacent: list[BenchCard] = []
        for bench in benches:
            text = _bench_positive_text(bench)
            core_hits = _matched_terms(text, core_terms)
            adjacent_hits = _matched_terms(text, adjacent_terms)
            if core_hits:
                core.append(bench)
            elif adjacent_hits:
                adjacent.append(bench)
        if not core and not adjacent:
            continue
        members = [*core, *adjacent]
        spaces.append(
            BenchProblemSpace(
                space_id=str(rule["space_id"]),
                name=str(rule["name"]),
                description=str(rule["description"]),
                core_benches=[bench.bench_name for bench in core],
                adjacent_benches=[bench.bench_name for bench in adjacent],
                shared_capabilities=_top_values(
                    value for bench in members for value in bench.evaluated_capabilities
                ),
                shared_metrics=_top_values(value for bench in members for value in bench.metrics),
                common_weaknesses=_top_values(value for bench in members for value in bench.weaknesses),
                evidence_fields=["domain", "keywords", "evaluated_capabilities", "metrics", "weaknesses"],
                confidence=_space_confidence(core, adjacent),
            )
        )
    return spaces


def _build_relations(benches: list[BenchCard]) -> list[BenchRelation]:
    relations: list[BenchRelation] = []
    for left, right in combinations(benches, 2):
        relations.extend(_relations_for_pair(left, right))
    return relations


def _relations_for_pair(left: BenchCard, right: BenchCard) -> list[BenchRelation]:
    relations: list[BenchRelation] = []
    left_positive = _bench_positive_text(left)
    right_positive = _bench_positive_text(right)
    shared_capabilities = _shared_tokens(left.evaluated_capabilities, right.evaluated_capabilities)
    shared_domains = _shared_tokens(left.domain, right.domain)

    if len(shared_capabilities) >= 2 or _is_gui_pair(left_positive, right_positive):
        relations.append(
            BenchRelation(
                source_bench=left.bench_name,
                target_bench=right.bench_name,
                relation_type="same_capability",
                rationale="两者评估的能力或任务家族有明显重叠。",
                evidence=_relation_evidence(left, right, shared_capabilities or shared_domains),
                confidence="medium",
            )
        )

    if _is_failure_bench(left_positive) != _is_failure_bench(right_positive) and _both_gui_related(
        left_positive,
        right_positive,
    ):
        relations.append(
            BenchRelation(
                source_bench=left.bench_name,
                target_bench=right.bench_name,
                relation_type="complementary",
                rationale="一个更偏任务完成，另一个补充失败恢复或鲁棒性维度。",
                evidence=_relation_evidence(left, right, ["failure/recovery", "GUI task completion"]),
                confidence="high",
            )
        )

    if _is_finance_workflow_pair(left_positive, right_positive):
        relations.append(
            BenchRelation(
                source_bench=left.bench_name,
                target_bench=right.bench_name,
                relation_type="domain_specialization",
                rationale="金融 Bench 可以视为真实工作流评估的领域特化切片。",
                evidence=_relation_evidence(left, right, ["finance", "workflow"]),
                confidence="medium",
            )
        )

    if _is_workflow_pair(left_positive, right_positive) and _metric_sets_differ(left, right):
        relations.append(
            BenchRelation(
                source_bench=left.bench_name,
                target_bench=right.bench_name,
                relation_type="metric_mismatch",
                rationale="两者都靠近真实工作流评估，但任务、指标或 judge 口径不同，分数不能直接横向比较。",
                evidence=_relation_evidence(left, right, [*left.metrics[:2], *right.metrics[:2]]),
                confidence="medium",
            )
        )

    if (_has_reproducibility_risk(left) or _has_reproducibility_risk(right)) and (
        _is_workflow_pair(left_positive, right_positive) or _shares_any_context(left_positive, right_positive)
    ):
        relations.append(
            BenchRelation(
                source_bench=left.bench_name,
                target_bench=right.bench_name,
                relation_type="reproducibility_risk",
                rationale="至少一个 Bench 存在公开性、专家评审成本、榜单设置或复现条件风险。",
                evidence=_relation_evidence(left, right, ["reproducibility", "leaderboard", "expert review"]),
                confidence="medium",
            )
        )

    if not relations and shared_domains and _metric_sets_differ(left, right):
        relations.append(
            BenchRelation(
                source_bench=left.bench_name,
                target_bench=right.bench_name,
                relation_type="incomparable",
                rationale="领域或概念相邻，但任务形式和评分协议不足以支持直接比较。",
                evidence=_relation_evidence(left, right, shared_domains),
                confidence="low",
            )
        )
    return relations


def _build_benchmark_level_weaknesses(
    benches: list[BenchCard],
    relations: list[BenchRelation],
) -> list[BenchmarkLevelWeakness]:
    weaknesses: list[BenchmarkLevelWeakness] = []
    metric_mismatch_benches = _benches_from_relations(relations, "metric_mismatch")
    if metric_mismatch_benches:
        weaknesses.append(
            BenchmarkLevelWeakness(
                claim="跨 Bench 分数不能直接横向比较，因为任务、指标和 judge 口径不统一。",
                weakness_type="metric_mismatch",
                involved_benches=metric_mismatch_benches,
                evidence=["metric_mismatch relations", "metrics", "scoring_protocol", "judge_type"],
                counter_evidence=["BrowserGym 提供 web benchmark suite 形式的统一接口，但主要集中在 web agent。"],
                severity="high",
            )
        )

    risky = [bench.bench_name for bench in benches if _has_reproducibility_risk(bench)]
    if risky:
        weaknesses.append(
            BenchmarkLevelWeakness(
                claim="部分真实工作流 Bench 的公开性、专家评审成本或榜单设置会限制完全可复现实验。",
                weakness_type="reproducibility_risk",
                involved_benches=risky,
                evidence=["BenchCard weaknesses", "source_type", "judge_type", "leaderboard_urls"],
                severity="high",
            )
        )

    gui_task = [bench.bench_name for bench in benches if _both_terms(_bench_positive_text(bench), ("gui", "agent"))]
    recovery = [bench.bench_name for bench in benches if _is_failure_bench(_bench_positive_text(bench))]
    if gui_task and recovery:
        weaknesses.append(
            BenchmarkLevelWeakness(
                claim="GUI Agent Bench 的任务成功率需要和 failure-conditioned 诊断结合，否则很难解释失败原因。",
                weakness_type="failure_diagnosis_gap",
                involved_benches=sorted(set(gui_task + recovery)),
                evidence=["success-rate metrics", "GUI-RobustEval failure/recovery metrics"],
                counter_evidence=["GUI-RobustEval 已经开始单独评估错误感知和错误后恢复。"],
                severity="medium",
            )
        )

    domain_specific = _benches_from_relations(relations, "domain_specialization")
    if domain_specific:
        weaknesses.append(
            BenchmarkLevelWeakness(
                claim="领域特化 Bench 不能直接外推为通用 agent 能力结论。",
                weakness_type="domain_generalization_risk",
                involved_benches=domain_specific,
                evidence=["domain_specialization relations", "domain", "task_format"],
                severity="medium",
            )
        )

    medical = [
        bench.bench_name for bench in benches if _has_any(_bench_positive_text(bench), ("medical", "radiology", "lesion"))
    ]
    if medical:
        weaknesses.append(
            BenchmarkLevelWeakness(
                claim="医学相关 Bench 可以支撑局部数据或文本证据，但未必能验证医学 VLM 的时序变化推理。",
                weakness_type="coverage_gap",
                involved_benches=medical,
                evidence=["medical_multimodal_evaluation problem space", "BenchCard not_suitable_for", "weaknesses"],
                severity="medium",
            )
        )
    return weaknesses


def _review_result_template(moc: BenchMOC) -> dict:
    return BenchMOCReviewResult(
        overall_verdict="needs-revision",
        summary="请在这里总结 MOC 初稿是否可信、哪些判断需要修改。",
        problem_space_reviews=[
            BenchProblemSpaceReview(
                space_id=space.space_id,
                verdict="keep",
                rename_to="",
                reason="",
                core_benches=space.core_benches,
                adjacent_benches=space.adjacent_benches,
                remove_benches=[],
            )
            for space in moc.problem_spaces[:3]
        ],
        relation_reviews=[
            BenchRelationReview(
                source_bench=relation.source_bench,
                target_bench=relation.target_bench,
                verdict="keep",
                relation_type=relation.relation_type,
                reason="",
                confidence=relation.confidence,
            )
            for relation in moc.relations[:5]
        ],
        weakness_reviews=[
            BenchmarkWeaknessReview(
                claim=weakness.claim,
                verdict="keep",
                revision="",
                reason="",
                evidence=weakness.evidence,
                confidence="medium",
            )
            for weakness in moc.benchmark_level_weaknesses
        ],
        open_questions=["哪些关系需要回到 benchmark 论文或 leaderboard 表格继续核验？"],
    ).model_dump(mode="json")


def _apply_space_reviews(
    spaces: list[BenchProblemSpace],
    reviews: list[BenchProblemSpaceReview],
) -> list[BenchProblemSpace]:
    review_by_id = {review.space_id: review for review in reviews}
    refined: list[BenchProblemSpace] = []
    for space in spaces:
        review = review_by_id.get(space.space_id)
        if review and review.verdict == "drop":
            continue
        if not review:
            refined.append(space)
            continue
        core = review.core_benches or space.core_benches
        adjacent = review.adjacent_benches or space.adjacent_benches
        remove = set(review.remove_benches)
        refined.append(
            space.model_copy(
                update={
                    "name": review.rename_to or space.name,
                    "core_benches": [bench for bench in core if bench not in remove],
                    "adjacent_benches": [bench for bench in adjacent if bench not in remove],
                    "common_weaknesses": _append_if_present(space.common_weaknesses, review.reason),
                    "confidence": "high" if review.verdict == "keep" else space.confidence,
                }
            )
        )
    return refined


def _apply_relation_reviews(
    relations: list[BenchRelation],
    reviews: list[BenchRelationReview],
) -> list[BenchRelation]:
    refined: list[BenchRelation] = []
    for relation in relations:
        review = _find_relation_review(relation, reviews)
        if review and review.verdict == "drop":
            continue
        if not review:
            refined.append(relation)
            continue
        refined.append(
            relation.model_copy(
                update={
                    "relation_type": review.relation_type or relation.relation_type,
                    "rationale": review.reason or relation.rationale,
                    "confidence": review.confidence or relation.confidence,
                }
            )
        )
    return refined


def _apply_weakness_reviews(
    weaknesses: list[BenchmarkLevelWeakness],
    reviews: list[BenchmarkWeaknessReview],
) -> list[BenchmarkLevelWeakness]:
    review_by_claim = {review.claim: review for review in reviews}
    refined: list[BenchmarkLevelWeakness] = []
    for weakness in weaknesses:
        review = review_by_claim.get(weakness.claim)
        if review and review.verdict == "drop":
            continue
        if not review:
            refined.append(weakness)
            continue
        refined.append(
            weakness.model_copy(
                update={
                    "claim": review.revision or weakness.claim,
                    "evidence": review.evidence or weakness.evidence,
                    "review_status": "codex-reviewed",
                    "severity": _severity_from_confidence(review.confidence, weakness.severity),
                }
            )
        )
    return refined


def _find_relation_review(
    relation: BenchRelation,
    reviews: list[BenchRelationReview],
) -> BenchRelationReview | None:
    pair = {relation.source_bench, relation.target_bench}
    for review in reviews:
        if {review.source_bench, review.target_bench} == pair:
            return review
    return None


def _bench_text(bench: BenchCard) -> str:
    values = [
        bench.bench_name,
        " ".join(bench.aliases),
        bench.benchmark_family,
        " ".join(bench.domain),
        " ".join(bench.keywords),
        " ".join(bench.tags),
        " ".join(bench.evaluated_capabilities),
        bench.task_goal,
        bench.task_format,
        " ".join(bench.metrics),
        bench.scoring_protocol,
        bench.judge_type,
        " ".join(bench.strengths),
        " ".join(bench.weaknesses),
        " ".join(bench.suitable_for),
        " ".join(bench.not_suitable_for),
        " ".join(result.model for result in bench.model_results),
        " ".join(result.organization for result in bench.model_results),
        " ".join(source.source_type for source in bench.source_urls),
    ]
    return " ".join(values).lower()


def _bench_positive_text(bench: BenchCard) -> str:
    values = [
        bench.bench_name,
        " ".join(bench.aliases),
        bench.benchmark_family,
        " ".join(bench.domain),
        " ".join(bench.keywords),
        " ".join(bench.tags),
        " ".join(bench.evaluated_capabilities),
        bench.task_goal,
        bench.task_format,
        " ".join(bench.metrics),
        bench.scoring_protocol,
        bench.judge_type,
        " ".join(bench.strengths),
        " ".join(bench.suitable_for),
        " ".join(result.model for result in bench.model_results),
        " ".join(result.organization for result in bench.model_results),
        " ".join(source.source_type for source in bench.source_urls),
    ]
    return " ".join(values).lower()


def _matched_terms(text: str, terms: tuple[str, ...]) -> list[str]:
    tokens = set(TOKEN_RE.findall(text))
    return [term for term in terms if _term_matches(term, text, tokens)]


def _term_matches(term: str, text: str, tokens: set[str]) -> bool:
    if re.search(r"[^a-z0-9]", term):
        return term in text
    return term in tokens


def _top_values(values: object, *, limit: int = 6) -> list[str]:
    counter = Counter(value for value in values if isinstance(value, str) and value)
    return [value for value, _ in counter.most_common(limit)]


def _space_confidence(core: list[BenchCard], adjacent: list[BenchCard]) -> str:
    if len(core) >= 2:
        return "high"
    if core or len(adjacent) >= 2:
        return "medium"
    return "low"


def _shared_tokens(left_values: list[str], right_values: list[str]) -> list[str]:
    left_tokens = {token for value in left_values for token in TOKEN_RE.findall(value.lower())}
    right_tokens = {token for value in right_values for token in TOKEN_RE.findall(value.lower())}
    stop = {"agent", "benchmark", "evaluation", "task", "score", "rate"}
    return sorted(token for token in left_tokens & right_tokens if len(token) > 2 and token not in stop)


def _relation_evidence(left: BenchCard, right: BenchCard, terms: list[str]) -> list[str]:
    evidence = [
        (
            f"{left.bench_name}: capabilities={', '.join(left.evaluated_capabilities[:3]) or 'unknown'}; "
            f"metrics={', '.join(left.metrics[:3]) or 'unknown'}"
        ),
        (
            f"{right.bench_name}: capabilities={', '.join(right.evaluated_capabilities[:3]) or 'unknown'}; "
            f"metrics={', '.join(right.metrics[:3]) or 'unknown'}"
        ),
    ]
    if terms:
        evidence.append("matched terms: " + ", ".join(terms[:6]))
    return evidence


def _is_gui_pair(left_text: str, right_text: str) -> bool:
    return _both_gui_related(left_text, right_text) and _has_any(left_text + " " + right_text, ("success", "task", "workflow"))


def _both_gui_related(left_text: str, right_text: str) -> bool:
    return _has_any(left_text, ("gui", "desktop", "android", "mobile", "browser", "web")) and _has_any(
        right_text,
        ("gui", "desktop", "android", "mobile", "browser", "web"),
    )


def _is_failure_bench(text: str) -> bool:
    return _has_any(text, ("failure", "error", "recovery", "robustness", "post-error"))


def _is_finance_workflow_pair(left_text: str, right_text: str) -> bool:
    left_finance = _has_any(left_text, ("finance", "financial", "filing", "edgar", "sec"))
    right_finance = _has_any(right_text, ("finance", "financial", "filing", "edgar", "sec"))
    left_workflow = _has_any(left_text, ("workflow", "real-world", "professional", "business", "spreadsheet"))
    right_workflow = _has_any(right_text, ("workflow", "real-world", "professional", "business", "spreadsheet"))
    left_medical = _has_any(left_text, ("medical", "radiology", "lesion", "cxr", "ct"))
    right_medical = _has_any(right_text, ("medical", "radiology", "lesion", "cxr", "ct"))
    return (left_finance and right_workflow and not right_medical) or (
        right_finance and left_workflow and not left_medical
    )


def _is_workflow_pair(left_text: str, right_text: str) -> bool:
    return _has_any(left_text, ("workflow", "real-world", "professional", "business")) and _has_any(
        right_text,
        ("workflow", "real-world", "professional", "business"),
    )


def _metric_sets_differ(left: BenchCard, right: BenchCard) -> bool:
    left_metrics = {metric.lower() for metric in left.metrics}
    right_metrics = {metric.lower() for metric in right.metrics}
    return bool(left_metrics and right_metrics and left_metrics != right_metrics)


def _has_reproducibility_risk(bench: BenchCard) -> bool:
    text = _bench_text(bench)
    return _has_any(text, ("private", "expert", "leaderboard", "reproducible", "复现", "公开", "榜单", "专家"))


def _shares_any_context(left_text: str, right_text: str) -> bool:
    contexts = (
        ("medical", "radiology", "lesion"),
        ("gui", "desktop", "android", "browser", "web"),
        ("finance", "financial"),
        ("workflow", "real-world", "professional", "business"),
    )
    return any(_has_any(left_text, context) and _has_any(right_text, context) for context in contexts)


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    tokens = set(TOKEN_RE.findall(text))
    return any(_term_matches(term, text, tokens) for term in terms)


def _both_terms(text: str, terms: tuple[str, ...]) -> bool:
    return all(_term_matches(term, text, set(TOKEN_RE.findall(text))) for term in terms)


def _benches_from_relations(relations: list[BenchRelation], relation_type: str) -> list[str]:
    benches: set[str] = set()
    for relation in relations:
        if relation.relation_type != relation_type:
            continue
        benches.add(relation.source_bench)
        benches.add(relation.target_bench)
    return sorted(benches)


def _append_if_present(values: list[str], value: str) -> list[str]:
    if not value:
        return values
    return [*values, f"Codex Review note: {value}"]


def _severity_from_confidence(confidence: str, default: str) -> str:
    if confidence == "high":
        return "high"
    if confidence == "low":
        return "low"
    return default
