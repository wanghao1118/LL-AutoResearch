# SEED paper extraction for AutoDesign

Status: `PAPER_EXTRACTION_ONLY`

This document extracts the Motivation, Contribution, and Benchmark from **SEED: Self-Evolving On-Policy Distillation for Agentic Reinforcement Learning** (arXiv:2607.14777v1, 2026-07-16). It is not an experiment design and contains no new observed result.

The canonical machine-readable handoff is `assets/input/seed_arxiv_2607_14777_handoff.json`. The paper PDF is preserved at `assets/input/arxiv_2607.14777.pdf`.

## Input boundary

The AutoDesign input preserves the paper's scientific problem, three contribution claims, benchmark identities, evaluation roles, metrics, aggregation rules, and the requirement that the deployed SEED policy use no hindsight skill prompt or auxiliary skill machinery.

The handoff deliberately does not copy the paper's observed scores into target effects. Author-selected models, baselines, hyperparameters, and hardware are recorded below only to distinguish experimental context from benchmark definition; they are not immutable scientific locks for a new AutoDesign run.

## Motivation

### M1. Long-horizon agent learning needs intermediate decision supervision

Language agents in embodied environments, web navigation, and search-based QA must repeatedly interpret observations, act, use tools, and revise plans. Their consequences can appear many turns later. Outcome-based reinforcement learning provides a terminal success or reward signal, but does not identify which intermediate observation, action, or tool call caused progress or failure.

### M2. A terminal scalar reward wastes useful structure inside a trajectory

A failed episode can contain several correct subgoals and only one decisive local mistake. A successful episode can contain a reusable workflow that the scalar outcome never labels. Broadcasting the same trajectory-level advantage to all action tokens therefore leaves a gap between episode-level outcomes and token-level policy learning.

### M3. Completed trajectories expose useful hindsight

After an episode ends, the full history reveals achieved subgoals, deviations, decisive observations, effective action orderings, and failure-avoidance rules. This hindsight can be expressed as natural-language skills and used as privileged training supervision.

### M4. Existing hindsight mechanisms can become static or externally dependent

Reflection, episodic memory, retrieved experience, fixed teachers, static skill datasets, and one-time distillation can leave supervision tied to an earlier policy distribution or require extra inference-time context. As the policy changes, it visits new states and produces new failure modes; its supervision should change with it.

### M5. The paper's design requirements

The desired supervision is:

- **On-policy:** derived from states, actions, and failures induced by the current policy.
- **Dense:** converts trajectory hindsight into decision-token guidance rather than only terminal credit.
- **Self-evolving:** refreshes trajectory collection and analysis as the policy improves.
- **Parametric at deployment:** internalized into the policy, with no skill prompt, analyzer, skill bank, memory, or retrieval module required at inference.

## Contributions

### C1. Self-evolving hindsight-skill training framework

**We propose SEED, a two-stage self-evolving on-policy distillation framework that first teaches the policy to extract reusable natural-language hindsight skills from completed successful and failed trajectories and then uses the latest policy checkpoint as both the rollout actor and trajectory analyzer during reinforcement learning, allowing decision making and skill analysis to evolve jointly without requiring skills at inference time.**

SEED uses two stages:

1. **Hindsight-skill SFT:** completed successful and failed trajectories are analyzed into concise reusable workflows or failure-avoidance rules; the policy is fine-tuned to perform this trajectory analysis.
2. **Self-evolving OPD:** the latest policy checkpoint both collects on-policy trajectories and analyzes them into skills. Updating the shared model advances the actor and analyzer together.

The training-only skills are not added to the deployed agent's prompt.

### C2. Policy-synchronized dense on-policy distillation

**We introduce a policy-synchronized hindsight on-policy distillation mechanism that re-scores fixed on-policy action tokens under ordinary and skill-augmented contexts, converts the detached skill-induced log-probability shift into a dense token-level gate, and jointly optimizes the resulting distillation signal with outcome-based reinforcement learning to provide decision-specific credit aligned with the current policy distribution.**

For an action sequence sampled by the current policy, SEED keeps the sampled tokens fixed and evaluates them under two contexts:

- the ordinary interaction history;
- the same history augmented with the trajectory's hindsight skill.

The detached skill-induced log-probability shift is transformed into a token-level gate. The resulting on-policy distillation loss is jointly optimized with outcome-based RL and KL regularization. The intended mechanism is to give different action tokens different hindsight credit while keeping supervision aligned with the policy's current trajectory distribution.

### C3. Empirical performance, efficiency, and robustness claim

**We conduct extensive experiments across text-based and vision-based long-horizon agentic tasks, demonstrating that SEED improves task performance and sample efficiency over representative prompting, outcome-only reinforcement learning, and self-distillation or skill-distillation baselines, generalizes to unseen scenarios, and requires no additional skill machinery at inference time.**

