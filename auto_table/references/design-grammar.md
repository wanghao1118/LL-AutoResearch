# Main-table design grammar

A strong main table is a compact scientific argument. Design it in this order; visual styling is the final layer, not the first.

Before rendering, record a compact visual plan with five decisions:

```text
rows       exact identity fields and order
groups     none / whitespace / rules / bands, with the semantic reason
columns    evidence hierarchy and reading direction
values     primary statistic plus any aligned auxiliary slot
emphasis   focal row and valid ranking/significance scope
```

Evaluate these decisions together. Each visible channel must add information that another channel does not already communicate. A group name in the data is evidence available to the planner, not an instruction to draw a group row.

## 1. Comparison contract

Write down the valid ranking universe before arranging cells.

- Which rows share the same task, data, supervision, backbone, budget, and evaluation protocol?
- Are proprietary systems, oracles, ensembles, literature-only results, or incompatible settings shown only as references?
- Is best/second-best computed globally, within a method family, or among open/reproducible systems?
- What is the explicit baseline for every delta, speedup, or relative improvement?

Display a scientifically useful reference even when it is excluded from ranking, and state that exclusion in the正文 or internal `context_notes`.

## 2. Row topology

The left side answers "what exactly was run?"

- Use separate identity columns when model, method, backbone, data, budget, protocol, or source changes comparability.
- Grouping is optional. Do not introduce a taxonomy merely because the input has an ordering or because a template supports groups.
- Use full-width family bands only when readers primarily need to scan categories such as proprietary / general / multimodal / agentic systems.
- Treat full-width bands as a parallel classification system: require at least two categories, each with at least two displayed methods. If only one category survives that test, flatten the entire body. A singleton category does not justify an extra row; render the method directly, optionally with focal-row shading.
- Match separator strength to the semantic boundary: no separator for an already clear flat list, whitespace for a weak subdivision, a full-width midrule when a regime change must remain visible across numeric columns, and a band when the taxonomy is itself a primary reading axis.
- When repeated family/regime labels are suppressed, use a rule or band only if readers otherwise cannot trace a scientifically important boundary. Horizontal rules are not a default requirement.
- Use a restrained focal-row shade only to locate the proposed system. It must not substitute for numerical emphasis.

## 3. Column topology

The right side answers "what happened?"

- `dataset → metric` supports benchmark-by-benchmark reading.
- `metric family → dataset` supports quality-efficiency or clean-robustness trade-offs.
- A manuscript table may instead use semantic metric families when they are explicit in the evidence: for example, two morphology metrics, two statement metrics, and two task/mechanism metrics; or two classification metrics and two mechanism metrics. These are examples of the grouping test, not fixed names.
- Add a top-level metric tier only when at least two categories each span two or more adjacent leaf metrics. Keep the header flat when categories would be ambiguous, overlap, reorder the scientific scan path, or leave singleton pseudo-groups.
- Keep category labels short and neutral. A group heading organizes measurements; it must not introduce a stronger scientific claim than the leaf metrics support.
- Put `Avg.` at the end of a benchmark block only when its macro/micro/weighted definition is known.
- Keep quality, absolute cost, and relative speedup separate. Do not collapse them into a decorative composite score.

## 4. Value grammar

Choose one primary representation per evidence type:

```text
87.4                 point estimate
87.4 ± 0.3           mean ± declared SD/SE
87.4 [86.9, 87.9]    estimate + confidence interval
87.4 (+2.1)          absolute result + absolute-point delta
87.4 (+2.5%)         absolute result + relative delta
1.43×                ratio or speedup
```

Never infer uncertainty or significance. Define precision and unit per metric. Rank on unrounded values, then format. Missing, not applicable, and failed experiments are different states; the current renderer reserves `--` for unavailable evidence.

Auxiliary values are optional annotations, not peers of the primary measurement. When any row in a metric column shows a delta or interval annotation, reserve the same secondary slot for that whole column (blank in rows without one). The primary values must keep a shared alignment axis; adding information must not shift the focal row's measurements sideways.

## 5. Emphasis grammar

Recommended default:

- focal-row shade: locate the proposed method;
- bold: best within the declared ranking universe;
- underline: second-best within that universe;
- `*`, `†`, `‡`: only for explicitly documented significance, provenance, or protocol differences.

Ties share a marker. Color is secondary and the table must remain intelligible in grayscale.

A focal-row shade is one continuous semantic channel, not a collection of highlighted cells. It must cover the identity columns, every evidence column, and the spacing between them. In LaTeX, prefer a single `\rowcolor` applied before the first cell and a column layout that paints ordinary intercolumn padding. Avoid repeated `\cellcolor` and verify that `tabular*` stretch glue does not split the band into blocks. If the rasterized PDF shows gaps, change the column specification or fitting strategy before delivery.

## 6. Caption contract

Use one concise identifying sentence, normally `Main results on ...`, `Ablation results`, or another direct description of the table's subject. Do not turn the caption into an experimental-method paragraph. Metric definitions, aggregation, run count, compared systems, protocol, ranking scope, missingness, caveats, and interpretation belong in the paper body unless the user explicitly requests a necessary legend.

Do not render prose or notes below the table. Preserve useful author context in internal `context_notes` so a writing system can place it in the正文 later. The caption and table are the only user-facing deliverables; provenance manifests and normalized data exist to verify them.

## 7. Visual QA

Compile the actual LaTeX and compare it with the visual plan. Check that group bands occur only as two or more meaningful parallel categories, no orphan band remains after singleton suppression, metric groups each span at least two genuinely related adjacent metrics, focal shading is continuous across the complete row and does not hide rules, multi-level headers align with their evidence columns, primary numbers share an alignment axis, the table has no prose below its bottom rule, and the scan path remains clear in grayscale.
