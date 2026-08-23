# Innovation Lens

Use this stage after P3 candidate generation and before Weakness deepening. Its purpose is to preserve non-obvious research opportunities without confusing an interesting hypothesis with an evidence-backed Weakness.

## Review Each Candidate

Answer these questions using the frozen P3 output and its Evidence Pack:

1. **Unexpected observation:** What failure, contradiction, reversal, or proxy-target mismatch makes this candidate more than an uncovered topic?
2. **Residual after the best solution:** What does the strongest same-setting solution already fix, and what important failure remains?
3. **Ordinary explanations:** Could missing data, model capacity, routine SFT, evaluation noise, or an upstream failure explain the result? State the strongest ordinary explanation rather than dismissing it.
4. **Mechanism insight:** What technical object, relationship, state, signal, or interface may be represented, transmitted, supervised, or used incorrectly?
5. **Intervention leverage:** What single variable or relationship could be changed to test that mechanism? Name the intervention target, not a complete architecture.
6. **Decisive test:** What smallest controlled comparison would distinguish the mechanism insight from the strongest ordinary explanation?
7. **Knowledge gain:** If the hypothesis is rejected, what useful conclusion would the experiment still establish?

Do not invent a mechanism merely to make a candidate sound innovative. When evidence supports only an observation or hypothesis, label it accordingly.

## Assess Two Independent Axes

```text
Evidence Readiness: high | medium | low
Innovation Potential: high | medium | low
```

`Evidence Readiness` describes whether the current literature supports the claimed residual failure. `Innovation Potential` describes whether resolving it could add non-obvious, testable knowledge.

High innovation potential normally requires:

- a non-obvious relationship or mechanism, not only an uncovered combination;
- a residual problem that survives the strongest existing solution;
- an actionable intervention target;
- a decisive test against a credible competing explanation;
- useful knowledge gain even if the proposed mechanism is wrong.

The following do not establish innovation by themselves:

- nobody has combined the components;
- more data, a larger model, or routine SFT;
- a newly named module or unified framework;
- adding another benchmark or improving an aggregate score without explaining the capability gained.

## Retention Rule

Preserve both of these when justified:

- the best evidence-ready candidate;
- a distinct high-upside candidate that still needs a named validation experiment.

Do not force either category or a fixed count. A high-upside candidate that lacks decisive evidence must proceed as `NEEDS_WEAKNESS_VALIDATION`, not `READY_FOR_METHOD_DESIGN`.

## Output

Write `internal/innovation_review.md` with one compact record per P3 candidate:

```text
Candidate ID:
Unexpected Observation:
Strongest Existing Solution And Residual:
Strongest Ordinary Explanation:
Mechanism Insight:
Intervention Target:
Decisive Test:
Knowledge Gain If Rejected:
Evidence Readiness:
Innovation Potential:
Retention Decision And Reason:
```
