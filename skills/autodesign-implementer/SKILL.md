---
name: autodesign-implementer
description: "Implement, revise, or materialize an accepted AutoDesign method route and evidence plan as a real runnable research project. Use when generated_project, environments, entrypoints, preflight checks, commands, result contracts, observed-data charts, or training and inference state must be created or aligned with accepted scientific decisions."
---

# AutoDesign Implementer

Translate accepted scientific decisions into executable code without inventing a different method.

## Inputs

Read `method_route.md`, `evidence_plan.md`, required R0 evidence, `AUTODESIGN_STATE.md`, and `references/implementation-contract.md`.

## Implement

1. Materialize the project under the run's `generated_project/` directory.
2. Preserve the accepted intervention, component identities, baseline configurations, protocol locks, downgrades, experiments, variants, tasks, metrics, and seeds.
3. Map every accepted experiment ID to a runnable entrypoint.
4. Include a complete environment definition with every real runtime dependency and compatible version. Do not assume model frameworks or benchmark SDKs are preinstalled.
5. Implement four decision-relevant preflight categories: data contract, benchmark interface, metric contract, and method sanity.
6. Make smoke run all preflights and a tiny representative path.
7. Generate non-empty smoke, experiment, and aggregate commands. Commands must operate from `generated_project/` under Linux Bash.
8. Make launchers honor `AUTODESIGN_MAX_PARALLEL_JOBS` and use only `CUDA_VISIBLE_DEVICES`; leave existing GPU processes unchanged.
9. Preserve training objectives, datasets, learning curves, checkpoints, and reload behavior for training routes. Preserve prompts, decoding, tools, retrieval state, and inference budgets for train-free routes.
10. Generate declared tables and figures from observed results, never predicted values.
11. Run local preflight and smoke when their resource contract permits it. Repair literal failures before handoff.
12. When validating a migration against an existing observed run, copy the authoritative raw records into the new run, label the project as `provenance_replay`, preserve every value, and schedule exactly the replayed cells. A replay validates implementation and worker handoffs; it does not count as a new experiment or fill evidence absent from the source run.

## Output

Write `implementation_notes.md`, the project environment, runnable entrypoints, `commands.sh`, an explicit `experiment_schedule.json`, and a result contract described in the reference. Record exact deviations as blockers instead of silently simplifying the study.

Update `AUTODESIGN_STATE.md` to `IMPLEMENTATION_READY` and set the next Skill to `autodesign-executor`.
