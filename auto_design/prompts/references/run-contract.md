# Experiment Run Contract

## Required project surfaces

- environment definition;
- preflight implementation covering all four categories;
- smoke entrypoint;
- experiment entrypoint or launcher;
- aggregate entrypoint;
- collect step producing the declared result paths;
- one entrypoint mapping per experiment ID across all four families;
- case-study selection implemented from the design's literal pre-result rule;
- chart and table generators reading observed results only;
- a materialized identity record for every variant and benchmark;
- `command_plan.json`, `experiment_schedule.json`, `result_contract.json`.

These surfaces apply to full implementation after a scientific design `PASS`. A run in `WAITING_FOR_R0` materializes only what its registered probes require and does not create a full experiment schedule.

## R0-only execution

R0-only mode requires `Verdict: PROVISIONAL_WAITING_FOR_R0`, state `WAITING_FOR_R0`, and `r0_plan.md`. Execute only the named candidate comparisons. `r0_record.json` records the covered high-impact choice ID, the direct candidate instantiation IDs for that choice, fixed controls, fit/materialization IDs and candidate-selection IDs when adaptation or data construction occurs, commands, metrics, raw observations, literal selection and kill rules, selected outcome, and exit status. Fit/materialization IDs and candidate-selection IDs are disjoint, and neither pool is later claim-bearing evaluation. A proxy comparison cannot resolve the registered choice.

## `implementation_notes.md`

Record: selected route and full configuration; scientific locks and autonomous choices; selected components and source revisions; baseline configurations; family and evidence class per experiment; training or inference state; experiment-to-entrypoint map; environment file; exact five-stage commands; primary result path; schedule path; table and chart paths; resource estimate; resource adaptations, non-claim-bearing pilots, and blockers; machine-context source file when remote; execution mode `fresh_experiment`.

## Decision-relevant preflight

Each check records the accepted value, the materialized value, a literal failure condition, and the next action. Include when applicable: variant and model revision; data manifest, training input path, sample count, sampling policy, planned-versus-observed group distributions; source, teacher, scaffold, turn, token, label, difficulty, or quality distributions the design requires; benchmark identity, provenance, revision, split, scaffold, timeout, metric definition; maximum length, epochs, learning rate, objective, trainable parameter ratio; prompt, tool, retriever, decoding, state, and inference-budget identity for train-free routes; the production dataflow from required transformation to the exact consumed artifact.

Do not add a check without a concrete failure and a changed next action. A failed scientific-lock or planned-composition check blocks expensive execution.

## `command_plan.json`

An object keyed by stage, each value a non-empty list of literal Bash commands run from `generated_project/`:

```json
{
  "preflight": ["python3 preflight.py --report reports/preflight.json"],
  "smoke": ["bash run_smoke.sh"],
  "experiment": ["bash run_experiments.sh"],
  "aggregate": ["python3 aggregate.py"],
  "collect": ["python3 collect.py --out ../collected_results.json"]
}
```

## `experiment_schedule.json`

Explicit execution cells with experiment ID, variant ID, benchmark task ID, benchmark provenance, family, evidence class, integer seed, and planned metric names. Family is exactly `main`, `ablation`, `case_study`, or `analysis`. Evidence class is exactly `CLAIM_BEARING`, `MECHANISM_PILOT`, or `ENGINEERING_SMOKE`. Seeds are execution identity; all scheduled metrics are aggregated into absolute experiment × variant × task × metric results. `expected_effects.json` is a smaller inventory of claim-relevant decision effects anchored to those aggregates; reference-only and presentation-only aggregates need no target entry. The schedule exists to test result completeness and preserve the accepted design identity; scientific appropriateness and table structure come from `experiment_design.md`.

The accepted schedule is immutable during an execution round. Missing cells, unexpected cells, changed evidence classes, or changed benchmark provenance prevent the run from qualifying for diagnosis. A deliberate new round first revises the design and invalidates downstream records.

## `result_contract.json`

