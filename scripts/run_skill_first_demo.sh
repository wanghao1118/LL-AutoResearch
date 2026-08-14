#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
RUN_DIR="${1:-$ROOT/assets/output/skill_first_demo}"
INPUT="$ROOT/assets/input/demo_input.json"
STAGE_RUNNER="$ROOT/skills/autodesign-executor/scripts/run_stage.py"
python3 - "$RUN_DIR" <<'PY'
from pathlib import Path
import shutil
import sys
path = Path(sys.argv[1])
if path.exists():
    shutil.rmtree(path)
PY
cd "$ROOT"
python3 -m autodesign skill-init "$INPUT" --output "$RUN_DIR"
cat > "$RUN_DIR/method_route.md" <<'MD'
# Method Route

## Input classification

`method_specified`: the fixture tests contribution-to-evidence coverage planning.

## Selected route

A train-free deterministic planner maps claims to evidence roles and rejects incomplete plans.

## Falsifier

The route fails when a required claim has no runnable falsifying experiment.

## R0 gate

`required: no` because this is an engineering contract fixture with an existing runnable intervention.
MD
python3 -m autodesign skill-advance "$RUN_DIR" METHOD_ROUTE_READY --changed-input method_route.md --literal-result route_selected
cat > "$RUN_DIR/evidence_plan.md" <<'MD'
# Evidence Plan

## Claim ledger

| Claim ID | Original claim | Experiment | Falsifier |
| --- | --- | --- | --- |
| C1.1 | The planner reaches complete contribution-to-evidence coverage. | exp-main | method does not exceed the manual template |

## Experiment

`exp-main` compares `skill-first` with `manual-template` on `coverage-audit`, metric `requirement_coverage`, seeds 1 and 2.

## Coverage audit

PASS: the fixture has a direct main comparison and literal falsifier.
MD
python3 -m autodesign skill-advance "$RUN_DIR" EVIDENCE_PLAN_READY --changed-input evidence_plan.md --literal-result evidence_coverage_pass
mkdir -p "$RUN_DIR/generated_project"
cat > "$RUN_DIR/generated_project/run_fixture.py" <<'PY'
import json
import sys
from pathlib import Path

mode = sys.argv[1]
output = Path("assets/output/results.json")
if mode == "preflight":
    print("PREFLIGHT_PASS data_contract benchmark_interface metric_contract method_sanity")
elif mode == "smoke":
    print("SMOKE_PASS representative_cells=2")
elif mode == "experiment":
    output.parent.mkdir(parents=True, exist_ok=True)
    runs = []
    for variant, value in (("skill-first", 1.0), ("manual-template", 0.75)):
        for seed in (1, 2):
            runs.append({
                "experiment_id": "exp-main",
                "variant_id": variant,
                "benchmark_task_id": "coverage-audit",
                "seed": seed,
                "metrics": {"requirement_coverage": value},
                "status": "completed",
            })
    output.write_text(json.dumps({"schema_version": "1.0", "runs": runs}, indent=2) + "\n")
    print(f"EXPERIMENT_PASS cells={len(runs)} result={output}")
elif mode == "aggregate":
    payload = json.loads(output.read_text())
    print(f"AGGREGATE_PASS cells={len(payload['runs'])} result={output}")
elif mode == "collect":
    payload = json.loads(output.read_text())
    print(f"COLLECT_PASS cells={len(payload['runs'])} result={output}")
else:
    raise SystemExit(2)
PY
cat > "$RUN_DIR/generated_project/environment.yml" <<'YAML'
name: autodesign-skill-fixture
channels:
  - defaults
dependencies:
  - python=3.9
YAML
cat > "$RUN_DIR/implementation_notes.md" <<'MD'
# Implementation Notes

