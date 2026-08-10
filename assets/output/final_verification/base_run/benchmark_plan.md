# Auto-Bench Plan: workflow_demo_base_adaptation

- Status: **AUTOMATIC_LITERATURE_CHECK_PENDING**
- Route: **base_benchmark_adaptation**
- Task-family coverage: **50.0%**
- Decision: best existing match scores 0.677, but portfolio coverage is 50.0%

## Matcher-Visible Paper Input

### Introduction

We study an agent that follows a laboratory protocol in an interactive simulator, observes assay outcomes, and revises the procedure.

### Method

The method decomposes a wet-lab objective into reagent preparation, instrument operation, measurement, and verification subgoals. It executes action-observation trajectories with long-horizon planning.

## Inferred Evaluation Profile

- Tasks: scientific_experiment_planning, sequential_decision_making
- Explicit benchmark counts: {}
- Declared total evaluation breadth: 0
- Uncovered tasks: none
- Modalities: text
- Interactions: interactive_environment
- Outputs: action_trajectory
- Capabilities: long_horizon_planning, tool_use

## Selected Benchmark Portfolio

- **ALFWorld** (`alfworld`): score=0.677; role=core_task_coverage; source=https://arxiv.org/abs/2010.03768

## Top Candidates

1. **ALFWorld** (`alfworld`) — 0.677; tasks=['sequential_decision_making']
2. **ScienceWorld** (`scienceworld`) — 0.677; tasks=['sequential_decision_making']
3. **WebArena** (`webarena`) — 0.570; tasks=['sequential_decision_making']
4. **WebShop** (`webshop`) — 0.460; tasks=['sequential_decision_making']
5. **ToolBench** (`toolbench`) — 0.352; tasks=[]
6. **Mind2Web** (`mind2web`) — 0.297; tasks=[]
7. **HotpotQA** (`hotpotqa`) — 0.153; tasks=[]
8. **OSWorld** (`osworld`) — 0.130; tasks=['sequential_decision_making']
9. **FEVER** (`fever`) — 0.120; tasks=[]
10. **GSM8K** (`gsm8k`) — 0.120; tasks=[]

## Online Literature Leads

- Online search was disabled or returned no relevant arXiv metadata hits.

## Catalog Admission Proposals

- No benchmark-like online hit met the proposal threshold.

## Adaptation and Synthesis

- Missing task families: ['scientific_experiment_planning']
- Synthesis required: True
- Official and adapted metrics must be reported separately.
- Test examples stay frozen and never seed synthetic records.

## Automatic Literature Validation

Current status: **AUTOMATIC_LITERATURE_CHECK_PENDING**.
- Existing-paper blind test: after matching, reveal the source paper and compare its actual benchmarks with Selected and Top-6 using MATCH / PARTIAL / MISMATCH.
- The source comparison runs in a separate evaluator process; the matcher never receives paper identity, experiment sections, or benchmark labels.
- Every mismatch, missing benchmark, extra benchmark, catalog gap, and route error becomes machine-readable optimization feedback; no user submission is required.

- Synthesis execution: **DRAFTS_READY_FOR_AUTOMATIC_VALIDATION**
- Executed modules: ['interaction_wrapper', 'compositional_recombination', 'counterfactual_perturbation']
