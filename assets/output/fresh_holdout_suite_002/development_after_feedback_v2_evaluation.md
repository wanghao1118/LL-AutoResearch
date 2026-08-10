# Auto-Bench Blind Evaluation

- Verdict: **NEEDS_ITERATION**
- Cases: 5
- Mean primary Recall@5: 0.933
- Mean primary Recall@6: 0.933
- Mean primary MRR: 0.400
- Mean selected modeled-benchmark recall: 0.933
- Mean selected actual-benchmark precision: 0.400
- Route accuracy: 1.000

## Case Results

### fresh2_001 — PAL: Program-aided Language Models

- Source paper: [PAL: Program-aided Language Models](https://arxiv.org/abs/2211.10435)
- Introduction source section: ['Introduction']
- Method source section(s): ['Background: Few-shot Prompting', 'Program-aided Language Models']
- Matcher-visible input: `assets/input/fresh_holdout_suite_002/cases/fresh2_001.json`
- Paper evidence sections: ['Experimental Setup', 'Mathematical Reasoning', 'Symbolic Reasoning', 'Algorithmic Tasks', 'Appendix: Datasets']
- The source identity and actual benchmarks below were revealed only after matching completed.

#### Benchmarks Used by the Paper

| Role | Benchmark | Evidence section | Auto-Bench selected | Auto-Bench rank |
|---|---|---|---:|---:|
| primary | GSM8K | Mathematical Reasoning | True | 1 |
| primary | SVAMP | Mathematical Reasoning | True | 2 |
| unmodeled | ASDiv | Appendix: Datasets | False | outside catalog |
| unmodeled | SingleOp | Appendix: Datasets | False | outside catalog |
| unmodeled | SingleEq | Appendix: Datasets | False | outside catalog |
| unmodeled | AddSub | Appendix: Datasets | False | outside catalog |
| unmodeled | MultiArith | Appendix: Datasets | False | outside catalog |
| unmodeled | GSM-Hard | Appendix: Datasets | False | outside catalog |
| unmodeled | Reasoning about Colored Objects | Symbolic Reasoning | False | outside catalog |
| unmodeled | Penguins in a Table | Symbolic Reasoning | False | outside catalog |
| unmodeled | Date Understanding | Symbolic Reasoning | False | outside catalog |
| unmodeled | Object Counting | Algorithmic Tasks | False | outside catalog |
| unmodeled | Repeat Copy | Algorithmic Tasks | False | outside catalog |

#### Auto-Bench Selected Portfolio

| Rank | Benchmark | Score | Selection role | Role in source paper |
|---:|---|---:|---|---|
| 1 | GSM8K | 0.625 | core_task_coverage | primary |
| 2 | SVAMP | 0.625 | declared_suite_breadth:math_reasoning | primary |

#### Direct Comparison

- Selected primary matches: ['gsm8k', 'svamp']
- Selected secondary matches: []
- Selected post-freeze catalog matches: []
- Primary benchmarks missing from selected portfolio: []
- Secondary benchmarks missing from selected portfolio: []
- Post-freeze catalog benchmarks missing from selected portfolio: []
- Selected recommendations not used by the paper: []
- Top-6 primary matches: ['gsm8k', 'svamp']
- Recall@5 / Recall@6: 1.000 / 1.000
- Selected modeled-benchmark recall: 1.000
- Selected actual-benchmark precision: 1.000
- Route: base_benchmark_adaptation (expected base_benchmark_adaptation)
- Expected route at original freeze: base_benchmark_adaptation
- Route reason: best existing match scores 0.625, but portfolio coverage is 50.0%
- Inferred task coverage: 0.500
- Missing task families: ['symbolic_reasoning']
- Synthesis required: True
- Catalog admission proposals: []

#### Automatic Literature Check

- Source evidence terms are verified before the gold record is admitted.
- `autobench auto-review` compares paper benchmarks, task families, selected portfolio, and route.
- Output decisions are MATCH / PARTIAL / MISMATCH with typed optimization errors.
- Human submission required: False.

### fresh2_002 — ReWOO: Decoupling Reasoning from Observations for Efficient Augmented Language Models

- Source paper: [ReWOO: Decoupling Reasoning from Observations for Efficient Augmented Language Models](https://arxiv.org/abs/2305.18323)
- Introduction source section: ['Introduction']
- Method source section(s): ['Methodology']
- Matcher-visible input: `assets/input/fresh_holdout_suite_002/cases/fresh2_002.json`
- Paper evidence sections: ['Experiments / Setups / Tasks and Datasets']
- The source identity and actual benchmarks below were revealed only after matching completed.

#### Benchmarks Used by the Paper

| Role | Benchmark | Evidence section | Auto-Bench selected | Auto-Bench rank |
|---|---|---|---:|---:|
| primary | HotpotQA | Tasks and Datasets | True | 2 |
| primary | TriviaQA | Tasks and Datasets | True | 1 |
| primary | GSM8K | Tasks and Datasets | False | 7 |
| unmodeled | SportsUnderstanding | Tasks and Datasets | False | outside catalog |
| unmodeled | StrategyQA | Tasks and Datasets | False | outside catalog |
| unmodeled | PhysicsQuestions | Tasks and Datasets | False | outside catalog |
| unmodeled | SOTUQA | Tasks and Datasets | False | outside catalog |
| unmodeled | Curated Real-World ALM Tasks | Tasks and Datasets | False | outside catalog |

#### Auto-Bench Selected Portfolio

| Rank | Benchmark | Score | Selection role | Role in source paper |
|---:|---|---:|---|---|
| 1 | TriviaQA | 0.830 | core_task_coverage | primary |
| 2 | HotpotQA | 0.813 | declared_suite_breadth:knowledge_intensive_qa | primary |

#### Direct Comparison

- Selected primary matches: ['triviaqa', 'hotpotqa']
- Selected secondary matches: []
- Selected post-freeze catalog matches: []
- Primary benchmarks missing from selected portfolio: ['gsm8k']
- Secondary benchmarks missing from selected portfolio: []
- Post-freeze catalog benchmarks missing from selected portfolio: []
- Selected recommendations not used by the paper: []
- Top-6 primary matches: ['triviaqa', 'hotpotqa']
- Recall@5 / Recall@6: 0.667 / 0.667
- Selected modeled-benchmark recall: 0.667
- Selected actual-benchmark precision: 1.000
- Route: base_benchmark_adaptation (expected base_benchmark_adaptation)
- Expected route at original freeze: base_benchmark_adaptation
- Route reason: best existing match scores 0.830, but portfolio coverage is 50.0%
- Inferred task coverage: 0.500
- Missing task families: ['tool_augmented_nlp']
- Synthesis required: True
- Catalog admission proposals: []

#### Automatic Literature Check

- Source evidence terms are verified before the gold record is admitted.
- `autobench auto-review` compares paper benchmarks, task families, selected portfolio, and route.
- Output decisions are MATCH / PARTIAL / MISMATCH with typed optimization errors.
- Human submission required: False.

### fresh2_003 — Inner Monologue: Embodied Reasoning through Planning with Language Models

- Source paper: [Inner Monologue: Embodied Reasoning through Planning with Language Models](https://arxiv.org/abs/2207.05608)
- Introduction source section: ['Introduction']
- Method source section(s): ['Leveraging Embodied Language Feedback', 'Problem Statement', 'Sources of Feedback']
- Matcher-visible input: `assets/input/fresh_holdout_suite_002/cases/fresh2_003.json`
- Paper evidence sections: ['Experimental Results', 'Simulated Tabletop Rearrangement', 'Real-World Tabletop Rearrangement', 'Real-World Mobile Manipulator in a Kitchen Setting']
- The source identity and actual benchmarks below were revealed only after matching completed.

#### Benchmarks Used by the Paper

| Role | Benchmark | Evidence section | Auto-Bench selected | Auto-Bench rank |
|---|---|---|---:|---:|
| unmodeled | Ravens-based Simulated Tabletop Rearrangement | Simulated Tabletop Rearrangement | False | outside catalog |
| unmodeled | Real-World Tabletop Rearrangement | Real-World Tabletop Rearrangement | False | outside catalog |
| unmodeled | Real-World Kitchen Mobile Manipulation | Real-World Mobile Manipulator in a Kitchen Setting | False | outside catalog |

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
- Missing task families: ['robot_manipulation']
- Synthesis required: True
- Catalog admission proposals: []

#### Automatic Literature Check

- Source evidence terms are verified before the gold record is admitted.
- `autobench auto-review` compares paper benchmarks, task families, selected portfolio, and route.
- Output decisions are MATCH / PARTIAL / MISMATCH with typed optimization errors.
- Human submission required: False.

### fresh2_004 — LLM+P: Empowering Large Language Models with Optimal Planning Proficiency

- Source paper: [LLM+P: Empowering Large Language Models with Optimal Planning Proficiency](https://arxiv.org/abs/2304.11477)
- Introduction source section: ['Introduction']
- Method source section(s): ['Method']
- Matcher-visible input: `assets/input/fresh_holdout_suite_002/cases/fresh2_004.json`
- Paper evidence sections: ['Experiments / Benchmark Problems']
- The source identity and actual benchmarks below were revealed only after matching completed.

#### Benchmarks Used by the Paper

| Role | Benchmark | Evidence section | Auto-Bench selected | Auto-Bench rank |
|---|---|---|---:|---:|
| unmodeled | Blocksworld | Benchmark Problems | False | outside catalog |
| unmodeled | Barman | Benchmark Problems | False | outside catalog |
| unmodeled | Floortile | Benchmark Problems | False | outside catalog |
| unmodeled | Grippers | Benchmark Problems | False | outside catalog |
| unmodeled | Storage | Benchmark Problems | False | outside catalog |
| unmodeled | Termes | Benchmark Problems | False | outside catalog |
| unmodeled | Tyreworld | Benchmark Problems | False | outside catalog |

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
- Missing task families: ['classical_planning', 'creative_writing']
- Synthesis required: True
- Catalog admission proposals: []

#### Automatic Literature Check

- Source evidence terms are verified before the gold record is admitted.
- `autobench auto-review` compares paper benchmarks, task families, selected portfolio, and route.
- Output decisions are MATCH / PARTIAL / MISMATCH with typed optimization errors.
- Human submission required: False.

### fresh2_005 — ViperGPT: Visual Inference via Python Execution for Reasoning

- Source paper: [ViperGPT: Visual Inference via Python Execution for Reasoning](https://arxiv.org/abs/2303.08128)
- Introduction source section: ['Introduction']
- Method source section(s): ['Method', 'Program Generation', 'Modules and Their API', 'Program Execution']
- Matcher-visible input: `assets/input/fresh_holdout_suite_002/cases/fresh2_005.json`
- Paper evidence sections: ['Evaluation', 'Visual Grounding', 'Compositional Image Question Answering', 'External Knowledge-dependent Image Question Answering', 'Video Causal/Temporal Reasoning']
- The source identity and actual benchmarks below were revealed only after matching completed.

#### Benchmarks Used by the Paper

| Role | Benchmark | Evidence section | Auto-Bench selected | Auto-Bench rank |
|---|---|---|---:|---:|
| unmodeled | RefCOCO | Visual Grounding | False | outside catalog |
| unmodeled | RefCOCO+ | Visual Grounding | False | outside catalog |
| unmodeled | GQA | Compositional Image Question Answering | False | outside catalog |
| unmodeled | OK-VQA | External Knowledge-dependent Image Question Answering | False | outside catalog |
| unmodeled | NExT-QA | Video Causal/Temporal Reasoning | False | outside catalog |

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
- Missing task families: ['visual_reasoning']
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
