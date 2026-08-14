---
name: autodesign-result-scientist
description: "Diagnose, interpret, or iterate on completed AutoDesign results. Use after execution to distinguish preregistration and analyzer issues, implementation behavior, API transport failures, evaluator failures, missing evidence, mixed or negative scientific results, tuning opportunities, stopping decisions, and paper-ready reporting scope."
---

# AutoDesign Result Scientist

Interpret observed evidence without manufacturing support for a contribution.

## Entry gate

Read `input_brief.md`, `method_route.md`, `evidence_plan.md`, `execution_record.json`, raw results, `result_summary.json`, and `references/diagnosis-contract.md`. Stop before scientific diagnosis unless current preflight, smoke, experiment, aggregate, and collect records pass and scheduled cells and metrics are complete.

## Diagnose

1. Separate four layers: preregistration or analyzer, implementation or model behavior, API or transport, and evaluator.
2. Recompute aggregates from raw records. Preserve denominators, seeds, missing cells, and failed slices.
3. Diagnose every original contribution independently as `SUPPORTED`, `MIXED`, `NOT_SUPPORTED`, or `INCOMPLETE`.
4. Cite exact experiments, variants, tasks, metrics, uncertainty, cases, and falsifiers.
5. Treat one-seed, post-hoc slices, and position-specific effects as exploratory and state required replication.
6. Select one route:
   - `iteration` when required evidence is incomplete;
   - `tuning` when evidence is complete but mixed or negative and a justified single-variable action remains;
   - `stop` when a preregistered kill threshold is crossed or no diagnostic action remains;
   - `report` when contributions are adequately supported.
7. Always write `result_route.md` with the selected route, exact reason, owner Skill, changed variable or artifact, whether new execution is required, invalidated downstream artifacts, and literal continue and stop thresholds.
8. For `iteration`, write `next_round.md` with the missing evidence, minimum experiment cells, fixed controls, command intent, expected observation, cost, and completion threshold.
9. Only after selecting `tuning`, read `references/result_tuning_prompt.md`. Supply it with the current input brief, accepted method and evidence plan, execution record, raw results, deterministic summary, and current contribution diagnosis. Use its JSON schema to write `result_tuning.json`.
10. Treat the tuning reference as an action catalog, not as permission to weaken the pipeline invariants. Keep every original contribution and claim unchanged, retain every observed negative or mixed result, keep baseline and method budgets comparable, and never convert an unexecuted expected delta into an observed result.
11. For every tuning action preserve input state → one primary action → expected diagnostic change → required execution → observed output state. Classify the action as `reporting_only`, `implementation_change`, `new_evidence`, or `execution_retry`, then write `next_round.md` when any action remains unexecuted.
12. Produce paper-ready tables and figures only from observed aggregates. Keep negative and mixed results visible.
13. If execution mode is `provenance_replay`, preserve the source run's evidence scope. Diagnose the copied observations, but state that the replay adds no seed, task, baseline, or sensitivity evidence and cannot upgrade a scientific verdict.

## Route handoff

- `iteration`: route the precise failure to the method router, evidence designer, implementer, or executor named in `result_route.md`; after execution and ingestion, run this Skill again.
- `tuning`: route `reporting_only` actions to the integrity auditor; route every action requiring code, data, configuration, or new observations through the named owner Skill, execution, ingestion, and a fresh diagnosis.
- `stop` or `report`: route to the integrity auditor with all negative and mixed evidence retained.

Do not send an open `iteration` or execution-required `tuning` route to the final audit.

## Output

Write `result_diagnosis.md` and `result_route.md`; write `result_tuning.json` only for tuning and `next_round.md` whenever another action or run is required. Write paper-ready artifacts under `reports/` only from observed evidence.

Update `AUTODESIGN_STATE.md` to `RESULT_DIAGNOSIS_READY` and set the next Skill to `run-autodesign`. The orchestrator must close or execute the recorded route before final audit.
