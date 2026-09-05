# AutoDesign Flow Contract

## Two phases

```text
DESIGN                                   RUN
autodesign-experiment-design      →      autodesign-experiment-run
  input_brief.md                           generated_project/
  experiment_design.md ──→ AutoWriting     command_plan.json
  expected_effects.json   (non-blocking)   experiment_schedule.json
  r0_plan.md (conditional)                 result_contract.json
                                           execution_record.json
                                           result_summary.json
                                           effect_comparison.md
                                                        ↓
                                    autodesign-result-scientist
                                    autodesign-integrity-auditor
```

Files are the handoff boundary between Skills. Research reasoning stays readable in Markdown; machine facts stay in compact JSON.

AutoWriting is a downstream consumer, not an AutoDesign state. After Design publishes the `## AutoWriting handoff` section, writing may proceed independently while Run continues. AutoWriting never owns or mutates AutoDesign's accepted scientific artifacts.

## Canonical run layout

```text
assets/output/<run>/
├── AUTODESIGN_STATE.md
├── input_brief.md
├── experiment_design.md
├── expected_effects.json
├── r0_plan.md
├── r0_record.json
├── implementation_notes.md
├── generated_project/
├── command_plan.json
├── experiment_schedule.json
├── result_contract.json
├── execution_record.json
├── breakpoint_recovery.md
├── method_revision_request.md
├── method_revision_proposal.md
├── method_revision_decision.md
├── idea_abandonment.md
├── raw_results.json
├── result_summary.json
├── effect_comparison.md
├── result_diagnosis.md
├── result_route.md
├── result_tuning.json
├── next_round.md
├── integrity_audit.md
└── reports/
    ├── tables/
    └── charts/
```

R0 files exist only when `experiment_design.md` marks R0 required. `result_tuning.json` exists only for a tuning route. `next_round.md` exists only while another action or run is required.

## State vocabulary

- `INPUT_READY`
- `EXPERIMENT_DESIGN_READY`
- `WAITING_FOR_R0`
- `R0_PASSED`
- `R0_FAILED_RETURN_TO_DESIGN`
- `WAITING_FOR_METHOD_REVISION_APPROVAL`
- `IMPLEMENTATION_READY`
- `EXECUTION_IN_PROGRESS`
- `EXECUTION_COMPLETE`
- `RESULT_DIAGNOSIS_READY`
- `INTEGRITY_AUDIT_PASS`
- `COMPLETE`
- `IDEA_ABANDONED`

A failed or rejected candidate does not erase the last accepted state. Use `skill-advance` for transitions and `skill-repair-state` to canonicalize repairable Markdown table whitespace. History cell values escape Markdown delimiters before writing. `Last completed stage` names an accepted milestone, never `EXECUTION_IN_PROGRESS`; while the design is `WAITING_FOR_R0`, that milestone remains `INPUT_READY`. `RESULT_DIAGNOSIS_READY` requires `result_summary.json.status: READY_FOR_GPT_DIAGNOSIS`. `INTEGRITY_AUDIT_PASS` requires an observed `Verdict: PASS`, and `COMPLETE` requires the current state already be `INTEGRITY_AUDIT_PASS`.

## Authoritative artifacts

`input_brief.md` is the authoritative scientific-intent artifact. It preserves the literal Motivation and Contribution from the AutoSearch handoff, any optional Benchmark and every additional item the user supplied, then records scientific locks, autonomous design choices with outcome-impact classifications, resource constraints, operational definitions, and blockers. When Benchmark is absent, `experiment_design.md` owns its contribution-driven selection or design. Later Skills may resolve an autonomous choice but may never rewrite a scientific lock.

`experiment_design.md` is the authoritative design artifact: claim ledger, Idea semantics, locks, autonomous-choice impact table with role closure, contribution-to-benchmark requirements, benchmark candidate and reuse/adapt/new decision, route selection, baseline decision, R0 gate, experiment cards with estimands for all four families, planned execution cells, absolute aggregate results, paper table plan, decision effects, preflight requirements, reporting plan, AutoWriting handoff, and a coverage audit declaring `PASS`, `PROVISIONAL_WAITING_FOR_R0`, or `FAIL`. A provisional declaration is structurally usable for R0 but is not an accepted scientific design.

`expected_effects.json` holds read-only design-time simulated targets, one per claim-relevant decision effect. A numeric entry anchors to the target variant's absolute experiment × variant × task × metric aggregate and names a reference variant when the threshold is relative. Baseline and presentation-only aggregate rows stay out of this file. Every value carries `value_status: SIMULATED_TARGET` with a literal `decision_threshold`, a `target_basis` of `handoff_reported` / `published_baseline` / `design_estimate`, and an `on_miss` route. Observed values and threshold outcomes live in `result_summary.json` and `effect_comparison.md`, never in this file. A simulated target is never evidence. It may appear only in an explicitly marked AutoWriting draft and never in `reports/` or submission-ready results. Editing a target after seeing results is an integrity failure.

