# Auto-Bench Plan: fresh2_002

- Status: **AUTOMATIC_LITERATURE_CHECK_PENDING**
- Route: **base_benchmark_adaptation**
- Task-family coverage: **50.0%**
- Decision: best existing match scores 0.830, but portfolio coverage is 50.0%

## Matcher-Visible Paper Input

### Introduction

-2mm Introduction. There is a trending paradigm to couple large language models (LLMs) with external plugins or tools, enabling LLMs to interact with environment and retrieve up-to-date knowledge. The tool-augmented LLMs, often referred to as augmented language models (ALMs), have fueled several prevailing applications like Auto-GPT for autonomous task executions. Existing efforts on ALMs have been widely grounded in the prompting paradigm similar to , which interleaves verbal reasoning and tool-calling consecutively. [t] belowskip=0pt figs/Figure1.pdf Workflow of . Given a question, Planner composes a comprehensive blueprint of interlinked plans prior to tool response. The blueprint instructs Worker to use external tools and collect evidence. Finally, plans and evidence are paired and fed to Solver for the answer. -1em Such paradigm, however, introduces frequent execution and suspension of LLMs, together with potentially huge cost in terms of token consumption. LLMs generate tokens conditioned on the former context. When interacting with external tools, an LLM has to be halted for tool response. Moreover, the APIs of black-box LLMs, such as ChatGPT, are stateless. To resume the token generation, all the historical tokens (including context prompt, exemplars, all previous reasoning traces and observations) are fed into the LLM, leading to significant prompt redundancy. The commercial LLM service provided by OpenAI charges in terms of token consumption. Thereby, prompt redundancy brings substantial expense to average users Single request to solve a multi-step task with Auto-GPT easily exceeds \$1 (excluding API costs). . However, to the best of our knowledge, there is no prior work exploring to reduce the token consumption of ALMs. This paper proposes , a novel prompting paradigm for ALMs. As illustrated in , compartmentalizes the key components of an ALM: step-wise reasoning, tool-calls, and summarization, into three separate modules: Planner, Worker, and Solver. Planner breaks down a task and formulates a blueprint of interdependent plans, each of which is allocated to Worker. Worker retrieves external knowledge from tools to provide evidence. Solver synthesizes all the plans and evidence to generate the ultimate answer to the initial task. As shown in Figure , separates the reasoning process of LLMs from external tools, avoiding the redundancy of interleaved prompts in observation-dependent reasoning, thereby significantly reducing token usage and enhancing prompting efficiency. [t] figs/Figure2.pdf In (a) observation-dependent reasoning, the task requested from a user is first wrapped with context prompt and exemplars, then fed into an LLM to initiate a reasoning process. The LLM generates a thought(T) and an action(A), then waits for the observation(O) from tools. The observation is stacked into the prompt history to start the next LLM call. In (b), Planner produces at once a list of interdependent plans(P) and calls Worker to fetch evidence(E) from tools. The P and E are combined with the task, and then fed into Solver for the final answer. Note that in (a), the context and exemplars are repeatedly fed into the LLM, resulting in prompt redundancy. r 0.5 -10mm figs/scatter_jerry-v2.pdf Overall benchmark performance of different methods. -4mm To holistically evaluate METHOD_X, we conduct experiments over six multi-step and knowledge-intensive NLP benchmarks and a curated dataset. Evaluation baselines of include two non-ALM prompting methods, Direct Prompting, and Chain-of-Thought prompting (CoT) , and a prevailing ALM paradigm, , featuring observation-dependent reasoning. provides an averaged performance over benchmarks in Table , demonstrating consistent efficiency gain of over its observation-dependent counterpart. Furthermore, we demonstrate the potential of for system parameter efficiency through instruction tuning and Specialization . We observe that LLaMa 7B fine-tuned with a small number of epochs can be on par with GPT3.5 in a zero-shot setup, underscoring the capability of to facilitate lightweight and scalable ALM deployment. Contributions. Our contributions to the field of ALM can be summarized as follows: (1) We identify and assess reasoning ability of LLMs without explicit observations (termed foreseeable reasoning). Extensive experiments show that foreseeable reasoning can be harnessed to encourage prompt- efficient ALMs. (2) We introduce a modular framework, , designed to capitalize on the foreseeable reasoning ability of language models. Comprehensive testing suggests that, compared to the prevalent thought-action-observation style ALMs, can achieve comparable or superior performance while substantially reducing token usage. In addition, exhibits greater robustness in real-world scenarios. (3) We demonstrate a pipeline to offload the general ability of foreseeable reasoning from LLMs into smaller language models, enabling the smaller model to utilize unseen tools in zero-shot setups. This research highlights the potential of towards scalable and parameter-efficient ALM.

