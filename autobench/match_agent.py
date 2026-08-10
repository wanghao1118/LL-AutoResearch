"""Agents 4 and 5: compatibility scoring and benchmark-portfolio selection."""

from __future__ import annotations

import re

from .models import BenchmarkRecord, CapabilityProfile, ScoredCandidate, SearchHit


WEIGHTS = {
    "task": 0.32,
    "modality": 0.12,
    "interaction": 0.16,
    "output": 0.12,
    "environment": 0.10,
    "capability": 0.10,
    "metric": 0.05,
    "literature": 0.03,
}

SPECIALIZED_CAPABILITIES = {"multilingual_code_generation"}

SPECIALIZATION_GATES: dict[str, tuple[str, frozenset[str]]] = {
    "ambignq": ("output_types", frozenset({"disambiguated_question"})),
    "tabmwp": ("environments", frozenset({"structured_table"})),
    "game_of_24": ("capabilities", frozenset({"long_horizon_planning"})),
    "multipl_e": ("capabilities", frozenset({"multilingual_code_generation"})),
    "leetcodehardgym": (
        "capabilities",
        frozenset({"iterative_improvement", "multilingual_code_generation"}),
    ),
}

SPECIALIZATION_BREADTH_EXEMPTIONS: dict[str, tuple[str, int]] = {
    "ambignq": ("knowledge_intensive_qa", 3),
    "tabmwp": ("math_reasoning", 3),
}

TASK_ENVIRONMENT_GATES: dict[str, tuple[frozenset[str], frozenset[str]]] = {
    "online_store": (frozenset({"web_navigation"}), frozenset({"website"})),
}


def _coverage(required: list[str], offered: list[str], candidate_denominator: bool = False) -> float:
    required_set = set(required)
    offered_set = set(offered)
    if not required_set or not offered_set:
        return 0.0
    denominator = len(offered_set) if candidate_denominator else len(required_set)
    return len(required_set & offered_set) / max(denominator, 1)


def _environment_fit(required: list[str], offered: list[str]) -> float:
    """Reward a benchmark that matches a visible domain-specific environment.

    Generic website or executor compatibility remains useful, but it should not
    outrank an explicitly supported online-store, repository, table, or other
    domain environment merely because the generic record has fewer labels.
    """

    required_set = set(required)
    offered_set = set(offered)
    if not required_set or not offered_set:
        return 0.0
    generic = {"website", "knowledge_base", "code_executor"}
    specific_required = required_set - generic
    if specific_required:
        if specific_required & offered_set:
            return 1.0
        if required_set & offered_set:
            return 0.5
        return 0.0
    return _coverage(required, offered, candidate_denominator=True)


def task_normalized_score(candidate: ScoredCandidate) -> float:
    """Restore the task component to one for cross-profile thresholds.

    Candidate scores intentionally divide task coverage by the number of tasks
    in a broad method profile. Selection thresholds should not become stricter
    merely because the same paper contains more task families, so this view is
    used only for route and supplementary-admission gates.
    """

    task_component = candidate.component_scores["task"]
    if task_component <= 0:
        return candidate.score
    return candidate.score + WEIGHTS["task"] * (1.0 - task_component)


def _deferred_breadth_variant(
    profile: CapabilityProfile,
    candidate: ScoredCandidate,
) -> bool:
    """Place subtype-specific breadth variants after canonical task coverage.

    An explicit multi-benchmark count makes AmbigNQ or TabMWP eligible even
    without disambiguation/table wording. In that case they remain useful suite
    variants, but a general QA/math benchmark should occupy the earlier core
    rank. Direct subtype evidence removes this deferral.
    """

    exemption = SPECIALIZATION_BREADTH_EXEMPTIONS.get(candidate.benchmark_id)
    specialization = SPECIALIZATION_GATES.get(candidate.benchmark_id)
    if not exemption or not specialization:
        return False
    task, required_count = exemption
    if profile.task_benchmark_counts.get(task, 0) < required_count:
        return False
    profile_field, accepted_values = specialization
    return set(getattr(profile, profile_field)).isdisjoint(accepted_values)


