# Result Diagnosis Contract

## Readiness

Record execution status, expected and observed cells, missing and unexpected cells, planned and observed metrics, and any infrastructure failures. Missing execution evidence blocks scientific interpretation.

Record whether observations came from a fresh experiment or a provenance replay. A replay can validate recomputation and artifact flow but cannot expand the source run's scientific coverage.

## Contribution diagnosis

For every contribution record:

- exact original claim;
- status;
- supporting observations;
- contradicting observations;
- uncertainty and scope;
- falsifier outcome;
- required missing evidence;
- allowed conclusion wording.

## Routing

- `iteration`: specify missing evidence, exact next experiment, owner Skill, cost, and completion threshold.
- `tuning`: read `result_tuning_prompt.md`, specify one justified primary variable per experimental action, diagnostic rationale, owner Skill, guardrails, required execution, and stop threshold.
- `stop`: cite the crossed kill criterion or exhausted decision path.
- `report`: give main-table, appendix, case, and limitation placement.

Reporting scope can choose where results appear, but cannot rewrite the original contribution or omit observed failures.

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

An iteration or execution-required tuning route remains open until its action is implemented, executed, ingested, and rediagnosed. Reporting-only tuning can proceed directly to audit only when `result_tuning.json` changes no experiment, configuration, raw result, aggregate, contribution, or claim.

## `result_tuning.json`

Use the JSON schema in `result_tuning_prompt.md`. Replace available placeholders with observed values and references; keep unavailable values as `TBD`. Require:

- `reporting_scope.claim_policy` equal to `KEEP_ORIGINAL_CONTRIBUTION_AND_CLAIM_UNCHANGED`;
- every action linked to a contribution diagnosis and observed result reference;
- the action class and whether fresh execution is required;
- complete decision-log input and output states;
- no claim rewrite, hidden failed slice, omitted observed ablation, seed subset selection, or automatic upgrade from expected to observed evidence.

## `next_round.md`

For each open action record its owner Skill, one primary changed variable, fixed controls, minimum experiment cells, literal command intent, expected observation, cost, continue threshold, stop threshold, invalidated artifacts, and the stage that resumes after completion.
