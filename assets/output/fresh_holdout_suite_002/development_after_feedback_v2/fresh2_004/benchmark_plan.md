# Auto-Bench Plan: fresh2_004

- Status: **AUTOMATIC_LITERATURE_CHECK_PENDING**
- Route: **new_benchmark_synthesis**
- Task-family coverage: **0.0%**
- Decision: no catalog task family covers the explicitly stated method domain

## Matcher-Visible Paper Input

### Introduction

Introduction. Ever since the birth of the field, AI researchers have sought to create programs that can converse in natural language with the same grace and flexibility as people. While even relatively simple models, such as Eliza from 1966 , can generate responses to some prompts that seem reasonable, it has always been relatively easy to generate prompts that expose their weaknesses compared to people --- their lack of true ``understanding." While large language models (LLMs) such as GPT-4 and ChatGPT have far surpassed expectations of just a few years ago, they are no different in this respect. Indeed the internet is now awash with examples of people reveling in getting ChatGPT to generate output that even a 5-year-old human child would know to be ill-advised. figures/fig1.pdf METHOD_X makes use of a large language model (LLM) to produce the PDDL description of the given problem, then leverages a classical planner for finding an optimal plan, then translates the raw plan back to natural language using the LLM again. Given how LLMs are designed and trained, this phenomenon should come as no surprise. They are not specifically built to demonstrate understanding. They are trained to generate sequences of words that might be plausible to a human given a prior context. In the terms of Mahowald et al. LLMs have become amazingly proficient at linguistic competence --- knowing how to say things; but they are not nearly as good at functional competence --- knowing what to say. Specifically, they can be (relatively) easily fooled by, for example, asking for the result of a straightforward arithmetic problem that does not appear in their training corpus or by asking for the solution to a novel planning problem that requires knowledge about how the world works. [ standard jigsaw, title=A Failure Example of GPT-4 in Planning, opacityback=0, ] Problem (P1): You have 5 blocks. One cannot place more than one block on another block. b5 is on top of b3. b4 is on top of b2. b2 is on top of b1. b3 is on top of b4. b1 is on the table. b5 is clear. Your arm is empty. Your goal is to move the blocks. b1 should be on top of b2. b3 should be on top of b5. b4 should be on top of b1. \\\\ GPT-4: \\ 1. Move b5 from b3 to the table. \\ 2. Move b3 from b4 to b5. \\ 3. Move b4 from b2 to the table. \\ 4. Move b2 from b1 to b5. \\ 5. Move b1 from the table to b2. \\ 6. Move b4 from the table to b1. r 0.35 -160pt figures/[REDACTED_BENCHMARK]-intro.png Does that mean that we should increase efforts to include all arithmetic and planning problems in their training corpus? Clearly, that is a fool's errand. On the other hand, why should it be necessary? We already have calculators and general-purpose symbolic planners that are guaranteed to produce correct answers. Thus a natural alternative approach, and one that we are admittedly not the first to explore, is to connect LLMs to such tools. With this motivation in mind, the objective of the research reported in this paper is, for the first time, to enable LLMs to solve planning problems correctly. We aim to do so without altering the LLMs themselves, even with finetuning . Rather, we introduce a methodology, called METHOD_X by which, when posed a natural language description of a planning problem, the LLM: outputs a problem description suitable as input to a general-purpose planner; solves the problem using the general-purpose planner; and converts the output of the planner back to natural language (or connects to action executors of a robot). Our extensive empirical evaluations indicate that METHOD_X is able to generate correct solutions to many more planning problems than are LLMs on their own. While demonstrated in this paper on planning problems, this general methodology can be applied to any class of problems for which we have a sound and complete solver, such as arithmetic problems (by leveraging calculators). : In this paper, we do not ask the LLM to recognize that it has been posed a prompt that is suitable for processing using the proposed METHOD_X pipeline. A valuable future research direction will be to consider recognizing when a prompt should be processed by METHOD_X.

### Method

