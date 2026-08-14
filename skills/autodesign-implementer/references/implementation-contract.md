# Implementation Contract

## Required project surfaces

- environment definition;
- smoke entrypoint;
- experiment entrypoint or launcher;
- aggregate entrypoint;
- one entrypoint mapping for every experiment ID;
- result contract;
- explicit `experiment_schedule.json` cells;
- chart generators;
- preflight implementation.

For a `provenance_replay`, also require the copied source observations, the source run path, a declaration that no observed value is changed, and a schedule derived one-for-one from those records. Do not present replay as fresh model execution.

## `implementation_notes.md`

Record:

- selected method route and full configuration;
- selected components and source revisions;
- selected baseline configurations;
- training or inference state;
- experiment-to-entrypoint map;
- environment file;
- exact smoke, experiment, and aggregate commands;
- primary result path;
- experiment schedule path;
- table and chart paths;
- resource estimate;
- implemented downgrades and blockers.
- execution mode (`fresh_experiment` or `provenance_replay`) and, for replay, the exact scientific evidence that remains absent.

## Result contract

Write `result_contract.json` with schema version `1.0`, the generated-project-relative primary result path, and format `autodesign-results-v1`. The result records contain experiment ID, variant ID, benchmark task ID, seed, planned metrics, and completion status. Failed runs remain explicit records or execution failures; they are not converted to successful zeros.

## Acceptance

Implementation is ready only when all planned experiment IDs have entrypoints, all four preflight categories execute, the environment is materialized, commands are non-empty, result and chart paths stay inside the generated project, and smoke passes where resources permit.
