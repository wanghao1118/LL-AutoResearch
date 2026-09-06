from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from auto_table.engine.manuscript import ManuscriptError, inspect_manuscript, replace_manuscript


SOURCE = r"""\documentclass{article}
\begin{document}
\section{Experiments}
\subsection{Main Results}
\begin{table}[t]
\caption{Original results.}
\label{tab:main}
\begin{tabular}{lc}\toprule Method & Score \\\midrule A & 1 \\\bottomrule\end{tabular}
\end{table}
\end{document}
"""


def _archive(tmp_path: Path, source: str = SOURCE) -> Path:
    archive = tmp_path / "paper.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("paper/main.tex", source)
        bundle.writestr("paper/refs.bib", "")
    return archive


def test_inspect_manuscript_extracts_label_named_table_and_context(tmp_path: Path) -> None:
    manifest = inspect_manuscript(_archive(tmp_path), tmp_path / "inspection")

    assert manifest["main_tex"] == "paper/main.tex"
    assert manifest["table_count"] == 1
    assert manifest["tables"][0]["label"] == "tab:main"
    assert manifest["tables"][0]["section"] == "Experiments"
    assert manifest["tables"][0]["subsection"] == "Main Results"
    assert manifest["tables"][0]["replacement_file"] == "tab-main.tex"
    assert (tmp_path / "inspection/original-tables/tab-main.tex").is_file()


def test_inspect_manuscript_reads_nested_latex_in_caption(tmp_path: Path) -> None:
    source = SOURCE.replace(
        r"\caption{Original results.}",
        r"\caption{Ablation of \(\mathcal{L}_{\mathrm{dep}}\) with \texttt{risk05}.}",
    )
    manifest = inspect_manuscript(_archive(tmp_path, source), tmp_path / "inspection")
    assert manifest["tables"][0]["caption"] == (
        r"Ablation of \(\mathcal{L}_{\mathrm{dep}}\) with \texttt{risk05}."
    )


def test_replace_manuscript_preserves_label_and_packages_patched_source(tmp_path: Path) -> None:
    replacements = tmp_path / "replacements"
    replacements.mkdir()
    replacements.joinpath("tab-main.tex").write_text(
        r"""\begin{table}[t]
\caption{Improved results.}
\label{tab:main}
\centering
\begin{tabular}{lc}\toprule Method & Score \\\midrule \textbf{A} & \textbf{1} \\\bottomrule\end{tabular}
\end{table}
""",
        encoding="utf-8",
    )
    replacements.joinpath("preamble.tex").write_text(
        "\\usepackage[table]{xcolor}\n\\definecolor{AutoTableOurs}{HTML}{EAF2FF}\n",
        encoding="utf-8",
    )

    manifest = replace_manuscript(
        _archive(tmp_path), replacements, tmp_path / "patched", compile_pdf=False
    )

    patched = (tmp_path / "patched/source/paper/main.tex").read_text(encoding="utf-8")
    assert "Improved results" in patched and "Original results" not in patched
    assert patched.index(r"\definecolor{AutoTableOurs}") < patched.index(r"\begin{document}")
    assert manifest["replaced_tables"] == ["tab-main.tex"]
    assert manifest["preamble_file"] == "preamble.tex"
    assert (tmp_path / "patched/replacement-tables/preamble.tex").is_file()
    assert zipfile.is_zipfile(tmp_path / "patched/manuscript-patched.zip")


def test_replace_manuscript_rejects_changed_label(tmp_path: Path) -> None:
    replacements = tmp_path / "replacements"
    replacements.mkdir()
    replacements.joinpath("tab-main.tex").write_text(
        SOURCE[SOURCE.index(r"\begin{table}"):SOURCE.index(r"\end{table}") + len(r"\end{table}")]
        .replace("tab:main", "tab:other"),
        encoding="utf-8",
    )
    with pytest.raises(ManuscriptError, match="must preserve label"):
        replace_manuscript(_archive(tmp_path), replacements, tmp_path / "patched")


def test_inspect_manuscript_rejects_zip_slip(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("../escape.tex", SOURCE)
    with pytest.raises(ManuscriptError, match="unsafe archive member"):
        inspect_manuscript(archive, tmp_path / "inspection")


def test_replace_manuscript_rejects_document_body_in_preamble(tmp_path: Path) -> None:
    replacements = tmp_path / "replacements"
    replacements.mkdir()
    replacements.joinpath("tab-main.tex").write_text(
        SOURCE[SOURCE.index(r"\begin{table}"):SOURCE.index(r"\end{table}") + len(r"\end{table}")],
        encoding="utf-8",
    )
    replacements.joinpath("preamble.tex").write_text(r"\begin{document}", encoding="utf-8")
    with pytest.raises(ManuscriptError, match="configuration commands only"):
        replace_manuscript(_archive(tmp_path), replacements, tmp_path / "patched")