### Method

-1mm Methodology. -2mm A salient ability of humans is to predict possible outcomes from to-be-conducted actions. The foreseen outcome of action usually turns out to be instructive enough for adapting and planning on the next steps. Similarly, we design a framework described below. -2mm METHOD_X with Plan-Work-Solve Paradigm. -1mm Planner leverages the foreseeable reasoning of LLMs to compose a solution blueprint. Concretely, it contains consecutive tuples where represents a descriptive message of the current step, and , subscripted by step number , is a special token to store presumably correct evidence from corresponding designated Worker[Instruction]. This paradigm enables to tackle multi-step and complex tasks, particularly those where a subsequent step depends on the observations of prior steps, by referring to from previous steps in the instructions given to Workers. Worker enables to interact with the environment through tool-calls. Once Planner provides a blueprint, designated Workers are invoked with instruction input, and populate with real evidence or observations. Solver processes all plans and evidence to formulate a solution to the original task or problem, such as providing answers in QA tasks or returning the work status for action requests. We note that prompting Solver to use the provided plans and evidence "with caution" enhances the overall performance of . We attribute this improvement to Solver's inherent reasoning ability to resolve simple tasks or partially compensate for failures in the Planner or Worker. Prompt Redundancy Reduction. ALM systems based on interleaving reasoning and observations suffer undesirable prompt redundancy as depicted in (a). Consider a typical observation-dependent ALM solving a question with reasoning steps to derive the final response . Starting with a context prompt and a group of exemplars , ALM iteratively generates tuples of Thought, Action, and Observation (TAOs), denoted as . Let denote the number of tokens for a text sequence . The total number of input tokens can be calculated as Eq. ( ). Token_I^ TAO & = (C + S + Q)+ _ j=1 ^ k-1 (C + S + Q + _ t=1 ^ j (T_t + A_t + O_t) ) \\ & = k (Q) _ Question + k (C) _ Context + k ( S ) _ Exemplars + _ j=1 ^ k-1 (k-j) (T_j + A_j + O_j) _ TAOs The equation above suggests that duplicated and identical prompts are used as input redundantly. Since and are usually nontrivial, input tokens quadratically grow oversize as the number of steps increases, usually leading to token limit excess, ridiculously high computation, and time expenses. On the contrary, avoids such interleaving pattern as illustrated in (b). Specifically, let be the plan, evidence variable and evidence response at step , The total input tokens for METHOD_X is: Token_I^ & = (C_ planner + S + Q)+ (C_ solver + Q + _ j=1 ^k P_j + E_j) \\ & 2 (Q) _ Question + 2 (C) _ Context + ( S ) _ Exemplars + _ j=1 ^k (P_j + E_j) _ PEs It is hard to quantitatively measure the difference between the two methods without explicit knowledge of prompting setup. However, if we empirically equalize TAOs with PEs, then Eq. ( ) differs from Eq. ( ) linearly by size of and quadratically by size of to the term . Such analysis directly suggests that as a task sent to ALM becomes increasingly complicated, thus introducing more reasoning steps, can save substantially larger amounts of computation costs in ALM systems. Note that some LLM-based tools potentially introduce additional token consumption. These tokens are also counted in our experiments. Parameter Efficiency by Specialization. A common concern of ALMs is that binding parametric language models and non-parametric tool calls complicates end-to-end training . To mitigate this problem, Toolformer fine-tunes language models on tool-augmented corpus in a self-supervised way. Similarly, makes an attempt to fine-tune reasoning ability on collected reasoning traces from [REDACTED_BENCHMARK] . These approaches, however, are tested in limited setups. Concretely, Toolformer is limited in an independent sampling of tools, thus failing to function on multi-step reasoning tasks. 's approach in fine-tuning completes thought-action-observations trajectories is unproven to generalize well into unseen tasks or tool set. decouples reasoning from tool-calls, allowing to optimize the generic ability of foreseeable reasoning on a Planner module because no tool response is exposed during fine-tuning. Inspired by recent Specialization framework , we attempt to elicit foreseeable reasoning from GPT-3.5 and offload into LLaMa 7B as depicted in . We start by using text-davinci-003 to infer 4000 (Plan, ) blueprints on mixed training data of [REDACTED_BENCHMARK] and [REDACTED_BENCHMARK]. Following the bootstrapping method , we sample those leading to correct answers, yielding approximately 2000 Planner instruction data. A pretrained LLaMa 7B is instruction fine-tuned on 52k self-instruct dataset, producing Alpaca 7B that approximates general ability of text-davinci-003. Subsequently, we further fine-tune Alpaca-7B on the Planner instruction data to obtain a 7B Planner model specialized in foreseeable reasoning. Finally, we assess the potential of Specialization on multiple benchmarks, replacing the Planner with GPT-3.5, Alpaca 7B, and Planner 7B. [t] figs/Figure3.pdf Offloading foreseeable reasoning from GPT-3.5 into Alpaca 7B. A small LLaMa LM is fine-tuned on self-instructed data generated by GPT-3.5, producing Alpaca, endowed with general reasoning ability. Alpaca is then further fine-tuned on blueprints generated by GPT-3.5, leading to Planner 7B, a model specializing in foreseeable reasoning. -1mm

