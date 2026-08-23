# AutoSearch Skills

This directory contains the two reusable Skills for the Prompt-first AutoSearch workflow:

- `autosearch-research-discovery`: starts from a research `FIELD`, runs the frozen P3 discovery prompt, reviews innovation potential, deepens evidence-backed Weaknesses, and prepares Candidate Contribution and AutoDesign handoff artifacts.
- `autosearch-research-judge`: independently reviews evidence, scope, Weakness validity, innovation potential, clarity, and AutoDesign readiness.

The frozen P3 prompt remains unchanged. Discovery writes the raw P3 candidates before loading later-stage guidance, so P3 baseline behavior can still be compared with the Skill-enhanced result.

The intended order is:

```text
FIELD
-> frozen P3 discovery
-> innovation review
-> Weakness deepening
-> Candidate Contribution / AutoDesign handoff
-> independent Judge
```

Copy either Skill directory into `${CODEX_HOME:-~/.codex}/skills/` to install it locally.
