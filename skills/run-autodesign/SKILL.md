---
name: run-autodesign
description: "Orchestrate or resume a Skill-first AutoDesign research pipeline from natural-language motivation, contributions, and benchmarks through method routing, R0, evidence design, implementation, local or remote execution, result diagnosis, integrity audit, and paper-ready artifacts. Use for full AutoDesign runs, existing-run continuation, pipeline migration, or end-to-end experiment automation."
---

# Run AutoDesign

Run the research workflow rather than returning only a plan. Keep research decisions in Skills and use code only for command execution, state facts, and deterministic result completeness.

## Locate the run

Use the user's current workspace or an explicitly selected run workspace. The installed Skills and `autodesign` Python package are the runtime dependencies; the AutoDesign source repository is not required after installation. Put inputs in `assets/input`, logs in `assets/logs`, outputs in `assets/output/<run>`, and project documentation in `docs`.

For an existing run, read these first when present:

- `AUTODESIGN_STATE.md`
- `input_brief.md`
- `method_route.md`
- `r0_record.json`
- `evidence_plan.md`
- `implementation_notes.md`
- `execution_record.json`
- `result_summary.json`
- `result_diagnosis.md`
- `result_route.md`
- `result_tuning.json`
- `next_round.md`
- `integrity_audit.md`

Resume from the first unfinished or invalidated stage. Do not rerun an expensive completed stage unless its input artifact changed.

## Read machine context

Before planning implementation or execution, read the effective `AGENTS.md` or `CLAUDE.md` instructions for the current workspace according to the current agent's normal precedence. When a run needs local or remote GPUs, treat an `AutoDesign GPU 执行上下文` section there as the only source of machine facts for SSH, allowed directories, GPU IDs, concurrency, environment location, timeouts, and process-preservation rules. Do not create or read a Python/JSON GPU configuration. If no such section applies, do not assume a remote host or GPU assignment.

Record the instruction file used and the resolved execution facts in `implementation_notes.md` and `execution_record.json`; keep research commands in the generated project's contracts rather than in the machine-context section.

## Use the artifact contract

Read `references/artifact-contract.md` before a new run or whenever handoff state is ambiguous. Start new runs from `assets/AUTODESIGN_STATE.template.md`. Markdown is the primary research interface; JSON is reserved for machine-observed execution and result records.

Only user-declared fields are locks. Defaults are recommendations. Preserve original contribution claims verbatim and record any scope change explicitly.

## Dispatch the pipeline

Load each named sibling Skill through the current agent's native Skill mechanism. When a filesystem path is required, resolve it from the parent directory of this installed `run-autodesign` Skill; an explicit custom installation may instead provide `AUTODESIGN_SKILLS_DIR`. Do not copy a worker's full instructions into this orchestrator.

1. **Input brief**: normalize the user's natural-language motivation, numbered contributions, benchmark tasks, metrics, splits, and explicit constraints into `input_brief.md`.
2. **Method route**: follow `$autodesign-method-router`; produce `method_route.md`. A goal-only route requires an independently executed R0.
3. **Evidence design**: follow `$autodesign-evidence-designer`; produce `evidence_plan.md` with claim-level falsifiers, baselines, experiments, tables, and figures.
4. **Implementation**: follow `$autodesign-implementer`; materialize `generated_project`, `implementation_notes.md`, environment definitions, commands, and result contract.
5. **Execution**: follow `$autodesign-executor`; run preflight, smoke, experiment, aggregate, and collect locally or remotely, preserving every literal command and exit status.
6. **Result science**: follow `$autodesign-result-scientist`; separate transport, evaluator, implementation, and method behavior before selecting iteration, tuning, stopping, or reporting. Require `result_route.md` for every diagnosis and `result_tuning.json` for tuning.
7. **Route closure**: read `result_route.md` and dispatch its owner Skill. An iteration or execution-required tuning action must pass through implementation or evidence repair, execution, result ingestion, and a fresh result diagnosis. Reporting-only tuning, `stop`, and `report` proceed to audit only when no experimental action remains open.
8. **Independent audit**: follow `$autodesign-integrity-auditor`; require a literal PASS before completion.

## Close result routes

- If the route identifies a method-selection defect, return to `$autodesign-method-router`.
- If it identifies missing or redesigned evidence, return to `$autodesign-evidence-designer`.
- If it changes code, configuration, data preparation, metrics, seeds, or launch commands, return to `$autodesign-implementer` and then `$autodesign-executor`.
- If it is only an unchanged-input execution or transport retry, return to `$autodesign-executor`.
- After every fresh or corrected execution, ingest results and rerun `$autodesign-result-scientist`.
- If tuning is selected, the result scientist must load `references/result_tuning_prompt.md`; do not reconstruct or shorten that prompt in the orchestrator.
- If no new execution is required, preserve the route decision and proceed to `$autodesign-integrity-auditor`.

## Apply gates

- **Route gate**: method-specified input preserves its core intervention; goal-only input compares at least two routes.
- **R0 gate**: a required R0 must have an executed record. A design-authored `passed` string is not evidence.
- **Evidence gate**: main, ablation, case, and interesting roles are necessary but insufficient; every original claim and derived test axis needs a real falsifier.
- **Implementation gate**: every accepted experiment has a runnable entrypoint, complete environment, preflight, result path, and observed chart path.
- **Execution gate**: `preflight → smoke → experiment → aggregate → collect` must all exit zero under the current commands before result diagnosis.
- **Result gate**: observed cells equal scheduled experiment × variant × task × seed cells and planned metrics; `result_summary.json.status` must be `READY_FOR_GPT_DIAGNOSIS` before entering `RESULT_DIAGNOSIS_READY`.
- **Route-closure gate**: `result_route.md` exists, every required tuning/iteration action is either executed and rediagnosed or explicitly closed by its threshold, and expected deltas are not reported as observations.
- **Integrity gate**: claims, runs, aggregates, tables, figures, and conclusions agree without hiding negative or mixed results.

## Maintain state

After each stage, use `python3 -m autodesign skill-advance` to update `AUTODESIGN_STATE.md` with:

- current stage;
- last completed stage;
- blocking condition;
- next Skill;
- changed input artifact;
- produced artifacts;
- literal decision and reason.

Append one history row instead of rewriting the scientific history. Keep failed routes and negative evidence visible.

Pass literal values directly to `skill-advance`; the state writer escapes table delimiters and line breaks so agent text cannot change the History column structure.

If table whitespace or alignment was edited manually, run `python3 -m autodesign skill-repair-state <run_dir>` before resuming. `INTEGRITY_AUDIT_PASS` and `COMPLETE` require a literal `Verdict: PASS`; an in-progress state keeps the previous completed milestone in `Last completed stage`.

## Finish

Completion requires:

- all stages through integrity audit are complete;
- no required artifact is missing;
- execution and result completeness pass;
- tables and figures are backed by observed aggregates;
- the latest result route is closed and no execution-required entry remains in `next_round.md`;
- `integrity_audit.md` says `PASS` with no unresolved blocker;
- `AUTODESIGN_STATE.md` ends at `COMPLETE`.

Return the run directory, selected route, execution target, exact result counts, contribution verdicts, tables, figures, and unresolved scientific limitations.
