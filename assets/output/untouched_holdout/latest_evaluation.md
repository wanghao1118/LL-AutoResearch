# Auto-Bench Blind Evaluation

- Verdict: **PASS**
- Cases: 1
- Mean primary Recall@5: 1.000
- Mean primary Recall@6: 1.000
- Mean primary MRR: 1.000
- Mean selected modeled-benchmark recall: 1.000
- Mean selected actual-benchmark precision: 1.000
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
| primary | HotpotQA | HotPotQA | True | 3 |
| primary | HumanEval | Programming | True | 4 |
| primary | MBPP | Programming | True | 5 |
| primary | WebShop | WebShop | True | 1 |
| admitted_after_freeze | Game of 24 | Ablation Study and Additional Analysis | True | 2 |

#### Auto-Bench Selected Portfolio

| Rank | Benchmark | Score | Selection role | Role in source paper |
|---:|---|---:|---|---|
| 1 | WebShop | 0.761 | core_task_coverage | primary |
| 2 | Game of 24 | 0.429 | core_task_coverage | admitted_after_freeze |
| 3 | HotpotQA | 0.424 | core_task_coverage | primary |
| 4 | HumanEval | 0.387 | core_task_coverage | primary |
| 5 | MBPP | 0.387 | supplementary_triangulation:code_generation | primary |

#### Direct Comparison

- Selected primary matches: ['webshop', 'hotpotqa', 'humaneval', 'mbpp']
- Selected secondary matches: []
- Selected post-freeze catalog matches: ['game_of_24']
- Primary benchmarks missing from selected portfolio: []
- Secondary benchmarks missing from selected portfolio: []
- Post-freeze catalog benchmarks missing from selected portfolio: []
- Selected recommendations not used by the paper: []
- Top-6 primary matches: ['webshop', 'hotpotqa', 'humaneval', 'mbpp']
- Recall@5 / Recall@6: 1.000 / 1.000
- Selected modeled-benchmark recall: 1.000
- Selected actual-benchmark precision: 1.000
- Route: direct_portfolio (expected direct_portfolio)
- Expected route at original freeze: direct_portfolio
- Route reason: portfolio covers 100.0% of inferred task families; weakest task-normalized selected compatibility is 0.643
- Inferred task coverage: 1.000
- Missing task families: []
- Synthesis required: False
- Catalog admission proposals: []

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
