import unittest
from unittest import mock
from pathlib import Path
import json
import tempfile

from web import serve


class WebServerTests(unittest.TestCase):
    def test_safe_run_directory_rejects_traversal(self):
        for value in ("../outside", "direction-invalid", "medical-vlm-novelty"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    serve.safe_run_directory(value)

    def test_safe_run_directory_allows_known_and_generated_runs(self):
        self.assertEqual(serve.safe_run_directory("medical-vlm-10").name, "medical-vlm-10")
        self.assertEqual(
            serve.safe_run_directory("direction-20260825-184950-bf9c19").name,
            "direction-20260825-184950-bf9c19",
        )

    def test_run_summary_exposes_folder_configuration_and_ideas(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "research_runs"
            web_root = Path(temp_dir) / "web"
            run_dir = root / "medical-vlm-10"
            run_dir.mkdir(parents=True)
            fallback_data = web_root / "data" / "ideas.json"
            fallback_data.parent.mkdir(parents=True)
            fallback_data.write_text(
                json.dumps({"ideas": [{"id": "idea_one", "index": 1}]}),
                encoding="utf-8",
            )
            with (
                mock.patch.object(serve, "RUNS_ROOT", root),
                mock.patch.object(serve, "WEB_ROOT", web_root),
                mock.patch.object(serve.JOB_MANAGER, "snapshots", return_value=[]),
            ):
                summaries = serve.list_run_summaries()
            self.assertEqual(len(summaries), 1)
            self.assertEqual(summaries[0]["status"], "ready")
            self.assertEqual(len(summaries[0]["ideas"]), 1)
            self.assertTrue(summaries[0]["deletable"])

    def test_deleted_known_run_is_not_recreated_in_summaries(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "research_runs"
            web_root = Path(temp_dir) / "web"
            root.mkdir(parents=True)
            fallback_data = web_root / "data" / "ideas.json"
            fallback_data.parent.mkdir(parents=True)
            fallback_data.write_text(json.dumps({"ideas": []}), encoding="utf-8")
            with (
                mock.patch.object(serve, "RUNS_ROOT", root),
                mock.patch.object(serve, "WEB_ROOT", web_root),
                mock.patch.object(serve.JOB_MANAGER, "snapshots", return_value=[]),
            ):
                self.assertEqual(serve.list_run_summaries(), [])

    def test_delete_known_run_removes_directory_and_fallback_data(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "research_runs"
            web_root = Path(temp_dir) / "web"
            run_dir = root / "medical-vlm-10"
            fallback_data = web_root / "data" / "ideas.json"
            run_dir.mkdir(parents=True)
            fallback_data.parent.mkdir(parents=True)
            fallback_data.write_text("{}", encoding="utf-8")
            with (
                mock.patch.object(serve, "RUNS_ROOT", root),
                mock.patch.object(serve, "WEB_ROOT", web_root),
            ):
                serve.delete_run_directory(run_dir)
            self.assertFalse(run_dir.exists())
            self.assertFalse(fallback_data.exists())

    def test_delete_direction_run_removes_its_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "direction-20260826-120000-abcdef"
            run_dir.mkdir()
            (run_dir / "job.json").write_text("{}", encoding="utf-8")
            with mock.patch.object(serve, "RUNS_ROOT", root):
                serve.delete_run_directory(run_dir)
            self.assertFalse(run_dir.exists())

    def test_job_snapshot_contains_folder_identity(self):
        with mock.patch.object(serve.ResearchJob, "add_event"):
            job = serve.ResearchJob("测试方向", 2, False, 30)
        snapshot = job.snapshot()
        self.assertEqual(snapshot["run_name"], job.run_dir.name)
        self.assertEqual(snapshot["direction"], "测试方向")
        self.assertEqual(snapshot["status"], "queued")

    def test_human_review_is_persisted_and_applied(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "direction-20260826-120000-abcdef"
            run_dir.mkdir()
            dataset = {"ideas": [{"id": "idea_one"}, {"id": "idea_two"}]}
            (run_dir / "web-data.json").write_text(
                json.dumps(dataset),
                encoding="utf-8",
            )

            serve.write_human_review(run_dir, "idea_one", "approved")
            serve.write_human_review(run_dir, "idea_two", "discarded")

            reviews = serve.read_human_reviews(run_dir)
            self.assertEqual(reviews, {"idea_one": "approved", "idea_two": "discarded"})
            enriched = serve.apply_human_reviews(dataset, run_dir)
            self.assertEqual(enriched["ideas"][0]["human_review"], "approved")
            self.assertEqual(enriched["ideas"][1]["human_review"], "discarded")

            serve.write_human_review(run_dir, "idea_one", None)
            self.assertEqual(serve.read_human_reviews(run_dir), {"idea_two": "discarded"})
            self.assertIsNone(serve.apply_human_reviews(dataset, run_dir)["ideas"][0]["human_review"])

    def test_human_review_rejects_invalid_decision_and_unknown_idea(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "direction-20260826-120000-abcdef"
            run_dir.mkdir()
            (run_dir / "web-data.json").write_text(
                json.dumps({"ideas": [{"id": "idea_one"}]}),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                serve.write_human_review(run_dir, "idea_one", "maybe")
            with self.assertRaises(ValueError):
                serve.write_human_review(run_dir, "missing", "approved")


if __name__ == "__main__":
    unittest.main()
