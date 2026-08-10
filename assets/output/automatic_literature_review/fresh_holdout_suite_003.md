# Auto-Bench Automatic Literature Review

- Status: **AUTOMATED_LITERATURE_AUDIT_MISMATCH**
- Evidence class: **fresh_holdout**
- Reviewer: **AUTO_LITERATURE_EVALUATOR**
- Human submission required: **False**
- Blind checks passed: **True**

## fresh3_001 — Toolformer: Language Models Can Teach Themselves to Use Tools

- Source: https://arxiv.org/abs/2302.04761
- Source sections: `{'introduction': ['Introduction'], 'method': ['Approach', 'Tools']}`
- Gold evidence sections: `['Experiments / Downstream Tasks / LAMA', 'Experiments / Math Datasets', 'Experiments / Question Answering', 'Experiments / Multilingual Question Answering', 'Experiments / Temporal Datasets', 'Experiments / Language Modeling']`
- Decision: **PARTIAL**
- Selected: `['triviaqa', 'hotpotqa']`
- Matches: `['triviaqa']`
- Missing: `['svamp']`
- Extras: `['hotpotqa']`
- Outside catalog: `['SQuAD subset of LAMA', 'Google-RE subset of LAMA', 'T-REx subset of LAMA', 'ASDiv', 'MAWPS', 'Web Questions', 'Natural Questions', 'MLQA', 'TempLAMA', 'Dateset', 'WikiText', 'CCNet language-modeling subset']`
- Outside-catalog task-family recall: `0.0000`
- All inferred task families: `['knowledge_intensive_qa']`
- Matched outside-catalog task families: `[]`
- Missing outside-catalog task families: `['language_modeling', 'math_reasoning', 'tool_augmented_nlp']`
- Route: `direct_portfolio`; expected `base_benchmark_adaptation`
- Selected recall: `0.5000`
- Selected precision: `0.5000`
- Error types: `['CATALOG_GAP', 'UNMODELED_TASK_INFERENCE_GAP', 'PORTFOLIO_RECALL_GAP', 'PORTFOLIO_PRECISION_GAP', 'ROUTE_ERROR']`
- Optimization feedback: `['verify and type the paper-backed benchmarks that remain outside the catalog', 'expand task-family inference for paper benchmarks outside the current catalog', 'improve task, modality, environment, or suite-breadth inference for missed paper choices', 'tighten specialization and environment gates for paper-external selections', 'align direct reuse versus adaptation/synthesis with uncovered task families']`

## fresh3_002 — ProgPrompt: Generating Situated Robot Task Plans using Large Language Models

- Source: https://arxiv.org/abs/2209.11302
- Source sections: `{'introduction': ['Introduction'], 'method': ['Our Method: ProgPrompt']}`
- Gold evidence sections: `['Experiments / Simulation Experiments', 'Experiments / Real-Robot Experiments']`
- Decision: **PARTIAL**
- Selected: `['alfworld']`
- Matches: `[]`
- Missing: `[]`
- Extras: `['alfworld']`
- Outside catalog: `['VirtualHome Household Task Set', 'Physical Robot Tabletop Task Set']`
- Outside-catalog task-family recall: `0.5000`
- All inferred task families: `['embodied_household', 'symbolic_reasoning']`
- Matched outside-catalog task families: `['embodied_household']`
- Missing outside-catalog task families: `['robot_manipulation']`
- Route: `base_benchmark_adaptation`; expected `base_benchmark_adaptation`
- Selected recall: `1.0000`
- Selected precision: `0.0000`
- Error types: `['CATALOG_GAP', 'UNMODELED_TASK_INFERENCE_GAP', 'PORTFOLIO_PRECISION_GAP']`
- Optimization feedback: `['verify and type the paper-backed benchmarks that remain outside the catalog', 'expand task-family inference for paper benchmarks outside the current catalog', 'tighten specialization and environment gates for paper-external selections']`

## fresh3_003 — Visual Programming: Compositional visual reasoning without training

