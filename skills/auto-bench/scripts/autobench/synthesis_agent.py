"""Agent 6: plan base-benchmark adaptation and provenance-preserving synthesis."""

from __future__ import annotations

import copy
import re
from typing import Any, Iterable

from .match_agent import task_normalized_score
from .models import BenchmarkRecord, CapabilityProfile, ScoredCandidate


DIRECT_COVERAGE = 1.0
DIRECT_MIN_SCORE = 0.44
BASE_MIN_SCORE = 0.30


def validate_synthesis_source(source_benchmark: str, source_split: str) -> None:
    """Require named, non-test source data before creating synthetic drafts."""

    if not str(source_benchmark).strip():
        raise ValueError("source_benchmark must be non-empty")
    if not str(source_split).strip():
        raise ValueError("source_split must be non-empty")
    split_tokens = set(re.findall(r"[a-z0-9]+", str(source_split).casefold()))
    if split_tokens & {"test", "holdout", "hidden"}:
        raise ValueError("test, holdout, and hidden splits may not seed synthetic records")


def decide_route(
    profile: CapabilityProfile,
    ranked: list[ScoredCandidate],
    selected_ids: list[str],
    coverage_ratio: float,
) -> tuple[str, str]:
    """Choose direct reuse, base adaptation, or new synthesis from evidence."""

    selected = [candidate for candidate in ranked if candidate.benchmark_id in selected_ids]
    normalized_selected_scores = [
        task_normalized_score(candidate)
        for candidate in selected
        if candidate.component_scores["task"] > 0
    ]
    minimum_selected = min(normalized_selected_scores, default=0.0)
    top_score = ranked[0].score if ranked else 0.0
    if not profile.task_families:
        return (
            "new_benchmark_synthesis",
            "no catalog task family covers the explicitly stated method domain",
        )
    if coverage_ratio >= DIRECT_COVERAGE and minimum_selected >= DIRECT_MIN_SCORE:
        return (
            "direct_portfolio",
            f"portfolio covers {coverage_ratio:.1%} of inferred task families; "
            f"weakest task-normalized selected compatibility is {minimum_selected:.3f}",
        )
    if selected_ids and ranked and ranked[0].component_scores["task"] > 0 and top_score >= BASE_MIN_SCORE:
        return (
            "base_benchmark_adaptation",
            f"best existing match scores {top_score:.3f}, but portfolio coverage is {coverage_ratio:.1%}",
        )
    return (
        "new_benchmark_synthesis",
        f"no catalog benchmark reaches the base-adaptation threshold {BASE_MIN_SCORE:.2f}",
    )


def build_adaptation_plan(
    profile: CapabilityProfile,
    ranked: list[ScoredCandidate],
    selected_ids: list[str],
) -> dict[str, Any]:
    """Describe exactly what is retained and changed from base benchmarks."""

    selected = [candidate for candidate in ranked if candidate.benchmark_id in selected_ids]
    covered = {task for item in selected for task in item.matched_requirements["task_families"]}
    missing = sorted(
        (set(profile.task_families) - covered) | set(profile.uncovered_task_families)
    )
    return {
        "base_benchmarks": [item.benchmark_id for item in selected],
        "retain": [
            "official task semantics and unmodified test examples",
            "official metric definitions reported separately",
            "source IDs, split names, and license/access metadata",
        ],
        "add": [
            "method-specific interaction wrapper without exposing test labels",
            "capability-targeted challenge split for uncovered requirements",
            "cost, latency, and failure-state logging when the method is interactive",
        ],
        "missing_task_families": missing,
        "adaptation_hooks": sorted({hook for item in selected for hook in item.adaptation_hooks}),
        "split_policy": {
            "development": "derive transformations from train/development data only",
            "validation": "freeze prompts and thresholds before hidden-test execution",
            "test": "retain official test data; no synthesis seed may originate from test examples",
        },
    }