def _literature_evidence(record: BenchmarkRecord, hits: list[SearchHit]) -> tuple[float, list[str]]:
    """Return named-source or topical corroboration from live search hits.

    Exact benchmark-name mentions are strongest evidence. A hit retrieved from
    a method-derived query can also corroborate the benchmark's task fit when
    it contains one of the record's multi-token task phrases, even if it does
    not name the benchmark. This keeps online search useful without treating an
    arbitrary new paper as a fully specified benchmark record.
    """

    aliases = [record.name.casefold(), *(alias.casefold() for alias in record.aliases)]
    topical_phrases = [
        " ".join(re.findall(r"[a-z0-9]+", keyword.casefold()))
        for keyword in record.keywords
        if len(re.findall(r"[a-z0-9]+", keyword.casefold())) >= 2
    ]
    named: list[str] = []
    topical: list[str] = []
    for hit in hits:
        haystack = f"{hit.title} {hit.summary}".casefold()
        if any(re.search(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])", haystack) for alias in aliases):
            named.append(hit.url)
            continue
        normalized_haystack = " ".join(re.findall(r"[a-z0-9]+", haystack))
        if any(phrase in normalized_haystack for phrase in topical_phrases):
            topical.append(hit.url)
    if named:
        return 1.0, sorted(set([*named, *topical]))
    if topical:
        return 0.5, sorted(set(topical))
    return 0.0, []


def score_candidate(
    profile: CapabilityProfile,
    record: BenchmarkRecord,
    search_hits: list[SearchHit],
) -> ScoredCandidate:
    """Score one benchmark and expose every component used in the decision."""

    mismatches: list[str] = []
    if "image" in record.modalities and "image" not in profile.modalities:
        mismatches.append("image-dependent benchmark for a non-image method")
    if record.task_families == ["math_reasoning"] and "math_reasoning" not in profile.task_families:
        mismatches.append("math-only benchmark outside inferred task families")
    if "code" in record.modalities and "code" not in profile.modalities:
        mismatches.append("code benchmark for a method without code input or output")
    specialization = SPECIALIZATION_GATES.get(record.benchmark_id)
    if specialization:
        profile_field, accepted_values = specialization
        observed_values = set(getattr(profile, profile_field))
        breadth_exemption = SPECIALIZATION_BREADTH_EXEMPTIONS.get(record.benchmark_id)
        breadth_supported = bool(
            breadth_exemption
            and profile.task_benchmark_counts.get(breadth_exemption[0], 0) >= breadth_exemption[1]
        )
        if observed_values.isdisjoint(accepted_values) and not breadth_supported:
            mismatches.append(
                "specialized benchmark lacks visible method evidence for "
                + ", ".join(sorted(accepted_values))
            )
    for required_environment, (affected_tasks, generic_environments) in TASK_ENVIRONMENT_GATES.items():
        if required_environment not in profile.environments:
            continue
        if set(record.task_families).isdisjoint(affected_tasks):
            continue
        if required_environment in record.environments:
            continue
        if set(record.environments) & generic_environments:
            mismatches.append(
                f"generic environment does not satisfy explicit {required_environment} scope"
            )

    literature_score, literature_urls = _literature_evidence(record, search_hits)
    components = {
        "task": _coverage(profile.task_families, record.task_families),
        "modality": _coverage(profile.modalities, record.modalities, candidate_denominator=True),
        "interaction": _coverage(profile.interactions, record.interactions, candidate_denominator=True),
        "output": _coverage(profile.output_types, record.output_types, candidate_denominator=True),
        "environment": _environment_fit(profile.environments, record.environments),
        "capability": _coverage(profile.capabilities, record.capabilities, candidate_denominator=True),
        "metric": _coverage(profile.suggested_metrics, record.metrics, candidate_denominator=True),
        "literature": literature_score,
    }
    score = sum(components[key] * WEIGHTS[key] for key in WEIGHTS)
    if mismatches:
        score *= 0.20

    matched = {
        "task_families": sorted(set(profile.task_families) & set(record.task_families)),
        "modalities": sorted(set(profile.modalities) & set(record.modalities)),
        "interactions": sorted(set(profile.interactions) & set(record.interactions)),
        "output_types": sorted(set(profile.output_types) & set(record.output_types)),
        "environments": sorted(set(profile.environments) & set(record.environments)),
        "capabilities": sorted(set(profile.capabilities) & set(record.capabilities)),
        "metrics": sorted(set(profile.suggested_metrics) & set(record.metrics)),
    }
    evidence = [record.source_url, *literature_urls]
    return ScoredCandidate(
        benchmark_id=record.benchmark_id,
        name=record.name,
        score=round(score, 6),
        component_scores={key: round(value, 6) for key, value in components.items()},
        matched_requirements=matched,
        hard_mismatches=mismatches,
        evidence=sorted(set(evidence)),
        source_url=record.source_url,
        metrics=record.metrics,
        adaptation_hooks=record.adaptation_hooks,
    )


