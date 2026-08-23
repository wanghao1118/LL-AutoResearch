---
name: autosearch-research-discovery
description: Discover and deepen evidence-backed AI research weaknesses, turn a design-ready weakness into candidate contributions, and prepare an AutoDesign handoff. Use when a user supplies a research FIELD or an existing P3/Evidence Pack and wants Insight, Method Weakness, technical bottlenecks, or a concrete research package. Do not use for full architecture, loss, training, or experiment implementation.
---

# AutoSearch Research Discovery

Build one or more independent research packages through four gates:

```text
P3 discovery -> Innovation review -> Weakness deepening -> Candidate Contribution and AutoDesign handoff
```

The user may provide only `FIELD`. Default missing values to:

```text
MODE: frontier_discovery
QUESTION: What important, real, falsifiable Method Weakness remains in this field?
EVIDENCE_CUTOFF: current date
TIME_RANGE: recent 5 years, plus necessary foundational work
```

Do not introduce a static branch dictionary or carry domain terms from prior runs into the current field.

## Default Research Output

For real research discovery, retain one to three non-duplicative Weaknesses that independently pass the evidence gates. Do not ask the user to choose an output mode, do not force a quota, and do not discard a second qualified Weakness merely because another one ranks higher.

Use a single-best result only as an internal evaluation behavior when the user explicitly requests a blind Prompt comparison or one strongest answer. It is not a normal user-facing mode.

## Choose A Mode

- `full`: Start from `FIELD`; run the frozen P3 prompt, review candidate innovation potential, and then deepen the retained candidates.
- `deepen`: Use a supplied P3 output and Evidence Pack. Start with innovation review; do not repeat search unless a decisive evidence hole is identified.
- `handoff`: Use a `READY_FOR_METHOD_DESIGN` Weakness and its technical bottlenecks to prepare Candidate Contribution and AutoDesign inputs.

If the user does not specify a mode, choose the earliest stage required by the supplied material.

## Stage 1: P3 Discovery

When running `full`, read only [references/p3-discovery-frozen.md](references/p3-discovery-frozen.md) for candidate generation and follow it exactly. Do not read the innovation, deepening, or contribution references until the P3 output has been written. This isolation preserves P3 as a comparable baseline.

Treat its final Weaknesses and Idea Seeds as candidates, not approved conclusions. Preserve its candidate-type distinctions and evidence audit. Save an unchanged snapshot as `internal/p3_raw_candidates.md` before any later stage rewrites, merges, ranks, or removes a candidate.

Legacy P3 labels such as `APPROVED_METHOD_WEAKNESS` or `METHOD_WEAKNESS_CANDIDATE` are input annotations only. Rejudge them during deepening and emit the current user-facing states; do not carry an old approval forward automatically.

Do not patch the frozen P3 prompt for a particular domain. Record any observed failure for later Skill revision.

## Stage 2: Review Innovation Potential

After the raw P3 snapshot is frozen, read [references/innovation-lens.md](references/innovation-lens.md). Review every candidate for non-obvious mechanism insight, residual novelty after the strongest existing solution, an actionable intervention variable, and a decisive distinguishing experiment.

For `deepen`, first copy the supplied P3 output unchanged into `internal/p3_raw_candidates.md`; do not reinterpret it before the snapshot exists.

Write `internal/innovation_review.md`. Keep `Evidence Readiness` separate from `Innovation Potential`: a speculative but high-upside candidate may remain visible for targeted validation, but innovation potential cannot upgrade an unsupported claim into an established Method Weakness. Do not overwrite or silently delete the raw P3 candidates.

## Stage 3: Separate And Deepen Core Weaknesses

Read [references/weakness-deepener.md](references/weakness-deepener.md). First decide which candidates are genuinely the same research problem and which must remain separate. Then deepen each retained core Method Weakness independently: freeze its scope, audit the strongest existing solution in the same setting, identify the residual problem, and derive two or three related manifestations and technical bottlenecks.

Different settings may support a shared field-level Insight without supporting one merged Weakness. Merge candidates only when they share the target ability, experimental setting, residual mechanism, and a decisive experiment that can test the combined claim.

Stop or downgrade when the evidence supports only a Validation Gap or Benchmark Weakness. Do not force a method paper from missing evaluation coverage.

## Stage 4: Build The Research Package

Only after an individual Weakness passes the deepening gate, read [references/contribution-handoff.md](references/contribution-handoff.md). Produce one overall Candidate Contribution plus only the necessary supporting contributions for that Weakness. Then hand AutoDesign the variables, required comparisons, metrics, evidence obligations, and falsifiers without choosing the full implementation.

Use these user-facing states:

- `READY_FOR_METHOD_DESIGN` / 可进入方法设计: generate a normal Candidate Contribution and AutoDesign handoff.
- `NEEDS_WEAKNESS_VALIDATION` / 需要先验证: preserve the idea, but generate only the decisive validation and a conditional method direction.
- `VALIDATION_GAP` / 验证缺口: do not present a Method Contribution.
- `BENCHMARK_WEAKNESS` / 评估问题: route separately from Method Contribution.
- `EVIDENCE_INSUFFICIENT` / 证据不足, or `REJECTED` / 不成立: stop the method-design path.

`Candidate Contribution` always means a proposal awaiting experiments, never an established paper contribution.

Use [references/output-contract.md](references/output-contract.md) for the user-facing result. Prefer plain Chinese. Explain every unavoidable technical term on first use. Avoid invented labels when ordinary language is clearer.

## Evidence Discipline

- Separate paper-reported facts, cross-paper synthesis, and untested hypotheses.
- State the dataset, benchmark, baseline, metric, and setting behind claims about existing performance whenever the source provides them.
- A missing paper, experiment, or unified framework is not by itself a Method Weakness.
- Abstract-only evidence cannot prove that a method, experiment, or result is absent.
- Keep the strongest boundary or partial solution visible; describe what remains after it.
- Mark inaccessible or unverified full text instead of filling the gap with inference.

## Ownership Boundary

AutoSearch owns:

- scope and evidence;
- Insight and evidence-reviewed Weakness;
- related manifestations and technical bottlenecks;
- Candidate Contribution and novelty boundary;
- required data, baselines, metrics, key experiments, and falsifiers.

AutoDesign owns:

- concrete architecture;
- exact module implementation;
- losses and training schedule;
- data construction recipe;
- complete experiment matrix and execution.

Do not claim an experimental result before it exists. Use `Candidate Contribution` until real experiments support it.
