# Auto-Bench Blind Evaluation

- Verdict: **NEEDS_ITERATION**
- Cases: 5
- Mean primary Recall@5: 1.000
- Mean primary Recall@6: 1.000
- Mean primary MRR: 0.600
- Mean selected modeled-benchmark recall: 0.900
- Mean selected actual-benchmark precision: 0.500
- Route accuracy: 1.000

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
| primary | SVAMP | Math Datasets | False | 4 |
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
| 1 | TriviaQA | 0.620 | core_task_coverage | primary |
| 2 | GSM8K | 0.450 | core_task_coverage | not_used_in_paper |

#### Direct Comparison

- Selected primary matches: ['triviaqa']
- Selected secondary matches: []
- Selected post-freeze catalog matches: []
- Primary benchmarks missing from selected portfolio: ['svamp']
- Secondary benchmarks missing from selected portfolio: []
- Post-freeze catalog benchmarks missing from selected portfolio: []
- Selected recommendations not used by the paper: ['gsm8k']
- Top-6 primary matches: ['triviaqa', 'svamp']
- Recall@5 / Recall@6: 1.000 / 1.000
- Selected modeled-benchmark recall: 0.500
- Selected actual-benchmark precision: 0.500
- Route: base_benchmark_adaptation (expected base_benchmark_adaptation)
- Expected route at original freeze: base_benchmark_adaptation
- Route reason: best existing match scores 0.620, but portfolio coverage is 50.0%
- Inferred task coverage: 0.500
- Missing task families: ['language_modeling', 'tool_augmented_nlp']
- Synthesis required: True
- Catalog admission proposals: []

#### Automatic Literature Check

- Source evidence terms are verified before the gold record is admitted.
- `autobench auto-review` compares paper benchmarks, task families, selected portfolio, and route.
- Output decisions are MATCH / PARTIAL / MISMATCH with typed optimization errors.
- Human submission required: False.

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
- Missing task families: ['robot_manipulation']
- Synthesis required: True
- Catalog admission proposals: []

#### Automatic Literature Check

- Source evidence terms are verified before the gold record is admitted.
- `autobench auto-review` compares paper benchmarks, task families, selected portfolio, and route.
- Output decisions are MATCH / PARTIAL / MISMATCH with typed optimization errors.
- Human submission required: False.

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
- Missing task families: ['image_editing', 'visual_reasoning']
- Synthesis required: True
- Catalog admission proposals: []

#### Automatic Literature Check

- Source evidence terms are verified before the gold record is admitted.
- `autobench auto-review` compares paper benchmarks, task families, selected portfolio, and route.
- Output decisions are MATCH / PARTIAL / MISMATCH with typed optimization errors.
- Human submission required: False.

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
| primary | GSM8K | Datasets | True | 2 |
| primary | SVAMP | Datasets | True | 3 |
| primary | TabMWP | Datasets | True | 1 |
| unmodeled | AQuA | Datasets | False | outside catalog |
| unmodeled | MultiArith | Datasets | False | outside catalog |
| unmodeled | FinQA | Datasets | False | outside catalog |
| unmodeled | ConvFinQA | Datasets | False | outside catalog |
| unmodeled | TATQA | Datasets | False | outside catalog |

#### Auto-Bench Selected Portfolio

| Rank | Benchmark | Score | Selection role | Role in source paper |
|---:|---|---:|---|---|
| 1 | TabMWP | 0.845 | core_task_coverage | primary |
| 2 | GSM8K | 0.638 | declared_suite_breadth:math_reasoning | primary |
| 3 | SVAMP | 0.638 | declared_suite_breadth:math_word_problem | primary |

#### Direct Comparison

- Selected primary matches: ['tabmwp', 'gsm8k', 'svamp']
- Selected secondary matches: []
- Selected post-freeze catalog matches: []
- Primary benchmarks missing from selected portfolio: []
- Secondary benchmarks missing from selected portfolio: []
- Post-freeze catalog benchmarks missing from selected portfolio: []
- Selected recommendations not used by the paper: []
- Top-6 primary matches: ['tabmwp', 'gsm8k', 'svamp']
- Recall@5 / Recall@6: 1.000 / 1.000
- Selected modeled-benchmark recall: 1.000
- Selected actual-benchmark precision: 1.000
- Route: base_benchmark_adaptation (expected base_benchmark_adaptation)
- Expected route at original freeze: base_benchmark_adaptation
- Route reason: best existing match scores 0.845, but portfolio coverage is 75.0%
- Inferred task coverage: 0.750
- Missing task families: ['financial_numerical_qa']
- Synthesis required: True
- Catalog admission proposals: []

#### Automatic Literature Check

- Source evidence terms are verified before the gold record is admitted.
- `autobench auto-review` compares paper benchmarks, task families, selected portfolio, and route.
- Output decisions are MATCH / PARTIAL / MISMATCH with typed optimization errors.
- Human submission required: False.

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
| primary | Game of 24 | Game of 24 | True | 1 |
| unmodeled | Creative Writing | Creative Writing | False | outside catalog |
| unmodeled | 5x5 Mini Crosswords | Mini Crosswords | False | outside catalog |

#### Auto-Bench Selected Portfolio

| Rank | Benchmark | Score | Selection role | Role in source paper |
|---:|---|---:|---|---|
| 1 | Game of 24 | 0.565 | core_task_coverage | primary |

#### Direct Comparison

- Selected primary matches: ['game_of_24']
- Selected secondary matches: []
- Selected post-freeze catalog matches: []
- Primary benchmarks missing from selected portfolio: []
- Secondary benchmarks missing from selected portfolio: []
- Post-freeze catalog benchmarks missing from selected portfolio: []
- Selected recommendations not used by the paper: []
- Top-6 primary matches: ['game_of_24']
- Recall@5 / Recall@6: 1.000 / 1.000
- Selected modeled-benchmark recall: 1.000
- Selected actual-benchmark precision: 1.000
- Route: base_benchmark_adaptation (expected base_benchmark_adaptation)
- Expected route at original freeze: base_benchmark_adaptation
- Route reason: best existing match scores 0.565, but portfolio coverage is 33.3%
- Inferred task coverage: 0.333
- Missing task families: ['creative_writing', 'word_puzzle']
- Synthesis required: True
- Catalog admission proposals: []

#### Automatic Literature Check

- Source evidence terms are verified before the gold record is admitted.
- `autobench auto-review` compares paper benchmarks, task families, selected portfolio, and route.
- Output decisions are MATCH / PARTIAL / MISMATCH with typed optimization errors.
- Human submission required: False.

## Integrity Checks

- All input leakage scans passed: True
- Matcher loaded hidden labels: False
- Gold labels were opened only by this post-run evaluator.
- This source-revealed report is the input to the automatic literature evaluator.
