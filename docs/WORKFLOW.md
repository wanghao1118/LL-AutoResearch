# Auto-Bench Workflow Specification

## 1. Input Boundary

Accepted fields are `case_id`, `introduction`, `method`, and optional operational
constraints. Inputs containing a catalog benchmark alias or a configured paper
identity marker stop at the leakage gate. Experiment, Results, Appendix, title,
author, venue, citation metadata, and benchmark labels stay outside the matching
process.

## 2. Agent Contracts

### A1 — Capability Profile

Extract task families, uncovered task families, modalities, interactions,
outputs, environments, method capabilities, and candidate metric types. Every
extracted label carries visible text evidence. Explicit tasks remain in the
profile even when no catalog record covers them; otherwise a mixed-domain
method could incorrectly appear complete. The deterministic fallback preserves
an explicit new-domain task phrase and emits modality-specific output and metric
candidates for later human construct definition.

### A2 — Query Planning

Generate task-led search queries. A query describes the evaluation need and
does not contain paper identity. Domain aliases are expanded when benchmark
papers use different terminology, and every alias maps back to its originating
profile task.

### A3 — Literature Retrieval

Search the curated catalog and optionally the official arXiv API. Candidate
records require a primary paper URL and explicit access/license notes. A live
hit that names a catalog benchmark receives full literature corroboration; a
hit sharing a multi-token task phrase receives partial corroboration. Broad
hits are retained as literature leads, but incomplete hits do not silently
become selectable benchmark records. If a hit explicitly presents a benchmark,
dataset, evaluation suite, or evaluation framework, A3 emits a structured
`CATALOG_ADMISSION_REVIEW_REQUIRED` proposal. It lists the method-derived task
match and the fields still requiring primary-source verification: benchmark ID,
official metrics, dataset or harness URL, split definition, access, and license.
Its `selection_eligible` field remains false until a separate catalog review.

### A4 — Compatibility Judgement

Score task, modality, interaction, output, environment, capability, metric, and
retrieval evidence separately. Hard modality/domain contradictions sharply
reduce the score.

### A5 — Portfolio Selection

Use coverage-first ranking to prevent one benchmark family from occupying every
top position. First cover all inferred task families, then reserve a slot for
explicit specialized capabilities such as multilingual code generation, and
run two environment-compatible triangulation rounds. Incomplete-coverage plans
retain a minimal base portfolio so redundant candidates do not hide the missing
construct. Selected items are labeled `core_task_coverage`,
`specialized_capability:<capability>`, or `supplementary_triangulation:<task>`.

### A6 — Adaptation/Synthesis

Use three routes:

| Route | Trigger | Output |
|---|---|---|
| Direct portfolio | Coverage = 100% and every selected task-normalized score ≥ 0.44 | Existing benchmarks + official metrics |
| Base adaptation | Best score ≥ 0.30 but direct gate misses | Retained primitives + new wrapper/data plan |
| New synthesis | No candidate reaches 0.30 | New construct/data/metric proposal |

All synthesized examples retain source IDs, source split, transformation,
expected output, deterministic checks, and human-review status. Test, hidden,
and holdout examples never seed generation. `verify_synthetic_records` resolves
every source ID and checks transform-specific input and expected-output
preservation before a draft is marked ready for review.

`python3 -m autobench run` connects A1–A7 in one command. It writes the plan,
executes requested synthesis modules when named train/development records are
available, writes one verification sidecar per module, freezes two independent
reviewer pages, and records all paths in `workflow_manifest.json`. If synthesis
is required without base records, it emits an explicit schema-bearing request
instead of pretending that data were generated.

### A7 — Source-Revealed Literature Audit

After every blind worker exits, `step3_evaluate_blind_results.py` opens the
separate gold files and joins each anonymous case with its source paper title,
official arXiv link, actual benchmarks, and evidence sections. It computes
Selected and Top-6 matches, misses, and extra recommendations.

`step5_prepare_human_review.py` creates one interactive report for the
researcher. The researcher opens each paper, verifies the experiment-derived
benchmark list, compares it with Auto-Bench output, and records `MATCH`,
`PARTIAL`, or `MISMATCH`. `step6_finalize_literature_audit.py` validates that all
source and comparison checks were completed.

