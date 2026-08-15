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
- a materialized identity record for every variant and benchmark;

## `implementation_notes.md`

Record:

- selected method route and full configuration;
- scientific locks and autonomous design choices;
- selected components and source revisions;
- selected baseline configurations;
- evidence class and benchmark provenance for every experiment;
- training or inference state;
- experiment-to-entrypoint map;
- environment file;
- exact smoke, experiment, and aggregate commands;
- primary result path;
- experiment schedule path;
- table and chart paths;
- resource estimate;
- resource adaptations, non-claim-bearing pilots, and blockers;
- execution mode `fresh_experiment`.

## Decision-relevant preflight

Each preflight check records the accepted value, materialized value, literal failure condition, and next action. Include, when applicable:

- variant and model revision;
- data manifest, training input path, sample count, sampling policy, and planned-versus-observed group distributions;
- source, teacher, scaffold, turn, token, label, difficulty, or quality distributions required by the evidence plan;
- benchmark identity, provenance, revision, split, scaffold, timeout, and metric definition;
- maximum length, epochs, learning rate, objective, and trainable parameter ratio;
- prompt, tool, retriever, decoding, state, and inference-budget identity for train-free routes;
- the production dataflow from required filtering or transformation to the exact consumed artifact.

Do not add a check without a concrete failure and changed next action. A failed scientific-lock or planned-composition check blocks expensive execution.

## Result contract

Write `result_contract.json` with schema version `1.0`, the generated-project-relative primary result path, and format `autodesign-results-v1`. The result records contain experiment ID, evidence class, variant ID, benchmark identity and provenance, benchmark task ID, seed, planned metrics, and completion status. Failed runs remain explicit records or execution failures; they are not converted to successful zeros.

## Acceptance

Implementation is ready only when all planned experiment IDs have entrypoints, all four preflight categories execute, the environment is materialized, commands are non-empty, result and chart paths stay inside the generated project, and smoke passes where resources permit.
