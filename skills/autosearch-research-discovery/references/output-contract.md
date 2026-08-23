# Output Contract

Return concise Chinese prose with citations near supported claims. Real research discovery defaults to a portfolio of one to three independent Weaknesses.

## RESEARCH_PORTFOLIO.md

```text
# Research Portfolio

## Field
## Field-Level Insight
## Retained Weaknesses
| ID | Plain-language Weakness | Scope | Type | Status | Why independent |
## Why These Weaknesses Were Split Or Merged
## Ranked-Out Or Reclassified Candidates
## Recommended Next Actions
```

The field-level Insight may connect multiple Weaknesses but must not be used as evidence that they share one mechanism. Keep the portfolio readable; detailed evidence belongs in each Weakness package.

Create one subdirectory per retained Weakness:

```text
weaknesses/
  W01/
    RESEARCH_BRIEF.md
    AUTODESIGN_HANDOFF.md   # only when the status permits it
    RUN_AUDIT.md
  W02/
    ...
```

## RESEARCH_BRIEF.md

```text
# Research Brief

## Field And Scope
## Scope Provenance
## Background
## Insight
## Core Weakness
## Why It Matters
## Strongest Existing Solution And Boundary
## Evidence Status
## Decisive Validation Before Design (required for NEEDS_WEAKNESS_VALIDATION)
## Manifestation 1 / Technical Bottleneck 1
## Manifestation 2 / Technical Bottleneck 2
## Manifestation 3 / Technical Bottleneck 3 (only if necessary)
## Capability-Chain Roles
## Candidate Contribution
## Weakness-Contribution Mapping
## Plain-Language Summary
```

The plain-language summary must say what fails, why it fails, what the candidate changes, and how to test it. Keep it understandable to a general AI researcher.

For `READY_FOR_METHOD_DESIGN`, `Candidate Contribution` contains the proposed research claim. For `NEEDS_WEAKNESS_VALIDATION`, replace it with `Conditional Method Direction` and make the missing decisive test prominent. Other statuses must not be presented as Method Contributions.

## AUTODESIGN_HANDOFF.md

```text
# AutoDesign Handoff

## Frozen Problem Definition
## Required Capabilities
## Candidate Intervention Targets
## Required Data And Labels
## Must-Include Baselines
## Metrics
## Minimal Distinguishing Experiments
## Ablations And Failure Analysis
## Falsification Conditions
## Resource Constraints
## Decisions Left To AutoDesign
```

## RUN_AUDIT.md

```text
# Run Audit

## Mode And Cutoff
## Evidence Used
## Direct Facts
## Cross-Paper Inferences
## Untested Hypotheses
## Strongest Counterevidence
## Missing Or Inaccessible Evidence
## Merge-Split Decision
## Ranked-Out Or Reclassified Candidates
## Final Status
```

P3 search artifacts may remain in an internal `evidence/` directory. For an explicitly requested internal single-best evaluation, preserve the legacy three-file layout without exposing the evaluation switch as a normal user choice.
