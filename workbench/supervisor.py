"""Keep the browser control surface available when the research service is down."""

from __future__ import annotations

import argparse
import http.client
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WEB_ROOT = Path(__file__).resolve().parent / "web"


class Service:
    def __init__(self, workspace: Path, data_dir: Path):
        self.workspace, self.data_dir = workspace.resolve(), data_dir.resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.settings_path = self.data_dir / "service_settings.json"
        self.settings = (
            json.loads(self.settings_path.read_text()) if self.settings_path.is_file() else {}
        )
        self.log_path = self.workspace / "assets/logs/workbench/service.log"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.process: subprocess.Popen | None = None
        self.port = 0
        self.restarting = False
        self.message = "服务准备启动。"

    def start(self) -> None:
        with self.lock:
            if self.process and self.process.poll() is None:
                return
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                self.port = sock.getsockname()[1]
            env = {**os.environ, **self.settings}
            env["PYTHONPATH"] = str(WEB_ROOT.parents[1]) + os.pathsep + env.get("PYTHONPATH", "")
            command = [
                sys.executable,
                "-m",
                "workbench.server",
                "--port",
                str(self.port),
                "--workspace",
                str(self.workspace),
                "--data-dir",
                str(self.data_dir),
            ]
            with self.log_path.open("ab") as log:
                self.process = subprocess.Popen(
                    command,
                    cwd=self.workspace,
                    env=env,
                    stdout=log,
                    stderr=log,
                    start_new_session=True,
                )
            self.message = "研究服务正在启动。"

    def request(self, path: str, method: str = "GET", timeout: float = 3) -> dict:
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=timeout)
        try:
            conn.request(
                method,
                path,
                body=b"{}" if method == "POST" else None,
                headers={"Content-Type": "application/json"},
            )
            response = conn.getresponse()
            data = json.loads(response.read())
            if response.status >= 400:
                raise ValueError(data.get("error", "服务请求失败。"))
            return data
        finally:
            conn.close()

    def state(self) -> dict:
        alive = self.process is not None and self.process.poll() is None
        ready = False
        if alive:
            try:
                ready = self.request("/api/runtime", timeout=1).get("status") == "ok"
            except (OSError, ValueError, http.client.HTTPException):
                pass
        return {
            "supervised": True,
            "connected": ready,
            "restarting": self.restarting,
            "message": "服务已连接，可在网页管理任务。"
            if ready and self.message == "研究服务正在启动。"
            else self.message,
            "settings": self.settings,
            "log_url": "/api/service/log",
        }

    def restart(self, settings: dict | None = None) -> None:
        with self.lock:
            if self.restarting:
                raise ValueError("服务正在重启，请等待状态更新。")
            if settings is not None:
                cleaned = {}
                for key in ("CODEX_CLI", "LATEX_COMPILER"):
                    value = str(settings.get(key, "")).strip()
                    if value:
                        resolved = shutil.which(value)
                        if not resolved:
                            raise ValueError(f"找不到可执行文件：{value}")
                        cleaned[key] = resolved
                self.settings = cleaned
                self.settings_path.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2))
            self.restarting = True
            self.message = "正在停止任务控制器并保存恢复点；保留训练进程。"
            threading.Thread(target=self._restart, daemon=True).start()

    def _restart(self) -> None:
        try:
            if self.process and self.process.poll() is None:
                self.request("/api/runtime/prepare-restart", "POST", timeout=10)
                deadline = time.monotonic() + 45
                while not self.request("/api/runtime")["idle"]:
                    if time.monotonic() >= deadline:
                        self.request("/api/runtime/activate", "POST")
                        raise ValueError("当前控制器尚未退出，保留服务。可查看日志后再次重启。")
                    time.sleep(0.5)
                self.process.terminate()
                self.process.wait(timeout=10)
            self.start()
            self.message = "服务已重新启动；原任务保持暂停，可在网页继续。"
        except (OSError, ValueError, http.client.HTTPException, subprocess.TimeoutExpired) as error:
            self.message = f"重启未完成：{error}。查看服务日志定位原因。"
        finally:
            self.restarting = False

    def close(self) -> None:
        if self.process and self.process.poll() is None:
            try:
                self.request("/api/runtime/prepare-restart", "POST", timeout=10)
            except (OSError, ValueError, http.client.HTTPException):
                pass
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, service: Service, **kwargs):
        self.service = service
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def respond(self, value: dict, status: int = 200) -> None:
        data = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def route(self) -> None:
        path = self.path.split("?", 1)[0].rstrip("/")
        if path == "/api/service" and self.command == "GET":
            self.respond(self.service.state())
            return
        if path == "/api/service/log" and self.command == "GET":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            with self.service.log_path.open("rb") as log:
                shutil.copyfileobj(log, self.wfile)
            return
        if path == "/api/service/restart" and self.command == "POST":
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 16384:
                    raise ValueError("无效的服务操作请求。")
                payload = json.loads(self.rfile.read(size))
                self.service.restart(payload.get("settings"))
                self.respond({"status": "restarting"}, 202)
            except (ValueError, OSError, TypeError, AttributeError) as error:
                self.respond({"error": str(error)}, 400)
            return
        # Static workbench files remain available even when its worker has exited.
        if self.command in {"GET", "HEAD"} and not path.startswith(("/api/", "/auto-")):
            (super().do_GET if self.command == "GET" else super().do_HEAD)()
            return
        if self.service.restarting and self.command not in {"GET", "HEAD"}:
            self.respond({"error": "服务正在重启，请等待重新连接后操作。"}, 503)
            return
        conn = http.client.HTTPConnection("127.0.0.1", self.service.port, timeout=60)
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 <= size <= 32 * 1024 * 1024:
                raise ValueError("请求超过 32 MB。")
            body = self.rfile.read(size) if size else None
            headers = {
                k: v for k, v in self.headers.items() if k.lower() not in {"host", "connection"}
            }
            conn.request(self.command, self.path, body=body, headers=headers)
            response = conn.getresponse()
        except (OSError, ValueError, http.client.HTTPException) as error:
            self.respond({"error": f"研究服务不可用，请返回工作台启动服务。{error}"}, 503)
            conn.close()
            return
        try:
            self.send_response(response.status)
            for key, value in response.getheaders():
                if key.lower() not in {
                    "connection",
                    "transfer-encoding",
                    "server",
                    "date",
                    "cache-control",
                }:
                    self.send_header(key, value)
            self.end_headers()
            if self.command != "HEAD":
                while chunk := response.read(64 * 1024):
                    self.wfile.write(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            conn.close()

    do_GET = route
    do_HEAD = route
    do_POST = route
    do_PUT = route
    do_DELETE = route

    def log_message(self, format, *args):
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="AutoResearch 工作台与浏览器服务恢复入口")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8760)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--data-dir", type=Path)
    args = parser.parse_args()
    workspace = args.workspace.expanduser().resolve()
    if not workspace.is_dir():
        parser.error("workspace 必须是已存在的目录")
    service = Service(workspace, args.data_dir or workspace / "assets/output/workbench")
    server = ThreadingHTTPServer((args.host, args.port), partial(Handler, service=service))
    try:
        service.start()
        print(f"AutoResearch: http://{args.host}:{server.server_port}/", flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        service.close()
        server.server_close()


if __name__ == "__main__":
    main()
