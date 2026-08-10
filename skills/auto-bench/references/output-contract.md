# Output contract

Return one concise research-facing report with the following sections.

## 1. Input provenance

- paper title and official URL, when applicable;
- matcher-visible sections;
- confirmation that benchmark evidence was loaded only after plan generation.

## 2. Evaluation profile

List task families, uncovered tasks, modalities, interactions, outputs, environments, capabilities, declared suite breadth, and the exact Introduction/Method phrases supporting them.

## 3. Benchmark portfolio

Use a table:

| Priority | Benchmark | Portfolio role | Construct covered | Metrics | Source | Execution needs |
|---|---|---|---|---|---|---|

Recommend a portfolio, not a single benchmark, unless the method truly has one atomic construct.

## 4. Route and construction plan

State one route: `direct_portfolio`, `base_benchmark_adaptation`, or `new_benchmark_synthesis`.

For adaptation/synthesis include:

- source train/development records;
- transformation modules;
- record schema and provenance;
- deterministic verifier;
- data split and contamination controls;
- benchmark size and stratification plan;
- success, robustness, efficiency, and safety metrics;
- early stop or kill thresholds.

## 5. Automatic literature comparison

Report `MATCH`, `PARTIAL`, `MISMATCH`, or `NOT_APPLICABLE`, followed by:

- paper benchmarks recovered;
- paper benchmarks missing;
- recommendations not used by the paper;
- catalog-external task families recovered or missed;
- route agreement;
- typed error list.

Decision semantics:

- `MATCH`: blind protocol clean, modeled benchmarks covered, catalog-external task families inferred, route correct, and no erroneous selected benchmark.
- `PARTIAL`: at least one valid construct recovered but one or more recall, precision, task-family, or route gaps remain.
- `MISMATCH`: no valid paper evaluation construct recovered or blind isolation failed.
- `NOT_APPLICABLE`: no existing source paper supplies benchmark gold.

## 6. Evidence label and next gate

State whether the result is fresh evidence or feedback regression. Define the next action and measurable pass condition. Do not claim generalization from feedback regression.
