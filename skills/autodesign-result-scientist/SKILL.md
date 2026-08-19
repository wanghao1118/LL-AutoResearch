---
name: autodesign-result-scientist
description: "Diagnose, interpret, or iterate on completed AutoDesign results. Use after execution to distinguish preregistration and analyzer issues, implementation behavior, API transport failures, evaluator failures, missing evidence, mixed or negative scientific results, target-versus-observed misses, tuning opportunities, stopping decisions, and paper-ready reporting scope."
---

# AutoDesign Result Scientist

Interpret observed evidence without manufacturing support for a contribution.

## Entry gate

Read `input_brief.md`, `experiment_design.md`, `expected_effects.json`, `implementation_notes.md`, preflight reports, `execution_record.json`, raw results, `result_summary.json`, `effect_comparison.md`, and `references/diagnosis-contract.md`.

Stop before scientific diagnosis unless current preflight, smoke, experiment, aggregate, and collect records pass, scheduled cells and metrics are complete, no unexpected cell is unresolved, evidence identities match the accepted design, and `effect_comparison.md` covers every design entry.

## Diagnose

1. Diagnose in this order: scientific-lock or provenance defect; data-preparation defect; implementation defect; API or transport defect; evaluator defect; method behavior. Do not interpret downstream behavior before upstream evidence eligibility passes.
2. Recompute aggregates from raw records. Preserve denominators, seeds, missing cells, and failed slices.
3. Diagnose every original contribution independently as `SUPPORTED`, `MIXED`, `NOT_SUPPORTED`, or `INCOMPLETE`. A required scientific-lock, provenance, data-preparation, or implementation defect forces `INCOMPLETE` and `iteration`; it cannot produce `NOT_SUPPORTED` or `stop`.
4. Cite exact experiments, families, variants, tasks, metrics, uncertainty, cases, and falsifiers.
5. Use only `CLAIM_BEARING` experiments for contribution verdicts. Report pilot and smoke observations separately as engineering or mechanism diagnostics. Read across families deliberately: main experiments establish the effect, ablations attribute it, case studies illustrate it, and analysis experiments bound it. A main result without its supporting ablation attribution is incomplete attribution, not a supported mechanism.
6. Read `effect_comparison.md` as a routing input, not as a verdict. A `MISSED` threshold identifies where to look; a `MET` threshold is a threshold fact and never by itself upgrades a contribution to `SUPPORTED`. Treat a systematically miscalibrated `simulated_target` as a design finding to report, and never justify a verdict by how close an observation came to a design-time target.
7. Treat one-seed, post-hoc slices, and position-specific effects as exploratory and state the additional runs required for confirmation.
8. Select one route:
   - `iteration` when required evidence is incomplete;
   - `tuning` when evidence is complete but mixed or negative and a justified single-variable action remains;
   - `stop` when eligible claim-bearing evidence crosses a preregistered kill threshold or no diagnostic action remains;
   - `report` when contributions are adequately supported.
9. Always write `result_route.md` with the selected route, exact reason, owner Skill, changed variable or artifact, whether new execution is required, invalidated downstream artifacts, and literal continue and stop thresholds.
10. After selecting `iteration` or `tuning`, read `references/result_tuning_prompt.md`. Supply it with the current input brief, accepted design, execution record, raw results, deterministic summary, effect comparison, and current contribution diagnosis. Use its action schema to plan the next step.
11. For `iteration`, use the action plan to write `next_round.md` with the missing evidence, minimum experiment cells, fixed controls, command intent, expected observation, cost, and completion threshold. Write `result_tuning.json` only when the selected route is `tuning`.
12. Treat the action reference as a catalog, not as permission to weaken the pipeline invariants. Keep every original contribution and claim unchanged, retain every observed negative or mixed result, keep baseline and method budgets and seed sets comparable, and never convert an unexecuted expected delta or a simulated target into an observed result.
13. For every tuning action preserve input state → one primary action → expected diagnostic change → required execution → observed output state. Classify the action as `reporting_only`, `implementation_change`, `new_evidence`, or `execution_retry`, then write `next_round.md` when any action remains unexecuted.
14. Produce paper-ready tables and figures only from observed aggregates. Keep all claim-critical negative, mixed, and failed-slice results visible.

## Route handoff

- `iteration`: route the precise failure to the owner named in `result_route.md` — `autodesign-experiment-design` for a route, evidence, or experiment-set defect, `autodesign-experiment-run` for a code, data, configuration, or execution defect. After execution and ingestion, run this Skill again.
- `tuning`: route `reporting_only` actions to the integrity auditor; route every action requiring code, data, configuration, or new observations through the named owner Skill, execution, ingestion, recomparison, and a fresh diagnosis.
- `stop` or `report`: route to the integrity auditor with all negative and mixed evidence retained.

Do not send an open `iteration` or execution-required `tuning` route to the final audit.

## Output

Write `result_diagnosis.md` and `result_route.md`; write `result_tuning.json` only for tuning and `next_round.md` whenever another action or run is required. Write paper-ready artifacts under `reports/` only from observed evidence.

Update `AUTODESIGN_STATE.md` to `RESULT_DIAGNOSIS_READY` and set the next Skill to `run-autodesign`. The orchestrator must close or execute the recorded route before final audit.
