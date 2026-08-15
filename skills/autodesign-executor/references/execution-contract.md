# Execution Contract

## Stage record

Each stage records:

- stage name;
- exact command and working directory;
- exact input artifact paths;
- start and finish timestamps;
- stdout and stderr;
- exit status;
- executor and GPU IDs when applicable;
- machine-context source (`AGENTS.md` or `CLAUDE.md`) when applicable;
- produced paths;
- next action on failure.

The preflight stage also records the accepted and observed scientific locks, variant identities, data composition, benchmark provenance, protocol values, and production input paths required by the evidence plan. A mismatch is an execution blocker even when a lower-level command can run.

## Ordered completion

Result diagnosis requires successful current records for `preflight`, `smoke`, `experiment`, `aggregate`, and `collect` in that order. Multiple commands within a stage stay contiguous. A later success does not erase an earlier failure unless the failed stage is explicitly retried and replaced.

An out-of-order or stale-stage request returns a rejected-attempt result without rewriting the authoritative execution record. `run-local --stage all` reuses the unchanged successful prefix and starts at the first missing, failed, or stale stage.

The accepted `experiment_schedule.json` is immutable during an execution round. Missing cells, unexpected cells, changed evidence classes, or changed benchmark provenance prevent `collect` from qualifying the run for diagnosis. A deliberate new round first revises the owning evidence or implementation artifact and invalidates downstream records.

The portable stage runner requires a readable `command_plan.json` and an existing working directory before execution. It returns a structured JSON `FAIL` for either missing input. Remote records retain all earlier stage evidence, including failures, when a later stage is invoked; the aggregate record remains `FAIL` until that failed stage is explicitly retried and replaced.

## Remote sequence

Read instruction context → validate → preflight → sync → bootstrap → smoke → experiment → aggregate → collect. The effective `AGENTS.md` or `CLAUDE.md` supplies SSH, allowed directories, GPU IDs, concurrency, environment location, timeouts, and process-preservation rules. Deployment still requires a materialized `generated_project/`, a complete five-stage `command_plan.json`, a non-empty `experiment_schedule.json`, and a valid `result_contract.json`. The command plan and result contract—not the machine-context file—define experiment commands and result paths. The Skill does not create or read a Python/JSON GPU configuration; it uses the current agent's native shell, SSH, and file-transfer tools directly.

## Resource failures

Preserve exact resource errors and the first failed stage. Do not turn a resource block into a scientific method verdict.