Schema version `1.0`, the generated-project-relative primary result path, and format `autodesign-results-v1`. Result records contain experiment ID, family, evidence class, variant ID, benchmark identity and provenance, benchmark task ID, seed, planned metrics, and completion status. Failed runs stay explicit records or execution failures; they are never converted to successful zeros.

## Stage record

Each stage records stage name; exact command and working directory; exact input artifact paths; start and finish timestamps; stdout and stderr; exit status; executor and GPU IDs when applicable; machine-context source file when applicable; produced paths; next action on failure.

The preflight stage also records accepted versus observed scientific locks, variant identities, data composition, benchmark provenance, protocol values, and production input paths. A mismatch is an execution blocker even when a lower-level command can run.

## Ordered completion

Diagnosis requires successful current records for `preflight`, `smoke`, `experiment`, `aggregate`, `collect` in that order. Multiple commands within a stage stay contiguous. A later success does not erase an earlier failure unless that stage is explicitly retried and replaced. An out-of-order or stale-stage request returns a rejected-attempt result without rewriting the authoritative record. `run-local --stage all` reuses the unchanged successful prefix and starts at the first missing, failed, or stale stage.

The portable stage runner requires a readable `command_plan.json` and an existing working directory, and returns a structured JSON `FAIL` for either missing input.

## Remote sequence

Read instruction context → validate → preflight → sync → bootstrap → smoke → experiment → aggregate → collect. The effective `AGENTS.md` or `CLAUDE.md` supplies SSH, allowed directories, GPU IDs, concurrency, environment location, timeouts, and process-preservation rules. Deployment still requires a materialized `generated_project/`, a complete five-stage `command_plan.json`, a non-empty `experiment_schedule.json`, and a valid `result_contract.json`. The command plan and result contract — not the machine-context file — define commands and result paths. This worker does not create or read a Python/JSON GPU configuration.

## Resource failures

Preserve exact resource errors and the first failed stage. Never turn a resource block into a scientific method verdict.

## Breakpoint recovery

`breakpoint_recovery.md` uses one stable record per executed repair and keeps these fields readable: current accepted method-revision ID; approved method-revision count and limit for the Idea; breakpoint ID and failed stage; literal evidence; diagnosis; repair class `boundary_only`; exact changed setting or implementation; accepted and materialized scientific identities; identity-preservation rationale; command; result; progress evidence; and next action. Boundary repair has no fixed numeric cap. A new approved method revision starts a new recovery sequence without deleting prior history or resetting the Idea-level method-revision count.

A boundary-only repair may alter execution equivalence or literal implementation defects, but it does not alter the intervention, outcome-impacting component identities, data eligibility/composition, benchmark protocol, metric, seed plan, evidence class, comparison budget, or claim interpretation. If preserving those invariants cannot address the failure, stop without spending the remaining retry allowance.

After a `no_admissible_boundary_repair` or `no_new_progress` decision, write `method_revision_request.md` with: request ID; breakpoint ID; accepted method-revision ID; failed stage and evidence paths; attempted repairs and outcomes; preserved Motivation/Contribution/Benchmark locks; accepted method identity; unresolved capability gap; and affected execution artifacts. This request contains no proposed method change and grants no permission to edit the design.

## `effect_comparison.md`

Written after ingestion, from the read-only `expected_effects.json` plus observed aggregates. One row per design entry; do not modify the target file:

| Entry ID | Experiment | Family | Variant | Task | Metric | Simulated target | Decision threshold | Observed | Threshold outcome | On miss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Rules:

- Threshold outcome is exactly `MET`, `MISSED`, or `NOT_EVALUABLE`. Use `NOT_EVALUABLE` when the reference variant or a required cell is absent, and name what is missing.
- Every design entry appears, including missed and not-evaluable ones. Dropping a missed row is an integrity failure.
- Observed values come only from `result_summary.json` aggregates.
- `simulated_target` values are never edited after execution. A miscalibrated target is reported as a design finding under a `## Target calibration findings` section.
- Follow the table with `## Routing` listing every `MISSED` entry, its `on_miss` route, and the affected claim IDs, for `diagnosis` to act on.
- A `MET` outcome is a threshold fact, not a contribution verdict. Contribution verdicts belong to the result scientist.
