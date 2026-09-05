# Result Diagnosis Contract

## Readiness

Record execution status, expected and observed cells, missing and unexpected cells, planned and observed metrics, and any infrastructure failures from available artifacts. Missing execution evidence blocks scientific interpretation, not engineering diagnosis, recovery planning, or a requested conservative report. Mark unknown counts and unavailable sources explicitly rather than inferring completeness.

Identify the current run's experiment commands and execution record for each observation. If that provenance cannot be established, record the gap and exclude the observation from claim-bearing evidence.

Record evidence eligibility before behavior interpretation: scientific locks, family, evidence class, benchmark provenance, data manifest and composition, implementation identity, expected and unexpected cells, and production input paths. If a required claim-bearing comparison fails this check, the affected contribution is `INCOMPLETE`.

Check whether `effect_comparison.md` exists and covers every `expected_effects.json` entry. A missing or partial comparison blocks method-behavior interpretation and evidence-based contribution verdicts; still diagnose the gap, mark affected contributions `INCOMPLETE`, and describe the required correction.

## Target comparison

Read `effect_comparison.md` as routing input only.

- A `MISSED` threshold localizes where to investigate; it is not itself a `NOT_SUPPORTED` verdict.
- A `MET` threshold is a fact about the observation clearing its own design-time threshold. It never by itself upgrades a contribution to `SUPPORTED`, and it never substitutes for a falsifier outcome.
- A `NOT_EVALUABLE` entry names the missing reference variant or cell and normally forces `INCOMPLETE` for the affected claim.
- Never justify a verdict by how near an observation came to a `simulated_target`, and never edit a target to match an observation. Report systematic miscalibration as a design finding for `design`.

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

- `iteration`: specify missing evidence, exact next experiment, owner worker, cost, and completion threshold.
- `tuning`: read `result_tuning_prompt.md`, specify one justified primary variable per experimental action, diagnostic rationale, owner worker, guardrails, required execution, and stop threshold.
- `stop`: cite the crossed kill criterion or exhausted decision path and show that the underlying evidence was claim-bearing and eligible.
- `report`: give main-table, appendix, case, and limitation placement.

`owner_stage` is exactly `design` for a route, evidence, experiment-set, or target-calibration defect, or `run` for a code, data, configuration, command, or execution defect.

Reporting scope can choose where results appear, but cannot rewrite the original contribution or omit claim-critical negative, mixed, failed-slice, or ablation results.

Execution follows the user's authorized scope. Continue admissible recovery when execution is authorized; method revisions retain their explicit approval gate. For an explicit diagnosis-only, stop-execution, or conservative-report request, deliver the requested artifacts without starting new experiments. Keep the scientific route and missing-evidence actions recorded, including `iteration` and `execution_required: yes` when execution would be necessary to close the evidence gap, and state that dispatch is withheld by the user's scope restriction. This is a completed diagnostic/reporting delivery with an incomplete experiment, not a scientific `stop` verdict or full-run `COMPLETE`.

## Report closure

For `stop`, `report`, and reporting-only routes, the accepted reporting plan is an output contract rather than an optional suggestion. Materialize every named table, figure, case-study panel, and analysis artifact under `reports/`. A negative or conservative conclusion changes the caption and claim boundary, not whether the artifact exists.

An explicitly requested conservative report may also be delivered while the scientific route remains open. Apply the same reporting-plan and visible-gap requirements, retain the last accepted run state and unresolved actions, and do not advance to final audit or `COMPLETE` on the strength of report delivery.

Write `reports/report_manifest.json` with one entry per planned output: output path, source experiment/effect IDs, evidence status (`READY`, `INCOMPLETE`, or `N/A`), and a literal reason when not ready. Write `reports/index.html` as the readable entry point. If evidence is missing or ineligible, the planned artifact itself must visibly say `INCOMPLETE` or `N/A` and identify the missing source; never omit it, substitute a simulated target, or encode unavailable as zero. Diagnostic-only partial values may be shown only with an explicit label and may not fill a claim-bearing paper cell.

## `result_route.md`

Record all fields below:

- `route`: exactly `iteration`, `tuning`, `stop`, or `report`;
- exact decision reason and contribution IDs;
- `owner_stage` for the next action;
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
- no manual edit or overwrite of an observed raw value, aggregate, uncertainty, or paper-table number;
- tuning selection uses training/validation evidence only, with a declared search budget and fresh confirmation identity;
- baseline tuning keeps or strengthens the fairest comparable baseline rather than selecting a weaker configuration;
- a change motivated by already observed test results is labeled as a post-result revision, and the original result remains visible.

## `next_round.md`

For each open action record its owner worker, one primary changed variable, fixed controls, minimum experiment cells, literal command intent, expected observation, cost, continue threshold, stop threshold, invalidated artifacts, and the stage that resumes after completion.
