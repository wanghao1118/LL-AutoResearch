# Weakness Deepener

Use this stage to separate, deepen, and review the strongest P3 candidates. A real FIELD may contain multiple publishable research problems. Retain one to three independent Weaknesses when the evidence supports them; do not merge them to satisfy a single-answer format and do not force a quota.

## 0. Separate Candidates Before Deepening

For each candidate, record a compact scope signature:

```text
Target object or unit
Input and modality
Available supervision
Temporal, spatial, scale, or interaction boundary
Task and expected output
Evaluation or deployment setting
```

Candidates may share a field-level Insight while remaining separate Weaknesses.

Merge two candidates only when all of the following hold:

1. They require the same core ability in the same or directly comparable setting.
2. Their evidence supports a common residual mechanism after the same strongest existing solution.
3. Their manifestations form one necessary capability chain or sibling failure set.
4. One primary controlled experiment can test the combined claim and isolate its parts.

Split them when the modality, task, supervision, temporal boundary, output, strongest solution, likely mechanism, or decisive experiment differs materially. Semantic similarity and a broad shared theme are not enough to merge.

A prerequisite, central operation, and claim-verification stage may remain one Weakness only when they operate on the same target outcome in the same research setting and can be isolated inside one experimental system. This exception prevents one coherent method problem from being over-split.

## 1. Rewrite The Candidate In Plain Language

State in one sentence:

```text
Under [specific setting], current methods cannot reliably [required behavior], causing [observable failure].
```

The sentence must name a missing capability or unresolved behavior. It must not rely on phrases such as "lacks a unified framework", "is not fully explored", or "has not jointly covered all tasks".

## 2. Freeze Scope Before Proposing A Mechanism

Specify only dimensions that change the research problem:

- object and unit of analysis;
- input modality and available supervision;
- task and expected output;
- deployment or evaluation setting;
- temporal, spatial, scale, or interaction boundary when relevant;
- excluded neighboring tasks.

If the P3 field is too broad, narrow it using evidence and user intent. Mark the boundary as `provisional` when data feasibility remains unknown.

For every scope restriction, record one provenance label:

- `user_specified`;
- `directly_supported_by_evidence`;
- `provisional_inference`.

Do not silently infer a modality, dimensionality, supervision condition, number of observations, disease, environment, or deployment constraint from a broad FIELD. A provisional restriction must remain visible until the user or evidence confirms it.

## 3. Audit The Strongest Existing Solution

Identify the closest same-domain solution, not merely a semantically similar paper. Record:

```text
What it actually solves
Input and supervision
Dataset/environment
Benchmark and metric
Relevant result
What it still assumes or leaves unresolved
Evidence location and confidence
```

If a paper already solves the claimed problem in the same setting, revise the Weakness to the residual boundary or reject it.

## 4. Decompose Each Weakness Without Mixing Research Problems

Derive two or three observable manifestations. They must be failures of the same core ability and form a coherent chain or sibling set.

When the target outcome requires a sequence of capabilities, first draw the shortest necessary capability chain. Assign each proposed bottleneck one role:

- `prerequisite`: its output is required before the central operation can be evaluated;
- `core_transfer`: it carries the target object or state through the task;
- `claim_verification`: it tests whether the final output actually depends on that object or state.

Include a stage only when its failure directly breaks the same target outcome. Do not expand a narrow P3 candidate into an end-to-end system unless the frozen Scope explicitly requires that complete path.

For each manifestation, separate:

```text
Manifestation: what goes wrong
Technical bottleneck: why current methods struggle
Existing partial solution: what has already been tried
Residual: what remains after the best solution
Distinguishing test: the smallest observation that separates the proposed explanation from its strongest competitor
```

A manifestation is not yet a technical bottleneck. For example, "the model loses the target" is a manifestation; uncertainty accumulation, unstable identity evidence, or an inaccessible state may be candidate bottlenecks.

## 5. Eliminate Ordinary Explanations

Before proposing an innovative direction, test whether the failure can plausibly be explained by:

- missing data or labels;
- insufficient model capacity;
- ordinary SFT coverage;
- evaluation noise;
- upstream detection failure;
- a different task definition.

Do not reject these explanations merely because they are uninteresting. State the evidence needed to distinguish them.

Cross-domain analogies may be searched only after the bottleneck is fixed. Use them to import a mechanism principle, not to rename a familiar module.

## 6. Evidence And Design Gate

Choose exactly one status:

- `READY_FOR_METHOD_DESIGN`: scope, behavior failure, strongest same-setting solution, residual, and at least one distinguishing test are supported well enough to invest in method design.
- `NEEDS_WEAKNESS_VALIDATION`: plausible and valuable, but a named decisive evidence check is still required before full method design.
- `VALIDATION_GAP`: the missing item is direct validation rather than an established method failure.
- `BENCHMARK_WEAKNESS`: measurement cannot distinguish the target ability from a proxy.
- `EVIDENCE_INSUFFICIENT`: current materials cannot support or cleanly classify the claim.
- `REJECTED`: existing work or evidence contradicts the claim.

Only `READY_FOR_METHOD_DESIGN` proceeds automatically to Candidate Contribution. `NEEDS_WEAKNESS_VALIDATION` receives a decisive validation plan and a conditional method direction, not a fully asserted Contribution.

## 7. Build The Portfolio

After judging candidates independently:

1. Remove paraphrase duplicates.
2. Keep one to three highest-value independent Weaknesses that pass at least `NEEDS_WEAKNESS_VALIDATION`.
3. Keep Method Weaknesses separate from Benchmark Weaknesses and Validation Gaps.
4. Record rejected or lower-ranked candidates in the audit rather than silently deleting them.
5. Give every retained Weakness its own scope, evidence subset, strongest solution, status, falsifier, Contribution decision, and AutoDesign decision.

Do not average evidence across the portfolio. Strong evidence for one Weakness cannot upgrade another.
