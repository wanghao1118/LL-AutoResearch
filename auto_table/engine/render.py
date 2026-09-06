from __future__ import annotations

import html
import re
from collections import Counter
from typing import Any

from .planner import emphasis_map


def latex_escape(value: Any) -> str:
    replacements = {
        "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
        "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
        "~": r"\textasciitilde{}", "^": r"\textasciicircum{}", "±": r"$\pm$",
    }
    return "".join(replacements.get(character, character) for character in str(value))


def _metric_header(meta: dict[str, Any], label: str | None = None) -> str:
    arrow = (r"$\uparrow$" if meta["direction"] == "max" else r"$\downarrow$") if meta.get("show_direction", True) else ""
    unit = f" ({latex_escape(meta['unit'])})" if meta.get("unit") else ""
    return f"{latex_escape(label or meta['label'])}{unit}{f' {arrow}' if arrow else ''}"


def _formatted_cell(cell: dict[str, Any] | None, precision: int, missing_marker: str = "--") -> str:
    if cell is None:
        return latex_escape(missing_marker)
    mean = f"{cell['mean']:.{precision}f}"
    return mean if cell["sd"] is None else f"{mean} $\\pm$ {cell['sd']:.{precision}f}"


def _auxiliary_text(cell: dict[str, Any] | None) -> str | None:
    if cell is None or not cell.get("auxiliary"):
        return None
    auxiliary = cell["auxiliary"]
    value = auxiliary["value"]
    precision = auxiliary["precision"]
    suffix = "%" if auxiliary["kind"] == "relative_percent" else ""
    return f"{value:+.{precision}f}{suffix}"


def _color(value: Any, default: str) -> str:
    text = str(value or default).lstrip("#").upper()
    return text if re.fullmatch(r"[0-9A-F]{6}", text) else default


def _column_header(spec: dict[str, Any], column: dict[str, Any]) -> str:
    if spec["orientation"] == "methods_rows":
        meta = spec["metrics"][column["metric"]]
        return _metric_header(meta, column.get("label"))
    return latex_escape(column["label"])


def _cell_precision(spec: dict[str, Any], row: dict[str, Any], column: dict[str, Any]) -> int:
    metric = column["metric"] if spec["orientation"] == "methods_rows" else row["metric"]
    return spec["metrics"][metric]["precision"]


def _groups(columns: list[dict[str, Any]], widths: list[int] | None = None) -> list[tuple[str, int]]:
    groups: list[tuple[str, int]] = []
    for index, column in enumerate(columns):
        label = column.get("group_label") or ""
        width = widths[index] if widths else 1
        if groups and groups[-1][0] == label:
            groups[-1] = (label, groups[-1][1] + width)
        else:
            groups.append((label, width))
    return groups


def _auxiliary_columns(spec: dict[str, Any]) -> set[int]:
    """Return logical columns that need a separate, alignment-preserving auxiliary slot."""
    return {
        column_index
        for row in spec["rows"]
        for column_index, cell in enumerate(row["cells"])
        if cell and cell.get("auxiliary")
    }


def _row_separator(spec: dict[str, Any], row_index: int) -> bool:
    if row_index == 0:
        return False
    current, previous = spec["rows"][row_index], spec["rows"][row_index - 1]
    separate_groups = bool(spec.get("style", {}).get("separate_row_groups", False))
    if separate_groups and current.get("group") != previous.get("group") and (current.get("group") or previous.get("group")):
        return True
    return any(
        field.get("separator") and current["identity"].get(field["key"]) != previous["identity"].get(field["key"])
        for field in spec["identity_columns"]
    )


def _banded_groups(spec: dict[str, Any]) -> set[str]:
    """Return groups worth showing as a parallel visual classification."""
    sizes = Counter(str(row["group"]) for row in spec["rows"] if row.get("group"))
    eligible = {group for group, size in sizes.items() if size >= 2}
    return eligible if len(eligible) >= 2 else set()


def _identity_values(spec: dict[str, Any], row_index: int) -> list[str]:
    row = spec["rows"][row_index]
    values = []
    for field in spec["identity_columns"]:
        value = row["identity"].get(field["key"])
        if field.get("suppress_repeat") and row_index > 0 and row.get("group") == spec["rows"][row_index - 1].get("group"):
            previous = spec["rows"][row_index - 1]["identity"].get(field["key"])
            if value == previous:
                value = ""
        values.append(latex_escape(value or ""))
    return values


