# Auto-Bench Blind Evaluation

- Verdict: **NEEDS_ITERATION**
- Cases: 1
- Mean primary Recall@5: 0.250
- Mean primary Recall@6: 0.500
- Mean primary MRR: 0.333
- Mean selected modeled-benchmark recall: 0.750
- Mean selected actual-benchmark precision: 0.600
- Route accuracy: 1.000

## Case Results

### holdout_001 — Language Agent Tree Search Unifies Reasoning Acting and Planning in Language Models

- Source paper: [Language Agent Tree Search Unifies Reasoning Acting and Planning in Language Models](https://arxiv.org/abs/2310.04406)
- Introduction source section: ['Introduction']
- Method source section(s): ['Unifying Reasoning, Acting, and Planning']
- Matcher-visible input: `assets/input/untouched_holdout_cases/holdout_001.json`
- Paper evidence sections: ['HotPotQA', 'Programming', 'WebShop', 'Ablation Study and Additional Analysis']
- The source identity and actual benchmarks below were revealed only after matching completed.

#### Benchmarks Used by the Paper

| Role | Benchmark | Evidence section | Auto-Bench selected | Auto-Bench rank |
|---|---|---|---:|---:|
| primary | HotpotQA | HotPotQA | False | 15 |
| primary | HumanEval | Programming | True | 6 |
| primary | MBPP | Programming | True | 10 |
| primary | WebShop | WebShop | True | 3 |
| unmodeled | Game of 24 | Ablation Study and Additional Analysis | False | outside catalog |

#### Auto-Bench Selected Portfolio

| Rank | Benchmark | Score | Selection role | Role in source paper |
|---:|---|---:|---|---|
| 1 | WebArena | 0.970 | core_task_coverage | not_used_in_paper |
| 6 | HumanEval | 0.593 | core_task_coverage | primary |
| 2 | Mind2Web | 0.937 | supplementary_triangulation:web_navigation | not_used_in_paper |
| 3 | WebShop | 0.893 | supplementary_triangulation:sequential_decision_making | primary |
| 10 | MBPP | 0.593 | supplementary_triangulation:code_generation | primary |

#### Direct Comparison

- Selected primary matches: ['humaneval', 'webshop', 'mbpp']
- Selected secondary matches: []
- Primary benchmarks missing from selected portfolio: ['hotpotqa']
- Secondary benchmarks missing from selected portfolio: []
- Selected recommendations not used by the paper: ['webarena', 'mind2web']
- Top-6 primary matches: ['webshop', 'humaneval']
- Recall@5 / Recall@6: 0.250 / 0.500
- Selected modeled-benchmark recall: 0.750
- Selected actual-benchmark precision: 0.600
- Route: direct_portfolio (expected direct_portfolio)

#### Human Literature Check

- [ ] Opened the source paper and verified the listed evidence sections.
- [ ] Confirmed the benchmark list actually used by the paper.
- [ ] Compared the paper benchmark list with Auto-Bench Selected and Top-6 results.
- Human judgement: MATCH / PARTIAL / MISMATCH
- Notes:

## Integrity Checks

- All input leakage scans passed: True
- Matcher loaded hidden labels: False
- Gold labels were opened only by this post-run evaluator.
- This source-revealed report is the intended human audit surface.
