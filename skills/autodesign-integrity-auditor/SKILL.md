---
name: autodesign-integrity-auditor
description: "Independently audit an AutoDesign run for claim-support alignment, experiment coverage, baseline fairness, execution completeness, metric recomputation, table and figure provenance, negative-result preservation, conclusion scope, and final pipeline readiness. Use before declaring a run complete or after substantive result changes."
---

# AutoDesign Integrity Auditor

Audit raw artifacts independently. Say PASS when the run is correct; do not invent issues to satisfy the review.

## Inputs

Read original input, method route, R0 record when required, evidence plan, implementation notes, execution record, raw results, result summary, diagnosis, `result_route.md`, any `result_tuning.json` and `next_round.md`, tables, figures, and `references/audit-contract.md`.

## Audit

1. Confirm every final claim is an unchanged or explicitly narrowed original claim.
2. Trace each claim to experiments, variants, tasks, metrics, seeds, falsifier, table, and figure.
3. Confirm selected baselines actually ran in main experiments under their fairness plan.
4. Confirm implementation matches the accepted method and protocol decisions.
5. Confirm current smoke, experiment, and aggregate commands exited zero in order.
6. Recompute result counts and aggregate values from raw records.
7. Confirm every displayed table cell and figure point comes from observed aggregates.
8. Confirm negative, mixed, failed-slice, and exploratory findings remain visible and correctly scoped.
9. Confirm the diagnosis route and next action follow literal thresholds.
10. Confirm every iteration or execution-required tuning action was implemented, executed, ingested, and rediagnosed, or was explicitly closed by its recorded stop threshold.
11. Confirm tuning kept original contributions and claims unchanged, preserved all observed failed slices and ablations, and did not present an expected delta as an observation.
12. List only concrete reachable defects. If none remain, state PASS.

## Output

Write `integrity_audit.md` with a literal `Verdict: PASS` or `Verdict: FAIL`. A failure lists file, field or line, observed contradiction, scientific consequence, and required correction.

An open iteration or execution-required tuning route is a literal FAIL. On PASS, update `AUTODESIGN_STATE.md` through `INTEGRITY_AUDIT_PASS` to `COMPLETE`. On FAIL, keep the last accepted state and route to the Skill that owns the defect.
