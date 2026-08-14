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

For a provenance replay, the record states that mode explicitly and names the copied source observation file. Replay success is an execution-layer result, not fresh scientific evidence.

## Remote sequence

Validate → plan → preflight → sync → bootstrap → smoke → experiment → aggregate → collect. Generated project commands and result contract override demo configuration. Git mode requires a clean synchronized revision; rsync mode records a release description.

## Resource failures

Preserve exact resource errors and the first failed stage. Do not turn a resource block into a scientific method verdict.
