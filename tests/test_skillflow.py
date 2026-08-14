import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from autodesign.skillflow import (
    advance_skill_run,
    initialize_skill_run,
    inspect_skill_run,
    verify_skill_run,
)

ROOT = Path(__file__).resolve().parent.parent


class SkillFlowTests(unittest.TestCase):
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
            (run_dir / "result_summary.json").write_text("{}", encoding="utf-8")
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

    def test_portable_stage_runner_preserves_ordered_prefix(self) -> None:
        script = ROOT / "skills/autodesign-executor/scripts/run_stage.py"
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run"
            project = run_dir / "generated_project"
            project.mkdir(parents=True)
            for stage in ("preflight", "smoke", "experiment", "aggregate", "collect"):
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
                        sys.executable,
                        "-c",
                        f"print('{stage.upper()}_PASS')",
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


if __name__ == "__main__":
    unittest.main()
