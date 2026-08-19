# Experiment Design Contract

`experiment_design.md` is the single design artifact and carries the AutoWriting handoff. `expected_effects.json` is its read-only machine-readable target companion. Both are written by `$autodesign-experiment-design` and read by `$autodesign-experiment-run`; execution never writes back into the target file.

## 1. Claim ledger

| Claim ID | Contribution | Original claim (literal) | Mechanism | Required axes | Claim-bearing experiments | Falsifier | Status boundary |
| --- | --- | --- | --- | --- | --- | --- | --- |

Every contribution appears at least once. Every required axis maps to a real `CLAIM_BEARING` comparison. Pilots and smokes stay visible but never satisfy this mapping.

## 2. Idea semantics

For every central term: operational meaning, what it constrains, what it does not constrain, observable implication, disallowed reinterpretation, unresolved uncertainty. Derive from the handoff plus ordinary technical usage only.

## 3. Scientific locks and autonomous choices

| Choice ID | Autonomous choice | Outcome impact | Effect on what the experiment can show | Candidate A | Candidate B | Fixed controls | Resolution source | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Outcome impact is exactly `high` or `low`. A high-impact resolution source is either an explicit user decision or a planned R0 comparing at least two candidate instantiations. A documented default, plausibility argument, or citation alone is not a resolution; the design stays blocked while any high-impact freedom is unresolved.

## 4. Route selection

| Route ID | Family | Intervention | Minimal probe | Falsifier | Contribution fit | Benchmark fit | Compute and data | Source evidence | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

At least two candidate routes for `mechanism_specified` or `goal_only` input. Record the selected route ID, full method configuration, conditional component roles, and why each rejected route is less diagnostic. Record every scientific lock and its honored implementation. A lock change cannot be accepted by disclosure: either restore it, or reclassify the reduced route as `MECHANISM_PILOT` / `ENGINEERING_SMOKE` and keep the affected contribution `INCOMPLETE`.

## 5. Baseline decision

For each candidate: source, revision, role coverage, contribution fit, benchmark fit, scaffold and protocol requirements, fairness plan, cost, selected or rejected, rationale. Selected baselines must appear as variants in `main` `CLAIM_BEARING` experiments. Equal budgets never justify changing a baseline's defining scaffold.

## 6. R0 gate

Record `required: yes_or_no`, covered uncertainty or high-impact choice IDs, at least two candidate instantiations per unresolved high-impact choice, fixed controls, probe IDs, evidence class, literal selection threshold, literal kill threshold, cost, and next action per outcome. A single-candidate probe cannot pass this gate. R0 is never claim support by itself.

## 7. Experiment cards

Each card records:

- experiment ID;
- **family**: `main`, `ablation`, `case_study`, or `analysis`;
- **evidence class**: `CLAIM_BEARING`, `MECHANISM_PILOT`, or `ENGINEERING_SMOKE`;
- mapped claim IDs and the exact claim subset tested;
- hypothesis and falsifier;
- variants and baselines;
- benchmark identity, provenance, revision, tasks, splits, facets, metrics, protocol locks;
- seeds;
- controlled axes and the single changed axis;
- data manifest, sampling policy, planned composition, and quality observables when applicable;
- entrypoint intent (what code must exist, not the code itself);
- result artifacts;
- decision rule;
- priority and cost.

Family-specific additions:

- `main`: reference baseline for the reported delta; uncertainty reporting method.
- `ablation`: the removed or replaced component, the single changed axis, every fixed axis, and which claim collapses if no difference appears.
- `case_study`: the pre-result selection rule, required category counts including failures, sampling seed, display fields, and the eligible pool definition.
- `analysis`: the analysis axis, its levels, the expected shape or direction, and the boundary the analysis is meant to locate.

## 8. Execution, result, presentation, and decision identities

Keep four related identities separate:

- **execution cell**: experiment × variant × task × seed, with family, evidence class, benchmark provenance, and planned metrics;
- **aggregate result**: experiment × variant × task × metric, evaluated after combining every planned seed and containing the absolute observed value plus uncertainty;
- **paper result cell**: a table or figure location that displays one aggregate result, or an explicitly named derived summary such as a commensurate macro average;
- **decision effect**: a claim-relevant comparison, drop, direction, curve shape, or category requirement with a simulated target, literal threshold, and miss route.

