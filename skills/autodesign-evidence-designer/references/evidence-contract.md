# Evidence Plan Contract

## Claim ledger

| Claim ID | Contribution | Original claim | Mechanism | Required axes | Supporting experiments | Falsifier | Scope |
| --- | --- | --- | --- | --- | --- | --- | --- |

Every original claim appears at least once and every required axis maps to a real comparison.

## Baseline decision

For each candidate record source, revision, role coverage, contribution fit, benchmark fit, fairness plan, resource cost, selected or rejected status, and rationale. Selected baselines must appear in main experiment variants.

## Experiment card

Each experiment contains:

- ID and evidence role;
- mapped claim IDs and exact claim subset;
- hypothesis and falsifier;
- variants and baselines;
- benchmark tasks, splits, facets, and metrics;
- seeds;
- controlled and changed axes;
- implementation entrypoint intent;
- result artifacts;
- decision rule;
- priority and cost.

## Expected cells

Define the Cartesian cells expected from experiment × variant × task × seed. Do not call theoretical or missing cells observed results.

## Reporting plan

Each table and figure declares experiment IDs, fields or axes, output path, and the decision it supports. Case examples specify the selection rule before results are inspected.

## Coverage audit

End with literal `PASS` only when every claim and required axis has a supporting experiment and falsifier. Otherwise list blockers and keep the state before `EVIDENCE_PLAN_READY`.