def render_latex(spec: dict[str, Any], caption: str) -> str:
    columns = spec["columns"]
    identity_columns = spec["identity_columns"]
    wide = len(columns) + len(identity_columns) > 6
    environment = "table*" if wide else "table"
    style = spec.get("style", {})
    font_size = style.get("font_size", "footnotesize" if wide else "small")
    if font_size not in {"scriptsize", "footnotesize", "small", "normalsize"}:
        font_size = "footnotesize" if wide else "small"
    tabcolsep = float(style.get("tabcolsep", 3.5 if wide else 5.0))
    fit_width = bool(style.get("fit_width", False))
    group_bands = style.get("row_group_style") == "band" and spec["orientation"] == "methods_rows"
    banded_groups = _banded_groups(spec)
    separator_style = style.get("row_separator_style", "space")
    if separator_style not in {"space", "rule"}:
        separator_style = "space"
    band_color = _color(style.get("group_band_color"), "EFEFEF")
    highlight_color = _color(style.get("highlight_color"), "E8F1FF")
    highlight_methods = set(style.get("highlight_methods", []))
    missing_marker = str(style.get("missing_marker", "--"))
    auxiliary_columns = _auxiliary_columns(spec)
    physical_widths = [2 if index in auxiliary_columns else 1 for index in range(len(columns))]
    column_spec = "l" * len(identity_columns) + "".join(
        r"r@{\hspace{0.25em}}l" if index in auxiliary_columns else "c"
        for index in range(len(columns))
    )
    lines = [
        f"\\begin{{{environment}}}[t]", "  \\centering",
        f"  \\{font_size}",
        f"  \\setlength{{\\tabcolsep}}{{{tabcolsep:g}pt}}",
        f"  \\caption{{{latex_escape(caption)}}}", f"  \\label{{{latex_escape(spec['label'])}}}",
    ]
    if fit_width:
        lines.append("  \\resizebox{\\textwidth}{!}{%")
    lines.extend([
        "  \\begin{tabular}{" + column_spec + "}",
        "    \\toprule",
    ])
    groups = _groups(columns, physical_widths)
    has_groups = any(label for label, _ in groups)
    if has_groups:
        header = [""] * len(identity_columns) + [
            f"\\multicolumn{{{span}}}{{c}}{{{latex_escape(label)}}}" for label, span in groups
        ]
        lines.append("    " + " & ".join(header) + r" \\")
        start = len(identity_columns) + 1
        rules = []
        for label, span in groups:
            if label:
                rules.append(f"\\cmidrule(lr){{{start}-{start + span - 1}}}")
            start += span
        if rules:
            lines.append("    " + " ".join(rules))
    leaf_header = [latex_escape(field["label"]) for field in identity_columns]
    leaf_header += [
        f"\\multicolumn{{2}}{{c}}{{{_column_header(spec, column)}}}"
        if index in auxiliary_columns else _column_header(spec, column)
        for index, column in enumerate(columns)
    ]
    lines.append("    " + " & ".join(leaf_header) + r" \\")
    lines.append("    \\midrule")

    styles = emphasis_map(spec)
    for row_index, row in enumerate(spec["rows"]):
        group_changed = row_index == 0 or row.get("group") != spec["rows"][row_index - 1].get("group")
        if group_bands and str(row.get("group")) in banded_groups and group_changed:
            span = len(identity_columns) + sum(physical_widths)
            lines.append(
                f"    \\rowcolor[HTML]{{{band_color}}} "
                f"\\multicolumn{{{span}}}{{c}}{{\\textbf{{{latex_escape(row['group'])}}}}} \\\\"
            )
        elif _row_separator(spec, row_index):
            lines.append("    \\midrule" if separator_style == "rule" else "    \\addlinespace")
        values = []
        for column_index, (column, cell) in enumerate(zip(columns, row["cells"])):
            value = _formatted_cell(cell, _cell_precision(spec, row, column), missing_marker)
            cell_style = styles.get((row_index, column_index))
            if cell_style == "bold":
                value = f"\\textbf{{{value}}}"
            elif cell_style == "underline":
                value = f"\\underline{{{value}}}"
            auxiliary = _auxiliary_text(cell)
            values.append(value)
            if column_index in auxiliary_columns:
                values.append(f"{{\\scriptsize ({latex_escape(auxiliary)})}}" if auxiliary else "")
        prefix = f"\\rowcolor[HTML]{{{highlight_color}}} " if row.get("method") in highlight_methods else ""
        lines.append("    " + prefix + " & ".join(_identity_values(spec, row_index) + values) + r" \\")
    lines.extend(["    \\bottomrule", "  \\end{tabular}"])
    if fit_width:
        lines.append("  }")
    lines.append(f"\\end{{{environment}}}")
    return "\n".join(lines) + "\n"


def render_preview_document() -> str:
    return "\n".join([
        r"\documentclass{article}", r"\usepackage[margin=1in]{geometry}",
        r"\usepackage{booktabs}", r"\usepackage{graphicx}", r"\usepackage[table]{xcolor}",
        r"\begin{document}", r"\input{table.tex}",
        r"\end{document}", "",
    ])


