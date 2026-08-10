# Auto-Bench Plan: fresh2_003

- Status: **HUMAN_REVIEW_REQUIRED**
- Route: **direct_portfolio**
- Task-family coverage: **100.0%**
- Decision: portfolio covers 100.0% of inferred task families; weakest task-normalized selected compatibility is 0.600

## Matcher-Visible Paper Input

### Introduction

[t] figures/feedback-teaser.pdf _X enables grounded closed-loop feedback for robot planning with large language models by leveraging a collection of perception models (e.g., scene descriptors and success detectors) in tandem with pretrained language-conditioned robot skills. Experiments show our system can reason and replan to accomplish complex long-horizon tasks for (a) mobile manipulation and (b,c) tabletop manipulation in both simulated and real settings. 1.4em

### Method

with METHOD_X In this section, we introduce how LLMs can act as interactive problem solvers and incorporate embodied environment observations into grounded planning through a process we refer to as METHOD_X. Problem Statement. Our setting consists of an embodied robotic agent attempting to perform a high-level natural language instruction . This robotic agent is only capable of executing short-horizon skills from a library of previously trained policies with short language descriptions , which may be trained with reinforcement learning or behavioral cloning. The ``planner,'' which is a pretrained LLM , attempts to find a sequence of skills to accomplish the instruction. To observe the environment, the planner has access to textual feedback from the environment that can be appended to the instruction or requested by the planner. The observation may be success detection, object detection, scene description, visual-question answering, or even human feedback. Our work studies to what extent the LLM planner is able to reason over and utilize such feedback to ``close the loop'' with the environment and improve planning. METHOD_X. We formulate an ``METHOD_X'' by continually injecting information from the various sources of feedback into the LLM planning language prompts as the robot interacts with the environment. While LLMs have demonstrated exceptional planning capabilities for embodied control tasks , prior works have found it crucial to ground LLM predictions with external components such as affordance functions in order to produce useful plans that are executable by robots. However, LLMs used in this context have thus far remained one-directional -- providing a list of skills, without making corrections or leveraging opportunities to replan accordingly. In contrast, METHOD_X studies settings where grounded environment feedback is provided directly to the LLM in a closed-loop fashion. This promotes improved LLM reasoning in complex long-horizon settings, even before any external affordance-based grounding methods are applied. Our analysis assumes textual feedback is provided to the planner, but does not assume a single specific method of fusing LLM planning with low-level robotic control or a specific method of extracting environment feedback into language. Rather than focusing on a particular algorithmic implementation, our aim is to provide a case study on the value of incorporating different types of feedback into closed-loop LLM-based planning. Thus, METHOD_X in Sec utilizes language feedback within separate systems that incorporate different LLMs, different methods of fusing planning with control, different environments and tasks, and different methods of acquiring control policies. We note that in our specific implementations of METHOD_X, we use pre-trained LLMs for planning that are not finetuned, but rather evaluated solely with few-shot prompting; the full prompts can be found in the Appendix. Sources of Feedback. In theory any type of environment feedback can inform the LLM planner, as long as it can be expressed through language. We focus on the specific forms of feedback shown in Fig , which can be broken down into task-specific feedback, such as success detection, and scene-specific feedback (either ``passive'' or ``active''), which describes the scene. Specific instantiations and implementation details of each type of feedback can be found in Sec , Sec , and Sec respectively for each domain. Success Detection.. Semantic success detection is a binary classification problem of whether the low-level skill has succeeded. Engineered success detectors can operate on ground-truth state in simulation, while learned success detectors can be trained on real examples of successes and failures in the real world . We use the output of success detectors in language form, which we refer to as Success feedback. Passive Scene Description.. While there are many ways to describe the semantics contained within a scene, we use the term Passive Scene Description to broadly describe sources of scene feedback that are consistently provided and follow some structure. Passive Scene Description covers all sources of environment grounding feedback that are automatically provided and injected into the LLM prompt without any active prompting or querying by the LLM planner. One common type of such feedback is object recognition -- we refer to the textual outputs of such object recognizers as Object feedback. We also demonstrate the use of a task-progress scene description in the simulated tabletop rearrangement environment, to which we refer as Scene feedback. Active Scene Description.. As the proactive counterpart to Passive Scene Description, Active Scene Description encompasses sources of feedback that are provided directly in response to active queries by the LLM planner. In this case, the LLM can directly ask a question about the scene, and this question can be answered either by a person, or by another pretrained model, such as a Visual Question Answering (VQA) model . While the previous types of feedback are strictly structured and narrow in their scope, in the Active Scene Description setting the LLM can receive unstructured answers to open-ended questions, allowing it to actively gather information relevant to the scene, the task, or even preferences of the user (in the case of human-provided response). The combined output we send to the LLM planner includes both the LLM-generated question along with the response. As we aim to investigate whether and how a LLM planner can incorporate such feedback and wish to study both structured VQA-style human feedback as well as unstructured human preferences feedback, we only consider human-provided response in this work, which we refer to as Human feedback. figures/types_of_feedback.pdf Various types of textual feedback. success_detection_color Success Detection gives task-specific task completion information, scene_description_color Passive Scene Description gives structured semantic scene information at every planning step, and vqa_color Active Scene Description gives unstructured semantic information only when queried by the LLM planner. 1.4em

## Inferred Evaluation Profile

- Tasks: embodied_household, knowledge_intensive_qa, sequential_decision_making
- Explicit benchmark counts: {}
- Uncovered tasks: none
- Modalities: text
- Interactions: static
- Outputs: action_trajectory, short_answer
- Capabilities: evidence_grounding, long_horizon_planning

## Selected Benchmark Portfolio

- **ALFWorld** (`alfworld`): score=0.537; role=core_task_coverage; source=https://arxiv.org/abs/2010.03768
- **HotpotQA** (`hotpotqa`): score=0.467; role=core_task_coverage; source=https://arxiv.org/abs/1809.09600
- **TriviaQA** (`triviaqa`): score=0.467; role=supplementary_triangulation:knowledge_intensive_qa; source=https://arxiv.org/abs/1705.03551
- **ScienceWorld** (`scienceworld`): score=0.430; role=supplementary_triangulation:sequential_decision_making; source=https://arxiv.org/abs/2203.07540
- **WebArena** (`webarena`): score=0.387; role=supplementary_triangulation:sequential_decision_making; source=https://arxiv.org/abs/2307.13854

## Top Candidates

1. **ALFWorld** (`alfworld`) — 0.537; tasks=['embodied_household', 'sequential_decision_making']
2. **HotpotQA** (`hotpotqa`) — 0.467; tasks=['knowledge_intensive_qa']
3. **TriviaQA** (`triviaqa`) — 0.467; tasks=['knowledge_intensive_qa']
4. **ScienceWorld** (`scienceworld`) — 0.430; tasks=['sequential_decision_making']
5. **WebArena** (`webarena`) — 0.387; tasks=['sequential_decision_making']
6. **GSM8K** (`gsm8k`) — 0.425; tasks=[]
7. **SVAMP** (`svamp`) — 0.425; tasks=[]
8. **WebShop** (`webshop`) — 0.293; tasks=['sequential_decision_making']
9. **MMLU** (`mmlu`) — 0.280; tasks=[]
10. **RealToxicityPrompts** (`realtoxicityprompts`) — 0.280; tasks=[]

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
