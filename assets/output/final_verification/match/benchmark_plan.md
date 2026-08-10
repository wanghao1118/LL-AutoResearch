# Auto-Bench Plan: case_001

- Status: **AUTOMATIC_LITERATURE_CHECK_PENDING**
- Route: **direct_portfolio**
- Task-family coverage: **100.0%**
- Decision: portfolio covers 100.0% of inferred task families; weakest task-normalized selected compatibility is 0.843

## Matcher-Visible Paper Input

### Introduction

Introduction. A unique feature of human intelligence is the ability to seamlessly combine task-oriented actions with verbal reasoning (or inner speech, ), which has been theorized to play an important role in human cognition for enabling self-regulation or strategization and maintaining a working memory . Consider the example of cooking up a dish in the kitchen. Between any two specific actions, we may reason in language in order to track progress (``now that everything is cut, I should heat up the pot of water’’), to handle exceptions or adjust the plan according to the situation (``I don’t have salt, so let me use soy sauce and pepper instead’’), and to realize when external information is needed (``how do I prepare dough? Let me search on the Internet’’). We may also act (open a cookbook to read the recipe, open the fridge, check ingredients) to support the reasoning and to answer questions (``What dish can I make right now?''). This tight synergy between ``acting'’ and ``reasoning'’ allows humans to learn new tasks quickly and perform robust decision making or reasoning, even under previously unseen circumstances or facing information uncertainties. Recent results have hinted at the possibility of combining verbal reasoning with interactive decision making in autonomous systems. On one hand, properly prompted large language models (LLMs) have demonstrated emergent capabilities to carry out several steps of reasoning traces to derive answers from questions in arithmetic, commonsense, and symbolic reasoning tasks . However, this ``chain-of-thought’' reasoning is a static black box, in that the model uses its own internal representations to generate thoughts and is not grounded in the external world, which limits its ability to reason reactively or update its knowledge. This can lead to issues like fact hallucination and error propagation over the reasoning process (Figure (1b)). On the other hand, recent work has explored the use of pre-trained language models for planning and acting in interactive environments , with a focus on predicting actions via language priors. These approaches usually convert multi-modal observations into text, use a language model to generate domain-specific actions or plans, and then use a controller to choose or execute them. However, they do not employ language models to reason abstractly about high-level goals or maintain a working memory to support acting, barring who perform a limited form of verbal reasoning to reiterate spatial facts about the current state. Beyond such simple embodied tasks to interact with a few blocks, there have not been studies on how reasoning and acting can be combined in a synergistic manner for general task solving, and if such a combination can bring systematic benefits compared to reasoning or acting alone. In this work, we present METHOD_X, a general paradigm to combine reasoning and acting with language models for solving diverse language reasoning and decision making tasks (Figure ). METHOD_X prompts LLMs to generate both verbal reasoning traces and actions pertaining to a task in an interleaved manner, which allows the model to perform dynamic reasoning to create, maintain, and adjust high-level plans for acting (reason to act), while also interact with the external environments (e.g.\,Wikipedia) to incorporate additional information into reasoning (act to reason). The best approach overall is a combination of METHOD_X and REASONING_BASELINE that allows for the use of both internal knowledge and externally obtained information during reasoning. We also demonstrate the importance of sparse, versatile reasoning in decision making by showing consistent advantages over controlled baselines with actions only. Besides general applicability and performance boost, the combination of reasoning and acting also contributes to model interpretability, trustworthiness, and diagnosability across all domains, as humans can readily distinguish information from model's internal knowledge versus external environments, as well as inspect reasoning traces to understand the decision basis of model actions. To summarize, our key contributions are the following: (1) we introduce METHOD_X, a novel prompt-based paradigm to synergize reasoning and acting in language models for general task solving; (2) we perform extensive experiments across diverse benchmarks to showcase the advantage of METHOD_X in a few-shot learning setup over prior approaches that perform either reasoning or action generation in isolation; (3) we present systematic ablations and analysis to understand the importance of acting in reasoning tasks, and reasoning in interactive tasks; (4) we analyze the limitations of METHOD_X under the prompting setup (i.e.\,limited support of reasoning and acting behaviors), and perform initial finetuning experiments showing the potential of METHOD_X to improve with additional training data. Scaling up METHOD_X to train and operate on more tasks and combining it with complementary paradigms like reinforcement learning could further unlock the potential of large language models.

### Method

