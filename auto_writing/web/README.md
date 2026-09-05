# Auto Writing Web

Run the local workspace from `auto_writing`:

```powershell
.\run_web.ps1
```

To keep the server running independently of the current terminal:

```powershell
.\run_web.ps1 -Detached
```

Detached-server logs are written to `tmp/web_server.stdout.log` and `tmp/web_server.stderr.log`.

The default URL is `http://127.0.0.1:8766`.

Each writing project is stored below `writing_runs/<project-id>/` with this layout:

```text
input/                       uploaded experiment description
input/supporting_materials/  optional papers, tables, and notes
context/                     literature research and subsection-plan JSON files
manuscript/                  six generated section JSON files
manuscript/referenc.json     merged/final verified reference artifact
manuscript/references.bib    compilation-ready BibTeX database
prompts/                     resolved research and writing prompts with runtime paths
publication/template.zip     uploaded LaTeX template
publication/source/          adapted LaTeX source tree
publication/build/           compiler working files
publication/manuscript-latex.zip  downloadable LaTeX package
publication/manuscript.pdf   compiled PDF when compilation succeeds
publication/compile.log      complete compiler output
path_contract.json           path-to-content contract shown in the UI
project.json                 project and generation state
```

Prompt templates in `prompt_templates.json` contain no machine-specific path. The server injects the active project's absolute paths into `PATH_CONTEXT_JSON` immediately before launching a Codex CLI agent.

Introduction and Related Work use manual gates:

1. Introduction: run literature research, wait for completion, then generate the section.
2. Related Work: plan exactly three subsections, run literature research for those topics, then generate the section.

Each click starts only the selected step. Research sessions use live web search and save structured evidence before any manuscript generation is allowed.

The Introduction and Related Work research tasks also merge their verified sources into `manuscript/referenc.json` as a draft bibliography. After the five body sections and Abstract are ready, use the **参考文献** tab to start the final reference task manually. It retains relevant verified sources, researches missing coverage, inserts LaTeX citations into both opening Introduction paragraphs, every Related Work subsection, and every named dataset, backbone, and baseline in Experiments, then writes 20–25 cited records plus `references.bib`.

Abstract is the sixth writing section. Its generation button is enabled only after Introduction, Related Work, Method, Experiments, and Conclusion are all ready. The final workflow order is Abstract, Reference, then LaTeX publication. If an Abstract draft misses its hard format, word-count, or sentence-count contract, the server automatically runs one constrained refinement pass before reporting a failure.

## Project files

Use the pencil button beside the project title to rename a writing, replace its experiment description, remove existing supporting files, or add new supporting files. A title-only change preserves generated sections. Replacing, adding, or removing an input file marks all research, manuscript sections, and publication artifacts as stale so they cannot be mistaken for output based on the latest evidence.

## LaTeX publication

The **排版发布** tab becomes available after all six manuscript sections and the final reference task are ready. Upload a ZIP containing a LaTeX template with a primary TeX file. The publication task safely extracts the archive, identifies the primary document, asks a dedicated Codex agent to adapt the Abstract, five body sections, citations, and bibliography to the template, packages the resulting source, and compiles a PDF.

Compiler discovery checks `LATEX_COMPILER`, commands on `PATH`, a local `tools/tectonic/tectonic.exe`, and the Tectonic binary bundled with the local Codex LaTeX plugin. Supported commands are `latexmk`, `tectonic`, `xelatex`, and `pdflatex`. Set `LATEX_TIMEOUT_SECONDS` to change the default five-minute compiler timeout. If compilation fails, the adapted LaTeX ZIP remains downloadable and the UI shows the path to `publication/compile.log`.
