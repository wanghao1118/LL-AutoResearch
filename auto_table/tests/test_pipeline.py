import json
from pathlib import Path

import pytest

from auto_table.engine.ingest import load_inputs
from auto_table.engine.pipeline import generate
from auto_table.engine.templates import available_templates
from auto_table.engine.table_types import available_table_types


def test_wide_csv_end_to_end(tmp_path: Path) -> None:
    source = tmp_path / "results.csv"
    source.write_text(
        "group,method,dataset,seed,accuracy,latency_ms\n"
        "Base,A,D1,1,80,12\n"
        "Base,A,D1,2,82,10\n"
        "Ours,B,D1,1,84,9\n"
        "Ours,B,D1,2,86,7\n",
        encoding="utf-8",
    )
    config = {
        "input": {"metric_columns": ["accuracy", "latency_ms"]},
        "metrics": {
            "accuracy": {"direction": "max", "precision": 1},
            "latency_ms": {"direction": "min", "precision": 1},
        },
    }
    manifest = generate([source], tmp_path / "out", config)
    spec = json.loads((tmp_path / "out/table-spec.json").read_text())
    latex = (tmp_path / "out/table.tex").read_text()
    caption = (tmp_path / "out/caption.txt").read_text()
    description = (tmp_path / "out/description.txt").read_text()

    assert manifest["observation_count"] == 8
    assert manifest["displayed_cell_count"] == 4
    assert spec["rows"][1]["cells"][0]["mean"] == 85
    assert spec["rows"][1]["cells"][1]["mean"] == 8
    assert r"\textbf{85.0 $\pm$ 1.4}" in latex
    assert r"\textbf{8.0 $\pm$ 1.4}" in latex
    assert caption == "Main results.\n"
    assert "compares 2 displayed systems" in description
    assert "Accuracy" in description and "Latency Ms" in description


def test_authored_description_is_preserved_as_a_user_facing_deliverable(tmp_path: Path) -> None:
    source = tmp_path / "results.csv"
    source.write_text("method,dataset,score\nA,D,1\n", encoding="utf-8")
    authored = (
        "This table reports system A on dataset D using the registered score. "
        "Its purpose is to document the primary quantitative comparison."
    )
    manifest = generate([source], tmp_path / "out", {
        "input": {"metric_columns": ["score"]},
        "metrics": {"score": {"direction": "max"}},
        "description": authored,
    })

    assert (tmp_path / "out/description.txt").read_text(encoding="utf-8") == authored + "\n"
    assert json.loads((tmp_path / "out/table-spec.json").read_text())["description"] == authored
    assert manifest["deliverables"] == [
        "caption.txt", "description.txt", "table.tex", "table.html"
    ]


def test_nested_json(tmp_path: Path) -> None:
    source = tmp_path / "nested.json"
    source.write_text(json.dumps({
        "A": {"D1": {"score": [1, 3]}},
        "B": {"D1": {"score": [2, 4]}},
    }))
    observations = load_inputs([source])
    assert len(observations) == 4
    assert observations[1].run == "2"
    assert observations[1].method_source_field == "json_object_key"


def test_method_name_is_verbatim_from_selected_input_field(tmp_path: Path) -> None:
    source = tmp_path / "official.csv"
    source.write_text(
        "model,official_method_name,dataset,score\n"
        "backbone,ThAInker++ (Ours),D,91.2\n",
        encoding="utf-8",
    )
    manifest = generate([source], tmp_path / "out", {
        "input": {"method_field": "official_method_name", "metric_columns": ["score"]},
        "metrics": {"score": {"direction": "max"}},
    })
    spec = json.loads((tmp_path / "out/table-spec.json").read_text(encoding="utf-8"))

    assert spec["methods"] == ["ThAInker++ (Ours)"]
    assert spec["rows"][0]["method"] == "ThAInker++ (Ours)"
    assert manifest["method_identity_policy"] == "verbatim_from_input"
    assert manifest["method_identity"] == [{
        "method": "ThAInker++ (Ours)",
        "input_fields": ["official_method_name"],
        "sources": [str(source)],
    }]


