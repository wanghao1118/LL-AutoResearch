"""Command-line interface for Auto-Bench."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .auto_literature_review import write_review
from .models import MethodInput
from .pipeline import AutoBenchPipeline
from .review_gate import (
    evaluate_review_matrix,
    evaluate_reviews,
    load_review_scope,
    load_reviews,
    write_review_report,
)
from .synthesis_agent import synthesize_records, verify_synthetic_records
from .workflow import SYNTHESIS_TRANSFORMATIONS, run_workflow


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Blind method-to-benchmark matching workflow")
    subparsers = parser.add_subparsers(dest="command", required=True)

    match = subparsers.add_parser("match", help="generate a benchmark plan")
    match.add_argument("--input", required=True)
    match.add_argument("--catalog", default="configs/benchmark_catalog.json")
    match.add_argument("--output", required=True)
    match.add_argument("--online", action="store_true")

    run = subparsers.add_parser(
        "run",
        help="run matching, optional synthesis, and automatic-validation preparation",
    )
    run.add_argument("--input", required=True)
    run.add_argument("--catalog", default="configs/benchmark_catalog.json")
    run.add_argument("--output", required=True)
    run.add_argument("--online", action="store_true")
    run.add_argument("--base-records", help="train/development JSONL used when synthesis is required")
    run.add_argument("--source-benchmark")
    run.add_argument("--source-split")
    run.add_argument(
        "--transformation",
        action="append",
        choices=SYNTHESIS_TRANSFORMATIONS,
        help="repeat to execute multiple synthesis modules",
    )

    synthesize = subparsers.add_parser("synthesize", help="create provenance-preserving draft records")
    synthesize.add_argument("--input", required=True, help="base JSONL records")
    synthesize.add_argument("--source-benchmark", required=True)
    synthesize.add_argument("--source-split", required=True)
    synthesize.add_argument(
        "--transformation",
        choices=("interaction_wrapper", "compositional_recombination", "counterfactual_perturbation"),
        default="interaction_wrapper",
    )
    synthesize.add_argument("--output", required=True)

    auto_review = subparsers.add_parser(
        "auto-review",
        help="compare a sealed blind evaluation with source-paper evidence automatically",
    )
    auto_review.add_argument("--evaluation", required=True)
    auto_review.add_argument("--output-json", required=True)
    auto_review.add_argument("--output-markdown", required=True)
    auto_review.add_argument(
        "--evidence-class",
        choices=("feedback_regression", "untouched_holdout", "fresh_holdout"),
        required=True,
    )

    review = subparsers.add_parser(
        "review",
        help="legacy independent-review evaluator; not required by the current workflow",
    )
    review.add_argument("--input", required=True, action="append")
    review.add_argument("--scope", help="frozen review_scope.json used to detect omitted items")
    review.add_argument("--output", required=True)
    review.add_argument("--report", help="optional readable Markdown verdict")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Dispatch CLI commands and return a process exit status."""

    args = _build_parser().parse_args(argv)
    if args.command == "match":
        method_input = MethodInput.from_dict(json.loads(Path(args.input).read_text(encoding="utf-8")))
        pipeline = AutoBenchPipeline(args.catalog)
        plan = pipeline.run(method_input, online_search=args.online)
        paths = pipeline.write_outputs(plan, args.output)
        print(json.dumps({key: str(value) for key, value in paths.items()}, ensure_ascii=False))
        return 0
    if args.command == "run":
        method_input = MethodInput.from_dict(json.loads(Path(args.input).read_text(encoding="utf-8")))
        manifest = run_workflow(
            method_input,
            args.catalog,
            args.output,
            online_search=args.online,
            base_records_path=args.base_records,
            source_benchmark=args.source_benchmark,
            source_split=args.source_split,
            transformations=args.transformation,
        )
        print(json.dumps(manifest, ensure_ascii=False))
        return 2 if manifest["synthesis_execution"]["status"] == "BASE_RECORDS_REQUIRED" else 0
    if args.command == "synthesize":
        records = [json.loads(line) for line in Path(args.input).read_text(encoding="utf-8").splitlines() if line.strip()]
        drafts = synthesize_records(
            records,
            args.source_benchmark,
            args.source_split,
            transformation=args.transformation,
        )
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in drafts), encoding="utf-8")
        verification = verify_synthetic_records(
            records,
            drafts,
            args.source_benchmark,
            args.source_split,
            args.transformation,
        )
        verification_path = target.with_suffix(".verification.json")
        verification_path.write_text(
            json.dumps(verification, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "output": str(target),
                    "records": len(drafts),
                    "verification": str(verification_path),
                    "verification_status": verification["status"],
                },
                ensure_ascii=False,
            )
        )
        return 0
    if args.command == "auto-review":
        verdict = write_review(
            args.evaluation,
            args.output_json,
            args.output_markdown,
            evidence_class=args.evidence_class,
        )
        print(
            json.dumps(
                {
                    "status": verdict["status"],
                    "decision_counts": verdict["decision_counts"],
                    "human_submission_required": False,
                },
                ensure_ascii=False,
            )
        )
        return 0
    reviews = []
    for input_path in args.input:
        reviews.extend(load_reviews(input_path))
    expected_pairs = load_review_scope(args.scope) if args.scope else None
    if reviews and all("case_id" in review and "benchmark_id" in review for review in reviews):
        verdict = evaluate_review_matrix(reviews, expected_pairs=expected_pairs)
    else:
        verdict = evaluate_reviews(reviews)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(verdict, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path = Path(args.report) if args.report else target.with_suffix(".md")
    write_review_report(report_path, verdict)
    print(json.dumps({"verdict": verdict, "report": str(report_path)}, ensure_ascii=False))
    return 0 if verdict["status"] == "APPROVED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
