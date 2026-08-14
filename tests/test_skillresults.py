import json
import tempfile
import unittest
from pathlib import Path

from autodesign.skillresults import ingest_skill_results, summarize_skill_results


class SkillResultTests(unittest.TestCase):
    def setUp(self) -> None:
        self.schedule = {
            "schema_version": "1.0",
            "cells": [
                {
                    "experiment_id": "exp-main",
                    "variant_id": "method",
                    "benchmark_task_id": "task",
                    "seed": seed,
                    "metrics": ["score"],
                }
                for seed in (1, 2)
            ],
        }
        self.results = {
            "schema_version": "1.0",
            "runs": [
                {
                    "experiment_id": "exp-main",
                    "variant_id": "method",
                    "benchmark_task_id": "task",
                    "seed": seed,
                    "metrics": {"score": value},
                    "status": "completed",
                }
                for seed, value in ((1, 0.5), (2, 0.7))
            ],
        }

    def test_explicit_schedule_reaches_diagnosis_without_design_schema(self) -> None:
        summary = summarize_skill_results(self.results, self.schedule)
        self.assertEqual(summary["status"], "READY_FOR_GPT_DIAGNOSIS", summary["errors"])
        self.assertEqual(summary["expected_cell_count"], 2)
        self.assertEqual(summary["observed_cell_count"], 2)
        self.assertAlmostEqual(summary["aggregates"][0]["mean"], 0.6)
        self.assertEqual(summary["automatic_claim_verdict"], "NOT_ASSIGNED")

    def test_missing_cell_and_boolean_seed_are_rejected(self) -> None:
        missing = summarize_skill_results(
            {"schema_version": "1.0", "runs": self.results["runs"][:1]}, self.schedule
        )
        self.assertEqual(missing["status"], "INCOMPLETE")
        self.assertEqual(len(missing["missing_cells"]), 1)

        invalid = json.loads(json.dumps(self.results))
        invalid["runs"][0]["seed"] = True
        report = summarize_skill_results(invalid, self.schedule)
        self.assertEqual(report["status"], "INCOMPLETE")
        self.assertTrue(any("invalid cell key" in error for error in report["errors"]))

    def test_ingest_requires_complete_current_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            plan = {
                "preflight": ["printf preflight"],
                "smoke": ["printf smoke"],
                "experiment": ["printf experiment"],
                "aggregate": ["printf aggregate"],
                "collect": ["printf collect"],
            }
            (run_dir / "experiment_schedule.json").write_text(
                json.dumps(self.schedule), encoding="utf-8"
            )
            (run_dir / "command_plan.json").write_text(json.dumps(plan), encoding="utf-8")
            (run_dir / "execution_record.json").write_text(
                json.dumps(
                    {
                        "status": "FAIL",
                        "executor": "local",
                        "commands": [
                            {"stage": "smoke", "command": "printf smoke", "exit_status": 1}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            results_path = run_dir / "results.json"
            results_path.write_text(json.dumps(self.results), encoding="utf-8")

            summary = ingest_skill_results(run_dir, results_path)

            self.assertEqual(summary["status"], "INCOMPLETE")
            self.assertIn(
                "execution_record.status must be PASS before result ingestion",
                summary["errors"],
            )


if __name__ == "__main__":
    unittest.main()
