---
name: autodesign-experiment-run
description: "Execute a registered AutoDesign R0 probe or implement and run an accepted experiment design, locally or on a configured SSH GPU server. Covers R0-only resolution, project materialization, environments, entrypoints, preflight, five-stage execution, result collection, and observed-versus-simulated-target comparison. Use after $autodesign-experiment-design produces a provisional R0 plan or an accepted experiment_design.md, or to resume a partially executed run."
---

# AutoDesign Experiment Run

Execute the accepted design and record facts. Do not change the science to make execution pass.

This Skill is the second half of AutoDesign. It never authors experiments: if the right action is to add, remove, or redefine an experiment, stop and return to `$autodesign-experiment-design`.

## Entry gate

Read `input_brief.md`, `experiment_design.md`, `expected_effects.json`, `AUTODESIGN_STATE.md`, `breakpoint_recovery.md` when present, `references/run-contract.md`, and the effective `AGENTS.md` or `CLAUDE.md` for the current workspace.

Choose the permitted mode from the design declaration and state:

- `PASS` plus `EXPERIMENT_DESIGN_READY` permits full implementation only when no required R0 remains and every high-impact choice has an explicit user decision or an executed direct two-candidate comparison.
- `PROVISIONAL_WAITING_FOR_R0` plus `WAITING_FOR_R0` permits only the registered `r0_plan.md`; do not materialize or execute the full experiment portfolio.

Stop on any other declaration/state pairing.

## Read machine context

For GPU or remote work, resolve the `AutoDesign GPU 执行上下文` section in the effective `AGENTS.md` or `CLAUDE.md` before issuing any remote or accelerator command. That section is the only source of SSH, allowed directories, GPU IDs, concurrency, environment location, timeouts, and process-preservation rules. Do not create or read a Python/JSON GPU configuration. With no such section, do not assume a remote host or GPU assignment. Record the instruction file used and the resolved execution facts in `implementation_notes.md` and `execution_record.json`.

## Implement

1. Materialize the project under `generated_project/`.
2. Preserve the accepted intervention, scientific locks, component identities, baseline configurations, experiment families, evidence classes, protocol decisions, variants, tasks, metrics, and seeds. Do not downgrade a blocked `CLAIM_BEARING` experiment to a pilot here — that is a design change.
3. Map every accepted experiment ID to a runnable entrypoint, including every ablation, case study, and analysis experiment. A design entry with no entrypoint is an incomplete implementation, not an optional extra.
4. Include a complete environment definition with every real runtime dependency and compatible version. Do not assume model frameworks or benchmark SDKs are preinstalled.
5. Implement four decision-relevant preflight categories: data contract, benchmark interface and provenance, metric and protocol contract, and method sanity. Every check names the concrete failure it detects and the changed next action.
6. Implement the case-study selection rule as code that consumes the design's literal rule, so selection cannot depend on observed scores.
7. Make smoke run all preflights plus a tiny representative path.
8. Generate non-empty preflight, smoke, experiment, aggregate, and collect commands operating from `generated_project/` under Linux Bash. Write them to `command_plan.json`.
9. Make launchers honor `AUTODESIGN_MAX_PARALLEL_JOBS` and use only `CUDA_VISIBLE_DEVICES`; leave existing GPU processes unchanged.
10. Preserve training objectives, datasets, learning curves, checkpoints, and reload behavior for training routes. Preserve prompts, decoding, tools, retrieval state, and inference budgets for train-free routes.
11. Before expensive execution, materialize and inspect each variant's scientific identity: model revision, data manifest, sample count, sampling policy, planned-versus-observed composition, training input path, maximum length, epochs, learning rate, and trainable parameter ratio where applicable; or the corresponding prompt, tool, retriever, state, decoding, and budget identities for train-free routes.
12. When filtering, decontamination, selection, or transformation is required, materialize the derived artifact and make the launch command consume that exact artifact. A unit test of the transformation does not prove the production path uses it.
13. Write `experiment_schedule.json` with one cell per planned experiment × variant × task × seed execution cell, including its metrics, and `result_contract.json` for result paths. Map those cells to the design's aggregate experiment × variant × task × metric effect rows. Generate tables and figures from observed results only.
14. Run local preflight and smoke when the resource contract permits. Repair literal failures; a scientific-lock or planned-composition mismatch returns to `$autodesign-experiment-design`.

For R0-only mode, implement and run only the registered probes. Preserve the candidate choice, fixed controls, and the disjoint fit/materialization and candidate-selection IDs from `r0_plan.md`; do not replace the registered uncertainty with a proxy comparison. Write those identities and literal observations into `r0_record.json`, then return to `$autodesign-experiment-design` without starting the full portfolio.

## Execute

Use this fixed sequence:

```text
preflight → smoke → experiment → aggregate → collect
```

For generic local commands use `scripts/run_stage.py`, or `python3 -m autodesign run-local <run_dir>`, to record command, literal stdout, literal stderr, exit status, and timestamps. When a stage has multiple commands, invoke once per command in exact plan order. For remote GPU execution, use the machine facts from the instruction file with the agent's own shell, SSH, and transfer tools; `command_plan.json` and `result_contract.json` remain the authority for commands and result paths.

Resume rules:

