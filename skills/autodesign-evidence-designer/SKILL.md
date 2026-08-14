---
name: autodesign-evidence-designer
description: "Design, review, or repair a contribution-complete AutoDesign experiment portfolio. Use after method routing to map original claims and mechanisms to main experiments, baselines, ablations, case studies, boundary analyses, metrics, splits, seeds, tables, figures, falsifiers, and low-cost gates without reducing evidence to labels."
---

# AutoDesign Evidence Designer

Build a paper evidence package that can falsify every original contribution.

## Inputs

Read `input_brief.md`, accepted `method_route.md`, any executed `r0_record.json`, and `AUTODESIGN_STATE.md`. Stop if a required R0 has not passed.

Read `references/evidence-contract.md` before finalizing.

## Design evidence

1. Copy every original claim verbatim into a claim ledger.
2. Derive the concrete test axes each claim entails, such as main effect, recovery, partial masking, teacher quality, data budget, unseen generalization, latency, or robustness.
3. Design contribution-specific main, ablation, case, and interesting or boundary evidence. These roles are necessary but do not prove semantic coverage.
4. Give each experiment a direct observable, a falsifier, controlled axes, variants, tasks, metrics, splits, seeds, and decision rule.
5. Select baselines independently. Cover closest work, strongest applicable system, and simple control; require every selected baseline to execute in a main experiment under a fairness plan.
6. Use at least two teacher levels for teacher-quality claims, at least three data levels for budget claims, matched seen and unseen evaluation for generalization, error-to-recovery metrics for recovery, same-data mask on and off for partial masking, and error-present and error-absent strata for error conditioning.
7. Plan tables and figures by exact experiment IDs, fields, output paths, and decision use.
8. Order experiments by information gain and cost. Put cheap kill tests before expensive confirmation.
9. Narrow one-seed and exploratory claims explicitly; specify replication needed for confirmation.

## Output

Write `evidence_plan.md` with a claim ledger, baseline decision, experiment cards, execution order, expected cells, reporting plan, and coverage audit. Do not predict final numeric values.

Update `AUTODESIGN_STATE.md` to `EVIDENCE_PLAN_READY` and set the next Skill to `autodesign-implementer`.
