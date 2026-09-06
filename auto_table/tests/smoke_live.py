"""Opt-in real Codex/TeX smoke. All inputs are explicitly synthetic engineering fixtures."""

import argparse
import base64
import io
import json
import time
import urllib.request
import zipfile
from pathlib import Path


def request(url, path, payload=None):
    req = urllib.request.Request(
        url + "/auto-table/api/" + path,
        data=None if payload is None else json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def encoded(name, data):
    return {"name": name, "content_base64": base64.b64encode(data).decode()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8769")
    parser.add_argument("--mode", choices=["results", "manuscript"], required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--export-only", action="store_true", help="write synthetic inputs for browser upload"
    )
    args = parser.parse_args()
    if args.mode == "results":
        data = b"method,dataset,seed,accuracy,latency_ms\nBaseline,D1,17,80,12\nBaseline,D1,29,82,10\nCandidate,D1,17,84,9\nCandidate,D1,29,86,7\nBaseline,D2,17,70,20\nBaseline,D2,29,72,18\nCandidate,D2,17,74,15\nCandidate,D2,29,76,13\n"
        files = [encoded("synthetic-results.csv", data)]
        requirements = "Engineering smoke only; all data are synthetic. Produce one main_benchmark table with Candidate as focal method, Baseline as reference, D1 and D2 datasets, accuracy (%) higher is better and latency_ms (ms) lower is better. Keep mean and sample SD and all values. Use English caption and description, a restrained continuous focal-row highlight and compact readable headers."
    else:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as bundle:
            bundle.writestr(
                "main.tex",
                r"""\documentclass{article}
\usepackage[margin=1in]{geometry}
\usepackage{booktabs}
\usepackage[table]{xcolor}
\title{Synthetic engineering fixture}
\author{}
\date{}
\begin{document}
\maketitle
This document contains synthetic values for software testing, not research evidence.
\input{sections/results}
\end{document}
""",
            )
            bundle.writestr(
                "sections/results.tex",
                r"""\section{Experiments}
Candidate is compared with Baseline on D1 and D2. Scores are percentages; higher is better. Table~\ref{tab:main} contains means and sample standard deviations over two illustrative runs. No scientific conclusion is made.
\begin{table}[ht]
\centering
\caption{Synthetic scores on D1 and D2.}
\label{tab:main}
\begin{tabular}{lcc}
\toprule
Method & D1 & D2 \\
\midrule
Baseline & $81.0 \pm 1.4$ & $71.0 \pm 1.4$ \\
Candidate & $85.0 \pm 1.4$ & $75.0 \pm 1.4$ \\
\bottomrule
\end{tabular}
\end{table}
\subsection{Ablation}
Table~\ref{tab:ablation} is a single-run synthetic ablation on D1; no uncertainty is available.
\begin{table}[ht]
\centering
\caption{Synthetic ablation on D1.}
\label{tab:ablation}
\begin{tabular}{lc}
\toprule
Variant & Score \\
\midrule
Full & 85.0 \\
w/o module & 82.0 \\
\bottomrule
\end{tabular}
\end{table}
""",
            )
        files = [encoded("synthetic-manuscript.zip", buffer.getvalue())]
        requirements = "Engineering smoke only. Improve both experiment tables from this synthetic manuscript. Preserve every number, uncertainty, label, method/variant/dataset name, caption fact and non-table prose. Candidate is the focal method only in tab:main. Keep the ablation restrained. Use English captions and verify compiled pages."
    if args.export_only:
        args.out.mkdir(parents=True, exist_ok=True)
        for item in files:
            (args.out / item["name"]).write_bytes(base64.b64decode(item["content_base64"]))
        print(str(args.out.resolve()))
        return
    project = request(
        args.url,
        "projects",
        {
            "title": "工程验收 · " + args.mode + " · 合成数据",
            "mode": args.mode,
            "files": files,
            "requirements": requirements,
        },
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(project, ensure_ascii=False, indent=2))
    print("project=" + project["id"], flush=True)
    request(args.url, f"projects/{project['id']}/start", {})
    last = None
    deadline = time.monotonic() + 2400
    while time.monotonic() < deadline:
        project = request(args.url, f"projects/{project['id']}")
        current = (project["step"], project["status"])
        if current != last:
            print(
                json.dumps(
                    {
                        "step": project["step"],
                        "status": project["status"],
                        "message": project["message"],
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
            last = current
        if project["status"] != "running":
            args.out.write_text(json.dumps(project, ensure_ascii=False, indent=2))
            print("final=" + str(args.out), flush=True)
            raise SystemExit(0 if project["status"] == "ready" else 1)
        time.sleep(1)
    raise SystemExit(
        "Smoke timeout; project is preserved on server. Stop or continue it from the UI."
    )


if __name__ == "__main__":
    main()