1. Read the current `execution_record.json` and compare recorded commands directly with current commands.
2. Keep only the successful ordered prefix whose inputs are unchanged; resume from the first missing, failed, or stale stage.
3. A failed retry replaces that stage record and invalidates later records. A later command in the same stage appends evidence rather than replacing an earlier one.
4. Reject an out-of-order stage without rewriting `execution_record.json`, so the first failure stays available for diagnosis.
5. Treat a revised design, schedule, scientific identity, benchmark provenance, or materialized data manifest as an input change that invalidates the affected prefix.

## Recover execution breakpoints

When implementation or a stage blocks, preserve the failed command, stdout/stderr, exit status, checkpoint, produced paths, and the successful ordered prefix. Give the breakpoint a stable ID and append it to `breakpoint_recovery.md`. Boundary repair has no fixed numeric attempt limit. Unless the user set a different value before recovery began, use `method_revision_limit: 2` for the Idea.

First attempt only boundary repairs that leave the accepted scientific identity unchanged. Allowed repairs include device placement, equivalent effective batch via batch size plus gradient accumulation, worker/concurrency count, checkpoint/resume cadence, a non-locked timeout, literal file/path/configuration wiring, transport retry, or a compatible dependency correction. A change to the learning objective, method component, data eligibility/composition, benchmark/split/metric, teacher/judge, prompt/tool policy, decoding or inference budget, seed plan, comparison budget, or another outcome-impacting identity is not a boundary repair and must not be performed here.

For each executed attempt, record: attempt index; breakpoint and failed stage; literal failure; exact change; accepted-versus-materialized scientific identities; why the method, Idea, and claim interpretation are unchanged; affected command; observed result; and next action. Resume from the first affected stage. A retry of an unchanged command against an unchanged failure is not progress; another attempt needs a materially different admissible repair, new evidence, or measurable progress. If the accepted method advances past the breakpoint, keep the ledger and continue execution.

Continue boundary repair for as many materially different admissible attempts as remain useful. Stop only when no boundary-only change can plausibly address the observed failure, or repeated attempts yield the same failure with no new evidence, new action, or measurable progress. Then write `method_revision_request.md` with the breakpoint evidence, repairs tried, preserved locks, current accepted method identity, and the smallest unresolved capability gap. Return to `$autodesign-experiment-design`; do not propose, implement, or test a method change in this Skill.

Never treat R0 as another breakpoint retry. An R0 failure follows the registered R0 return path. If a later approved method revision creates an unresolved high-impact choice, the design Skill decides whether a new R0 is required.

Before smoke or any expensive command, read the preflight report rather than trusting its exit code. When a scientific lock, evidence class, planned data composition, benchmark provenance, or production dataflow check fails, stop advancement to dependent stages and immediately enter the boundary-repair flow above. Continue admissible repairs within the authorized execution scope; if none remains or no new progress is possible, prepare the existing method-revision handoff. Never edit the accepted design, schedule, or a preflight threshold inside this Skill to make execution pass.

On GPU servers: preserve existing processes, use Linux Bash, honor the instruction-file GPU IDs and concurrency cap, and materialize the project and environment before sync. At the first failed stage, halt dependent stages, preserve logs, checkpoints, and failed stage records, and enter boundary repair rather than ending the task. Resume from the first affected stage after repair and collect every result path declared by `result_contract.json`; unavailable paths remain explicit gaps, not successful collection.

Do not infer success from file presence. All five stages must exit zero under the current commands.

## Ingest results and compare against targets

After `collect` succeeds:

```bash
python3 -m autodesign skill-ingest <run_dir> <collected_results.json>
python3 -m autodesign skill-compare-effects <run_dir>
```

`skill-ingest` checks completeness only: observed cells must equal scheduled cells and planned metrics, with no missing or unexpected cell. It assigns no scientific verdict.

`skill-compare-effects` reads the design-time `expected_effects.json` without modifying it and writes `effect_comparison.md`. Record, per entry: family, metric, simulated target, decision threshold, observed value, and threshold outcome `MET`, `MISSED`, or `NOT_EVALUABLE`.

Comparison rules:

- A simulated target is never evidence. A `MET` outcome means the observation cleared its own threshold, not that the target was correct.
- Never overwrite an observed value with a target, and never present a target as a result. Targets stay out of `reports/`; only the explicitly marked downstream AutoWriting draft may carry simulated values.
- A missed threshold routes by the entry's `on_miss` value and stays visible in the comparison table.
- A design-time target that turns out to be badly calibrated is a design finding to report, not a reason to edit the target after seeing results. Editing `simulated_target` post-hoc is a literal integrity failure.
- Case-study entries evaluate required category counts, including failure categories. Analysis entries evaluate the observed shape against `expected_shape`.

## Output

Write `implementation_notes.md`, the project environment, runnable entrypoints, `command_plan.json`, `experiment_schedule.json`, `result_contract.json`, preflight reports, `execution_record.json`, logs, collected results, `result_summary.json`, and `effect_comparison.md`. When a breakpoint occurs, also maintain `breakpoint_recovery.md` and, after boundary recovery ends without resolution, `method_revision_request.md`. Keep `expected_effects.json` byte-for-byte unchanged. Record exact deviations as blockers instead of silently simplifying the study.

In R0-only mode, update `AUTODESIGN_STATE.md` to `R0_PASSED` or `R0_FAILED_RETURN_TO_DESIGN` after writing `r0_record.json`; the next Skill is `autodesign-experiment-design`. In full mode, update to `IMPLEMENTATION_READY` after materialization, `EXECUTION_IN_PROGRESS` while stages remain, then `EXECUTION_COMPLETE` once all five stages pass and the effect comparison exists; the next Skill is `autodesign-result-scientist`.
