"""The existing writing steps in dependency order; no second generation implementation."""

import base64
import io
import zipfile
from pathlib import Path

STEPS = (
    ("research", "intro_research"),
    ("section", "intro"),
    ("research", "related_work_plan"),
    ("research", "related_work_research"),
    ("section", "related_work"),
    ("section", "method"),
    ("section", "experiments"),
    ("section", "conclusion"),
    ("section", "abstract"),
    ("research", "reference_insertion"),
    ("publication", "publication"),
)


def next_step(project: dict) -> tuple | None:
    for kind, key in STEPS:
        record = (
            project["publication"]
            if kind == "publication"
            else project["sections" if kind == "section" else "research"][key]
        )
        if record.get("status") != "ready":
            return kind, key, record
    return None


def template_payload(run_dir: Path) -> dict:
    template = run_dir / "input/latex-template.zip"
    if template.is_file():
        data = template.read_bytes()
    else:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr(
                "main.tex",
                r"""\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{graphicx,amsmath,booktabs,natbib}
\usepackage[margin=1in]{geometry}
\title{Research manuscript}
\author{}
\date{}
\begin{document}
\maketitle
\bibliographystyle{plainnat}
\bibliography{references}
\end{document}
""",
            )
        data = buffer.getvalue()
    return {"name": "latex-template.zip", "content_base64": base64.b64encode(data).decode()}
