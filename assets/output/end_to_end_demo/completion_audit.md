# Auto-Bench Completion Audit

- Status: **AUTOMATED_LITERATURE_VALIDATION_NEEDS_ITERATION**
- Machine workflow ready: **True**
- Automatic validation complete: **True**
- Automatic validation passed: **False**
- Human submission required: **False**

## Machine checks

### Introduction and Method only, with hidden labels isolated

- Status: **PASS**
- Evidence:
```json
{
  "case_count": 3,
  "all_leakage_checks_passed": true,
  "any_matcher_loaded_hidden_labels": false,
  "run_manifest": "assets/output/blind_runs/run_manifest.json"
}
```

### Automatic benchmark search, ranking, and portfolio selection

- Status: **PASS**
- Evidence:
```json
{
  "case_count": 3,
  "mean_primary_recall_at_5": 0.9166666666666666,
  "mean_primary_recall_at_6": 1.0,
  "mean_primary_mrr": 0.8333333333333334,
  "mean_selected_modeled_recall": 1.0,
  "mean_selected_actual_precision": 0.7222222222222222,
  "route_accuracy": 1.0,
  "all_leakage_checks_passed": true,
  "any_matcher_loaded_hidden_labels": false
}
```

### Live literature search with typed catalog-admission isolation

- Status: **PASS**
- Evidence:
```json
{
  "search_hit_count": 22,
  "catalog_admission_proposal_count": 9,
  "all_proposals_excluded_from_selection": true
}
```

### Direct, base-adaptation, and new-synthesis routes

- Status: **PASS**
- Evidence:
```json
{
  "direct": {
    "route": "direct_portfolio",
    "synthesis_status": "NOT_REQUIRED"
  },
  "base_adaptation": {
    "route": "base_benchmark_adaptation",
    "synthesis_status": "DRAFTS_READY_FOR_HUMAN_REVIEW"
  },
  "new_synthesis": {
    "route": "new_benchmark_synthesis",
    "synthesis_status": "BASE_RECORDS_REQUIRED"
  },
  "new_synthesis_online": {
    "route": "new_benchmark_synthesis",
    "synthesis_status": "BASE_RECORDS_REQUIRED"
  }
}
```

### Executable synthesis with deterministic provenance verification

- Status: **PASS**
- Evidence:
```json
[
  {
    "transformation": "interaction_wrapper",
    "records": 2,
    "verification_status": "PASS",
    "verification": "assets/output/end_to_end_demo/base_adaptation/synthesis/interaction_wrapper.verification.json"
  },
  {
    "transformation": "compositional_recombination",
    "records": 1,
    "verification_status": "PASS",
    "verification": "assets/output/end_to_end_demo/base_adaptation/synthesis/compositional_recombination.verification.json"
  },
  {
    "transformation": "counterfactual_perturbation",
    "records": 2,
    "verification_status": "PASS",
    "verification": "assets/output/end_to_end_demo/base_adaptation/synthesis/counterfactual_perturbation.verification.json"
  }
]
```

### Newest fresh-suite matcher freeze and worker isolation

- Status: **PASS**
- Evidence:
```json
{
  "suite_id": "fresh_holdout_suite_003",
  "case_count": 5,
  "matcher_frozen_file_sizes_unchanged": true,
  "all_sandboxes_excluded_hidden_labels": true,
  "meta_agent_inspection_caveat": "meta-agent inspection occurred only after matcher and paper selection freeze; no matcher file changed and workers received no experiment content"
}
```

## Authoritative fresh automatic review

```json
{
  "artifact": "assets/output/automatic_literature_review/fresh_holdout_suite_003.json",
  "status": "AUTOMATED_LITERATURE_AUDIT_MISMATCH",
  "evidence_class": "fresh_holdout",
  "case_count": 5,
  "decision_counts": {
    "MATCH": 0,
    "PARTIAL": 4,
    "MISMATCH": 1
  },
  "all_source_evidence_complete": true,
  "all_blind_checks_passed": true
}
```

## Latest feedback regression

```json
{
  "artifact": "assets/output/automatic_literature_review/fresh_holdout_suite_003_feedback_v3.json",
  "status": "AUTOMATED_LITERATURE_AUDIT_PARTIAL",
  "evidence_class": "feedback_regression",
  "case_count": 5,
  "decision_counts": {
    "MATCH": 3,
    "PARTIAL": 2,
    "MISMATCH": 0
  },
  "all_source_evidence_complete": true,
  "all_blind_checks_passed": true
}
```
