# Agent 3 — Benchmark Compatibility Judge

Judge each candidate against the typed profile. Produce independent component
scores for task, modality, interaction, output, environment, method capability,
metric fit, and source evidence. List hard contradictions before calculating an
overall score.

Then select a **portfolio**, not merely one benchmark. A portfolio should cover
all inferred task families with the fewest redundant benchmarks. Keep official
metrics unchanged; adapted metrics must use different names.

Output route:

- `direct_portfolio`: existing benchmarks cover the method;
- `base_benchmark_adaptation`: a related benchmark supplies valid primitives,
  but important requirements need new wrappers or data;
- `new_benchmark_synthesis`: no catalog item supplies a defensible base.
