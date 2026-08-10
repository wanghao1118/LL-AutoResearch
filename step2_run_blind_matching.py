#!/usr/bin/env python3
"""Run Auto-Bench in a gold-free temporary sandbox for every blind case.

The worker sandbox contains exactly three logical inputs: the ``autobench``
package, the public benchmark catalog, and one anonymized Introduction+Method
JSON file.  Paper source, paper identity, experiment sections, and hidden labels
are not copied into the sandbox.  Outputs are copied back only after the worker
process exits.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases-dir", default="assets/input/blind_cases")
    parser.add_argument("--case-pattern", default="case_*.json")
    parser.add_argument("--catalog", default="configs/benchmark_catalog.json")
    parser.add_argument("--output-dir", default="assets/output/blind_runs")
    parser.add_argument("--online", action="store_true")
    return parser.parse_args()


def run_case(case_path: Path, catalog_path: Path, output_root: Path, online: bool) -> dict:
    case_id = case_path.stem
    with tempfile.TemporaryDirectory(prefix=f"auto-bench-{case_id}-") as temp_name:
        sandbox = Path(temp_name)
        shutil.copytree(ROOT / "autobench", sandbox / "autobench")
        shutil.copy2(catalog_path, sandbox / "catalog.json")
        shutil.copy2(case_path, sandbox / "input.json")
        command = [
            sys.executable,
            "-m",
            "autobench",
            "match",
            "--input",
            "input.json",
            "--catalog",
            "catalog.json",
            "--output",
            "output",
        ]
        if online:
            command.append("--online")
        env = {
            "PATH": os.environ.get("PATH", ""),
            "LANG": os.environ.get("LANG", "C.UTF-8"),
            "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
            "PYTHONPATH": str(sandbox),
            "HOME": str(sandbox / "home"),
        }
        (sandbox / "home").mkdir()
        completed = subprocess.run(
            command,
            cwd=sandbox,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"blind worker failed for {case_id}: exit={completed.returncode}\n"
                f"stdout={completed.stdout}\nstderr={completed.stderr}"
            )
        destination = output_root / case_id
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(sandbox / "output", destination)
        inventory = ["autobench/", "catalog.json", "input.json", "home/", "output/"]
        return {
            "case_id": case_id,
            "command": command,
            "worker_exit_status": completed.returncode,
            "worker_stdout": completed.stdout.strip(),
            "worker_stderr": completed.stderr.strip(),
            "sandbox_inventory": inventory,
            "hidden_labels_present_in_sandbox": False,
            "output_dir": destination.relative_to(ROOT).as_posix(),
        }


def main() -> int:
    args = parse_args()
    cases_dir = ROOT / args.cases_dir
    catalog_path = ROOT / args.catalog
    output_root = ROOT / args.output_dir
    output_root.mkdir(parents=True, exist_ok=True)
    case_paths = sorted(cases_dir.glob(args.case_pattern))
    if not case_paths:
        raise ValueError(f"no blind cases found in {cases_dir}")
    runs = [run_case(path, catalog_path, output_root, args.online) for path in case_paths]
    manifest = {
        "schema_version": "1.0",
        "runner": "gold_free_temporary_sandbox",
        "online_search": args.online,
        "cases": runs,
    }
    manifest_path = output_root / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for run in runs:
        print(
            json.dumps(
                {
                    "case_id": run["case_id"],
                    "exit_status": run["worker_exit_status"],
                    "hidden_labels_present_in_sandbox": run["hidden_labels_present_in_sandbox"],
                },
                ensure_ascii=False,
            )
        )
    print(json.dumps({"manifest": manifest_path.relative_to(ROOT).as_posix()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