- Source: https://arxiv.org/abs/2211.11559
- Source sections: `{'introduction': ['Introduction'], 'method': ['Visual Programming']}`
- Gold evidence sections: `['Tasks / Compositional Visual Question Answering', 'Tasks / Zero-Shot Reasoning on Image Pairs', 'Tasks / Factual Knowledge Object Tagging', 'Tasks / Image Editing with Natural Language']`
- Decision: **PARTIAL**
- Selected: `[]`
- Matches: `[]`
- Missing: `[]`
- Extras: `[]`
- Outside catalog: `['GQA', 'NLVRv2', 'Factual Knowledge Object Tagging', 'Language-Guided Image Editing']`
- Outside-catalog task-family recall: `0.5000`
- All inferred task families: `['image_generation', 'visual_reasoning']`
- Matched outside-catalog task families: `['visual_reasoning']`
- Missing outside-catalog task families: `['image_editing']`
- Route: `new_benchmark_synthesis`; expected `new_benchmark_synthesis`
- Selected recall: `1.0000`
- Selected precision: `0.0000`
- Error types: `['CATALOG_GAP', 'UNMODELED_TASK_INFERENCE_GAP']`
- Optimization feedback: `['verify and type the paper-backed benchmarks that remain outside the catalog', 'expand task-family inference for paper benchmarks outside the current catalog']`

## fresh3_004 — Program of Thoughts Prompting: Disentangling Computation from Reasoning for Numerical Reasoning Tasks

- Source: https://arxiv.org/abs/2211.12588
- Source sections: `{'introduction': ['Introduction'], 'method': ['Program of Thoughts']}`
- Gold evidence sections: `['Experiments / Experimental Setup / Datasets']`
- Decision: **PARTIAL**
- Selected: `['gsm8k', 'svamp']`
- Matches: `['gsm8k', 'svamp']`
- Missing: `['tabmwp']`
- Extras: `[]`
- Outside catalog: `['AQuA', 'MultiArith', 'FinQA', 'ConvFinQA', 'TATQA']`
- Outside-catalog task-family recall: `0.5000`
- All inferred task families: `['math_reasoning', 'math_word_problem']`
- Matched outside-catalog task families: `['math_reasoning']`
- Missing outside-catalog task families: `['financial_numerical_qa']`
- Route: `direct_portfolio`; expected `base_benchmark_adaptation`
- Selected recall: `0.6667`
- Selected precision: `1.0000`
- Error types: `['CATALOG_GAP', 'UNMODELED_TASK_INFERENCE_GAP', 'PORTFOLIO_RECALL_GAP', 'ROUTE_ERROR']`
- Optimization feedback: `['verify and type the paper-backed benchmarks that remain outside the catalog', 'expand task-family inference for paper benchmarks outside the current catalog', 'improve task, modality, environment, or suite-breadth inference for missed paper choices', 'align direct reuse versus adaptation/synthesis with uncovered task families']`

## fresh3_005 — Tree of Thoughts: Deliberate Problem Solving with Large Language Models

- Source: https://arxiv.org/abs/2305.10601
- Source sections: `{'introduction': ['Introduction'], 'method': ['Tree of Thoughts: Deliberate Problem Solving with LM']}`
- Gold evidence sections: `['Experiments / Game of 24', 'Experiments / Creative Writing', 'Experiments / Mini Crosswords']`
- Decision: **MISMATCH**
- Selected: `[]`
- Matches: `[]`
- Missing: `['game_of_24']`
- Extras: `[]`
- Outside catalog: `['Creative Writing', '5x5 Mini Crosswords']`
- Outside-catalog task-family recall: `0.0000`
- All inferred task families: `['two_strategies_to_generate_candidates_for_the_next']`
- Matched outside-catalog task families: `[]`
- Missing outside-catalog task families: `['creative_writing', 'word_puzzle']`
- Route: `new_benchmark_synthesis`; expected `base_benchmark_adaptation`
- Selected recall: `0.0000`
- Selected precision: `0.0000`
- Error types: `['CATALOG_GAP', 'UNMODELED_TASK_INFERENCE_GAP', 'PORTFOLIO_RECALL_GAP', 'ROUTE_ERROR']`
- Optimization feedback: `['verify and type the paper-backed benchmarks that remain outside the catalog', 'expand task-family inference for paper benchmarks outside the current catalog', 'improve task, modality, environment, or suite-breadth inference for missed paper choices', 'align direct reuse versus adaptation/synthesis with uncovered task families']`
