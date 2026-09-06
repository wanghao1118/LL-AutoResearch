"""Opt-in isolated pipeline smoke: fixture research, real TeX and AutoTable Codex calls.

Run with PYTHONPATH=src:auto_search .venv/bin/python3 -m workbench.tests.smoke_pipeline_live
No GPU research is launched. Keep --serve open for browser inspection, then Ctrl-C.
"""

import argparse
import json
import threading
import time
from pathlib import Path

from pytest import MonkeyPatch

from auto_design.tests.test_application import FullRunner
from workbench.server import Workbench, writing
from workbench.tests.test_pipeline import seed_search, seed_writing


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8769)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--resume", type=Path, help="Resume a preserved smoke workspace")
    args = parser.parse_args()
    root = (
        args.resume
        or (Path.cwd() / "assets/output/pipeline-table-smoke" / time.strftime("%Y%m%d-%H%M%S"))
    ).resolve()
    root.mkdir(parents=True, exist_ok=True)
    monkeypatch = MonkeyPatch()
    real_compile = writing.compile_latex
    seed_search(monkeypatch)
    writing_calls = []
    seed_writing(monkeypatch, writing_calls, with_table=True)
    monkeypatch.setattr(writing, "compile_latex", real_compile)
    app = Workbench(root, root / "assets/output/workbench", port=args.port)
    app.design.runner = FullRunner()
    app.start_modules()
    thread = threading.Thread(target=app.server.serve_forever, daemon=True)
    thread.start()
    try:
        if args.resume:
            flow = app.pipeline.list()[0]
            app.pipeline.action(flow["id"], "resume", {})
        else:
            flow = app.pipeline.create(
                {
                    "direction": "ENGINEERING FIXTURE ONLY - four module integration",
                    "paper_count": 2,
                }
            )
        print(
            json.dumps(
                {
                    "url": f"http://127.0.0.1:{args.port}",
                    "flow_id": flow["id"],
                    "workspace": str(root),
                }
            ),
            flush=True,
        )
        deadline = time.monotonic() + 900
        state = None
        while time.monotonic() < deadline:
            current = app.pipeline.get(flow["id"])
            observed = (current["stage"], current["status"], current["message"])
            if observed != state:
                print(json.dumps(observed, ensure_ascii=False), flush=True)
                state = observed
            if current["status"] in {"blocked", "completed"}:
                summary = {
                    "engineering_only": True,
                    "research_and_writing": "explicit fixture responses",
                    "table_model": "real Codex CLI",
                    "pdf_compilation": "real TeX",
                    "flow": current,
                    "writing_calls": writing_calls,
                }
                if current.get("table_id"):
                    summary["table"] = app.table.load(current["table_id"])
                (root / "summary.json").write_text(
                    json.dumps(summary, ensure_ascii=False, indent=2)
                )
                print(str(root / "summary.json"), flush=True)
                if current["status"] != "completed":
                    raise RuntimeError(current["message"])
                break
            time.sleep(0.5)
        else:
            raise TimeoutError("Live smoke exceeded 900 seconds; outputs are preserved.")
        if args.serve:
            thread.join()
    finally:
        app.server.shutdown()
        app.close()
        monkeypatch.undo()


if __name__ == "__main__":
    main()
