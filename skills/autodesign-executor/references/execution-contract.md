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
- produced paths;
- next action on failure.

## Ordered completion

Result diagnosis requires successful current records for `preflight`, `smoke`, `experiment`, `aggregate`, and `collect` in that order. Multiple commands within a stage stay contiguous. A later success does not erase an earlier failure unless the failed stage is explicitly retried and replaced.

An out-of-order or stale-stage request returns a rejected-attempt result without rewriting the authoritative execution record. `run-local --stage all` reuses the unchanged successful prefix and starts at the first missing, failed, or stale stage.

For a provenance replay, the record states that mode explicitly and names the copied source observation file. Replay success is an execution-layer result, not fresh scientific evidence.

## Remote sequence

Validate → plan → preflight → sync → bootstrap → smoke → experiment → aggregate → collect. Validation requires a materialized `generated_project/`, a complete five-stage `command_plan.json`, a non-empty `experiment_schedule.json`, and a valid `result_contract.json` before deployment. Generated project commands and result contract override demo configuration. Git mode requires a clean synchronized revision; rsync mode records a release description.

## Resource failures

Preserve exact resource errors and the first failed stage. Do not turn a resource block into a scientific method verdict.
