# Auto-Bench Blind Evaluation

- Verdict: **PASS**
- Cases: 3
- Mean primary Recall@5: 0.806
- Mean primary Recall@6: 1.000
- Mean primary MRR: 0.833
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
| primary | HotpotQA | Knowledge-Intensive Reasoning Tasks | True | 3 |
| primary | FEVER | Knowledge-Intensive Reasoning Tasks | True | 2 |
| primary | ALFWorld | Decision Making Tasks | True | 1 |
| primary | WebShop | Decision Making Tasks | False | 6 |

#### Auto-Bench Selected Portfolio

| Rank | Benchmark | Score | Role in source paper |
|---:|---|---:|---|
| 1 | ALFWorld | 0.870 | primary |
| 2 | FEVER | 0.890 | primary |
| 3 | HotpotQA | 0.890 | primary |
| 4 | WebArena | 0.730 | not_used_in_paper |

#### Direct Comparison

- Selected primary matches: ['alfworld', 'fever', 'hotpotqa']
- Selected secondary matches: []
- Primary benchmarks missing from selected portfolio: ['webshop']
- Secondary benchmarks missing from selected portfolio: []
- Selected recommendations not used by the paper: ['webarena']
- Top-6 primary matches: ['alfworld', 'fever', 'hotpotqa', 'webshop']
- Recall@5 / Recall@6: 0.750 / 1.000
- Route: direct_portfolio (expected direct_portfolio)

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
| primary | ALFWorld | Sequential decision making: ALFWorld | False | 6 |
| primary | HotpotQA | Reasoning: HotpotQA | True | 4 |
| primary | HumanEval | Programming | True | 2 |
| secondary | MBPP | Programming | False | 5 |
| unmodeled | LeetcodeHardGym | Programming | False | outside catalog |
| unmodeled | MultiPL-E language ports | Programming | False | outside catalog |

#### Auto-Bench Selected Portfolio

| Rank | Benchmark | Score | Role in source paper |
|---:|---|---:|---|
| 1 | ScienceWorld | 0.837 | not_used_in_paper |
| 2 | HumanEval | 0.793 | primary |
| 3 | ToolBench | 0.752 | not_used_in_paper |
| 4 | HotpotQA | 0.647 | primary |

#### Direct Comparison

- Selected primary matches: ['humaneval', 'hotpotqa']
- Selected secondary matches: []
- Primary benchmarks missing from selected portfolio: ['alfworld']
- Secondary benchmarks missing from selected portfolio: ['mbpp']
- Selected recommendations not used by the paper: ['scienceworld', 'toolbench']
- Top-6 primary matches: ['humaneval', 'hotpotqa', 'alfworld']
- Recall@5 / Recall@6: 0.667 / 1.000
- Route: direct_portfolio (expected direct_portfolio)

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
| secondary | HumanEvalFix | Experimental Setup | False | 4 |

#### Auto-Bench Selected Portfolio

| Rank | Benchmark | Score | Role in source paper |
|---:|---|---:|---|
| 1 | SWE-bench | 0.623 | primary |
| 2 | HumanEval | 0.593 | not_used_in_paper |

#### Direct Comparison

- Selected primary matches: ['swe_bench']
- Selected secondary matches: []
- Primary benchmarks missing from selected portfolio: []
- Secondary benchmarks missing from selected portfolio: ['humanevalfix']
- Selected recommendations not used by the paper: ['humaneval']
- Top-6 primary matches: ['swe_bench']
- Recall@5 / Recall@6: 1.000 / 1.000
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
