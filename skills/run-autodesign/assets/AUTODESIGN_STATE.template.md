# AutoDesign State

| Field | Value |
| --- | --- |
| Pipeline | AutoDesign design-then-run v2 |
| Run | RUN_NAME |
| Current stage | INPUT_READY |
| Last completed stage | INPUT_READY |
| Blocking condition | none |
| Next Skill | autodesign-experiment-design |
| Accepted route | pending |
| Execution target | pending |
| Primary result | pending |

## Accepted inputs

- Input brief: `input_brief.md`
- Explicit locks: pending

## Current artifacts

| Artifact | Status | Decision use |
| --- | --- | --- |
| `input_brief.md` | ready | experiment design input |

## History

| Round | From | To | Changed input | Literal result | Next action |
| ---: | --- | --- | --- | --- | --- |
| 0 | new | INPUT_READY | `input_brief.md` | handoff accepted | run experiment design |
