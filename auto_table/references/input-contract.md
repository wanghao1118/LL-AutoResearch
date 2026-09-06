# Input contract

The generator accepts CSV, TSV, JSON, and JSONL. Multiple files may be passed together.

## Long format

Required fields:

```text
method, dataset, metric, value
```

`method` is copied verbatim into the table. The loader also accepts `model`, `system`, or `approach` as the identity field. When a file contains several candidates, select the authoritative one explicitly:

```json
{"input": {"method_field": "official_method_name"}}
```

The generator does not synthesize an official name from filenames, folder names, paper titles, claims, families, or other metadata. It records the chosen input field and source file in `manifest.json.method_identity`.

Optional fields:

```text
seed/run/run_id/fold, setting, group
```

Template-specific identity fields may include:

```text
model, family, backbone, trainable_params, params, depth,
pretrain_data, training_data, regime, protocol, source_type, extra_data
```

## Wide format

Each row is one run and numeric metric columns are pivoted automatically. If the file also contains numeric metadata such as epoch or parameter count, declare metrics explicitly:

```json
{"input": {"metric_columns": ["accuracy", "f1", "latency_ms"]}}
```

## Nested JSON

The supported nesting is:

```text
method → dataset → metric → scalar or list-of-runs
```

Use tabular input instead when model/method/budget fields must remain separate.

## Reported summaries

When only an authoritative aggregate is available, use long-format rows with:

```text
method,dataset,metric,mean,sd,n
```

`sd` may be blank for a singleton or a source that reports only a point estimate. These rows are recorded as `reported_summary`; their underlying values and run IDs remain empty, and the pipeline never synthesizes pseudo-runs. A reported summary cannot share a table cell with raw observations or another summary.

## Scientific semantics

- Repeated values with distinct run IDs are aggregated with arithmetic mean and sample SD.
- Duplicate run IDs inside one method/dataset/setting/metric cell are rejected.
- A singleton stays a scalar; no uncertainty is inferred.
- Pre-aggregated `mean`, `sd`, and `n` are accepted only when explicitly reported and retain summary-only lineage.
- Missing cells remain missing and render as `--`.
- Metric direction should be explicit. Name-based inference emits a warning and is not equivalent to author confirmation.
- Published values and newly reproduced values should use a `source_type` or `group` field and an explanatory note.
- Family-banded layouts read the `group` field directly. The renderer never infers families from method names. Outside an explicitly grouped layout, a `group` field remains metadata and does not automatically add a visible separator.
- Common descriptor fields are preserved automatically. If two aggregates differ on an identity/protocol field that the chosen layout does not display, generation fails instead of silently overwriting one result; add that field to `layout.row_fields`, `layout.column_fields`, or `column_group_field`.
