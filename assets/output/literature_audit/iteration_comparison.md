# Auto-Bench Literature Audit: Round 2 → Round 3

- Round 2 human status: **LITERATURE_AUDIT_PARTIAL**
- Interpretation: Round 3 is a feedback-driven regression on the same papers, not a new untouched holdout. A fresh-paper audit is still needed for an unbiased generalization estimate.

## Aggregate change

| Metric | Round 2 | Round 3 | Delta |
|---|---:|---:|---:|
| Mean primary Recall@5 | 0.9167 | 0.9167 | +0.0000 |
| Mean primary Recall@6 | 1.0000 | 1.0000 | +0.0000 |
| Mean primary MRR | 0.6667 | 0.8333 | +0.1667 |
| Mean selected modeled recall | 1.0000 | 1.0000 | +0.0000 |
| Mean selected actual precision | 0.7111 | 0.7222 | +0.0111 |

## case_001 — ReAct: Synergizing Reasoning and Acting in Language Models

- Previous human judgement: **MATCH**
- Previous human note: perfect
- Selected before: `['webarena', 'fever', 'hotpotqa', 'alfworld', 'mind2web', 'webshop']`
- Selected after: `['webarena', 'alfworld', 'fever', 'hotpotqa', 'visualwebarena', 'webshop']`
- Newly selected: `['visualwebarena']`
- Removed from selection: `['mind2web']`
- Modeled matches before: `['fever', 'hotpotqa', 'alfworld', 'webshop']`
- Modeled matches after: `['alfworld', 'fever', 'hotpotqa', 'webshop']`
- Modeled misses before: `[]`
- Modeled misses after: `[]`
- Selected modeled recall: 1.0000 → 1.0000
- Selected actual precision: 0.6667 → 0.6667
- Modeled-gold ranks before: `{'hotpotqa': 3, 'fever': 2, 'alfworld': 4, 'webshop': 6}`
- Modeled-gold ranks after: `{'hotpotqa': 4, 'fever': 3, 'alfworld': 2, 'webshop': 6}`
- Paper choices newly added to the catalog: `[]`
- Paper choices still outside the catalog: `[]`

## case_002 — Reflexion: Language Agents with Verbal Reinforcement Learning

- Previous human judgement: **PARTIAL**
- Previous human note: 你的分数最高的bench：	ScienceWorld并没有被入选，而且论文中也有两个bench：LeetcodeHardGym、MultiPL-E language ports，你没有选到
- Selected before: `['scienceworld', 'humaneval', 'hotpotqa', 'mbpp', 'alfworld']`
- Selected after: `['leetcodehardgym', 'alfworld', 'hotpotqa', 'multipl_e', 'humaneval', 'mbpp']`
- Newly selected: `['leetcodehardgym', 'multipl_e']`
- Removed from selection: `['scienceworld']`
- Modeled matches before: `['humaneval', 'hotpotqa', 'mbpp', 'alfworld']`
- Modeled matches after: `['leetcodehardgym', 'alfworld', 'hotpotqa', 'multipl_e', 'humaneval', 'mbpp']`
- Modeled misses before: `[]`
- Modeled misses after: `[]`
- Selected modeled recall: 1.0000 → 1.0000
- Selected actual precision: 0.8000 → 1.0000
- Modeled-gold ranks before: `{'alfworld': 5, 'hotpotqa': 3, 'humaneval': 2, 'mbpp': 4}`
- Modeled-gold ranks after: `{'alfworld': 2, 'hotpotqa': 3, 'humaneval': 5, 'leetcodehardgym': 1, 'mbpp': 6, 'multipl_e': 4}`
- Paper choices newly added to the catalog: `['LeetcodeHardGym', 'MultiPL-E language ports']`
- Paper choices still outside the catalog: `[]`

## case_003 — SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering

- Previous human judgement: **MATCH**
- Previous human note: good
- Selected before: `['swe_bench', 'humanevalfix', 'humaneval']`
- Selected after: `['swe_bench', 'humanevalfix', 'humaneval', 'leetcodehardgym']`
- Newly selected: `['leetcodehardgym']`
- Removed from selection: `[]`
- Modeled matches before: `['swe_bench', 'humanevalfix']`
- Modeled matches after: `['swe_bench', 'humanevalfix']`
- Modeled misses before: `[]`
- Modeled misses after: `[]`
- Selected modeled recall: 1.0000 → 1.0000
- Selected actual precision: 0.6667 → 0.5000
- Modeled-gold ranks before: `{'swe_bench': 1, 'humanevalfix': 2}`
- Modeled-gold ranks after: `{'swe_bench': 1, 'humanevalfix': 2}`
- Paper choices newly added to the catalog: `[]`
- Paper choices still outside the catalog: `[]`

## Reading rule

Selected modeled recall excludes paper choices that remain outside the public catalog. Those choices stay visible above and must be considered in the human MATCH/PARTIAL/MISMATCH decision.
