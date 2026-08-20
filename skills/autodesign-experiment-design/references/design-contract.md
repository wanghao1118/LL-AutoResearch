# Experiment Design Contract

`experiment_design.md` is the design and AutoWriting-handoff artifact. `expected_effects.json` is its read-only design-target companion. `$autodesign-experiment-run` reads both and never writes observations into the target file.

## Required design records

Use stable IDs and record these sections in `experiment_design.md`:

1. **Claim ledger**: `claim_id`, literal contribution, mechanism, required axes, claim-bearing experiment IDs, falsifier, and status boundary. Every contribution and derived axis maps to real `CLAIM_BEARING` evidence; pilots/smokes remain visible but do not satisfy coverage.
2. **Idea semantics**: central term, operational meaning, constraints, non-constraints, observable implication, disallowed reinterpretation, and unresolved uncertainty.
3. **Locks and choices**: `choice_id`, choice, `high|low` outcome impact, effect on interpretation, candidates, fixed controls, resolution source, and status. Follow with a role inventory containing role, identity/protocol, purpose, outcome impact, and closure source.
4. **Route inventory**: `route_id`, family, intervention, minimal probe, falsifier, contribution/benchmark fit, cost/data, source evidence, and status. Name the selected configuration and rejected alternatives.
5. **Baseline inventory**: `baseline_id`, source/revision, selected/rejected, and separate role records for `causal_reference` and `contextual_baseline`. For each claimed role state the mapped claim/experiment, independence, matched or intentionally unmatched axes, defining scaffold/protocol, fairness plan, cost, and evidence gap. A dual-role baseline has two explicit role records.
6. **R0 gate**: `required`, covered uncertainty/choice IDs, candidate IDs, changed axis, fixed outcome-impacting axes, fit/materialization/selection ID pools, literal selection and kill rules, next action, and total cost. Add an R0 execution-cell inventory with `cell_id`, arm/reference role, data IDs, budget, command intent, output, metric, and cost. Every cell cited by a rule must occur here.

The selected route records each honored lock. A reduced route stays `MECHANISM_PILOT` or `ENGINEERING_SMOKE` and leaves the affected claim incomplete. A baseline selected for either role appears in a main experiment; when an external system cannot be run comparably, record the unresolved contextual evidence gap instead of silently replacing it with an internal variant.

## Experiment and result identities

Each experiment card records:

- `experiment_id`; family `main|ablation|case_study|analysis`; evidence class `CLAIM_BEARING|MECHANISM_PILOT|ENGINEERING_SMOKE`;
- mapped claims and exact subset; hypothesis; variants/baselines; benchmark identity, provenance/revision, tasks, splits, metrics, and protocol locks;
- seeds; changed axis; fixed axes; data manifest/composition; entrypoint intent; outputs; priority/cost;
- for `CLAIM_BEARING`, one primary `research_question`, `intervention`, `matched_reference`, `primary_metric`, `literal_falsifier`, and `claim_collapse`;
- for applicable failure/recovery work, `taxonomy_id`, frozen categories and sampling rule. The related case-study and quantitative-analysis cards use the same `taxonomy_id`; categories include recovered, unrecovered, and side effect.

Family additions: `main` names uncertainty reporting; `ablation` names the single removed/replaced component; `case_study` names eligible pool, pre-result sampler/seed, category counts, shortfall rule, and display fields; `analysis` names the tested axis, levels, expected direction/shape, and boundary.

Keep these identities separate:

- **execution cell**: experiment × variant × task × seed, with evidence class, provenance, budget, command/output, and metrics;
- **aggregate result**: experiment × variant × task × metric after planned seeds, containing absolute observed value and uncertainty;
- **paper result cell**: table/figure location displaying an aggregate or defined derived summary;
- **decision effect**: claim-relevant comparison, drop, direction, shape, or category requirement with target, literal threshold, and miss route.

`experiment_schedule.json` expands ordinary execution cells per seed; `result_summary.json` contains produced aggregates; `expected_effects.json` contains decision effects only. Relative effects require both target and reference aggregates in the plan. Baseline/presentation rows still need execution, aggregate, and paper cells, but no fake threshold.

List planned execution cells, aggregate keys, paper cells, and decision effects separately in the design. A later round or changed R0 winner revises the design, table plan, schedule, affected result keys, and effect IDs explicitly; it never appends an incompatible cell under an old identity. Shared compute is allowed only when two paper roles point to the same immutable execution/result key.

## Paper and reporting records