-15pt Method. -5pt This section first uses a running example to investigate ways for formulating planning prompts in PDDL and then introduces the METHOD_X method. -10pt Large Language Model as a PDDL Writer. LLMs are bad at planning (or long-horizon reasoning) but they are good at describing and translating textual inputs, including re-writing planning prompts in the PDDL format. The intuition is that we can view PDDL as a different language than English, so re-writing planning prompts in PDDL is essentially a ``machine translation" task that LLMs are known to excel at. Here we provide an example of a PDDL problem file written by GPT-4 without any prompt-engineering. As we see, the generated file appears to have the correct PDDL syntax but uses a made-up predicate (empty) and misses the initial condition that b1 is on the table. [ standard jigsaw, title=An Example PDDL Problem File Written by GPT-4, opacityback=0, ] Prompt: purple Description of Problem (P1) + Provide me with the problem PDDL file that describes the planning problem directly without further explanations. \\\\ GPT-4 (the generated problem PDDL): (:objects b1 b2 b3 b4 b5 - block) \\ (:init (on b5 b3) (on b4 b2) (on b2 b1) (on b3 b4) (clear b5) (empty)) \\ (:goal (and (on b1 b2) (on b3 b5) (on b4 b1))) -10pt In-Context Learning. -5pt LLMs are known to be capable of in-context learning without finetuning their parameters. By in-context learning, we mean LLMs' ability to perform unseen downstream tasks by simply conditioning on a few input-label pairs (demonstrations) . Here is a pair of problem descriptions in natural language and in PDDL provided to GPT-4 as context. When the context is included with the prompt from the example above, the resulting PDDL problem file is directly solvable by the planner. [ standard jigsaw, title=An Example PDDL Problem File Written by GPT-4 with Context, opacityback=0, ] Context (shaded): An example planning problem is: You have 5 blocks. b2 is on top of b5. b5 is on top of b1. b1 is on top of b4. b3 is on top of b2. b4 is on the table. b3 is clear. Your arm is empty. Your goal is to move the blocks. b4 should be on top of b3. The problem PDDL is: (:objects b1 b2 b3 b4 b5) \\ (:init (arm-empty) (on b1 b4) (on b2 b5) (on b3 b2) \\ (on-table b4) (on b5 b1) (clear b3)) \\ (:goal (and (on b4 b3)))) Prompt: purple Description of Problem (P1) + purple Context + Provide me with the problem PDDL file that describes the planning problem directly without further explanations. \\ GPT-4 (the generated problem PDDL): (:objects b1 b2 b3 b4 b5 ) \\ (:init (arm-empty) (on-table b1) (on b2 b1) (on b3 b4) \\ (on b4 b2) (on b5 b3) (clear b5))) \\ (:goal (and (on b1 b2) (on b3 b5) (on b4 b1))) \\\\ Planner:\\ (unstack b5 b3) (putdown b5) (unstack b3 b4) (stack b3 b5) \\ (unstack b4 b2) (putdown b4) (unstack b2 b1) (putdown b2) \\ (pickup b1) (stack b1 b2) (pickup b4) (stack b4 b1) METHOD_X (METHOD_X ) Having introduced the LLM's ability to encode problems in PDDL and in-context learning, we are ready to introduce the proposed METHOD_X solution (the bottom of Fig. ). In particular, we assume that for each problem domain, a human expert can provide a domain description (i.e. action preconditions and effects) that will be fixed for all problem instances that happen in that domain. While the problem of automatically generating the description is another valuable research question, in this proposed work, we assume that the description is available as a PDDL domain file. The METHOD_X method is directly applicable as a natural language interface for giving tasks to robot systems. For instance, assume we want a robot to act as a bartender to make cocktails. It is reasonable to tell it what actions it can take, but leave itself to infer how to make new cocktails most efficiently given a set of ingredients to combine. Moreover, we assume the agent is provided with a minimal example that demonstrates what an example problem PDDL looks like for a simple problem inside that domain. Next, the agent is provided with a new (potentially quite complicated) problem ( ). The LLM then uses the in-context learning to infer the problem PDDL file corresponding to . Once the problem PDDL file is generated, we feed it into any classical planner, together with the provided domain PDDL file, to generate a PDDL plan . In the end, the LLM translates the PDDL plan back into the natural language to finish up the METHOD_X pipeline. \\ purple To summarize, the assumptions we need for METHOD_X are: A robot knows when to trigger METHOD_X based on its conversation with a human user. A domain PDDL is provided to define the actions that the robot is capable of. This specification is task-agnostic --- the entities relevant to the task are specified in the LLM-generated problem PDDL. A simple problem description in natural language and its corresponding problem PDDL file are also provided.

## Inferred Evaluation Profile

- Tasks: none
- Explicit benchmark counts: {}
- Declared total evaluation breadth: 0
- Uncovered tasks: classical_planning, creative_writing
- Modalities: text
- Interactions: retrieval_tool
- Outputs: generated_passage, reasoning_trace
- Capabilities: external_information_retrieval, long_horizon_planning, tool_use

## Selected Benchmark Portfolio

- No existing benchmark passed the portfolio threshold.

## Top Candidates

1. **HotpotQA** (`hotpotqa`) — 0.267; tasks=[]
2. **ToolBench** (`toolbench`) — 0.267; tasks=[]
3. **FEVER** (`fever`) — 0.250; tasks=[]
4. **TriviaQA** (`triviaqa`) — 0.250; tasks=[]
5. **ALFWorld** (`alfworld`) — 0.187; tasks=[]
6. **ScienceWorld** (`scienceworld`) — 0.187; tasks=[]
7. **Mind2Web** (`mind2web`) — 0.160; tasks=[]
8. **WebArena** (`webarena`) — 0.160; tasks=[]
9. **WebShop** (`webshop`) — 0.127; tasks=[]
10. **GSM8K** (`gsm8k`) — 0.120; tasks=[]

## Online Literature Leads

- Online search was disabled or returned no relevant arXiv metadata hits.

## Catalog Admission Proposals

- No benchmark-like online hit met the proposal threshold.

## Adaptation and Synthesis

- Missing task families: ['classical_planning', 'creative_writing']
- Synthesis required: True
- Official and adapted metrics must be reported separately.
- Test examples stay frozen and never seed synthetic records.

## Automatic Literature Validation

Current status: **AUTOMATIC_LITERATURE_CHECK_PENDING**.
- Existing-paper blind test: after matching, reveal the source paper and compare its actual benchmarks with Selected and Top-6 using MATCH / PARTIAL / MISMATCH.
- The source comparison runs in a separate evaluator process; the matcher never receives paper identity, experiment sections, or benchmark labels.
- Every mismatch, missing benchmark, extra benchmark, catalog gap, and route error becomes machine-readable optimization feedback; no user submission is required.
