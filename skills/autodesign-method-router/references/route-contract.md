# Method Route Contract

`method_route.md` must contain:

## Input classification

- classification;
- exact original claims;
- scientific locks from the supplied Idea and plan;
- autonomous design choices;
- resource constraints.

## Idea semantics

For every central term record its operational meaning, what it constrains, what it does not constrain, observable implication, disallowed reinterpretation, and unresolved uncertainty. Use only the supplied scientific intent plus ordinary technical usage. Do not import unstated configurations or outcomes.

## Autonomous-choice impact

| Choice ID | Autonomous choice | Outcome impact | Effect on what the experiment can show | Candidate A | Candidate B | Fixed controls | Resolution source | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Classify outcome impact exactly as `high` or `low`. A high-impact freedom materially changes the experiment's possible evidence or interpretation, including who generates training data, teacher or judge roles, or the execution substrate. Its resolution source must be either an explicit user decision or an executed R0 comparison of at least two candidate instantiations. A documented default, plausibility argument, or source citation alone is not a resolution. Mark the route blocked while any high-impact freedom remains unresolved.

## Intervention targets

For each contribution: target, proposed mechanism, observable prediction, falsifier.

## Candidate routes

| Route ID | Family | Intervention | Minimal probe | Falsifier | Contribution fit | Benchmark fit | Compute and data | Source evidence | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Use at least two candidate routes for mechanism-specified or goal-only input.

## Selected route

Record selected route ID, rationale, complete method configuration, conditional component roles, expected evidence, and why the rejected routes are inapplicable or less diagnostic.

## Protocol decisions

Record every scientific lock, its honored implementation, autonomous decisions, and resource adaptations. A scientific-lock change cannot be accepted by disclosure alone. Either restore the lock or classify the reduced route as `MECHANISM_PILOT` or `ENGINEERING_SMOKE` while keeping the affected contribution `INCOMPLETE`.

## R0 gate

Record `required: yes_or_no`, covered route uncertainty or high-impact choice IDs, at least two candidate instantiations for each unresolved high-impact choice, fixed controls, probe IDs, evidence class, literal selection threshold, literal kill threshold, cost, execution target, observed comparison, and next action for each outcome. R0 must cover every high-impact autonomous choice not resolved by the user. A single-candidate probe cannot pass this gate. R0 is never sufficient claim support by itself.

## Decision log

Preserve route selection before component instantiation. Every decision states its outcome-impact class, evidence, uncertainty, and what result would change it.
