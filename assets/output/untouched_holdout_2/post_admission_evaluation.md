# Auto-Bench Blind Evaluation

- Verdict: **PASS**
- Cases: 1
- Mean primary Recall@5: 1.000
- Mean primary Recall@6: 1.000
- Mean primary MRR: 0.333
- Mean selected modeled-benchmark recall: 1.000
- Mean selected actual-benchmark precision: 1.000
- Route accuracy: 1.000

## Case Results

### holdout_002 — CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing

- Source paper: [CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing](https://arxiv.org/abs/2305.11738)
- Introduction source section: ['Introduction']
- Method source section(s): ['CRITIC: Correcting with Tool-Interactive Critiquing']
- Matcher-visible input: `assets/input/untouched_holdout_2_cases/holdout_002.json`
- Paper evidence sections: ['Free-form Question Answering', 'Mathematical Program Synthesis', 'Toxicity Reduction']
- The source identity and actual benchmarks below were revealed only after matching completed.

#### Benchmarks Used by the Paper

| Role | Benchmark | Evidence section | Auto-Bench selected | Auto-Bench rank |
|---|---|---|---:|---:|
| primary | HotpotQA | Free-form Question Answering | True | 4 |
| admitted_after_freeze | AmbigNQ | Free-form Question Answering | True | 6 |
| admitted_after_freeze | TriviaQA | Free-form Question Answering | True | 1 |
| primary | GSM8K | Mathematical Program Synthesis | True | 3 |
| admitted_after_freeze | SVAMP | Mathematical Program Synthesis | True | 5 |
| admitted_after_freeze | TabMWP | Mathematical Program Synthesis | True | 7 |
| admitted_after_freeze | RealToxicityPrompts | Toxicity Reduction | True | 2 |

#### Auto-Bench Selected Portfolio

| Rank | Benchmark | Score | Selection role | Role in source paper |
|---:|---|---:|---|---|
| 1 | TriviaQA | 0.517 | core_task_coverage | admitted_after_freeze |
| 2 | RealToxicityPrompts | 0.397 | core_task_coverage | admitted_after_freeze |
| 3 | GSM8K | 0.372 | core_task_coverage | primary |
| 4 | HotpotQA | 0.467 | explicit_suite_cardinality:knowledge_intensive_qa | primary |
| 5 | SVAMP | 0.372 | explicit_suite_cardinality:math_reasoning | admitted_after_freeze |
| 6 | AmbigNQ | 0.517 | explicit_suite_cardinality:knowledge_intensive_qa | admitted_after_freeze |
| 7 | TabMWP | 0.472 | explicit_suite_cardinality:math_reasoning | admitted_after_freeze |

#### Direct Comparison

- Selected primary matches: ['gsm8k', 'hotpotqa']
- Selected secondary matches: []
- Selected post-freeze catalog matches: ['triviaqa', 'realtoxicityprompts', 'svamp', 'ambignq', 'tabmwp']
- Primary benchmarks missing from selected portfolio: []
- Secondary benchmarks missing from selected portfolio: []
- Post-freeze catalog benchmarks missing from selected portfolio: []
- Selected recommendations not used by the paper: []
- Top-6 primary matches: ['gsm8k', 'hotpotqa']
- Recall@5 / Recall@6: 1.000 / 1.000
- Selected modeled-benchmark recall: 1.000
- Selected actual-benchmark precision: 1.000
- Route: direct_portfolio (expected direct_portfolio)
- Expected route at original freeze: base_benchmark_adaptation
- Route reason: portfolio covers 100.0% of inferred task families; weakest task-normalized selected compatibility is 0.585
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
