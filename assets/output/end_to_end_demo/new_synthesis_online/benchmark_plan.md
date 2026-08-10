# Auto-Bench Plan: workflow_demo_new_synthesis

- Status: **HUMAN_REVIEW_REQUIRED**
- Route: **new_benchmark_synthesis**
- Task-family coverage: **0.0%**
- Decision: no catalog task family covers the explicitly stated method domain

## Matcher-Visible Paper Input

### Introduction

We study conditional polyphonic music generation from audio motifs and affect descriptions.

### Method

The method emits multi-track audio events while preserving harmonic structure, timbre, and long-range rhythm.

## Inferred Evaluation Profile

- Tasks: none
- Uncovered tasks: audio_music_generation
- Modalities: audio, text
- Interactions: static
- Outputs: generated_audio
- Capabilities: none

## Selected Benchmark Portfolio

- No existing benchmark passed the portfolio threshold.

## Top Candidates

1. **MMLU** (`mmlu`) — 0.280; tasks=[]
2. **FEVER** (`fever`) — 0.200; tasks=[]
3. **HotpotQA** (`hotpotqa`) — 0.200; tasks=[]
4. **ALFWorld** (`alfworld`) — 0.120; tasks=[]
5. **ScienceWorld** (`scienceworld`) — 0.120; tasks=[]
6. **ToolBench** (`toolbench`) — 0.120; tasks=[]
7. **GAIA** (`gaia`) — 0.060; tasks=[]
8. **Mind2Web** (`mind2web`) — 0.060; tasks=[]
9. **OSWorld** (`osworld`) — 0.060; tasks=[]
10. **WebArena** (`webarena`) — 0.060; tasks=[]

## Online Literature Leads

- [PerformanceNet: Score-to-Audio Music Generation with Multi-Band Convolutional Residual Network](https://arxiv.org/abs/1811.04357v1) — query: `"audio music generation" benchmark dataset evaluation audio text`
- A task-topical hit may corroborate catalog fit; admission as a new benchmark still requires a complete task, metric, access, license, and source record.

## Catalog Admission Proposals

- No benchmark-like online hit met the proposal threshold.

## Adaptation and Synthesis

- Missing task families: ['audio_music_generation']
- Synthesis required: True
- Official and adapted metrics must be reported separately.
- Test examples stay frozen and never seed synthetic records.

## Human Validation

Current status: **HUMAN_REVIEW_REQUIRED**.
- Existing-paper blind test: after matching, reveal the source paper and compare its actual benchmarks with Selected and Top-6 using MATCH / PARTIAL / MISMATCH.
- New method without literature gold: two independent reviewers score construct alignment, task representativeness, metric validity, data quality, leakage control, and execution feasibility.
Automated retrieval metrics do not approve either validation track.

- Synthesis execution: **BASE_RECORDS_REQUIRED**
- Executed modules: []