`r0_record.json` records the observed resolution of each required R0: covered uncertainty or high-impact choice IDs, candidate instantiation IDs, fixed controls, disjoint fit/materialization and candidate-selection IDs when adaptation occurs, commands, metrics, raw observations, the literal selection or kill rule, the selected outcome, and exit status. Every unresolved high-impact choice needs results from at least two direct candidate instantiations of that choice; prose acceptance, a proxy comparison, or a one-candidate record cannot set `R0_PASSED`.

`breakpoint_recovery.md` is the readable execution-recovery ledger. It declares `method_revision_limit`, counts approved method revisions for the current Idea, and records every breakpoint, attempted boundary-only change, identity-preservation argument, result, and escalation reason. Boundary repair has no fixed numeric cap: continue while a materially different admissible repair, new evidence, or measurable progress exists, and escalate only when none remains. The default method-revision limit is two approved revisions per Idea unless the user sets a different value before recovery begins.

`method_revision_request.md` contains the unresolved breakpoint evidence after boundary recovery stops. `method_revision_proposal.md` contains one smallest revision with a stable `Revision ID`; `method_revision_decision.md` records the same ID and the user's literal `APPROVE_MINIMAL_METHOD_REVISION`, `APPROVE_EXCEPTION_METHOD_REVISION`, `REJECT_METHOD_REVISION`, or `ABANDON_IDEA` decision. Old decisions do not authorize a new proposal ID. `idea_abandonment.md` closes the Idea without deleting failed attempts or reusable artifacts.

`WAITING_FOR_METHOD_REVISION_APPROVAL` preserves the last accepted design while prohibiting implementation of the proposal. `IDEA_ABANDONED` is terminal and means the user chose to stop this Idea; it does not convert an implementation/resource breakpoint into scientific evidence against the method.

`experiment_schedule.json` lists explicit cells with experiment ID, variant ID, benchmark task ID, benchmark provenance, family, evidence class, integer seed, and planned metric names. Family is exactly `main`, `ablation`, `case_study`, or `analysis`. Evidence class is exactly `CLAIM_BEARING`, `MECHANISM_PILOT`, or `ENGINEERING_SMOKE`.

`execution_record.json` records only observed facts:

```json
{
  "schema_version": "1.0",
  "executor": "local_or_remote",
  "status": "PASS_OR_FAIL",
  "commands": [
    {
      "stage": "smoke",
      "command": "literal command",
      "stdout": "literal stdout",
      "stderr": "literal stderr",
      "exit_status": 0
    }
  ]
}
```

`result_summary.json` contains scheduled and observed cell counts, missing and unexpected cells, aggregates, and errors, with `automatic_claim_verdict` fixed at `NOT_ASSIGNED`.

`effect_comparison.md` pairs every design entry with its observation and a threshold outcome of `MET`, `MISSED`, or `NOT_EVALUABLE`, and routes every miss by its `on_miss` value. A `MET` outcome is a threshold fact, not a contribution verdict.

The AutoWriting handoff has no separate state transition. `ACCEPTED` permits drafting every designed section with placeholders. `PROVISIONAL_WAITING_FOR_R0` permits only stable sections and keeps route-dependent text conditional. An R0 or design revision republishes the section and names affected entry IDs; writing progress never blocks experiment execution.

`result_route.md` contains the route decision, owner Skill, required action, execution requirement, invalidation scope, thresholds, and closure condition. At `RESULT_DIAGNOSIS_READY` the next Skill is `run-autodesign`, which dispatches that route rather than sending every diagnosis directly to audit.

`reports/report_manifest.json` closes the accepted reporting plan. It lists every named table, figure, case-study panel, and analysis artifact with its path, source IDs, and `READY`, `INCOMPLETE`, or `N/A` evidence status. `reports/index.html` is the human-readable entry point. Terminal, conservative, mixed, and negative routes still materialize the full plan: unavailable evidence is shown at the planned output path with its exact reason and is never silently omitted or replaced by zero or a simulated target.

Unexpected cells stay explicit and make the current result summary ineligible for diagnosis until the design and schedule are deliberately revised and downstream artifacts invalidated. A later round never extends an accepted schedule silently.

## Invalidation

Invalidate downstream artifacts when their accepted input changes:

- `input_brief.md` change invalidates every later stage;
- `experiment_design.md` or `expected_effects.json` change invalidates R0, implementation, execution, comparison, diagnosis, and audit;
- generated code, environment, command, or result-contract change invalidates execution and later stages;
- a result change invalidates comparison, diagnosis, and audit;
- an experimental tuning or iteration change invalidates the affected design or implementation plus execution, result summary, comparison, diagnosis, route, and audit;
- an approved method revision invalidates the affected design entries, implementation, execution, comparison, diagnosis, and audit; its approval applies only to the matching revision ID;
- reporting-only tuning invalidates reports and audit but not raw execution evidence.

Directly compare the relevant artifact contents. Do not create checksum ledgers.
