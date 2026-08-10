# Auto-Bench Blind Evaluation

- Verdict: **NEEDS_ITERATION**
- Cases: 5
- Mean primary Recall@5: 0.633
- Mean primary Recall@6: 0.733
- Mean primary MRR: 0.412
- Mean selected modeled-benchmark recall: 0.633
- Mean selected actual-benchmark precision: 0.300
- Route accuracy: 0.400

## Case Results

### fresh3_001 — Toolformer: Language Models Can Teach Themselves to Use Tools

- Source paper: [Toolformer: Language Models Can Teach Themselves to Use Tools](https://arxiv.org/abs/2302.04761)
- Introduction source section: ['Introduction']
- Method source section(s): ['Approach', 'Tools']
- Matcher-visible input: `assets/input/fresh_holdout_suite_003/cases/fresh3_001.json`
- Paper evidence sections: ['Experiments / Downstream Tasks / LAMA', 'Experiments / Math Datasets', 'Experiments / Question Answering', 'Experiments / Multilingual Question Answering', 'Experiments / Temporal Datasets', 'Experiments / Language Modeling']
- The source identity and actual benchmarks below were revealed only after matching completed.

#### Benchmarks Used by the Paper

| Role | Benchmark | Evidence section | Auto-Bench selected | Auto-Bench rank |
|---|---|---|---:|---:|
| primary | SVAMP | Math Datasets | False | 6 |
| primary | TriviaQA | Question Answering | True | 1 |
| unmodeled | SQuAD subset of LAMA | LAMA | False | outside catalog |
| unmodeled | Google-RE subset of LAMA | LAMA | False | outside catalog |
| unmodeled | T-REx subset of LAMA | LAMA | False | outside catalog |
| unmodeled | ASDiv | Math Datasets | False | outside catalog |
| unmodeled | MAWPS | Math Datasets | False | outside catalog |
| unmodeled | Web Questions | Question Answering | False | outside catalog |
| unmodeled | Natural Questions | Question Answering | False | outside catalog |
| unmodeled | MLQA | Multilingual Question Answering | False | outside catalog |
| unmodeled | TempLAMA | Temporal Datasets | False | outside catalog |
| unmodeled | Dateset | Temporal Datasets | False | outside catalog |
| unmodeled | WikiText | Language Modeling | False | outside catalog |
| unmodeled | CCNet language-modeling subset | Language Modeling | False | outside catalog |

#### Auto-Bench Selected Portfolio

| Rank | Benchmark | Score | Selection role | Role in source paper |
|---:|---|---:|---|---|
| 1 | TriviaQA | 0.780 | core_task_coverage | primary |
| 2 | HotpotQA | 0.747 | supplementary_triangulation:knowledge_intensive_qa | not_used_in_paper |

#### Direct Comparison

- Selected primary matches: ['triviaqa']
- Selected secondary matches: []
- Selected post-freeze catalog matches: []
- Primary benchmarks missing from selected portfolio: ['svamp']
- Secondary benchmarks missing from selected portfolio: []
- Post-freeze catalog benchmarks missing from selected portfolio: []
- Selected recommendations not used by the paper: ['hotpotqa']
- Top-6 primary matches: ['triviaqa', 'svamp']
- Recall@5 / Recall@6: 0.500 / 1.000
- Selected modeled-benchmark recall: 0.500
- Selected actual-benchmark precision: 0.500
- Route: direct_portfolio (expected base_benchmark_adaptation)
- Expected route at original freeze: base_benchmark_adaptation
- Route reason: portfolio covers 100.0% of inferred task families; weakest task-normalized selected compatibility is 0.747
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

### fresh3_002 — ProgPrompt: Generating Situated Robot Task Plans using Large Language Models

- Source paper: [ProgPrompt: Generating Situated Robot Task Plans using Large Language Models](https://arxiv.org/abs/2209.11302)
- Introduction source section: ['Introduction']
- Method source section(s): ['Our Method: ProgPrompt']
- Matcher-visible input: `assets/input/fresh_holdout_suite_003/cases/fresh3_002.json`
- Paper evidence sections: ['Experiments / Simulation Experiments', 'Experiments / Real-Robot Experiments']
- The source identity and actual benchmarks below were revealed only after matching completed.

#### Benchmarks Used by the Paper

| Role | Benchmark | Evidence section | Auto-Bench selected | Auto-Bench rank |
|---|---|---|---:|---:|
| unmodeled | VirtualHome Household Task Set | Simulation Experiments | False | outside catalog |
| unmodeled | Physical Robot Tabletop Task Set | Real-Robot Experiments | False | outside catalog |

#### Auto-Bench Selected Portfolio

| Rank | Benchmark | Score | Selection role | Role in source paper |
|---:|---|---:|---|---|
| 1 | ALFWorld | 0.777 | core_task_coverage | not_used_in_paper |

#### Direct Comparison

- Selected primary matches: []
- Selected secondary matches: []
- Selected post-freeze catalog matches: []
- Primary benchmarks missing from selected portfolio: []
- Secondary benchmarks missing from selected portfolio: []
- Post-freeze catalog benchmarks missing from selected portfolio: []
- Selected recommendations not used by the paper: ['alfworld']
- Top-6 primary matches: []
- Recall@5 / Recall@6: 1.000 / 1.000
- Selected modeled-benchmark recall: 1.000
- Selected actual-benchmark precision: 0.000
- Route: base_benchmark_adaptation (expected base_benchmark_adaptation)
- Expected route at original freeze: base_benchmark_adaptation
- Route reason: best existing match scores 0.777, but portfolio coverage is 50.0%
- Inferred task coverage: 0.500
- Missing task families: ['symbolic_reasoning']
- Synthesis required: True
- Catalog admission proposals: []

#### Human Literature Check

- [ ] Opened the source paper and verified the listed evidence sections.
- [ ] Confirmed the benchmark list actually used by the paper.
- [ ] Compared the paper benchmark list with Auto-Bench Selected and Top-6 results.
- Human judgement: MATCH / PARTIAL / MISMATCH
- Notes:

### fresh3_003 — Visual Programming: Compositional visual reasoning without training

- Source paper: [Visual Programming: Compositional visual reasoning without training](https://arxiv.org/abs/2211.11559)
- Introduction source section: ['Introduction']
- Method source section(s): ['Visual Programming']
- Matcher-visible input: `assets/input/fresh_holdout_suite_003/cases/fresh3_003.json`
- Paper evidence sections: ['Tasks / Compositional Visual Question Answering', 'Tasks / Zero-Shot Reasoning on Image Pairs', 'Tasks / Factual Knowledge Object Tagging', 'Tasks / Image Editing with Natural Language']
- The source identity and actual benchmarks below were revealed only after matching completed.

#### Benchmarks Used by the Paper

| Role | Benchmark | Evidence section | Auto-Bench selected | Auto-Bench rank |
|---|---|---|---:|---:|
| unmodeled | GQA | Compositional Visual Question Answering | False | outside catalog |
| unmodeled | NLVRv2 | Zero-Shot Reasoning on Image Pairs | False | outside catalog |
| unmodeled | Factual Knowledge Object Tagging | Factual Knowledge Object Tagging | False | outside catalog |
| unmodeled | Language-Guided Image Editing | Image Editing with Natural Language | False | outside catalog |

#### Auto-Bench Selected Portfolio

| Rank | Benchmark | Score | Selection role | Role in source paper |
|---:|---|---:|---|---|

#### Direct Comparison

- Selected primary matches: []
- Selected secondary matches: []
- Selected post-freeze catalog matches: []
- Primary benchmarks missing from selected portfolio: []
- Secondary benchmarks missing from selected portfolio: []
- Post-freeze catalog benchmarks missing from selected portfolio: []
- Selected recommendations not used by the paper: []
- Top-6 primary matches: []
- Recall@5 / Recall@6: 1.000 / 1.000
- Selected modeled-benchmark recall: 1.000
- Selected actual-benchmark precision: 0.000
- Route: new_benchmark_synthesis (expected new_benchmark_synthesis)
- Expected route at original freeze: new_benchmark_synthesis
- Route reason: no catalog task family covers the explicitly stated method domain
- Inferred task coverage: 0.000
- Missing task families: ['image_generation', 'visual_reasoning']
- Synthesis required: True
- Catalog admission proposals: []

#### Human Literature Check

- [ ] Opened the source paper and verified the listed evidence sections.
- [ ] Confirmed the benchmark list actually used by the paper.
- [ ] Compared the paper benchmark list with Auto-Bench Selected and Top-6 results.
- Human judgement: MATCH / PARTIAL / MISMATCH
- Notes:

### fresh3_004 — Program of Thoughts Prompting: Disentangling Computation from Reasoning for Numerical Reasoning Tasks

- Source paper: [Program of Thoughts Prompting: Disentangling Computation from Reasoning for Numerical Reasoning Tasks](https://arxiv.org/abs/2211.12588)
- Introduction source section: ['Introduction']
- Method source section(s): ['Program of Thoughts']
- Matcher-visible input: `assets/input/fresh_holdout_suite_003/cases/fresh3_004.json`
- Paper evidence sections: ['Experiments / Experimental Setup / Datasets']
- The source identity and actual benchmarks below were revealed only after matching completed.

#### Benchmarks Used by the Paper

| Role | Benchmark | Evidence section | Auto-Bench selected | Auto-Bench rank |
|---|---|---|---:|---:|
| primary | GSM8K | Datasets | True | 1 |
| primary | SVAMP | Datasets | True | 2 |
| primary | TabMWP | Datasets | False | 9 |
| unmodeled | AQuA | Datasets | False | outside catalog |
| unmodeled | MultiArith | Datasets | False | outside catalog |
| unmodeled | FinQA | Datasets | False | outside catalog |
| unmodeled | ConvFinQA | Datasets | False | outside catalog |
| unmodeled | TATQA | Datasets | False | outside catalog |

#### Auto-Bench Selected Portfolio

| Rank | Benchmark | Score | Selection role | Role in source paper |
|---:|---|---:|---|---|
| 1 | GSM8K | 0.625 | core_task_coverage | primary |
| 2 | SVAMP | 0.625 | supplementary_triangulation:math_reasoning,math_word_problem | primary |

#### Direct Comparison

- Selected primary matches: ['gsm8k', 'svamp']
- Selected secondary matches: []
- Selected post-freeze catalog matches: []
- Primary benchmarks missing from selected portfolio: ['tabmwp']
- Secondary benchmarks missing from selected portfolio: []
- Post-freeze catalog benchmarks missing from selected portfolio: []
- Selected recommendations not used by the paper: []
- Top-6 primary matches: ['gsm8k', 'svamp']
- Recall@5 / Recall@6: 0.667 / 0.667
- Selected modeled-benchmark recall: 0.667
- Selected actual-benchmark precision: 1.000
- Route: direct_portfolio (expected base_benchmark_adaptation)
- Expected route at original freeze: base_benchmark_adaptation
- Route reason: portfolio covers 100.0% of inferred task families; weakest task-normalized selected compatibility is 0.625
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

### fresh3_005 — Tree of Thoughts: Deliberate Problem Solving with Large Language Models

- Source paper: [Tree of Thoughts: Deliberate Problem Solving with Large Language Models](https://arxiv.org/abs/2305.10601)
- Introduction source section: ['Introduction']
- Method source section(s): ['Tree of Thoughts: Deliberate Problem Solving with LM']
- Matcher-visible input: `assets/input/fresh_holdout_suite_003/cases/fresh3_005.json`
- Paper evidence sections: ['Experiments / Game of 24', 'Experiments / Creative Writing', 'Experiments / Mini Crosswords']
- The source identity and actual benchmarks below were revealed only after matching completed.

#### Benchmarks Used by the Paper

| Role | Benchmark | Evidence section | Auto-Bench selected | Auto-Bench rank |
|---|---|---|---:|---:|
| primary | Game of 24 | Game of 24 | False | 16 |
| unmodeled | Creative Writing | Creative Writing | False | outside catalog |
| unmodeled | 5x5 Mini Crosswords | Mini Crosswords | False | outside catalog |

#### Auto-Bench Selected Portfolio

| Rank | Benchmark | Score | Selection role | Role in source paper |
|---:|---|---:|---|---|

#### Direct Comparison

- Selected primary matches: []
- Selected secondary matches: []
- Selected post-freeze catalog matches: []
- Primary benchmarks missing from selected portfolio: ['game_of_24']
- Secondary benchmarks missing from selected portfolio: []
- Post-freeze catalog benchmarks missing from selected portfolio: []
- Selected recommendations not used by the paper: []
- Top-6 primary matches: []
- Recall@5 / Recall@6: 0.000 / 0.000
- Selected modeled-benchmark recall: 0.000
- Selected actual-benchmark precision: 0.000
- Route: new_benchmark_synthesis (expected base_benchmark_adaptation)
- Expected route at original freeze: base_benchmark_adaptation
- Route reason: no catalog task family covers the explicitly stated method domain
- Inferred task coverage: 0.000
- Missing task families: ['two_strategies_to_generate_candidates_for_the_next']
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