def build_synthesis_plan(profile: CapabilityProfile, adaptation_plan: dict[str, Any]) -> dict[str, Any]:
    """Build a data-generation plan with provenance and automatic QA gates."""

    target_tasks = adaptation_plan["missing_task_families"]
    return {
        "required": bool(adaptation_plan["missing_task_families"] or not adaptation_plan["base_benchmarks"]),
        "target_task_families": target_tasks,
        "construct_definition": {
            "status": "AUTOMATIC_CONSTRUCT_CHECK_PENDING" if target_tasks else "NOT_REQUIRED",
            "task_families": target_tasks,
            "uncovered_task_families": profile.uncovered_task_families,
            "modalities": profile.modalities,
            "interactions": profile.interactions,
            "output_types": profile.output_types,
            "capabilities": profile.capabilities,
            "candidate_metrics": profile.suggested_metrics,
            "evidence_terms": {
                key: value
                for key, value in profile.evidence_terms.items()
                if key.startswith("task:") or key.startswith("uncovered_task:")
            },
        },
        "source_policy": "use only licensed train/development records from named base benchmarks",
        "generation_modules": [
            {
                "name": "compositional_recombination",
                "purpose": "combine independent train-split constraints while preserving executable gold checks",
            },
            {
                "name": "counterfactual_perturbation",
                "purpose": "change one controlled factor and regenerate the expected answer with a deterministic verifier",
            },
            {
                "name": "interaction_wrapper",
                "purpose": "convert static examples into tool or environment episodes with logged action contracts",
            },
        ],
        "record_schema": [
            "synthetic_id",
            "source_benchmark",
            "source_split",
            "source_record_ids",
            "transformation",
            "input",
            "expected_output",
            "deterministic_checks",
            "automatic_validation_status",
        ],
        "quality_gates": [
            "exact and near-duplicate filtering against every split",
            "deterministic execution or answer verification where available",
            "stratified semantic-judge audit by task family and difficulty",
            "agreement check across independent automatic judge passes before scaling",
            "frozen test set before method tuning",
        ],
        "profile_snapshot": {
            "task_families": profile.task_families,
            "task_benchmark_counts": profile.task_benchmark_counts,
            "declared_evaluation_breadth": profile.declared_evaluation_breadth,
            "uncovered_task_families": profile.uncovered_task_families,
            "modalities": profile.modalities,
            "interactions": profile.interactions,
            "output_types": profile.output_types,
            "capabilities": profile.capabilities,
            "suggested_metrics": profile.suggested_metrics,
        },
    }


def synthesize_records(
    base_records: Iterable[dict[str, Any]],
    source_benchmark: str,
    source_split: str,
    transformation: str = "interaction_wrapper",
) -> list[dict[str, Any]]:
    """Create traceable draft records using an executable generic transform.

    ``interaction_wrapper`` converts a static task into a two-action episode:
    the agent may inspect the task and then submit an answer. The source answer
    is nested as the terminal gold and checked for exact preservation.

    ``compositional_recombination`` pairs adjacent base tasks into one ordered
    multi-part task whose expected output is the ordered list of source answers.

    ``counterfactual_perturbation`` requires each source record to provide a
    validated ``counterfactual`` object with replacement input, expected output,
    and a non-empty deterministic check. This prevents free-form generation from
    silently inventing gold labels.
    """

    validate_synthesis_source(source_benchmark, source_split)
    records = list(base_records)
    if not records:
        raise ValueError("base_records must contain at least one record")
    output: list[dict[str, Any]] = []
    for record in records:
        if "id" not in record or "input" not in record or "expected_output" not in record:
            raise ValueError("base record requires id, input, and expected_output")

    if transformation == "compositional_recombination":
        for index in range(0, len(records), 2):
            group = records[index : index + 2]
            if len(group) < 2:
                continue
            output.append(
                {
                    "synthetic_id": f"syn-{source_benchmark}-{len(output) + 1:06d}",
                    "source_benchmark": source_benchmark,
                    "source_split": source_split,
                    "source_record_ids": [str(item["id"]) for item in group],
                    "transformation": transformation,
                    "input": {"ordered_subtasks": [copy.deepcopy(item["input"]) for item in group]},
                    "expected_output": {
                        "ordered_answers": [copy.deepcopy(item["expected_output"]) for item in group]
                    },
                    "deterministic_checks": ["ordered_source_answers_preserved", "two_source_records_present"],
                    "automatic_validation_status": "PENDING",
                }
            )
        return output

    for index, record in enumerate(records, start=1):
        if transformation == "interaction_wrapper":
            transformed_input = {
                "goal": copy.deepcopy(record["input"]),
                "initial_observation": "Task loaded. Inspect before submitting the final answer.",
                "allowed_actions": ["inspect", "submit"],
                "max_steps": 2,
            }
            transformed_output = {"final_answer": copy.deepcopy(record["expected_output"])}
            checks = ["source_expected_output_preserved", "episode_schema_valid", "max_steps_equals_2"]
        elif transformation == "counterfactual_perturbation":
            counterfactual = record.get("counterfactual")
            if not isinstance(counterfactual, dict):
                raise ValueError("counterfactual transform requires a counterfactual object")
            if not all(key in counterfactual for key in ("input", "expected_output", "deterministic_check")):
                raise ValueError("counterfactual requires input, expected_output, and deterministic_check")
            if not str(counterfactual["deterministic_check"]).strip():
                raise ValueError("counterfactual deterministic_check must be non-empty")
            transformed_input = copy.deepcopy(counterfactual["input"])
            transformed_output = copy.deepcopy(counterfactual["expected_output"])
            checks = [str(counterfactual["deterministic_check"]), "counterfactual_schema_valid"]
        else:
            raise ValueError(f"unknown synthesis transformation: {transformation}")
        output.append(
            {
                "synthetic_id": f"syn-{source_benchmark}-{index:06d}",
                "source_benchmark": source_benchmark,
                "source_split": source_split,
                "source_record_ids": [str(record["id"])],
                "transformation": transformation,
                "input": transformed_input,
                "expected_output": transformed_output,
                "deterministic_checks": checks,
                "automatic_validation_status": "PENDING",
            }
        )
    return output


