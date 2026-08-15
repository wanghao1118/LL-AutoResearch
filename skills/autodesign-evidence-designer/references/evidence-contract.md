# Evidence Plan Contract

## Claim ledger

| Claim ID | Contribution | Original claim | Mechanism | Required axes | Claim-bearing experiments | Falsifier | Status boundary |
| --- | --- | --- | --- | --- | --- | --- | --- |

Every original claim appears at least once and every required axis maps to a real `CLAIM_BEARING` comparison. Pilot and smoke experiments remain visible but do not satisfy this mapping.

## Idea-consistency audit

For each planned experiment record the scientific locks it preserves, autonomous choices it instantiates, resource adaptations, and any affected contribution. A changed lock makes the experiment non-claim-bearing.

## Baseline decision

For each candidate record source, revision, role coverage, contribution fit, benchmark fit, scaffold and protocol requirements, fairness plan, resource cost, selected or rejected status, and rationale. Selected baselines must appear in main claim-bearing experiment variants. Equal budgets do not justify changing a baseline's defining scaffold or protocol.

## Experiment card

Each experiment contains:

- ID and evidence role;
- evidence class: `CLAIM_BEARING`, `MECHANISM_PILOT`, or `ENGINEERING_SMOKE`;
- mapped claim IDs and exact claim subset;
- hypothesis and falsifier;
- variants and baselines;
- benchmark identity, provenance, revision, tasks, splits, facets, metrics, and protocol locks;
- seeds;
- controlled and changed axes;
- data manifest, sampling policy, planned composition, and quality observables when applicable;
- implementation entrypoint intent;
- result artifacts;
- decision rule;
- priority and cost.

## Expected cells

Define the Cartesian cells expected from experiment × variant × task × seed, including evidence class and benchmark provenance. Do not call theoretical or missing cells observed results. A later round requires an explicit plan and schedule revision; it may not append cells silently.

## Preflight requirements

For every scientific lock or controlled axis, state the exact observable preflight check, failure condition, and changed next action. For data-based routes require planned-versus-materialized sample counts and distributions before expensive execution. When filtering or decontamination is required, trace the production path from source data through the materialized filtered artifact to the exact training input.

## Reporting plan

Each table and figure declares experiment IDs, fields or axes, output path, and the decision it supports. Case examples specify the selection rule before results are inspected.

## Coverage audit

End with literal `PASS` only when every claim and required axis has a claim-bearing experiment and falsifier, every locked benchmark has valid provenance, every selected baseline has a fairness plan, and every decision-relevant preflight has a failure action. Otherwise list blockers and keep the state before `EVIDENCE_PLAN_READY`.
