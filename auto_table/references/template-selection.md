# Template selection

Choose the evidence geometry first. Styling comes after the row/column decision. Templates are optional starting points, not mandatory table forms.

| Template | Use when | Identity/field treatment | Evidence axis |
|---|---|---|---|
| `benchmark-wide` | Many systems, a moderate number of dataset × metric cells | One Method column; use row groups for prior work vs ours | columns = dataset → metric |
| `family-banded-benchmark` | A dense leaderboard contains several scientifically meaningful model families | full-width family bands; optional focal-row shade; ranking may exclude reference families | columns = dataset → category/metric |
| `hierarchical-method-budget` | The same base model has several adaptation methods or budgets | Separate Model, Method, and # Trainable; suppress repeated model labels | columns = task → metric |
| `transposed-benchmark` | A small set of focal systems is evaluated on many benchmarks | systems become columns; optional pre-train-data group above them | rows = benchmark (and metric if needed) |
| `quality-efficiency` | The claim joins quality with cost, speed, memory, or parameters | keep Method at left; never collapse quality/cost to one score | columns = metric family → dataset |
| `scaled-variants` | Depth, model size, backbone, or data scale is itself part of the comparison | separate Family, Variant, Depth, and # Params | columns = benchmark → metric |
| `compact-regime-comparison` | Two to four tasks and method regimes such as prompting, finetuning, or oracle | separate Regime and Method; use whitespace between regimes | columns = task → metric |

## Orientation rule

Let `R` be the number of method variants and `C` the number of benchmark/metric combinations.

- Prefer methods-as-rows when `R >= C`, method names are long, or methods need multiple descriptor fields.
- Prefer datasets-as-rows when `C > R`, systems are few and focal, or readers need to scan one benchmark at a time.
- Do not transpose solely to avoid a width problem. First remove redundant metrics and fields that do not support the main claim.

## Identity fields versus measured fields

An identity field defines *what was run*; a measured field reports *what happened*.

- Identity: model family, method, backbone, training data, trainable parameter budget, supervision, protocol, source, scale.
- Measured: accuracy, F1, BLEU, loss, latency, memory, FLOPs, human win rate.

If changing a value could invalidate a direct comparison, display it as an identity/protocol field or state it in the正文 and internal `context_notes`. Do not overload the caption with it.

## Header order

- `dataset → metric`: best for standard multi-benchmark evaluation because a reader finishes one benchmark before moving to the next.
- `metric → dataset`: best for quality-efficiency claims because all quality values and all cost values form separate visual blocks.
- A single dataset or single metric should collapse to one header row.

## Row grouping

Use group changes only for scientifically meaningful regimes: prior work / reproduced baselines / ours; base model family; prompting / finetuning / supervised oracle. A flat table with no internal separator is valid. When grouping helps, prefer whitespace for weak subdivisions and reserve a full-width rule for a boundary that must be traceable across all metric columns. Avoid repeating the same family label on every row.

Use `family-banded-benchmark` when the group taxonomy is itself one of the first things readers must understand. A band is stronger than whitespace and should not be used for incidental source ordering.
