# Auto-Bench Plan: case_002

- Status: **HUMAN_REVIEW_REQUIRED**
- Route: **direct_portfolio**
- Task-family coverage: **100.0%**
- Decision: portfolio covers 100.0% of inferred task families; weakest selected compatibility is 0.647

## Matcher-Visible Paper Input

### Introduction

Recent works such as ReAct , SayCan , Toolformer , HuggingGPT , generative agents , and WebGPT have demonstrated the feasibility of autonomous decision-making agents that are built on top of a large language model (LLM) core. These methods use LLMs to generate text and `actions` that can be used in API calls and executed in an environment. Since they rely on massive models with an enormous number of parameters, such approaches have been so far limited to using in-context examples as a way of teaching the agents, since more traditional optimization schemes like reinforcement learning with gradient descent require substantial amounts of compute and time. In this paper, we propose an alternative approach called METHOD_X that uses verbal reinforcement to help agents learn from prior failings. METHOD_X converts binary or scalar feedback from the environment into verbal feedback in the form of a textual summary, which is then added as additional context for the LLM agent in the next episode. This self-reflective feedback acts as a `semantic' gradient signal by providing the agent with a concrete direction to improve upon, helping it learn from prior mistakes to perform better on the task. This is akin to how humans iteratively learn to accomplish complex tasks in a few-shot manner -- by reflecting on their previous failures in order to form an improved plan of attack for the next attempt. For example, in figure , a METHOD_X agent learns to optimize its own behavior to solve decision-making, programming, and reasoning tasks through trial, error, and self-reflection. Generating useful reflective feedback is challenging since it requires a good understanding of where the model made mistakes (i.e. the credit assignment problem ) as well as the ability to generate a summary containing actionable insights for improvement. We explore three ways for doing this -- simple binary environment feedback, pre-defined heuristics for common failure cases, and self-evaluation such as binary classification using LLMs (decision-making) or self-written unit tests (programming). In all implementations, the evaluation signal is amplified to natural language experience summaries which can be stored in long-term memory. METHOD_X has several advantages compared to more traditional RL approaches like policy or value-based learning: 1) it is lightweight and doesn't require finetuning the LLM, 2) it allows for more nuanced forms of feedback (e.g. targeted changes in actions), compared to scalar or vector rewards that are challenging to perform accurate credit assignment with, 3) it allows for a more explicit and interpretable form of episodic memory over prior experiences, and 4) it provides more explicit hints for actions in future episodes. At the same time, it does have the disadvantages of relying on the power of the LLM's self-evaluation capabilities (or heuristics) and not having a formal guarantee for success. However, as LLM capabilities improve, we only expect this paradigm to get better over time. Across all three types of tasks, we observe METHOD_X agents are better decision-makers, reasoners, and programmers. More concretely, METHOD_X agents improve on decision-making [REDACTED_BENCHMARK] tasks over strong baseline approaches by an absolute 22 in 12 iterative learning steps, and on reasoning questions in [REDACTED_BENCHMARK] by 20 , and Python programming tasks on [REDACTED_BENCHMARK] by as much as 11 . To summarize, our contributions are the following: We propose METHOD_X, a new paradigm for `verbal` reinforcement that parameterizes a policy as an agent's memory encoding paired with a choice of LLM parameters. We explore this emergent property of self-reflection in LLMs and empirically show that self-reflection is extremely useful to learn complex tasks over a handful of trials. We introduce [REDACTED_BENCHMARK], a code-generation RL gym environment consisting of 40 challenging Leetcode questions (`hard-level`) in 19 programming languages. [t] figures/METHOD_X_tasks.pdf METHOD_X works on decision-making , programming , and reasoning tasks.

### Method

[t] .48 figures/METHOD_X_rl.pdf .48 [H] Reinforcement via self-reflection Initialize Actor, Evaluator, Self-Reflection: , , Initialize policy , Generate initial trajectory using Evaluate using Generate initial self-reflection using Set Set not pass or max trials Generate using Evaluate using Generate self-reflection using Append to Increment (a) Diagram of METHOD_X. (b) METHOD_X reinforcement algorithm -10pt We develop a modular formulation for METHOD_X, utilizing three distinct models: an Actor, denoted as , which generates text and actions; an Evaluator model, represented by , that scores the outputs produced by ; and a Self-Reflection model, denoted as , which generates verbal reinforcement cues to assist the Actor in self-improvement. We provide a detailed description of each of these models and subsequently elucidate their collaborative functioning within the METHOD_X framework. Actor. The Actor is built upon a large language model (LLM) that is specifically prompted to generate the necessary text and actions conditioned on the state observations. Analogous to traditional policy-based RL setups, we sample an action or generation, , from the current policy at time , receive an observation from the environment . We explore various Actor models, including Chain of Thought and ReAct . These diverse generation models allow us to explore different aspects of text and action generation within the METHOD_X framework, providing valuable insights into their performance and effectiveness. In addition, we also add a memory component mem that provides additional context to this agent. This adaption was inspired by , who suggest a policy iteration approach using in-context learning. Details on how this is populated are provided below. Evaluator. The Evaluator component of the METHOD_X framework plays a crucial role in assessing the quality of the generated outputs produced by the Actor. It takes as input a generated trajectory and computes a reward score that reflects its performance within the given task context. Defining effective value and reward functions that apply to semantic spaces is difficult, so we investigate several variants of the Evaluator model. For reasoning tasks, we explore reward functions based on exact match (EM) grading, ensuring that the generated output aligns closely with the expected solution. In decision-making tasks, we employ pre-defined heuristic functions that are tailored to specific evaluation criteria. Additionally, we experiment with using a different instantiation of an LLM itself as an Evaluator, generating rewards for decision-making and programming tasks. This multi-faceted approach to Evaluator design allows us to examine different strategies for scoring generated outputs, offering insights into their effectiveness and suitability across a range of tasks. Self-reflection. The Self-Reflection model instantiated as an LLM, plays a crucial role in the METHOD_X framework by generating verbal self-reflections to provide valuable feedback for future trials. Given a sparse reward signal, such as a binary success status (success/fail), the current trajectory, and its persistent memory mem, the self-reflection model generates nuanced and specific feedback. This feedback, which is more informative than scalar rewards, is then stored in the agent's memory (mem). For instance, in a multi-step decision-making task, when the agent receives a failure signal, it can infer that a specific action led to subsequent incorrect actions and . The agent can then verbally state that it should have taken a different action, , which would have resulted in and , and store this experience in its memory. In subsequent trials, the agent can leverage its past experiences to adapt its decision-making approach at time by choosing action . This iterative process of trial, error, self-reflection, and persisting memory enables the agent to rapidly improve its decision-making ability in various environments by utilizing informative feedback signals. Memory. Core components of the METHOD_X process are the notion of short-term and long-term memory. At inference time, the Actor conditions its decisions on short and long-term memory, similar to the way that humans remember fine-grain recent details while also recalling distilled important experiences from long-term memory. In the RL setup, the trajectory history serves as the short-term memory while outputs from the Self-Reflection model are stored in long-term memory. These two memory components work together to provide context that is specific but also influenced by lessons learned over several trials, which is a key advantage of METHOD_X agents over other LLM action choice works. The METHOD_X process. METHOD_X is formalized as an iterative optimization process in . In the first trial, the Actor produces a trajectory by interacting with the environment. The Evaluator then produces a score which is computed as . is only a scalar reward for trial that improves as task-specific performance increases. After the first trial, to amplify to a feedback form that can be used for improvement by an LLM, the Self-Reflection model analyzes the set of to produce a summary which is stored in the memory mem. is a verbal experience feedback for trial . The Actor, Evaluator, and Self-Reflection models work together through trials in a loop until the Evaluator deems to be correct. As mentioned in , the memory component of METHOD_X is crucial to its effectiveness. After each trial , , is appended mem. In practice, we bound mem by a maximum number of stored experiences, (usually set to 1-3) to adhere to max context LLM limitations.

## Inferred Evaluation Profile

- Tasks: code_generation, knowledge_intensive_qa, sequential_decision_making
- Uncovered tasks: none
- Modalities: code, text
- Interactions: interactive_environment, retrieval_tool
- Outputs: action_trajectory, function_implementation, short_answer
- Capabilities: episodic_memory, iterative_improvement, long_horizon_planning, self_reflection, test_based_verification, tool_use

## Selected Benchmark Portfolio

- **ScienceWorld** (`scienceworld`): score=0.837; role=core_task_coverage; source=https://arxiv.org/abs/2203.07540
- **HumanEval** (`humaneval`): score=0.793; role=core_task_coverage; source=https://arxiv.org/abs/2107.03374
- **HotpotQA** (`hotpotqa`): score=0.647; role=core_task_coverage; source=https://arxiv.org/abs/1809.09600
- **MBPP** (`mbpp`): score=0.793; role=supplementary_triangulation:code_generation; source=https://arxiv.org/abs/2108.07732
- **ALFWorld** (`alfworld`): score=0.677; role=supplementary_triangulation:sequential_decision_making; source=https://arxiv.org/abs/2010.03768

## Top Candidates

1. **ScienceWorld** (`scienceworld`) — 0.837; tasks=['sequential_decision_making']
2. **HumanEval** (`humaneval`) — 0.793; tasks=['code_generation']
3. **HotpotQA** (`hotpotqa`) — 0.647; tasks=['knowledge_intensive_qa']
4. **MBPP** (`mbpp`) — 0.793; tasks=['code_generation']
5. **ALFWorld** (`alfworld`) — 0.677; tasks=['sequential_decision_making']
6. **OSWorld** (`osworld`) — 0.650; tasks=['sequential_decision_making']
7. **WebArena** (`webarena`) — 0.570; tasks=['sequential_decision_making']
8. **VisualWebArena** (`visualwebarena`) — 0.497; tasks=['sequential_decision_making']
9. **HumanEvalFix** (`humanevalfix`) — 0.480; tasks=['code_generation']
10. **WebShop** (`webshop`) — 0.460; tasks=['sequential_decision_making']

## Online Literature Leads

- Online search was disabled or returned no relevant arXiv metadata hits.

## Catalog Admission Proposals

- No benchmark-like online hit met the proposal threshold.

## Adaptation and Synthesis

- Missing task families: []
- Synthesis required: False
- Official and adapted metrics must be reported separately.
- Test examples stay frozen and never seed synthetic records.

## Human Validation

Current status: **HUMAN_REVIEW_REQUIRED**.
- Existing-paper blind test: after matching, reveal the source paper and compare its actual benchmarks with Selected and Top-6 using MATCH / PARTIAL / MISMATCH.
- New method without literature gold: two independent reviewers score construct alignment, task representativeness, metric validity, data quality, leakage control, and execution feasibility.
Automated retrieval metrics do not approve either validation track.
