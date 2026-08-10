from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic import ValidationError

from .schema import (
    DomainProfile,
    PaperRecord,
    PaperSeedRecord,
    QueryPlan,
    SeedLibrarySelection,
    TopicSeed,
)
from .utils import clean_text, normalize_title, tokens


def default_seed_dir() -> Path:
    configured = os.getenv("AUTORESEARCH_SEED_DIR", "").strip()
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[2] / "data" / "paper_seed"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_topic_seeds(seed_dir: Path) -> list[TopicSeed]:
    topic_dir = seed_dir / "topics"
    if not topic_dir.exists():
        return []
    seeds: list[TopicSeed] = []
    for path in sorted(topic_dir.glob("*.json")):
        try:
            seed = TopicSeed.model_validate(_read_json(path))
        except (json.JSONDecodeError, OSError, ValidationError):
            seed = None
        if seed:
            seeds.append(seed)
    return seeds


def _load_paper_seeds(seed_dir: Path) -> list[PaperSeedRecord]:
    path = seed_dir / "papers.jsonl"
    if not path.exists():
        return []
    seeds: list[PaperSeedRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            seed = PaperSeedRecord.model_validate_json(line)
        except (ValueError, ValidationError):
            seed = None
        if seed:
            seeds.append(seed)
    return seeds


def _topic_seed_text(seed: TopicSeed) -> str:
    return " ".join(
        [
            seed.topic_id,
            seed.display_name,
            *seed.aliases,
            *seed.core_queries,
            *seed.benchmark_terms,
            *seed.weakness_lenses,
        ]
    )


def _topic_score(topic: str, profile: DomainProfile | None, seed: TopicSeed) -> float:
    topic_terms = set(tokens(topic))
    seed_terms = set(tokens(_topic_seed_text(seed)))
    score = float(len(topic_terms & seed_terms))
    if profile:
        profile_terms = set(tokens(f"{profile.domain_id} {profile.domain_name} {profile.seed_topic}"))
        score += len(profile_terms & seed_terms) * 0.5
        if profile.domain_id and profile.domain_id in seed.topic_id:
            score += 4.0
    normalized_topic = normalize_title(topic)
    if normalize_title(seed.display_name) in normalized_topic or seed.topic_id.replace("-", " ") in normalized_topic:
        score += 3.0
    return score


def _select_topic_seed(
    topic: str,
    profile: DomainProfile | None,
    topic_seeds: list[TopicSeed],
) -> tuple[TopicSeed | None, list[str]]:
    if not topic_seeds:
        return None, []
    scored = sorted(
        ((seed, _topic_score(topic, profile, seed)) for seed in topic_seeds),
        key=lambda row: row[1],
        reverse=True,
    )
    best, best_score = scored[0]
    if best_score < 2.0:
        return None, []
    matched = [seed.topic_id for seed, score in scored if score > 0]
    return best, matched[:5]


def _paper_matches_topic(paper: PaperSeedRecord, topic_seed: TopicSeed | None, topic: str) -> bool:
    if topic_seed:
        wanted = {topic_seed.topic_id, *topic_seed.aliases}
        if wanted & set(paper.topics):
            return True
        normalized_title = normalize_title(paper.title)
        return any(normalize_title(title) == normalized_title for title in topic_seed.must_include_papers)
    topic_terms = set(tokens(topic))
    paper_terms = set(tokens(" ".join([paper.title, *paper.topics, *paper.known_claims])))
    return len(topic_terms & paper_terms) >= 2


def _seed_to_paper(seed: PaperSeedRecord) -> PaperRecord:
    abstract_parts = [
        seed.why_seed,
        "Known claims: " + "; ".join(seed.known_claims) if seed.known_claims else "",
        "Known limitations: " + "; ".join(seed.known_limitations) if seed.known_limitations else "",
        "Datasets: " + ", ".join(seed.datasets) if seed.datasets else "",
        "Metrics: " + ", ".join(seed.metrics) if seed.metrics else "",
    ]
    return PaperRecord(
        title=seed.title,
        abstract=clean_text(" ".join(part for part in abstract_parts if part)),
        year=seed.year,
        venue=seed.venue,
        authors=seed.authors,
        url=seed.url,
        pdf_url=seed.pdf_url,
        doi=seed.doi,
        pmid=seed.pmid,
        pmcid=seed.pmcid,
        arxiv_id=seed.arxiv_id,
        source="paper_seed",
        source_records=["paper_seed"],
        raw={"paper_seed": seed.model_dump()},
    )


def load_seed_selection(
    topic: str,
    profile: DomainProfile | None = None,
    seed_dir: Path | None = None,
) -> SeedLibrarySelection:
    root = seed_dir or default_seed_dir()
    if not root.exists():
        return SeedLibrarySelection(seed_dir=str(root), status="missing")
    try:
        topic_seeds = _load_topic_seeds(root)
        paper_seeds = _load_paper_seeds(root)
        topic_seed, matched_topics = _select_topic_seed(topic, profile, topic_seeds)
        selected_papers = [
            paper for paper in paper_seeds if _paper_matches_topic(paper, topic_seed, topic)
        ]
        status = "ok" if topic_seed or selected_papers else "no_match"
        return SeedLibrarySelection(
            seed_dir=str(root),
            topic_seed=topic_seed,
            paper_seeds=selected_papers,
            matched_topics=matched_topics,
            added_queries=list(topic_seed.core_queries if topic_seed else []),
            added_papers=len(selected_papers),
            status=status,
        )
    except Exception as exc:  # noqa: BLE001 - seed library should not stop a search run.
        return SeedLibrarySelection(seed_dir=str(root), status="failed", error=str(exc))


def seed_records_to_papers(selection: SeedLibrarySelection | None) -> list[PaperRecord]:
    if not selection:
        return []
    return [_seed_to_paper(seed) for seed in selection.paper_seeds]


def extend_query_plan_with_seed(plan: QueryPlan, selection: SeedLibrarySelection | None, max_total: int = 12) -> QueryPlan:
    if not selection or not selection.added_queries:
        return plan
    seen = {normalize_title(query) for query in plan.queries}
    queries = list(plan.queries)
    for query in selection.added_queries:
        normalized = normalize_title(query)
        if normalized and normalized not in seen:
            queries.append(query)
            seen.add(normalized)
        if len(queries) >= max_total:
            break
    return QueryPlan(topic=plan.topic, queries=queries, perspectives=plan.perspectives)
