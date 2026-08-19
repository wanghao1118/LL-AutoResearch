---
name: autodesign-experiment-design
description: "Design a complete paper-grade experiment portfolio from an AutoSearch handoff of Motivation, Contribution, and Benchmark. Produces the method route, main experiments, ablations, case studies, analysis experiments, paper-table plans, simulated decision effects, and a draft-safe handoff that lets AutoWriting start before real results arrive. Use before implementation or execution, for a design-first writing handoff, or to repair a design after a failed R0 or result route."
---

# AutoDesign Experiment Design

Design the experiments. Do not implement them and do not run them.

This Skill is the first half of AutoDesign. It consumes the upstream AutoSearch handoff and produces one design artifact plus one machine-readable, design-time target artifact. The design artifact also carries the downstream AutoWriting handoff. `$autodesign-experiment-run` is the only Skill that writes experiment code or executes experiment commands.

Apply this precedence:

```text
scientific intent > evidence eligibility > design completeness > presentation
```

## Read the input

The authoritative input is the AutoSearch handoff: **Motivation**, **Contribution**, and **Benchmark**. Read `references/autosearch-handoff.md` for the accepted schema and the natural-language fallback.

1. Locate `autosearch_handoff.json` in the run directory or `assets/input/`. If no such file exists, accept Motivation, Contribution, and Benchmark pasted as natural language in the conversation and normalize them yourself.
2. Preserve the handoff verbatim in `input_brief.md` before interpreting anything. Never paraphrase a contribution into the ledger.
3. Stop and report a blocker if Motivation, Contribution, or Benchmark is absent. A missing benchmark is a blocker, not an invitation to select one.
4. Separate the input into:
   - **scientific locks**: stated mechanisms and named benchmarks, splits, metrics, datasets, models, baselines, protocols, or fairness requirements needed to interpret a contribution;
   - **autonomous design choices**: details the handoff did not specify and this Skill may choose;
   - **resource constraints**: limits that change cost planning but never relax a lock.
5. Classify every autonomous choice as `high` or `low` outcome impact. A **high-impact** freedom materially changes what the experiment can show, including who generates training data, teacher or judge roles, and the execution substrate. Resolve each high-impact freedom through an explicit user decision or a planned R0 that compares at least two candidate instantiations. A single documented default is not a resolution.

Use literature only to select applicable baselines and components, confirm benchmark protocols, and locate official implementations or model cards. Do not import unstated method configurations or outcomes, and do not redefine the Idea from external material.

## Choose the method route

Choose the scientific intervention before concrete components. Do not default to a student/teacher/training menu.

1. Build an Idea semantics table for every central term: operational meaning, what it constrains, what it does not constrain, observable implication, disallowed reinterpretation, unresolved uncertainty.
2. Classify the handoff as `method_specified`, `mechanism_specified`, or `goal_only`.
3. For `method_specified`, preserve the core intervention and compare implementation choices only. For `mechanism_specified` or `goal_only`, compare at least two route families with different falsifiable predictions.
4. Consider only applicable families: inference-time control, prompting or decoding, retrieval or memory, tool or environment adaptation, data construction, SFT, preference optimization, RL, hybrid, or a contribution-specific alternative.
5. Give every candidate a minimal probe, falsifier, contribution fit, benchmark fit, resource estimate, and rejection condition.
6. Require an R0 gate for `goal_only`, for every unresolved high-impact autonomous choice, and for any expensive route whose central feasibility remains uncertain. Write `r0_plan.md` when R0 is required; `$autodesign-experiment-run` executes it and returns `r0_record.json` here for a design revision.
7. Select the smallest sufficient set of conditional roles: backbone, teacher, verifier, retriever, reward model, tool, or training loop.

## Design the four experiment families

Assign every experiment exactly one **family** and exactly one **evidence class**. The two are orthogonal: family is the paper role, evidence class is claim eligibility.

