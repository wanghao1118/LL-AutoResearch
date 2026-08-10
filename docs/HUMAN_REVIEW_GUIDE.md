# Human Literature Benchmark Audit

## Purpose

The human audit checks whether Auto-Bench can recover the benchmarks actually
used by an existing paper. It is deliberately separated into two phases:

1. **Blind matching:** the worker receives only anonymized Introduction and
   Method text. Paper title, authors, source ID, experiment sections, and actual
   benchmark labels remain outside its sandbox.
2. **Source-revealed audit:** after the worker exits, the report identifies the
   source paper and shows the experiment-derived benchmark gold beside the
   Auto-Bench recommendations.

## What You Should Do

### Round 3 feedback regression

Open:

`assets/output/literature_audit/literature_audit.html`

For each of the three cases:

1. note that the source-paper and actual-benchmark checks are already marked as
   carried from the completed Round 2 audit because those scopes are unchanged;
2. compare the updated Auto-Bench Selected portfolio and Top-6 list with the
   displayed paper benchmark list;
3. record one judgement:
   - `MATCH`: the recommendation adequately recovers the paper's benchmark
     choices;
   - `PARTIAL`: important choices appear in Top-6 or Selected, but material
     misses or unnecessary additions remain;
   - `MISMATCH`: the recommendation misses the paper's central evaluation
     setting;
4. write a short note explaining important matches, misses, or extras.

The route, uncovered-task, adaptation, and synthesis sections are supporting
context for this literature comparison; they do not add another mandatory
checkbox. Reopen the source paper whenever you want to recheck the carried
evidence, but the page only asks for a fresh comparison of the changed output.

Click **Validate and download audit JSON**. Save the file as:

`assets/output/literature_audit/literature_audit_submission_round_3.json`

Then run:

```bash
python3 step6_finalize_literature_audit.py \
  --input assets/output/literature_audit/literature_audit_submission_round_3.json
```

The page begins with the Round 2 human judgement and the exact before/after
portfolio. In case 2, LeetcodeHardGym and MultiPL-E are now catalog records and
all six paper benchmarks are selected; ScienceWorld was removed. Cases 1 and 3
also changed under the coverage-balanced ranking, so all three current
comparisons receive a fresh judgement. The full numerical trace is in
`assets/output/literature_audit/iteration_comparison.md`.

Every downloaded file includes the current `audit_id`. The finalizer rejects a
Round 2 JSON against the Round 3 scope, so the old recommendation judgement is
not silently reused for the revised portfolio.

The final status is one of:

- `LITERATURE_AUDIT_CONFIRMED`;
- `LITERATURE_AUDIT_PARTIAL`;
- `LITERATURE_AUDIT_MISMATCH`;
- `HUMAN_LITERATURE_AUDIT_REQUIRED` when a case remains incomplete.

### Untouched holdout

Open this separate page:

`assets/output/untouched_holdout/human_audit/literature_audit.html`

It contains one paper that was selected and frozen before the first match. Open
the linked source, verify the benchmark evidence sections, compare the paper's
actual benchmarks with Selected and Top-6, and choose `MATCH`, `PARTIAL`, or
`MISMATCH`. The preserved machine result is `NEEDS_ITERATION`; do not change the
label merely because the result is weak.

Download the page output as
`literature_audit_submission_holdout_1.json`, place it under
`assets/output/untouched_holdout/human_audit/`, and finalize it with:

```bash
python3 step6_finalize_literature_audit.py \
  --input assets/output/untouched_holdout/human_audit/literature_audit_submission_holdout_1.json \
  --scope assets/output/untouched_holdout/human_audit/literature_audit.json \
  --output assets/output/untouched_holdout/human_audit/final_verdict.json
```

This holdout verdict is independent of the three-case Round 3 verdict.

### Current holdout-002 plan

The immutable first result is retained under
`assets/output/untouched_holdout_2/first_run_evaluation.json`. For validating the
current matcher and route, open:

`assets/output/untouched_holdout_2/current_human_audit/literature_audit.html`

Verify the linked CRITIC source and its QA, mathematical program synthesis, and
toxicity experiment sections. The page should show HotPotQA and GSM8K as modeled
matches, the remaining paper datasets as outside-catalog choices, and base
adaptation/synthesis for the uncovered toxicity task.

Download `literature_audit_submission_holdout_2_current.json`, then finalize:

```bash
python3 step6_finalize_literature_audit.py \
  --input assets/output/untouched_holdout_2/current_human_audit/literature_audit_submission_holdout_2_current.json \
  --scope assets/output/untouched_holdout_2/current_human_audit/literature_audit.json \
  --output assets/output/untouched_holdout_2/current_human_audit/final_verdict.json
```

The original pre-feedback audit remains available at
`assets/output/untouched_holdout_2/human_audit/literature_audit.html`; it is an
audit of the frozen first result rather than the current matcher.

## New-Method Suitability Review

When applying Auto-Bench to a genuinely new method, there is no paper benchmark
gold to reveal. `python3 -m autobench run` generates the separate two-person
construct-suitability package together with the plan. For an existing plan it
can also be regenerated with:

```bash
python3 scripts/prepare_new_method_suitability_review.py \
  --plan assets/output/METHOD_CASE/benchmark_plan.json \
  --output-dir assets/output/METHOD_CASE/suitability_review
```

That suitability gate is not used to score the three literature-recovery cases.
