---
name: autodesign-method-router
description: "Select, compare, validate, or revise an AutoDesign method route for a research Idea. Use when motivation and contributions exist but the intervention, train-free versus training route, backbone roles, R0 probe, or resource-feasible scientific mechanism is undecided or must be reconsidered after a failed R0."
---

# AutoDesign Method Router

Choose the scientific intervention before concrete components. Do not default to a student/teacher/training menu.

## Inputs

Read `input_brief.md` and the current `AUTODESIGN_STATE.md`. Preserve each original contribution claim verbatim. Treat only explicitly declared constraints as locks.

Read `references/route-contract.md` before writing the final artifact.

## Route

1. Classify the input as `method_specified`, `mechanism_specified`, or `goal_only`.
2. Identify the intervention target implied by every contribution.
3. For `method_specified`, preserve the core intervention and compare implementation choices only.
4. For `mechanism_specified` or `goal_only`, compare at least two meaningfully different route families with different falsifiable predictions.
5. Consider only applicable families: inference-time control, prompting or decoding, retrieval or memory, tool or environment adaptation, data construction, SFT, preference optimization, RL, hybrid, or a contribution-specific alternative.
6. Research current components from primary papers, official repositories, model cards, and benchmark documentation when selection depends on current availability.
7. Give every candidate a minimal probe, falsifier, contribution fit, benchmark fit, resource estimate, and rejection condition.
8. Require a low-cost R0 for `goal_only`. A failed R0 returns to route selection; it does not silently switch the full experiment.
9. Select the smallest sufficient set of conditional roles: backbone, teacher, verifier, retriever, reward model, tool, or training loop.

## Output

Write `method_route.md` using the reference contract. State one selected route, rejected routes, sources, explicit locks, downgrades, R0 decision, and decision boundary. Use `TBD` only for genuinely unresolved evidence and make it a blocker.

Update `AUTODESIGN_STATE.md` to `METHOD_ROUTE_READY`, `WAITING_FOR_R0_IMPLEMENTATION`, or `R0_FAILED_RETURN_TO_METHOD_ROUTE`.
