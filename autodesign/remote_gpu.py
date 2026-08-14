"""SSH-based remote GPU deployment and execution for AutoDesign.

Source code reaches the server through the configured Git or rsync mode. SSH
carries control scripts and execution output; result collection uses rsync.
"""

from __future__ import annotations

import json
import posixpath
import re
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from .io import read_json, write_json, write_text
from .runner import STAGE_ORDER, execution_progress

PLACEHOLDER_PATTERN = re.compile(r"(?:^|[^A-Za-z])(?:[A-Z0-9_]*_TBD|TBD)(?:$|[^A-Za-z])")


class RemoteGPUError(RuntimeError):
    """Raised for invalid remote GPU operations."""


def _quote(value: Any) -> str:
    return shlex.quote(str(value))


def _has_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return bool(PLACEHOLDER_PATTERN.search(value))
    if isinstance(value, list):
        return any(_has_placeholder(item) for item in value)
    if isinstance(value, dict):
        return any(_has_placeholder(item) for item in value.values())
    return False


def _nested(config: dict[str, Any], dotted: str) -> Any:
    value: Any = config
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def _is_inside(child: str, parent: str) -> bool:
    child_path = PurePosixPath(posixpath.normpath(child))
    parent_path = PurePosixPath(posixpath.normpath(parent))
    return child_path == parent_path or parent_path in child_path.parents


def _read_required_json(path: Path, label: str, errors: list[str]) -> Any:
    if not path.is_file():
        errors.append(f"local run is missing {label}: {path}")
        return None
    try:
        return read_json(path)
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"local run has invalid {label}: {path}: {error}")
        return None


def _validate_materialized_run_contracts(run_dir: Path, errors: list[str]) -> None:
    """Reject old or partial runs before any remote deployment consumes resources."""

    command_plan_path = run_dir / "command_plan.json"
    command_plan = _read_required_json(command_plan_path, "command_plan.json", errors)
    if command_plan is not None:
        if not isinstance(command_plan, dict):
            errors.append("local command_plan.json must contain an object")
        else:
            for stage in STAGE_ORDER:
                commands = command_plan.get(stage)
                if not isinstance(commands, list) or not commands or not all(
                    isinstance(command, str) and command.strip() for command in commands
                ):
                    errors.append(
                        f"local command_plan.json requires non-empty command list: {stage}"
                    )

    schedule_path = run_dir / "experiment_schedule.json"
    schedule = _read_required_json(schedule_path, "experiment_schedule.json", errors)
    if schedule is not None:
        if not isinstance(schedule, dict) or schedule.get("schema_version") != "1.0":
            errors.append("local experiment_schedule.json must use schema_version 1.0")
        else:
            cells = schedule.get("cells")
            if not isinstance(cells, list) or not cells:
                errors.append("local experiment_schedule.json cells must be non-empty")
            else:
                for index, cell in enumerate(cells):
                    if not isinstance(cell, dict):
                        errors.append(
                            f"local experiment_schedule.json cells[{index}] must be an object"
                        )
                        continue
                    identifiers = (
                        cell.get("experiment_id"),
                        cell.get("variant_id"),
                        cell.get("benchmark_task_id"),
                    )
                    if not all(isinstance(value, str) and value.strip() for value in identifiers):
                        errors.append(
                            f"local experiment_schedule.json cells[{index}] has invalid IDs"
                        )
                    seed = cell.get("seed")
                    if not isinstance(seed, int) or isinstance(seed, bool):
                        errors.append(
                            f"local experiment_schedule.json cells[{index}] has invalid seed"
                        )
                    metrics = cell.get("metrics")
                    if not isinstance(metrics, list) or not metrics or not all(
                        isinstance(metric, str) and metric.strip() for metric in metrics
                    ):
                        errors.append(
                            f"local experiment_schedule.json cells[{index}] has invalid metrics"
                        )

    result_contract_path = run_dir / "result_contract.json"
    result_contract = _read_required_json(
        result_contract_path, "result_contract.json", errors
    )
    if result_contract is not None:
        if not isinstance(result_contract, dict):
            errors.append("local result_contract.json must contain an object")
        else:
            if result_contract.get("schema_version") != "1.0":
                errors.append("local result_contract.json must use schema_version 1.0")
            if result_contract.get("format") != "autodesign-results-v1":
                errors.append(
                    "local result_contract.json format must be autodesign-results-v1"
                )
            result_path = PurePosixPath(str(result_contract.get("path") or ""))
            if not str(result_path) or result_path.is_absolute() or ".." in result_path.parts:
                errors.append(
                    "local result_contract.json path must stay inside generated_project"
                )


