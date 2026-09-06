from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .ingest import InputError
from .manuscript import ManuscriptError, inspect_manuscript, replace_manuscript
from .pipeline import generate
from .templates import available_templates
from .table_types import available_table_types


def _config(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    with Path(path).open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("config root must be a JSON object")
    return data


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="paper2table",
        description="LaTeX manuscripts or structured results → publication-ready tables",
    )
    sub = root.add_subparsers(dest="command", required=True)
    generate_parser = sub.add_parser("generate", help="run the complete deterministic pipeline")
    generate_parser.add_argument("inputs", nargs="+", help="CSV, TSV, JSON, or JSONL experiment files")
    generate_parser.add_argument("--config", help="JSON design/semantic config")
    generate_parser.add_argument("--template", help="research-backed main-table template ID or JSON path")
    generate_parser.add_argument("--out", default="output/main-table", help="output directory")
    sub.add_parser("list-templates", help="list reusable main-table design templates")
    sub.add_parser("list-types", help="list scientific table roles and their design strategies")
    inspect_parser = sub.add_parser(
        "inspect-manuscript", help="extract a LaTeX ZIP and inventory its table environments"
    )
    inspect_parser.add_argument("archive", help="LaTeX source ZIP")
    inspect_parser.add_argument("--pdf", help="optional compiled PDF used as visual reference")
    inspect_parser.add_argument("--out", default="output/manuscript-inspection")
    inspect_parser.add_argument("--main-file", help="main TeX path relative to archive root")
    replace_parser = sub.add_parser(
        "replace-manuscript", help="replace label-matched tables in a LaTeX ZIP"
    )
    replace_parser.add_argument("archive", help="LaTeX source ZIP")
    replace_parser.add_argument("--replacements", required=True, help="directory of label-named .tex tables")
    replace_parser.add_argument("--pdf", help="optional compiled PDF used as visual reference")
    replace_parser.add_argument("--out", default="output/manuscript-patched")
    replace_parser.add_argument("--compile", action="store_true", help="compile the patched main TeX with latexmk")
    replace_parser.add_argument("--main-file", help="main TeX path relative to archive root")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "generate":
            manifest = generate(args.inputs, args.out, _config(args.config), args.template)
            print(json.dumps(manifest, ensure_ascii=False, indent=2))
            return 0
        if args.command == "list-templates":
            print(json.dumps(available_templates(), ensure_ascii=False, indent=2))
            return 0
        if args.command == "list-types":
            print(json.dumps(available_table_types(), ensure_ascii=False, indent=2))
            return 0
        if args.command == "inspect-manuscript":
            manifest = inspect_manuscript(args.archive, args.out, args.pdf, args.main_file)
            print(json.dumps(manifest, ensure_ascii=False, indent=2))
            return 0
        if args.command == "replace-manuscript":
            manifest = replace_manuscript(
                args.archive, args.replacements, args.out, args.pdf, args.compile, args.main_file
            )
            print(json.dumps(manifest, ensure_ascii=False, indent=2))
            return 0
    except (InputError, ManuscriptError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}")
        return 2
    return 1
