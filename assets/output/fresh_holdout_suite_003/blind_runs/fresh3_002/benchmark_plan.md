# Auto-Bench Plan: fresh3_002

- Status: **HUMAN_REVIEW_REQUIRED**
- Route: **base_benchmark_adaptation**
- Task-family coverage: **50.0%**
- Decision: best existing match scores 0.777, but portfolio coverage is 50.0%

## Matcher-Visible Paper Input

### Introduction

Everyday household tasks require both commonsense understanding of the world and situated knowledge about the current environment. To create a task plan for ``Make dinner,'' an agent needs common sense: object affordances, such as that the stove and microwave can be used for heating; logical sequences of actions, such as an oven must be preheated before food is added; and task relevance of objects and actions, such as heating and food are actions related to ``dinner'' in the first place. However, this reasoning is infeasible without state feedback. The agent needs to know what food is available in the current environment, such as whether the freezer contains fish or the fridge contains chicken. Autoregressive large language models (LLMs) trained on large corpora to generate text sequences conditioned on input prompts have remarkable multi-task generalization. This ability has recently been leveraged to generate plausible action plans in context of robotic task planning by either scoring next steps or generating new steps directly. In scoring mode, the LLM evaluates an enumeration of actions and their arguments from the space of what's possible. For instance, given a goal to ``Make dinner'' with first action being ``open the fridge'', the LLM could score a list of possible actions: ``pick up the chicken'', ``pick up the soda'', ``close the fridge'', , ``turn on the lightswitch.'' In text-generation mode, the LLM can produce the next few words, which then need to be mapped to actions and world objects available to the agent. For example, if the LLM produced ``reach in and pick up the jar of pickles,'' that string would have to neatly map to an executable action like ``pick up jar.'' A key component missing in LLM-based task planning is state feedback from the environment. The fridge in the house might not contain chicken, soda, or pickles, but a high-level instruction ``Make dinner'' doesn't give us that world state information. Our work introduces situated-awareness in LLM-based robot task planning. figs/teaser.pdf METHOD_X leverages LLMs' strengths in both world knowledge and programming language understanding to generate situated task plans that can be directly executed. -0.5cm We introduce METHOD_X, a prompting scheme that goes beyond conditioning LLMs in natural language. METHOD_X utilizes programming language structures, leveraging the fact that LLMs are trained on vast web corpora that includes many programming tutorials and code documentation (Fig. ). METHOD_X provides an LLM a Pythonic program header that imports available actions and their expected parameters, shows a list of environment objects, and then defines functions like make dinner whose bodies are sequences of actions operating on objects. We incorporate situated state feedback from the environment by asserting preconditions of our plan, such as being close to the fridge before attempting to open it, and responding to failed assertions with recovery actions. What's more, we show that including natural language comments in METHOD_X programs to explain the goal of the upcoming action improves task success of generated plan programs. [ht] figs/plan_and_exec.pdf Our METHOD_X s include import statement, object list, and example tasks (PROMPT for Planning). The Generated Plan is for microwave salmon. We highlight prompt comments, actions as imported function calls with objects as arguments, and assertions with recovery steps. PROMPT for State Feedback represents example assertion checks. We further show execution of the program. We illustrate a scenario where an assertion succeeds or fails, and how the generated plan corrects the error before executing the next step. Full Execution of the program is shown in bottom-right.

### Method

