# Experiment Design Contract

`experiment_design.md` is the design and AutoWriting-handoff artifact. `expected_effects.json` is its read-only design-target companion. `run` reads both and never writes observations into the target file.

## Required design records

Use stable IDs and record these sections in `experiment_design.md`:

1. **Claim ledger**: `claim_id`, literal contribution, mechanism, required axes, claim-bearing experiment IDs, falsifier, and status boundary. Every contribution and derived axis maps to real `CLAIM_BEARING` evidence; pilots/smokes remain visible but do not satisfy coverage.
2. **Idea semantics**: central term, operational meaning, constraints, non-constraints, observable implication, disallowed reinterpretation, and unresolved uncertainty.
3. **Locks and choices**: `choice_id`, choice, `high|low` outcome impact, effect on interpretation, candidates, fixed controls, resolution source, and status. Follow with a role inventory containing role, identity/protocol, purpose, outcome impact, and closure source.
4. **Benchmark decision**: claim-to-benchmark requirements matrix; candidate inventory with source evidence, covered/missing requirements, access, protocol, metrics, baselines, adaptation cost, and provenance risk; selected route `direct_reuse|base_benchmark_adaptation|new_benchmark_construction`; selected and rejected identities; contribution coverage; pre-result selection rationale; and frozen protocol. When adapting or constructing, include the benchmark design, R0 validity gate, versioned identity, and claim-bearing validation cards required by the worker.
5. **Route inventory**: `route_id`, family, intervention, minimal probe, falsifier, contribution/benchmark fit, cost/data, source evidence, and status. Name the selected configuration and rejected alternatives.
6. **Baseline inventory**: `baseline_id`, source/revision, selected/rejected, and separate role records for `causal_reference` and `contextual_baseline`. For each claimed role state the mapped claim/experiment, independence, matched or intentionally unmatched axes, defining scaffold/protocol, fairness plan, cost, and evidence gap. A dual-role baseline has two explicit role records.
7. **R0 gate**: `required`, covered uncertainty/choice or benchmark-validity IDs, candidate IDs, changed axis, fixed outcome-impacting axes, fit/materialization/selection ID pools, literal selection and kill rules, next action, and total cost. Add an R0 execution-cell inventory with `cell_id`, arm/reference role, data IDs, budget, command intent, output, metric, and cost. Every cell cited by a rule must occur here.

The selected route records each honored lock. A reduced route stays `MECHANISM_PILOT` or `ENGINEERING_SMOKE` and leaves the affected claim incomplete. A baseline selected for either role appears in a main experiment; when an external system cannot be run comparably, record the unresolved contextual evidence gap instead of silently replacing it with an internal variant.

## Experiment and result identities

Each experiment card records:

- `experiment_id`; family `main|ablation|case_study|analysis`; evidence class `CLAIM_BEARING|MECHANISM_PILOT|ENGINEERING_SMOKE`;
- mapped claims and exact subset; hypothesis; variants/baselines; benchmark identity, provenance/revision, tasks, splits, metrics, and protocol locks;
- seeds; changed axis; fixed axes; data manifest/composition; entrypoint intent; outputs; priority/cost;
- for `CLAIM_BEARING`, one primary `research_question`, `intervention`, `matched_reference`, `primary_metric`, `literal_falsifier`, and `claim_collapse`;
- for applicable failure/recovery work, `taxonomy_id`, frozen categories and sampling rule. The related case-study and quantitative-analysis cards use the same `taxonomy_id`; categories include recovered, unrecovered, and side effect.

Family additions: `main` names uncertainty reporting; `ablation` names the single removed/replaced component; `case_study` names eligible pool, pre-result sampler/seed, category counts, shortfall rule, display fields, a paper-facing `case_figure_plan`, and a concrete `case_figure_draft`; `analysis` names the tested axis, levels, expected direction/shape, and boundary.

The `case_figure_plan` describes the figure before results exist: `figure_id`, paper question, taxonomy/category, panel cases and match key when comparison is claimed, ordered visual stages, visible evidence fields, annotation meanings, source artifact paths, compression rule, caption claim, size/content budget, and `reports/` output path. This record applies only to the Case Study figure, not the method-overview figure or a main-results plot.

Use a fixed paper-placement budget unless the handoff names another venue format: a full-width `figure*` spanning both columns of a two-column arXiv-style paper, width `0.96–1.00\textwidth`, artwork height about `0.38–0.42\textheight`, and total figure height including caption no more than `0.48\textheight`. For two cases, use two side-by-side transcript panels of about `0.47–0.48\textwidth` each with a `0.02–0.04\textwidth` gutter. This two-panel layout may show two preregistered categories without implying a matched causal comparison; a baseline/method contrast still requires its registered match key. At final placement, keep body text at least 7.5 pt and panel labels about 8.5–9 pt.

