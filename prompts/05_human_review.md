# Agent 5 — Post-Match Literature Audit

This agent runs only after the blind matcher exits. It reveals the source paper
title, official link, and experiment-derived benchmark list to the researcher.
For each source paper, present:

1. the exact anonymized Introduction and Method that the matcher received;
2. benchmarks actually used by the paper and the experiment sections that name
   them;
3. Auto-Bench Selected and Top-6 recommendations;
4. selected matches, missed paper benchmarks, and recommendations absent from
   the paper;
5. a human `MATCH`, `PARTIAL`, or `MISMATCH` judgement with notes.

Paper identity and benchmark gold remain outside the matcher process. A
two-person construct-suitability review is run separately for a new method
without literature gold.
