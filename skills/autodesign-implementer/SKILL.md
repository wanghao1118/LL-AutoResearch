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
2. Preserve the accepted intervention, scientific locks, component identities, baseline configurations, experiment evidence classes, protocol decisions, experiments, variants, tasks, metrics, and seeds. Do not turn a blocked claim-bearing experiment into a pilot without returning to evidence design.
3. Map every accepted experiment ID to a runnable entrypoint.
4. Include a complete environment definition with every real runtime dependency and compatible version. Do not assume model frameworks or benchmark SDKs are preinstalled.
5. Implement four decision-relevant preflight categories: data contract, benchmark interface and provenance, metric and protocol contract, and method sanity. Every check names the concrete failure it detects and the changed next action.
6. Make smoke run all preflights and a tiny representative path.
7. Generate non-empty smoke, experiment, and aggregate commands. Commands must operate from `generated_project/` under Linux Bash.
8. Make launchers honor `AUTODESIGN_MAX_PARALLEL_JOBS` and use only `CUDA_VISIBLE_DEVICES`; leave existing GPU processes unchanged.
9. Preserve training objectives, datasets, learning curves, checkpoints, and reload behavior for training routes. Preserve prompts, decoding, tools, retrieval state, and inference budgets for train-free routes.
10. Before expensive execution, materialize and inspect each variant's scientific identity. For data-based routes record the model revision, data manifest, sample count, sampling policy, planned-versus-observed composition and quality axes, training input path, maximum length, epochs, learning rate, and trainable parameter ratio when applicable. For train-free routes record the corresponding prompt, tool, retriever, state, decoding, and budget identities.
11. When filtering, decontamination, selection, or transformation is required, materialize the derived data artifact and make the launch command consume that exact artifact. A unit test of the transformation does not prove the production data path uses it.
12. Generate declared tables and figures from observed results, never predicted values.
13. Run local preflight and smoke when their resource contract permits it. Repair literal failures before handoff; a scientific-lock or planned-composition mismatch returns to the owning Skill instead of being waived.

## Output

Write `implementation_notes.md`, the project environment, runnable entrypoints, `commands.sh`, an explicit `experiment_schedule.json`, preflight reports, and a result contract described in the reference. Record exact deviations as blockers instead of silently simplifying the study.

Update `AUTODESIGN_STATE.md` to `IMPLEMENTATION_READY` and set the next Skill to `autodesign-executor`.
