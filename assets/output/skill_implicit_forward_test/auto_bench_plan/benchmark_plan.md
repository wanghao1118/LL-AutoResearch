# Auto-Bench Plan: multimodal_ecommerce_reflective_agent

- Status: **AUTOMATIC_LITERATURE_CHECK_PENDING**
- Route: **base_benchmark_adaptation**
- Task-family coverage: **75.0%**
- Decision: best existing match scores 0.813, but portfolio coverage is 75.0%

## Matcher-Visible Paper Input

### Introduction

We study a multimodal autonomous agent for goal-directed online shopping. Given a natural-language purchase request and only the rendered webpage screenshot as its primary visual observation, the agent must understand product cards, prices, attributes, controls, and page state; navigate an e-commerce website; and complete the requested purchase task. The setting combines screenshot-based computer use, web navigation, and long-horizon sequential decision making. Evaluation must separate end-to-end goal completion from visual grounding, constraint satisfaction, planning efficiency, robustness to interface variation, and recovery after action failure.

### Method

At every interaction step, the agent receives the user goal, the current webpage screenshot, and the browser action history. A planner decomposes the request into subgoals and produces a multi-step plan. A visual grounding module identifies actionable interface targets from the screenshot. An action policy invokes browser actions such as click, type, scroll, select, back, and terminate, then consumes the next screenshot and execution feedback. When an action fails, produces no useful state change, reaches an unexpected page, or violates a subgoal expectation, a self-reflection module performs self-evaluation over the attempted action, observed failure, and plan state; it proposes a corrected subgoal or browser action and retries under a bounded action budget. The final output is a browser action trajectory and a terminal selected-product or completed-order state. The evaluation should compare the complete method with no-reflection, no-visual-grounding, and no-explicit-planner variants and should log screenshots, actions, failures, reflections, retries, latency, and cost.

## Inferred Evaluation Profile

- Tasks: computer_use, sequential_decision_making, web_navigation
- Explicit benchmark counts: {}
- Declared total evaluation breadth: 0
- Uncovered tasks: visual_reasoning
- Modalities: image, text, web
- Interactions: browser, interactive_environment
- Outputs: action_trajectory, selected_product, visual_answer
- Capabilities: long_horizon_planning, self_reflection, tool_use

## Selected Benchmark Portfolio

- **WebShop** (`webshop`): score=0.813; role=core_task_coverage; source=https://arxiv.org/abs/2207.01206
- **OSWorld** (`osworld`): score=0.763; role=core_task_coverage; source=https://arxiv.org/abs/2404.07972

## Top Candidates

1. **WebShop** (`webshop`) — 0.813; tasks=['sequential_decision_making', 'web_navigation']
2. **OSWorld** (`osworld`) — 0.763; tasks=['computer_use', 'sequential_decision_making']
3. **ALFWorld** (`alfworld`) — 0.623; tasks=['sequential_decision_making']
4. **ScienceWorld** (`scienceworld`) — 0.623; tasks=['sequential_decision_making']
5. **ToolBench** (`toolbench`) — 0.352; tasks=[]
6. **GAIA** (`gaia`) — 0.233; tasks=[]
7. **VisualWebArena** (`visualwebarena`) — 0.184; tasks=['computer_use', 'sequential_decision_making', 'web_navigation']
8. **WebArena** (`webarena`) — 0.163; tasks=['sequential_decision_making', 'web_navigation']
9. **HotpotQA** (`hotpotqa`) — 0.153; tasks=[]
10. **Mind2Web** (`mind2web`) — 0.135; tasks=['web_navigation']

## Online Literature Leads

- Online search was disabled or returned no relevant arXiv metadata hits.

## Catalog Admission Proposals

- No benchmark-like online hit met the proposal threshold.

## Adaptation and Synthesis

- Missing task families: ['visual_reasoning']
- Synthesis required: True
- Official and adapted metrics must be reported separately.
- Test examples stay frozen and never seed synthetic records.

## Automatic Literature Validation

Current status: **AUTOMATIC_LITERATURE_CHECK_PENDING**.
- Existing-paper blind test: after matching, reveal the source paper and compare its actual benchmarks with Selected and Top-6 using MATCH / PARTIAL / MISMATCH.
- The source comparison runs in a separate evaluator process; the matcher never receives paper identity, experiment sections, or benchmark labels.
- Every mismatch, missing benchmark, extra benchmark, catalog gap, and route error becomes machine-readable optimization feedback; no user submission is required.
