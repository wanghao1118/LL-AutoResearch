# Auto-Bench Literature Audit: Round 1 → Round 2

- Round 1 human status: **LITERATURE_AUDIT_PARTIAL**
- Interpretation: Round 2 is a feedback-driven regression on the same papers, not a new untouched holdout. A fresh-paper audit is still needed for an unbiased generalization estimate.

## Aggregate change

| Metric | Round 1 | Round 2 | Delta |
|---|---:|---:|---:|
| Mean primary Recall@5 | 1.0000 | 1.0000 | +0.0000 |
| Mean primary Recall@6 | 1.0000 | 1.0000 | +0.0000 |
| Mean primary MRR | 1.0000 | 0.3333 | -0.6667 |
| Mean selected modeled recall | 1.0000 | 1.0000 | +0.0000 |
| Mean selected actual precision | 0.6667 | 1.0000 | +0.3333 |

## holdout_002 — CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing

- Previous human judgement: **PARTIAL**
- Previous human note: 有所差距
- Selected before: `['hotpotqa', 'gsm8k', 'toolbench']`
- Selected after: `['triviaqa', 'realtoxicityprompts', 'gsm8k', 'hotpotqa', 'svamp', 'ambignq', 'tabmwp']`
- Newly selected: `['triviaqa', 'realtoxicityprompts', 'svamp', 'ambignq', 'tabmwp']`
- Removed from selection: `['toolbench']`
- Modeled matches before: `['hotpotqa', 'gsm8k']`
- Modeled matches after: `['triviaqa', 'realtoxicityprompts', 'gsm8k', 'hotpotqa', 'svamp', 'ambignq', 'tabmwp']`
- Modeled misses before: `[]`
- Modeled misses after: `[]`
- Selected modeled recall: 1.0000 → 1.0000
- Selected actual precision: 0.6667 → 1.0000
- Modeled-gold ranks before: `{'hotpotqa': 1, 'gsm8k': 2}`
- Modeled-gold ranks after: `{'hotpotqa': 4, 'gsm8k': 3, 'ambignq': 6, 'triviaqa': 1, 'svamp': 5, 'tabmwp': None, 'realtoxicityprompts': 2}`
- Paper choices newly added to the catalog: `['AmbigNQ', 'TriviaQA', 'SVAMP', 'TabMWP', 'RealToxicityPrompts']`
- Paper choices still outside the catalog: `[]`

## Reading rule

Selected modeled recall excludes paper choices that remain outside the public catalog. Those choices stay visible above and must be considered in the human MATCH/PARTIAL/MISMATCH decision.
