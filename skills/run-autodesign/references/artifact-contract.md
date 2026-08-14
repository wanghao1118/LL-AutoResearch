# AutoDesign Artifact Contract

## Purpose

Use files as the handoff boundary between Skills. Research reasoning stays readable in Markdown. Machine facts stay in compact JSON.

## Canonical run layout

```text
assets/output/<run>/
├── AUTODESIGN_STATE.md
├── input_brief.md
├── method_route.md
├── r0_plan.md
├── r0_record.json
├── evidence_plan.md
├── implementation_notes.md
├── generated_project/
├── command_plan.json
├── experiment_schedule.json
├── execution_record.json
├── result_summary.json
├── result_diagnosis.md
├── result_route.md
├── result_tuning.json
├── next_round.md
├── integrity_audit.md
└── reports/
    ├── tables/
    └── charts/
```

R0 files are required only when `method_route.md` marks R0 required. `result_tuning.json` exists only for a tuning route, and `next_round.md` exists only while another action or run is required.

## State vocabulary

Use one of:

- `INPUT_READY`
- `METHOD_ROUTE_READY`
- `WAITING_FOR_R0_IMPLEMENTATION`
- `R0_PASSED`
- `R0_FAILED_RETURN_TO_METHOD_ROUTE`
- `EVIDENCE_PLAN_READY`
- `IMPLEMENTATION_READY`
- `EXECUTION_IN_PROGRESS`
- `EXECUTION_COMPLETE`
- `RESULT_DIAGNOSIS_READY`
- `INTEGRITY_AUDIT_PASS`
- `COMPLETE`

A failed or rejected candidate does not erase the last accepted state.

Use `skill-advance` for state transitions and `skill-repair-state` to canonicalize repairable Markdown table whitespace. History cell values escape Markdown delimiters before writing. `Last completed stage` names a completed milestone, never `EXECUTION_IN_PROGRESS`. `RESULT_DIAGNOSIS_READY` requires `result_summary.json.status: READY_FOR_GPT_DIAGNOSIS`; `INTEGRITY_AUDIT_PASS` requires an observed `Verdict: PASS`, and `COMPLETE` requires the current state already be `INTEGRITY_AUDIT_PASS`.

## Machine records

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

`result_summary.json` contains scheduled and observed cell counts, missing and unexpected cells, aggregates, errors, and no automatic scientific claim verdict.

`result_route.md` contains the scientific route decision, owner Skill, required action, execution requirement, invalidation scope, thresholds, and closure condition. At `RESULT_DIAGNOSIS_READY`, the next Skill is `run-autodesign`, which dispatches that route rather than sending every diagnosis directly to audit.

`result_tuning.json` follows the bundled result-tuning Prompt schema. It is a proposed or completed action record, not observed evidence by itself. `next_round.md` records every action that still requires implementation, execution, or confirmation.

`experiment_schedule.json` lists explicit cells with experiment ID, variant ID, benchmark task ID, integer seed, and planned metric names. It exists only to test result completeness; it does not decide which experiments are scientifically appropriate.

## Invalidation

Invalidate downstream artifacts when their accepted input changes:

- `input_brief.md` change invalidates every later stage;
- `method_route.md` change invalidates R0, evidence plan, implementation, execution, and diagnosis;
- `evidence_plan.md` change invalidates implementation and later stages;
- generated code, environment, command, or result-contract change invalidates execution and later stages;
- result change invalidates diagnosis and audit.
- an experimental tuning or iteration change invalidates the affected evidence plan or implementation plus execution, result summary, diagnosis, route, and audit;
- reporting-only tuning invalidates reports and audit but not raw execution evidence.

Directly compare the relevant artifact contents. Do not create checksum ledgers.
