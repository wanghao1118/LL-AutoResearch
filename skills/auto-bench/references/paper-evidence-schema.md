# Paper evidence schema

Create this file only after the matcher has written and sealed its plan.

```json
{
  "schema_version": "1.0",
  "case_id": "paper_or_method_id",
  "source_title": "Official paper title",
  "source_url": "https://arxiv.org/abs/0000.00000",
  "source_input_sections": ["Introduction", "Method"],
  "gold_evidence_sections": ["Experiments", "Datasets", "Evaluation"],
  "expected_route": "direct_portfolio",
  "actual_benchmarks": [
    {
      "benchmark_id": "catalog_id_or_null",
      "benchmark_name": "Benchmark name used by the paper",
      "role": "primary",
      "task_family": "task_family_label",
      "evidence_section": "Experiments > Datasets",
      "evidence_locator": "Table 1 or page 7",
      "evidence_summary": "Paraphrase of how the paper uses this benchmark"
    }
  ]
}
```

## Required evidence

- Use the official paper or official project source.
- Record every benchmark used for the main method evaluation, including catalog-external benchmarks.
- Use `primary`, `secondary`, or `unmodeled` for `role`.
- Set `benchmark_id` to a catalog ID only when it is the same benchmark. Otherwise use `null` and role `unmodeled`.
- Give every benchmark a task family and evidence section.
- Prefer a section/table/page locator plus a concise paraphrase over a long quotation.
- Infer `expected_route` when omitted:
  - all constructs covered by catalog: `direct_portfolio`;
  - mixed covered and uncovered constructs: `base_benchmark_adaptation`;
  - all central constructs outside catalog: `new_benchmark_synthesis`.

## Evidence classes

- `fresh_holdout`: skill and paper selection were frozen before benchmark evidence was revealed.
- `feedback_regression`: rules changed after evidence reveal; use only to verify the fix.
- `untouched_holdout`: a separately preserved holdout selected before the current feedback change.
