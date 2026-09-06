"""Engineering fixtures exercise files, state transitions, cancellation and PDF rendering."""

import base64
import io
import json
import threading
import time
import zipfile
from pathlib import Path

import fitz
import pytest

from auto_table.application import Application, read_json
from auto_table.engine.manuscript import inspect_manuscript, replace_manuscript

DATA = b"method,dataset,seed,score\nBaseline,D1,1,80\nBaseline,D1,2,82\nCandidate,D1,1,84\nCandidate,D1,2,86\n"
CONFIG = {
    "input": {"metric_columns": ["score"]},
    "metrics": {"score": {"direction": "max", "precision": 1}},
    "table_type": "simple_comparison",
    "title": "Engineering fixture",
    "description": "Synthetic values used only to test the table pipeline.",
}


def file(name, data):
    return {"name": name, "content_base64": base64.b64encode(data).decode()}


def payload(**extra):
    return {
        "title": "Engineering fixture — no scientific result",
        "mode": "results",
        "files": [file("results.csv", DATA)],
        **extra,
    }


def fake_compile(main, build, log, callback):
    build.mkdir(parents=True, exist_ok=True)
    pdf = build / "preview.pdf"
    with fitz.open() as document:
        page = document.new_page()
        page.insert_text((70, 70), "ENGINEERING FIXTURE ONLY")
        document.save(pdf)
    log.write_text("Engineering compiler fixture; no TeX compilation performed.\n")
    return "fixture", pdf


class Runner:
    def __init__(self, passed=True):
        self.calls = []
        self.passed = passed

    def __call__(self, prompt, schema, directory, logs, name, job):
        self.calls.append(name)
        if name == "design":
            return {
                "rationale": "Engineering fixture",
                "tables": [{"id": "main", "title": "Fixture", "config_json": json.dumps(CONFIG)}],
                "replacements": [],
                "preamble": "",
            }
        return {
            "passed": self.passed,
            "findings": ["Engineering reviewer fixture only."],
            "inspected_pages": [str(p) for p in sorted(directory.glob("tables/*/pages/*.png"))],
        }


def wait(app, project_id):
    deadline = time.monotonic() + 6
    while time.monotonic() < deadline:
        with app.lock:
            if project_id not in app.jobs:
                return app.load(project_id)
        time.sleep(0.01)
    raise AssertionError("table fixture did not finish")


def test_results_pipeline_keeps_sd_lineage_and_real_artifacts(tmp_path):
    runner = Runner()
    app = Application(tmp_path, runner=runner, compiler=fake_compile)
    p = app.create(payload())
    assert not app.jobs and p["status"] == "idle"
    app.start(p["id"])
    result = wait(app, p["id"])
    assert result["status"] == "ready"
    assert runner.calls == ["design", "review"]
    output = result["outputs"][0]
    spec = read_json(Path(output["directory"]) / "table-spec.json")
    assert spec["rows"][1]["cells"][0]["mean"] == 85
    assert spec["rows"][1]["cells"][0]["values"] == [84, 86]
    assert spec["rows"][1]["cells"][0]["sd"] == pytest.approx(2**0.5)
    assert Path(output["pdf"]).is_file() and Path(output["pages"][0]).is_file()
    assert read_json(Path(output["directory"]) / "manifest.json")["compiled_pdf"] == output["pdf"]
    with zipfile.ZipFile(app.directory(p["id"]) / "attempt-1/deliverables.zip") as bundle:
        assert "main/preview.pdf" in bundle.namelist()
    assert (tmp_path / "assets/input/auto_table" / p["id"] / "results.csv").read_bytes() == DATA


def test_compile_failure_resumes_without_regenerating_plan(tmp_path):
    runner = Runner()

    def failure(*args):
        raise RuntimeError("compiler unavailable fixture")

    app = Application(tmp_path, runner=runner, compiler=failure)
    p = app.create(payload())
    app.start(p["id"])
    result = wait(app, p["id"])
    assert result["status"] == "failed" and result["step"] == "compile"
    assert Path(result["outputs"][0]["tex"]).is_file()
    original = (app.directory(p["id"]) / "attempt-1/plan.json").read_bytes()
    app.compiler = fake_compile
    app.start(p["id"])
    assert wait(app, p["id"])["status"] == "ready"
    assert runner.calls == ["design", "review"]
    assert (app.directory(p["id"]) / "attempt-1/plan.json").read_bytes() == original


