---
name: autodesign-executor
description: "Execute, monitor, collect, or resume an AutoDesign generated project locally or on a configured SSH GPU server. Use for preflight, sync, bootstrap, smoke, experiment, aggregate, result collection, exact command logging, GPU isolation, timeout handling, and continuation from the first failed or unfinished stage."
---

# AutoDesign Executor

Execute the accepted project and record facts. Do not change the scientific method to make execution pass.

## Inputs

Read `implementation_notes.md`, `evidence_plan.md`, `AUTODESIGN_STATE.md`, the generated environment and commands, `references/execution-contract.md`, and the effective `AGENTS.md` or `CLAUDE.md` instructions for the current workspace. For GPU work, resolve the `AutoDesign GPU 执行上下文` section before issuing any remote or accelerator command.

## Resume decision

1. Read the current `execution_record.json` if it exists.
2. Compare recorded commands directly with current commands.
3. Keep only the successful ordered prefix whose inputs are unchanged.
4. Resume from the first missing, failed, or stale stage.
5. A failed retry replaces that stage record and invalidates later stage records.
6. Keep all successful commands within a multi-command stage in plan order. A later command in the same stage appends evidence; it does not replace the earlier command.
7. Reject an out-of-order stage without rewriting `execution_record.json`, so the first failed command remains available for diagnosis.
8. Treat a revised evidence plan, experiment schedule, scientific identity, benchmark provenance, or materialized data manifest as an input change that invalidates the affected execution prefix.

## Execute

Use this fixed scientific sequence:

```text
preflight → smoke → experiment → aggregate → collect
```

For generic local commands, use `scripts/run_stage.py` to record command, literal stdout, literal stderr, exit status, and timestamps. `command_plan.json` and the selected working directory must exist before invocation; missing inputs return a JSON `FAIL` without writing an execution record. When a stage has multiple commands, invoke the script once per command in the exact plan order; the runner keeps the complete same-stage prefix.

For remote GPU execution, use the SSH, transfer, Conda, GPU, timeout, and directory facts from the effective `AGENTS.md` or `CLAUDE.md`; use `command_plan.json` and `result_contract.json` as the authority for commands and result paths. Run SSH, transfer, environment, and stage commands with the agent's normal tools. 不需要 Python GPU 控制器，也不要创建或读取 Python/JSON GPU 配置。

Before starting smoke or any expensive command, read the preflight report rather than relying only on its exit code. Stop when a scientific lock, evidence class, planned data composition, benchmark provenance, or production dataflow check fails. Do not edit the accepted method, schedule, or preflight threshold inside the executor to make execution pass.

On GPU servers:

- preserve existing GPU processes;
- use Linux Bash;
- honor the instruction-file GPU IDs and concurrency cap;
- materialize the generated project and its environment before sync;
- stop at the first failed stage;
- preserve logs and checkpoints;
- preserve a failed stage in `execution_record.json` even if a later stage is invoked manually;
- collect the authoritative primary result and every additional result path declared by `result_contract.json`.

Do not infer success from file presence alone. Preflight, smoke, experiment, aggregate, and collect must all exit zero under the current commands. Missing or unexpected scheduled cells, changed evidence identities, or results appended outside the accepted schedule keep execution incomplete and require a deliberate plan revision before diagnosis.

## Output

Write or update `execution_record.json`, logs, collected results, and `AUTODESIGN_STATE.md`. Use `EXECUTION_IN_PROGRESS` until the complete sequence passes; then use `EXECUTION_COMPLETE` and set the next Skill to `autodesign-result-scientist`.
