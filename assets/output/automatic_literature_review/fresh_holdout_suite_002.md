# Auto-Bench Automatic Literature Review

- Status: **AUTOMATED_LITERATURE_AUDIT_MISMATCH**
- Evidence class: **fresh_holdout**
- Reviewer: **AUTO_LITERATURE_EVALUATOR**
- Human submission required: **False**
- Blind checks passed: **True**

## fresh2_001 — PAL: Program-aided Language Models

- Source: https://arxiv.org/abs/2211.10435
- Source sections: `{'introduction': ['Introduction'], 'method': ['Background: Few-shot Prompting', 'Program-aided Language Models']}`
- Gold evidence sections: `['Experimental Setup', 'Mathematical Reasoning', 'Symbolic Reasoning', 'Algorithmic Tasks', 'Appendix: Datasets']`
- Decision: **PARTIAL**
- Selected: `['gsm8k', 'svamp']`
- Matches: `['gsm8k', 'svamp']`
- Missing: `[]`
- Extras: `[]`
- Outside catalog: `['ASDiv', 'SingleOp', 'SingleEq', 'AddSub', 'MultiArith', 'GSM-Hard', 'Reasoning about Colored Objects', 'Penguins in a Table', 'Date Understanding', 'Object Counting', 'Repeat Copy']`
- Outside-catalog task-family recall: `0.0000`
- Matched outside-catalog task families: `[]`
- Missing outside-catalog task families: `['algorithmic_reasoning', 'math_word_problem', 'symbolic_reasoning']`
- Route: `direct_portfolio`; expected `base_benchmark_adaptation`
- Selected recall: `1.0000`
- Selected precision: `1.0000`
- Error types: `['CATALOG_GAP', 'UNMODELED_TASK_INFERENCE_GAP', 'ROUTE_ERROR']`
- Optimization feedback: `['verify and type the paper-backed benchmarks that remain outside the catalog', 'expand task-family inference for paper benchmarks outside the current catalog', 'align direct reuse versus adaptation/synthesis with uncovered task families']`

## fresh2_002 — ReWOO: Decoupling Reasoning from Observations for Efficient Augmented Language Models

- Source: https://arxiv.org/abs/2305.18323
- Source sections: `{'introduction': ['Introduction'], 'method': ['Methodology']}`
- Gold evidence sections: `['Experiments / Setups / Tasks and Datasets']`
- Decision: **PARTIAL**
- Selected: `['alfworld', 'triviaqa', 'hotpotqa']`
- Matches: `['triviaqa', 'hotpotqa']`
- Missing: `['gsm8k']`
- Extras: `['alfworld']`
- Outside catalog: `['SportsUnderstanding', 'StrategyQA', 'PhysicsQuestions', 'SOTUQA', 'Curated Real-World ALM Tasks']`
- Outside-catalog task-family recall: `0.0000`
- Matched outside-catalog task families: `[]`
- Missing outside-catalog task families: `['commonsense_reasoning', 'current_event_qa', 'knowledge_intensive_qa', 'real_world_tool_use', 'scientific_reasoning']`
- Route: `direct_portfolio`; expected `base_benchmark_adaptation`
- Selected recall: `0.6667`
- Selected precision: `0.6667`
- Error types: `['CATALOG_GAP', 'UNMODELED_TASK_INFERENCE_GAP', 'PORTFOLIO_RECALL_GAP', 'PORTFOLIO_PRECISION_GAP', 'ROUTE_ERROR']`
- Optimization feedback: `['verify and type the paper-backed benchmarks that remain outside the catalog', 'expand task-family inference for paper benchmarks outside the current catalog', 'improve task, modality, environment, or suite-breadth inference for missed paper choices', 'tighten specialization and environment gates for paper-external selections', 'align direct reuse versus adaptation/synthesis with uncovered task families']`

## fresh2_003 — Inner Monologue: Embodied Reasoning through Planning with Language Models