def rank_candidates(
    profile: CapabilityProfile,
    catalog: list[BenchmarkRecord],
    search_hits: list[SearchHit],
) -> list[ScoredCandidate]:
    """Rank candidates with coverage-first, balanced task triangulation.

    A global score sort can fill Top-K with variants of one high-scoring task.
    The first phase therefore covers all inferred task families. Explicit
    specialized capabilities receive the next slot. Two round-robin passes then
    add environment-compatible alternatives across tasks before the remaining
    records return to score order. Displayed scores stay unmodified.
    """

    remaining = sorted(
        [score_candidate(profile, record, search_hits) for record in catalog],
        key=lambda item: (-item.score, item.benchmark_id),
    )
    ranked: list[ScoredCandidate] = []
    target_tasks = set(profile.task_families)
    covered_tasks: set[str] = set()
    while remaining and covered_tasks < target_tasks:
        covering = [
            item
            for item in remaining
            if set(item.matched_requirements["task_families"]) - covered_tasks
            and not item.hard_mismatches
        ]
        if not covering:
            break
        best = sorted(
            covering,
            key=lambda item: (
                -len(set(item.matched_requirements["task_families"]) - covered_tasks),
                _deferred_breadth_variant(profile, item),
                -item.score,
                item.benchmark_id,
            ),
        )[0]
        remaining.remove(best)
        ranked.append(best)
        covered_tasks.update(best.matched_requirements["task_families"])

    for capability in sorted(set(profile.capabilities) & SPECIALIZED_CAPABILITIES):
        candidates = [
            item
            for item in remaining
            if capability in item.matched_requirements["capabilities"]
            and not item.hard_mismatches
            and (not profile.environments or item.matched_requirements["environments"])
        ]
        if not candidates:
            continue
        chosen = sorted(candidates, key=lambda item: (-item.score, item.benchmark_id))[0]
        remaining.remove(chosen)
        ranked.append(chosen)

    supplementary_rounds = {task: 0 for task in target_tasks}
    for round_number in (1, 2):
        for task in sorted(target_tasks):
            if supplementary_rounds[task] >= round_number:
                continue
            candidates = [
                item
                for item in remaining
                if task in item.matched_requirements["task_families"]
                and not item.hard_mismatches
                and (not profile.environments or item.matched_requirements["environments"])
            ]
            if not candidates:
                continue
            chosen = sorted(
                candidates,
                key=lambda item: (
                    _deferred_breadth_variant(profile, item),
                    -item.score,
                    item.benchmark_id,
                ),
            )[0]
            remaining.remove(chosen)
            ranked.append(chosen)
            for supported_task in set(chosen.matched_requirements["task_families"]) & target_tasks:
                supplementary_rounds[supported_task] = max(
                    supplementary_rounds[supported_task],
                    round_number,
                )

    ranked.extend(remaining)
    return ranked


