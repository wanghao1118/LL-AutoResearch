# Independent Review Rubric

## Hard Gates

Fail or downgrade the package when any condition holds:

1. The core Weakness is only "no unified framework", "not fully studied", or missing joint evaluation.
2. Scope changes between evidence, Weakness, Contribution, and experiment requirements.
3. The strongest existing same-setting solution is omitted or already resolves the claim.
4. The two or three subproblems do not belong to one core Weakness.
5. The Contribution is a list of modules without explaining why each is necessary.
6. Claimed novelty or results are presented as established before experiments.
7. Critical evidence is inferred from abstracts as proof of absence.
8. Evidence from materially different modalities, tasks, supervision, temporal boundaries, outputs, or evaluation settings is merged into one Method Weakness without a same-setting causal bridge and one decisive experiment that can test the combined claim.
9. A portfolio contains paraphrase duplicates presented as separate publication opportunities.

## Portfolio Structure Gate

When more than one Weakness is supplied:

1. Compare each candidate's target object, input, supervision, boundary, task, output, strongest existing solution, and decisive experiment.
2. Allow a shared field-level Insight, but require every Weakness to have its own evidence subset and residual claim.
3. Require merging only when the candidates form one necessary capability chain in the same setting and can be isolated inside one experimental system.
4. Require splitting when their likely mechanism, strongest solution, or primary falsification experiment differs materially.
5. Judge every retained Weakness independently; do not average away a failure.

## Scored Dimensions

Score each from 0 to 4 and cite the packet evidence:

1. **Evidence faithfulness:** direct facts, synthesis, and hypotheses are separated.
2. **Scope integrity:** the object, task, input, and setting stay fixed.
3. **Weakness validity:** the missing behavior is important, observable, and not merely missing validation.
4. **Residual novelty:** the Weakness remains after the strongest partial solution.
5. **Decomposition quality:** manifestations and bottlenecks are related, specific, and non-duplicative.
6. **Mechanism depth:** bottlenecks explain why ordinary solutions may fail and name competing explanations.
7. **Contribution alignment:** one overall method and its necessary components address the bottlenecks.
8. **Experiment discriminativeness:** required tests can distinguish the proposed explanation from alternatives.
9. **AutoDesign readiness:** data, baselines, metrics, falsifiers, constraints, and open decisions are actionable.
10. **Human clarity:** a general AI researcher can understand the problem without decoding invented terminology.

## Separate Innovation Assessment

Report innovation separately from evidence readiness. Do not average the two into one reassuring total, and do not let a high-upside idea bypass a hard evidence gate.

Assess:

1. **Non-obviousness:** the candidate identifies more than missing coverage or an untried combination.
2. **Mechanism novelty:** it proposes a testable new account of what is lost, confused, misaligned, or inaccessible.
3. **Residual novelty:** the claim remains meaningful after the strongest same-setting solution.
4. **Intervention leverage:** one controllable variable can test the proposed mechanism without requiring an entire new system first.
5. **Knowledge gain:** a negative result would still distinguish explanations or establish a useful boundary.

Return both:

```text
Evidence Readiness: high | medium | low
Innovation Potential: high | medium | low
```

An evidence-ready but incremental candidate may be suitable for engineering rather than a strong research Contribution. A high-innovation but low-evidence candidate requires targeted validation before AutoDesign.

## Verdicts

- `APPROVE_FOR_AUTODESIGN`: no hard-gate failure; core dimensions are at least 3; evidence uncertainty is explicit.
- `VALIDATE_BEFORE_AUTODESIGN`: the Weakness is plausible and important, but a named decisive check must precede full method design.
- `REVISE`: the core idea is viable but one or two named defects prevent handoff.
- `EVIDENCE_INSUFFICIENT`: the claim may be valuable, but decisive same-setting evidence is missing.
- `RECLASSIFY_AS_VALIDATION_GAP`: evidence does not establish a method failure.
- `RECLASSIFY_AS_BENCHMARK_WEAKNESS`: the central problem is measurement.
- `REJECT`: contradicted, already solved in scope, internally incoherent, or not important enough to justify the proposed work.

## Output

```text
Portfolio Structure Verdict: required only for multiple Weaknesses
Split-Merge Findings: required only for multiple Weaknesses
Verdict:
One-Sentence Assessment:
Hard-Gate Findings:
Score Table:
Evidence Readiness:
Innovation Potential:
Innovation Assessment:
Strongest Part:
Decisive Weakness:
Most Important Missing Evidence:
Highest-Priority Revision:
AutoDesign Readiness:
```

Do not average away a hard-gate failure. A high total score cannot compensate for an invalid core Weakness.
