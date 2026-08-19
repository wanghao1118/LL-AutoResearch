# AutoSearch Handoff Contract

## Ownership

AutoSearch is an upstream module owned outside this repository. AutoDesign consumes its exported result and must not depend on how it was produced. Treat every handoff field as authoritative scientific intent and preserve it verbatim in `input_brief.md`.

## Required content

Three things must arrive, whatever the transport:

| Field | Required | Meaning |
| --- | --- | --- |
| `motivation` | yes | why the Idea matters and what gap it closes |
| `contribution` | yes | the numbered claims this run must support or refute |
| `benchmark` | yes | the named datasets, splits, and metrics the claims are judged on |

A handoff missing any of the three is a blocker. Do not select a benchmark, invent a contribution, or infer a motivation to fill a gap.

## Channel A: canonical file

Preferred transport is `autosearch_handoff.json`, read from the run directory or `assets/input/`:

```json
{
  "schema_version": "1.0",
  "motivation": "one or more paragraphs of literal upstream text",
  "contribution": [
    "C1: <literal claim text>",
    "C2: <literal claim text>"
  ],
  "benchmark": {
    "primary": [
      {"name": "<official benchmark name>", "metric": "<metric>", "note": "<protocol note>"}
    ],
    "secondary": [{"name": "<benchmark>", "purpose": "<why>"}],
    "metrics": ["<metric>"],
    "train_test_split": {"train": "<...>", "test": "<...>"},
    "reported_baselines": ["<system>"],
    "constraints": {"evaluation_protocol": "<...>", "reporting": "<...>"}
  }
}
```

Only `motivation`, `contribution`, and `benchmark` are required. Accept `contributions` as an alias for `contribution`. Inside `benchmark`, only `primary` is required; treat every other key as optional enrichment.

## Channel B: natural language

AutoSearch is under separate development and its export may drift or arrive as prose. Accept Motivation, Contribution, and Benchmark pasted directly into the conversation, or as Markdown, and normalize them yourself.

This is a real input path, not a degraded one. A Skill invocation such as `/run-autodesign` followed by free-form text is expected usage. The user may also supply more than the three required items — an initial experiment plan, preferred baselines, related work, compute limits, or a partial design. Absorb every extra item into `input_brief.md` and classify it as a scientific lock, an autonomous choice, or a resource constraint. Never discard supplied information because the schema has no field for it, and never demand JSON when the three required items are already present in prose.

When normalizing prose:

1. Quote the literal input first, under a heading that names its channel.
2. Number the contributions `C1..Cn` in the order given. Do not merge, split, or reword them.
3. Record each benchmark exactly as named. Preserve the official identifier including version.
4. List every ambiguous term with the operational definition you will use, and mark it as an assumption to be confirmed.
5. Record anything the input did not state and this run must choose as an autonomous design choice.

## Unresolved and conflicting input

- An ambiguous term becomes an explicit operational definition plus an assumption record, never a silent choice.
- A conflict between two handoff statements is a blocker reported to the user; do not resolve it by preference.
- A field the handoff omits is an autonomous design choice subject to outcome-impact classification.
- A handoff-reported numeric result is a design-time reference for a simulated target. It is never an observation for this run.

## `input_brief.md`

Structure it as:

1. `## Handoff source` — channel, file path when applicable, timestamp.
2. `## Motivation (literal)`.
3. `## Contribution (literal, numbered)`.
4. `## Benchmark (literal)`.
5. `## Additional user-supplied input (literal)` — every extra item that arrived with the request.
6. `## Scientific locks` — with the exact source line for each.
7. `## Autonomous design choices` — each with `high` or `low` outcome impact.
8. `## Resource constraints`.
9. `## Operational definitions and assumptions`.
10. `## Blockers`.

Later Skills may resolve an autonomous choice. No Skill may rewrite a scientific lock.
