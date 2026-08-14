---
name: autodesign-executor
description: "Execute, monitor, collect, or resume an AutoDesign generated project locally or on a configured SSH GPU server. Use for preflight, sync, bootstrap, smoke, experiment, aggregate, result collection, exact command logging, GPU isolation, timeout handling, and continuation from the first failed or unfinished stage."
---

# AutoDesign Executor

Execute the accepted project and record facts. Do not change the scientific method to make execution pass.

## Inputs

Read `implementation_notes.md`, `evidence_plan.md`, `AUTODESIGN_STATE.md`, the generated environment and commands, and `references/execution-contract.md`.

## Resume decision

1. Read the current `execution_record.json` if it exists.
2. Compare recorded commands directly with current commands.
3. Keep only the successful ordered prefix whose inputs are unchanged.
4. Resume from the first missing, failed, or stale stage.
5. A failed retry replaces that stage record and invalidates later stage records.
6. Keep all successful commands within a multi-command stage in plan order. A later command in the same stage appends evidence; it does not replace the earlier command.
7. Reject an out-of-order stage without rewriting `execution_record.json`, so the first failed command remains available for diagnosis.

## Execute

Use this fixed scientific sequence:

```text
preflight → smoke → experiment → aggregate → collect
```

For generic local commands, use `scripts/run_stage.py` to record command, literal stdout, literal stderr, exit status, and timestamps. `command_plan.json` and the selected working directory must exist before invocation; missing inputs return a JSON `FAIL` without writing an execution record. When a stage has multiple commands, invoke the script once per command in the exact plan order; the runner keeps the complete same-stage prefix. For this repository's remote controller, use the existing `python3 -m autodesign remote-*` commands only after validation confirms the generated project, five-stage command plan, experiment schedule, and result contract.

For a provenance replay, execute all five stages locally, record `execution_mode: provenance_replay`, and keep source execution evidence separate from replay execution evidence. A successful replay proves the migrated project can validate, reproduce, aggregate, and collect the frozen observations; it does not prove a new model run occurred.

On GPU servers:

- preserve existing GPU processes;
- use Linux Bash;
- honor configured GPU IDs and concurrency cap;
- materialize the generated project and its environment before sync;
- stop at the first failed stage;
- preserve logs and checkpoints;
- preserve a failed stage in `execution_record.json` even if a later stage is invoked manually;
- collect the authoritative primary result and every additional configured result path.

Do not infer success from file presence alone. Preflight, smoke, experiment, aggregate, and collect must all exit zero under the current commands.

## Output

Write or update `execution_record.json`, logs, collected results, and `AUTODESIGN_STATE.md`. Use `EXECUTION_IN_PROGRESS` until the complete sequence passes; then use `EXECUTION_COMPLETE` and set the next Skill to `autodesign-result-scientist`.
