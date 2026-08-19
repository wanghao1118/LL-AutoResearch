---
name: run-autodesign
description: "Orchestrate or resume the AutoDesign pipeline: design experiments from an AutoSearch handoff of Motivation, Contribution, and Benchmark, then execute them. Covers experiment design across main, ablation, case-study, and analysis families with simulated target effects, followed by implementation, execution, result diagnosis, and integrity audit. Use for a new AutoDesign run, same-run continuation, or end-to-end experiment automation."
---

# Run AutoDesign

AutoDesign has two phases, in this order:

```text
DESIGN  →  RUN
```

Design decides what experiments exist and what effect each one should achieve. Run implements and executes them, then compares observation against the design's targets. Never interleave the two: no code is written before the design's coverage audit says `PASS`, and no experiment is added or redefined during execution.

Apply this precedence throughout:

```text
scientific intent > evidence eligibility > execution completeness > presentation
```

A completed pipeline that changed the Idea or evaluated it with ineligible evidence is not a successful scientific run.

## Accept the input

The upstream module is **AutoSearch**, owned outside this repository. AutoDesign consumes three things from its export: **Motivation**, **Contribution**, and **Benchmark**.

Two input channels are equally valid:

- a canonical `autosearch_handoff.json` in the run directory or `assets/input/`;
- natural language in the conversation — this is normal usage, for example `/run-autodesign` followed by the motivation, contributions, and benchmark written out in prose.

The user may also supply more than the three required items: an initial experiment plan, preferred baselines, compute limits, related work, or explicit constraints. Absorb everything supplied; never discard information because no schema field matches it, and never demand a JSON file when the three required items are already present in the request. Stop with a blocker only when Motivation, Contribution, or Benchmark is genuinely absent.

`$autodesign-experiment-design` owns normalization into `input_brief.md`. Read `references/autodesign-flow.md` for the run layout, state vocabulary, and invalidation rules.

## Locate the run

Use the user's current workspace or an explicitly selected run workspace. The installed Skills and the `autodesign` Python package are the runtime dependencies; this source repository is not required after installation. Put inputs in `assets/input`, logs in `assets/logs`, outputs in `assets/output/<run>`, and documentation in `docs`.

When resuming the same Idea and run, read these first when present:

- `AUTODESIGN_STATE.md`
- `input_brief.md`
- `experiment_design.md`
- `expected_effects.json`
- `r0_record.json`
- `implementation_notes.md`
- `execution_record.json`
- `result_summary.json`
- `effect_comparison.md`
- `result_diagnosis.md`
- `result_route.md`
- `next_round.md`
- `integrity_audit.md`

Resume from the first unfinished or invalidated stage. Do not rerun an expensive completed stage unless its input artifact changed. Design and execute fresh experiments for the supplied Idea; never copy pre-existing observations into a new run as a substitute for executed evidence.

## Dispatch

Load each named sibling Skill through the current agent's native Skill mechanism. When a filesystem path is required, resolve it from the parent directory of this installed `run-autodesign` Skill, or from `AUTODESIGN_SKILLS_DIR` when explicitly provided. Do not copy a worker's instructions into this orchestrator.

**Phase 1 — Design.** Follow `$autodesign-experiment-design`. It normalizes the handoff into `input_brief.md`, selects the method route, designs the `main`, `ablation`, `case_study`, and `analysis` experiments, and writes `experiment_design.md` plus `expected_effects.json` with a simulated target and decision threshold for every planned cell. It writes `r0_plan.md` when a low-cost gate is required.

**Phase 1b — R0, only when required.** Dispatch `$autodesign-experiment-run` to execute the R0 probe and return `r0_record.json`, then return to `$autodesign-experiment-design` to accept or revise the route. A failed R0 revises the design; it never silently switches the full experiment.

**Phase 2 — Run.** Follow `$autodesign-experiment-run`. It materializes `generated_project/`, writes `command_plan.json`, `experiment_schedule.json`, and `result_contract.json`, executes `preflight → smoke → experiment → aggregate → collect`, ingests results, and writes `effect_comparison.md` comparing observed values against the design's simulated targets.

**Phase 3 — Result science.** Follow `$autodesign-result-scientist`. It checks evidence eligibility before behavior, assigns contribution verdicts, and writes `result_route.md`.

**Phase 4 — Route closure.** Read `result_route.md` and dispatch its owner Skill. An iteration or execution-required tuning action must pass back through design or implementation repair, execution, ingestion, and a fresh diagnosis. Reporting-only tuning, `stop`, and `report` proceed to audit only when no experimental action remains open.