def validate_remote_config(config: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    errors: list[str] = []
    missing_slots: list[str] = []
    required_fields = (
        "ssh.host",
        "ssh.user",
        "ssh.port",
        "ssh.connect_timeout_seconds",
        "ssh.strict_host_key_checking",
        "remote.allowed_root",
        "remote.repo_dir",
        "remote.work_dir",
        "remote.policy_file",
        "git.repo_url",
        "git.remote_name",
        "git.branch",
        "git.pull_mode",
        "transfer.mode",
        "transfer.rsync_executable",
        "transfer.source_dir",
        "transfer.excludes",
        "conda.executable",
        "conda.env_name",
        "conda.environment_file",
        "gpu.visible_devices",
        "gpu.required_count",
        "limits.max_parallel_jobs",
        "limits.command_timeout_seconds",
        "run.commands",
        "run.result_paths",
        "run.primary_result_path",
        "local.run_dir",
        "local.artifact_dir",
        "local.log_dir",
        "local.result_dir",
    )
    if config.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    for field in required_fields:
        value = _nested(config, field)
        if value in (None, "", []):
            errors.append(f"Missing field: {field}")
        elif _has_placeholder(value):
            missing_slots.append(field)

    ssh = config.get("ssh") or {}
    if not isinstance(ssh.get("port"), int) or not 1 <= ssh.get("port", 0) <= 65535:
        errors.append("ssh.port must be an integer from 1 through 65535")
    if not isinstance(ssh.get("connect_timeout_seconds"), int) or ssh.get(
        "connect_timeout_seconds", 0
    ) <= 0:
        errors.append("ssh.connect_timeout_seconds must be a positive integer")
    if not isinstance(ssh.get("strict_host_key_checking"), bool):
        errors.append("ssh.strict_host_key_checking must be a boolean")
    identity = str(ssh.get("identity_file") or "").strip()
    if identity and not Path(identity).expanduser().is_file():
        errors.append(f"ssh.identity_file does not exist: {identity}")

    remote = config.get("remote") or {}
    allowed_root = str(remote.get("allowed_root") or "")
    repo_dir = str(remote.get("repo_dir") or "")
    work_dir = str(remote.get("work_dir") or "")
    for field, value in (
        ("remote.allowed_root", allowed_root),
        ("remote.repo_dir", repo_dir),
        ("remote.work_dir", work_dir),
    ):
        if value and not PurePosixPath(value).is_absolute():
            errors.append(f"{field} must be an absolute POSIX path")
        if any(character.isspace() for character in value):
            errors.append(f"{field} must not contain whitespace")
        if ".." in PurePosixPath(value).parts:
            errors.append(f"{field} must not contain ..")
        if value and posixpath.normpath(value) != value:
            errors.append(f"{field} must be a normalized POSIX path")
    if posixpath.normpath(allowed_root) == "/":
        errors.append("remote.allowed_root must be narrower than /")
    if allowed_root and repo_dir and not _is_inside(repo_dir, allowed_root):
        errors.append("remote.repo_dir must be inside remote.allowed_root")
    if repo_dir and work_dir and not _is_inside(work_dir, repo_dir):
        errors.append("remote.work_dir must be inside remote.repo_dir")

    git = config.get("git") or {}
    if git.get("pull_mode") != "ff-only":
        errors.append("git.pull_mode must be ff-only")

    transfer = config.get("transfer") or {}
    transfer_mode = transfer.get("mode")
    if transfer_mode not in {"git", "rsync"}:
        errors.append("transfer.mode must be git or rsync")
    source_dir_value = str(transfer.get("source_dir") or "")
    source_dir = (repo_root / source_dir_value).resolve()
    try:
        source_dir.relative_to(repo_root)
    except ValueError:
        errors.append("transfer.source_dir must stay inside the local repository")
    if source_dir_value and not source_dir.is_dir():
        errors.append(f"transfer.source_dir does not exist: {source_dir}")
    excludes = transfer.get("excludes")
    if not isinstance(excludes, list) or not all(
        isinstance(item, str) and item for item in excludes
    ):
        errors.append("transfer.excludes must be a list of non-empty strings")

    conda = config.get("conda") or {}
    environment_file = PurePosixPath(str(conda.get("environment_file") or ""))
    if environment_file.is_absolute() or ".." in environment_file.parts:
        errors.append("conda.environment_file must be relative to remote.repo_dir")
    elif str(environment_file):
        local_environment_file = repo_root / Path(str(environment_file))
        if not local_environment_file.is_file():
            errors.append(f"Local environment definition is missing: {local_environment_file}")

    gpu = config.get("gpu") or {}
    visible_devices = gpu.get("visible_devices") or []
    if not isinstance(visible_devices, list) or not visible_devices:
        errors.append("gpu.visible_devices must be a non-empty list")
    elif any(
        not isinstance(item, str) or not item.isdigit() for item in visible_devices
    ) and not _has_placeholder(visible_devices):
        errors.append("gpu.visible_devices accepts numeric GPU indexes")
    if gpu.get("required_count") != len(visible_devices) and not _has_placeholder(
        visible_devices
    ):
        errors.append("gpu.required_count must match gpu.visible_devices length")

    limits = config.get("limits") or {}
    if not isinstance(limits.get("max_parallel_jobs"), int) or limits.get(
        "max_parallel_jobs", 0
    ) <= 0:
        errors.append("limits.max_parallel_jobs must be a positive integer")
    if not isinstance(limits.get("command_timeout_seconds"), int) or limits.get(
        "command_timeout_seconds", 0
    ) <= 0:
        errors.append("limits.command_timeout_seconds must be a positive integer")

    run_commands = (config.get("run") or {}).get("commands")
    if not isinstance(run_commands, dict):
        errors.append("run.commands must be an object")
    else:
        missing_stages = [stage for stage in STAGE_ORDER if stage not in run_commands]
        if missing_stages:
            errors.append(
                "run.commands is missing ordered stages: " + ", ".join(missing_stages)
            )
        for stage in STAGE_ORDER:
            command = run_commands.get(stage)
            if stage in run_commands and (
                not isinstance(command, str) or not command.strip()
            ):
                errors.append(f"run.commands.{stage} must be a non-empty string")

    policy_file_value = str(remote.get("policy_file") or "")
    policy_path = repo_root / policy_file_value
    if policy_file_value and not policy_path.is_file():
        errors.append(f"remote.policy_file does not exist: {policy_path}")
    elif policy_path.is_file() and _has_placeholder(policy_path.read_text(encoding="utf-8")):
        missing_slots.append("remote.policy_file content")

    result_paths = (config.get("run") or {}).get("result_paths") or []
    for index, result_path in enumerate(result_paths):
        if not isinstance(result_path, str) or not result_path.strip():
            errors.append(f"run.result_paths[{index}] must be a non-empty string")
            continue
        path = PurePosixPath(str(result_path))
        if path.is_absolute() or ".." in path.parts:
            errors.append(f"run.result_paths[{index}] must be relative to remote.repo_dir")
    primary_result_path = str((config.get("run") or {}).get("primary_result_path") or "")
    if primary_result_path and not _has_placeholder(primary_result_path):
        primary_path = PurePosixPath(primary_result_path)
        if primary_path.is_absolute() or ".." in primary_path.parts:
            errors.append("run.primary_result_path must be relative to remote.repo_dir")
        if primary_result_path not in result_paths:
            errors.append("run.primary_result_path must also appear in run.result_paths")

    local = config.get("local") or {}
    for field in ("run_dir", "artifact_dir", "log_dir", "result_dir"):
        raw_path = str(local.get(field) or "")
        if not raw_path or _has_placeholder(raw_path):
            continue
        resolved = (repo_root / raw_path).resolve()
        try:
            resolved.relative_to(repo_root)
        except ValueError:
            errors.append(f"local.{field} must stay inside the local repository")
    run_dir_value = str(local.get("run_dir") or "")
    generated_project = repo_root / "MISSING_RUN_DIR" / "generated_project"
    project_environment_file = generated_project / "environment.yml"
    if run_dir_value and not _has_placeholder(run_dir_value):
        run_dir = (repo_root / run_dir_value).resolve()
        if not run_dir.is_dir():
            errors.append(f"local.run_dir does not exist: {run_dir}")
        else:
            _validate_materialized_run_contracts(run_dir, errors)
            generated_project = run_dir / "generated_project"
            if not generated_project.is_dir():
                errors.append(
                    "local generated_project is missing: "
                    f"{generated_project}; run the autodesign-implementer Skill before remote sync"
                )
            project_environment_relative = "environment.yml"
            relative_environment_path = PurePosixPath(project_environment_relative)
            if (
                relative_environment_path.is_absolute()
                or ".." in relative_environment_path.parts
            ):
                errors.append(
                    "generated project environment path must stay inside generated_project"
                )
            else:
                project_environment_file = generated_project / Path(
                    str(relative_environment_path)
                )
                if generated_project.is_dir() and not project_environment_file.is_file():
                    errors.append(
                        "generated project environment definition is missing: "
                        f"{project_environment_file}"
                    )

    status = "FAIL" if errors else "CONFIG_INCOMPLETE" if missing_slots else "PASS"
    return {
        "status": status,
        "ready_for_ssh": status == "PASS",
        "missing_slots": sorted(set(missing_slots)),
        "errors": errors,
        "resolved_policy_file": str(policy_path.resolve()) if policy_path.exists() else str(policy_path),
        "resolved_environment_file": str(
            (repo_root / Path(str(environment_file))).resolve()
        ),
        "resolved_generated_project": str(generated_project.resolve()),
        "resolved_project_environment_file": str(project_environment_file.resolve()),
    }


class RemoteGPUController:
    """Build and execute constrained SSH operations from one config file."""

    OPERATIONS = ("preflight", "sync", "bootstrap", "run")

    def __init__(
        self,
        config_path: str | Path,
        *,
        repo_root: str | Path | None = None,
        ssh_executable: str = "ssh",
    ) -> None:
        self.repo_root = (
            Path(repo_root).resolve()
            if repo_root is not None
            else Path(__file__).resolve().parent.parent
        )
        self.config_path = Path(config_path).resolve()
        self.config = read_json(self.config_path)
        if not isinstance(self.config, dict):
            raise RemoteGPUError("Remote GPU config must be a JSON object")
        self.ssh_executable = ssh_executable
        self.command_source = "config.run.commands"
        self.result_contract_source = "config.run"
        self._apply_materialized_run_contract()

    def _apply_materialized_run_contract(self) -> None:
        """Prefer the accepted code bundle's commands and primary result path."""

        local = self.config.get("local") or {}
        run_dir_value = str(local.get("run_dir") or "")
        if not run_dir_value or _has_placeholder(run_dir_value):
            return
        run_path = (self.repo_root / run_dir_value).resolve()
        command_plan_path = run_path / "command_plan.json"
        if command_plan_path.is_file():
            self.command_source = str(command_plan_path)
            try:
                command_plan = read_json(command_plan_path)
            except (OSError, json.JSONDecodeError):
                command_plan = None
            if isinstance(command_plan, dict):
                resolved_commands: dict[str, str] = {}
                for stage in STAGE_ORDER:
                    commands = command_plan.get(stage)
                    if not isinstance(commands, list) or not commands or not all(
                        isinstance(command, str) and command.strip()
                        for command in commands
                    ):
                        break
                    resolved_commands[stage] = " && ".join(commands)
                if len(resolved_commands) == len(STAGE_ORDER):
                    self.config.setdefault("run", {})["commands"] = resolved_commands

        result_contract_path = run_path / "result_contract.json"
        if not result_contract_path.is_file():
            return
        self.result_contract_source = str(result_contract_path)
        try:
            result_contract = read_json(result_contract_path)
        except (OSError, json.JSONDecodeError):
            return
        if (
            not isinstance(result_contract, dict)
            or result_contract.get("schema_version") != "1.0"
        ):
            return
        result_path = PurePosixPath(str(result_contract.get("path") or ""))
        remote = self.config.get("remote") or {}
        try:
            work_relative = PurePosixPath(str(remote["work_dir"])).relative_to(
                PurePosixPath(str(remote["repo_dir"]))
            )
        except (KeyError, ValueError):
            return
        if not str(result_path) or result_path.is_absolute() or ".." in result_path.parts:
            return
        primary_result_path = str(work_relative / result_path)
        run = self.config.setdefault("run", {})
        run["primary_result_path"] = primary_result_path
        run["result_paths"] = [primary_result_path]

    def validate(self) -> dict[str, Any]:
        report = validate_remote_config(self.config, self.repo_root)
        report["config_path"] = str(self.config_path)
        report["run_command_source"] = self.command_source
        report["result_contract_source"] = self.result_contract_source
        report["local_git"] = self.local_git_state()
        return report

    def local_git_state(self) -> dict[str, Any]:
        def git(*args: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                ["git", *args],
                cwd=self.repo_root,
                text=True,
                capture_output=True,
                check=False,
            )

        branch = git("branch", "--show-current")
        commit = git("rev-parse", "HEAD")
        status = git("status", "--porcelain")
        upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
        divergence = git("rev-list", "--left-right", "--count", "@{u}...HEAD")
        configured_git = self.config.get("git") or {}
        configured_branch = str(configured_git.get("branch") or "")
        configured_remote = str(configured_git.get("remote_name") or "")
        configured_url = str(configured_git.get("repo_url") or "")
        remote_url = git("remote", "get-url", configured_remote) if configured_remote else None
        branch_name = branch.stdout.strip()
        upstream_name = upstream.stdout.strip() if upstream.returncode == 0 else None
        behind_count: int | None = None
        ahead_count: int | None = None
        if divergence.returncode == 0:
            fields = divergence.stdout.split()
            if len(fields) == 2 and all(field.isdigit() for field in fields):
                behind_count, ahead_count = (int(fields[0]), int(fields[1]))
        expected_upstream = f"{configured_remote}/{configured_branch}"
        remote_url_value = remote_url.stdout.strip() if remote_url and remote_url.returncode == 0 else None
        return {
            "branch": branch_name,
            "commit": commit.stdout.strip(),
            "dirty": bool(status.stdout.strip()),
            "upstream": upstream_name,
            "ahead_count": ahead_count,
            "behind_count": behind_count,
            "remote_url": remote_url_value,
            "configured_branch_matches": branch_name == configured_branch,
            "configured_upstream_matches": upstream_name == expected_upstream,
            "configured_remote_url_matches": remote_url_value == configured_url,
            "ready_for_remote_pull": (
                branch_name == configured_branch
                and not bool(status.stdout.strip())
                and upstream_name == expected_upstream
                and remote_url_value == configured_url
                and ahead_count == 0
                and behind_count == 0
            ),
        }

    def _ssh_argv(self) -> list[str]:
        ssh = self.config["ssh"]
        argv = [
            self.ssh_executable,
            "-p",
            str(ssh["port"]),
            "-o",
            "BatchMode=yes",
            "-o",
            f"ConnectTimeout={ssh['connect_timeout_seconds']}",
            "-o",
            f"StrictHostKeyChecking={'yes' if ssh['strict_host_key_checking'] else 'accept-new'}",
        ]
        identity = str(ssh.get("identity_file") or "").strip()
        if identity:
            argv.extend(["-i", str(Path(identity).expanduser())])
        argv.extend([f"{ssh['user']}@{ssh['host']}", "/bin/bash", "-s"])
        return argv

    def _ssh_transport_argv(self) -> list[str]:
        return self._ssh_argv()[:-3]

    def _rsync_argv(self, *, upload: bool) -> list[str]:
        transfer = self.config["transfer"]
        ssh = self.config["ssh"]
        remote = self.config["remote"]
        transport = " ".join(_quote(item) for item in self._ssh_transport_argv())
        argv = [
            transfer["rsync_executable"],
            "-az",
            "--partial",
            "--itemize-changes",
            "-e",
            transport,
        ]
        if upload:
            for pattern in transfer["excludes"]:
                argv.extend(["--exclude", pattern])
            argv.extend(["--exclude", ".autodesign_rsync_release"])
            if transfer.get("delete_remote_extraneous"):
                argv.append("--delete")
            source = str((self.repo_root / transfer["source_dir"]).resolve()).rstrip("/") + "/"
            destination = f"{ssh['user']}@{ssh['host']}:{remote['repo_dir'].rstrip('/')}/"
            argv.extend([source, destination])
        return argv

    def _generated_project_rsync_argv(self) -> list[str]:
        """Build the rsync command that places generated code in remote.work_dir."""

        ssh = self.config["ssh"]
        remote = self.config["remote"]
        local = self.config["local"]
        source = (
            self.repo_root / str(local["run_dir"]) / "generated_project"
        ).resolve()
        destination = f"{ssh['user']}@{ssh['host']}:{remote['work_dir'].rstrip('/')}/"
        return [
            *self._rsync_argv(upload=False),
            "--exclude",
            "assets/output/",
            "--exclude",
            "assets/logs/",
            str(source).rstrip("/") + "/",
            destination,
        ]

    @staticmethod
    def _project_environment_relative_path() -> str:
        return "environment.yml"

    def _common_script(self) -> str:
        remote = self.config["remote"]
        return f"""set -euo pipefail
export LC_ALL=C
ALLOWED_ROOT={_quote(remote['allowed_root'])}
REPO_DIR={_quote(remote['repo_dir'])}
WORK_DIR={_quote(remote['work_dir'])}

case "$REPO_DIR/" in
  "$ALLOWED_ROOT/"*) ;;
  *) printf 'REMOTE_POLICY_FAIL repo_outside_allowed_root=%s\\n' "$REPO_DIR" >&2; exit 21 ;;
esac
case "$WORK_DIR/" in
  "$REPO_DIR/"*) ;;
  *) printf 'REMOTE_POLICY_FAIL work_outside_repo=%s\\n' "$WORK_DIR" >&2; exit 22 ;;
esac
"""

    @staticmethod
    def _gpu_snapshot_script() -> str:
        return """printf 'GPU_STATE_BEGIN\\n'
nvidia-smi --query-gpu=index,uuid,name,memory.total,memory.used,memory.free,utilization.gpu --format=csv,noheader,nounits
printf 'GPU_STATE_END\\nCOMPUTE_PROCESSES_BEGIN\\n'
nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader,nounits 2>/dev/null || true
printf 'COMPUTE_PROCESSES_END\\n'
"""

    def build_script(self, operation: str, command_key: str | None = None) -> str:
        if operation not in self.OPERATIONS:
            raise RemoteGPUError(f"Unknown remote operation: {operation}")
        config = self.config
        git = config["git"]
        conda = config["conda"]
        gpu = config["gpu"]
        common = self._common_script()
        if operation == "preflight":
            gpu_words = " ".join(_quote(item) for item in gpu["visible_devices"])
            transfer_command = "git" if config["transfer"]["mode"] == "git" else "rsync"
            gpu_snapshot = self._gpu_snapshot_script()
            return common + f"""
CONDA_EXE={_quote(conda['executable'])}
test -x "$CONDA_EXE" || {{ printf 'PREFLIGHT_FAIL conda=%s\\n' "$CONDA_EXE" >&2; exit 31; }}
command -v {_quote(transfer_command)} >/dev/null
command -v rsync >/dev/null
command -v nvidia-smi >/dev/null
command -v timeout >/dev/null
AVAILABLE_GPUS="$(nvidia-smi --query-gpu=index --format=csv,noheader,nounits | tr -d ' ')"
for gpu_id in {gpu_words}; do
  printf '%s\\n' "$AVAILABLE_GPUS" | grep -Fxq "$gpu_id" || {{ printf 'PREFLIGHT_FAIL gpu=%s\\n' "$gpu_id" >&2; exit 32; }}
done
{gpu_snapshot.rstrip()}
printf 'PREFLIGHT_PASS host=%s conda=%s gpus=%s allowed_root=%s\\n' "$(hostname)" "$CONDA_EXE" {_quote(','.join(gpu['visible_devices']))} "$ALLOWED_ROOT"
"""
        if operation == "sync":
            if config["transfer"]["mode"] == "rsync":
                return common + """
command -v rsync >/dev/null
mkdir -p "$ALLOWED_ROOT"
if [ -e "$REPO_DIR" ] && [ ! -d "$REPO_DIR" ]; then
  printf 'RSYNC_PREPARE_FAIL repo_path_not_directory=%s\n' "$REPO_DIR" >&2
  exit 44
fi
mkdir -p "$REPO_DIR"
mkdir -p "$WORK_DIR"
printf 'RSYNC_PREPARE_PASS repo=%s\n' "$REPO_DIR"
"""
            expected_commit = self.local_git_state()["commit"]
            return common + f"""
REPO_URL={_quote(git['repo_url'])}
REMOTE_NAME={_quote(git['remote_name'])}
BRANCH={_quote(git['branch'])}
EXPECTED_COMMIT={_quote(expected_commit)}
mkdir -p "$ALLOWED_ROOT"
if [ -d "$REPO_DIR/.git" ]; then
  cd "$REPO_DIR"
  tracked_changes="$(git status --porcelain --untracked-files=no)"
  [ -z "$tracked_changes" ] || {{ printf 'GIT_SYNC_FAIL tracked_changes\\n%s\\n' "$tracked_changes" >&2; exit 41; }}
  actual_url="$(git remote get-url "$REMOTE_NAME")"
  [ "$actual_url" = "$REPO_URL" ] || {{ printf 'GIT_SYNC_FAIL remote_url=%s expected=%s\\n' "$actual_url" "$REPO_URL" >&2; exit 42; }}
  git fetch "$REMOTE_NAME" "$BRANCH"
  git checkout "$BRANCH"
  git pull --ff-only "$REMOTE_NAME" "$BRANCH"
else
  [ ! -e "$REPO_DIR" ] || {{ printf 'GIT_SYNC_FAIL repo_dir_exists_without_git=%s\\n' "$REPO_DIR" >&2; exit 43; }}
  git clone --single-branch --branch "$BRANCH" "$REPO_URL" "$REPO_DIR"
  cd "$REPO_DIR"
fi
ACTUAL_COMMIT="$(git rev-parse HEAD)"
[ "$ACTUAL_COMMIT" = "$EXPECTED_COMMIT" ] || {{ printf 'GIT_SYNC_FAIL commit=%s expected=%s\\n' "$ACTUAL_COMMIT" "$EXPECTED_COMMIT" >&2; exit 45; }}
printf 'GIT_SYNC_PASS branch=%s commit=%s repo=%s\\n' "$(git branch --show-current)" "$ACTUAL_COMMIT" "$REPO_DIR"
"""
        if operation == "bootstrap":
            project_environment_relative = self._project_environment_relative_path()
            return common + f"""
export PIP_TIMEOUT=180
export PIP_RETRIES=20
export PIP_RESUME_RETRIES=30
export TMPDIR="$WORK_DIR/assets/tmp"
export PIP_CACHE_DIR="$WORK_DIR/assets/cache/pip"
mkdir -p "$TMPDIR" "$PIP_CACHE_DIR"
CONDA_EXE={_quote(conda['executable'])}
ENV_NAME={_quote(conda['env_name'])}
ENV_FILE="$REPO_DIR/{conda['environment_file']!s}"
PROJECT_ENV_REL={_quote(project_environment_relative)}
PROJECT_ENV_FILE="$WORK_DIR/$PROJECT_ENV_REL"
test -d "$REPO_DIR"
test -d "$WORK_DIR"
test -f "$ENV_FILE"
test -f "$PROJECT_ENV_FILE" || {{ printf 'CONDA_BOOTSTRAP_FAIL project_environment=%s\\n' "$PROJECT_ENV_FILE" >&2; exit 46; }}
test -x "$CONDA_EXE"
cd "$REPO_DIR"
if "$CONDA_EXE" env list | awk 'NF && $1 !~ /^#/ {{print $1}}' | grep -Fxq "$ENV_NAME"; then
  "$CONDA_EXE" env update --name "$ENV_NAME" --file "$ENV_FILE" --prune
  env_action=updated
else
  "$CONDA_EXE" env create --name "$ENV_NAME" --file "$ENV_FILE"
  env_action=created
fi
cd "$WORK_DIR"
"$CONDA_EXE" env update --name "$ENV_NAME" --file "$PROJECT_ENV_FILE"
project_env_action=updated
cd "$REPO_DIR"
"$CONDA_EXE" run --no-capture-output -n "$ENV_NAME" python3 -m pip install -e "$REPO_DIR"
python_version="$("$CONDA_EXE" run -n "$ENV_NAME" python3 -c 'import platform; print(platform.python_version())')"
printf 'CONDA_BOOTSTRAP_PASS env=%s action=%s project_env=%s python=%s control_file=%s project_file=%s\\n' "$ENV_NAME" "$env_action" "$project_env_action" "$python_version" "$ENV_FILE" "$PROJECT_ENV_FILE"
"""

        commands = (config.get("run") or {}).get("commands") or {}
        if not command_key or command_key not in commands:
            raise RemoteGPUError(f"Unknown run command key: {command_key}")
        run_command = commands[command_key]
        gpu_csv = ",".join(gpu["visible_devices"])
        timeout_seconds = config["limits"]["command_timeout_seconds"]
        max_parallel_jobs = config["limits"]["max_parallel_jobs"]
        gpu_snapshot = self._gpu_snapshot_script()
        if config["transfer"]["mode"] == "git":
            source_guard = """test -d "$REPO_DIR/.git"
cd "$REPO_DIR"
[ "$(git branch --show-current)" = "$BRANCH" ] || { printf 'REMOTE_RUN_FAIL branch=%s expected=%s\n' "$(git branch --show-current)" "$BRANCH" >&2; exit 51; }
tracked_changes="$(git status --porcelain --untracked-files=no)"
[ -z "$tracked_changes" ] || { printf 'REMOTE_RUN_FAIL tracked_changes\n%s\n' "$tracked_changes" >&2; exit 52; }
SOURCE_REVISION="$(git rev-parse HEAD)"
"""
        else:
            source_guard = """test -d "$REPO_DIR"
test -f "$REPO_DIR/.autodesign_rsync_release"
cd "$REPO_DIR"
SOURCE_REVISION="$(tr '\n' ';' < .autodesign_rsync_release)"
"""
        return common + f"""
CONDA_EXE={_quote(conda['executable'])}
ENV_NAME={_quote(conda['env_name'])}
BRANCH={_quote(git['branch'])}
GPU_CSV={_quote(gpu_csv)}
RUN_COMMAND={_quote(run_command)}
LOCK_DIR="$ALLOWED_ROOT/.autodesign_gpu_job.lock"

test -x "$CONDA_EXE"
{source_guard.rstrip()}
mkdir "$LOCK_DIR" 2>/dev/null || {{ printf 'REMOTE_RUN_FAIL active_job_lock=%s\\n' "$LOCK_DIR" >&2; exit 53; }}
trap 'rmdir "$LOCK_DIR"' EXIT
export CUDA_VISIBLE_DEVICES="$GPU_CSV"
export NVIDIA_VISIBLE_DEVICES="$GPU_CSV"
export AUTODESIGN_ALLOWED_ROOT="$ALLOWED_ROOT"
export AUTODESIGN_COMMAND_TIMEOUT_SECONDS={timeout_seconds}
export AUTODESIGN_MAX_PARALLEL_JOBS={max_parallel_jobs}
export TOKENIZERS_PARALLELISM=false
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME="$WORK_DIR/assets/cache/huggingface"
export HF_HUB_DOWNLOAD_TIMEOUT=600
export HF_HUB_ETAG_TIMEOUT=60
mkdir -p "$HF_HOME"
printf 'REMOTE_RUN_START key=%s transfer=%s revision=%s gpus=%s work_dir=%s\\n' {_quote(command_key)} {_quote(config['transfer']['mode'])} "$SOURCE_REVISION" "$CUDA_VISIBLE_DEVICES" "$WORK_DIR"
{gpu_snapshot.rstrip()}
set +e
cd "$WORK_DIR"
timeout --signal=TERM --kill-after=60s "${{AUTODESIGN_COMMAND_TIMEOUT_SECONDS}}s" \
  "$CONDA_EXE" run --no-capture-output -n "$ENV_NAME" \
  /bin/bash -lc "$RUN_COMMAND"
run_exit=$?
set -e
printf 'REMOTE_RUN_END key=%s exit_status=%s gpus=%s\\n' {_quote(command_key)} "$run_exit" "$CUDA_VISIBLE_DEVICES"
exit "$run_exit"
"""

    def render_agent_prompt(self) -> str:
        report = self.validate()
        remote = self.config["remote"]
        policy_path = self.repo_root / remote["policy_file"]
        policy = policy_path.read_text(encoding="utf-8") if policy_path.exists() else "POLICY_FILE_MISSING"
        return f"""# AutoDesign Remote GPU Agent Prompt

你在 SSH GPU 服务器上运行 AutoDesign 实验。所有远端动作通过本项目 `remote-*` CLI 生成的脚本执行。

## 固定执行合同

- 源码传输模式：`{self.config['transfer']['mode']}`，可选 Git clone/pull 或 rsync 增量同步。
- 远端允许根目录：`{remote['allowed_root']}`
- 远端仓库目录：`{remote['repo_dir']}`
- 远端工作目录：`{remote['work_dir']}`
- Git 分支：`{self.config['git']['branch']}`
- Conda 环境：`{self.config['conda']['env_name']}`
- 强制 GPU：`{','.join(self.config['gpu']['visible_devices'])}`
- 最大并行任务：`{self.config['limits']['max_parallel_jobs']}`
- 命令超时秒数：`{self.config['limits']['command_timeout_seconds']}`
- 本地执行记录目录：`{self.config['local']['run_dir']}`
- 配置状态：`{report['status']}`

运行顺序固定为：host-preflight → sync → bootstrap → project-preflight → smoke → experiment → aggregate → project-collect → result-transfer。每一步保存 stdout、stderr 与 exit status；上一步 PASS 后进入下一步。

## 用户填写的约束

{policy.rstrip()}
"""

    def write_plan(self, output_dir: str | Path, command_key: str = "experiment") -> dict[str, Any]:
        validation = self.validate()
        if validation["status"] == "FAIL":
            return {"status": "FAIL", "failed_step": "validate", "validation": validation}
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        scripts = {
            operation: self.build_script(operation, command_key if operation == "run" else None)
            for operation in self.OPERATIONS
        }
        report = {
            "status": "PLAN_READY",
            "config_validation": self.validate(),
            "ssh_argv": self._ssh_argv(),
            "command_key": command_key,
            "scripts": scripts,
            "code_transport": self.config["transfer"]["mode"],
        }
        if self.config["transfer"]["mode"] == "rsync":
            report["rsync_argv"] = self._rsync_argv(upload=True)
            report["generated_project_rsync_argv"] = self._generated_project_rsync_argv()
        plan_path = write_json(output_path / "remote_execution_plan.json", report)
        prompt_path = write_text(output_path / "remote_agent_prompt.md", self.render_agent_prompt())
        return {
            "status": "PLAN_READY",
            "plan": str(plan_path.resolve()),
            "agent_prompt": str(prompt_path.resolve()),
            "config_status": report["config_validation"]["status"],
        }

    def _artifact_path(self, section: str, name: str, suffix: str) -> Path:
        configured = self.config.get("local", {}).get(section)
        base = self.repo_root / str(configured)
        base.mkdir(parents=True, exist_ok=True)
        return base / f"{name}.{suffix}"

    def _write_pipeline_execution_record(self, remote_record: dict[str, Any]) -> Path:
        """Write the remote command in the execution shape consumed by ingest-results."""

        run_path = (self.repo_root / self.config["local"]["run_dir"]).resolve()
        record_path = run_path / "execution_record.json"
        command_key = str(remote_record["command_key"])
        existing: dict[str, Any] | None = None
        if record_path.is_file() and command_key != STAGE_ORDER[0]:
            candidate = read_json(record_path)
            if isinstance(candidate, dict) and candidate.get("executor") == "remote_gpu":
                existing = candidate
        commands: list[dict[str, Any]] = []
        if existing and command_key in STAGE_ORDER:
            target_index = STAGE_ORDER.index(command_key)
            existing_commands = existing.get("commands") or []
            for prior_stage in STAGE_ORDER[:target_index]:
                group = [
                    item
                    for item in existing_commands
                    if isinstance(item, dict) and item.get("stage") == prior_stage
                ]
                expected_command = self.config["run"]["commands"].get(prior_stage)
                if (
                    len(group) != 1
                    or group[0].get("command") != expected_command
                    or group[0].get("exit_status") != 0
                ):
                    break
                commands.extend(group)
        commands.append(
            {
                "stage": command_key,
                "command_index": 1,
                "command": self.config["run"]["commands"][command_key],
                "stdout": remote_record["stdout"],
                "stderr": remote_record["stderr"],
                "exit_status": remote_record["exit_status"],
                "remote_record_path": remote_record.get("record_path"),
            }
        )
        status = "PASS" if all(item["exit_status"] == 0 for item in commands) else "FAIL"
        progress = execution_progress(commands)
        pipeline_record = {
            "status": status,
            "executor": "remote_gpu",
            "stage": "remote",
            "started_at": existing.get("started_at") if existing else remote_record["started_at"],
            "finished_at": remote_record["finished_at"],
            "commands": commands,
            "gpu_visible_devices": self.config["gpu"]["visible_devices"],
            "transfer_mode": self.config["transfer"]["mode"],
            **progress,
        }
        return write_json(record_path, pipeline_record)

    def execute(
        self,
        operation: str,
        *,
        command_key: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        validation = self.validate()
        if validation["status"] == "FAIL":
            return {
                "status": "FAIL",
                "operation": operation,
                "command_key": command_key,
                "validation": validation,
            }
        script = self.build_script(operation, command_key)
        argv = self._ssh_argv()
        if dry_run:
            return {
                "status": "DRY_RUN",
                "operation": operation,
                "command_key": command_key,
                "config_status": validation["status"],
                "ssh_argv": argv,
                "remote_script": script,
            }
        if validation["status"] != "PASS":
            return {
                "status": "CONFIG_INCOMPLETE",
                "operation": operation,
                "validation": validation,
            }

        started_at = datetime.now(timezone.utc).isoformat()
        timeout = self.config["limits"]["command_timeout_seconds"]
        try:
            completed = subprocess.run(
                argv,
                input=script,
                text=True,
                capture_output=True,
                check=False,
                timeout=timeout,
            )
            exit_status = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
        except subprocess.TimeoutExpired as error:
            exit_status = 124
            stdout = error.stdout or ""
            stderr = (error.stderr or "") + f"\nREMOTE_TIMEOUT seconds={timeout}\n"
        record = {
            "status": "PASS" if exit_status == 0 else "FAIL",
            "operation": operation,
            "command_key": command_key,
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "ssh_argv": argv,
            "remote_script": script,
            "stdout": stdout,
            "stderr": stderr,
            "exit_status": exit_status,
        }
        artifact_name = f"run_{command_key}" if operation == "run" else operation
        record_path = self._artifact_path("artifact_dir", artifact_name, "json")
        log_path = self._artifact_path("log_dir", artifact_name, "log")
        write_json(record_path, record)
        write_text(
            log_path,
            f"SSH_ARGV: {json.dumps(argv)}\nEXIT_STATUS: {exit_status}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}",
        )
        record["record_path"] = str(record_path.resolve())
        record["log_path"] = str(log_path.resolve())
        if operation == "run":
            pipeline_record = self._write_pipeline_execution_record(record)
            record["pipeline_execution_record"] = str(pipeline_record.resolve())
            write_json(record_path, record)
        return record

    def deploy(self, *, dry_run: bool = False) -> dict[str, Any]:
        records: list[dict[str, Any]] = []
        for operation in ("preflight", "sync", "bootstrap"):
            record = (
                self.sync(dry_run=dry_run)
                if operation == "sync"
                else self.execute(operation, dry_run=dry_run)
            )
            records.append(record)
            if record["status"] == "FAIL" or (
                not dry_run and record["status"] != "PASS"
            ):
                break
        return {
            "status": (
                "FAIL"
                if any(item["status"] == "FAIL" for item in records)
                else "DRY_RUN"
                if dry_run
                else "PASS"
                if len(records) == 3 and all(item["status"] == "PASS" for item in records)
                else "FAIL"
            ),
            "operations": records,
        }

    def sync(self, *, dry_run: bool = False) -> dict[str, Any]:
        validation = self.validate()
        if validation["status"] == "FAIL":
            return {"status": "FAIL", "operation": "sync", "validation": validation}
        if self.config["transfer"]["mode"] == "git":
            local_git = self.local_git_state()
            if dry_run:
                record = self.execute("sync", dry_run=True)
                record["local_git"] = local_git
                record["generated_project_rsync_argv"] = (
                    self._generated_project_rsync_argv()
                )
                return record
            if validation["status"] != "PASS":
                return {"status": "CONFIG_INCOMPLETE", "validation": validation}
            if not local_git["ready_for_remote_pull"]:
                return {
                    "status": "FAIL",
                    "operation": "sync",
                    "mode": "git",
                    "error": "LOCAL_GIT_NOT_READY",
                    "local_git": local_git,
                }
            source_sync = self.execute("sync")
            if source_sync["status"] != "PASS":
                return source_sync
            timeout = self.config["limits"]["command_timeout_seconds"]
            generated_project_rsync_argv = self._generated_project_rsync_argv()
            generated_project_transferred = subprocess.run(
                generated_project_rsync_argv,
                text=True,
                capture_output=True,
                check=False,
                timeout=timeout,
            )
            report = {
                "status": (
                    "PASS" if generated_project_transferred.returncode == 0 else "FAIL"
                ),
                "operation": "sync",
                "mode": "git",
                "source_sync": source_sync,
                "generated_project_rsync": {
                    "command": generated_project_rsync_argv,
                    "stdout": generated_project_transferred.stdout,
                    "stderr": generated_project_transferred.stderr,
                    "exit_status": generated_project_transferred.returncode,
                },
                "exit_status": generated_project_transferred.returncode,
            }
            write_json(self._artifact_path("artifact_dir", "sync", "json"), report)
            return report

        prepare = self.execute("sync", dry_run=dry_run)
        rsync_argv = self._rsync_argv(upload=True)
        generated_project_rsync_argv = self._generated_project_rsync_argv()
        local_git = self.local_git_state()
        release_text = (
            f"mode=rsync\nbranch={local_git['branch']}\n"
            f"source_revision={local_git['commit']}\ndirty={str(local_git['dirty']).lower()}\n"
        )
        finalize_script = self._common_script() + f"""
cat > "$REPO_DIR/.autodesign_rsync_release" <<'AUTODESIGN_RELEASE'
{release_text.rstrip()}
AUTODESIGN_RELEASE
printf 'RSYNC_FINALIZE_PASS release=%s\\n' "$REPO_DIR/.autodesign_rsync_release"
"""
        if dry_run:
            return {
                "status": "DRY_RUN",
                "operation": "sync",
                "mode": "rsync",
                "config_status": validation["status"],
                "prepare": prepare,
                "rsync_argv": rsync_argv,
                "generated_project_rsync_argv": generated_project_rsync_argv,
                "finalize_script": finalize_script,
            }
        if validation["status"] != "PASS":
            return {"status": "CONFIG_INCOMPLETE", "validation": validation}
        if prepare["status"] != "PASS":
            return prepare

        timeout = self.config["limits"]["command_timeout_seconds"]
        transferred = subprocess.run(
            rsync_argv,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
        if transferred.returncode == 0:
            generated_project_transferred = subprocess.run(
                generated_project_rsync_argv,
                text=True,
                capture_output=True,
                check=False,
                timeout=timeout,
            )
        else:
            generated_project_transferred = None
        if (
            transferred.returncode == 0
            and generated_project_transferred is not None
            and generated_project_transferred.returncode == 0
        ):
            finalized = subprocess.run(
                self._ssh_argv(),
                input=finalize_script,
                text=True,
                capture_output=True,
                check=False,
                timeout=timeout,
            )
        else:
            finalized = None
        exit_status = (
            transferred.returncode
            if transferred.returncode != 0
            else generated_project_transferred.returncode
            if generated_project_transferred is not None
            and generated_project_transferred.returncode != 0
            else finalized.returncode
            if finalized is not None
            else 1
        )
        report = {
            "status": "PASS" if exit_status == 0 else "FAIL",
            "operation": "sync",
            "mode": "rsync",
            "prepare": prepare,
            "rsync": {
                "command": rsync_argv,
                "stdout": transferred.stdout,
                "stderr": transferred.stderr,
                "exit_status": transferred.returncode,
            },
            "generated_project_rsync": (
                {
                    "command": generated_project_rsync_argv,
                    "stdout": generated_project_transferred.stdout,
                    "stderr": generated_project_transferred.stderr,
                    "exit_status": generated_project_transferred.returncode,
                }
                if generated_project_transferred is not None
                else None
            ),
            "finalize": (
                {
                    "stdout": finalized.stdout,
                    "stderr": finalized.stderr,
                    "exit_status": finalized.returncode,
                }
                if finalized is not None
                else None
            ),
            "exit_status": exit_status,
        }
        write_json(self._artifact_path("artifact_dir", "sync", "json"), report)
        return report

    def collect_results(self, *, dry_run: bool = False) -> dict[str, Any]:
        validation = self.validate()
        if validation["status"] == "FAIL":
            return {"status": "FAIL", "operation": "collect", "validation": validation}
        ssh = self.config["ssh"]
        repo_dir = self.config["remote"]["repo_dir"]
        result_paths = self.config["run"]["result_paths"]
        local_result_dir = self.repo_root / self.config["local"]["result_dir"]
        local_result_dir.mkdir(parents=True, exist_ok=True)
        commands = []
        rsync_base = self._rsync_argv(upload=False)
        for result_path in result_paths:
            source = f"{ssh['user']}@{ssh['host']}:{repo_dir}/./{result_path}"
            commands.append(
                [
                    *rsync_base,
                    "-R",
                    source,
                    str(local_result_dir),
                ]
            )
        if dry_run:
            return {
                "status": "DRY_RUN",
                "config_status": validation["status"],
                "commands": commands,
                "destination": str(local_result_dir.resolve()),
            }
        if validation["status"] != "PASS":
            return {"status": "CONFIG_INCOMPLETE", "validation": validation}

        records = []
        timeout = self.config["limits"]["command_timeout_seconds"]
        for command in commands:
            completed = subprocess.run(
                command,
                text=True,
                capture_output=True,
                check=False,
                timeout=timeout,
            )
            records.append(
                {
                    "command": command,
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                    "exit_status": completed.returncode,
                }
            )
            if completed.returncode != 0:
                break
        status = "PASS" if len(records) == len(commands) and all(
            item["exit_status"] == 0 for item in records
        ) else "FAIL"
        report = {
            "status": status,
            "records": records,
            "destination": str(local_result_dir.resolve()),
        }
        write_json(self._artifact_path("artifact_dir", "collect", "json"), report)
        return report