- family: `main`, `ablation`, `case_study`, `analysis`;
- evidence class: `CLAIM_BEARING`, `MECHANISM_PILOT`, `ENGINEERING_SMOKE`.

Only `CLAIM_BEARING` experiments can support, mix, or refute a contribution. Family labels alone never prove coverage.

### Main experiments

Answer "does the contribution hold on the locked benchmark". Every contribution needs at least one `main` + `CLAIM_BEARING` experiment on a named benchmark, split, and metric from the handoff, with multiple seeds and reported uncertainty. Select baselines independently: closest work, strongest applicable system, and a simple control. Every selected baseline must actually run in a main experiment under a source-backed fairness plan; preserve a baseline's defining scaffold or protocol instead of equalizing it away. Keep every locked benchmark identifier exact — a surrogate may appear only as a distinctly named pilot and may never reuse an official benchmark identifier.

### Ablation experiments

Answer "which part causes the effect". Decompose the accepted mechanism into removable or replaceable components and change exactly one variable per ablation while holding every other axis fixed. Cover component removal, component substitution, and leave-one-group-out where a group axis exists. State for each ablation which claim collapses if the ablation shows no difference. An ablation that changes two axes at once is a design defect, not a cheaper experiment.

### Case studies

Answer "what does the behavior look like". Predefine the selection rule, the sample count, and the display fields **before any result exists**. Require both success and failure cases, and state the category budget, for example `4 recovered trajectories + 4 unrecovered trajectories, sampled by fixed seed from the eligible pool`. Post-hoc cherry-picking is a literal design failure; if the selection rule cannot be written without looking at results, the case study is not designed yet.

### Analysis experiments

Answer "why it works and when it breaks". Select the axes the contributions actually entail, such as data-budget or scaling curves, teacher-quality levels, seen versus unseen generalization, robustness or perturbation, sensitivity to a key hyperparameter, error taxonomy, and cost or latency. Use at least two teacher levels for a teacher-quality claim, at least three data levels for a budget claim, matched seen and unseen evaluation for a generalization claim, and error-present and error-absent strata for an error-conditioning claim.

## Design paper tables before target effects

Design the paper-facing result structure before writing simulated targets. Read the paper-table contract in `references/design-contract.md` and give every planned table a paper question, row semantics, column semantics, absolute-result sources, optional derived impact columns, and output path.

1. Make the primary table a complete method comparison. Use methods, models, scaffolds, or comparable systems as rows; use locked benchmarks, splits, metrics, or metric groups as columns. Include every selected baseline and the proposed method, and show absolute observed performance with uncertainty where applicable. A table of task-wise deltas is not a primary results table.
2. Keep internal component removals and substitutions in an ablation table unless they are independently meaningful baselines. Show the full method and each one-axis variant as rows, absolute performance on the relevant tasks, and optionally a drop or impact column.
3. Use compact analysis tables for a discrete local question such as one optimization stage, backbone transfer, data-source removal, error group, or protocol choice. Use a figure instead when the evidence is primarily a curve, distribution, or trajectory.
4. Adapt the layout to the study. Multi-level metric headers, method groups, model/scaffold columns, paired rows per backbone, domain leave-one-out rows, and compact two-row mechanism tables are all valid. Do not copy a fixed template when another orientation makes the comparison clearer.
5. Define averages only across commensurate cells and state whether they are macro or weighted. Mark genuinely unavailable cells as unavailable; never turn them into zero.

Separate three objects in the design:

- an **aggregate result** is an absolute observed experiment × variant × task × metric value after combining seeds;
- a **paper result cell** displays an aggregate result in a table or figure;
- a **decision effect** is a claim-relevant comparison, drop, direction, shape, or category requirement that needs a target and an `on_miss` route.

Baselines and other display rows need aggregate results and paper placeholders, but they do not need fake scientific thresholds merely because they appear in a table.

## Write the simulated decision effects

