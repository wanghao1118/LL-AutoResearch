# Matcher-visible input schema

Use exactly these fields:

```json
{
  "case_id": "paper_or_method_id",
  "introduction": "Complete Introduction text with paper identity and benchmark names removed for blind recovery.",
  "method": "Complete Method text with paper identity and benchmark names removed for blind recovery.",
  "constraints": {
    "compute": "optional compute budget",
    "data_access": "optional access constraints",
    "target_setting": "optional deployment setting"
  }
}
```

## Rules

- Require non-empty `case_id`, `introduction`, and `method` strings.
- Keep full method details needed to infer tasks, modalities, interactions, outputs, environments, and metrics.
- Exclude title, authors, paper ID, benchmark names, result numbers, experiment tables, and benchmark-specific split labels in blind mode.
- Put user constraints only in `constraints`; do not insert hidden benchmark labels there.
- Preserve the sealed input JSON beside the plan for provenance.
