---
name: autodesign-integrity-auditor
description: "Independently audit an AutoDesign run for claim-support alignment, experiment coverage, baseline fairness, execution completeness, metric recomputation, table and figure provenance, negative-result preservation, conclusion scope, and final pipeline readiness. Use before declaring a run complete or after substantive result changes."
---

# AutoDesign Integrity Auditor

Audit raw artifacts independently. Say PASS when the run is correct; do not invent issues to satisfy the review.

## Inputs

Read original input, method route, R0 record when required, evidence plan, implementation notes, execution record, raw results, result summary, diagnosis, `result_route.md`, any `result_tuning.json` and `next_round.md`, tables, figures, and `references/audit-contract.md`.

## Audit

1. Confirm every final claim preserves the original contribution; result wording may describe observed regional behavior but may not rewrite the claim.
2. Trace each claim to eligible claim-bearing experiments, variants, tasks, benchmark provenance, metrics, seeds, falsifier, table, and figure.
3. Confirm pilots and smokes are visibly separated and never substitute for missing claim-bearing evidence.
4. Confirm selected baselines actually ran in main experiments under their source-backed fairness plan.
5. Confirm implementation matches the accepted Idea semantics, scientific locks, method, evidence classes, and protocol decisions.
6. Confirm current preflight, smoke, experiment, aggregate, and collect commands exited zero in order and their accepted inputs remain current.
7. Recompute result counts and aggregate values from raw records; reject missing or unexpected cells and schedule drift.
8. Confirm every displayed table cell and figure point comes from observed aggregates and every declared case or report category was actually produced.
9. Confirm negative, mixed, failed-slice, ablation, and exploratory findings remain visible and correctly scoped.
10. Confirm the diagnosis route and next action follow literal thresholds and upstream defects were not interpreted as method behavior.
11. Confirm every iteration or execution-required tuning action was implemented, executed, ingested, and rediagnosed, or was explicitly closed by its recorded stop threshold.
12. Confirm tuning kept original contributions and claims unchanged, used comparable budgets and seed sets, preserved all observed failed slices and ablations, and did not present an expected delta as an observation.
13. Treat a changed scientific lock, claim-bearing surrogate, unconsumed required data transformation, planned-composition failure, unexpected result cell, stale diagnosis or audit, contradictory baseline status, or missing declared report category as a literal FAIL.
14. List only concrete reachable defects. If none remain, state PASS.

## Output

Write `integrity_audit.md` with a literal `Verdict: PASS` or `Verdict: FAIL`. A failure lists file, field or line, observed contradiction, scientific consequence, and required correction.

An open iteration or execution-required tuning route is a literal FAIL. On PASS, update `AUTODESIGN_STATE.md` through `INTEGRITY_AUDIT_PASS` to `COMPLETE`. On FAIL, keep the last accepted state and route to the Skill that owns the defect.
