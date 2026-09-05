# Auto Writing

Auto Writing is a local browser workspace that turns experiment descriptions and supporting
documents into an evidence-grounded research manuscript. Each manual action launches one Codex
CLI agent, records the resolved runtime paths, and validates the structured result before it is
accepted.

The frontend is included in `web/index.html`, `web/app.js`, and `web/styles.css`. The Python server
uses only the standard library and serves both the UI and the project API.

## Features

- Create and edit writing projects without losing track of selected input files.
- Generate Introduction, Related Work, Method, Experiments, Conclusion, and Abstract in English.
- Require manual literature research before Introduction and Related Work generation.
- Merge verified research sources into `referenc.json` and a compilation-ready `references.bib`.
- Complete a final 20-25 item reference pass covering Introduction, Related Work, datasets,
  backbones, and comparison methods.
- Upload a LaTeX template ZIP, adapt the manuscript to it, and download either the resulting
  LaTeX package or compiled PDF.
- Keep every writing project isolated under its own runtime directory.

## Workflow

```text
Create project
  -> Introduction research -> Introduction
  -> Related Work plan -> Related Work research -> Related Work
  -> Method -> Experiments -> Conclusion
  -> Abstract
  -> Reference research and citation insertion
  -> LaTeX adaptation and PDF compilation
```

Every step is started manually. The UI disables downstream actions until their prerequisites are
ready. Updating an input file marks affected research, writing, and publication artifacts as stale.

## Requirements

- Python 3.11 or later
- An installed and authenticated Codex CLI
- Network access for literature-research steps
- Optional: `tectonic`, `latexmk`, `xelatex`, or `pdflatex` for PDF compilation

The server can also discover the Tectonic binary bundled with the Codex LaTeX plugin.

## Quick Start

From the repository root on Windows:

```powershell
cd auto_writing
.\run_web.ps1 -Detached
```

Open `http://127.0.0.1:8766/`.

To run in the foreground, omit `-Detached`. On macOS or Linux, or when using a specific Python
interpreter:

```bash
python auto_writing/web/serve.py --host 127.0.0.1 --port 8766
```

Useful environment variables:

| Variable | Purpose |
| --- | --- |
| `CODEX_CLI` | Explicit path to the Codex CLI executable |
| `CODEX_MODEL` | Optional model override for writing and research agents |
| `CODEX_REASONING_EFFORT` | Optional reasoning-effort override |
| `CODEX_TIMEOUT_SECONDS` | Writing timeout in seconds |
| `CODEX_RESEARCH_TIMEOUT_SECONDS` | Literature-research timeout in seconds |
| `LATEX_COMPILER` | Explicit path to a supported LaTeX compiler |
| `LATEX_TIMEOUT_SECONDS` | PDF compilation timeout in seconds |

## Project Data

Runtime data is created locally and is intentionally not tracked by Git:

```text
auto_writing/writing_runs/<project-id>/
  input/                  uploaded experiment and supporting documents
  context/                structured literature research and plans
  manuscript/             generated section JSON, referenc.json, and references.bib
  prompts/                resolved prompts and Codex execution logs
  publication/            template source, LaTeX ZIP, PDF, and compile log
  path_contract.json      exact path contract supplied to agents
  project.json            project state
```

The server binds to localhost by default. Uploaded documents and generated manuscripts remain on
the local machine unless the user explicitly moves or publishes them.

## Source Layout

```text
auto_writing/
  run_web.ps1
  web/
    index.html
    app.js
    styles.css
    serve.py
    prompt_templates.json
    research_prompt_templates.json
    latex_prompt_template.json
    schemas/
    assets/
  tests/
    test_web.py
```

## Tests

Run from the repository root:

```bash
python -m unittest discover -s auto_writing/tests -v
```

The tests cover project lifecycle, dependency gates, prompt path injection, Abstract refinement,
reference migration and citation coverage, safe LaTeX extraction, and publication fallback behavior.
