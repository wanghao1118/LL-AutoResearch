# Auto-Bench Automatic Literature Review

- Status: **AUTOMATED_LITERATURE_AUDIT_PARTIAL**
- Evidence class: **feedback_regression**
- Reviewer: **AUTO_LITERATURE_EVALUATOR**
- Human submission required: **False**
- Blind checks passed: **True**

## fresh2_001 — PAL: Program-aided Language Models

- Source: https://arxiv.org/abs/2211.10435
- Source sections: `{'introduction': ['Introduction'], 'method': ['Background: Few-shot Prompting', 'Program-aided Language Models']}`
- Gold evidence sections: `['Experimental Setup', 'Mathematical Reasoning', 'Symbolic Reasoning', 'Algorithmic Tasks', 'Appendix: Datasets']`
- Decision: **MATCH**
- Selected: `['gsm8k', 'svamp']`
- Matches: `['gsm8k', 'svamp']`
- Missing: `[]`
- Extras: `[]`
- Outside catalog: `['ASDiv', 'SingleOp', 'SingleEq', 'AddSub', 'MultiArith', 'GSM-Hard', 'Reasoning about Colored Objects', 'Penguins in a Table', 'Date Understanding', 'Object Counting', 'Repeat Copy']`
- Outside-catalog task-family recall: `1.0000`
- All inferred task families: `['math_reasoning', 'symbolic_reasoning']`
- Matched outside-catalog task families: `['math_reasoning', 'symbolic_reasoning']`
- Missing outside-catalog task families: `[]`
- Route: `base_benchmark_adaptation`; expected `base_benchmark_adaptation`
- Selected recall: `1.0000`
- Selected precision: `1.0000`
- Error types: `['CATALOG_GAP']`
- Optimization feedback: `['verify and type the paper-backed benchmarks that remain outside the catalog']`

## fresh2_002 — ReWOO: Decoupling Reasoning from Observations for Efficient Augmented Language Models

- Source: https://arxiv.org/abs/2305.18323
- Source sections: `{'introduction': ['Introduction'], 'method': ['Methodology']}`
- Gold evidence sections: `['Experiments / Setups / Tasks and Datasets']`
- Decision: **PARTIAL**
- Selected: `['triviaqa', 'hotpotqa']`
- Matches: `['triviaqa', 'hotpotqa']`
- Missing: `['gsm8k']`
- Extras: `[]`
- Outside catalog: `['SportsUnderstanding', 'StrategyQA', 'PhysicsQuestions', 'SOTUQA', 'Curated Real-World ALM Tasks']`
- Outside-catalog task-family recall: `1.0000`
- All inferred task families: `['knowledge_intensive_qa', 'tool_augmented_nlp']`
- Matched outside-catalog task families: `['tool_augmented_nlp']`
- Missing outside-catalog task families: `[]`
- Route: `base_benchmark_adaptation`; expected `base_benchmark_adaptation`
- Selected recall: `0.6667`
- Selected precision: `1.0000`
- Error types: `['CATALOG_GAP', 'PORTFOLIO_RECALL_GAP']`
- Optimization feedback: `['verify and type the paper-backed benchmarks that remain outside the catalog', 'improve task, modality, environment, or suite-breadth inference for missed paper choices']`

## fresh2_003 — Inner Monologue: Embodied Reasoning through Planning with Language Models

- Source: https://arxiv.org/abs/2207.05608
- Source sections: `{'introduction': ['Introduction'], 'method': ['Leveraging Embodied Language Feedback', 'Problem Statement', 'Sources of Feedback']}`
- Gold evidence sections: `['Experimental Results', 'Simulated Tabletop Rearrangement', 'Real-World Tabletop Rearrangement', 'Real-World Mobile Manipulator in a Kitchen Setting']`
- Decision: **MATCH**
- Selected: `[]`
- Matches: `[]`
- Missing: `[]`
- Extras: `[]`
- Outside catalog: `['Ravens-based Simulated Tabletop Rearrangement', 'Real-World Tabletop Rearrangement', 'Real-World Kitchen Mobile Manipulation']`
- Outside-catalog task-family recall: `1.0000`
- All inferred task families: `['robot_manipulation']`
- Matched outside-catalog task families: `['robot_manipulation']`
- Missing outside-catalog task families: `[]`
- Route: `new_benchmark_synthesis`; expected `new_benchmark_synthesis`
- Selected recall: `1.0000`
- Selected precision: `0.0000`
- Error types: `['CATALOG_GAP']`
- Optimization feedback: `['verify and type the paper-backed benchmarks that remain outside the catalog']`

## fresh2_004 — LLM+P: Empowering Large Language Models with Optimal Planning Proficiency

- Source: https://arxiv.org/abs/2304.11477
- Source sections: `{'introduction': ['Introduction'], 'method': ['Method']}`
- Gold evidence sections: `['Experiments / Benchmark Problems']`
- Decision: **MATCH**
- Selected: `[]`
- Matches: `[]`
- Missing: `[]`
- Extras: `[]`
- Outside catalog: `['Blocksworld', 'Barman', 'Floortile', 'Grippers', 'Storage', 'Termes', 'Tyreworld']`
- Outside-catalog task-family recall: `1.0000`
- All inferred task families: `['classical_planning', 'creative_writing']`
- Matched outside-catalog task families: `['classical_planning']`
- Missing outside-catalog task families: `[]`
- Route: `new_benchmark_synthesis`; expected `new_benchmark_synthesis`
- Selected recall: `1.0000`
- Selected precision: `0.0000`
- Error types: `['CATALOG_GAP']`
- Optimization feedback: `['verify and type the paper-backed benchmarks that remain outside the catalog']`

## fresh2_005 — ViperGPT: Visual Inference via Python Execution for Reasoning

- Source: https://arxiv.org/abs/2303.08128
- Source sections: `{'introduction': ['Introduction'], 'method': ['Method', 'Program Generation', 'Modules and Their API', 'Program Execution']}`
- Gold evidence sections: `['Evaluation', 'Visual Grounding', 'Compositional Image Question Answering', 'External Knowledge-dependent Image Question Answering', 'Video Causal/Temporal Reasoning']`
- Decision: **MATCH**
- Selected: `[]`
- Matches: `[]`
- Missing: `[]`
- Extras: `[]`
- Outside catalog: `['RefCOCO', 'RefCOCO+', 'GQA', 'OK-VQA', 'NExT-QA']`
- Outside-catalog task-family recall: `1.0000`
- All inferred task families: `['visual_reasoning']`
- Matched outside-catalog task families: `['visual_reasoning']`
- Missing outside-catalog task families: `[]`
- Route: `new_benchmark_synthesis`; expected `new_benchmark_synthesis`
- Selected recall: `1.0000`
- Selected precision: `0.0000`
- Error types: `['CATALOG_GAP']`
- Optimization feedback: `['verify and type the paper-backed benchmarks that remain outside the catalog']`
