"""Agent 2: turn a capability profile into benchmark-search queries."""

from __future__ import annotations

from .models import CapabilityProfile


TASK_SEARCH_ALIASES = {
    "toxicity_reduction": (
        "toxic degeneration",
        "toxic language generation",
        "text detoxification",
    ),
}


def build_queries(profile: CapabilityProfile, max_queries: int = 8) -> list[str]:
    """Build compact, task-led literature queries without paper identity."""

    queries: list[str] = []
    modality = " ".join(profile.modalities)
    interaction = " ".join(profile.interactions)
    target_tasks = [*profile.task_families, *profile.uncovered_task_families]
    for task in target_tasks:
        readable = task.replace("_", " ")
        queries.append(f'"{readable}" benchmark dataset evaluation {modality}')
    for task in target_tasks:
        for alias in TASK_SEARCH_ALIASES.get(task, ()):
            queries.append(f'"{alias}" benchmark dataset evaluation {modality}')
    for task in target_tasks:
        readable = task.replace("_", " ")
        if interaction != "static":
            queries.append(f'"{readable}" agent benchmark {interaction}')
    if profile.capabilities:
        traits = " ".join(item.replace("_", " ") for item in profile.capabilities[:3])
        queries.append(f"agent benchmark {traits}")
    deduped: list[str] = []
    for query in queries:
        normalized = " ".join(query.split())
        if normalized not in deduped:
            deduped.append(normalized)
    return deduped[:max_queries]