Write every decision effect you intend to test **before execution**, as a simulated target with a decision threshold. Anchor a numeric effect to the proposed or ablated variant's absolute aggregate result and name its reference variant when the threshold is relative. Execution cells remain per seed; ordinary baseline display cells stay out of `expected_effects.json`.

1. Every value carries `value_status: "SIMULATED_TARGET"`. A simulated target is a design hypothesis. It is never an observation, never enters `reports/`, and never satisfies a claim. It may appear only in an explicitly marked AutoWriting draft under the handoff rules below.
2. Give each entry a `simulated_target`, an `acceptable_range`, and a literal `decision_threshold` that can be evaluated against observed numbers, for example `>= reference + 2.0` with an explicit `threshold_reference_variant`.
3. Derive targets from the handoff's reported numbers where it supplies them, from published baseline numbers where those are locked, and from an explicitly labelled estimate otherwise. Record which of the three each target came from.
4. State `on_miss` for every entry: the route to take when the observed value misses the threshold, one of `iteration`, `tuning`, or `stop`.
5. Cover every family that owns a claim-relevant decision. A main effect states the target advantage over its reference baseline; an ablation effect states the expected drop when its component is removed; a case study states the required category counts; an analysis effect states the expected difference, shape, or direction.
6. Write `expected_effects.json` per `references/design-contract.md`. Keep it aligned one-for-one with the decision effects in `experiment_design.md`; do not add entries for reference-only or presentation-only result cells and do not repeat entries per seed.

Order experiments by information gain per unit cost: cheap kill tests before expensive confirmation.

## Output

Write `experiment_design.md` containing the claim ledger, Idea semantics, scientific locks, autonomous-choice impact table with resolution evidence, candidate and selected route, baseline decision, R0 gate, experiment cards for all four families, planned execution cells, aggregate results, paper table plan, decision effects, preflight requirements, reporting plan, AutoWriting handoff, and coverage audit. Write read-only `expected_effects.json` with the simulated decision targets. Write `r0_plan.md` only when R0 is required.

In `## AutoWriting handoff`, record `ACCEPTED` or `PROVISIONAL_WAITING_FOR_R0`, the sections safe to draft now, conditional sections, and complete table and figure shells. Use `{{RESULT:<experiment_id>::<variant_id>::<benchmark_task_id>::<metric>}}` for every absolute aggregate displayed in a paper shell and `{{EFFECT:<entry_id>}}` only for an optional derived comparison column. Name the replacement sources after execution. If a numeric simulated target is useful for drafting, require the document-level label `DRAFT — SIMULATED TARGETS, NO OBSERVED RESULTS` and a same-cell or same-caption `SIMULATED_TARGET` label. Never permit draft values to become observed prose, final claims, or submission-ready results. When R0 revises the design, reissue the handoff and name every invalidated table, result key, and effect entry ID.

Validate the design before handing off:

```bash
python3 -m autodesign skill-check-design <run_dir>
```

End the coverage audit with a literal `PASS` only when every contribution and derived axis has a `CLAIM_BEARING` falsifier, all four families are populated or every absent family has a reason under `## Absent families`, every locked benchmark has valid provenance, every selected baseline has a fairness plan, every case study has a pre-result selection rule, the primary paper table contains absolute results for selected baselines and the proposed method across the locked evaluation scope, every decision effect has a simulated target with a threshold, and the AutoWriting handoff labels its maturity and complete result placeholders. Otherwise list blockers and do not advance.

The gate checks only that an absent family has *a* reason written, never whether the reason holds. That judgement is yours: an absence is justified when it follows from the contributions — a failure-mode finding owns no module to ablate, a distributional claim cannot ride on one trace. Filler that clears the gate (`n/a`, `TBD`, `待定`) is a design you have not finished, and `autodesign-integrity-auditor` reads these reasons verbatim and fails them.

Update `AUTODESIGN_STATE.md` with `python3 -m autodesign skill-advance` to `EXPERIMENT_DESIGN_READY`, or to `WAITING_FOR_R0` when R0 must run first. The next Skill is `autodesign-experiment-run`.