- Source: https://arxiv.org/abs/2207.05608
- Source sections: `{'introduction': ['Introduction'], 'method': ['Leveraging Embodied Language Feedback', 'Problem Statement', 'Sources of Feedback']}`
- Gold evidence sections: `['Experimental Results', 'Simulated Tabletop Rearrangement', 'Real-World Tabletop Rearrangement', 'Real-World Mobile Manipulator in a Kitchen Setting']`
- Decision: **MISMATCH**
- Selected: `['alfworld', 'hotpotqa', 'triviaqa', 'scienceworld', 'webarena']`
- Matches: `[]`
- Missing: `[]`
- Extras: `['alfworld', 'hotpotqa', 'triviaqa', 'scienceworld', 'webarena']`
- Outside catalog: `['Ravens-based Simulated Tabletop Rearrangement', 'Real-World Tabletop Rearrangement', 'Real-World Kitchen Mobile Manipulation']`
- Outside-catalog task-family recall: `0.0000`
- Matched outside-catalog task families: `[]`
- Missing outside-catalog task families: `['robot_manipulation']`
- Route: `direct_portfolio`; expected `new_benchmark_synthesis`
- Selected recall: `1.0000`
- Selected precision: `0.0000`
- Error types: `['CATALOG_GAP', 'UNMODELED_TASK_INFERENCE_GAP', 'PORTFOLIO_PRECISION_GAP', 'ROUTE_ERROR']`
- Optimization feedback: `['verify and type the paper-backed benchmarks that remain outside the catalog', 'expand task-family inference for paper benchmarks outside the current catalog', 'tighten specialization and environment gates for paper-external selections', 'align direct reuse versus adaptation/synthesis with uncovered task families']`

## fresh2_004 — LLM+P: Empowering Large Language Models with Optimal Planning Proficiency

- Source: https://arxiv.org/abs/2304.11477
- Source sections: `{'introduction': ['Introduction'], 'method': ['Method']}`
- Gold evidence sections: `['Experiments / Benchmark Problems']`
- Decision: **MISMATCH**
- Selected: `['alfworld', 'scienceworld', 'webarena']`
- Matches: `[]`
- Missing: `[]`
- Extras: `['alfworld', 'scienceworld', 'webarena']`
- Outside catalog: `['Blocksworld', 'Barman', 'Floortile', 'Grippers', 'Storage', 'Termes', 'Tyreworld']`
- Outside-catalog task-family recall: `0.0000`
- Matched outside-catalog task families: `[]`
- Missing outside-catalog task families: `['classical_planning']`
- Route: `direct_portfolio`; expected `new_benchmark_synthesis`
- Selected recall: `1.0000`
- Selected precision: `0.0000`
- Error types: `['CATALOG_GAP', 'UNMODELED_TASK_INFERENCE_GAP', 'PORTFOLIO_PRECISION_GAP', 'ROUTE_ERROR']`
- Optimization feedback: `['verify and type the paper-backed benchmarks that remain outside the catalog', 'expand task-family inference for paper benchmarks outside the current catalog', 'tighten specialization and environment gates for paper-external selections', 'align direct reuse versus adaptation/synthesis with uncovered task families']`

## fresh2_005 — ViperGPT: Visual Inference via Python Execution for Reasoning

- Source: https://arxiv.org/abs/2303.08128
- Source sections: `{'introduction': ['Introduction'], 'method': ['Method', 'Program Generation', 'Modules and Their API', 'Program Execution']}`
- Gold evidence sections: `['Evaluation', 'Visual Grounding', 'Compositional Image Question Answering', 'External Knowledge-dependent Image Question Answering', 'Video Causal/Temporal Reasoning']`
- Decision: **MISMATCH**
- Selected: `['swe_bench', 'multipl_e', 'triviaqa', 'leetcodehardgym', 'humaneval', 'mbpp']`
- Matches: `[]`
- Missing: `[]`
- Extras: `['swe_bench', 'multipl_e', 'triviaqa', 'leetcodehardgym', 'humaneval', 'mbpp']`
- Outside catalog: `['RefCOCO', 'RefCOCO+', 'GQA', 'OK-VQA', 'NExT-QA']`
- Outside-catalog task-family recall: `0.0000`
- Matched outside-catalog task families: `[]`
- Missing outside-catalog task families: `['compositional_visual_qa', 'knowledge_visual_qa', 'video_qa', 'visual_grounding']`
- Route: `direct_portfolio`; expected `new_benchmark_synthesis`
- Selected recall: `1.0000`
- Selected precision: `0.0000`
- Error types: `['CATALOG_GAP', 'UNMODELED_TASK_INFERENCE_GAP', 'PORTFOLIO_PRECISION_GAP', 'ROUTE_ERROR']`
- Optimization feedback: `['verify and type the paper-backed benchmarks that remain outside the catalog', 'expand task-family inference for paper benchmarks outside the current catalog', 'tighten specialization and environment gates for paper-external selections', 'align direct reuse versus adaptation/synthesis with uncovered task families']`
