import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from autodesign.runner import execution_completion_errors, run_local_commands
from autodesign.skillflow import (
    advance_skill_run,
    initialize_skill_run,
    inspect_skill_run,
    repair_skill_state,
    verify_skill_run,
)

ROOT = Path(__file__).resolve().parent.parent


class SkillFlowTests(unittest.TestCase):
    @staticmethod
    def _write_execution_fixture(run_dir: Path, *, experiment_exit: int = 0) -> dict:
        project = run_dir / "generated_project"
        project.mkdir(parents=True)
        plan = {
            "preflight": ["printf preflight"],
            "smoke": ["printf smoke"],
            "experiment": [f"python3 -c 'raise SystemExit({experiment_exit})'"],
            "aggregate": ["printf aggregate"],
            "collect": ["printf collect"],
        }
        (run_dir / "command_plan.json").write_text(json.dumps(plan), encoding="utf-8")
        return plan

    def test_initialize_markdown_first_run_preserves_only_explicit_locks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_path = root / "input.json"
            input_path.write_text(
                json.dumps(
                    {
                        "motivation": "Need a flexible research route.",
                        "contribution": ["A train-free controller improves recovery."],
                        "benchmark": {
                            "tasks": ["ALFWorld"],
                            "constraints": {"student": "model-a"},
                        },
                    }
                ),
                encoding="utf-8",
            )
            run_dir = root / "run"

            report = initialize_skill_run(input_path, run_dir)

            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["current_stage"], "INPUT_READY")
            self.assertEqual(report["next_skill"], "autodesign-method-router")
            brief = (run_dir / "input_brief.md").read_text(encoding="utf-8")
            self.assertIn('"student": "model-a"', brief)
            self.assertNotIn('"seeds": [', brief)
            self.assertIn("recommendations, not locks", brief)

    def test_existing_run_rejects_changed_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first.md"
            second = root / "second.md"
            first.write_text("Idea one", encoding="utf-8")
            second.write_text("Idea two", encoding="utf-8")
            run_dir = root / "run"
            initialize_skill_run(first, run_dir)

            with self.assertRaisesRegex(ValueError, "different input"):
                initialize_skill_run(second, run_dir)

    def test_stage_advance_requires_artifacts_and_supports_r0_states(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_path = root / "input.md"
            input_path.write_text("A goal-only research idea", encoding="utf-8")
            run_dir = root / "run"
            initialize_skill_run(input_path, run_dir)

            with self.assertRaisesRegex(ValueError, "method_route.md"):
                advance_skill_run(
                    run_dir,
                    "METHOD_ROUTE_READY",
                    changed_input="input_brief.md",
                    literal_result="route selected",
                )
            self.assertEqual(inspect_skill_run(run_dir)["current_stage"], "INPUT_READY")

            (run_dir / "method_route.md").write_text("R0 required", encoding="utf-8")
            (run_dir / "r0_plan.md").write_text("probe", encoding="utf-8")
            waiting = advance_skill_run(
                run_dir,
                "WAITING_FOR_R0_IMPLEMENTATION",
                changed_input="method_route.md",
                literal_result="R0 required",
            )
            self.assertEqual(waiting["next_skill"], "autodesign-implementer")
            state = (run_dir / "AUTODESIGN_STATE.md").read_text(encoding="utf-8")
            self.assertIn("| Accepted route | recorded in `method_route.md` |", state)
            self.assertIn("| `r0_plan.md` | ready |", state)
            self.assertIn("| Blocking condition | observed R0 result required |", state)

    def test_complete_run_requires_current_execution_and_integrity_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            run_dir.mkdir(exist_ok=True)
            (run_dir / "AUTODESIGN_STATE.md").write_text(
                "# AutoDesign State\n\n| Current stage | COMPLETE |\n", encoding="utf-8"
            )
            for name in (
                "input_brief.md",
                "method_route.md",
                "evidence_plan.md",
                "implementation_notes.md",
                "result_diagnosis.md",
                "result_route.md",
            ):
                (run_dir / name).write_text(name, encoding="utf-8")
            (run_dir / "generated_project").mkdir()
            plan = {
                "preflight": ["printf preflight"],
                "smoke": ["printf smoke"],
                "experiment": ["printf experiment"],
                "aggregate": ["printf aggregate"],
                "collect": ["printf collect"],
            }
            (run_dir / "command_plan.json").write_text(json.dumps(plan), encoding="utf-8")
            (run_dir / "experiment_schedule.json").write_text(
                json.dumps({"schema_version": "1.0", "cells": [{"experiment_id": "exp", "variant_id": "method", "benchmark_task_id": "task", "seed": 1, "metrics": ["score"]}]}),
                encoding="utf-8",
            )
            (run_dir / "result_contract.json").write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "path": "assets/output/results.json",
                        "format": "autodesign-results-v1",
                    }
                ),
                encoding="utf-8",
            )
            execution = {
                "status": "PASS",
                "executor": "local",
                "commands": [
                    {"stage": stage, "command": commands[0], "exit_status": 0}
                    for stage, commands in plan.items()
                ],
            }
            (run_dir / "execution_record.json").write_text(
                json.dumps(execution), encoding="utf-8"
            )
            (run_dir / "result_summary.json").write_text(
                json.dumps({"status": "READY_FOR_GPT_DIAGNOSIS"}), encoding="utf-8"
            )
            (run_dir / "integrity_audit.md").write_text(
                "# Integrity Audit\n\nVerdict: PASS\n", encoding="utf-8"
            )

            report = verify_skill_run(run_dir)

            self.assertEqual(report["status"], "PASS", report["errors"])
            self.assertEqual(inspect_skill_run(run_dir)["next_skill"], "none")

            execution["commands"][-2]["exit_status"] = 7
            (run_dir / "execution_record.json").write_text(
                json.dumps(execution), encoding="utf-8"
            )
            failed = verify_skill_run(run_dir)
            self.assertEqual(failed["status"], "FAIL")
            self.assertIn(
                "execution_record aggregate has a non-zero exit status", failed["errors"]
            )

    def test_result_diagnosis_requires_route_and_returns_to_orchestrator(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_path = root / "input.md"
            input_path.write_text("Diagnose this completed run", encoding="utf-8")
            run_dir = root / "run"
            initialize_skill_run(input_path, run_dir)
            for name in ("method_route.md", "evidence_plan.md", "implementation_notes.md"):
                (run_dir / name).write_text(name, encoding="utf-8")
            (run_dir / "generated_project").mkdir()
            (run_dir / "command_plan.json").write_text("{}", encoding="utf-8")
            (run_dir / "experiment_schedule.json").write_text("{}", encoding="utf-8")
            (run_dir / "result_contract.json").write_text("{}", encoding="utf-8")
            (run_dir / "execution_record.json").write_text("{}", encoding="utf-8")
            (run_dir / "result_summary.json").write_text(
                json.dumps({"status": "READY_FOR_GPT_DIAGNOSIS"}),
                encoding="utf-8",
            )
            (run_dir / "result_diagnosis.md").write_text(
                "# Result diagnosis\n", encoding="utf-8"
            )

            with self.assertRaisesRegex(ValueError, "result_route.md"):
                advance_skill_run(
                    run_dir,
                    "RESULT_DIAGNOSIS_READY",
                    changed_input="result_summary.json",
                    literal_result="diagnosis ready",
                )

            (run_dir / "result_route.md").write_text(
                "# Result route\n\nroute: tuning\nexecution_required: yes\n",
                encoding="utf-8",
            )
            routed = advance_skill_run(
                run_dir,
                "RESULT_DIAGNOSIS_READY",
                changed_input="result_diagnosis.md",
                literal_result="tuning route recorded",
            )
            self.assertEqual(routed["next_skill"], "run-autodesign")

    def test_result_diagnosis_rejects_incomplete_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_path = root / "input.md"
            input_path.write_text("Diagnose this run", encoding="utf-8")
            run_dir = root / "run"
            initialize_skill_run(input_path, run_dir)
            (run_dir / "result_summary.json").write_text(
                json.dumps({"status": "INCOMPLETE"}), encoding="utf-8"
            )

            before = (run_dir / "AUTODESIGN_STATE.md").read_bytes()
            with self.assertRaisesRegex(
                ValueError, "requires result_summary.json status READY_FOR_GPT_DIAGNOSIS"
            ):
                advance_skill_run(
                    run_dir,
                    "RESULT_DIAGNOSIS_READY",
                    changed_input="result_summary.json",
                    literal_result="diagnosed",
                )
            self.assertEqual((run_dir / "AUTODESIGN_STATE.md").read_bytes(), before)

    def test_portable_stage_runner_preserves_ordered_prefix(self) -> None:
        script = ROOT / "skills/autodesign-executor/scripts/run_stage.py"
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run"
            project = run_dir / "generated_project"
            project.mkdir(parents=True)
            plan = {
                stage: [f"printf {stage}"]
                for stage in ("preflight", "smoke", "experiment", "aggregate", "collect")
            }
            (run_dir / "command_plan.json").write_text(
                json.dumps(plan), encoding="utf-8"
            )
            for stage, commands in plan.items():
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(script),
                        "--run-dir",
                        str(run_dir),
                        "--stage",
                        stage,
                        "--cwd",
                        str(project),
                        "--",
                        commands[0],
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
            record = json.loads((run_dir / "execution_record.json").read_text())
            self.assertTrue(record["workflow_complete"])
            self.assertEqual(
                record["completed_stages"],
                ["preflight", "smoke", "experiment", "aggregate", "collect"],
            )
            self.assertEqual(
                [item["stage"] for item in record["commands"]],
                ["preflight", "smoke", "experiment", "aggregate", "collect"],
            )

    def test_portable_stage_requires_command_plan(self) -> None:
        script = ROOT / "skills/autodesign-executor/scripts/run_stage.py"
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run"
            project = run_dir / "generated_project"
            project.mkdir(parents=True)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--run-dir",
                    str(run_dir),
                    "--stage",
                    "preflight",
                    "--cwd",
                    str(project),
                    "--",
                    "printf preflight",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 3)
            report = json.loads(completed.stdout)
            self.assertEqual(report["status"], "FAIL")
            self.assertIn("command_plan.json is required", report["error"])
            self.assertNotIn("Traceback", completed.stderr)
            self.assertFalse((run_dir / "execution_record.json").exists())

    def test_portable_stage_missing_cwd_returns_json_fail(self) -> None:
        script = ROOT / "skills/autodesign-executor/scripts/run_stage.py"
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run"
            run_dir.mkdir(parents=True)
            (run_dir / "command_plan.json").write_text(
                json.dumps({"preflight": ["printf preflight"]}), encoding="utf-8"
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--run-dir",
                    str(run_dir),
                    "--stage",
                    "preflight",
                    "--cwd",
                    str(run_dir / "missing-project"),
                    "--",
                    "printf preflight",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 3)
            report = json.loads(completed.stdout)
            self.assertEqual(report["status"], "FAIL")
            self.assertIn("execution cwd is missing", report["error"])
            self.assertIn("autodesign-implementer Skill", report["error"])
            self.assertNotIn("Traceback", completed.stderr)
            self.assertFalse((run_dir / "execution_record.json").exists())

    def test_portable_stage_runner_appends_multiple_commands_in_one_stage(self) -> None:
        script = ROOT / "skills/autodesign-executor/scripts/run_stage.py"
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run"
            project = run_dir / "generated_project"
            project.mkdir(parents=True)
            plan = {
                "preflight": ["printf preflight"],
                "smoke": ["printf smoke"],
                "experiment": ["printf cmd-A", "printf cmd-B"],
                "aggregate": ["printf aggregate"],
                "collect": ["printf collect"],
            }
            (run_dir / "command_plan.json").write_text(json.dumps(plan), encoding="utf-8")
            for stage, commands in plan.items():
                for command in commands:
                    completed = subprocess.run(
                        [
                            sys.executable,
                            str(script),
                            "--run-dir",
                            str(run_dir),
                            "--stage",
                            stage,
                            "--cwd",
                            str(project),
                            "--",
                            command,
                        ],
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(completed.returncode, 0, completed.stderr)

            record = json.loads((run_dir / "execution_record.json").read_text())
            experiment = [
                item["command"]
                for item in record["commands"]
                if item["stage"] == "experiment"
            ]
            self.assertEqual(experiment, ["printf cmd-A", "printf cmd-B"])
            self.assertEqual(execution_completion_errors(record, plan), [])

    def test_portable_stage_rejection_preserves_failed_command_evidence(self) -> None:
        script = ROOT / "skills/autodesign-executor/scripts/run_stage.py"
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run"
            project = run_dir / "generated_project"
            project.mkdir(parents=True)
            (run_dir / "command_plan.json").write_text(
                json.dumps(
                    {
                        "preflight": ["printf preflight"],
                        "smoke": ["printf smoke"],
                        "experiment": ["exit 3"],
                        "aggregate": ["printf aggregate"],
                        "collect": ["printf collect"],
                    }
                ),
                encoding="utf-8",
            )

            def invoke(stage: str, command: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [
                        sys.executable,
                        str(script),
                        "--run-dir",
                        str(run_dir),
                        "--stage",
                        stage,
                        "--cwd",
                        str(project),
                        "--",
                        command,
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )

            self.assertEqual(invoke("preflight", "printf preflight").returncode, 0)
            self.assertEqual(invoke("smoke", "printf smoke").returncode, 0)
            self.assertEqual(invoke("experiment", "exit 3").returncode, 3)
            before = (run_dir / "execution_record.json").read_bytes()

            rejected = invoke("aggregate", "printf aggregate")

            self.assertEqual(rejected.returncode, 3)
            self.assertEqual((run_dir / "execution_record.json").read_bytes(), before)
            record = json.loads(before)
            failure = next(item for item in record["commands"] if item["stage"] == "experiment")
            self.assertEqual(failure["exit_status"], 3)

    def test_portable_stage_restarts_when_its_plan_changed(self) -> None:
        script = ROOT / "skills/autodesign-executor/scripts/run_stage.py"
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run"
            project = run_dir / "generated_project"
            project.mkdir(parents=True)
            plan = {"preflight": ["printf old"]}
            (run_dir / "command_plan.json").write_text(json.dumps(plan), encoding="utf-8")

            first = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--run-dir",
                    str(run_dir),
                    "--stage",
                    "preflight",
                    "--cwd",
                    str(project),
                    "--",
                    "printf old",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            plan["preflight"] = ["printf new"]
            (run_dir / "command_plan.json").write_text(json.dumps(plan), encoding="utf-8")

            second = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--run-dir",
                    str(run_dir),
                    "--stage",
                    "preflight",
                    "--cwd",
                    str(project),
                    "--",
                    "printf new",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(second.returncode, 0, second.stderr)
            record = json.loads((run_dir / "execution_record.json").read_text())
            self.assertEqual(
                [item["command"] for item in record["commands"]], ["printf new"]
            )

    def test_run_local_all_reuses_unchanged_successful_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run"
            project = run_dir / "generated_project"
            project.mkdir(parents=True)
            trace = project / "trace.txt"
            plan = {
                stage: [f"printf '{stage}\\n' >> '{trace}'"]
                for stage in ("preflight", "smoke", "experiment", "aggregate", "collect")
            }
            (run_dir / "command_plan.json").write_text(json.dumps(plan), encoding="utf-8")
            self.assertEqual(run_local_commands(run_dir, "preflight")["status"], "PASS")
            self.assertEqual(run_local_commands(run_dir, "smoke")["status"], "PASS")
            plan["experiment"] = [f"printf 'experiment-v2\\n' >> '{trace}'"]
            (run_dir / "command_plan.json").write_text(json.dumps(plan), encoding="utf-8")

            record = run_local_commands(run_dir, "all")

            lines = trace.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines.count("preflight"), 1)
            self.assertEqual(lines.count("smoke"), 1)
            self.assertEqual(record["reused_stages"], ["preflight", "smoke"])
            self.assertTrue(record["workflow_complete"])

    def test_rejected_local_stage_preserves_failed_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run"
            self._write_execution_fixture(run_dir, experiment_exit=3)
            for stage in ("preflight", "smoke"):
                self.assertEqual(run_local_commands(run_dir, stage)["status"], "PASS")
            self.assertEqual(run_local_commands(run_dir, "experiment")["status"], "FAIL")
            before = (run_dir / "execution_record.json").read_bytes()

            rejected = run_local_commands(run_dir, "aggregate")

            self.assertEqual(rejected["status"], "FAIL")
            self.assertTrue(rejected["record_preserved"])
            self.assertEqual((run_dir / "execution_record.json").read_bytes(), before)
            failure = next(
                item
                for item in json.loads(before)["commands"]
                if item["stage"] == "experiment"
            )
            self.assertEqual(failure["exit_status"], 3)

    def test_run_local_missing_project_has_actionable_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            (run_dir / "command_plan.json").write_text(
                json.dumps({stage: [f"printf {stage}"] for stage in ("preflight", "smoke", "experiment", "aggregate", "collect")}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "generated_project is missing.*implementer"):
                run_local_commands(run_dir, "preflight")

    def test_audit_fail_cannot_advance_or_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            run_dir.mkdir(exist_ok=True)
            (run_dir / "AUTODESIGN_STATE.md").write_text(
                "# AutoDesign State\n\n| Current stage | RESULT_DIAGNOSIS_READY |\n"
                "| Last completed stage | RESULT_DIAGNOSIS_READY |\n"
                "| Blocking condition | none |\n"
                "| Next Skill | run-autodesign |\n"
                "| Accepted route | recorded in `method_route.md` |\n"
                "| Execution target | `generated_project/` via `command_plan.json` |\n"
                "| Primary result | recorded in `result_summary.json` |\n\n"
                "## Current artifacts\n\n## History\n",
                encoding="utf-8",
            )
            for name in (
                "input_brief.md",
                "method_route.md",
                "evidence_plan.md",
                "implementation_notes.md",
                "result_diagnosis.md",
                "result_route.md",
            ):
                (run_dir / name).write_text(name, encoding="utf-8")
            (run_dir / "generated_project").mkdir()
            plan = {stage: [f"printf {stage}"] for stage in ("preflight", "smoke", "experiment", "aggregate", "collect")}
            (run_dir / "command_plan.json").write_text(json.dumps(plan), encoding="utf-8")
            (run_dir / "experiment_schedule.json").write_text("{}", encoding="utf-8")
            (run_dir / "result_contract.json").write_text("{}", encoding="utf-8")
            (run_dir / "execution_record.json").write_text("{}", encoding="utf-8")
            (run_dir / "result_summary.json").write_text("{}", encoding="utf-8")
            audit = run_dir / "integrity_audit.md"
            audit.write_text("# Integrity Audit\n\nVerdict: FAIL\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Verdict: PASS"):
                advance_skill_run(
                    run_dir,
                    "INTEGRITY_AUDIT_PASS",
                    changed_input="integrity_audit.md",
                    literal_result="audit failed",
                )
            with self.assertRaisesRegex(ValueError, "INTEGRITY_AUDIT_PASS"):
                advance_skill_run(
                    run_dir,
                    "COMPLETE",
                    changed_input="AUTODESIGN_STATE.md",
                    literal_result="complete",
                )

            audit.write_text("# Integrity Audit\n\nVerdict: PASS\n", encoding="utf-8")
            advance_skill_run(
                run_dir,
                "INTEGRITY_AUDIT_PASS",
                changed_input="integrity_audit.md",
                literal_result="audit passed",
            )
            audit.write_text("# Integrity Audit\n\nVerdict: FAIL\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Verdict: PASS"):
                advance_skill_run(
                    run_dir,
                    "COMPLETE",
                    changed_input="AUTODESIGN_STATE.md",
                    literal_result="complete",
                )

    def test_state_whitespace_is_tolerated_and_repairable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "input.md"
            source.write_text("idea", encoding="utf-8")
            run_dir = root / "run"
            initialize_skill_run(source, run_dir)
            state_path = run_dir / "AUTODESIGN_STATE.md"
            state_path.write_text(
                state_path.read_text(encoding="utf-8").replace(
                    "| Current stage | INPUT_READY |",
                    "|   Current stage   |   INPUT_READY   |",
                ),
                encoding="utf-8",
            )

            self.assertEqual(inspect_skill_run(run_dir)["current_stage"], "INPUT_READY")
            repaired = repair_skill_state(run_dir)
            self.assertEqual(repaired["status"], "PASS")
            self.assertIn(
                "| Current stage | INPUT_READY |",
                state_path.read_text(encoding="utf-8"),
            )

    def test_state_history_escapes_pipe_characters(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "input.md"
            source.write_text("idea", encoding="utf-8")
            run_dir = root / "run"
            initialize_skill_run(source, run_dir)
            (run_dir / "method_route.md").write_text("route", encoding="utf-8")

            advance_skill_run(
                run_dir,
                "METHOD_ROUTE_READY",
                changed_input="metric | config",
                literal_result="acc=0.9 | loss=0.3",
            )

            history = next(
                line
                for line in (run_dir / "AUTODESIGN_STATE.md")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.startswith("| 1 |")
            )
            self.assertEqual(history.count("|"), 7)
            self.assertIn("metric &#124; config", history)
            self.assertIn("acc=0.9 &#124; loss=0.3", history)

    def test_in_progress_state_preserves_last_completed_milestone(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "input.md"
            source.write_text("idea", encoding="utf-8")
            run_dir = root / "run"
            initialize_skill_run(source, run_dir)
            for name in ("method_route.md", "evidence_plan.md", "implementation_notes.md"):
                (run_dir / name).write_text(name, encoding="utf-8")
            (run_dir / "generated_project").mkdir()
            (run_dir / "command_plan.json").write_text("{}", encoding="utf-8")
            (run_dir / "experiment_schedule.json").write_text("{}", encoding="utf-8")
            (run_dir / "result_contract.json").write_text("{}", encoding="utf-8")

            advance_skill_run(
                run_dir,
                "EXECUTION_IN_PROGRESS",
                changed_input="command_plan.json",
                literal_result="execution started",
            )

            state = (run_dir / "AUTODESIGN_STATE.md").read_text(encoding="utf-8")
            self.assertIn("| Current stage | EXECUTION_IN_PROGRESS |", state)
            self.assertIn("| Last completed stage | IMPLEMENTATION_READY |", state)


if __name__ == "__main__":
    unittest.main()
