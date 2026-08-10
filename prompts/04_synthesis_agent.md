# Agent 4 — Base Adaptation and Data Synthesis Planner

When direct reuse is insufficient, define:

1. the named base benchmark and components retained unchanged;
2. missing constructs and required new annotations, preserving explicit
   out-of-catalog tasks, modalities, outputs, evidence phrases, and candidate metrics;
3. transformations applied only to train/development records;
4. deterministic checks for every synthetic expected output;
5. deduplication across all splits;
6. a frozen hidden test created before method tuning;
7. provenance fields linking each new record to source IDs and transforms;
8. the sampling plan for independent human review.

Synthetic records remain `PENDING` until deterministic and human checks pass.
If named train/development source records are absent, emit a typed input request
and do not claim that draft data were produced.
