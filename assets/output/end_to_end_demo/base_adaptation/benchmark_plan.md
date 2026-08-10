# Auto-Bench Plan: workflow_demo_base_adaptation

- Status: **HUMAN_REVIEW_REQUIRED**
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
3. **OSWorld** (`osworld`) — 0.650; tasks=['sequential_decision_making']
4. **WebArena** (`webarena`) — 0.570; tasks=['sequential_decision_making']
5. **VisualWebArena** (`visualwebarena`) — 0.550; tasks=['sequential_decision_making']
6. **WebShop** (`webshop`) — 0.460; tasks=['sequential_decision_making']
7. **ToolBench** (`toolbench`) — 0.352; tasks=[]
8. **Mind2Web** (`mind2web`) — 0.297; tasks=[]
9. **GAIA** (`gaia`) — 0.173; tasks=[]
10. **HotpotQA** (`hotpotqa`) — 0.153; tasks=[]

## Online Literature Leads

- Online search was disabled or returned no relevant arXiv metadata hits.

## Catalog Admission Proposals

- No benchmark-like online hit met the proposal threshold.

## Adaptation and Synthesis

- Missing task families: ['scientific_experiment_planning']
- Synthesis required: True
- Official and adapted metrics must be reported separately.
- Test examples stay frozen and never seed synthetic records.

## Human Validation

Current status: **HUMAN_REVIEW_REQUIRED**.
- Existing-paper blind test: after matching, reveal the source paper and compare its actual benchmarks with Selected and Top-6 using MATCH / PARTIAL / MISMATCH.
- New method without literature gold: two independent reviewers score construct alignment, task representativeness, metric validity, data quality, leakage control, and execution feasibility.
Automated retrieval metrics do not approve either validation track.

- Synthesis execution: **DRAFTS_READY_FOR_HUMAN_REVIEW**
- Executed modules: ['interaction_wrapper', 'compositional_recombination', 'counterfactual_perturbation']
