---
name: auto-bench
description: Derive, design, and automatically validate benchmark portfolios from a research paper's Introduction and Method or from a proposed method idea. Use when asked to recommend benchmarks, datasets, metrics, baselines, evaluation protocols, benchmark adaptations, or new benchmark construction for a paper or research method; when asked to check whether recommended benchmarks match those used by a source paper; or when the user mentions Auto-Bench, auto bench, benchmark discovery, benchmark design, benchmark selection, Method-to-Benchmark, 根据论文方法找 benchmark, 根据创新点设计评测, or 自动核对论文 benchmark. Produce a portfolio rather than a single benchmark and perform source-paper comparison automatically without requesting user scoring.
---

# Auto-Bench

## Objective

Turn a paper's visible method claims into an evidence-backed evaluation package:

1. infer task, modality, interaction, output, environment, and capability requirements;
2. recommend a task-diverse benchmark portfolio and metrics;
3. choose direct reuse, base-benchmark adaptation, or new-benchmark synthesis;
4. when a source paper exists, compare the sealed recommendation with its reported benchmarks automatically;
5. feed misses, extras, catalog gaps, and route errors into the next iteration.

Do not reduce a multi-task method to one benchmark. Do not request a user-authored Match/Partial/Mismatch submission.

## Select the mode

- **Existing paper, blind recovery:** Use only Introduction and Method for matching. Reveal Experiment/Evaluation evidence after writing the plan.
- **Existing paper, practical evaluation design:** Still generate the plan from Introduction and Method first, then use the paper's Experiment/Evaluation section as automatic validation evidence.
- **New method or innovation:** Generate the benchmark portfolio, metrics, baselines, and construction route. Mark literature comparison `NOT_APPLICABLE` when no source-paper benchmark gold exists.
- **Catalog gap:** Search official benchmark papers or project pages, but keep unverified leads outside selected recommendations until task, metric, data/harness, split, access, license, and source fields are known.

## Workflow

### 1. Build the matcher-visible input

Extract only Introduction and Method. If given a PDF, use the PDF capability to identify section boundaries. If given a paper URL, use the official paper source.

Write a JSON input following [references/input-schema.md](references/input-schema.md). Redact paper title, authors, source ID, benchmark names, result numbers, tables, and experiment-only text for blind recovery.

Run the leakage gate and matcher:

```bash
SKILL_ROOT="${CODEX_HOME:-$HOME/.codex}/skills/auto-bench"
python3 "$SKILL_ROOT/scripts/run_auto_bench.py" match \
  --input /PATH/method_input.json \
  --output /PATH/auto_bench_plan
```

Add `--online` only when live arXiv metadata search is useful. Preserve the resulting `benchmark_plan.json` before reading source-paper benchmark labels.

### 2. Inspect the evaluation profile

Check all of these fields before accepting the portfolio:

- `task_families` and `uncovered_task_families`
- declared per-task benchmark counts and total evaluation breadth
- modalities, interactions, output types, and environments
- required capabilities and suggested metrics
- evidence terms copied from Introduction/Method

Treat an uncovered task as a route signal, not as a generic text task.

### 3. Interpret the route

- `direct_portfolio`: catalog benchmarks cover all explicit task families with sufficient compatibility.
- `base_benchmark_adaptation`: at least one credible base benchmark exists, but tasks, environments, or interaction contracts remain uncovered.
- `new_benchmark_synthesis`: no catalog task family covers the central construct.

For adaptation or synthesis, specify:

- base benchmark and retained official semantics;
- added task family, interaction wrapper, or challenge split;
- train/development-only data source policy;
- record provenance and deterministic expected-output checks;
- primary, robustness, efficiency, and safety metrics;
- frozen validation/test protocol and stop thresholds.

Never seed generated records from test, hidden, or holdout examples.

### 4. Automatically compare with the source paper

After the plan is sealed, inspect the source paper's Experiment, Evaluation, Dataset, Benchmark, and table-caption evidence. Record every paper benchmark, including catalog-external ones, using [references/paper-evidence-schema.md](references/paper-evidence-schema.md).

Run:

```bash
python3 "$SKILL_ROOT/scripts/review_plan.py" \
  --plan /PATH/auto_bench_plan/benchmark_plan.json \
  --paper-evidence /PATH/paper_evidence.json \
  --output-json /PATH/automatic_literature_review.json \
  --output-markdown /PATH/automatic_literature_review.md \
  --evidence-class fresh_holdout
```

Use `feedback_regression` after modifying the skill based on revealed answers. Never present a feedback regression as fresh generalization evidence.

### 5. Act on typed errors

- `BLIND_PROTOCOL_FAILURE`: restore Introduction/Method-only isolation first.
- `CATALOG_GAP`: add or adapt a paper-backed benchmark only after completing its record.
- `UNMODELED_TASK_INFERENCE_GAP`: improve task-family extraction using method-visible language.
- `PORTFOLIO_RECALL_GAP`: improve coverage, modality, environment, or declared-breadth reasoning.
- `PORTFOLIO_PRECISION_GAP`: tighten specialization and environment gates.
- `ROUTE_ERROR`: correct direct reuse versus adaptation/synthesis logic.

Make generic rule changes. Do not encode a hidden benchmark name as a paper-specific shortcut.

### 6. Deliver the result

Follow [references/output-contract.md](references/output-contract.md). Always report:

- source paper and visible sections, when applicable;
- inferred evaluation profile;
- selected portfolio with role and primary source;
- metric matrix and execution requirements;
- route and, if needed, benchmark-construction plan;
- automatic literature decision and exact missing/extra items;
- whether evidence is `fresh_holdout`, `feedback_regression`, or `not_applicable`;
- next optimization or experiment gate.

## Resources

- `scripts/run_auto_bench.py`: generate a benchmark plan or execute adaptation/synthesis.
- `scripts/review_plan.py`: compare a sealed plan with paper evidence automatically.
- `assets/benchmark_catalog.json`: portable literature-grounded benchmark catalog.
- `references/input-schema.md`: matcher-visible input contract.
- `references/paper-evidence-schema.md`: post-match source-evidence contract.
- `references/output-contract.md`: required answer structure and decision semantics.