List the execution cells, aggregate results, and decision effects separately. `experiment_schedule.json` expands execution cells per seed. `result_summary.json` contains every produced aggregate result. `expected_effects.json` contains one target per decision effect, not one target per display cell and not one target per seed.

A numeric decision effect is anchored to the aggregate result for its target variant. A relative threshold names the reference variant whose aggregate result supplies the comparison. Reference-only baselines and other presentation-only rows remain in the schedule and paper tables without receiving vacuous targets such as `>= 0`. Every expected effect and every relative reference must resolve to a planned aggregate result once `experiment_schedule.json` exists. A later round requires an explicit design, table-plan, and schedule revision; it may not append results or effects silently.

## 9. Paper table plan

Design tables as paper arguments, not as dumps of effect entries. For each table record:

- table ID, family or analysis role, paper question, mapped claims, and experiment IDs;
- row semantics and the exact ordered row groups;
- column semantics, including benchmark, split, metric, budget, condition, or derived-impact columns;
- the aggregate-result key behind every absolute result position;
- any optional decision-effect entry used for a delta, drop, or impact column;
- uncertainty display, average definition, missing-cell policy, caption claim, and output path under `reports/`.

Choose the layout from the evidence:

- **Primary results**: rows are comparable methods, models, scaffolds, or systems; columns are locked benchmarks, splits, and primary metric groups. Include every selected baseline and the proposed method. Show absolute performance, with uncertainty where applicable. Put the proposed method in a visibly named row or row group. A task-by-task delta-only layout is not a primary table.
- **Ablation**: rows contain the full method and one-axis removals, substitutions, or leave-one-group-out variants; columns contain the relevant task metrics. Preserve absolute performance and optionally add an impact column such as `Δ Avg.`. Do not move ordinary internal ablations into the primary table merely to increase its method count.
- **Focused analysis**: use a compact table when a discrete local question is best answered by exact values, for example `SFT` versus `+RL`, paired methods within each backbone, one data source removed at a time, an error group, or a protocol option. Keep only the benchmarks and metrics that answer that question. Use a figure instead for a continuous curve, distribution, or trajectory.

Multi-level headers, benchmark panels, metric panels, model/scaffold columns, method groups, paired backbone rows, and compact two-row tables are valid. No fixed orientation is mandatory. Optimize for the comparison the reader must make.

An average is valid only across commensurate cells and must be labelled macro, weighted, or otherwise defined. A genuinely unavailable result is marked unavailable and explained; it is never converted to zero. If primary and secondary metrics make one table unreadable, use panels or separate tables rather than dropping a locked metric.

## 10. Preflight requirements

For every scientific lock and controlled axis: the exact observable check, its failure condition, and the changed next action. For data-based routes require planned-versus-materialized sample counts and distributions before expensive execution. When filtering or decontamination is required, trace the production path from source data through the materialized artifact to the exact training input.

## 11. Reporting plan

Each table and figure declares experiment IDs, aggregate-result keys, optional decision-effect IDs, fields or axes, output path under `reports/`, and the decision it supports. The reporting plan must agree with the paper table plan; it may refine presentation but may not change the comparison set.

## 12. AutoWriting handoff

End the design with `## AutoWriting handoff`. This is a section of `experiment_design.md`, not a new state or a new schema. Record:

- `handoff_status`: `ACCEPTED` or `PROVISIONAL_WAITING_FOR_R0`;
- sections safe to draft now and sections that remain conditional;
- stable method, benchmark, baseline, protocol, and experiment identities;
- complete table shells and figure plans, with `{{RESULT:<experiment_id>::<variant_id>::<benchmark_task_id>::<metric>}}` for every absolute aggregate displayed and `{{EFFECT:<entry_id>}}` only where a derived effect is displayed;
- replacement source: `effect_comparison.md` and observed aggregates in `result_summary.json`;
- invalidation rule for an R0 or later design revision, naming affected section titles, table IDs, result keys, and decision-effect entry IDs.

Prefer placeholders over numeric simulations. When a numeric simulated target is useful, require the containing document to display `DRAFT — SIMULATED TARGETS, NO OBSERVED RESULTS` and require `SIMULATED_TARGET` in the same cell or caption. Draft targets never enter `reports/`, an observed-result sentence, a contribution verdict, or a submission-ready table or figure. AutoWriting may improve presentation but may not change the accepted scientific design.

## 13. Coverage audit

End with literal `PASS` only when:

