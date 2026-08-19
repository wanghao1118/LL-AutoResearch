# Integrity Audit Contract

## Required evidence

| Requirement | Authoritative artifact | Pass condition |
| --- | --- | --- |
| Handoff fidelity | AutoSearch handoff and input brief | Motivation, Contribution, and Benchmark preserved verbatim; extra user input classified, not discarded |
| Idea consistency | input brief and original request | scientific intent, meanings, and locks preserved without importing unstated method details |
| Route validity | experiment design and R0 record | selected route justified; every autonomous choice has an outcome-impact class; every high-impact freedom has an explicit user resolution or an executed comparison of at least two candidate instantiations |
| Family coverage | experiment design | main, ablation, case-study, and analysis families populated or every absent family justified under `## Absent families`; the design gate only checks that a reason was written, so judge each reason yourself — a filler such as `n/a`, `TBD`, or `待定`, or a reason that does not follow from the contributions, is a FAIL |
| Evidence eligibility | experiment design | every claim and test axis has an eligible claim-bearing falsifier; pilots and smokes are separate |
| Case-study integrity | experiment design and produced cases | pre-result selection rule followed; declared category counts including failures produced; no outcome-dependent selection |
| Target integrity | expected effects and effect comparison | every entry keeps `SIMULATED_TARGET`; no target edited post-hoc; no target in reports, tables, figures, or verdicts; every entry compared and every miss retained |
| Implementation fidelity | generated project, notes, and preflight | accepted locks, identities, compositions, families, experiments, and protocols implemented |
| Execution completion | execution record and logs | current preflight, smoke, experiment, aggregate, and collect exit zero in order |
| Result completeness | schedule, raw results, and summary | scheduled and observed cells, families, evidence classes, provenance, and metrics match with no unresolved unexpected cells |
| Numeric integrity | raw results, tables, figures | recomputed values match all displays |
| Route closure | result route, tuning record, next round, latest execution and diagnosis | no required action remains unexecuted, unrecompared, or unrediagnosed |
| Claim scope | diagnosis and report text | conclusions do not exceed observed evidence |

## Verdict

Use PASS only when every requirement has direct evidence and no unresolved blocker. Use FAIL for a concrete contradiction or missing required evidence. Do not replace the verdict with a score.

Literal FAIL conditions include: a high-impact freedom is unresolved or backed only by a single documented default; a scientific lock changed; a surrogate carries an official benchmark identity or claim-bearing role; a required filtered or transformed artifact is not consumed by the launch command; materialized data violates the planned composition; a raw cell falls outside the accepted schedule; a `simulated_target` was edited after execution; a simulated target is presented as an observation; a `MISSED` or `NOT_EVALUABLE` comparison row was dropped; a case study was selected on observed scores; a contribution verdict rests on proximity to a design-time target; new results leave comparison, diagnosis, or audit stale; baseline execution status contradicts reports; or a declared table, figure, or case category is missing.
