# Auto-Bench Literature Audit: Round 1 → Round 2

- Round 1 human status: **LITERATURE_AUDIT_PARTIAL**
- Interpretation: Round 2 is a feedback-driven regression on the same papers, not a new untouched holdout. A fresh-paper audit is still needed for an unbiased generalization estimate.

## Aggregate change

| Metric | Round 1 | Round 2 | Delta |
|---|---:|---:|---:|
| Mean primary Recall@5 | 0.8056 | 0.9167 | +0.1111 |
| Mean primary Recall@6 | 1.0000 | 1.0000 | +0.0000 |
| Mean primary MRR | 0.8333 | 0.6667 | -0.1667 |
| Mean selected modeled recall | 0.5833 | 1.0000 | +0.4167 |
| Mean selected actual precision | 0.5833 | 0.7111 | +0.1278 |

## case_001 — ReAct: Synergizing Reasoning and Acting in Language Models

- Previous human judgement: **MATCH**
- Previous human note: 论文实际使用了4个Benchmark，而你候选也给选了4个Benchmark，其中有3个是符合论文的，其中有一个排在了候选第6的位置。属于基本match的选择。
- Selected before: `['alfworld', 'fever', 'hotpotqa', 'webarena']`
- Selected after: `['webarena', 'fever', 'hotpotqa', 'alfworld', 'mind2web', 'webshop']`
- Modeled matches before: `['alfworld', 'fever', 'hotpotqa']`
- Modeled matches after: `['fever', 'hotpotqa', 'alfworld', 'webshop']`
- Modeled misses before: `['webshop']`
- Modeled misses after: `[]`
- Selected modeled recall: 0.7500 → 1.0000
- Selected actual precision: 0.7500 → 0.6667
- Modeled-gold ranks before: `{'hotpotqa': 3, 'fever': 2, 'alfworld': 1, 'webshop': 6}`
- Modeled-gold ranks after: `{'hotpotqa': 3, 'fever': 2, 'alfworld': 4, 'webshop': 6}`
- Paper choices still outside the catalog: `[]`

## case_002 — Reflexion: Language Agents with Verbal Reinforcement Learning

- Previous human judgement: **PARTIAL**
- Previous human note: 论文采用了5个Benchmark，并使用MultiPL-E语言端口。你在选择中选了4个Benchmark，只与原论文有1个重合。感觉重合率不是很高，而且候选的AlfWord是排在第6，MPEPP是排在第5，而且没有选择用MultiPL-E语言端口，这个差距还是蛮大的。
- Selected before: `['scienceworld', 'humaneval', 'toolbench', 'hotpotqa']`
- Selected after: `['scienceworld', 'humaneval', 'hotpotqa', 'mbpp', 'alfworld']`
- Modeled matches before: `['humaneval', 'hotpotqa']`
- Modeled matches after: `['humaneval', 'hotpotqa', 'mbpp', 'alfworld']`
- Modeled misses before: `['alfworld', 'mbpp']`
- Modeled misses after: `[]`
- Selected modeled recall: 0.5000 → 1.0000
- Selected actual precision: 0.5000 → 0.8000
- Modeled-gold ranks before: `{'alfworld': 6, 'hotpotqa': 4, 'humaneval': 2, 'mbpp': 5}`
- Modeled-gold ranks after: `{'alfworld': 5, 'hotpotqa': 3, 'humaneval': 2, 'mbpp': 4}`
- Paper choices still outside the catalog: `['LeetcodeHardGym', 'MultiPL-E language ports']`

## case_003 — SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering

- Previous human judgement: **PARTIAL**
- Previous human note: 论文选用了两个Benchmark，而你也采用了两个Benchmark。有一个是和论文符合的，另外一个是Human Aerial Fix，而你用的是Human Aerial，应该是它的子集吧，感觉是部分符合的。
- Selected before: `['swe_bench', 'humaneval']`
- Selected after: `['swe_bench', 'humanevalfix', 'humaneval']`
- Modeled matches before: `['swe_bench']`
- Modeled matches after: `['swe_bench', 'humanevalfix']`
- Modeled misses before: `['humanevalfix']`
- Modeled misses after: `[]`
- Selected modeled recall: 0.5000 → 1.0000
- Selected actual precision: 0.5000 → 0.6667
- Modeled-gold ranks before: `{'swe_bench': 1, 'humanevalfix': 4}`
- Modeled-gold ranks after: `{'swe_bench': 1, 'humanevalfix': 2}`
- Paper choices still outside the catalog: `[]`

## Reading rule

Selected modeled recall excludes paper choices that remain outside the public catalog. Those choices stay visible above and must be considered in the human MATCH/PARTIAL/MISMATCH decision.
