# AutoDesign Flow Contract

## Two phases

```text
DESIGN                                   RUN
autodesign-experiment-design      →      autodesign-experiment-run
  input_brief.md                           generated_project/
  experiment_design.md                     command_plan.json
  expected_effects.json                    experiment_schedule.json
  r0_plan.md (conditional)                 result_contract.json
                                           execution_record.json
                                           result_summary.json
                                           effect_comparison.md
                                                        ↓
                                    autodesign-result-scientist
                                    autodesign-integrity-auditor
```

Files are the handoff boundary between Skills. Research reasoning stays readable in Markdown; machine facts stay in compact JSON.

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
- `IMPLEMENTATION_READY`
- `EXECUTION_IN_PROGRESS`
- `EXECUTION_COMPLETE`
- `RESULT_DIAGNOSIS_READY`
- `INTEGRITY_AUDIT_PASS`
- `COMPLETE`

A failed or rejected candidate does not erase the last accepted state. Use `skill-advance` for transitions and `skill-repair-state` to canonicalize repairable Markdown table whitespace. History cell values escape Markdown delimiters before writing. `Last completed stage` names a completed milestone, never `EXECUTION_IN_PROGRESS`. `RESULT_DIAGNOSIS_READY` requires `result_summary.json.status: READY_FOR_GPT_DIAGNOSIS`. `INTEGRITY_AUDIT_PASS` requires an observed `Verdict: PASS`, and `COMPLETE` requires the current state already be `INTEGRITY_AUDIT_PASS`.

## Authoritative artifacts

`input_brief.md` is the authoritative scientific-intent artifact. It preserves the literal Motivation, Contribution, and Benchmark from the AutoSearch handoff, every additional item the user supplied, then records scientific locks, autonomous design choices with outcome-impact classifications, resource constraints, operational definitions, and blockers. Later Skills may resolve an autonomous choice but may never rewrite a scientific lock.

`experiment_design.md` is the authoritative design artifact: claim ledger, Idea semantics, locks, autonomous-choice impact table, route selection, baseline decision, R0 gate, experiment cards for all four families, expected cells, preflight requirements, reporting plan, and a coverage audit ending in a literal `PASS` or a blocker list.

`expected_effects.json` holds the design-time simulated targets. Every value carries `value_status: SIMULATED_TARGET` with a literal `decision_threshold`, a `target_basis` of `handoff_reported` / `published_baseline` / `design_estimate`, and an `on_miss` route. `observed_value` and `observed_status` are filled only by the run phase from real aggregates. A simulated target is never evidence and never enters `reports/`. Editing a target after seeing results is an integrity failure.

`r0_record.json` records the observed resolution of each required R0: covered uncertainty or high-impact choice IDs, candidate instantiation IDs, fixed controls, commands, metrics, raw observations, the literal selection or kill rule, the selected outcome, and exit status. Every unresolved high-impact choice needs results from at least two candidate instantiations; prose acceptance or a one-candidate record cannot set `R0_PASSED`.

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

`result_route.md` contains the route decision, owner Skill, required action, execution requirement, invalidation scope, thresholds, and closure condition. At `RESULT_DIAGNOSIS_READY` the next Skill is `run-autodesign`, which dispatches that route rather than sending every diagnosis directly to audit.

Unexpected cells stay explicit and make the current result summary ineligible for diagnosis until the design and schedule are deliberately revised and downstream artifacts invalidated. A later round never extends an accepted schedule silently.

## Invalidation

Invalidate downstream artifacts when their accepted input changes:

- `input_brief.md` change invalidates every later stage;
- `experiment_design.md` or `expected_effects.json` change invalidates R0, implementation, execution, comparison, diagnosis, and audit;
- generated code, environment, command, or result-contract change invalidates execution and later stages;
- a result change invalidates comparison, diagnosis, and audit;
- an experimental tuning or iteration change invalidates the affected design or implementation plus execution, result summary, comparison, diagnosis, route, and audit;
- reporting-only tuning invalidates reports and audit but not raw execution evidence.

Directly compare the relevant artifact contents. Do not create checksum ledgers.