def test_negative_review_and_revision_keep_previous_round(tmp_path):
    runner = Runner(False)
    app = Application(tmp_path, runner=runner, compiler=fake_compile)
    p = app.create(payload())
    app.start(p["id"])
    assert wait(app, p["id"])["status"] == "needs_revision"
    with pytest.raises(ValueError, match="本轮已结束"):
        app.start(p["id"])
    runner.passed = True
    app.start(p["id"], {"revise": True, "feedback": "Engineering revision"})
    result = wait(app, p["id"])
    assert result["attempt"] == 2 and result["status"] == "ready"
    assert (app.directory(p["id"]) / "attempt-1/review.json").is_file()


def test_missing_review_pages_cannot_complete(tmp_path):
    def runner(*args):
        value = Runner()(*args)
        if args[4] == "review":
            value["inspected_pages"] = []
        return value

    app = Application(tmp_path, runner=runner, compiler=fake_compile)
    p = app.create(payload())
    app.start(p["id"])
    assert wait(app, p["id"])["status"] == "needs_revision"


def test_cancel_and_restart_recover_without_starting_jobs(tmp_path):
    entered = threading.Event()

    def blocking(prompt, schema, directory, logs, name, job):
        entered.set()
        job.cancelled.wait(3)
        job.check()

    app = Application(tmp_path, runner=blocking, compiler=fake_compile)
    p = app.create(payload())
    app.start(p["id"])
    assert entered.wait(2)
    with pytest.raises(ValueError, match="仍在运行"):
        app.start(p["id"])
    app.stop(p["id"])
    result = wait(app, p["id"])
    assert result["status"] == "paused"
    result["status"] = "running"
    app.save(result)
    restored = Application(tmp_path, runner=Runner(), compiler=fake_compile)
    assert restored.load(p["id"])["status"] == "paused" and not restored.jobs
    restored.start(p["id"])
    assert wait(restored, p["id"])["status"] == "ready"


def test_custom_method_field_can_be_planned_after_inspection(tmp_path):
    app = Application(tmp_path, runner=Runner(), compiler=fake_compile)
    p = app.create(payload(files=[file("results.csv", b"name,score\nCandidate,1\n")]))
    directory = app.directory(p["id"]) / "attempt-1"
    directory.mkdir()
    app._inspect(p, directory, tmp_path, None)
    assert "ingestion_message" in p["inspection"]


def manuscript_zip():
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as bundle:
        bundle.writestr(
            "main.tex",
            r"\documentclass{article}"
            + "\n"
            + r"\begin{document}\input{sections/results}\end{document}",
        )
        bundle.writestr(
            "sections/results.tex",
            r"\section{Experiments}"
            + "\n"
            + r"\begin{table}\caption{Original}\label{tab:main}\begin{tabular}{lr}Baseline & 81.0\\Candidate & 85.0\end{tabular}\end{table}",
        )
    return data.getvalue()


def test_manuscript_subfile_replacement_preserves_other_source(tmp_path):
    archive = tmp_path / "manuscript.zip"
    archive.write_bytes(manuscript_zip())
    inspected = inspect_manuscript(archive, tmp_path / "inspection")
    assert inspected["tables"][0]["source_file"] == "sections/results.tex"
    replacements = tmp_path / "replacements"
    replacements.mkdir()
    source = (tmp_path / "inspection/original-tables/tab-main.tex").read_text()
    (replacements / "tab-main.tex").write_text(source.replace("{table}", "{table*}"))
    replace_manuscript(archive, replacements, tmp_path / "patched")
    assert (tmp_path / "patched/source/main.tex").read_text() == (
        tmp_path / "inspection/source/main.tex"
    ).read_text()
    assert r"\begin{table*}" in (tmp_path / "patched/source/sections/results.tex").read_text()


def test_explicit_main_and_commented_tables(tmp_path):
    archive = tmp_path / "multiple.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        for name in ("main.tex", "other.tex"):
            bundle.writestr(
                name,
                "\\documentclass{article}\n% \\begin{table}ignored\\end{table}\n\\begin{document}\n\\begin{table}81\\end{table}\n\\end{document}",
            )
    with pytest.raises(ValueError, match="multiple main"):
        inspect_manuscript(archive, tmp_path / "ambiguous")
    result = inspect_manuscript(archive, tmp_path / "selected", main_file="main.tex")
    assert result["table_count"] == 1
