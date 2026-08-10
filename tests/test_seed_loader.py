import json

from autoresearch.schema import QueryPlan
from autoresearch.seed_loader import (
    extend_query_plan_with_seed,
    load_seed_selection,
    seed_records_to_papers,
)


def test_seed_loader_matches_topic_and_adds_queries(tmp_path):
    seed_dir = tmp_path / "paper_seed"
    topic_dir = seed_dir / "topics"
    topic_dir.mkdir(parents=True)
    (topic_dir / "medical.json").write_text(
        json.dumps(
            {
                "topic_id": "medical-vlm-temporal-lesion",
                "display_name": "医学 VLM 时序病灶变化分析",
                "aliases": ["medical VLM temporal lesion change"],
                "core_queries": ["medical VLM longitudinal lesion change"],
                "must_include_papers": ["Seed Paper"],
            }
        ),
        encoding="utf-8",
    )
    (seed_dir / "papers.jsonl").write_text(
        json.dumps(
            {
                "title": "Seed Paper",
                "topics": ["medical-vlm-temporal-lesion"],
                "roles": ["benchmark_context"],
                "why_seed": "Important benchmark context.",
                "known_limitations": ["No lesion-level temporal metric by default."],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    selection = load_seed_selection(
        "medical VLM temporal lesion change analysis",
        seed_dir=seed_dir,
    )
    papers = seed_records_to_papers(selection)
    plan = extend_query_plan_with_seed(
        QueryPlan(topic="medical VLM", queries=["medical VLM"], perspectives=[]),
        selection,
    )

    assert selection.status == "ok"
    assert selection.topic_seed is not None
    assert selection.added_papers == 1
    assert papers[0].source_records == ["paper_seed"]
    assert "Important benchmark context" in papers[0].abstract
    assert "medical VLM longitudinal lesion change" in plan.queries
