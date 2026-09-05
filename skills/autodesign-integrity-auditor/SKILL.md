---
name: autodesign-integrity-auditor
description: "Independently audit an AutoDesign run for claim-support alignment, experiment coverage across main, ablation, case-study, and analysis families, baseline fairness, simulated-target integrity, execution completeness, metric recomputation, table and figure provenance, negative-result preservation, conclusion scope, and final pipeline readiness. Use before declaring a run complete or after substantive result changes."
---

# AutoDesign Integrity Auditor

Audit raw artifacts independently. Say PASS when the run is correct; do not invent issues to satisfy the review.

## Inputs

Read the original handoff and `input_brief.md`, `experiment_design.md`, `expected_effects.json`, `r0_record.json` when required, `implementation_notes.md`, `execution_record.json`, raw results, `result_summary.json`, `effect_comparison.md`, `result_diagnosis.md`, `result_route.md`, any `result_tuning.json`, `next_round.md`, and AutoWriting draft that is present, all tables and figures, and `references/audit-contract.md`.

## Audit

1. Confirm every final claim preserves the original contribution from the AutoSearch handoff; result wording may describe observed regional behavior but may not rewrite the claim.
2. Trace each claim to eligible claim-bearing experiments, families, variants, tasks, benchmark provenance, metrics, seeds, falsifier, table, and figure.
3. Confirm all four experiment families are present, or that an absent family is explicitly justified against the contributions in `experiment_design.md`. A contribution asserting a mechanism with no ablation attribution, or a behavioral claim with no case study, is a coverage defect.
4. Confirm every case study followed its pre-result selection rule, produced the declared category counts including failure categories, and shows no evidence of outcome-dependent selection.
5. Confirm pilots and smokes are visibly separated and never substitute for missing claim-bearing evidence.
6. Confirm selected baselines actually ran in main experiments under their source-backed fairness plan.
7. Confirm every autonomous choice has an outcome-impact classification and every non-benchmark high-impact freedom was resolved by an explicit user decision or an executed R0 comparison of at least two candidate instantiations before full implementation. Confirm the benchmark decision instead used contribution-derived, source-backed, pre-result criteria; any adaptation/new construction passed its measurement-validity R0 and was not chosen on proposed-method performance.
8. Confirm implementation matches the accepted Idea semantics, scientific locks, route, families, evidence classes, and protocol decisions.
9. Confirm current preflight, smoke, experiment, aggregate, and collect commands exited zero in order and their accepted inputs remain current.
10. Recompute result counts and aggregate values from raw records; reject missing or unexpected cells and schedule drift.
11. Audit simulated-target integrity. `expected_effects.json` remains the unchanged design-time file and every entry keeps `value_status: SIMULATED_TARGET`; `effect_comparison.md` covers every entry and retains every `MISSED` and `NOT_EVALUABLE` row. A simulated target may appear only in a document visibly marked `DRAFT — SIMULATED TARGETS, NO OBSERVED RESULTS`, with `SIMULATED_TARGET` in the same cell or caption. It never appears in `reports/`, an observed result, a claim verdict, or a submission-ready table or figure.
12. Confirm the paper table plan survived execution: the primary table compares selected baselines and the proposed method on the locked benchmark, split, and metric scope using absolute observed results; ablation tables keep the full method beside the declared one-axis variants; focused analysis tables answer one named local question. Multi-level headers, row groups, model/scaffold columns, paired rows, and optional deltas are presentation choices, not required templates. A delta may supplement but never replace the absolute values needed to interpret the comparison.
13. Confirm every submission-ready table cell and figure point comes from observed aggregates, every result placeholder has been replaced, unavailable values are not rendered as zero, and every declared case or report category was actually produced.
14. Confirm negative, mixed, failed-slice, ablation, and exploratory findings remain visible and correctly scoped.
15. Confirm the diagnosis route and next action follow literal thresholds, that upstream defects were not interpreted as method behavior, and that no verdict rests on proximity to a design-time target.
16. Confirm every iteration or execution-required tuning action was implemented, executed, ingested, recompared, and rediagnosed, or was explicitly closed by its recorded stop threshold.
17. Confirm tuning kept original contributions and claims unchanged, used comparable budgets and seed sets, preserved all observed failed slices and ablations, and did not present an expected delta as an observation.
18. Treat as a literal FAIL: an unresolved high-impact freedom; a single-candidate default for a non-benchmark high-impact freedom; a benchmark selected without contribution coverage and source evidence or after inspecting proposed-method performance; an adapted/new benchmark without its required validity R0; a changed scientific lock; a claim-bearing surrogate benchmark; an unconsumed required data transformation; a planned-composition failure; an unexpected result cell; a post-hoc edited simulated target; a target presented as an observation; a primary table that omits the proposed method, selected baselines, or locked result scope; a delta-only substitute for required absolute results; a dropped `MISSED` comparison row; an outcome-dependent case selection; a stale diagnosis or audit; a contradictory baseline status; or a missing declared report category.
19. List only concrete reachable defects. If none remain, state PASS.

## Output

Write `integrity_audit.md` with a literal `Verdict: PASS` or `Verdict: FAIL`. A failure lists file, field or line, observed contradiction, scientific consequence, and required correction.

An open iteration or execution-required tuning route is a literal FAIL. On PASS, update `AUTODESIGN_STATE.md` through `INTEGRITY_AUDIT_PASS` to `COMPLETE`. On FAIL, keep the last accepted state and route to the Skill that owns the defect.
