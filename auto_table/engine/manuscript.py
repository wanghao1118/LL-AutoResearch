from __future__ import annotations

import json
import re
import shutil
import subprocess
import zipfile
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any


class ManuscriptError(ValueError):
    """Raised when a manuscript bundle cannot be inspected or patched safely."""


_TABLE_RE = re.compile(
    r"\\begin\{(?P<environment>table\*?)\}(?P<body>.*?)\\end\{(?P=environment)\}",
    re.DOTALL,
)
_LABEL_RE = re.compile(r"\\label\{([^{}]+)\}")
_HEADING_RE = re.compile(r"\\(?P<level>section|subsection|subsubsection)\*?\{(?P<title>[^{}]+)\}")


@dataclass(frozen=True)
class TableBlock:
    index: int
    start: int
    end: int
    source: str
    environment: str
    label: str | None
    caption: str | None
    section: str | None
    subsection: str | None

    @property
    def replacement_name(self) -> str:
        if self.label:
            stem = re.sub(r"[^A-Za-z0-9._-]+", "-", self.label).strip("-")
            return f"{stem}.tex"
        return f"table-{self.index:02d}.tex"


def _dump(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _safe_extract(archive: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            target = (destination / member.filename).resolve()
            if destination.resolve() not in target.parents and target != destination.resolve():
                raise ManuscriptError(f"unsafe archive member: {member.filename}")
            mode = member.external_attr >> 16
            if mode & 0o170000 == 0o120000:
                raise ManuscriptError(f"symbolic links are not allowed in manuscript archives: {member.filename}")
        bundle.extractall(destination)


def _find_main_tex(source_dir: Path, selected: str | None = None) -> Path:
    if selected:
        path = (source_dir / selected).resolve()
        if source_dir.resolve() not in path.parents or not path.is_file():
            raise ManuscriptError(f"main TeX file does not exist inside the archive: {selected}")
        if not re.search(r"\\documentclass(?:\[[^]]*\])?\{", path.read_text(encoding="utf-8")):
            raise ManuscriptError(f"selected file has no documentclass: {selected}")
        return path
    candidates = []
    for path in source_dir.rglob("*.tex"):
        text = path.read_text(encoding="utf-8", errors="replace")
        if re.search(r"^[^%\n]*\\documentclass(?:\[[^]]*\])?\{", text, re.MULTILINE):
            candidates.append(path)
    if not candidates:
        raise ManuscriptError("no main TeX file containing \\documentclass was found")
    if len(candidates) > 1:
        names = ", ".join(str(path.relative_to(source_dir)) for path in candidates)
        raise ManuscriptError(f"multiple main TeX candidates found; select one explicitly: {names}")
    return candidates[0]


def manuscript_sources(source_dir: Path, main_tex: Path) -> list[Path]:
    """Follow literal input/include paths, in document order, relative to the main file."""
    visited: set[Path] = set()
    result: list[Path] = []

    def visit(path: Path) -> None:
        path = path.resolve()
        if path in visited:
            return
        if source_dir.resolve() not in path.parents:
            raise ManuscriptError(f"included TeX is outside the manuscript: {path}")
        visited.add(path)
        result.append(path)
        text = re.sub(r"(?<!\\)%[^\n]*", "", path.read_text(encoding="utf-8"))
        for match in re.finditer(r"\\(?:input|include)\s*\{([^{}]+)\}", text):
            name = match.group(1).strip()
            if "\\" in name:
                raise ManuscriptError(f"dynamic include needs an explicit source bundle: {name}")
            candidate = main_tex.parent / name
            if not candidate.suffix:
                candidate = candidate.with_suffix(".tex")
            if not candidate.is_file():
                raise ManuscriptError(f"included TeX file was not found: {name}")
            visit(candidate)

    visit(main_tex)
    return result


def manuscript_tables(source_dir: Path, main_tex: Path) -> list[tuple[Path, TableBlock]]:
    blocks = []
    names = set()
    for path in manuscript_sources(source_dir, main_tex):
        for table in scan_tables(path.read_text(encoding="utf-8")):
            # Unlabelled tables also have stable, manuscript-wide identifiers.
            table = replace(table, index=len(blocks) + 1)
            if table.replacement_name in names:
                raise ManuscriptError(f"ambiguous table replacement name: {table.replacement_name}")
            names.add(table.replacement_name)
            blocks.append((path, table))
    return blocks


def _context_before(text: str, position: int) -> tuple[str | None, str | None]:
    section = None
    subsection = None
    for match in _HEADING_RE.finditer(text, 0, position):
        level = match.group("level")
        title = match.group("title").strip()
        if level == "section":
            section, subsection = title, None
        elif level in {"subsection", "subsubsection"}:
            subsection = title
    return section, subsection


def _command_argument(source: str, command: str) -> str | None:
    match = re.search(rf"\\{re.escape(command)}(?:\[[^]]*\])?\s*\{{", source)
    if not match:
        return None
    start = match.end()
    depth = 1
    escaped = False
    for position in range(start, len(source)):
        character = source[position]
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return source[start:position]
    return None


def scan_tables(text: str) -> list[TableBlock]:
    tables: list[TableBlock] = []
    active = re.sub(r"(?<!\\)%[^\n]*", lambda m: " " * len(m.group()), text)
    for index, match in enumerate(_TABLE_RE.finditer(active), start=1):
        source = text[match.start():match.end()]
        label_match = _LABEL_RE.search(source)
        caption = _command_argument(source, "caption")
        section, subsection = _context_before(text, match.start())
        tables.append(TableBlock(
            index=index,
            start=match.start(),
            end=match.end(),
            source=source,
            environment=match.group("environment"),
            label=label_match.group(1) if label_match else None,
            caption=" ".join(caption.split()) if caption else None,
            section=section,
            subsection=subsection,
        ))
    return tables


def _validate_pdf(pdf: Path | None) -> str | None:
    if pdf is None:
        return None
    if not pdf.is_file() or pdf.read_bytes()[:4] != b"%PDF":
        raise ManuscriptError(f"optional PDF is not a readable PDF file: {pdf}")
    return str(pdf.resolve())


def inspect_manuscript(
    archive: str | Path,
    output_dir: str | Path,
    reference_pdf: str | Path | None = None,
    main_file: str | None = None,
) -> dict[str, Any]:
    archive_path = Path(archive).resolve()
    if not archive_path.is_file() or not zipfile.is_zipfile(archive_path):
        raise ManuscriptError(f"input is not a readable ZIP archive: {archive_path}")
    output = Path(output_dir).resolve()
    if output.exists():
        raise ManuscriptError(f"output directory already exists: {output}")
    source_dir = output / "source"
    table_dir = output / "original-tables"
    source_dir.mkdir(parents=True)
    table_dir.mkdir()
    _safe_extract(archive_path, source_dir)
    main_tex = _find_main_tex(source_dir, main_file)
    located = manuscript_tables(source_dir, main_tex)
    tables = [table for _, table in located]
    for table in tables:
        (table_dir / table.replacement_name).write_text(table.source + "\n", encoding="utf-8")
    manifest = {
        "schema_version": "paper2table-manuscript-v1",
        "archive": str(archive_path),
        "reference_pdf": _validate_pdf(Path(reference_pdf).resolve() if reference_pdf else None),
        "main_tex": str(main_tex.relative_to(source_dir)),
        "table_count": len(tables),
        "tables": [
            {
                "index": table.index,
                "environment": table.environment,
                "label": table.label,
                "caption": table.caption,
                "section": table.section,
                "subsection": table.subsection,
                "replacement_file": table.replacement_name,
                "source_file": str(path.relative_to(source_dir)),
            }
            for path, table in located
        ],
    }
    _dump(output / "manifest.json", manifest)
    return manifest


def _load_replacements(directory: Path, tables: list[TableBlock]) -> dict[int, str]:
    replacements: dict[int, str] = {}
    known_names = {table.replacement_name: table for table in tables}
    for path in sorted(directory.glob("*.tex")):
        if path.name == "preamble.tex":
            continue
        table = known_names.get(path.name)
        if table is None:
            raise ManuscriptError(f"replacement does not match a discovered table: {path.name}")
        code = path.read_text(encoding="utf-8").strip()
        found = scan_tables(code)
        if len(found) != 1 or found[0].source.strip() != code:
            raise ManuscriptError(f"replacement must contain exactly one complete table environment: {path.name}")
        if table.label and found[0].label != table.label:
            raise ManuscriptError(
                f"replacement {path.name} must preserve label {table.label!r}; found {found[0].label!r}"
            )
        replacements[table.index] = code
    if not replacements:
        raise ManuscriptError(f"no matching .tex replacements found in {directory}")
    return replacements


def _load_preamble(directory: Path) -> str | None:
    path = directory / "preamble.tex"
    if not path.is_file():
        return None
    code = path.read_text(encoding="utf-8").strip()
    forbidden = (r"\documentclass", r"\begin{document}", r"\end{document}")
    if any(token in code for token in forbidden):
        raise ManuscriptError("preamble.tex may contain configuration commands only")
    return code or None


def _zip_tree(source_dir: Path, destination: Path) -> None:
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                bundle.write(path, path.relative_to(source_dir))


def replace_manuscript(
    archive: str | Path,
    replacements_dir: str | Path,
    output_dir: str | Path,
    reference_pdf: str | Path | None = None,
    compile_pdf: bool = False,
    main_file: str | None = None,
) -> dict[str, Any]:
    output = Path(output_dir).resolve()
    manifest = inspect_manuscript(archive, output, reference_pdf, main_file)
    source_dir = output / "source"
    main_tex = source_dir / manifest["main_tex"]
    located = manuscript_tables(source_dir, main_tex)
    tables = [table for _, table in located]
    replacement_dir = Path(replacements_dir).resolve()
    replacements = _load_replacements(replacement_dir, tables)
    preamble = _load_preamble(replacement_dir)
    for path in dict.fromkeys(path for path, _ in located):
        text = path.read_text(encoding="utf-8")
        for source, table in reversed(located):
            if source == path and table.index in replacements:
                text = text[:table.start] + replacements[table.index] + text[table.end:]
        path.write_text(text, encoding="utf-8")
    text = main_tex.read_text(encoding="utf-8")
    if preamble:
        marker = r"\begin{document}"
        if marker not in text:
            raise ManuscriptError("main TeX file has no \\begin{document} marker")
        text = text.replace(marker, preamble + "\n\n" + marker, 1)
    main_tex.write_text(text, encoding="utf-8")

    patched_tables = [table for _, table in manuscript_tables(source_dir, main_tex)]
    if len(patched_tables) != len(tables):
        raise ManuscriptError("table count changed unexpectedly after replacement")
    replacement_out = output / "replacement-tables"
    replacement_out.mkdir()
    for table in patched_tables:
        if table.index in replacements:
            (replacement_out / table.replacement_name).write_text(table.source + "\n", encoding="utf-8")
    if preamble:
        (replacement_out / "preamble.tex").write_text(preamble + "\n", encoding="utf-8")

    archive_out = output / "manuscript-patched.zip"
    _zip_tree(source_dir, archive_out)
    manifest["replaced_tables"] = [
        table.replacement_name for table in tables if table.index in replacements
    ]
    manifest["preamble_file"] = "preamble.tex" if preamble else None
    manifest["patched_archive"] = str(archive_out)
    manifest["compiled_pdf"] = None

    if compile_pdf:
        latexmk = shutil.which("latexmk")
        if not latexmk:
            raise ManuscriptError("latexmk is required for --compile but was not found")
        command = [
            latexmk, "-pdf", "-interaction=nonstopmode", "-halt-on-error", main_tex.name
        ]
        result = subprocess.run(
            command,
            cwd=main_tex.parent,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        (output / "latexmk.log").write_text(result.stdout, encoding="utf-8")
        if result.returncode != 0:
            raise ManuscriptError(f"LaTeX compilation failed; see {output / 'latexmk.log'}")
        built = main_tex.with_suffix(".pdf")
        if not built.is_file() or built.read_bytes()[:4] != b"%PDF":
            raise ManuscriptError("LaTeX reported success but did not produce a valid PDF")
        compiled = output / "manuscript-patched.pdf"
        shutil.copy2(built, compiled)
        manifest["compiled_pdf"] = str(compiled)

    _dump(output / "manifest.json", manifest)
    return manifest