def verify_synthetic_records(
    base_records: Iterable[dict[str, Any]],
    drafts: Iterable[dict[str, Any]],
    source_benchmark: str,
    source_split: str,
    transformation: str,
) -> dict[str, Any]:
    """Verify generated records against their exact source records.

    The verifier resolves every recorded source ID, checks route-specific input
    and gold preservation, confirms unique synthetic IDs, and re-applies the
    non-test split rule. It returns a compact record suitable for workflow
    manifests and automatic-validation evidence.
    """

    validate_synthesis_source(source_benchmark, source_split)
    sources = list(base_records)
    generated = list(drafts)
    source_by_id: dict[str, dict[str, Any]] = {}
    for source in sources:
        source_id = str(source.get("id", ""))
        if not source_id or source_id in source_by_id:
            raise ValueError("base record IDs must be non-empty and unique")
        source_by_id[source_id] = source

    synthetic_ids = [str(record.get("synthetic_id", "")) for record in generated]
    if any(not synthetic_id for synthetic_id in synthetic_ids):
        raise ValueError("synthetic_id must be non-empty")
    if len(synthetic_ids) != len(set(synthetic_ids)):
        raise ValueError("synthetic_id values must be unique")

    expected_count = len(sources) // 2 if transformation == "compositional_recombination" else len(sources)
    if len(generated) != expected_count:
        raise ValueError(
            f"unexpected synthetic record count for {transformation}: "
            f"expected {expected_count}, got {len(generated)}"
        )

    verified_outputs = 0
    for record in generated:
        if record.get("source_benchmark") != source_benchmark:
            raise ValueError("synthetic source_benchmark does not match the requested source")
        if record.get("source_split") != source_split:
            raise ValueError("synthetic source_split does not match the requested split")
        if record.get("transformation") != transformation:
            raise ValueError("synthetic transformation metadata is inconsistent")
        if record.get("automatic_validation_status") != "PENDING":
            raise ValueError("synthetic records must remain PENDING until automatic validation")
        checks = record.get("deterministic_checks")
        if not isinstance(checks, list) or not checks or not all(str(item).strip() for item in checks):
            raise ValueError("synthetic records require non-empty deterministic checks")
        source_ids = [str(item) for item in record.get("source_record_ids", [])]
        if not source_ids or any(source_id not in source_by_id for source_id in source_ids):
            raise ValueError("synthetic record references an unknown source record")

        if transformation == "interaction_wrapper":
            if len(source_ids) != 1:
                raise ValueError("interaction_wrapper requires exactly one source record")
            source = source_by_id[source_ids[0]]
            if record.get("input", {}).get("goal") != source["input"]:
                raise ValueError("interaction_wrapper did not preserve the source input")
            if record.get("expected_output", {}).get("final_answer") != source["expected_output"]:
                raise ValueError("interaction_wrapper did not preserve the source gold")
        elif transformation == "compositional_recombination":
            if len(source_ids) != 2:
                raise ValueError("compositional_recombination requires two source records")
            source_group = [source_by_id[source_id] for source_id in source_ids]
            if record.get("input", {}).get("ordered_subtasks") != [item["input"] for item in source_group]:
                raise ValueError("compositional_recombination input order is inconsistent")
            expected = [item["expected_output"] for item in source_group]
            if record.get("expected_output", {}).get("ordered_answers") != expected:
                raise ValueError("compositional_recombination gold order is inconsistent")
        elif transformation == "counterfactual_perturbation":
            if len(source_ids) != 1:
                raise ValueError("counterfactual_perturbation requires exactly one source record")
            counterfactual = source_by_id[source_ids[0]].get("counterfactual")
            if not isinstance(counterfactual, dict):
                raise ValueError("counterfactual source metadata is missing")
            if record.get("input") != counterfactual.get("input"):
                raise ValueError("counterfactual input is inconsistent with its source")
            if record.get("expected_output") != counterfactual.get("expected_output"):
                raise ValueError("counterfactual gold is inconsistent with its source")
        else:
            raise ValueError(f"unknown synthesis transformation: {transformation}")
        verified_outputs += 1

    return {
        "status": "PASS",
        "source_benchmark": source_benchmark,
        "source_split": source_split,
        "transformation": transformation,
        "base_record_count": len(sources),
        "synthetic_record_count": len(generated),
        "unique_synthetic_ids": True,
        "source_ids_resolved": True,
        "verified_expected_outputs": verified_outputs,
        "automatic_validation_status": "PENDING",
    }
