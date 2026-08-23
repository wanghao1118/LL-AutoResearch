# Candidate Contribution And AutoDesign Handoff

Apply this file independently to each retained Weakness. Never design one Contribution by pooling evidence from separate Weaknesses.

## Entry Decision

- `READY_FOR_METHOD_DESIGN`: produce a normal Candidate Contribution and AutoDesign handoff.
- `NEEDS_WEAKNESS_VALIDATION`: produce the smallest decisive validation plus a conditional method direction. Do not commit AutoDesign to a full implementation yet.
- `VALIDATION_GAP`, `BENCHMARK_WEAKNESS`, `EVIDENCE_INSUFFICIENT`, or `REJECTED`: do not generate a Method Contribution from this path.

A Candidate Contribution is still awaiting experimental support. Do not call it a final or established Contribution.

## Candidate Contribution

For `READY_FOR_METHOD_DESIGN`, produce:

1. **Overall method contribution:** one concrete research direction that addresses the entire core Weakness.
2. **Necessary technical contributions:** zero to three components, each required by one approved bottleneck.
3. **Optional data or benchmark contribution:** include only when existing data or measurement cannot test the central claim.
4. **Expected empirical contribution:** phrase as a preregistered requirement, not an achieved result.

For every contribution state:

```text
Technical difficulty it addresses
Object or relationship it changes
Why the change could resolve the difficulty
How it differs from the strongest existing solution
What result would falsify it
```

The supporting contributions must form one method. Do not list three independent ideas. A generic module, larger model, more data, joint training, or a renamed mechanism cannot stand alone as innovation, though it may be part of an otherwise justified solution.

Be concrete about the mechanism principle, but leave exact architecture, loss, and training recipe to AutoDesign.

For `NEEDS_WEAKNESS_VALIDATION`, produce instead:

```text
Unresolved weakness claim
Decisive validation experiment
Outcomes that support, narrow, or reject it
Conditional method direction if supported
Evidence required before AutoDesign handoff
```

Do not invent a detailed method to compensate for an unverified problem.

## AutoDesign Handoff

Freeze:

- field and scope;
- core Weakness;
- evidence-backed technical bottlenecks;
- strongest existing solution and novelty boundary;
- behavior the method must change;
- claims AutoDesign must not silently replace.

Require AutoDesign to decide:

- implementable architecture and modules;
- exact objectives and training procedure;
- data preparation;
- experiment sequence and resource plan.

Provide the following checklist:

```text
Required data and labels
Must-include baselines
Main outcome metrics
Mechanism-diagnostic metrics
Minimal causal or distinguishing experiment
Key ablations
Failure analysis
Falsification conditions
Known evidence gaps
Resource constraints
```

Prefer staged evaluation that isolates each bottleneck before an end-to-end score. A final score alone cannot establish that the proposed mechanism solved the Weakness.