For each table or figure record `table_id`/`figure_id`, paper question, mapped claims/experiments, row and column semantics, aggregate-result key behind every absolute position, optional derived-effect ID, uncertainty, average definition, missing-cell policy, caption claim, and `reports/` output path.

The primary table contains the proposed method plus both closed baseline roles over the locked main scope and shows absolute results. Ablations show the full method and one-axis variants. Focused analyses contain only cells needed for their question; continuous curves/distributions/trajectories use figures. Averages state macro/weighted semantics and combine only commensurate cells; unavailable is not zero.

Preflight records each lock/controlled axis, observable check, failure condition, and changed next action. Reporting may refine presentation, never the comparison set.

The reporting plan lists source experiment/aggregate/effect IDs, fields or axes, output paths, and the decision supported. Table shells must be complete enough for AutoWriting to draft structure without inventing a row, metric, or comparison.

## AutoWriting handoff and placeholders

End with `## AutoWriting handoff` and record:

- `handoff_status: ACCEPTED|PROVISIONAL_WAITING_FOR_R0`, safe/conditional sections, stable identities, and invalidation rules;
- complete shells using `{{RESULT:<experiment_id>::<variant_id>::<benchmark_task_id>::<metric>}}` for absolute aggregates and `{{EFFECT:<entry_id>}}` only for displayed derived effects;
- replacement sources: observed aggregates in `result_summary.json` and comparisons in `effect_comparison.md`.

Prefer placeholders. If numeric targets appear, label the document `DRAFT — SIMULATED TARGETS, NO OBSERVED RESULTS` and the same cell/caption `SIMULATED_TARGET`.

## Coverage audit

End with exactly one `Verdict: PASS|PROVISIONAL_WAITING_FOR_R0|FAIL`. The audit explicitly reports:

- lock and role closure; baseline role closure; unresolved high-impact choices;
- R0 changed/fixed axes and whether every rule-referenced cell is registered and costed;
- contribution/axis → `CLAIM_BEARING` mapping and every Claim Contract outcome;
- family coverage or contribution-grounded reasons under literal `## Absent families` bullets shaped `- <family>: <reason>`;
- benchmark provenance, taxonomy links when applicable, preflight failure actions, paper/result/effect mappings, and handoff maturity.

`skill-check-design` validates deterministic structure only. `PASS` requires no unresolved choice/gap; `PROVISIONAL_WAITING_FOR_R0` permits only registered unresolved R0 choices, not baseline, confounding, Claim Contract, taxonomy, or reference-cell gaps. A failed audit stays before design readiness.

Artifact set and ownership:

- `input_brief.md` preserves the literal handoff and its lock/choice/resource classification;
- `experiment_design.md` owns all scientific decisions, inventories, shells, and the handoff;
- `expected_effects.json` owns design-time decision targets only and remains byte-stable during result ingestion;
- `r0_plan.md`, when required, owns the gate cells/rules; the observed `r0_record.json` is produced by execution and triggers a reissued design.

## `expected_effects.json`

Every value is a design hypothesis:

```json
{
  "schema_version": "1.0",
  "value_status": "SIMULATED_TARGET",
  "generated_by": "autodesign-experiment-design",
  "entries": [
    {
      "entry_id": "E1-ours-task-metric",
      "experiment_id": "E1",
      "family": "main",
      "evidence_class": "CLAIM_BEARING",
      "claim_ids": ["C1"],
      "variant_id": "ours",
      "benchmark_task_id": "task-id",
      "metric": "primary_metric",
      "simulated_target": 29.1,
      "acceptable_range": [26.0, 32.0],
      "target_basis": "design_estimate",
      "threshold_reference_variant": "causal-reference",
      "decision_threshold": ">= reference + 2.0",
      "on_miss": "iteration"
    }
  ]
}
```

Field rules:

- `target_basis` is `handoff_reported|published_baseline|design_estimate`; `on_miss` is `iteration|tuning|stop`; relative thresholds name `threshold_reference_variant`.
- `decision_threshold` is literal and evaluable. Numeric entries provide a numeric `simulated_target`; `acceptable_range`, when present, is an ordered numeric pair. A design estimate is labelled as such in the design prose.
- One entry anchors one decision effect to experiment, target variant, task, and metric after seed aggregation. Do not create entries for seeds or display-only references.
- A `case_study` entry uses positive-integer `required_categories` instead of `simulated_target`; an `analysis` shape uses `expected_shape: monotonic_increasing|monotonic_decreasing|saturating|non_monotonic|flat`.
- Entries and the decision-effect inventory agree one-for-one. Observations, threshold outcomes, and submission-ready prose never enter this file.