def render_html(spec: dict[str, Any], caption: str) -> str:
    styles = emphasis_map(spec)
    groups = _groups(spec["columns"])
    has_groups = any(label for label, _ in groups)
    style = spec.get("style", {})
    group_bands = style.get("row_group_style") == "band" and spec["orientation"] == "methods_rows"
    banded_groups = _banded_groups(spec)
    separator_style = style.get("row_separator_style", "space")
    if separator_style not in {"space", "rule"}:
        separator_style = "space"
    band_color = _color(style.get("group_band_color"), "EFEFEF")
    highlight_color = _color(style.get("highlight_color"), "E8F1FF")
    highlight_methods = set(style.get("highlight_methods", []))
    missing_marker = str(style.get("missing_marker", "--"))
    auxiliary_columns = _auxiliary_columns(spec)
    out = ["<!doctype html>", '<meta charset="utf-8">', "<style>",
           f"table{{border-collapse:collapse;font:14px system-ui;margin:2rem auto}}caption{{font-weight:600;margin:.8rem}}th,td{{padding:.45rem .7rem;text-align:center;border-bottom:1px solid #bbb}}thead tr:first-child th{{border-top:2px solid #222}}tbody tr:last-child td{{border-bottom:2px solid #222}}th:first-child,td:first-child{{text-align:left}}tbody tr.group-start.rule td{{border-top:2px solid #555}}tbody tr.group-start.space td{{padding-top:.8rem}}tbody tr.group-band th{{background:#{band_color};text-align:center;font-weight:700;border-top:1.5px solid #555}}.cell-grid{{display:inline-grid;width:100%;grid-template-columns:minmax(0,1fr) 4.8em;column-gap:.25em;align-items:baseline}}.cell-grid .primary{{text-align:right}}.cell-grid .aux{{font-size:.78em;color:#555;text-align:left}}",
           "</style>", "<table>", f"<caption>{html.escape(caption)}</caption>", "<thead>"]
    if has_groups:
        out.append("<tr>" + "".join(f'<th rowspan="2">{html.escape(f["label"])}</th>' for f in spec["identity_columns"]) + "".join(
            f'<th colspan="{span}">{html.escape(label)}</th>' for label, span in groups) + "</tr>")
        out.append("<tr>" + "".join(f"<th>{_html_column_header(spec, c)}</th>" for c in spec["columns"]) + "</tr>")
    else:
        out.append("<tr>" + "".join(f"<th>{html.escape(f['label'])}</th>" for f in spec["identity_columns"]) +
                   "".join(f"<th>{_html_column_header(spec, c)}</th>" for c in spec["columns"]) + "</tr>")
    out.extend(["</thead>", "<tbody>"])
    for row_index, row in enumerate(spec["rows"]):
        group_changed = row_index == 0 or row.get("group") != spec["rows"][row_index - 1].get("group")
        if group_bands and str(row.get("group")) in banded_groups and group_changed:
            colspan = len(spec["identity_columns"]) + len(spec["columns"])
            out.append(
                f'<tr class="group-band"><th colspan="{colspan}">{html.escape(str(row["group"]))}</th></tr>'
            )
        identity = "".join(f"<td>{html.escape(v)}</td>" for v in _identity_values_html(spec, row_index))
        cells = []
        for column_index, (column, cell) in enumerate(zip(spec["columns"], row["cells"])):
            value = _formatted_cell(cell, _cell_precision(spec, row, column), missing_marker).replace("$\\pm$", "±")
            escaped = html.escape(value)
            cell_style = styles.get((row_index, column_index))
            if cell_style == "bold":
                escaped = f"<strong>{escaped}</strong>"
            elif cell_style == "underline":
                escaped = f"<u>{escaped}</u>"
            auxiliary = _auxiliary_text(cell)
            if column_index in auxiliary_columns:
                auxiliary_html = f"({html.escape(auxiliary)})" if auxiliary else ""
                escaped = (
                    f'<span class="cell-grid"><span class="primary">{escaped}</span>'
                    f'<span class="aux">{auxiliary_html}</span></span>'
                )
            cells.append(f"<td>{escaped}</td>")
        class_name = (
            f' class="group-start {separator_style}"'
            if _row_separator(spec, row_index) and not group_bands else ""
        )
        row_style = f' style="background:#{highlight_color}"' if row.get("method") in highlight_methods else ""
        out.append(f"<tr{class_name}{row_style}>{identity}{''.join(cells)}</tr>")
    out.extend(["</tbody>", "</table>"])
    return "\n".join(out) + "\n"


def _html_column_header(spec: dict[str, Any], column: dict[str, Any]) -> str:
    if spec["orientation"] == "datasets_rows":
        return html.escape(column["label"])
    meta = spec["metrics"][column["metric"]]
    label = column.get("label") or meta["label"]
    unit = f" ({meta['unit']})" if meta.get("unit") else ""
    arrow = ("↑" if meta["direction"] == "max" else "↓") if meta.get("show_direction", True) else ""
    return html.escape(f"{label}{unit}{f' {arrow}' if arrow else ''}")


def _identity_values_html(spec: dict[str, Any], row_index: int) -> list[str]:
    row = spec["rows"][row_index]
    values = []
    for field in spec["identity_columns"]:
        value = row["identity"].get(field["key"]) or ""
        if field.get("suppress_repeat") and row_index > 0 and row.get("group") == spec["rows"][row_index - 1].get("group"):
            previous = spec["rows"][row_index - 1]["identity"].get(field["key"])
            if value == previous:
                value = ""
        values.append(str(value))
    return values