The same design must include `### Case-study figure draft — <figure_id>` with an actual transcript-style Markdown/ASCII typesetting draft, provisional labels, separator placement, callout locations, source-naming placeholders, and a caption draft. Do not return only prose such as “show the trajectory.” The visual unit is a readable trace excerpt, not an abstract stage or pipeline node. When two cases are planned, draft them as two columns:

```text
(a) {{CASE:CS1::case_a::short_label}}       (b) {{CASE:CS1::case_b::short_label}}
Prompt: {{CASE:CS1::case_a::task_excerpt}}  Prompt: {{CASE:CS1::case_b::task_excerpt}}
- - - - - - - - - - - - - - - - - - -    - - - - - - - - - - - - - - - - - - -
Agent: {{CASE:CS1::case_a::action_1}}        Agent: {{CASE:CS1::case_b::action_1}}
[Tool Call] {{CASE:CS1::case_a::call_1}}     [Tool Call] {{CASE:CS1::case_b::call_1}}
- - - - - - - - - - - - - - - - - - -    - - - - - - - - - - - - - - - - - - -
Tool: {{CASE:CS1::case_a::response_1}}       Tool: {{CASE:CS1::case_b::response_1}}
Agent: {{CASE:CS1::case_a::action_2}}        Agent: {{CASE:CS1::case_b::action_2}}
[Comment] {{CASE:CS1::case_a::decisive}}     [Comment] {{CASE:CS1::case_b::decisive}}
- - - - - - - - - - - - - - - - - - -    - - - - - - - - - - - - - - - - - - -
[Outcome] {{CASE:CS1::case_a::outcome}}      [Outcome] {{CASE:CS1::case_b::outcome}}

Caption draft: <the two behavioral cases illustrated without population-level generalization>
```

Use the registered case and variant IDs instead of the example IDs. Budget each panel for a short task excerpt, three to five visible interaction turns, one decisive taxonomy-linked comment, and one final outcome. Keep each excerpt to the shortest evidence-complete span; compress only non-decision turns and mark them as `[N non-decision turns omitted]`. Omit tool turns when the environment has no tools. Use black or neutral body text for the trace, one restrained accent for tool calls and decisive failure/recovery, and link/source color only for retrieved evidence when present. Keep labels inline; avoid rounded containers, arrows between stages, dashboard furniture, decorative badges, oversized internal titles, and a legend that merely repeats the labels. Put full source paths, long provenance, design-status notices, and secondary taxonomy notes in the design record, caption, or supplement rather than the figure body. Show exact observed excerpts or faithful summaries of observable events; never reconstruct hidden reasoning, dialogue, tool output, or outcomes. Every highlighted moment maps to the registered taxonomy or another named analysis field so the figure explains the quantitative evidence instead of becoming a standalone anecdote. At design time, keep unresolved trace content as visibly typed source placeholders; do not render a polished placeholder infographic that could be mistaken for an observed case.

Keep these identities separate:

- **execution cell**: experiment × variant × task × seed, with evidence class, provenance, budget, command/output, and metrics;
- **aggregate result**: experiment × variant × task × metric after planned seeds, containing absolute observed value and uncertainty;
- **paper result cell**: table/figure location displaying an aggregate or defined derived summary;
- **decision effect**: claim-relevant comparison, drop, direction, shape, or category requirement with target, literal threshold, and miss route.

`experiment_schedule.json` expands ordinary execution cells per seed; `result_summary.json` contains produced aggregates; `expected_effects.json` contains decision effects only. Relative effects require both target and reference aggregates in the plan. Baseline/presentation rows still need execution, aggregate, and paper cells, but no fake threshold.

List planned execution cells, aggregate keys, paper cells, and decision effects separately in the design. A later round or changed R0 winner revises the design, table plan, schedule, affected result keys, and effect IDs explicitly; it never appends an incompatible cell under an old identity. Shared compute is allowed only when two paper roles point to the same immutable execution/result key.

## Paper and reporting records

For each table or figure record `table_id`/`figure_id`, paper question, mapped claims/experiments, row and column semantics, aggregate-result key behind every absolute position, optional derived-effect ID, uncertainty, average definition, missing-cell policy, caption claim, and `reports/` output path.

The primary table contains the proposed method plus both closed baseline roles over the accepted main benchmark scope and shows absolute results. Ablations show the full method and one-axis variants. Focused analyses contain only cells needed for their question; continuous curves/distributions/trajectories use figures. Averages state macro/weighted semantics and combine only commensurate cells; unavailable is not zero.