def select_portfolio(
    profile: CapabilityProfile,
    ranked: list[ScoredCandidate],
    max_benchmarks: int = 6,
    minimum_score: float = 0.30,
    supplementary_minimum_score: float = 0.55,
) -> tuple[list[str], float, dict[str, str]]:
    """Select task coverage, explicit specializations, and triangulation.

    The first pass covers every inferred task family. The second reserves one
    benchmark for each explicit, method-specific capability such as multilingual
    code generation. The final pass adds at most two environment-compatible
    alternatives per task. This keeps a broad method from being evaluated by a
    single generic benchmark while excluding domain-specific alternatives whose
    environment has no support in the visible Introduction and Method.
    """

    target_tasks = set(profile.task_families) | set(profile.uncovered_task_families)
    explicit_counts = {
        task: count
        for task, count in profile.task_benchmark_counts.items()
        if task in target_tasks and count > 0
    }
    visible_minimum_size = sum(explicit_counts.get(task, 1) for task in target_tasks)
    effective_max_benchmarks = min(max(max_benchmarks, visible_minimum_size), 12)
    covered: set[str] = set()
    selected: list[str] = []
    roles: dict[str, str] = {}
    for candidate in ranked:
        if candidate.score < minimum_score or candidate.hard_mismatches:
            continue
        new_tasks = set(candidate.matched_requirements["task_families"]) - covered
        if not new_tasks:
            continue
        selected.append(candidate.benchmark_id)
        roles[candidate.benchmark_id] = "core_task_coverage"
        covered.update(new_tasks)
        if len(selected) >= effective_max_benchmarks or covered >= target_tasks:
            break

    ratio = 0.0 if not target_tasks else len(covered & target_tasks) / len(target_tasks)
    if covered < target_tasks:
        known_covered = covered & set(profile.task_families)
        if profile.declared_evaluation_breadth > len(target_tasks):
            for task in sorted(known_covered):
                if len(selected) >= effective_max_benchmarks:
                    break
                supplement = next(
                    (
                        candidate
                        for candidate in ranked
                        if candidate.benchmark_id not in selected
                        and task in candidate.matched_requirements["task_families"]
                        and task_normalized_score(candidate) >= supplementary_minimum_score
                        and not candidate.hard_mismatches
                    ),
                    None,
                )
                if supplement is None:
                    continue
                selected.append(supplement.benchmark_id)
                roles[supplement.benchmark_id] = f"declared_suite_breadth:{task}"
        rank_order = {candidate.benchmark_id: rank for rank, candidate in enumerate(ranked)}
        selected.sort(key=rank_order.__getitem__)
        return selected, round(ratio, 6), roles

    for capability in sorted(set(profile.capabilities) & SPECIALIZED_CAPABILITIES):
        for candidate in ranked:
            if len(selected) >= effective_max_benchmarks:
                break
            if candidate.benchmark_id in selected:
                continue
            if task_normalized_score(candidate) < supplementary_minimum_score or candidate.hard_mismatches:
                continue
            if capability not in candidate.matched_requirements["capabilities"]:
                continue
            selected.append(candidate.benchmark_id)
            roles[candidate.benchmark_id] = f"specialized_capability:{capability}"
            break

    selected_counts = {
        task: sum(
            task in candidate.matched_requirements["task_families"]
            for candidate in ranked
            if candidate.benchmark_id in selected
        )
        for task in covered & target_tasks
    }
    supplementary_by_task: dict[str, list[ScoredCandidate]] = {}
    for task in sorted(covered & target_tasks):
        if task in explicit_counts:
            remaining_slots = max(explicit_counts[task] - selected_counts.get(task, 0), 0)
        else:
            remaining_slots = 2
        if remaining_slots == 0:
            continue
        for candidate in ranked:
            if candidate.benchmark_id in selected:
                continue
            if task_normalized_score(candidate) < supplementary_minimum_score or candidate.hard_mismatches:
                continue
            if task not in candidate.matched_requirements["task_families"]:
                continue
            if profile.environments and not candidate.matched_requirements["environments"]:
                continue
            supplementary_by_task.setdefault(task, []).append(candidate)
            if len(supplementary_by_task[task]) >= remaining_slots:
                break
    supplementary_ids = {
        candidate.benchmark_id
        for candidates in supplementary_by_task.values()
        for candidate in candidates
    }
    for candidate in ranked:
        if len(selected) >= effective_max_benchmarks:
            break
        if candidate.benchmark_id not in supplementary_ids or candidate.benchmark_id in selected:
            continue
        selected.append(candidate.benchmark_id)
        supported_tasks = sorted(
            task
            for task, items in supplementary_by_task.items()
            if any(item.benchmark_id == candidate.benchmark_id for item in items)
        )
        role_prefix = (
            "explicit_suite_cardinality"
            if any(task in explicit_counts for task in supported_tasks)
            else "supplementary_triangulation"
        )
        roles[candidate.benchmark_id] = role_prefix + ":" + ",".join(supported_tasks)

    rank_order = {candidate.benchmark_id: rank for rank, candidate in enumerate(ranked)}
    selected.sort(key=rank_order.__getitem__)
    return selected, round(ratio, 6), roles
