# Auto-Bench Blind Evaluation

- Verdict: **PASS**
- Cases: 3
- Mean primary Recall@5: 0.917
- Mean primary Recall@6: 1.000
- Mean primary MRR: 0.833
- Mean selected modeled-benchmark recall: 1.000
- Mean selected actual-benchmark precision: 0.722
- Route accuracy: 1.000

## Case Results

### case_001 — ReAct: Synergizing Reasoning and Acting in Language Models

- Source paper: [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)
- Introduction source section: ['Introduction']
- Method source section(s): ['ReAct: Synergizing Reasoning + Acting']
- Matcher-visible input: `assets/input/blind_cases/case_001.json`
- Paper evidence sections: ['Knowledge-Intensive Reasoning Tasks', 'Decision Making Tasks']
- The source identity and actual benchmarks below were revealed only after matching completed.

#### Benchmarks Used by the Paper

| Role | Benchmark | Evidence section | Auto-Bench selected | Auto-Bench rank |
|---|---|---|---:|---:|
| primary | HotpotQA | Knowledge-Intensive Reasoning Tasks | True | 4 |
| primary | FEVER | Knowledge-Intensive Reasoning Tasks | True | 3 |
| primary | ALFWorld | Decision Making Tasks | True | 2 |
| primary | WebShop | Decision Making Tasks | True | 6 |

#### Auto-Bench Selected Portfolio

| Rank | Benchmark | Score | Selection role | Role in source paper |
|---:|---|---:|---|---|
| 1 | WebArena | 0.778 | core_task_coverage | not_used_in_paper |
| 2 | ALFWorld | 0.678 | core_task_coverage | primary |
| 3 | FEVER | 0.634 | core_task_coverage | primary |
| 4 | HotpotQA | 0.634 | core_task_coverage | primary |
| 5 | VisualWebArena | 0.738 | supplementary_triangulation:sequential_decision_making,web_navigation | not_used_in_paper |
| 6 | WebShop | 0.701 | supplementary_triangulation:sequential_decision_making,web_navigation | primary |

#### Direct Comparison

- Selected primary matches: ['alfworld', 'fever', 'hotpotqa', 'webshop']
- Selected secondary matches: []
- Primary benchmarks missing from selected portfolio: []
- Secondary benchmarks missing from selected portfolio: []
- Selected recommendations not used by the paper: ['webarena', 'visualwebarena']
- Top-6 primary matches: ['alfworld', 'fever', 'hotpotqa', 'webshop']
- Recall@5 / Recall@6: 0.750 / 1.000
- Selected modeled-benchmark recall: 1.000
- Selected actual-benchmark precision: 0.667
- Route: direct_portfolio (expected direct_portfolio)
- Route reason: portfolio covers 100.0% of inferred task families; weakest task-normalized selected compatibility is 0.870
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

### case_002 — Reflexion: Language Agents with Verbal Reinforcement Learning

- Source paper: [Reflexion: Language Agents with Verbal Reinforcement Learning](https://arxiv.org/abs/2303.11366)
- Introduction source section: ['Introduction']
- Method source section(s): ['Reflexion: reinforcement via verbal reflection']
- Matcher-visible input: `assets/input/blind_cases/case_002.json`
- Paper evidence sections: ['Sequential decision making: ALFWorld', 'Reasoning: HotpotQA', 'Programming']
- The source identity and actual benchmarks below were revealed only after matching completed.

#### Benchmarks Used by the Paper

| Role | Benchmark | Evidence section | Auto-Bench selected | Auto-Bench rank |
|---|---|---|---:|---:|
| primary | ALFWorld | Sequential decision making: ALFWorld | True | 2 |
| primary | HotpotQA | Reasoning: HotpotQA | True | 3 |
| primary | HumanEval | Programming | True | 5 |
| secondary | MBPP | Programming | True | 6 |
| primary | LeetcodeHardGym | Programming | True | 1 |
| secondary | MultiPL-E | Programming | True | 4 |

#### Auto-Bench Selected Portfolio

| Rank | Benchmark | Score | Selection role | Role in source paper |
|---:|---|---:|---|---|
| 1 | LeetcodeHardGym | 0.757 | core_task_coverage | primary |
| 2 | ALFWorld | 0.623 | core_task_coverage | primary |
| 3 | HotpotQA | 0.433 | core_task_coverage | primary |
| 4 | MultiPL-E | 0.580 | specialized_capability:multilingual_code_generation | secondary |
| 5 | HumanEval | 0.580 | supplementary_triangulation:code_generation | primary |
| 6 | MBPP | 0.580 | supplementary_triangulation:code_generation | secondary |

#### Direct Comparison

- Selected primary matches: ['leetcodehardgym', 'alfworld', 'hotpotqa', 'humaneval']
- Selected secondary matches: ['multipl_e', 'mbpp']
- Primary benchmarks missing from selected portfolio: []
- Secondary benchmarks missing from selected portfolio: []
- Selected recommendations not used by the paper: []
- Top-6 primary matches: ['leetcodehardgym', 'alfworld', 'hotpotqa', 'humaneval']
- Recall@5 / Recall@6: 1.000 / 1.000
- Selected modeled-benchmark recall: 1.000
- Selected actual-benchmark precision: 1.000
- Route: direct_portfolio (expected direct_portfolio)
- Route reason: portfolio covers 100.0% of inferred task families; weakest task-normalized selected compatibility is 0.647
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

### case_003 — SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering

- Source paper: [SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering](https://arxiv.org/abs/2405.15793)
- Introduction source section: ['Introduction']
- Method source section(s): ['The Agent-Computer Interface', 'SWE-agent: Designing an ACI for Software Engineering']
- Matcher-visible input: `assets/input/blind_cases/case_003.json`
- Paper evidence sections: ['Experimental Setup']
- The source identity and actual benchmarks below were revealed only after matching completed.

#### Benchmarks Used by the Paper

| Role | Benchmark | Evidence section | Auto-Bench selected | Auto-Bench rank |
|---|---|---|---:|---:|
| primary | SWE-bench | Experimental Setup | True | 1 |
| secondary | HumanEvalFix | Experimental Setup | True | 2 |

#### Auto-Bench Selected Portfolio

| Rank | Benchmark | Score | Selection role | Role in source paper |
|---:|---|---:|---|---|
| 1 | SWE-bench | 0.747 | core_task_coverage | primary |
| 2 | HumanEvalFix | 0.653 | core_task_coverage | secondary |
| 3 | HumanEval | 0.480 | supplementary_triangulation:code_generation | not_used_in_paper |
| 4 | LeetcodeHardGym | 0.480 | supplementary_triangulation:code_generation | not_used_in_paper |

#### Direct Comparison

- Selected primary matches: ['swe_bench']
- Selected secondary matches: ['humanevalfix']
- Primary benchmarks missing from selected portfolio: []
- Secondary benchmarks missing from selected portfolio: []
- Selected recommendations not used by the paper: ['humaneval', 'leetcodehardgym']
- Top-6 primary matches: ['swe_bench']
- Recall@5 / Recall@6: 1.000 / 1.000
- Selected modeled-benchmark recall: 1.000
- Selected actual-benchmark precision: 0.500
- Route: direct_portfolio (expected direct_portfolio)
- Route reason: portfolio covers 100.0% of inferred task families; weakest task-normalized selected compatibility is 0.693
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