**Phase 5 — Independent audit.** Follow `$autodesign-integrity-auditor`; require a literal `Verdict: PASS`.

## Close result routes

- A method-selection defect, missing evidence, redesigned experiment, or changed experiment set returns to `$autodesign-experiment-design`.
- A code, configuration, data-preparation, metric, seed, or command change returns to `$autodesign-experiment-run`.
- An unchanged-input execution or transport retry returns to `$autodesign-experiment-run` for execution only.
- After every fresh or corrected execution, ingest results, recompare effects, and rerun `$autodesign-result-scientist`.
- When iteration or tuning is selected, the result scientist loads its bundled `result_tuning_prompt.md` as the action planner; do not reconstruct that prompt here.
- When no new execution is required, preserve the route decision and proceed to `$autodesign-integrity-auditor`.

## Apply gates

- **Handoff gate**: Motivation, Contribution, and Benchmark are present and preserved verbatim; extra user-supplied input is absorbed and classified; nothing is invented to fill a gap.
- **Design gate**: `experiment_design.md` ends in a literal coverage-audit `PASS`. Every contribution and derived axis has a `CLAIM_BEARING` falsifier; all four families are populated or their absence is justified against the contributions; every case study has a pre-result selection rule with failure categories; every selected baseline has a fairness plan and appears in a main experiment.
- **Target gate**: every expected cell has an `expected_effects.json` entry with `value_status: SIMULATED_TARGET`, a literal `decision_threshold`, a `target_basis`, and an `on_miss` route. A simulated target never appears in `reports/`, a table, a figure, or a claim verdict.
- **Idea-consistency gate**: the route preserves the user's scientific locks and operational meaning; unstated choices remain explicit design decisions rather than retroactive additions to the Idea.
- **R0 gate**: a required R0 has an executed record covering every high-impact autonomous choice not resolved by the user, comparing at least two candidate instantiations. A design-authored `passed` string or a single documented default is not evidence, and R0 success alone never supports a contribution.
- **Implementation gate**: every accepted experiment across all four families has a runnable entrypoint, complete environment, decision-relevant preflight, result path, and observed chart path. Preflight compares planned and materialized scientific identities, data composition, benchmark provenance, and protocol values before expensive execution.
- **Execution gate**: `preflight → smoke → experiment → aggregate → collect` all exit zero under the current commands.
- **Result gate**: observed cells equal scheduled experiment × variant × task × seed cells and planned metrics, no unexpected cell is silently absorbed, each result preserves its family, evidence class, and benchmark provenance, and `result_summary.json.status` is `READY_FOR_GPT_DIAGNOSIS`.
- **Comparison gate**: `effect_comparison.md` covers every design entry with a threshold outcome, retains every `MISSED` and `NOT_EVALUABLE` row, and reports no post-hoc edit to a simulated target.
- **Route-closure gate**: `result_route.md` exists, every required action is executed and rediagnosed or explicitly closed by its threshold, and expected deltas are never reported as observations.
- **Integrity gate**: claims, runs, aggregates, tables, figures, and conclusions agree without hiding negative or mixed results.

## Maintain state

After each stage, run `python3 -m autodesign skill-advance` to update `AUTODESIGN_STATE.md` with the current stage, last completed stage, blocking condition, next Skill, changed input artifact, produced artifacts, and the literal decision and reason. Append one history row rather than rewriting scientific history; keep failed routes and negative evidence visible. Pass literal values directly — the state writer escapes table delimiters so agent text cannot break the History column.

If table whitespace or alignment was edited by hand, run `python3 -m autodesign skill-repair-state <run_dir>` before resuming. `INTEGRITY_AUDIT_PASS` and `COMPLETE` require a literal `Verdict: PASS`; an in-progress state keeps the previous completed milestone in `Last completed stage`.

## Finish

Completion requires:

- both phases and all post-stages through integrity audit are complete;
- no required artifact is missing;
- every required claim-bearing experiment is complete or a valid preregistered kill threshold has been crossed;
- no pilot or smoke substitutes for missing claim-bearing evidence;
- execution and result completeness pass;
- `effect_comparison.md` covers every design entry;
- tables and figures are backed by observed aggregates only;
- the latest result route is closed and no execution-required entry remains in `next_round.md`;
- `integrity_audit.md` says `PASS` with no unresolved blocker;
- `AUTODESIGN_STATE.md` ends at `COMPLETE`.

Return the run directory, selected route, experiment counts per family, execution target, exact result counts, target-versus-observed outcomes, contribution verdicts, tables, figures, and unresolved scientific limitations.
