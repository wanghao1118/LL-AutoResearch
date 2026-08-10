# Auto-Bench Blind Evaluation

- Verdict: **NEEDS_ITERATION**
- Cases: 5
- Mean primary Recall@5: 0.500
- Mean primary Recall@6: 0.500
- Mean primary MRR: 0.319
- Mean selected modeled-benchmark recall: 0.250
- Mean selected actual-benchmark precision: 0.067
- Route accuracy: 0.200

## Case Results

### fresh_001 — Self-Refine: Iterative Refinement with Self-Feedback

- Source paper: [Self-Refine: Iterative Refinement with Self-Feedback](https://arxiv.org/abs/2303.17651)
- Introduction source section: ['Introduction']
- Method source section(s): ['Method']
- Matcher-visible input: `assets/input/fresh_holdout_suite/cases/fresh_001.json`
- Paper evidence sections: ['Evaluation', 'Appendix: Task Details']
- The source identity and actual benchmarks below were revealed only after matching completed.

#### Benchmarks Used by the Paper

| Role | Benchmark | Evidence section | Auto-Bench selected | Auto-Bench rank |
|---|---|---|---:|---:|
| unmodeled | FED | Dialogue Response Generation / Evaluation | False | outside catalog |
| unmodeled | PIE | Code Optimization | False | outside catalog |
| unmodeled | Project CodeNet | Code Readability / Experiments | False | outside catalog |
| primary | GSM8K | Math Reasoning | False | 20 |
| unmodeled | Sentiment Reversal review-passage set | Sentiment Reversal | False | outside catalog |
| unmodeled | Acronym Generation paper-curated set | Acronym Generation | False | outside catalog |
| unmodeled | CommonGen-Hard | Constrained Generation | False | outside catalog |

#### Auto-Bench Selected Portfolio

| Rank | Benchmark | Score | Selection role | Role in source paper |
|---:|---|---:|---|---|
| 1 | HumanEval | 0.853 | core_task_coverage | not_used_in_paper |
| 2 | MBPP | 0.853 | supplementary_triangulation:code_generation | not_used_in_paper |
| 3 | HumanEvalFix | 0.750 | supplementary_triangulation:code_generation | not_used_in_paper |

#### Direct Comparison

- Selected primary matches: []
- Selected secondary matches: []
- Selected post-freeze catalog matches: []
- Primary benchmarks missing from selected portfolio: ['gsm8k']
- Secondary benchmarks missing from selected portfolio: []
- Post-freeze catalog benchmarks missing from selected portfolio: []
- Selected recommendations not used by the paper: ['humaneval', 'mbpp', 'humanevalfix']
- Top-6 primary matches: []
- Recall@5 / Recall@6: 0.000 / 0.000
- Selected modeled-benchmark recall: 0.000
- Selected actual-benchmark precision: 0.000
- Route: direct_portfolio (expected new_benchmark_synthesis)
- Expected route at original freeze: new_benchmark_synthesis
- Route reason: portfolio covers 100.0% of inferred task families; weakest task-normalized selected compatibility is 0.750
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

### fresh_002 — Graph of Thoughts: Solving Elaborate Problems with Large Language Models

- Source paper: [Graph of Thoughts: Solving Elaborate Problems with Large Language Models](https://arxiv.org/abs/2308.09687)
- Introduction source section: ['Introduction']
- Method source section(s): ['Graph of Thoughts', 'Architecture']
- Matcher-visible input: `assets/input/fresh_holdout_suite/cases/fresh_002.json`
- Paper evidence sections: ['Example Use Cases', 'Evaluation']
- The source identity and actual benchmarks below were revealed only after matching completed.

#### Benchmarks Used by the Paper

| Role | Benchmark | Evidence section | Auto-Bench selected | Auto-Bench rank |
|---|---|---|---:|---:|
| unmodeled | Sorting task suite | Example Use Cases / Sorting | False | outside catalog |
| unmodeled | Set Intersection task suite | Example Use Cases / Set Operations | False | outside catalog |
| unmodeled | Keyword Counting task suite | Example Use Cases / Keyword Counting | False | outside catalog |
| unmodeled | Document Merging task suite | Example Use Cases / Document Merging | False | outside catalog |

#### Auto-Bench Selected Portfolio

| Rank | Benchmark | Score | Selection role | Role in source paper |
|---:|---|---:|---|---|
| 1 | SWE-bench | 0.833 | core_task_coverage | not_used_in_paper |

#### Direct Comparison

- Selected primary matches: []
- Selected secondary matches: []
- Selected post-freeze catalog matches: []
- Primary benchmarks missing from selected portfolio: []
- Secondary benchmarks missing from selected portfolio: []
- Post-freeze catalog benchmarks missing from selected portfolio: []
- Selected recommendations not used by the paper: ['swe_bench']
- Top-6 primary matches: []
- Recall@5 / Recall@6: 1.000 / 1.000
- Selected modeled-benchmark recall: 1.000
- Selected actual-benchmark precision: 0.000
- Route: direct_portfolio (expected new_benchmark_synthesis)
- Expected route at original freeze: new_benchmark_synthesis
- Route reason: portfolio covers 100.0% of inferred task families; weakest task-normalized selected compatibility is 0.833
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

### fresh_003 — ExpeL: LLM Agents Are Experiential Learners

- Source paper: [ExpeL: LLM Agents Are Experiential Learners](https://arxiv.org/abs/2308.10144)
- Introduction source section: ['Introduction']
- Method source section(s): ['ExpeL: An Experiential Learning Agent']
- Matcher-visible input: `assets/input/fresh_holdout_suite/cases/fresh_003.json`
- Paper evidence sections: ['Experiments / Experimental Setup', 'Transfer Learning']
- The source identity and actual benchmarks below were revealed only after matching completed.

#### Benchmarks Used by the Paper

| Role | Benchmark | Evidence section | Auto-Bench selected | Auto-Bench rank |
|---|---|---|---:|---:|
| primary | HotpotQA | Experiments / Experimental Setup | False | 9 |
| primary | ALFWorld | Experiments / Experimental Setup | True | 1 |
| primary | WebShop | Experiments / Experimental Setup | False | 4 |
| primary | FEVER | Experiments / Experimental Setup and Transfer Learning | False | 11 |

#### Auto-Bench Selected Portfolio

| Rank | Benchmark | Score | Selection role | Role in source paper |
|---:|---|---:|---|---|
| 1 | ALFWorld | 0.837 | core_task_coverage | primary |
| 2 | ScienceWorld | 0.837 | supplementary_triangulation:sequential_decision_making | not_used_in_paper |
| 3 | WebArena | 0.730 | supplementary_triangulation:sequential_decision_making | not_used_in_paper |

#### Direct Comparison

- Selected primary matches: ['alfworld']
- Selected secondary matches: []
- Selected post-freeze catalog matches: []
- Primary benchmarks missing from selected portfolio: ['hotpotqa', 'webshop', 'fever']
- Secondary benchmarks missing from selected portfolio: []
- Post-freeze catalog benchmarks missing from selected portfolio: []
- Selected recommendations not used by the paper: ['scienceworld', 'webarena']
- Top-6 primary matches: ['alfworld', 'webshop']
- Recall@5 / Recall@6: 0.500 / 0.500
- Selected modeled-benchmark recall: 0.250
- Selected actual-benchmark precision: 0.333
- Route: direct_portfolio (expected direct_portfolio)
- Expected route at original freeze: direct_portfolio
- Route reason: portfolio covers 100.0% of inferred task families; weakest task-normalized selected compatibility is 0.730
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

### fresh_004 — Reasoning with Language Model is Planning with World Model

- Source paper: [Reasoning with Language Model is Planning with World Model](https://arxiv.org/abs/2305.14992)
- Introduction source section: ['Introduction']
- Method source section(s): ['Reasoning via Planning']
- Matcher-visible input: `assets/input/fresh_holdout_suite/cases/fresh_004.json`
- Paper evidence sections: ['Plan Generation', 'Math Reasoning', 'Logical Reasoning']
- The source identity and actual benchmarks below were revealed only after matching completed.

#### Benchmarks Used by the Paper

| Role | Benchmark | Evidence section | Auto-Bench selected | Auto-Bench rank |
|---|---|---|---:|---:|
| unmodeled | Blocksworld | Plan Generation | False | outside catalog |
| primary | GSM8K | Math Reasoning | False | 2 |
| unmodeled | PrOntoQA | Logical Reasoning | False | outside catalog |

#### Auto-Bench Selected Portfolio

| Rank | Benchmark | Score | Selection role | Role in source paper |
|---:|---|---:|---|---|
| 1 | Game of 24 | 0.565 | core_task_coverage | not_used_in_paper |

#### Direct Comparison

- Selected primary matches: []
- Selected secondary matches: []
- Selected post-freeze catalog matches: []
- Primary benchmarks missing from selected portfolio: ['gsm8k']
- Secondary benchmarks missing from selected portfolio: []
- Post-freeze catalog benchmarks missing from selected portfolio: []
- Selected recommendations not used by the paper: ['game_of_24']
- Top-6 primary matches: ['gsm8k']
- Recall@5 / Recall@6: 1.000 / 1.000
- Selected modeled-benchmark recall: 0.000
- Selected actual-benchmark precision: 0.000
- Route: direct_portfolio (expected base_benchmark_adaptation)
- Expected route at original freeze: base_benchmark_adaptation
- Route reason: portfolio covers 100.0% of inferred task families; weakest task-normalized selected compatibility is 0.565
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

### fresh_005 — Chameleon: Plug-and-Play Compositional Reasoning with Large Language Models

- Source paper: [Chameleon: Plug-and-Play Compositional Reasoning with Large Language Models](https://arxiv.org/abs/2304.09842)
- Introduction source section: ['Introduction']
- Method source section(s): ['General Framework', 'Module Inventory', 'Applications']
- Matcher-visible input: `assets/input/fresh_holdout_suite/cases/fresh_005.json`
- Paper evidence sections: ['Applications of Chameleon', 'Science Question Answering', 'Tabular Mathematical Reasoning', 'Experiments']
- The source identity and actual benchmarks below were revealed only after matching completed.

#### Benchmarks Used by the Paper

| Role | Benchmark | Evidence section | Auto-Bench selected | Auto-Bench rank |
|---|---|---|---:|---:|
| unmodeled | ScienceQA | Applications / Science Question Answering | False | outside catalog |
| primary | TabMWP | Applications / Tabular Mathematical Reasoning | False | 23 |

#### Auto-Bench Selected Portfolio

| Rank | Benchmark | Score | Selection role | Role in source paper |
|---:|---|---:|---|---|
| 1 | HumanEval | 0.480 | core_task_coverage | not_used_in_paper |
| 2 | HotpotQA | 0.467 | core_task_coverage | not_used_in_paper |
| 3 | Game of 24 | 0.447 | core_task_coverage | not_used_in_paper |
| 4 | MBPP | 0.480 | supplementary_triangulation:code_generation | not_used_in_paper |
| 5 | HumanEvalFix | 0.377 | supplementary_triangulation:code_generation | not_used_in_paper |

#### Direct Comparison

- Selected primary matches: []
- Selected secondary matches: []
- Selected post-freeze catalog matches: []
- Primary benchmarks missing from selected portfolio: ['tabmwp']
- Secondary benchmarks missing from selected portfolio: []
- Post-freeze catalog benchmarks missing from selected portfolio: []
- Selected recommendations not used by the paper: ['humaneval', 'hotpotqa', 'game_of_24', 'mbpp', 'humanevalfix']
- Top-6 primary matches: []
- Recall@5 / Recall@6: 0.000 / 0.000
- Selected modeled-benchmark recall: 0.000
- Selected actual-benchmark precision: 0.000
- Route: direct_portfolio (expected base_benchmark_adaptation)
- Expected route at original freeze: base_benchmark_adaptation
- Route reason: portfolio covers 100.0% of inferred task families; weakest task-normalized selected compatibility is 0.590
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
