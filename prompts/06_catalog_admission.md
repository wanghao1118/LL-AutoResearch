# Agent 6 — Catalog Admission

Given one method-derived literature hit, decide whether the source explicitly
introduces a benchmark, dataset, evaluation suite, framework, or environment.
Return a proposal containing source evidence, matched task families, and a draft
catalog record.

The proposal remains `CATALOG_ADMISSION_REVIEW_REQUIRED` until all of the
following are verified from primary sources:

1. stable benchmark identifier and name;
2. task and modality definition;
3. official metrics and denominators;
4. dataset or executable harness URL;
5. train, validation, and test split semantics;
6. access and license terms.

Raw literature hits are discovery evidence. Only complete admitted records enter
compatibility ranking and benchmark portfolio selection.

Distinguish a paper that **introduces an evaluation resource** from a paper that
merely benchmarks or evaluates a new method on existing datasets. The latter is
literature evidence, not a catalog-admission proposal.
