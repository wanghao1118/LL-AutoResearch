# Auto-Bench Automatic Literature Review

- Status: **AUTOMATED_LITERATURE_AUDIT_MISMATCH**
- Evidence class: **fresh_holdout**
- Reviewer: **AUTO_LITERATURE_EVALUATOR**
- Human submission required: **False**
- Blind checks passed: **True**

## fresh_001 — Self-Refine: Iterative Refinement with Self-Feedback

- Source: https://arxiv.org/abs/2303.17651
- Source sections: `{'introduction': ['Introduction'], 'method': ['Method']}`
- Gold evidence sections: `['Evaluation', 'Appendix: Task Details']`
- Decision: **MISMATCH**
- Selected: `['humaneval', 'mbpp', 'humanevalfix']`
- Matches: `[]`
- Missing: `['gsm8k']`
- Extras: `['humaneval', 'mbpp', 'humanevalfix']`
- Outside catalog: `['FED', 'PIE', 'Project CodeNet', 'Sentiment Reversal review-passage set', 'Acronym Generation paper-curated set', 'CommonGen-Hard']`
- Outside-catalog task-family recall: `0.0000`
- Matched outside-catalog task families: `[]`
- Missing outside-catalog task families: `['acronym_generation', 'code_optimization', 'code_readability', 'constrained_generation', 'dialogue_response_generation', 'sentiment_reversal']`
- Route: `direct_portfolio`; expected `new_benchmark_synthesis`
- Selected recall: `0.0000`
- Selected precision: `0.0000`
- Error types: `['CATALOG_GAP', 'UNMODELED_TASK_INFERENCE_GAP', 'PORTFOLIO_RECALL_GAP', 'PORTFOLIO_PRECISION_GAP', 'ROUTE_ERROR']`
- Optimization feedback: `['verify and type the paper-backed benchmarks that remain outside the catalog', 'expand task-family inference for paper benchmarks outside the current catalog', 'improve task, modality, environment, or suite-breadth inference for missed paper choices', 'tighten specialization and environment gates for paper-external selections', 'align direct reuse versus adaptation/synthesis with uncovered task families']`

## fresh_002 — Graph of Thoughts: Solving Elaborate Problems with Large Language Models

- Source: https://arxiv.org/abs/2308.09687
- Source sections: `{'introduction': ['Introduction'], 'method': ['Graph of Thoughts', 'Architecture']}`
- Gold evidence sections: `['Example Use Cases', 'Evaluation']`
- Decision: **MISMATCH**
- Selected: `['swe_bench']`
- Matches: `[]`
- Missing: `[]`
- Extras: `['swe_bench']`
- Outside catalog: `['Sorting task suite', 'Set Intersection task suite', 'Keyword Counting task suite', 'Document Merging task suite']`
- Outside-catalog task-family recall: `0.0000`
- Matched outside-catalog task families: `[]`
- Missing outside-catalog task families: `['document_merging', 'keyword_counting', 'set_intersection', 'sorting']`
- Route: `direct_portfolio`; expected `new_benchmark_synthesis`
- Selected recall: `1.0000`
- Selected precision: `0.0000`
- Error types: `['CATALOG_GAP', 'UNMODELED_TASK_INFERENCE_GAP', 'PORTFOLIO_PRECISION_GAP', 'ROUTE_ERROR']`
- Optimization feedback: `['verify and type the paper-backed benchmarks that remain outside the catalog', 'expand task-family inference for paper benchmarks outside the current catalog', 'tighten specialization and environment gates for paper-external selections', 'align direct reuse versus adaptation/synthesis with uncovered task families']`

## fresh_003 — ExpeL: LLM Agents Are Experiential Learners