At design time, every numeric paper position contains only its complete typed `{{RESULT:...}}` or `{{EFFECT:...}}` placeholder. Do not put `R ± CI`, `R+CI`, `C ± CI`, `Rate ± CI`, `Δ ± CI`, `mean ± std`, a bare `CI`, or another invented value/uncertainty shorthand into table cells. The reporting plan may require uncertainty, but its final display is chosen from observed aggregates after execution rather than simulated in the shell.

Preflight records each lock/controlled axis, observable check, failure condition, and changed next action. Reporting may refine presentation, never the comparison set.

The reporting plan lists source experiment/aggregate/effect IDs, fields or axes, output paths, and the decision supported. Table shells must be complete enough for AutoWriting to draft structure without inventing a row, metric, or comparison.

## AutoWriting handoff and placeholders

End with `## AutoWriting handoff` and record:

- `handoff_status: ACCEPTED|PROVISIONAL_WAITING_FOR_R0`, safe/conditional sections, stable identities, and invalidation rules;
- complete shells using `{{RESULT:<experiment_id>::<variant_id>::<benchmark_task_id>::<metric>}}` for absolute aggregates and `{{EFFECT:<entry_id>}}` only for displayed derived effects; these typed placeholders stand alone and are never decorated with `± CI`, `+CI`, `± std`, or other invented uncertainty text;
- replacement sources: observed aggregates in `result_summary.json` and comparisons in `effect_comparison.md`.

Prefer placeholders. If numeric targets appear, label the document `DRAFT — SIMULATED TARGETS, NO OBSERVED RESULTS` and the same cell/caption `SIMULATED_TARGET`.

## Coverage audit

End with exactly one `Verdict: PASS|PROVISIONAL_WAITING_FOR_R0|FAIL`. The audit explicitly reports:

- lock and role closure; benchmark requirement coverage and source-backed selection; baseline role closure; unresolved high-impact choices;
- for adapted/new benchmarks, construction identity, R0 measurement-validity outcome, and claim-bearing benchmark validation coverage;
- R0 changed/fixed axes and whether every rule-referenced cell is registered and costed;
- contribution/axis → `CLAIM_BEARING` mapping and every Claim Contract outcome;
- family coverage or contribution-grounded reasons under literal `## Absent families` bullets shaped `- <family>: <reason>`;
- benchmark provenance, taxonomy links when applicable, preflight failure actions, paper/result/effect mappings, and handoff maturity.

`check-design` validates deterministic structure only. `PASS` requires no unresolved choice/gap; `PROVISIONAL_WAITING_FOR_R0` permits only registered unresolved R0 choices, not baseline, confounding, Claim Contract, taxonomy, or reference-cell gaps. A failed audit stays before design readiness.

## Breakpoint-driven method revision proposal

`method_revision_proposal.md` is written only after `method_revision_request.md` shows that no admissible boundary-only repair remains or repeated attempts provide no new action, evidence, or measurable progress. It records:

- `Revision ID` and triggering request/breakpoint IDs;
- literal failure evidence and prior boundary-repair outcomes;
- original accepted method behavior and identity;
- exactly one smallest proposed method delta;
- preserved Motivation, Contribution, Benchmark, and unaffected method identities;
- changed identities, claim-meaning impact, and why the change remains within the original Idea rather than replacing it;
- affected experiment, effect, schedule, result, table, and figure IDs;
- falsifier, any newly required R0, expected cost, and rollback condition;
- boundary-repair history and progress evidence, `method_revision_limit`, approved method-revision count, and approval mode `WITHIN_LIMIT|LIMIT_REACHED`.

The proposal does not mutate the accepted design. `method_revision_decision.md` must repeat the exact `Revision ID` and one literal decision: `APPROVE_MINIMAL_METHOD_REVISION`, `APPROVE_EXCEPTION_METHOD_REVISION`, `REJECT_METHOD_REVISION`, or `ABANDON_IDEA`. At `LIMIT_REACHED`, another revision requires the exception decision and the user interface must expose `废弃当前 Idea`. A stale decision for another revision ID grants no authority.

Artifact set and ownership:

- `input_brief.md` preserves literal Motivation, Contribution, any optional Benchmark input, and the lock/choice/resource classification;
- `experiment_design.md` owns all scientific decisions, inventories, shells, and the handoff;
- `expected_effects.json` owns design-time decision targets only and remains byte-stable during result ingestion;
- `r0_plan.md`, when required, owns the gate cells/rules; the observed `r0_record.json` is produced by execution and triggers a reissued design.
- `method_revision_request.md` is produced by execution; `method_revision_proposal.md` is produced by design; `method_revision_decision.md` and `idea_abandonment.md` preserve the user's authority and terminal choice.

## `expected_effects.json`

Every value is a design hypothesis:

```json
{
  "schema_version": "1.0",
  "value_status": "SIMULATED_TARGET",
  "generated_by": "design",
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
