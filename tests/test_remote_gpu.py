import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from autodesign.cli import _run_remote_all
from autodesign.remote_gpu import RemoteGPUController, validate_remote_config
from autodesign.runner import STAGE_ORDER


class RemoteGPUTests(unittest.TestCase):
    def _fixture(self, root: Path, mode: str = "rsync") -> tuple[Path, dict]:
        project = root / "run/generated_project"
        project.mkdir(parents=True)
        (project / "environment.yml").write_text(
            "name: experiment\ndependencies:\n  - python=3.11\n", encoding="utf-8"
        )
        (root / "environments").mkdir()
        (root / "environments/autodesign-gpu.yml").write_text(
            "name: autodesign-gpu\ndependencies:\n  - python=3.11\n", encoding="utf-8"
        )
        (root / "configs").mkdir()
        (root / "configs/policy.md").write_text(
            "Use GPU 2 and work inside /srv/autodesign/project.", encoding="utf-8"
        )
        commands = {
            "preflight": "python3 preflight.py",
            "smoke": "python3 smoke.py",
            "experiment": "python3 train.py",
            "aggregate": "python3 aggregate.py",
            "collect": "python3 package.py",
        }
        config = {
            "schema_version": "1.0",
            "ssh": {
                "host": "gpu.example",
                "user": "researcher",
                "port": 2222,
                "identity_file": "",
                "connect_timeout_seconds": 15,
                "strict_host_key_checking": True,
            },
            "remote": {
                "allowed_root": "/srv/autodesign",
                "repo_dir": "/srv/autodesign/project",
                "work_dir": "/srv/autodesign/project/experiment",
                "policy_file": "configs/policy.md",
            },
            "git": {
                "repo_url": "git@example:repo.git",
                "remote_name": "origin",
                "branch": "codex/autodesign",
                "pull_mode": "ff-only",
            },
            "transfer": {
                "mode": mode,
                "rsync_executable": "rsync",
                "source_dir": ".",
                "delete_remote_extraneous": False,
                "excludes": [".git/", ".venv/", "assets/output/"],
            },
            "conda": {
                "executable": "/opt/conda/bin/conda",
                "env_name": "autodesign-gpu",
                "environment_file": "environments/autodesign-gpu.yml",
            },
            "gpu": {"visible_devices": ["2"], "required_count": 1},
            "limits": {"max_parallel_jobs": 1, "command_timeout_seconds": 300},
            "run": {
                "commands": commands,
                "result_paths": ["experiment/assets/output/results.json"],
                "primary_result_path": "experiment/assets/output/results.json",
            },
            "local": {
                "run_dir": "run",
                "artifact_dir": "artifacts",
                "log_dir": "logs",
                "result_dir": "results",
            },
        }
        (root / "run/command_plan.json").write_text(
            json.dumps({stage: [command] for stage, command in commands.items()}),
            encoding="utf-8",
        )
        (root / "run/result_contract.json").write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "path": "assets/output/results.json",
                    "format": "autodesign-results-v1",
                }
            ),
            encoding="utf-8",
        )
        (root / "run/experiment_schedule.json").write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "cells": [
                        {
                            "experiment_id": "exp",
                            "variant_id": "method",
                            "benchmark_task_id": "task",
                            "seed": 1,
                            "metrics": ["score"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        config_path = root / "configs/remote.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        return config_path, config

    def test_ready_config_and_supported_path_failures(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, config = self._fixture(root)
            report = validate_remote_config(config, root)
            self.assertEqual(report["status"], "PASS", report["errors"])

            del config["run"]["commands"]["collect"]
            report = validate_remote_config(config, root)
            self.assertIn(
                "run.commands is missing ordered stages: collect", report["errors"]
            )
            config["run"]["commands"]["collect"] = "python3 package.py"
            config["remote"]["work_dir"] = "/srv/another-project"
            report = validate_remote_config(config, root)
            self.assertIn("remote.work_dir must be inside remote.repo_dir", report["errors"])

    def test_materialized_five_stage_and_result_contract_override_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path, _ = self._fixture(root)
            plan = json.loads((root / "run/command_plan.json").read_text())
            plan["experiment"] = ["python3 train.py shard-a", "python3 train.py shard-b"]
            (root / "run/command_plan.json").write_text(json.dumps(plan), encoding="utf-8")

            controller = RemoteGPUController(config_path, repo_root=root)
            report = controller.validate()

            self.assertEqual(report["status"], "PASS", report["errors"])
            self.assertEqual(
                controller.config["run"]["commands"]["experiment"],
                "python3 train.py shard-a && python3 train.py shard-b",
            )
            self.assertEqual(
                controller.config["run"]["primary_result_path"],
                "experiment/assets/output/results.json",
            )
            self.assertTrue(report["run_command_source"].endswith("command_plan.json"))
            self.assertTrue(report["result_contract_source"].endswith("result_contract.json"))

    def test_scripts_use_linux_bash_gpu_scope_environment_and_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path, _ = self._fixture(root, mode="git")
            controller = RemoteGPUController(config_path, repo_root=root)
            scripts = [
                controller.build_script("preflight"),
                controller.build_script("sync"),
                controller.build_script("bootstrap"),
                controller.build_script("run", "experiment"),
            ]
            run_script = scripts[-1]
            self.assertIn('export CUDA_VISIBLE_DEVICES="$GPU_CSV"', run_script)
            self.assertIn("export AUTODESIGN_MAX_PARALLEL_JOBS=1", run_script)
            self.assertIn(".autodesign_gpu_job.lock", run_script)
            self.assertIn('/bin/bash -lc "$RUN_COMMAND"', run_script)
            self.assertIn('PROJECT_ENV_FILE="$WORK_DIR/$PROJECT_ENV_REL"', scripts[2])
            for script in scripts:
                parsed = subprocess.run(
                    ["/bin/bash", "-n"], input=script, text=True, capture_output=True, check=False
                )
                self.assertEqual(parsed.returncode, 0, parsed.stderr)

    def test_remote_record_preserves_complete_ordered_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path, _ = self._fixture(root)
            controller = RemoteGPUController(config_path, repo_root=root)
            for index, stage in enumerate(STAGE_ORDER):
                controller._write_pipeline_execution_record(
                    {
                        "command_key": stage,
                        "stdout": f"{stage.upper()}_PASS\n",
                        "stderr": "",
                        "exit_status": 0,
                        "record_path": f"/records/{stage}.json",
                        "started_at": f"2026-01-01T00:00:0{index}+00:00",
                        "finished_at": f"2026-01-01T00:00:1{index}+00:00",
                    }
                )
            record = json.loads((root / "run/execution_record.json").read_text())
            self.assertEqual([item["stage"] for item in record["commands"]], list(STAGE_ORDER))
            self.assertEqual(record["completed_stages"], list(STAGE_ORDER))
            self.assertTrue(record["workflow_complete"])

    def test_remote_all_dry_run_contains_all_five_project_stages(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path, _ = self._fixture(root)
            controller = RemoteGPUController(config_path, repo_root=root)

            report = _run_remote_all(controller, dry_run=True)

            self.assertEqual(report["status"], "DRY_RUN")
            self.assertEqual(
                [item["command_key"] for item in report["runs"]], list(STAGE_ORDER)
            )
            self.assertEqual(report["collect"]["status"], "DRY_RUN")

    def test_rsync_plan_and_literal_command_quoting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path, _ = self._fixture(root)
            controller = RemoteGPUController(config_path, repo_root=root)
            sync = controller.sync(dry_run=True)
            self.assertTrue(sync["generated_project_rsync_argv"][-2].endswith("/run/generated_project/"))
            self.assertEqual(
                sync["generated_project_rsync_argv"][-1],
                "researcher@gpu.example:/srv/autodesign/project/experiment/",
            )

            controller.config["run"]["commands"]["experiment"] = (
                "printf '%s\\n' '$HOME' '`literal`' 'quote\"value'"
            )
            script = controller.build_script("run", "experiment")
            assignment = next(
                line for line in script.splitlines() if line.startswith("RUN_COMMAND=")
            )
            executed = subprocess.run(
                ["/bin/bash", "-c", f'{assignment}\n/bin/bash -lc "$RUN_COMMAND"'],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(executed.returncode, 0, executed.stderr)
            self.assertEqual(executed.stdout.splitlines(), ["$HOME", "`literal`", 'quote"value'])

    def test_missing_generated_project_fails_before_sync(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path, _ = self._fixture(root)
            environment = root / "run/generated_project/environment.yml"
            environment.unlink()
            (root / "run/generated_project").rmdir()
            controller = RemoteGPUController(config_path, repo_root=root)

            report = controller.sync(dry_run=True)

            self.assertEqual(report["status"], "FAIL")
            self.assertTrue(
                any("autodesign-implementer Skill" in error for error in report["validation"]["errors"])
            )

    def test_old_run_contract_fails_before_remote_deploy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path, _ = self._fixture(root)
            (root / "run/command_plan.json").write_text(
                json.dumps(
                    {
                        "smoke": ["python3 smoke.py"],
                        "experiment": ["python3 train.py"],
                        "aggregate": ["python3 aggregate.py"],
                    }
                ),
                encoding="utf-8",
            )
            (root / "run/experiment_schedule.json").unlink()
            (root / "run/result_contract.json").unlink()
            controller = RemoteGPUController(config_path, repo_root=root)

            validation = controller.validate()
            report = _run_remote_all(controller, dry_run=False)

            self.assertEqual(validation["status"], "FAIL")
            self.assertTrue(any("command_plan.json" in error for error in validation["errors"]))
            self.assertTrue(any("experiment_schedule.json" in error for error in validation["errors"]))
            self.assertTrue(any("result_contract.json" in error for error in validation["errors"]))
            self.assertEqual(report["status"], "FAIL")
            self.assertEqual(report["failed_step"], "validate")
            self.assertNotIn("deploy", report)


if __name__ == "__main__":
    unittest.main()
