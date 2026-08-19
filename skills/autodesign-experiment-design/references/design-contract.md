# Experiment Design Contract

`experiment_design.md` is the single design artifact. `expected_effects.json` is its machine-readable target companion. Both are written by `$autodesign-experiment-design` and read by `$autodesign-experiment-run`.

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

## 8. Expected cells

Define the Cartesian cells from experiment × variant × task × seed, each with family, evidence class, and benchmark provenance. Theoretical or missing cells are never observations. A later round requires an explicit design and schedule revision; it may not append cells silently.

## 9. Preflight requirements

For every scientific lock and controlled axis: the exact observable check, its failure condition, and the changed next action. For data-based routes require planned-versus-materialized sample counts and distributions before expensive execution. When filtering or decontamination is required, trace the production path from source data through the materialized artifact to the exact training input.

## 10. Reporting plan

Each table and figure declares experiment IDs, fields or axes, output path under `reports/`, and the decision it supports.

## 11. Coverage audit

End with literal `PASS` only when:

- every contribution and derived axis has a `CLAIM_BEARING` falsifier;
- all four families are populated, or an absent family is explicitly justified against the contributions;
- every locked benchmark has valid provenance;
- every selected baseline has a fairness plan and appears in a main experiment;
- every case study has a pre-result selection rule with failure categories;
- every decision-relevant preflight has a failure action;
- every expected cell has a matching entry in `expected_effects.json`.

Otherwise list blockers and keep the state before `EXPERIMENT_DESIGN_READY`.

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
      "on_miss": "iteration",
      "observed_value": null,
      "observed_status": "NOT_EXECUTED"
    }
  ]
}
```

Field rules:

- `value_status` is always `SIMULATED_TARGET` at design time and stays on the file as a whole.
- `target_basis` is exactly `handoff_reported`, `published_baseline`, or `design_estimate`. A `design_estimate` must be labelled as such in `experiment_design.md`.
- `decision_threshold` is literal and evaluable against observed numbers. Relative thresholds name `threshold_reference_variant`.
- `on_miss` is exactly `iteration`, `tuning`, or `stop`.
- `observed_value` stays `null` and `observed_status` stays `NOT_EXECUTED` until `$autodesign-experiment-run` fills them from real results.
- For a `case_study` entry, use `required_categories` with integer counts in place of a numeric `simulated_target`.
- For an `analysis` entry whose prediction is a shape rather than a level, use `expected_shape` with one of `monotonic_increasing`, `monotonic_decreasing`, `saturating`, `non_monotonic`, or `flat`, and keep `decision_threshold` literal.

`expected_effects.json` and the expected cells in `experiment_design.md` must agree cell-for-cell. A simulated target may never be copied into `reports/`, a table, a figure, or a contribution verdict.