def test_group_metadata_does_not_force_a_visible_separator(tmp_path: Path) -> None:
    source = tmp_path / "groups.csv"
    source.write_text(
        "group,method,dataset,score\n"
        "Baseline,A,D,1\n"
        "Proposed,B,D,2\n",
        encoding="utf-8",
    )
    generate([source], tmp_path / "flat", {
        "input": {"metric_columns": ["score"]},
        "metrics": {"score": {"direction": "max"}},
    })
    flat_latex = (tmp_path / "flat/table.tex").read_text(encoding="utf-8")
    flat_html = (tmp_path / "flat/table.html").read_text(encoding="utf-8")
    assert flat_latex.count(r"\midrule") == 1
    assert r"\addlinespace" not in flat_latex
    assert 'class="group-start' not in flat_html

    generate([source], tmp_path / "explicit", {
        "input": {"metric_columns": ["score"]},
        "metrics": {"score": {"direction": "max"}},
        "style": {"separate_row_groups": True, "row_separator_style": "rule"},
    })
    explicit_latex = (tmp_path / "explicit/table.tex").read_text(encoding="utf-8")
    assert explicit_latex.count(r"\midrule") == 2


def test_reported_summary_preserves_sd_n_and_source_without_inventing_runs(tmp_path: Path) -> None:
    source = tmp_path / "summary.csv"
    source.write_text(
        "method,dataset,metric,mean,sd,n\n"
        "A,D,accuracy,87.4,0.3,3\n"
        "B,D,accuracy,88.1,0.2,3\n",
        encoding="utf-8",
    )
    manifest = generate([source], tmp_path / "out", {
        "metrics": {"accuracy": {"direction": "max", "precision": 1}},
    })
    spec = json.loads((tmp_path / "out/table-spec.json").read_text())
    cell = spec["rows"][0]["cells"][0]

    assert manifest["observation_count"] == 0
    assert manifest["reported_summary_count"] == 2
    assert manifest["represented_run_count"] == 6
    assert cell["mean"] == pytest.approx(87.4)
    assert cell["sd"] == pytest.approx(0.3)
    assert cell["n"] == 3
    assert cell["values"] == []
    assert cell["run_ids"] == []
    assert cell["aggregation_source"] == "reported_summary"


