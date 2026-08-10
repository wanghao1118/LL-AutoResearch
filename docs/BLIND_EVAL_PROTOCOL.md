# Blind Evaluation Protocol

## Question

Given only anonymized Introduction and Method content, can Auto-Bench retrieve a
suitable portfolio that contains the benchmarks later used by the original
paper?

## Isolation

1. Official arXiv source packages are downloaded to `assets/input/source_papers/`.
2. `step1_build_blind_fixtures.py` extracts Introduction and Method only.
3. Benchmark aliases, paper identity, citations, result-heavy sentences, title,
   authors, source path, and source ID are removed from visible cases.
4. Experiment-section labels are written to `assets/input/blind_gold/`.
5. `step2_run_blind_matching.py` runs each case in a temporary sandbox holding
   only the package, public catalog, and one visible case.
6. `step3_evaluate_blind_results.py` first validates every completed report,
   then opens hidden labels in a separate process.
7. A paper used for feedback ceases to be untouched. Before changing the
   matcher, the next paper fixture and gold are frozen separately. Its first
   result is immutable; later outputs are labeled feedback regressions.

## Metrics

- primary benchmark Recall@1/3/5/6;
- mean reciprocal rank of the first primary benchmark;
- route accuracy;
- selected-portfolio primary recall;
- leakage pass rate;
- hidden-label access count.

Modeled recall covers only paper benchmarks already represented in the public
catalog. Outside-catalog paper choices remain visible by name after reveal and
must be addressed through catalog admission, base adaptation, or synthesis;
they are never silently counted as recovered.

Exact benchmark recovery is diagnostic rather than proof of exclusive
suitability: Introduction/Method may specify only a task family, allowing more
than one scientifically defensible benchmark. After matching, the human audit
reveals the paper identity, official source link, actual benchmark list, and
evidence sections. The researcher then labels each case `MATCH`, `PARTIAL`, or
`MISMATCH` based on Selected and Top-6 recovery, misses, and extra recommendations.
