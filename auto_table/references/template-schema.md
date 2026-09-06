# Template and config schema

Templates are JSON objects in `auto_table/templates/`. User config is deep-merged over the selected template.

```json
{
  "template_id": "hierarchical-method-budget",
  "table_type": "main_tradeoff",
  "focal_methods": ["Ours"],
  "title": "Main results",
  "description": "This table compares the displayed adaptation methods across the selected tasks. Its purpose is to assess quality under different trainable-parameter budgets.",
  "label": "tab:main",
  "claim": "The adaptation method improves quality at lower trainable-parameter cost.",
  "input": {"metric_columns": ["accuracy"]},
  "layout": {
    "orientation": "methods_rows",
    "row_fields": [
      {"key": "model", "label": "Model", "suppress_repeat": true, "separator": true},
      {"key": "method", "label": "Method"},
      {"key": "trainable_params", "label": "# Trainable"}
    ],
    "column_order": ["dataset", "metric"]
  },
  "metrics": {
    "accuracy": {"label": "Acc.", "direction": "max", "unit": "%", "precision": 1, "priority": 1}
  },
  "selection": {
    "methods": ["Full FT", "Adapter", "Ours"],
    "datasets": ["MNLI", "SST-2"],
    "metrics": ["accuracy"],
    "max_columns": 8
  },
  "context_notes": ["All methods use the same backbone and evaluation protocol."]
}
```

`description` is written to `description.txt`. Prefer two or three compact sentences that identify the displayed evidence and its purpose in the paper. It is separate from the one-sentence caption and is never rendered below the table.

`table_type` selects the scientific-role strategy; `template_id` selects the row/column geometry. See [table types](table-types.md). `focal_methods` must use exact method names from the input and is required for claim-bearing main-table types.

## Layout fields

- `orientation`: `methods_rows` or `datasets_rows`.
- `row_fields`: identity columns on the left. `suppress_repeat` blanks repeated labels; `separator` marks a semantic boundary when the value changes. Its visual treatment is controlled by `style.row_separator_style`.
- `column_order`: `dataset, metric` or `metric, dataset` for methods-as-rows.
- `column_fields`: system label fields for datasets-as-rows.
- `column_group_field`: optional field such as `pretrain_data` rendered above system columns.
- `input.method_field`: optional authoritative method-name column. Values are copied verbatim; this option selects a field, not a rename mapping.

## Comparison scope

Use `comparison` to define which displayed systems participate in best/second-best ranking:

```json
{
  "comparison": {
    "rank_exclude_groups": ["Frontier Proprietary Models"],
    "rank_scope_label": "non-proprietary systems"
  }
}
```

`rank_include_groups`, `rank_include_methods`, and `rank_exclude_methods` are also supported. `rank_scope_label` is retained in the semantic spec for正文 writing; the concise caption does not expand it automatically.

## Visual hierarchy

```json
{
  "style": {
    "row_group_style": "band",
    "group_band_color": "EFEFEF",
    "highlight_methods": ["Ours"],
    "highlight_color": "E8F1FF",
    "fit_width": true,
    "font_size": "scriptsize",
    "tabcolsep": 2.5
  }
}
```

Colors are six-digit RGB hex values. `fit_width` uses `graphicx`; bands and row highlights use `xcolor` with the `table` option. `row_separator_style` accepts `space` (the default) or `rule`; use `rule` when fields marked with `separator` define visually important families or regimes.

`missing_marker` defaults to `--`; set it to `N/A` only when missing cells are scientifically not applicable or unsupported. Record its meaning in `context_notes` for正文 writing rather than adding prose below the table.

`group` metadata does not create separators by default. Set `row_group_style: "band"` for explicit full-width bands, or set `separate_row_groups: true` together with `row_separator_style: "space"` or `"rule"`. Fields marked with `separator: true` can still create whitespace/rules when their value changes. Horizontal rules are optional, not a success criterion.

Even with `row_group_style: "band"`, bands appear only when at least two groups each contain at least two displayed methods. If only one group qualifies, the entire body is flattened. This prevents singleton focal/reference groups and lone residual categories from consuming redundant classification rows.

Metric `direction` remains required for numerical semantics. Set `show_direction: false` for descriptive quantities such as category counts or failure rates where an up/down arrow would falsely imply desirability.

## Auxiliary deltas

Preserve the primary value while adding a parenthesized absolute or relative change:

```json
{
  "auxiliary": {
    "delta": {
      "baseline": {"method": "Strong Baseline"},
      "targets": [{"method": "Ours"}],
      "kind": "absolute",
      "precision": 1
    }
  }
}
```

Selectors may use any displayed identity field. The baseline must match exactly one row; ambiguity is an error. `kind` is `absolute` or `relative_percent`. Record the baseline and delta meaning in正文 or `context_notes`; the generated caption remains concise.

The renderer treats the delta as a secondary subcell. It reserves that subcell across every row of each affected metric column, including blank slots for rows without deltas, so the primary measurements remain aligned.

## Selection and compression

Lists in `selection` filter and order the corresponding dimension. `max_columns` is optional; when used, metric `priority` chooses which columns stay in the main table. Every removed column is recorded in `manifest.json.omitted_columns`.
