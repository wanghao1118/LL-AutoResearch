# Auto-Bench Blind Evaluation

- Verdict: **PASS**
- Cases: 1
- Mean primary Recall@5: 1.000
- Mean primary Recall@6: 1.000
- Mean primary MRR: 1.000
- Mean selected modeled-benchmark recall: 1.000
- Mean selected actual-benchmark precision: 0.667
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
| primary | HotpotQA | Free-form Question Answering | True | 1 |
| unmodeled | AmbigNQ | Free-form Question Answering | False | outside catalog |
| unmodeled | TriviaQA | Free-form Question Answering | False | outside catalog |
| primary | GSM8K | Mathematical Program Synthesis | True | 3 |
| unmodeled | SVAMP | Mathematical Program Synthesis | False | outside catalog |
| unmodeled | TabMWP | Mathematical Program Synthesis | False | outside catalog |
| unmodeled | RealToxicityPrompts | Toxicity Reduction | False | outside catalog |

#### Auto-Bench Selected Portfolio

| Rank | Benchmark | Score | Selection role | Role in source paper |
|---:|---|---:|---|---|
| 1 | HotpotQA | 0.680 | core_task_coverage | primary |
| 2 | ToolBench | 0.587 | core_task_coverage | not_used_in_paper |
| 3 | GSM8K | 0.585 | core_task_coverage | primary |

#### Direct Comparison

- Selected primary matches: ['hotpotqa', 'gsm8k']
- Selected secondary matches: []
- Primary benchmarks missing from selected portfolio: []
- Secondary benchmarks missing from selected portfolio: []
- Selected recommendations not used by the paper: ['toolbench']
- Top-6 primary matches: ['hotpotqa', 'gsm8k']
- Recall@5 / Recall@6: 1.000 / 1.000
- Selected modeled-benchmark recall: 1.000
- Selected actual-benchmark precision: 0.667
- Route: base_benchmark_adaptation (expected base_benchmark_adaptation)
- Route reason: best existing match scores 0.680, but portfolio coverage is 75.0%
- Inferred task coverage: 0.750
- Missing task families: ['toxicity_reduction']
- Synthesis required: True
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