- Source: https://arxiv.org/abs/2308.10144
- Source sections: `{'introduction': ['Introduction'], 'method': ['ExpeL: An Experiential Learning Agent']}`
- Gold evidence sections: `['Experiments / Experimental Setup', 'Transfer Learning']`
- Decision: **PARTIAL**
- Selected: `['alfworld', 'scienceworld', 'webarena']`
- Matches: `['alfworld']`
- Missing: `['hotpotqa', 'webshop', 'fever']`
- Extras: `['scienceworld', 'webarena']`
- Outside catalog: `[]`
- Outside-catalog task-family recall: `1.0000`
- Matched outside-catalog task families: `[]`
- Missing outside-catalog task families: `[]`
- Route: `direct_portfolio`; expected `direct_portfolio`
- Selected recall: `0.2500`
- Selected precision: `0.3333`
- Error types: `['PORTFOLIO_RECALL_GAP', 'PORTFOLIO_PRECISION_GAP']`
- Optimization feedback: `['improve task, modality, environment, or suite-breadth inference for missed paper choices', 'tighten specialization and environment gates for paper-external selections']`

## fresh_004 — Reasoning with Language Model is Planning with World Model

- Source: https://arxiv.org/abs/2305.14992
- Source sections: `{'introduction': ['Introduction'], 'method': ['Reasoning via Planning']}`
- Gold evidence sections: `['Plan Generation', 'Math Reasoning', 'Logical Reasoning']`
- Decision: **MISMATCH**
- Selected: `['game_of_24']`
- Matches: `[]`
- Missing: `['gsm8k']`
- Extras: `['game_of_24']`
- Outside catalog: `['Blocksworld', 'PrOntoQA']`
- Outside-catalog task-family recall: `0.0000`
- Matched outside-catalog task families: `[]`
- Missing outside-catalog task families: `['classical_planning', 'logical_reasoning']`
- Route: `direct_portfolio`; expected `base_benchmark_adaptation`
- Selected recall: `0.0000`
- Selected precision: `0.0000`
- Error types: `['CATALOG_GAP', 'UNMODELED_TASK_INFERENCE_GAP', 'PORTFOLIO_RECALL_GAP', 'PORTFOLIO_PRECISION_GAP', 'ROUTE_ERROR']`
- Optimization feedback: `['verify and type the paper-backed benchmarks that remain outside the catalog', 'expand task-family inference for paper benchmarks outside the current catalog', 'improve task, modality, environment, or suite-breadth inference for missed paper choices', 'tighten specialization and environment gates for paper-external selections', 'align direct reuse versus adaptation/synthesis with uncovered task families']`

## fresh_005 — Chameleon: Plug-and-Play Compositional Reasoning with Large Language Models

- Source: https://arxiv.org/abs/2304.09842
- Source sections: `{'introduction': ['Introduction'], 'method': ['General Framework', 'Module Inventory', 'Applications']}`
- Gold evidence sections: `['Applications of Chameleon', 'Science Question Answering', 'Tabular Mathematical Reasoning', 'Experiments']`
- Decision: **MISMATCH**
- Selected: `['humaneval', 'hotpotqa', 'game_of_24', 'mbpp', 'humanevalfix']`
- Matches: `[]`
- Missing: `['tabmwp']`
- Extras: `['humaneval', 'hotpotqa', 'game_of_24', 'mbpp', 'humanevalfix']`
- Outside catalog: `['ScienceQA']`
- Outside-catalog task-family recall: `0.0000`
- Matched outside-catalog task families: `[]`
- Missing outside-catalog task families: `['multimodal_science_qa']`
- Route: `direct_portfolio`; expected `base_benchmark_adaptation`
- Selected recall: `0.0000`
- Selected precision: `0.0000`
- Error types: `['CATALOG_GAP', 'UNMODELED_TASK_INFERENCE_GAP', 'PORTFOLIO_RECALL_GAP', 'PORTFOLIO_PRECISION_GAP', 'ROUTE_ERROR']`
- Optimization feedback: `['verify and type the paper-backed benchmarks that remain outside the catalog', 'expand task-family inference for paper benchmarks outside the current catalog', 'improve task, modality, environment, or suite-breadth inference for missed paper choices', 'tighten specialization and environment gates for paper-external selections', 'align direct reuse versus adaptation/synthesis with uncovered task families']`
