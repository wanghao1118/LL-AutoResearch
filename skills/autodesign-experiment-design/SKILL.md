---
name: autodesign-experiment-design
description: "Design a paper-grade experiment portfolio from an AutoSearch Motivation, Contribution, and Benchmark handoff. Use before implementation or execution, for a design-first AutoWriting handoff, or to revise a design after R0 or result feedback."
---

# AutoDesign Experiment Design

Design only: do not implement or run experiments. Preserve this precedence:

```text
scientific intent > evidence eligibility > design completeness > presentation
```

Read [references/autosearch-handoff.md](references/autosearch-handoff.md) for input normalization and [references/design-contract.md](references/design-contract.md) for artifact fields, identities, placeholders, and schemas.

## 1. Input locks and scope

The only authoritative scientific intent is the AutoSearch handoff's **Motivation**, **Contribution**, and **Benchmark**. Accept `autosearch_handoff.json` from the run directory or `assets/input/`, or the same three items as natural language. Preserve the literal handoff in `input_brief.md`; if any item is absent or contradictory, stop instead of inventing or selecting it.

Separate the input into:

- **scientific locks**: the stated mechanism plus named benchmarks, splits, metrics, data, models, baselines, protocols, fairness requirements, and scope-bearing language needed to interpret a contribution;
- **autonomous choices**: unstated design decisions, each classified `high` or `low` outcome impact;
- **resource constraints**: cost limits, which never relax a lock.

A high-impact choice changes what the experiment can show, including data constructor, teacher or judge identity/protocol, backbone, or execution substrate when it affects outcomes. Resolve it only by an explicit user decision or a registered R0 comparing at least two candidate instantiations. A default, citation, or plausibility argument does not resolve it.

Use literature to select applicable baselines/components, lock benchmark protocol, or locate official implementations and model cards. Do not import unstated method configurations or outcomes, and never redefine the Idea from external material.

A disclosed lock change is still a blocker; disclosure does not make reduced evidence claim-bearing.

## 2. Route and R0

Choose the scientific intervention before concrete components. Record the operational meaning, observable implication, prohibited reinterpretation, and uncertainty of each central term. Treat `all`, `each`, named stages/objects/spans, and equivalent scope language as locks; a subset route is an ablation or `MECHANISM_PILOT`, not the full method.

Classify the handoff as `method_specified`, `mechanism_specified`, or `goal_only`. Preserve a specified method. For mechanism-specified or goal-only input, compare at least two route families with distinct falsifiable predictions. Give each candidate its intervention, minimal probe, falsifier, contribution/benchmark fit, cost, and rejection condition. Select only roles the route needs, then close the role inventory: every outcome-impacting backbone, constructor/teacher, judge, verifier, retriever, reward model, tool, substrate, or training loop must be a lock or a resolved autonomous-choice row before it appears downstream.

Require R0 for goal-only input, unresolved high-impact choices, and expensive routes with unresolved central feasibility. R0 is a gate, never claim support. For every comparison:

- vary only the registered high-impact choice; keep teacher/backbone, data, budget, protocol, and every other outcome-impacting axis matched, or factor the additional axis into a separate control;
- preserve every scientific lock; an R0 win cannot legalize a weakened Idea;
- if fitting, adaptation, prompt selection, or data construction occurs, keep fit/materialization IDs, candidate-selection IDs, and later `CLAIM_BEARING` IDs disjoint;
- register every cell named by a selection or kill rule, including reference cells, in the R0 execution-cell inventory with budget, command intent, outputs, metrics, and cost.

Write `r0_plan.md` when required. `$autodesign-experiment-run` executes it; its matching `r0_record.json` returns here for design revision. A missing or unbudgeted rule reference is an evidence gap, not an implicit free comparison.

## 3. Claim-bearing evidence

Assign each experiment one paper family—`main`, `ablation`, `case_study`, or `analysis`—and one evidence class—`CLAIM_BEARING`, `MECHANISM_PILOT`, or `ENGINEERING_SMOKE`. Only `CLAIM_BEARING` evidence may support or refute a contribution.

Every claim-bearing experiment owns one primary research question and this **Claim Contract**:

```text
research_question
intervention
matched_reference
primary_metric
literal_falsifier
claim_collapse
```

The reference, unit, and aggregation must isolate the intervention. If the literal falsifier is met, `claim_collapse` names the exact claim to narrow or withdraw; extra interpretation cannot convert every outcome into support.

