---
name: autosearch-research-judge
description: Independently review an AutoSearch research package for evidence faithfulness, scope integrity, Method Weakness validity, technical depth, contribution alignment, clarity, and AutoDesign readiness. Use after discovery; do not generate or improve the candidate before scoring it.
---

# AutoSearch Research Judge

Review a supplied research portfolio or individual `RESEARCH_BRIEF`, `AUTODESIGN_HANDOFF`, and available evidence without reading the generator's intended answer or hidden rationale.

Read [references/review-rubric.md](references/review-rubric.md). Score the package before proposing corrections. Do not reward complexity, length, fashionable terminology, or similarity to a known paper.

Default to `packet_only` review. Verify external sources only when the user requests `source_verification`; otherwise mark claims that cannot be checked from the packet.

Keep Method Weakness, Benchmark Weakness, and Validation Gap separate. Do not upgrade missing evidence into a method claim.

For a portfolio, first review whether candidates were correctly split or merged. Then judge every Weakness independently. Do not average scores across Weaknesses, transfer evidence between them, or let one strong package upgrade another. A shared field-level Insight does not establish a shared causal mechanism.

Return the portfolio-structure verdict when applicable, then each Weakness verdict, scores, decisive reasons, and one highest-priority revision. Do not rewrite the full package unless explicitly requested.
