---
name: autodesign-experiment-run
description: "Implement and execute an accepted AutoDesign experiment design as a real runnable project, locally or on a configured SSH GPU server. Covers project materialization, environments, entrypoints, preflight, five-stage execution, result collection, and the observed-versus-simulated-target comparison. Use after $autodesign-experiment-design produces experiment_design.md, or to resume a partially executed run."
---

# AutoDesign Experiment Run

Execute the accepted design and record facts. Do not change the science to make execution pass.

This Skill is the second half of AutoDesign. It never authors experiments: if the right action is to add, remove, or redefine an experiment, stop and return to `$autodesign-experiment-design`.

## Entry gate

Read `input_brief.md`, `experiment_design.md`, `expected_effects.json`, `AUTODESIGN_STATE.md`, `references/run-contract.md`, and the effective `AGENTS.md` or `CLAUDE.md` for the current workspace.

Stop before implementation if the design's coverage audit is not `PASS`, if a required R0 has not been executed, or if any high-impact autonomous choice lacks an explicit user decision or an executed two-candidate comparison.

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

Before smoke or any expensive command, read the preflight report rather than trusting its exit code. Stop when a scientific lock, evidence class, planned data composition, benchmark provenance, or production dataflow check fails. Never edit the accepted design, schedule, or a preflight threshold inside this Skill to make execution pass.

On GPU servers: preserve existing processes, use Linux Bash, honor the instruction-file GPU IDs and concurrency cap, materialize the project and environment before sync, stop at the first failed stage, preserve logs and checkpoints and failed stage records, and collect every result path declared by `result_contract.json`.

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

Write `implementation_notes.md`, the project environment, runnable entrypoints, `command_plan.json`, `experiment_schedule.json`, `result_contract.json`, preflight reports, `execution_record.json`, logs, collected results, `result_summary.json`, and `effect_comparison.md`. Keep `expected_effects.json` byte-for-byte unchanged. Record exact deviations as blockers instead of silently simplifying the study.

Update `AUTODESIGN_STATE.md` with `python3 -m autodesign skill-advance`: `IMPLEMENTATION_READY` after materialization, `EXECUTION_IN_PROGRESS` while stages remain, then `EXECUTION_COMPLETE` once all five stages pass and the effect comparison exists. The next Skill is `autodesign-result-scientist`.