METHOD_X: Synergizing Reasoning + Acting Consider a general setup of an agent interacting with an environment for task solving. At time step , an agent receives an observation from the environment and takes an action following some policy , where is the context to the agent. Learning a policy is challenging when the mapping is highly implicit and requires extensive computation. For example, the agent shown in Figure (1c) is unable to generate the correct final action (Act 4) to finish the QA task as it requires complex reasoning over the trajectory context (Question, Act 1-3, Obs 1-3). Similarly, the agent shown in Figure (2a) fails to comprehend from the context that sinkbasin 1 does not contain peppershaker 1, thus keep producing hallucinating actions. The idea of METHOD_X is simple: we augment the agent's action space to , where is the space of language. An action in the language space, which we will refer to as a thought or a reasoning trace, does not affect the external environment, thus leading to no observation feedback. Instead, a thought aims to compose useful information by reasoning over the current context , and update the context to support future reasoning or acting. As shown in Figure , there could be various types of useful thoughts, e.g.\,decomposing task goals and create action plans (2b, Act 1; 1d, Thought 1), injecting commonsense knowledge relevant to task solving (2b, Act 1), extracting important parts from observations (1d, Thought2, 4), track progress and transit action plans (2b, Act 8), handle exceptions and adjust action plans (1d, Thought 3), and so on. However, as the language space is unlimited, learning in this augmented action space is difficult and requires strong language priors. , is prompted with few-shot in-context examples to generate both domain-specific actions and free-form language thoughts for task solving (Figure (1d), (2b)). Each in-context example is a human trajectory of actions, thoughts, and environment observations to solve a task instance (see Appendix ). For the tasks where reasoning is of primary importance (Figure (1)), we alternate the generation of thoughts and actions so that the task-solving trajectory consists of multiple thought-action-observation steps. In contrast, for decision making tasks that potentially involve a large number of actions (Figure (2)), thoughts only need to appear sparsely in the most relevant positions of a trajectory, so we let the language model decide the asynchronous occurrence of thoughts and actions for itself. Since decision making and reasoning capabilities are integrated into a large language model, METHOD_X enjoys several unique features: A) Intuitive and easy to design: Designing METHOD_X prompts is straightforward as human annotators just type down their thoughts in language on top of their actions taken. No ad-hoc format choice, thought design, or example selection is used in this paper. We detail prompt design for each task in Sections and . B) General and flexible: Due to the flexible thought space and thought-action occurrence format, METHOD_X works for diverse tasks with distinct action spaces and reasoning needs, including but not limited to QA, fact verification, text game, and web navigation. We also show in Section additional benefits when finetuning is enabled, and in Section how METHOD_X performance is robust to prompt selections. D) Human aligned and controllable: METHOD_X promises an interpretable sequential decision making and reasoning process where humans can easily inspect reasoning and factual correctness. Moreover, humans can also control or correct the agent behavior on the go by thought editing, as shown in Figure in Section .

## Inferred Evaluation Profile

- Tasks: embodied_household, fact_verification, knowledge_intensive_qa, sequential_decision_making, web_navigation
- Explicit benchmark counts: {}
- Declared total evaluation breadth: 0
- Uncovered tasks: none
- Modalities: text, web
- Interactions: browser, interactive_environment, retrieval_tool
- Outputs: action_trajectory, classification_label, short_answer, supporting_evidence
- Capabilities: evidence_grounding, external_information_retrieval, long_horizon_planning, reasoning_action_interleaving, tool_use

## Selected Benchmark Portfolio

- **WebArena** (`webarena`): score=0.778; role=core_task_coverage; source=https://arxiv.org/abs/2307.13854
- **ALFWorld** (`alfworld`): score=0.678; role=core_task_coverage; source=https://arxiv.org/abs/2010.03768
- **FEVER** (`fever`): score=0.634; role=core_task_coverage; source=https://arxiv.org/abs/1803.05355
- **HotpotQA** (`hotpotqa`): score=0.634; role=core_task_coverage; source=https://arxiv.org/abs/1809.09600
- **TriviaQA** (`triviaqa`): score=0.634; role=supplementary_triangulation:knowledge_intensive_qa; source=https://arxiv.org/abs/1705.03551
- **WebShop** (`webshop`): score=0.651; role=supplementary_triangulation:sequential_decision_making,web_navigation; source=https://arxiv.org/abs/2207.01206

## Top Candidates

1. **WebArena** (`webarena`) — 0.778; tasks=['sequential_decision_making', 'web_navigation']
2. **ALFWorld** (`alfworld`) — 0.678; tasks=['embodied_household', 'sequential_decision_making']
3. **FEVER** (`fever`) — 0.634; tasks=['fact_verification']
4. **HotpotQA** (`hotpotqa`) — 0.634; tasks=['knowledge_intensive_qa']
5. **TriviaQA** (`triviaqa`) — 0.634; tasks=['knowledge_intensive_qa']
6. **WebShop** (`webshop`) — 0.651; tasks=['sequential_decision_making', 'web_navigation']
7. **Mind2Web** (`mind2web`) — 0.681; tasks=['web_navigation']
8. **ScienceWorld** (`scienceworld`) — 0.614; tasks=['sequential_decision_making']
9. **ToolBench** (`toolbench`) — 0.465; tasks=[]
10. **GSM8K** (`gsm8k`) — 0.265; tasks=[]

## Online Literature Leads

- Online search was disabled or returned no relevant arXiv metadata hits.

## Catalog Admission Proposals

- No benchmark-like online hit met the proposal threshold.

## Adaptation and Synthesis

- Missing task families: []
- Synthesis required: False
- Official and adapted metrics must be reported separately.
- Test examples stay frozen and never seed synthetic records.

## Automatic Literature Validation

Current status: **AUTOMATIC_LITERATURE_CHECK_PENDING**.
- Existing-paper blind test: after matching, reveal the source paper and compare its actual benchmarks with Selected and Top-6 using MATCH / PARTIAL / MISMATCH.
- The source comparison runs in a separate evaluator process; the matcher never receives paper identity, experiment sections, or benchmark labels.
- Every mismatch, missing benchmark, extra benchmark, catalog gap, and route error becomes machine-readable optimization feedback; no user submission is required.
