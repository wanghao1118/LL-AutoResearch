# Auto-Bench Plan: installed_skill_smoke

- Status: **AUTOMATIC_LITERATURE_CHECK_PENDING**
- Route: **direct_portfolio**
- Task-family coverage: **100.0%**
- Decision: portfolio covers 100.0% of inferred task families; weakest task-normalized selected compatibility is 0.890

## Matcher-Visible Paper Input

### Introduction

We study multimodal web agents that understand screenshots and complete shopping tasks on websites.

### Method

The agent plans browser actions, observes visual feedback, and uses self-reflection after failed trajectories.

## Inferred Evaluation Profile

- Tasks: computer_use, web_navigation
- Explicit benchmark counts: {}
- Declared total evaluation breadth: 0
- Uncovered tasks: none
- Modalities: image, text, web
- Interactions: browser
- Outputs: action_trajectory
- Capabilities: long_horizon_planning, self_reflection, tool_use

## Selected Benchmark Portfolio

- **VisualWebArena** (`visualwebarena`): score=0.890; role=core_task_coverage; source=https://arxiv.org/abs/2401.13649
- **Mind2Web** (`mind2web`): score=0.777; role=supplementary_triangulation:web_navigation; source=https://arxiv.org/abs/2306.06070
- **WebArena** (`webarena`): score=0.730; role=supplementary_triangulation:web_navigation; source=https://arxiv.org/abs/2307.13854

## Top Candidates

1. **VisualWebArena** (`visualwebarena`) — 0.890; tasks=['computer_use', 'web_navigation']
2. **Mind2Web** (`mind2web`) — 0.777; tasks=['web_navigation']
3. **WebArena** (`webarena`) — 0.730; tasks=['web_navigation']
4. **WebShop** (`webshop`) — 0.570; tasks=['web_navigation']
5. **OSWorld** (`osworld`) — 0.550; tasks=['computer_use']
6. **ALFWorld** (`alfworld`) — 0.357; tasks=[]
7. **ScienceWorld** (`scienceworld`) — 0.357; tasks=[]
8. **ToolBench** (`toolbench`) — 0.272; tasks=[]
9. **GAIA** (`gaia`) — 0.153; tasks=[]
10. **HotpotQA** (`hotpotqa`) — 0.153; tasks=[]

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
