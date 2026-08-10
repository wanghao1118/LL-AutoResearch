#!/usr/bin/env python3
"""Exercise direct, base-adaptation, and new-synthesis workflow routes.

The direct route is covered by the three literature blind cases. This script
adds two method-only scenarios: a partially covered interactive laboratory
method that should adapt a sequential-decision benchmark, and an audio/music
method outside the catalog that should trigger a new benchmark proposal. It
also runs the draft-record synthesis module and verifies source provenance.
"""

from __future__ import annotations

import json
from pathlib import Path

from autobench.models import MethodInput
from autobench.pipeline import AutoBenchPipeline
from autobench.synthesis_agent import synthesize_records


ROOT = Path(__file__).resolve().parent


def main() -> int:
    pipeline = AutoBenchPipeline(ROOT / "configs/benchmark_catalog.json")
    demos = [
        MethodInput(
            case_id="route_base_adaptation",
            introduction=(
                "We study an agent that follows a laboratory protocol in an interactive simulator. "
                "The agent chooses sequential actions, observes assay outcomes, and revises the experimental procedure."
            ),
            method=(
                "The method decomposes a wet lab objective into reagent preparation, instrument operation, "
                "measurement, and verification subgoals. It uses action-observation trajectories and long horizon planning."
            ),
        ),
        MethodInput(
            case_id="route_new_synthesis",
            introduction=(
                "We study conditional polyphonic music generation from audio motifs and affect descriptions."
            ),
            method=(
                "The method emits multi-track audio events and preserves harmonic structure, timbre, and long-range rhythm."
            ),
        ),
    ]
    summary: list[dict] = []
    output_root = ROOT / "assets/output/route_demos"
    for demo in demos:
        plan = pipeline.run(demo)
        paths = pipeline.write_outputs(plan, output_root / demo.case_id)
        summary.append(
            {
                "case_id": demo.case_id,
                "route": plan.route,
                "coverage_ratio": plan.coverage_ratio,
                "selected_benchmarks": plan.selected_benchmarks,
                "synthesis_required": plan.synthesis_plan["required"],
                "status": plan.status,
                "outputs": {key: path.relative_to(ROOT).as_posix() for key, path in paths.items()},
            }
        )

    base_records = [
        {"id": "train-001", "input": {"goal": "prepare sample A"}, "expected_output": {"state": "prepared"}},
        {"id": "train-002", "input": {"goal": "measure sample B"}, "expected_output": {"state": "measured"}},
    ]
    drafts = synthesize_records(
        base_records,
        source_benchmark="scienceworld",
        source_split="train",
        transformation="interaction_wrapper",
    )
    synthesis_path = output_root / "synthesis_draft.jsonl"
    synthesis_path.parent.mkdir(parents=True, exist_ok=True)
    synthesis_path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in drafts),
        encoding="utf-8",
    )
    if not all(
        record["source_split"] == "train"
        and record["automatic_validation_status"] == "PENDING"
        for record in drafts
    ):
        raise ValueError("synthesis provenance or review state failed")

    summary_path = output_root / "route_demo_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for item in summary:
        print(json.dumps(item, ensure_ascii=False))
    print(
        json.dumps(
            {
                "synthesis_records": len(drafts),
                "synthesis_path": synthesis_path.relative_to(ROOT).as_posix(),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