## Inferred Evaluation Profile

- Tasks: knowledge_intensive_qa
- Explicit benchmark counts: {}
- Declared total evaluation breadth: 6
- Uncovered tasks: tool_augmented_nlp
- Modalities: text
- Interactions: interactive_environment, retrieval_tool
- Outputs: short_answer
- Capabilities: evidence_grounding, external_information_retrieval, long_horizon_planning, reasoning_action_interleaving, tool_use

## Selected Benchmark Portfolio

- **TriviaQA** (`triviaqa`): score=0.830; role=core_task_coverage; source=https://arxiv.org/abs/1705.03551
- **HotpotQA** (`hotpotqa`): score=0.813; role=declared_suite_breadth:knowledge_intensive_qa; source=https://arxiv.org/abs/1809.09600

## Top Candidates

1. **TriviaQA** (`triviaqa`) — 0.830; tasks=['knowledge_intensive_qa']
2. **HotpotQA** (`hotpotqa`) — 0.813; tasks=['knowledge_intensive_qa']
3. **FEVER** (`fever`) — 0.400; tasks=[]
4. **ALFWorld** (`alfworld`) — 0.380; tasks=[]
5. **ScienceWorld** (`scienceworld`) — 0.380; tasks=[]
6. **ToolBench** (`toolbench`) — 0.380; tasks=[]
7. **GSM8K** (`gsm8k`) — 0.265; tasks=[]
8. **SVAMP** (`svamp`) — 0.265; tasks=[]
9. **WebArena** (`webarena`) — 0.240; tasks=[]
10. **WebShop** (`webshop`) — 0.240; tasks=[]

## Online Literature Leads

- Online search was disabled or returned no relevant arXiv metadata hits.

## Catalog Admission Proposals

- No benchmark-like online hit met the proposal threshold.

## Adaptation and Synthesis

- Missing task families: ['tool_augmented_nlp']
- Synthesis required: True
- Official and adapted metrics must be reported separately.
- Test examples stay frozen and never seed synthetic records.

## Automatic Literature Validation

Current status: **AUTOMATIC_LITERATURE_CHECK_PENDING**.
- Existing-paper blind test: after matching, reveal the source paper and compare its actual benchmarks with Selected and Top-6 using MATCH / PARTIAL / MISMATCH.
- The source comparison runs in a separate evaluator process; the matcher never receives paper identity, experiment sections, or benchmark labels.
- Every mismatch, missing benchmark, extra benchmark, catalog gap, and route error becomes machine-readable optimization feedback; no user submission is required.