For AutoDesign, C3 is a claim that requires fresh evidence. It is not an input fact, and the paper's published numbers are not copied into expected effects.

## Benchmark details

### Primary main-table scope

| Benchmark task | Capability | Evaluation scope | Metric and aggregation |
| --- | --- | --- | --- |
| ALFWorld Seen | Text-based embodied household interaction | 140 tasks; Pick, Look, Clean, Heat, Cool, Pick2 | Success rate per family; equal-weight mean of the six family success rates |
| WebShop | Interactive product search and purchase | Standard 128 test tasks | Normalized task-completion score averaged and scaled by 100; exact success rate |
| Search-based QA | Search, evidence inspection, and answer synthesis | 51,713 questions from Natural Questions, TriviaQA, PopQA, HotpotQA, 2WikiMultiHopQA, MuSiQue, and Bamboogle | Accuracy per dataset; equal-weight mean of the seven dataset accuracies |

The Search-based QA aggregate is dataset-balanced. It must not be replaced by a micro-average over all 51,713 questions.

### Robustness, efficiency, and extension scope

| Evaluation | Role | Reported scope | Metric |
| --- | --- | --- | --- |
| ALFWorld Unseen | Out-of-distribution generalization | 134 tasks over the same six families | Per-family and macro-average success rate |
| ALFWorld and WebShop at 20/40/60/80/100% data | Sample efficiency | Five training-data fractions | ALFWorld macro success rate and WebShop exact success rate, compared with GRPO under matched fractions and a full-data reference |
| Sokoban 6x6 | Vision-based spatial planning | Sample count and split not reported in v1 | Success rate |
| EZPoints from Gym Cards | Vision-based recognition plus sequential arithmetic | Sample count and split not reported in v1 | Success rate |

### Evaluation-time interface lock

The proposed method must be evaluated using only the ordinary task prompt and environment interaction history. Hindsight skills, the trajectory analyzer, a skill bank, retrieval, and an augmented decision prompt are training-only and must not be present at test time.

Baselines that receive a skill during validation or testing must be marked explicitly and cannot be presented as having the same deployment interface.

### Paper-reported training-data context, not benchmark locks

For each benchmark configuration, the paper reports selecting 180 SFT tasks and executing eight independent rollouts per task, giving 1,440 completed trajectories. The RL stage reports 2,400 task instances for ALFWorld, 2,400 for WebShop, and 19,200 for Search-based QA. These counts are the authors' experiment construction choices, not intrinsic official benchmark splits.

Because the rollout group size is eight, these RL task-instance counts must not be mislabeled as total trajectory counts.

### Paper-reported author configuration, excluded from the fixed input

- Primary backbones: Qwen2.5-3B-Instruct, Qwen2.5-7B-Instruct, and Qwen3-1.7B-Instruct.
- Vision extension backbone: Qwen2.5-VL-3B-Instruct.
- Offline SFT analyzer: GLM-5.2, temperature 0.0, maximum response length 4,096.
- Hindsight-skill SFT: three epochs after lightweight format validation.
- RL: 150 policy updates; batch size 16 for ALFWorld and WebShop, 128 for Search; rollout group size 8.
- Reported optimization values: learning rate 1e-6, clip 0.2, OPD gate sharpness 5.0, OPD coefficient 0.01, KL coefficient 0.01.
- Context limits: prompt length 2,048 for ALFWorld and 4,096 for WebShop/Search; response length 512.
- Maximum interaction steps: 30 for ALFWorld, 15 for WebShop, 4 for Search.
- Author compute: eight NVIDIA A800 80GB GPUs.
- Reproduced comparison families: Vanilla, Skill-Prompt, GRPO, Skill-GRPO, Skill-GRPO with test-time skills, OPSD, GRPO+OPSD, Skill-SD, RLSD, and SDAR. ReAct appears in the ALFWorld Unseen and vision-extension comparisons.

These choices are retained for provenance and later feasibility comparison only. AutoDesign must independently decide the implementable backbone, fair baselines, and training schedule under the available hardware.

## Details not reported in arXiv v1

- Random seeds, independent run counts, uncertainty intervals, and significance tests.
- Exact task manifests for the selected SFT and RL subsets.
- Exact ALFWorld and WebShop environment revisions and dependency versions.
- Exact Search-R1 retrieval backend, search-index snapshot, and retrieval parameters.
- Evaluation sample counts and split definitions for Sokoban 6x6 and EZPoints.
- Full optimizer, scheduler, precision, distributed-training, and checkpoint-selection configuration.
- The number of SFT trajectory-skill pairs retained after format validation.

These gaps must stay explicit during experiment design. They are autonomous choices or R0 questions, not facts to be invented.

## AutoDesign readiness

The Motivation, C1-C3, and Benchmark are complete enough to initialize the design phase. The design must still resolve feasibility under the available two-GPU context and any high-impact choices about the analyzer, backbone, data materialization, and execution substrate before a claim-bearing run can begin.
