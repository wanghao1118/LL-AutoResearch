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
3. Assign every experiment exactly one evidence class: `CLAIM_BEARING`, `MECHANISM_PILOT`, or `ENGINEERING_SMOKE`. Only `CLAIM_BEARING` experiments can support, mix, or refute an original contribution.
4. Design contribution-specific main, ablation, case, and interesting or boundary evidence. These roles are necessary but do not prove semantic coverage.
5. Give each experiment a direct observable, a falsifier, controlled axes, variants, tasks, metrics, splits, seeds, evidence class, benchmark provenance, and decision rule.
6. Keep every named benchmark, split, metric, and protocol lock exact in claim-bearing experiments. A surrogate may be used only as a distinctly named pilot or smoke and may not reuse an official benchmark identifier or satisfy claim coverage.
7. Select baselines independently. Cover closest work, strongest applicable system, and simple control; require every selected baseline to execute in a main claim-bearing experiment under a source-backed fairness plan. Preserve baseline-specific scaffolds or protocols when equalizing them would change the compared system.
8. For data-based routes, predefine each variant's manifest, sampling policy, required composition axes, and minimum diversity or quality observables. Include applicable domain, scenario, source, teacher, scaffold, turn, token, label, or difficulty distributions. A data-budget or leave-one-group-out comparison must keep every non-target axis fixed.
9. Use at least two teacher levels for teacher-quality claims, at least three data levels for budget claims, matched seen and unseen evaluation for generalization, error-to-recovery metrics for recovery, same-data mask on and off for partial masking, and error-present and error-absent strata for error conditioning.
10. Plan tables and figures by exact experiment IDs, fields, output paths, and decision use. Predefine case-selection rules and the required number or category of outputs before observing results.
11. Order experiments by information gain and cost. Put cheap kill tests before expensive confirmation.
12. Label one-seed and post-hoc findings exploratory, keep the corresponding original contribution unresolved when confirmation is missing, and specify the additional runs needed.

## Output

Write `evidence_plan.md` with a claim ledger, Idea-consistency audit, baseline decision, experiment cards, execution order, expected cells, data and protocol preflight requirements, reporting plan, and coverage audit. Do not predict final numeric values.

Update `AUTODESIGN_STATE.md` to `EVIDENCE_PLAN_READY` and set the next Skill to `autodesign-implementer`.
