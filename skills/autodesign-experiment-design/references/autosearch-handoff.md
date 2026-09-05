# AutoSearch Handoff Contract

## Ownership

AutoSearch is an upstream module owned outside this repository. AutoDesign consumes its exported result and must not depend on how it was produced. Treat every supplied handoff field as authoritative scientific intent and preserve it verbatim in `input_brief.md`. AutoDesign owns benchmark selection when the handoff does not supply one.

## Required content

The handoff may contain these fields, with two required:

| Field | Required | Meaning |
| --- | --- | --- |
| `motivation` | yes | why the Idea matters and what gap it closes |
| `contribution` | yes | the numbered claims this run must support or refute |
| `benchmark` | no | optional user-selected datasets, splits, metrics, or protocol constraints; when supplied, these are scientific locks |

A handoff missing Motivation or Contribution is a blocker. A missing Benchmark is an instruction for the experiment-design Skill to select or design the smallest contribution-complete benchmark portfolio; never invent a contribution or infer a motivation to fill a gap.

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

Only `motivation` and `contribution` are required. Accept `contributions` as an alias for `contribution`. `benchmark` is optional. When present, accept either structured data or literal prose; inside a structured object, treat `primary` and every other key as user-supplied constraints rather than imposing another required subfield.

## Channel B: natural language

AutoSearch is under separate development and its export may drift or arrive as prose. Accept Motivation and Contribution pasted directly into the conversation, with or without Benchmark, or as Markdown, and normalize them yourself.

This is a real input path, not a degraded one. A Skill invocation such as `/run-autodesign` followed by free-form text is expected usage. The user may also supply a benchmark, an initial experiment plan, preferred baselines, related work, compute limits, or a partial design. Absorb every extra item into `input_brief.md` and classify it as a scientific lock, an autonomous choice, or a resource constraint. Never discard supplied information because the schema has no field for it, and never demand JSON when Motivation and Contribution are already present in prose.

When normalizing prose:

1. Quote the literal input first, under a heading that names its channel.
2. Number the contributions `C1..Cn` in the order given. Do not merge, split, or reword them.
3. Record each supplied benchmark exactly as named, preserving its official identifier and version; otherwise record `not supplied — AutoDesign selection required`.
4. List every ambiguous term with the operational definition you will use, and mark it as an assumption to be confirmed.
5. Record anything else the input did not state and this run must choose as an autonomous design choice.

## Unresolved and conflicting input

- An ambiguous term becomes an explicit operational definition plus an assumption record, never a silent choice.
- A conflict between two handoff statements is a blocker reported to the user; do not resolve it by preference.
- An omitted benchmark invokes the contribution-driven benchmark decision in the experiment-design Skill. Other omitted fields are autonomous design choices subject to outcome-impact classification.
- A handoff-reported numeric result is a design-time reference for a simulated target. It is never an observation for this run.

## `input_brief.md`

Structure it as:

1. `## Handoff source` — channel, file path when applicable, timestamp.
2. `## Motivation (literal)`.
3. `## Contribution (literal, numbered)`.
4. `## Benchmark input (literal or not supplied)`.
5. `## Additional user-supplied input (literal)` — every extra item that arrived with the request.
6. `## Scientific locks` — with the exact source line for each.
7. `## Autonomous design choices` — each with `high` or `low` outcome impact.
8. `## Resource constraints`.
9. `## Operational definitions and assumptions`.
10. `## Blockers`.

Later Skills may resolve an autonomous choice. The design Skill may select a benchmark only when it is not supplied, or add a separately named benchmark needed to cover an otherwise untestable contribution. No Skill may rewrite a scientific lock.
