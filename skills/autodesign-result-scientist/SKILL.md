---
name: autodesign-result-scientist
description: "Diagnose, interpret, or iterate on completed AutoDesign results. Use after execution to distinguish preregistration and analyzer issues, implementation behavior, API transport failures, evaluator failures, missing evidence, mixed or negative scientific results, tuning opportunities, stopping decisions, and paper-ready reporting scope."
---

# AutoDesign Result Scientist

Interpret observed evidence without manufacturing support for a contribution.

## Entry gate

Read `input_brief.md`, `method_route.md`, `evidence_plan.md`, `implementation_notes.md`, preflight reports, `execution_record.json`, raw results, `result_summary.json`, and `references/diagnosis-contract.md`. Stop before scientific diagnosis unless current preflight, smoke, experiment, aggregate, and collect records pass, scheduled cells and metrics are complete, no unexpected cell is unresolved, and evidence identities match the accepted plan.

## Diagnose

1. Diagnose in this order: scientific-lock or provenance defect; data-preparation defect; implementation defect; API or transport defect; evaluator defect; method behavior. Do not interpret downstream behavior before upstream evidence eligibility passes.
2. Recompute aggregates from raw records. Preserve denominators, seeds, missing cells, and failed slices.
3. Diagnose every original contribution independently as `SUPPORTED`, `MIXED`, `NOT_SUPPORTED`, or `INCOMPLETE`. A required scientific-lock, provenance, data-preparation, or implementation defect forces `INCOMPLETE` and `iteration`; it cannot produce `NOT_SUPPORTED` or `stop`.
4. Cite exact experiments, variants, tasks, metrics, uncertainty, cases, and falsifiers.
5. Use only `CLAIM_BEARING` experiments for contribution verdicts. Report pilot and smoke observations separately as engineering or mechanism diagnostics.
6. Treat one-seed, post-hoc slices, and position-specific effects as exploratory and state the additional runs required for confirmation.
7. Select one route:
   - `iteration` when required evidence is incomplete;
   - `tuning` when evidence is complete but mixed or negative and a justified single-variable action remains;
   - `stop` when eligible claim-bearing evidence crosses a preregistered kill threshold or no diagnostic action remains;
   - `report` when contributions are adequately supported.
8. Always write `result_route.md` with the selected route, exact reason, owner Skill, changed variable or artifact, whether new execution is required, invalidated downstream artifacts, and literal continue and stop thresholds.
9. After selecting `iteration` or `tuning`, read `references/result_tuning_prompt.md`. Supply it with the current input brief, accepted method and evidence plan, execution record, raw results, deterministic summary, and current contribution diagnosis. Use its action schema to plan the next step.
10. For `iteration`, use the action plan to write `next_round.md` with the missing evidence, minimum experiment cells, fixed controls, command intent, expected observation, cost, and completion threshold. Write `result_tuning.json` only when the selected route is `tuning`.
11. Treat the action reference as a catalog, not as permission to weaken the pipeline invariants. Keep every original contribution and claim unchanged, retain every observed negative or mixed result, keep baseline and method budgets and seed sets comparable, and never convert an unexecuted expected delta into an observed result.
12. For every tuning action preserve input state → one primary action → expected diagnostic change → required execution → observed output state. Classify the action as `reporting_only`, `implementation_change`, `new_evidence`, or `execution_retry`, then write `next_round.md` when any action remains unexecuted.
13. Produce paper-ready tables and figures only from observed aggregates. Keep all claim-critical negative, mixed, and failed-slice results visible.

## Route handoff

- `iteration`: route the precise failure to the method router, evidence designer, implementer, or executor named in `result_route.md`; after execution and ingestion, run this Skill again.
- `tuning`: route `reporting_only` actions to the integrity auditor; route every action requiring code, data, configuration, or new observations through the named owner Skill, execution, ingestion, and a fresh diagnosis.
- `stop` or `report`: route to the integrity auditor with all negative and mixed evidence retained.

Do not send an open `iteration` or execution-required `tuning` route to the final audit.

## Output

Write `result_diagnosis.md` and `result_route.md`; write `result_tuning.json` only for tuning and `next_round.md` whenever another action or run is required. Write paper-ready artifacts under `reports/` only from observed evidence.

Update `AUTODESIGN_STATE.md` to `RESULT_DIAGNOSIS_READY` and set the next Skill to `run-autodesign`. The orchestrator must close or execute the recorded route before final audit.
