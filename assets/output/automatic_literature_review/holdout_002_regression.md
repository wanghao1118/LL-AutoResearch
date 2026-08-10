# Auto-Bench Automatic Literature Review

- Status: **AUTOMATED_LITERATURE_AUDIT_CONFIRMED**
- Evidence class: **feedback_regression**
- Reviewer: **AUTO_LITERATURE_EVALUATOR**
- Human submission required: **False**
- Blind checks passed: **True**

## holdout_002 — CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing

- Source: https://arxiv.org/abs/2305.11738
- Source sections: `{'introduction': ['Introduction'], 'method': ['CRITIC: Correcting with Tool-Interactive Critiquing']}`
- Gold evidence sections: `['Free-form Question Answering', 'Mathematical Program Synthesis', 'Toxicity Reduction']`
- Decision: **MATCH**
- Selected: `['triviaqa', 'realtoxicityprompts', 'gsm8k', 'hotpotqa', 'svamp', 'ambignq', 'tabmwp']`
- Matches: `['gsm8k', 'hotpotqa', 'triviaqa', 'realtoxicityprompts', 'svamp', 'ambignq', 'tabmwp']`
- Missing: `[]`
- Extras: `[]`
- Outside catalog: `[]`
- Route: `direct_portfolio`; expected `direct_portfolio`
- Selected recall: `1.0000`
- Selected precision: `1.0000`
- Error types: `[]`
- Optimization feedback: `[]`