- Route: train-free Skill-first planner fixture
- Environment: `generated_project/environment.yml`
- Preflight: `python3 run_fixture.py preflight`
- Smoke: `python3 run_fixture.py smoke`
- Experiment: `python3 run_fixture.py experiment`
- Aggregate: `python3 run_fixture.py aggregate`
- Collect: `python3 run_fixture.py collect`
- Schedule: `experiment_schedule.json`
- Primary result: `generated_project/assets/output/results.json`
MD
cat > "$RUN_DIR/command_plan.json" <<'JSON'
{
  "preflight": ["python3 run_fixture.py preflight"],
  "smoke": ["python3 run_fixture.py smoke"],
  "experiment": ["python3 run_fixture.py experiment"],
  "aggregate": ["python3 run_fixture.py aggregate"],
  "collect": ["python3 run_fixture.py collect"]
}
JSON
cat > "$RUN_DIR/result_contract.json" <<'JSON'
{
  "schema_version": "1.0",
  "path": "assets/output/results.json",
  "format": "autodesign-results-v1"
}
JSON
cat > "$RUN_DIR/experiment_schedule.json" <<'JSON'
{
  "schema_version": "1.0",
  "cells": [
    {"experiment_id": "exp-main", "variant_id": "skill-first", "benchmark_task_id": "coverage-audit", "seed": 1, "metrics": ["requirement_coverage"]},
    {"experiment_id": "exp-main", "variant_id": "skill-first", "benchmark_task_id": "coverage-audit", "seed": 2, "metrics": ["requirement_coverage"]},
    {"experiment_id": "exp-main", "variant_id": "manual-template", "benchmark_task_id": "coverage-audit", "seed": 1, "metrics": ["requirement_coverage"]},
    {"experiment_id": "exp-main", "variant_id": "manual-template", "benchmark_task_id": "coverage-audit", "seed": 2, "metrics": ["requirement_coverage"]}
  ]
}
JSON
python3 -m autodesign skill-advance "$RUN_DIR" IMPLEMENTATION_READY --changed-input generated_project --literal-result implementation_ready
for stage in preflight smoke experiment aggregate collect; do
  python3 "$STAGE_RUNNER" --run-dir "$RUN_DIR" --stage "$stage" --cwd "$RUN_DIR/generated_project" -- "python3 run_fixture.py $stage"
done
python3 -m autodesign skill-advance "$RUN_DIR" EXECUTION_COMPLETE --changed-input execution_record.json --literal-result preflight_smoke_experiment_aggregate_collect_exit_zero
python3 -m autodesign skill-ingest "$RUN_DIR" "$RUN_DIR/generated_project/assets/output/results.json"
cat > "$RUN_DIR/result_diagnosis.md" <<'MD'
# Result Diagnosis

- Execution layer: PASS
- Expected cells: 4
- Observed cells: 4
- C1.1 status: SUPPORTED in this contract fixture
- Observation: skill-first mean 1.0; manual-template mean 0.75
- Scope: engineering fixture only, not paper evidence
- Route: report
MD
cat > "$RUN_DIR/result_route.md" <<'MD'
# Result Route

- route: `report`
- reason: all scheduled engineering-fixture evidence is complete and supports the fixture claim
- owner_skill: `autodesign-integrity-auditor`
- changed variable or artifact: none
- execution_required: `no`
- invalidated downstream artifacts: `integrity_audit.md`
- continue threshold: all 4 scheduled cells and 5 execution stages remain complete
- stop threshold: any missing cell, changed command, or aggregate mismatch
- closure condition: independent integrity audit passes
MD
python3 -m autodesign skill-advance "$RUN_DIR" RESULT_DIAGNOSIS_READY --changed-input result_summary.json --literal-result diagnosis_ready
cat > "$RUN_DIR/integrity_audit.md" <<'MD'
# Integrity Audit

Verdict: PASS

The four scheduled cells are present, all five current commands exited zero, the reported means match raw observations, and the conclusion is restricted to the engineering fixture.
MD
python3 -m autodesign skill-advance "$RUN_DIR" INTEGRITY_AUDIT_PASS --changed-input integrity_audit.md --literal-result integrity_pass
python3 -m autodesign skill-advance "$RUN_DIR" COMPLETE --changed-input AUTODESIGN_STATE.md --literal-result pipeline_complete
python3 -m autodesign skill-verify "$RUN_DIR"
printf 'SKILL_FIRST_DEMO_PASS run_dir=%s\n' "$RUN_DIR"
