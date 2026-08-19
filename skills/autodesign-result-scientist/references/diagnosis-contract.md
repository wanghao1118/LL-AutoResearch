# Result Diagnosis Contract

## Readiness

Record execution status, expected and observed cells, missing and unexpected cells, planned and observed metrics, and any infrastructure failures. Missing execution evidence blocks scientific interpretation.

Record that observations came from the current run's fresh experiment commands and identify their execution record.

Record evidence eligibility before behavior interpretation: scientific locks, family, evidence class, benchmark provenance, data manifest and composition, implementation identity, expected and unexpected cells, and production input paths. If a required claim-bearing comparison fails this check, the affected contribution is `INCOMPLETE`.

Record that `effect_comparison.md` exists and covers every `expected_effects.json` entry. A missing or partial comparison blocks diagnosis.

## Target comparison

Read `effect_comparison.md` as routing input only.

- A `MISSED` threshold localizes where to investigate; it is not itself a `NOT_SUPPORTED` verdict.
- A `MET` threshold is a fact about the observation clearing its own design-time threshold. It never by itself upgrades a contribution to `SUPPORTED`, and it never substitutes for a falsifier outcome.
- A `NOT_EVALUABLE` entry names the missing reference variant or cell and normally forces `INCOMPLETE` for the affected claim.
- Never justify a verdict by how near an observation came to a `simulated_target`, and never edit a target to match an observation. Report systematic miscalibration as a design finding for `autodesign-experiment-design`.

## Contribution diagnosis

For every contribution record:

- exact original claim;
- status;
- eligible claim-bearing experiments, with their families;
- cross-family reading: which main experiment establishes the effect, which ablation attributes it, which case study illustrates it, which analysis bounds it, and which of these is missing;
- separately reported pilot or smoke observations;
- supporting observations;
- contradicting observations;
- threshold outcomes from `effect_comparison.md` for the relevant entries;
- uncertainty and scope;
- falsifier outcome;
- required missing evidence;
- allowed conclusion wording.

## Routing

- `iteration`: specify missing evidence, exact next experiment, owner Skill, cost, and completion threshold.
- `tuning`: read `result_tuning_prompt.md`, specify one justified primary variable per experimental action, diagnostic rationale, owner Skill, guardrails, required execution, and stop threshold.
- `stop`: cite the crossed kill criterion or exhausted decision path and show that the underlying evidence was claim-bearing and eligible.
- `report`: give main-table, appendix, case, and limitation placement.

`owner_skill` is exactly `autodesign-experiment-design` for a route, evidence, experiment-set, or target-calibration defect, or `autodesign-experiment-run` for a code, data, configuration, command, or execution defect.

Reporting scope can choose where results appear, but cannot rewrite the original contribution or omit claim-critical negative, mixed, failed-slice, or ablation results.

## `result_route.md`

Record all fields below:

- `route`: exactly `iteration`, `tuning`, `stop`, or `report`;
- exact decision reason and contribution IDs;
- `owner_skill` for the next action;
- changed variable or artifact;
- `execution_required`: `yes` or `no`;
- invalidated downstream artifacts;
- literal continue and stop thresholds;
- route closure condition.

An iteration or execution-required tuning route remains open until its action is implemented, executed, ingested, recompared against the design targets, and rediagnosed. Reporting-only tuning can proceed directly to audit only when `result_tuning.json` changes no experiment, configuration, raw result, aggregate, contribution, or claim.

## `result_tuning.json`

Use the JSON schema in `result_tuning_prompt.md`. Replace available placeholders with observed values and references; keep unavailable values as `TBD`. Require:

- `reporting_scope.claim_policy` equal to `KEEP_ORIGINAL_CONTRIBUTION_AND_CLAIM_UNCHANGED`;
- every action linked to a contribution diagnosis and observed result reference;
- the action class and whether fresh execution is required;
- complete decision-log input and output states;
- no claim rewrite, hidden failed slice, omitted observed ablation, seed subset selection, or automatic upgrade from expected to observed evidence;
- no promotion of a `simulated_target` or an unexecuted expected delta into an observed value;
- no outcome-dependent metric, aggregation, seed-count, baseline-budget, case-selection, or table-row selection.

## `next_round.md`

For each open action record its owner Skill, one primary changed variable, fixed controls, minimum experiment cells, literal command intent, expected observation, cost, continue threshold, stop threshold, invalidated artifacts, and the stage that resumes after completion.