- **Main** asks whether the contribution holds on the locked benchmark. Map every contribution to a named benchmark, split, metric, multiple seeds, and uncertainty. Close two baseline roles: `causal_reference` is matched on key axes except the target intervention and estimates its effect; `contextual_baseline` is a recognizable independent external system that positions the paper. One baseline may serve both only when both roles are justified separately. Missing either role is an evidence gap even if other baselines exist. Run selected baselines under source-backed protocols without removing their defining scaffold; a surrogate remains a named pilot and never inherits an official benchmark identity.
- **Ablation** asks which part causes the effect. Remove or substitute one mechanism component while fixing all other axes. Sample eligibility, filtering, replenishment, and composition are data-axis changes and cannot be bundled with an objective, mask, or component change. A multi-axis contrast is a design defect.
- **Case study** asks what the behavior looks like. Freeze eligible pool, sampling rule/seed, category counts, and display fields before results. When a contribution concerns failure or recovery, define one preregistered taxonomy shared with its quantitative analysis and cover recovered, unrecovered, and side-effect cases. The panel illustrates that analysis; it is not a separately cherry-picked story. For every included case study, `experiment_design.md` must contain a first-pass **case-study figure draft**, not only figure metadata and not a method-overview or main-results figure. Match the visual grammar of a paper transcript excerpt: multi-line trace text, inline `Prompt`, `Agent`, `Tool Call`, `Tool Response`, `Comment`, and `Final Outcome` labels as applicable, dashed rules between turns, and restrained emphasis on decisive evidence. Target a half-page, full-width `figure*` in a two-column arXiv-style paper: when two cases are shown, place their transcript panels left and right rather than stacking them vertically. It is not a box-and-arrow process diagram: do not default to rounded cards, flow arrows, dashboard headers, status badges, or large legends. Follow the `case_figure_plan` and `case_figure_draft` size/content budget; never require hidden chain-of-thought or invent or ellipsis-compress evidence.
- **Analysis** asks why the method works and where it breaks. Test only axes entailed by the contributions, with enough levels and matched references to identify the claimed direction, shape, robustness, or transfer. Cross-context evidence compares within-context method effects; proposed-method scores alone do not isolate transfer.

Design paper-facing tables before simulated targets. The primary table plans absolute observed results for the proposed method and selected baselines across the locked scope; plan uncertainty in the result contract, but do not fabricate its display in an empty shell. Every numeric slot in a design-time table uses only the exact typed placeholder `{{RESULT:<experiment_id>::<variant_id>::<benchmark_task_id>::<metric>}}` or, for an intentionally displayed derived effect, `{{EFFECT:<entry_id>}}`. Never write mnemonic pseudo-values such as `R ± CI`, `R+CI`, `C ± CI`, `Rate ± CI`, `Δ ± CI`, `mean ± std`, or similar confidence/dispersion text in a placeholder cell. Decide the observed-value and uncertainty rendering only after the aggregate exists. Keep internal variants in ablation/focused analysis views, define only commensurate averages, and distinguish unavailable cells from zero. A curve, distribution, or trajectory belongs in a figure when that is the actual evidence.

## 4. Artifacts and readiness

Write `experiment_design.md`, read-only `expected_effects.json`, and `r0_plan.md` only when needed. Follow the contract for the claim ledger, route/R0 inventories, Claim Contracts, experiment cards, execution/aggregate/paper/decision identities, table shells, coverage audit, and JSON schema.

Pre-register one `SIMULATED_TARGET` entry per decision effect, not per seed or displayed reference cell. Each entry has a literal threshold, target basis, and `on_miss: iteration|tuning|stop`; relative thresholds name a planned reference aggregate. Simulated targets are hypotheses, never observations or claim support.

In `## AutoWriting handoff`, use `ACCEPTED` or `PROVISIONAL_WAITING_FOR_R0`, identify safe and conditional sections, provide complete result/effect placeholders, and name invalidations after R0 or design revision. Numeric draft targets require document-level `DRAFT — SIMULATED TARGETS, NO OBSERVED RESULTS` plus a same-cell/caption `SIMULATED_TARGET` label. They never enter `reports/`, observed prose, final claims, or submission-ready results.

Validate structure with:

```bash
python3 -m autodesign skill-check-design <run_dir>
```

Top-level `status: PASS` means only that deterministic artifact structure is usable; read `declared_design_readiness` separately. End the coverage audit with exactly one verdict:

- `PASS`: locks, role/baseline/R0 closure, Claim Contracts, evidence coverage, tables, targets, taxonomy links when applicable, and handoff are scientifically complete; no high-impact choice remains. Use `handoff_status: ACCEPTED` and advance to `EXPERIMENT_DESIGN_READY`.
- `PROVISIONAL_WAITING_FOR_R0`: the same design requirements hold, but registered high-impact choices await R0. Use the same handoff status and advance only to `WAITING_FOR_R0`.
- `FAIL`: any design/evidence gap remains. Name it and stay before design readiness.

An absent family needs a contribution-grounded reason under `## Absent families`; placeholder prose may satisfy the structural parser but not this scientific judgement. Update state with `python3 -m autodesign skill-advance`. The next execution Skill is `$autodesign-experiment-run`.
