# Auto-Bench Automatic Literature Review

- Status: **AUTOMATED_LITERATURE_AUDIT_PARTIAL**
- Evidence class: **feedback_regression**
- Reviewer: **AUTO_LITERATURE_EVALUATOR**
- Human submission required: **False**
- Blind checks passed: **True**

## case_001 — ReAct: Synergizing Reasoning and Acting in Language Models

- Source: https://arxiv.org/abs/2210.03629
- Source sections: `{'introduction': ['Introduction'], 'method': ['ReAct: Synergizing Reasoning + Acting']}`
- Gold evidence sections: `['Knowledge-Intensive Reasoning Tasks', 'Decision Making Tasks']`
- Decision: **PARTIAL**
- Selected: `['webarena', 'alfworld', 'fever', 'hotpotqa', 'triviaqa', 'webshop']`
- Matches: `['alfworld', 'fever', 'hotpotqa', 'webshop']`
- Missing: `[]`
- Extras: `['webarena', 'triviaqa']`
- Outside catalog: `[]`
- Route: `direct_portfolio`; expected `direct_portfolio`
- Selected recall: `1.0000`
- Selected precision: `0.6667`
- Error types: `['PORTFOLIO_PRECISION_GAP']`
- Optimization feedback: `['tighten specialization and environment gates for paper-external selections']`

## case_002 — Reflexion: Language Agents with Verbal Reinforcement Learning

- Source: https://arxiv.org/abs/2303.11366
- Source sections: `{'introduction': ['Introduction'], 'method': ['Reflexion: reinforcement via verbal reflection']}`
- Gold evidence sections: `['Sequential decision making: ALFWorld', 'Reasoning: HotpotQA', 'Programming']`
- Decision: **MATCH**
- Selected: `['leetcodehardgym', 'alfworld', 'hotpotqa', 'multipl_e', 'humaneval', 'mbpp']`
- Matches: `['leetcodehardgym', 'alfworld', 'hotpotqa', 'humaneval', 'multipl_e', 'mbpp']`
- Missing: `[]`
- Extras: `[]`
- Outside catalog: `[]`
- Route: `direct_portfolio`; expected `direct_portfolio`
- Selected recall: `1.0000`
- Selected precision: `1.0000`
- Error types: `[]`
- Optimization feedback: `[]`

## case_003 — SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering

- Source: https://arxiv.org/abs/2405.15793
- Source sections: `{'introduction': ['Introduction'], 'method': ['The Agent-Computer Interface', 'SWE-agent: Designing an ACI for Software Engineering']}`
- Gold evidence sections: `['Experimental Setup']`
- Decision: **PARTIAL**
- Selected: `['swe_bench', 'humanevalfix', 'humaneval', 'mbpp']`
- Matches: `['swe_bench', 'humanevalfix']`
- Missing: `[]`
- Extras: `['humaneval', 'mbpp']`
- Outside catalog: `[]`
- Route: `direct_portfolio`; expected `direct_portfolio`
- Selected recall: `1.0000`
- Selected precision: `0.5000`
- Error types: `['PORTFOLIO_PRECISION_GAP']`
- Optimization feedback: `['tighten specialization and environment gates for paper-external selections']`
