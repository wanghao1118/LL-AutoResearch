---
name: autodesign-method-router
description: "Select, compare, validate, or revise an AutoDesign method route for a research Idea. Use when motivation and contributions exist but the intervention, train-free versus training route, backbone roles, R0 probe, or resource-feasible scientific mechanism is undecided or must be reconsidered after a failed R0."
---

# AutoDesign Method Router

Choose the scientific intervention before concrete components. Do not default to a student/teacher/training menu.

## Inputs

Read `input_brief.md` and the current `AUTODESIGN_STATE.md`. Preserve each original contribution claim verbatim. Treat the scientific locks recorded from the user's Motivation, Contributions, Benchmark, initial plan, and explicit constraints as immutable. Keep unstated details available for independent design.

Read `references/route-contract.md` before writing the final artifact.

## Route

1. Build an Idea semantics table for every central term: operational meaning, what it constrains, what it does not constrain, observable implication, disallowed reinterpretation, and unresolved uncertainty. Derive meanings from the supplied Idea and ordinary technical usage; do not import unstated method details or results.
2. Classify the input as `method_specified`, `mechanism_specified`, or `goal_only`.
3. Identify the intervention target implied by every contribution.
4. For `method_specified`, preserve the core intervention and compare implementation choices only.
5. For `mechanism_specified` or `goal_only`, compare at least two meaningfully different route families with different falsifiable predictions.
6. Consider only applicable families: inference-time control, prompting or decoding, retrieval or memory, tool or environment adaptation, data construction, SFT, preference optimization, RL, hybrid, or a contribution-specific alternative.
7. Research current components from primary sources, official repositories, model cards, and benchmark documentation only when selecting implementable components, baselines, or protocols. External material may inform an autonomous choice but may not redefine the Idea.
8. Give every candidate a minimal probe, falsifier, contribution fit, benchmark fit, resource estimate, and rejection condition.
9. Require a low-cost R0 for `goal_only` and for any expensive route whose central feasibility or semantic interpretation remains uncertain. A failed R0 returns to route selection; it does not silently switch the full experiment.
10. Select the smallest sufficient set of conditional roles: backbone, teacher, verifier, retriever, reward model, tool, or training loop.

## Output

Write `method_route.md` using the reference contract. State one selected route, rejected routes, Idea semantics, scientific locks, autonomous choices, sources used for component or protocol selection, resource adaptations, non-claim-bearing pilots, R0 decision, and decision boundary. A changed scientific lock is a blocker, not an accepted downgrade. Use `TBD` only for genuinely unresolved evidence and make it a blocker.

Update `AUTODESIGN_STATE.md` to `METHOD_ROUTE_READY`, `WAITING_FOR_R0_IMPLEMENTATION`, or `R0_FAILED_RETURN_TO_METHOD_ROUTE`.
