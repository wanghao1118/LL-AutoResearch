# Table types and role-specific strategies

Classify a table by its scientific role before selecting a layout template. The role controls information density and emphasis; the template controls row/column geometry. Several tables may share a role, and a paper may contain multiple `main_benchmark` tables.

| `table_type` | Scientific role | Default strategy |
|---|---|---|
| `main_benchmark` | Core evidence comparing the focal method and baselines across benchmarks | Rich dataset × metric hierarchy, focal-system identification, scoped best/second-best, optional meaningful family bands, width fitting |
| `main_tradeoff` | Claim-bearing quality–efficiency, performance–cost, or robustness trade-off | Separate evidence families, preserve absolute values, scoped ranking, focal-system identification |
| `ablation` | Full/reference configuration versus controlled component or axis changes | Flat or lightly spaced rows, reference-row highlight, no default best/second-best ranking, retain unfavorable outcomes |
| `analysis` | Mechanism, sensitivity, error, failure, or interpretability evidence | Descriptive hierarchy, restrained emphasis, no decorative family taxonomy or automatic ranking |
| `diagnostic` | Incomplete, non-claim-bearing, or protocol-diagnostic evidence | Status/protocol visible as identity, no ranking, no implication that partial evidence is a formal aggregate |
| `simple_comparison` | Small direct comparison or descriptive summary | Minimal header and rules, no bands, no automatic ranking, compact layout |

## Main benchmark contract

`main_benchmark` is not synonymous with “Table 1.” A paper may use several core benchmark tables for different datasets, modalities, protocols, or evaluation families. Each table must still:

- declare `focal_methods` using exact input names;
- display at least one non-focal baseline;
- cover at least two displayed benchmark groups;
- contain focal and baseline evidence in every displayed benchmark group;
- define metric direction and a valid ranking universe;
- use visual richness only for real scientific dimensions such as benchmark blocks, metric families, protocol regimes, or model families.

## Role versus template

Examples:

- `main_benchmark` + `benchmark-wide`: standard methods × benchmarks main table;
- `main_benchmark` + `transposed-benchmark`: few systems evaluated on many benchmarks;
- `main_tradeoff` + `quality-efficiency`: quality and cost as parallel evidence blocks;
- `ablation` + `benchmark-wide`: clear component comparison without ranking decoration;
- `diagnostic` + `hierarchical-method-budget`: protocol/status fields remain visible when they affect interpretation.

Explicit config may refine a role strategy, but it must not contradict the scientific role—for example, a diagnostic table must not use best/second-best markers to imply a claim-bearing leaderboard.