After a completed audit drives matcher changes,
`step7_compare_literature_audit_rounds.py` records the exact human note,
before/after portfolios, ranks, modeled misses, precision, recall, and aggregate
deltas. Same-paper feedback regressions are labeled separately from untouched
holdout evidence.

For a new method with no literature gold, the two-person construct-fit gate is
required before research use and is prepared separately through
`scripts/prepare_new_method_suitability_review.py`.

### A8 — Untouched Holdout

`step8_build_untouched_holdout.py` freezes a newly selected paper before its
first match. Paper identity and experiment-derived gold remain in a separate
directory. `step9_run_untouched_holdout.py` first executes the gold-free worker,
then evaluates after worker exit, and preserves the original result under
`first_run_evaluation.*`; a weak evaluation exit status is still a valid first
result and is not discarded. `step10_prepare_holdout_review.py` builds a human
audit isolated from the feedback-tuned three-paper regression.

The first frozen holdout currently reports `NEEDS_ITERATION`: Recall@5 `0.25`,
Recall@6 `0.50`, selected modeled recall `0.75`, and selected precision `0.60`.
This result is evidence about generalization, not a trigger for silent tuning.
Any later matcher iteration must retain this first-run artifact and be evaluated
again on a different untouched paper.

### A9 — Staged Feedback and Second Holdout

The first LATS holdout exposed a generic hyphen-normalization miss for
`question-answering`. Before modifying the matcher, the CRITIC Introduction and
Method were frozen as `holdout_002`, with paper identity and experiment-derived
gold isolated. Only then was the generic normalization revision applied.

The frozen holdout-002 first run recovered both modeled paper benchmarks with
Recall@5/6 and selected modeled recall equal to `1.0`, but incorrectly chose the
direct route because toxicity reduction was absent from the profile. That
result remains immutable. The feedback regression adds the explicit uncovered
task, tightens direct reuse to full task-family coverage, routes to base
adaptation, and requires synthesis for toxicity reduction. A live alias query
for toxic degeneration retrieves RealToxicityPrompts as a review-only catalog
admission proposal. Neither the live lead nor hidden gold enters ranking.

`step11_build_second_untouched_holdout.py` reproduces the frozen fixture;
`step12_run_second_untouched_holdout.py` preserves or replays the result;
`step13_prepare_second_holdout_review.py` renders the immutable first-run audit;
and `step14_prepare_current_holdout_review.py` renders the current-plan audit.

### A10 — Round 3 catalog recovery and scope-bound revalidation

The completed Round 2 audit returned `MATCH / PARTIAL / MATCH`. Its Reflexion
note identified two paper choices outside the catalog and one unrelated leading
candidate. Round 3 adds primary-source catalog records for LeetcodeHardGym and
MultiPL-E, infers multilingual code generation from the visible method text,
and applies coverage-first balanced ranking. The Reflexion portfolio now selects
all six paper benchmarks and excludes ScienceWorld.

The three-paper regression reports Recall@5 `0.9167`, Recall@6 `1.0000`, MRR
`0.8333`, selected modeled recall `1.0000`, selected actual precision `0.7222`,
and route accuracy `1.0000`; hidden-label loading remains false. Holdout 001
records Recall@6 and selected modeled recall `0.7500`, while current holdout 002
remains `PASS` with both modeled benchmarks selected and correct base-adaptation
routing. `step15_audit_completion.py` joins these machine checks with the three
real human gates and keeps the project state at
`MACHINE_WORKFLOW_READY_HUMAN_GATES_PENDING` until their submissions arrive.

## 3. Metric Discipline

- Official benchmark metrics retain their published names and denominators.
- Adapted metrics use separate names and reports.
- Target method, answer extractor, judge, deterministic verifier, and human
  reviewers are distinct roles in provenance.
- Empty or failed method outputs remain failed outputs; later modules do not
  manufacture answers for them.
- One rollout is reported as `pass@1`/accuracy, not as a multi-rollout metric.

## 4. Decision State

`HUMAN_REVIEW_REQUIRED` is the initial proposal state. Literature validation
then uses `HUMAN_LITERATURE_AUDIT_REQUIRED`,
`LITERATURE_AUDIT_CONFIRMED`, `LITERATURE_AUDIT_PARTIAL`, or
`LITERATURE_AUDIT_MISMATCH`. Automated retrieval metrics never substitute for
the researcher's source-paper check.