def test_reported_summary_cannot_mix_with_raw_observation(tmp_path: Path) -> None:
    source = tmp_path / "mixed.csv"
    source.write_text(
        "method,dataset,metric,value,mean,sd,n\n"
        "A,D,score,1,,,\n"
        "A,D,score,,2,0.1,3\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="reported summary cannot be mixed"):
        generate([source], tmp_path / "out", {"metrics": {"score": {"direction": "max"}}})


def test_custom_missing_marker_renders_in_latex_and_html(tmp_path: Path) -> None:
    source = tmp_path / "missing.csv"
    source.write_text(
        "method,dataset,metric,value\nA,D1,score,1\nB,D2,score,2\n",
        encoding="utf-8",
    )
    generate([source], tmp_path / "out", {
        "title": "Coverage results",
        "metrics": {"score": {"direction": "max"}},
        "style": {"missing_marker": "N/A"},
        "context_notes": ["N/A is not applicable."],
    })
    assert "N/A" in (tmp_path / "out/table.tex").read_text()
    assert "N/A" in (tmp_path / "out/table.html").read_text()
    assert (tmp_path / "out/caption.txt").read_text() == "Coverage results.\n"


def test_context_notes_are_internal_and_never_render_below_table(tmp_path: Path) -> None:
    source = tmp_path / "results.csv"
    source.write_text("method,dataset,score\nA,D,1\n", encoding="utf-8")
    note = "This belongs in the paper body, not below the table."
    manifest = generate([source], tmp_path / "out", {
        "title": "Concise result",
        "input": {"metric_columns": ["score"]},
        "metrics": {"score": {"direction": "max"}},
        "context_notes": [note],
    })
    latex = (tmp_path / "out/table.tex").read_text(encoding="utf-8")
    html = (tmp_path / "out/table.html").read_text(encoding="utf-8")

    assert manifest["context_notes"] == [note]
    assert note not in latex and note not in html
    assert r"\parbox" not in latex
    assert (tmp_path / "out/caption.txt").read_text() == "Concise result.\n"


def test_descriptive_metric_can_hide_direction_arrow(tmp_path: Path) -> None:
    source = tmp_path / "descriptive.csv"
    source.write_text("method,dataset,metric,value\nSide effect,D,rate,41.6\n", encoding="utf-8")
    generate([source], tmp_path / "out", {
        "metrics": {"rate": {"direction": "max", "show_direction": False}},
        "emphasis": {},
    })
    latex = (tmp_path / "out/table.tex").read_text()
    html = (tmp_path / "out/table.html").read_text()
    assert r"Rate $\uparrow$" not in latex
    assert "Rate ↑" not in html


@pytest.mark.parametrize(
    ("stem", "record_count"),
    [
        ("core_evidence", 33),
        ("external_mll23", 18),
        ("ablations", 30),
        ("c2_diagnostic", 4),
        ("failure_taxonomy", 7),
    ],
)
def test_exp40_reported_tables_preserve_summary_lineage(
    tmp_path: Path, stem: str, record_count: int
) -> None:
    root = Path(__file__).parents[1]
    config = json.loads((root / f"examples/exp40/{stem}.json").read_text(encoding="utf-8"))
    manifest = generate(
        [root / f"examples/exp40/{stem}.csv"], tmp_path / stem, config
    )
    spec = json.loads((tmp_path / stem / "table-spec.json").read_text(encoding="utf-8"))

    assert manifest["verification"] == {"valid": True, "errors": []}
    assert manifest["warnings"] == []
    assert manifest["omitted_columns"] == []
    assert manifest["observation_count"] == 0
    assert manifest["reported_summary_count"] == record_count
    cells = [cell for row in spec["rows"] for cell in row["cells"] if cell is not None]
    assert len(cells) == record_count
    assert all(cell["aggregation_source"] == "reported_summary" for cell in cells)
    assert all(cell["values"] == [] and cell["run_ids"] == [] for cell in cells)

    if stem == "c2_diagnostic":
        assert spec["emphasis"] == {}
        assert spec["caption"] == "Matched-coverage diagnostic for C2."
        assert any("not evaluable" in note for note in spec["context_notes"])
        assert any(row["identity"]["evidence_status"].startswith("INCOMPLETE") for row in spec["rows"])
    if stem == "failure_taxonomy":
        assert spec["emphasis"] == {}
        assert all(not metric["show_direction"] for metric in spec["metrics"].values())


def test_column_budget_records_omissions(tmp_path: Path) -> None:
    source = tmp_path / "results.csv"
    source.write_text("method,dataset,a,b,c\nM,D,1,2,3\n", encoding="utf-8")
    config = {
        "metrics": {"a": {"priority": 3}, "b": {"priority": 1}, "c": {"priority": 2}},
        "selection": {"max_columns": 2},
    }
    manifest = generate([source], tmp_path / "out", config)
    spec = json.loads((tmp_path / "out/table-spec.json").read_text())
    assert [column["metric"] for column in spec["columns"]] == ["b", "c"]
    assert manifest["omitted_columns"] == [{"dataset": "D", "setting": None, "metric": "a"}]


def test_selection_filters_instead_of_only_reordering(tmp_path: Path) -> None:
    source = tmp_path / "results.csv"
    source.write_text("method,dataset,a,b\nA,D1,1,2\nB,D2,3,4\n", encoding="utf-8")
    generate([source], tmp_path / "out", {
        "selection": {"methods": ["B"], "datasets": ["D2"], "metrics": ["b"]}
    })
    spec = json.loads((tmp_path / "out/table-spec.json").read_text())
    assert spec["methods"] == ["B"]
    assert spec["columns"] == [{
        "dataset": "D2", "setting": None, "metric": "b", "group_label": None, "label": "B"
    }]
    assert spec["rows"][0]["cells"][0]["mean"] == 4


def test_score_is_a_valid_wide_metric(tmp_path: Path) -> None:
    source = tmp_path / "results.csv"
    source.write_text("method,dataset,score\nA,D,2\n", encoding="utf-8")
    observations = load_inputs([source])
    assert observations[0].metric == "score"


def test_duplicate_run_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "results.csv"
    source.write_text("method,dataset,seed,score\nA,D,1,2\nA,D,1,3\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate run IDs"):
        generate([source], tmp_path / "out", {"input": {"metric_columns": ["score"]}})


def test_hierarchical_method_fields_are_separate_columns(tmp_path: Path) -> None:
    source = tmp_path / "results.csv"
    source.write_text(
        "model,method,trainable_params,dataset,seed,accuracy\n"
        "RoBERTa,Full FT,125M,MNLI,1,87\n"
        "RoBERTa,LoRA,0.3M,MNLI,1,88\n",
        encoding="utf-8",
    )
    generate([source], tmp_path / "out", {
        "template": "hierarchical-method-budget",
        "input": {"metric_columns": ["accuracy"]},
        "metrics": {"accuracy": {"direction": "max"}},
    })
    spec = json.loads((tmp_path / "out/table-spec.json").read_text())
    assert [field["key"] for field in spec["identity_columns"]] == ["model", "method", "trainable_params"]
    assert spec["rows"][1]["identity"] == {
        "model": "RoBERTa", "method": "LoRA", "trainable_params": "0.3M"
    }


def test_transposed_benchmark_ranks_across_method_columns(tmp_path: Path) -> None:
    source = tmp_path / "results.csv"
    source.write_text(
        "method,pretrain_data,dataset,accuracy\n"
        "ViT,JFT,ImageNet,88.5\n"
        "BiT,JFT,ImageNet,87.5\n"
        "ViT,JFT,CIFAR-10,99.5\n"
        "BiT,JFT,CIFAR-10,99.3\n",
        encoding="utf-8",
    )
    generate([source], tmp_path / "out", {
        "template": "transposed-benchmark",
        "input": {"metric_columns": ["accuracy"]},
        "metrics": {"accuracy": {"direction": "max", "precision": 1}},
    })
    spec = json.loads((tmp_path / "out/table-spec.json").read_text())
    latex = (tmp_path / "out/table.tex").read_text()
    assert spec["orientation"] == "datasets_rows"
    assert [column["method"] for column in spec["columns"]] == ["ViT", "BiT"]
    assert [row["dataset"] for row in spec["rows"]] == ["ImageNet", "CIFAR-10"]
    assert r"\textbf{88.5}" in latex
    assert (tmp_path / "out/caption.txt").read_text() == "Main results.\n"


def test_transposed_columns_keep_groups_contiguous(tmp_path: Path) -> None:
    source = tmp_path / "results.csv"
    source.write_text(
        "method,pretrain_data,dataset,accuracy\n"
        "A,JFT,D,3\n"
        "A,ImageNet,D,2\n"
        "B,JFT,D,1\n",
        encoding="utf-8",
    )
    generate([source], tmp_path / "out", {
        "template": "transposed-benchmark",
        "input": {"metric_columns": ["accuracy"]},
    })
    spec = json.loads((tmp_path / "out/table-spec.json").read_text())
    assert [column["group_label"] for column in spec["columns"]] == ["JFT", "JFT", "ImageNet"]


@pytest.mark.parametrize(
    ("stem", "template_id"),
    [
        ("hierarchical", "hierarchical-method-budget"),
        ("transposed", "transposed-benchmark"),
        ("quality_efficiency", "quality-efficiency"),
        ("compact", "compact-regime-comparison"),
        ("scaled", "scaled-variants"),
        ("family_banded", "family-banded-benchmark"),
        ("statistical_delta", "benchmark-wide"),
    ],
)
def test_gallery_examples_generate_valid_specs(
    tmp_path: Path, stem: str, template_id: str
) -> None:
    gallery = Path(__file__).parents[1] / "examples" / "gallery"
    config = json.loads((gallery / f"{stem}.json").read_text(encoding="utf-8"))
    manifest = generate([gallery / f"{stem}.csv"], tmp_path / stem, config)

    assert manifest["template_id"] == template_id
    assert manifest["verification"] == {"valid": True, "errors": []}
    assert manifest["displayed_cell_count"] > 0


@pytest.mark.parametrize("stem", ["compact", "scaled", "hierarchical"])
def test_identity_group_templates_default_to_whitespace(
    tmp_path: Path, stem: str
) -> None:
    gallery = Path(__file__).parents[1] / "examples" / "gallery"
    config = json.loads((gallery / f"{stem}.json").read_text(encoding="utf-8"))
    generate([gallery / f"{stem}.csv"], tmp_path / stem, config)
    latex = (tmp_path / stem / "table.tex").read_text(encoding="utf-8")
    html = (tmp_path / stem / "table.html").read_text(encoding="utf-8")
    spec = json.loads((tmp_path / stem / "table-spec.json").read_text(encoding="utf-8"))

    assert latex.count("    \\midrule") == 1  # header rule only
    assert "\\addlinespace" in latex
    assert 'class="group-start space"' in html
    separator_field = next(field["key"] for field in spec["identity_columns"] if field.get("separator"))
    group_values = [row["identity"].get(separator_field) for row in spec["rows"]]
    assert len(list(dict.fromkeys(group_values))) > 1


def test_all_research_backed_templates_are_discoverable() -> None:
    assert {item["id"] for item in available_templates()} == {
        "benchmark-wide",
        "compact-regime-comparison",
        "family-banded-benchmark",
        "hierarchical-method-budget",
        "quality-efficiency",
        "scaled-variants",
        "transposed-benchmark",
    }


def test_all_scientific_table_types_are_discoverable() -> None:
    assert {item["id"] for item in available_table_types()} == {
        "main_benchmark",
        "main_tradeoff",
        "ablation",
        "analysis",
        "diagnostic",
        "simple_comparison",
    }


def test_main_benchmark_requires_focal_baseline_comparison_on_every_benchmark(
    tmp_path: Path,
) -> None:
    source = tmp_path / "results.csv"
    source.write_text(
        "method,dataset,score\n"
        "Baseline,D1,1\n"
        "Ours,D1,2\n"
        "Ours,D2,3\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="lacks a direct focal-versus-baseline comparison"):
        generate([source], tmp_path / "out", {
            "table_type": "main_benchmark",
            "focal_methods": ["Ours"],
            "input": {"metric_columns": ["score"]},
            "metrics": {"score": {"direction": "max"}},
        })


def test_ablation_type_suppresses_ranking_and_decorative_family_bands(
    tmp_path: Path,
) -> None:
    source = tmp_path / "results.csv"
    source.write_text(
        "group,method,dataset,score\n"
        "Reference,Full,D,4\n"
        "Reference,Alt reference,D,3\n"
        "Ablations,No A,D,2\n"
        "Ablations,No B,D,1\n",
        encoding="utf-8",
    )
    manifest = generate([source], tmp_path / "out", {
        "template": "family-banded-benchmark",
        "table_type": "ablation",
        "focal_methods": ["Full"],
        "input": {"metric_columns": ["score"]},
        "metrics": {"score": {"direction": "max"}},
    })
    spec = json.loads((tmp_path / "out/table-spec.json").read_text())
    latex = (tmp_path / "out/table.tex").read_text()

    assert manifest["table_type"] == "ablation"
    assert manifest["focal_methods"] == ["Full"]
    assert spec["emphasis"] == {}
    assert r"\rowcolor[HTML]{EFEFEF} \multicolumn" not in latex
    assert r"\textbf{4.00}" not in latex


def test_unknown_table_type_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "results.csv"
    source.write_text("method,dataset,score\nA,D,1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unknown table_type"):
        generate([source], tmp_path / "out", {
            "table_type": "decorative",
            "input": {"metric_columns": ["score"]},
        })


def test_family_bands_scoped_ranking_and_focal_highlight(tmp_path: Path) -> None:
    gallery = Path(__file__).parents[1] / "examples" / "gallery"
    config = json.loads((gallery / "family_banded.json").read_text(encoding="utf-8"))
    manifest = generate(
        [gallery / "family_banded.csv"], tmp_path / "family-banded", config
    )
    latex = (tmp_path / "family-banded/table.tex").read_text(encoding="utf-8")
    html = (tmp_path / "family-banded/table.html").read_text(encoding="utf-8")
    caption = (tmp_path / "family-banded/caption.txt").read_text(encoding="utf-8")

    assert manifest["ranking_scope"] == "non-proprietary systems"
    assert latex.count(r"\rowcolor[HTML]{EFEFEF} \multicolumn") == 4
    assert r"Aurora-Pro & 0.91" in latex
    assert r"Aurora-Pro & \textbf{0.91}" not in latex
    assert r"\rowcolor[HTML]{E8F1FF} PaperTable-Agent & \textbf{0.88}" in latex
    assert "--" in latex
    assert 'class="group-band"' in html
    assert caption == "Main results on WISE and HumanitiesBench.\n"
    assert manifest["context_notes"]


def test_family_bands_flatten_when_only_one_multirow_group_remains(tmp_path: Path) -> None:
    source = tmp_path / "groups.csv"
    source.write_text(
        "group,method,dataset,score\n"
        "Baselines,Base A,D,1\n"
        "Baselines,Base B,D,2\n"
        "Proposed method,Ours,D,3\n",
        encoding="utf-8",
    )
    generate([source], tmp_path / "out", {
        "template": "family-banded-benchmark",
        "input": {"metric_columns": ["score"]},
        "metrics": {"score": {"direction": "max"}},
        "style": {"highlight_methods": ["Ours"]},
    })
    latex = (tmp_path / "out/table.tex").read_text(encoding="utf-8")
    html = (tmp_path / "out/table.html").read_text(encoding="utf-8")

    assert r"\textbf{Baselines}" not in latex
    assert "Proposed method" not in latex
    assert r"\rowcolor[HTML]{E8F1FF} Ours" in latex
    assert 'class="group-band"' not in html
    assert ">Proposed method<" not in html


def test_family_bands_require_two_parallel_multirow_groups(tmp_path: Path) -> None:
    source = tmp_path / "groups.csv"
    source.write_text(
        "group,method,dataset,score\n"
        "Family A,A1,D,1\n"
        "Family A,A2,D,2\n"
        "Family B,B1,D,3\n"
        "Family B,B2,D,4\n"
        "Proposed method,Ours,D,5\n",
        encoding="utf-8",
    )
    generate([source], tmp_path / "out", {
        "template": "family-banded-benchmark",
        "input": {"metric_columns": ["score"]},
        "metrics": {"score": {"direction": "max"}},
        "style": {"highlight_methods": ["Ours"]},
    })
    latex = (tmp_path / "out/table.tex").read_text(encoding="utf-8")
    html = (tmp_path / "out/table.html").read_text(encoding="utf-8")

    assert r"\textbf{Family A}" in latex
    assert r"\textbf{Family B}" in latex
    assert "Proposed method" not in latex
    assert html.count('class="group-band"') == 2


def test_auxiliary_delta_preserves_main_value_and_lineage(tmp_path: Path) -> None:
    gallery = Path(__file__).parents[1] / "examples" / "gallery"
    config = json.loads((gallery / "statistical_delta.json").read_text(encoding="utf-8"))
    manifest = generate(
        [gallery / "statistical_delta.csv"], tmp_path / "statistical-delta", config
    )
    spec = json.loads((tmp_path / "statistical-delta/table-spec.json").read_text())
    latex = (tmp_path / "statistical-delta/table.tex").read_text(encoding="utf-8")
    html = (tmp_path / "statistical-delta/table.html").read_text(encoding="utf-8")
    target = next(row for row in spec["rows"] if row["method"] == "PaperTable-Ours")

    assert manifest["auxiliary_display"] == ["delta"]
    assert target["cells"][0]["mean"] == pytest.approx(84.6)
    assert target["cells"][0]["auxiliary"]["value"] == pytest.approx(2.4)
    assert target["cells"][0]["n"] == 2
    assert r"r@{\hspace{0.25em}}l" in latex
    assert r"\multicolumn{2}{c}{Accuracy (\%) $\uparrow$}" in latex
    assert r"\textbf{84.6 $\pm$ 0.1} & {\scriptsize (+2.4)}" in latex
    assert r"\underline{17.8 $\pm$ 0.1} & {\scriptsize (-2.2)}" in latex
    baseline_line = next(line for line in latex.splitlines() if line.lstrip().startswith("Strong Baseline &"))
    target_line = next(line for line in latex.splitlines() if "PaperTable-Ours &" in line)
    assert baseline_line.count(" & ") == target_line.count(" & ") == 12
    assert html.count('class="cell-grid"') == 24


def test_auxiliary_delta_requires_unique_baseline(tmp_path: Path) -> None:
    source = tmp_path / "results.csv"
    source.write_text(
        "method,model,dataset,score\n"
        "Base,A,D,1\n"
        "Base,B,D,2\n"
        "Ours,C,D,3\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="baseline matched 2 rows"):
        generate([source], tmp_path / "out", {
            "input": {"metric_columns": ["score"]},
            "layout": {"row_fields": ["model", "method"]},
            "auxiliary": {
                "delta": {
                    "baseline": {"method": "Base"},
                    "targets": [{"method": "Ours"}],
                }
            },
        })


def test_empty_ranking_scope_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "results.csv"
    source.write_text("group,method,dataset,score\nBaseline,A,D,1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="ranking scope selects no displayed systems"):
        generate([source], tmp_path / "out", {
            "input": {"metric_columns": ["score"]},
            "comparison": {"rank_exclude_groups": ["Baseline"]},
        })


def test_unrepresented_identity_dimension_cannot_silently_collapse(tmp_path: Path) -> None:
    source = tmp_path / "results.csv"
    source.write_text(
        "method,protocol,dataset,accuracy\n"
        "A,zero-shot,D,80\n"
        "A,fine-tuned,D,90\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="collapse into one table cell"):
        generate([source], tmp_path / "out", {
            "input": {"metric_columns": ["accuracy"]},
        })
