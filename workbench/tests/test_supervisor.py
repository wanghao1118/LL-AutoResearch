"""Exercise browser recovery against actual disposable worker processes."""

import json
import sys
import threading
import time
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from workbench.supervisor import Handler, Service


def wait_for(callback):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        result = callback()
        if result:
            return result
        time.sleep(0.1)
    raise AssertionError("Disposable worker did not reach expected state")


@pytest.fixture
def supervised(tmp_path):
    service = Service(tmp_path, tmp_path / "assets/output/workbench")
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, service=service))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def request(path, payload=None):
        req = Request(
            f"http://127.0.0.1:{server.server_port}{path}",
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={"Content-Type": "application/json"},
        )
        try:
            response = urlopen(req, timeout=15)
        except HTTPError as error:
            response = error
        with response:
            data = response.read()
            return response.status, json.loads(data) if "application/json" in response.headers.get(
                "Content-Type", ""
            ) else data

    try:
        yield service, request
    finally:
        service.close()
        server.shutdown()
        server.server_close()
        thread.join(5)


def test_browser_home_survives_worker_exit_and_restart_restores_tasks(supervised):
    service, request = supervised
    assert request("/")[0] == 200
    assert not request("/api/service")[1]["connected"]
    assert request("/api/service/restart", {})[0] == 202
    wait_for(lambda: service.state()["connected"])
    code, task = request(
        "/auto-design/api/tasks",
        {
            "title": "Engineering only",
            "idea": "Motivation: fixture\nContribution: fixture",
            "scope": "design_only",
        },
    )
    assert code == 201
    # Simulate a crash of our own disposable worker, never a user process.
    service.process.terminate()
    service.process.wait(5)
    assert request("/")[0] == 200
    assert not request("/api/service")[1]["connected"]
    assert request("/api/service/restart", {})[0] == 202
    wait_for(lambda: service.state()["connected"])
    tasks = request("/auto-design/api/tasks")[1]["tasks"]
    assert [t["id"] for t in tasks] == [task["id"]]
    assert tasks[0]["status"] == "created" and tasks[0]["attempts"] == []
    assert request("/api/service/log")[0] == 200


def test_restart_stops_only_the_task_controller_and_keeps_resume_point(supervised, tmp_path):
    service, request = supervised
    executable = tmp_path / "codex-engineering-fixture"
    executable.write_text(
        f"#!{sys.executable}\nimport sys,time\nfrom pathlib import Path\nsys.stdin.read()\nPath('controller-started.txt').write_text('engineering fixture')\ntime.sleep(30)\n"
    )
    executable.chmod(0o755)
    assert request("/api/service/restart", {"settings": {"CODEX_CLI": str(executable)}})[0] == 202
    wait_for(lambda: service.state()["connected"])
    _, task = request(
        "/auto-design/api/tasks",
        {"idea": "Motivation: fixture\nContribution: fixture", "scope": "design_only"},
    )
    assert request(f"/auto-design/api/tasks/{task['id']}/start", {})[0] == 202
    wait_for(lambda: (Path(task["run_dir"]) / "controller-started.txt").is_file())
    old_pid = service.process.pid
    assert request("/api/service/restart", {})[0] == 202
    wait_for(
        lambda: (
            not service.restarting
            and service.process.pid != old_pid
            and service.state()["connected"]
        )
    )
    restored = request(f"/auto-design/api/tasks/{task['id']}")[1]
    assert restored["status"] == "paused"
    assert len(restored["attempts"]) == 1
    record = Path(task["run_dir"]) / "assets/logs/0001-design/execution.json"
    assert json.loads(record.read_text())["finished_at"]
    assert request("/api/service/restart", {"settings": {"CODEX_CLI": "/missing/tool"}})[0] == 400
    assert service.settings["CODEX_CLI"] == str(executable)
