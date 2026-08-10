# Auto-Bench Literature Audit: Round 1 → Round 2

- Round 1 human status: **LITERATURE_AUDIT_PARTIAL**
- Interpretation: Round 2 is a feedback-driven regression on the same papers, not a new untouched holdout. A fresh-paper audit is still needed for an unbiased generalization estimate.

## Aggregate change

| Metric | Round 1 | Round 2 | Delta |
|---|---:|---:|---:|
| Mean primary Recall@5 | 0.2500 | 1.0000 | +0.7500 |
| Mean primary Recall@6 | 0.5000 | 1.0000 | +0.5000 |
| Mean primary MRR | 0.3333 | 1.0000 | +0.6667 |
| Mean selected modeled recall | 0.7500 | 1.0000 | +0.2500 |
| Mean selected actual precision | 0.6000 | 1.0000 | +0.4000 |

## holdout_001 — Language Agent Tree Search Unifies Reasoning Acting and Planning in Language Models

- Previous human judgement: **PARTIAL**
- Previous human note: 自己对比一下也能看出来，你选的Bench和人家论文用的还是有些差别的。
- Selected before: `['webarena', 'humaneval', 'mind2web', 'webshop', 'mbpp']`
- Selected after: `['webshop', 'game_of_24', 'hotpotqa', 'humaneval', 'mbpp']`
- Newly selected: `['game_of_24', 'hotpotqa']`
- Removed from selection: `['webarena', 'mind2web']`
- Modeled matches before: `['humaneval', 'webshop', 'mbpp']`
- Modeled matches after: `['webshop', 'game_of_24', 'hotpotqa', 'humaneval', 'mbpp']`
- Modeled misses before: `['hotpotqa']`
- Modeled misses after: `[]`
- Selected modeled recall: 0.7500 → 1.0000
- Selected actual precision: 0.6000 → 1.0000
- Modeled-gold ranks before: `{'hotpotqa': None, 'humaneval': 6, 'mbpp': None, 'webshop': 3}`
- Modeled-gold ranks after: `{'hotpotqa': 3, 'humaneval': 4, 'mbpp': 5, 'webshop': 1, 'game_of_24': 2}`
- Paper choices newly added to the catalog: `['Game of 24']`
- Paper choices still outside the catalog: `[]`

## Reading rule

Selected modeled recall excludes paper choices that remain outside the public catalog. Those choices stay visible above and must be considered in the human MATCH/PARTIAL/MISMATCH decision.