- every contribution and derived axis has a `CLAIM_BEARING` falsifier;
- all four families are populated, or every absent family is justified under `## Absent families`;
- every locked benchmark has valid provenance;
- every selected baseline has a fairness plan and appears in a main experiment;
- every case study has a pre-result selection rule with failure categories;
- every decision-relevant preflight has a failure action;
- the primary table shows absolute results for every selected baseline and the proposed method over the locked main-evaluation scope;
- every paper result cell maps to a planned aggregate result or an explicitly defined derived summary;
- every decision effect has exactly one matching entry in `expected_effects.json`, without fake targets for reference-only rows;
- the AutoWriting handoff covers every paper result cell and labels its maturity.

Otherwise list blockers and keep the state before `EXPERIMENT_DESIGN_READY`.

## Absent families

A family may be absent only when its absence follows from the contributions — a failure-mode
finding has no self-owned module to ablate, and a distributional claim cannot be carried by a
single trace. Record every absent family under a literal `## Absent families` heading, one
bullet per family, shaped `- <family>: <reason>`:

```markdown
## Absent families

- ablation: the contribution is a failure-mode finding with no self-owned module to remove
- case_study: the claim is distributional, so no single trace can carry it
```

`skill-check-design` fails when a family is absent from `expected_effects.json` and this
section has no reason for it. The gate checks one thing only: that a reason was written for
that family — a bare `- ablation:`, or prose without the `<family>:` label, leaves it unwritten.
It does not grade the reason. `- ablation: n/a` clears the gate and is still a failed design:
whether a reason follows from the contributions is judged by this Skill when writing it, and
re-judged by `autodesign-integrity-auditor`, which reads the reason text verbatim. Write the
argument that actually holds, and do not invent a hollow experiment to fill a family.

## `expected_effects.json`

Written at design time; every value is a hypothesis, never an observation.

```json
{
  "schema_version": "1.0",
  "value_status": "SIMULATED_TARGET",
  "generated_by": "autodesign-experiment-design",
  "entries": [
    {
      "entry_id": "E1-ours-tb10-pass1",
      "experiment_id": "E1",
      "family": "main",
      "evidence_class": "CLAIM_BEARING",
      "claim_ids": ["C3"],
      "variant_id": "ours-32b",
      "benchmark_task_id": "terminal-bench-1.0",
      "metric": "pass@1",
      "simulated_target": 29.1,
      "acceptable_range": [26.0, 32.0],
      "target_basis": "handoff_reported",
      "threshold_reference_variant": "qwen2.5-coder-32b-instruct",
      "decision_threshold": ">= reference + 2.0",
      "on_miss": "iteration"
    }
  ]
}
```

Field rules:

- `value_status` is always `SIMULATED_TARGET` at design time and stays on the file as a whole.
- One entry represents one decision effect anchored to the target variant's aggregate-result key: experiment ID, variant ID, benchmark task ID, and metric. Seeds belong to the execution schedule and are aggregated before comparison.
- A relative effect names `threshold_reference_variant`; its reference aggregate uses the same experiment, task, and metric. Both target and reference aggregates must be planned. The reference row does not need its own expected-effect entry unless it independently carries a scientific decision.
- Do not create entries merely because an absolute baseline, control, or method score is displayed in a paper table. In particular, do not invent `>= 0` thresholds for reference-only rows.
- `target_basis` is exactly `handoff_reported`, `published_baseline`, or `design_estimate`. A `design_estimate` must be labelled as such in `experiment_design.md`.
- `decision_threshold` is literal and evaluable against observed numbers. Relative thresholds name `threshold_reference_variant`.
- `on_miss` is exactly `iteration`, `tuning`, or `stop`.
- The file contains design-time facts only. `$autodesign-experiment-run` reads it but never adds observed values or threshold outcomes to it.
- For a `case_study` entry, use `required_categories` with integer counts in place of a numeric `simulated_target`.
- For an `analysis` entry whose prediction is a shape rather than a level, use `expected_shape` with one of `monotonic_increasing`, `monotonic_decreasing`, `saturating`, `non_monotonic`, or `flat`, and keep `decision_threshold` literal.

`expected_effects.json` and the decision-effect inventory in `experiment_design.md` must agree one-for-one. Aggregate results and paper result cells are a broader set and are not duplicated into the target file. A simulated target may appear only in the explicitly marked AutoWriting draft form above; it never enters `reports/`, an observed result, a contribution verdict, or a submission-ready table or figure.
