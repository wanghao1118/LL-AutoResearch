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
4. Classify every autonomous choice as `high` or `low` outcome impact. A high-impact freedom materially changes what the experiment can show, including who generates training data, teacher or judge roles, or the execution substrate.
5. Resolve every high-impact freedom through either an explicit user decision or a low-cost R0 that compares at least two candidate instantiations under fixed controls and a literal selection or kill rule. Do not accept plausibility, documentation, or a single default as resolution evidence.
6. For `method_specified`, preserve the core intervention and compare implementation choices only.
7. For `mechanism_specified` or `goal_only`, compare at least two meaningfully different route families with different falsifiable predictions.
8. Consider only applicable families: inference-time control, prompting or decoding, retrieval or memory, tool or environment adaptation, data construction, SFT, preference optimization, RL, hybrid, or a contribution-specific alternative.
9. Research current components from primary sources, official repositories, model cards, and benchmark documentation only when selecting implementable components, baselines, or protocols. External material may inform an autonomous choice but may not redefine the Idea.
10. Give every candidate a minimal probe, falsifier, contribution fit, benchmark fit, resource estimate, and rejection condition.
11. Require a low-cost R0 for `goal_only`, every unresolved high-impact autonomous choice, and any expensive route whose central feasibility or semantic interpretation remains uncertain. A failed R0 returns to route selection; it does not silently switch the full experiment.
12. Select the smallest sufficient set of conditional roles: backbone, teacher, verifier, retriever, reward model, tool, or training loop.

## Output

Write `method_route.md` using the reference contract. State one selected route, rejected routes, Idea semantics, scientific locks, autonomous choices with outcome-impact classifications and resolution evidence, sources used for component or protocol selection, resource adaptations, non-claim-bearing pilots, R0 decision, and decision boundary. A changed scientific lock or unresolved high-impact freedom is a blocker, not an accepted default. Use `TBD` only for genuinely unresolved evidence and make it a blocker.

Update `AUTODESIGN_STATE.md` to `METHOD_ROUTE_READY`, `WAITING_FOR_R0_IMPLEMENTATION`, or `R0_FAILED_RETURN_TO_METHOD_ROUTE`.
