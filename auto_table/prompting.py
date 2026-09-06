"""Versioned system instructions replace the installed Skill dependency."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def instructions() -> str:
    return (ROOT / "prompts/system.md").read_text(encoding="utf-8")


def design_prompt(project: dict, directory: Path, inspection: dict) -> str:
    references = ["table-types.md", "design-grammar.md", "input-contract.md", "template-schema.md"]
    rules = "\n\n".join(
        (ROOT / "references" / name).read_text(encoding="utf-8") for name in references
    )
    mode = project["mode"]
    request = (
        "Return table plans in tables: each has a unique simple id, a title, and config_json containing "
        "the complete deterministic engine JSON config. Use the input contract. Declare metric columns, "
        "directions, scientific table_type, focal_methods for main tables, names copied verbatim, title, "
        "caption and evidence-specific description. Keep all evidence represented across the returned "
        "tables. Respect supplied configuration overrides. Return replacements=[] and preamble=''."
        if mode == "results"
        else "Read the full manuscript source and original tables in inspection/source and inspection/original-tables. "
        "Select experiment tables from scientific context, not file order. Return replacements with exact "
        "manifest filename and one complete table/table* environment per selected table, preserving label. "
        "Return optional preamble (packages, colors, reusable commands only). Return tables=[]. "
        "Do not alter non-table prose or invent experiments. Preserve every original number, uncertainty, "
        "unit, missing marker, method/dataset/metric name, and caption fact. "
        "The build uses the original document class and bibliography. Avoid duplicate package option conflicts."
    )
    context = {
        "mode": mode,
        "inputs": project["inputs"],
        "requirements": project["requirements"],
        "config": project.get("config", {}),
        "inspection": inspection,
        "previous_feedback": project.get("feedback", ""),
    }
    return (
        instructions()
        + "\n\n"
        + rules
        + "\n\nTASK\n"
        + request
        + "\nTask directory: "
        + str(directory)
        + "\nReference PDFs and original input files are at "
        "the absolute paths listed below. Read them completely; use PDF tools when useful. "
        "Return only the schema object. rationale must explain the scientific role and layout choice "
        "in Chinese. Do not write files or run experiments.\n"
        + json.dumps(context, ensure_ascii=False, indent=2)
    )


def review_prompt(project: dict, directory: Path, outputs: list[dict]) -> str:
    return (
        instructions() + "\n\nINDEPENDENT OUTPUT REVIEW\n"
        "Inspect ALL rendered PNG pages listed below using image viewing tools. Read the original "
        "inputs and the generated LaTeX and table-specs. Compare every visible value, uncertainty, "
        "identity, metric direction, and missing marker with the source. Verify legibility, alignment, "
        "no clipping/overlap, useful headers, valid ranking scope, and continuous full-row highlight. "
        "For manuscripts, ensure only selected tables/preamble changed and labels/caption facts survive. "
        "Compilation success alone is not sufficient. If a required page cannot be viewed, return passed=false. "
        "Return passed=true only if both evidence preservation and visual quality pass. "
        "Return concise Chinese findings and list every inspected image path in inspected_pages. "
        "Do not edit files or run experiments.\nTask directory: "
        + str(directory)
        + "\n"
        + json.dumps({"project": project, "outputs": outputs}, ensure_ascii=False, indent=2)
    )