METHOD_X We represent robot plans as pythonic programs. Following the paradigm of LLM prompting, we create a prompt structured as pythonic code and use an LLM to complete the code (Fig. ). We use features available in Python to construct prompts that elicit an LLM to generate situated robot task plans, conditioned on a natural language instruction. Representing Robot Plans as Pythonic Functions Plan functions consist of API calls to action primitives, comments to summarize actions, and assertions for tracking execution (Fig. ). Primitive actions use objects as arguments. For example, the ``put salmon in the microwave'' task includes API calls like find(salmon). [!t] figs/plan_eg.pdf Pythonic METHOD_X\ plan for put salmon in the microwave. We utilize comments in the code to provide natural language summaries for subsequent sequences of actions. Comments help break down the high-level task into logical sub-tasks. For example, in Fig. , the put salmon in microwave task is broken down into sub-tasks using comments `` grab salmon'' and `` put salmon in microwave''. This partitioning could help the LLM to express its knowledge about tasks and sub-tasks in natural language and aid planning. Comments also inform the LLM about immediate goals, reducing the possibility of incoherent, divergent, or repetitive outputs. Prior work has also shown the efficacy of similar intermediate summaries called `chain of thought' for improving performance of LLMs on a range of arithmetic, commonsense, and symbolic reasoning tasks. We empirically verify the utility of comments (Tab. ; column Comments ). Assertions provide an environment feedback mechanism to make sure that the preconditions hold, and enable error recovery when they do not. For example, in Fig. , before the grab(salmon) action, the plan asserts the agent is close to salmon. If not, the agent first executes find(salmon). In Tab. , we show that such assert statements (column Feedback ) benefit plan generation. [ht] Evaluation of generated programs on [REDACTED_BENCHMARK]. METHOD_X uses 3 fixed example programs, except the Davinci backbone which can fit only 2 in the available API. use 1 dynamically selected example, as described in their paper. LangPrompt uses 3 natural language text examples. Best performing model with a GPT3 backbone is shown in blue (used for our ablation studies); best performing model overall shown in bold. We also showcase how each METHOD_X feature adds to the performance of the method. llcclrrr CBCEFB 2 * & 3 c --- Prompt Format and Parameters --- & & & & \\ CBCEFB & Format & Comments & Feedback & LLM Backbone & & & \\ 1 & METHOD_X & & & Codex & 0.11 & 0.05 & 0.09 \\ EFEFEF 2 & METHOD_X & & & Davinci & 0.22 0.04 & 0.60 0.04 & 0.46 0.04 \\ 2-4 3 & METHOD_X & & & GPT3 & 0.34 0.08 & 0.84 0.01 & 0.65 0.05 \\ EFEFEF 4 & METHOD_X & & & GPT3 & 0.28 0.04 & 0.82 0.01 & 0.56 0.02 \\ 5 & METHOD_X & & & GPT3 & 0.30 0.00 & 0.65 0.01 & 0.58 0.02 \\ EFEFEF 6 & METHOD_X & & & GPT3 & 0.18 0.04 & 0.68 0.01 & 0.42 0.02 \\ 7 & LangPrompt & - & - & GPT3 & 0.00 0.00 & 0.36 0.00 & 0.42 0.02 \\ 2-4 EFEFEF 8 & 3 c Baseline from Huang et al. & GPT3 & 0.00 0.00 & 0.45 0.03 & 0.21 0.03 \\ Constructing Programming Language Prompts We provide information about the environment and primitive actions to the LLM through prompt construction. As done in few-shot LLM prompting, we also provide the LLM with examples of sample tasks and plans. Fig. illustrates our prompt function which takes in all the information (observations, action primitives, examples) and produces a Pythonic prompt for the LLM to complete. The LLM then predicts the next task (.) as an executable function (microwave salmon in Fig. ). In the task microwave salmon, a reasonable first step that an LLM could generate is take out(salmon, grocery bag). However, the agent responsible for the executing the plan might not have a primitive action to take out. To inform the LLM about the agent's action primitives, we provide them as Pythonic import statements. These encourage the LLM to restrict its output to only functions that are available in the current context. To change agents, METHOD_X\ just needs a new list of imported functions representing agent actions. A grocery bag object might also not exist in the environment. We provide the available objects in the environment as a list of strings. Since our prompting scheme explicitly lists out the set of functions and objects available to the model, the generated plans typically contain actions an agent can take and objects available in the environment. METHOD_X\ also includes a few example tasks---fully executable program plans. Each example task demonstrates how to complete a given task using available actions and objects in the given environment. These examples demonstrate the relationship between task name, given as the function handle, and actions to take, as well as the restrictions on actions and objects to involve. Task Plan Generation and Execution The given task is fully inferred by the LLM based on the METHOD_X\ prompt. Generated plans are executed on a virtual agent or a physical robot system using an interpreter that executes each action command against the environment. Assertion checking is done in a closed-loop manner during execution, providing current environment state feedback.

## Inferred Evaluation Profile

- Tasks: embodied_household
- Explicit benchmark counts: {}
- Declared total evaluation breadth: 0
- Uncovered tasks: symbolic_reasoning
- Modalities: text
- Interactions: retrieval_tool
- Outputs: action_trajectory, structured_answer
- Capabilities: evidence_grounding, long_horizon_planning, tool_use

## Selected Benchmark Portfolio

- **ALFWorld** (`alfworld`): score=0.777; role=core_task_coverage; source=https://arxiv.org/abs/2010.03768

## Top Candidates

1. **ALFWorld** (`alfworld`) — 0.777; tasks=['embodied_household']
2. **ScienceWorld** (`scienceworld`) — 0.357; tasks=[]
3. **ToolBench** (`toolbench`) — 0.352; tasks=[]
4. **WebArena** (`webarena`) — 0.330; tasks=[]
5. **Mind2Web** (`mind2web`) — 0.297; tasks=[]
6. **HotpotQA** (`hotpotqa`) — 0.267; tasks=[]
7. **FEVER** (`fever`) — 0.250; tasks=[]
8. **TriviaQA** (`triviaqa`) — 0.250; tasks=[]
9. **WebShop** (`webshop`) — 0.220; tasks=[]
10. **GSM8K** (`gsm8k`) — 0.120; tasks=[]

## Online Literature Leads

- Online search was disabled or returned no relevant arXiv metadata hits.

## Catalog Admission Proposals

- No benchmark-like online hit met the proposal threshold.

## Adaptation and Synthesis

- Missing task families: ['symbolic_reasoning']
- Synthesis required: True
- Official and adapted metrics must be reported separately.
- Test examples stay frozen and never seed synthetic records.

## Human Validation

Current status: **HUMAN_REVIEW_REQUIRED**.
- Existing-paper blind test: after matching, reveal the source paper and compare its actual benchmarks with Selected and Top-6 using MATCH / PARTIAL / MISMATCH.
- New method without literature gold: two independent reviewers score construct alignment, task representativeness, metric validity, data quality, leakage control, and execution feasibility.
Automated retrieval metrics do not approve either validation track.
