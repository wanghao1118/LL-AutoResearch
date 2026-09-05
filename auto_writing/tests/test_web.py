from __future__ import annotations

import base64
import io
import json
import tempfile
import unittest
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from auto_writing.web import serve


def encoded_file(name: str, content: bytes) -> dict[str, str]:
    return {
        "name": name,
        "content_base64": base64.b64encode(content).decode("ascii"),
    }


def encoded_zip(name: str, files: dict[str, str]) -> dict[str, str]:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, content in files.items():
            archive.writestr(path, content)
    return encoded_file(name, buffer.getvalue())


class AutoWritingWebTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.runs_root = Path(self.temporary.name) / "writing_runs"
        self.root_patch = patch.object(serve, "WRITING_RUNS_ROOT", self.runs_root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def create_project(self) -> dict[str, object]:
        return serve.create_project(
            "Reliable indoor sensing",
            encoded_file(
                "experiment.md",
                b"# Experiment\nMethod, protocol, baselines, and measured results.\n",
            ),
            [encoded_file("references.txt", b"Verified supporting notes.\n")],
        )

    def intro_research_result(self) -> dict[str, object]:
        return {
            "research_direction": "Reliable sensing methods for fine-grained indoor activity recognition.",
            "paragraph_1_evidence": [
                {
                    "claim": f"Supported significance claim {index} for the research field.",
                    "evidence": f"Primary-source evidence {index} explains the scientific and practical role.",
                    "source_title": f"Authoritative source {index}",
                    "authors": f"Research Author {index}",
                    "year": 2015 + index,
                    "venue": "Test Journal",
                    "source_url": f"https://example.org/source-{index}",
                    "doi": f"10.0000/source.{index}",
                    "citation_key": f"ResearchSource{index}",
                    "bibtex": f"@article{{ResearchSource{index}, title={{Authoritative source {index}}}, author={{Research Author}}, year={{20{15 + index}}}}}",
                }
                for index in range(1, 4)
            ],
            "paragraph_2_papers": [
                {
                    "title": f"Representative sensing paper {index}",
                    "lead_author": f"Author{index}",
                    "authors": f"Author{index} and Collaborator{index}",
                    "year": 2020 + index,
                    "venue": "Test Conference",
                    "method_name": f"Method{index}",
                    "mechanism": "The method uses a verified sensing mechanism described by its primary source.",
                    "development_role": "The work advances the technical line toward the paper's target setting.",
                    "source_url": f"https://example.org/paper-{index}",
                    "doi": f"10.0000/test.{index}",
                    "citation_key": f"SensingPaper{index}",
                    "bibtex": f"@inproceedings{{SensingPaper{index}, title={{Representative sensing paper {index}}}, author={{Author and Collaborator}}, year={{{2020 + index}}}}}",
                }
                for index in range(1, 5)
            ],
            "synthesis_guidance": {
                "paragraph_1_logic": "Move from the importance of the broad field to the narrower sensing direction.",
                "paragraph_2_logic": "Connect representative methods through changes in their technical mechanisms.",
                "transition_to_unresolved_challenge": "End with a broad challenge that several technical lines attempt to address.",
            },
            "evidence_boundaries": [],
        }

    def reference_result(self) -> dict[str, object]:
        scopes = {
            **{f"Ref{index:02d}": "intro_p1" for index in range(1, 4)},
            **{f"Ref{index:02d}": "intro_p2" for index in range(4, 7)},
            **{f"Ref{index:02d}": "related_work" for index in range(7, 13)},
            **{f"Ref{index:02d}": "experiments_datasets" for index in range(13, 15)},
            **{f"Ref{index:02d}": "experiments_backbones" for index in range(15, 17)},
            **{f"Ref{index:02d}": "experiments_baselines" for index in range(17, 21)},
        }
        references = [
            {
                "citation_key": key,
                "title": f"Verified reference paper {index}",
                "authors": f"Author {index} and Collaborator {index}",
                "year": 2000 + index,
                "venue": "Verified Conference",
                "doi": f"10.0000/reference.{index}",
                "source_url": f"https://example.org/reference-{index}",
                "bibtex": f"@article{{{key}, title={{Verified reference paper {index}}}, author={{Author and Collaborator}}, year={{{2000 + index}}}}}",
                "used_in": [scopes[key]],
            }
            for index, key in enumerate(scopes, start=1)
        ]
        return {
            "references": references,
            "bibtex": "\n\n".join(item["bibtex"] for item in references),
            "updated_sections": {
                "intro": (
                    "\\section{Introduction}\n\n"
                    "The broad field is important and supports a consequential research workflow \\cite{Ref01,Ref02,Ref03}.\n\n"
                    "Prior technical approaches developed several relevant mechanisms but retain limitations \\cite{Ref04,Ref05,Ref06}.\n\n"
                    "The unresolved technical problem follows from these limitations and motivates the present work.\n\n"
                    "We introduce the proposed method and summarize its evidence-backed contributions."
                ),
                "related_work": (
                    "\\section{Related Work}\n"
                    "\\subsection{Research Line One}\nRepresentative methods establish the first technical line \\cite{Ref07,Ref08}.\n"
                    "\\subsection{Research Line Two}\nA second family develops complementary mechanisms \\cite{Ref09,Ref10}.\n"
                    "\\subsection{Research Line Three}\nThe closest approaches leave the target problem unresolved \\cite{Ref11,Ref12}."
                ),
                "experiments": (
                    "\\section{Experiments}\n"
                    "\\subsection{Datasets and Models}\nThe evaluation uses verified datasets \\cite{Ref13,Ref14} and backbone models \\cite{Ref15,Ref16}.\n"
                    "\\subsection{Comparisons}\nThe comparison includes established baseline methods \\cite{Ref17,Ref18,Ref19,Ref20}.\n"
                    "The reported measurements and conclusions remain unchanged from the completed experiment section."
                ),
            },
            "coverage": {
                "intro_p1": ["Ref01", "Ref02", "Ref03"],
                "intro_p2": ["Ref04", "Ref05", "Ref06"],
                "related_work": [f"Ref{index:02d}" for index in range(7, 13)],
                "experiments_datasets": [
                    {"target": "Dataset A", "citation_keys": ["Ref13"]},
                    {"target": "Dataset B", "citation_keys": ["Ref14"]},
                ],
                "experiments_backbones": [
                    {"target": "Backbone A", "citation_keys": ["Ref15"]},
                    {"target": "Backbone B", "citation_keys": ["Ref16"]},
                ],
                "experiments_baselines": [
                    {"target": "Baseline family", "citation_keys": ["Ref17", "Ref18", "Ref19", "Ref20"]}
                ],
            },
            "evidence_boundaries": [],
        }

    def seed_research(
        self, project: dict[str, object], action: str, result: dict[str, object]
    ) -> None:
        run_dir = self.runs_root / project["id"]
        serve.write_json_atomic(serve.research_output_path(run_dir, action), result)
        project["research"][action]["status"] = "ready"
        serve.save_project(project)

    def test_project_has_six_sections_and_runtime_path_contract(self) -> None:
        project = self.create_project()
        view = serve.project_view(project)
        self.assertEqual([item["key"] for item in view["sections"]], list(serve.SECTION_ORDER))
        self.assertEqual(view["completed"], 0)
        self.assertEqual(view["total"], 6)
        self.assertTrue(Path(view["experiment"]["path"]).is_file())
        contract_path = Path(view["path_contract_path"])
        self.assertTrue(contract_path.is_file())
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        self.assertIn("experiment_description", contract["entries"])
        self.assertIn("intro_literature_research", contract["entries"])
        self.assertIn("related_work_subsection_plan", contract["entries"])
        self.assertIn("contains", contract["entries"]["generated_method"])
        self.assertEqual([item["key"] for item in view["actions"]], list(serve.RESEARCH_ACTIONS))
        self.assertFalse(view["publication"]["available"])
        self.assertEqual(
            view["publication"]["missing_sections"],
            list(serve.SECTION_ORDER) + ["reference_insertion"],
        )

    def test_legacy_project_marks_old_publication_stale(self) -> None:
        project = self.create_project()
        project["sections"].pop("abstract")
        project["research"].pop("reference_insertion")
        project["publication"]["status"] = "ready"
        serve.write_json_atomic(self.runs_root / project["id"] / "project.json", project)

        upgraded = serve.load_project(project["id"])

        self.assertIn("abstract", upgraded["sections"])
        self.assertIn("reference_insertion", upgraded["research"])
        self.assertEqual(upgraded["publication"]["status"], "stale")
        self.assertIn("Abstract", upgraded["publication"]["error"])

    def test_project_files_can_be_replaced_added_and_removed(self) -> None:
        project = self.create_project()
        run_dir = self.runs_root / project["id"]
        for action in serve.RESEARCH_ACTIONS:
            serve.write_json_atomic(serve.research_output_path(run_dir, action), {"value": action})
            project["research"][action]["status"] = "ready"
        for section in serve.SECTION_ORDER:
            serve.write_json_atomic(
                serve.section_output_path(run_dir, section),
                {section: f"\\section{{{section}}}\n" + "Complete generated content. " * 6},
            )
            project["sections"][section]["status"] = "ready"
        serve.save_project(project)

        updated = serve.update_project(
            project["id"],
            "Updated sensing paper",
            encoded_file("replacement.md", b"# Replacement experiment\nNew evidence.\n"),
            [],
            [encoded_file("new-reference.txt", b"New supporting evidence.\n")],
        )

        self.assertEqual(updated["experiment"]["name"], "replacement.md")
        self.assertEqual([item["name"] for item in updated["support_files"]], ["new-reference.txt"])
        self.assertFalse((run_dir / "input" / "experiment.md").exists())
        self.assertFalse((run_dir / "input" / "supporting_materials" / "references.txt").exists())
        self.assertTrue((run_dir / "input" / "replacement.md").is_file())
        self.assertTrue(all(item["status"] == "stale" for item in updated["sections"].values()))
        self.assertTrue(all(item["status"] == "stale" for item in updated["research"].values()))

    def test_title_only_edit_preserves_sections_and_stales_existing_publication(self) -> None:
        project = self.create_project()
        run_dir = self.runs_root / project["id"]
        for section in serve.SECTION_ORDER:
            serve.write_json_atomic(
                serve.section_output_path(run_dir, section),
                {section: f"\\section{{{section}}}\n" + "Complete generated content. " * 6},
            )
            project["sections"][section]["status"] = "ready"
        output_dir = serve.publication_dir(run_dir)
        output_dir.mkdir()
        (output_dir / "manuscript-latex.zip").write_bytes(b"zip")
        project["publication"]["status"] = "ready"
        serve.save_project(project)

        updated = serve.update_project(
            project["id"],
            "Renamed paper",
            None,
            [item["relative_path"] for item in project["support_files"]],
            [],
        )

        self.assertTrue(all(item["status"] == "ready" for item in updated["sections"].values()))
        self.assertEqual(updated["publication"]["status"], "stale")

    def test_latex_template_extraction_rejects_traversal_and_finds_main(self) -> None:
        destination = self.runs_root / "template"
        valid = encoded_zip(
            "template.zip",
            {"conference/main.tex": "\\documentclass{article}\n\\begin{document}\nSample\n\\end{document}"},
        )
        _, valid_data = serve.decode_zip_file(valid)
        paths = serve.extract_latex_template(valid_data, destination)
        main = serve.detect_latex_main(paths, destination)
        self.assertEqual(main.relative_to(destination).as_posix(), "conference/main.tex")

        unsafe = encoded_zip("unsafe.zip", {"../escape.tex": "unsafe"})
        _, unsafe_data = serve.decode_zip_file(unsafe)
        with self.assertRaisesRegex(ValueError, "不安全"):
            serve.extract_latex_template(unsafe_data, self.runs_root / "unsafe")

    def test_atomic_json_writes_are_safe_under_concurrent_refreshes(self) -> None:
        target = self.runs_root / "concurrent" / "path_contract.json"

        def write_many(worker: int) -> None:
            for iteration in range(25):
                serve.write_json_atomic(
                    target,
                    {"worker": worker, "iteration": iteration},
                )

        with ThreadPoolExecutor(max_workers=12) as executor:
            list(executor.map(write_many, range(12)))

        result = json.loads(target.read_text(encoding="utf-8"))
        self.assertIn(result["worker"], range(12))
        self.assertIn(result["iteration"], range(25))
        self.assertEqual(list(target.parent.glob(".*.tmp")), [])

    def test_prompt_paths_are_injected_at_runtime(self) -> None:
        project = self.create_project()
        self.seed_research(project, "intro_research", self.intro_research_result())
        prompt = serve.build_resolved_prompt(project, "intro")
        experiment_path = str(
            (self.runs_root / project["id"] / project["experiment"]["relative_path"]).resolve()
        )
        self.assertIn(json.dumps(experiment_path)[1:-1], prompt)
        self.assertIn("current_output", prompt)
        self.assertIn("intro_research", prompt)
        self.assertNotIn("D:/Projects/auto_research", prompt)
        self.assertNotRegex(prompt, r"[\u3400-\u9fff]")
        resolved_path = self.runs_root / project["id"] / "prompts" / "intro.resolved.txt"
        self.assertEqual(resolved_path.read_text(encoding="utf-8").strip(), prompt)

    def test_missing_upstream_section_returns_actionable_precondition(self) -> None:
        project = self.create_project()
        with self.assertRaises(serve.GenerationPreconditionError) as context:
            serve.build_resolved_prompt(project, "method")
        self.assertEqual(context.exception.missing, ["intro"])
        self.assertIn("请先完成", str(context.exception))
        self.assertIn("Introduction", str(context.exception))

    def test_intro_generation_requires_manual_research(self) -> None:
        project = self.create_project()
        with self.assertRaises(serve.GenerationPreconditionError) as context:
            serve.build_resolved_prompt(project, "intro")
        self.assertEqual(context.exception.missing, ["intro_research"])
        self.assertIn("Introduction 论文调研", str(context.exception))

    def test_abstract_requires_all_five_body_sections(self) -> None:
        project = self.create_project()
        with self.assertRaises(serve.GenerationPreconditionError) as context:
            serve.build_resolved_prompt(project, "abstract")
        self.assertEqual(context.exception.missing, list(serve.BASE_SECTION_ORDER))

        run_dir = self.runs_root / project["id"]
        for section in serve.BASE_SECTION_ORDER:
            serve.write_json_atomic(
                serve.section_output_path(run_dir, section),
                {section: f"\\section{{{serve.SECTION_LABELS[section]}}}\n" + "Completed body content. " * 8},
            )
            project["sections"][section]["status"] = "ready"
        serve.save_project(project)
        prompt = serve.build_resolved_prompt(project, "abstract")
        self.assertIn("180 to 250 English words", prompt)
        self.assertNotRegex("\n".join(serve.load_templates()["abstract"]["template"]), r"[A-Za-z]:[\\/]")

    def test_abstract_output_contract_checks_length_sentences_and_citations(self) -> None:
        project = self.create_project()
        sentence = "The completed paper supports this concise evidence based abstract statement through verified technical reasoning and measured experimental results within the stated evaluation scope only."
        content = "\\begin{abstract}\n" + " ".join(f"{sentence[:-1]} {index}." for index in range(1, 9)) + "\n\\end{abstract}"
        with patch.object(serve, "invoke_codex_json", return_value={"content": content}):
            self.assertEqual(serve.invoke_codex(project, "abstract", "prompt"), content)
        cited = content.replace("evaluation scope only 1.", "evaluation scope only \\cite{Example} 1.")
        with (
            patch.object(serve, "invoke_codex_json", return_value={"content": cited}),
            self.assertRaisesRegex(ValueError, "不应包含参考文献"),
        ):
            serve.invoke_codex(project, "abstract", "prompt")

    def test_abstract_automatically_refines_an_overlong_first_draft(self) -> None:
        project = self.create_project()
        sentence = "The completed paper supports this concise evidence based abstract statement through verified technical reasoning and measured experimental results within the stated evaluation scope only."
        valid = "\\begin{abstract}\n" + " ".join(
            f"{sentence[:-1]} {index}." for index in range(1, 9)
        ) + "\n\\end{abstract}"
        overlong = valid.replace(
            "\n\\end{abstract}",
            " " + " ".join(["additional"] * 100) + "\n\\end{abstract}",
        )
        with patch.object(
            serve,
            "invoke_codex_json",
            side_effect=[{"content": overlong}, {"content": valid}],
        ) as invoke:
            self.assertEqual(serve.invoke_codex(project, "abstract", "prompt"), valid)
        self.assertEqual(invoke.call_count, 2)
        refinement_prompt = (
            self.runs_root
            / project["id"]
            / "prompts"
            / "abstract_refinement.resolved.txt"
        ).read_text(encoding="utf-8")
        self.assertIn("200 to 230 English words", refinement_prompt)

    def test_intro_research_rejects_placeholder_results(self) -> None:
        project = self.create_project()
        result = self.intro_research_result()
        result["research_direction"] = "Undetermined because the experiment file was inaccessible."
        with self.assertRaisesRegex(ValueError, "占位内容"):
            serve.validate_research_result(project, "intro_research", result)

    def test_reference_prompt_requires_written_targets_and_exposes_existing_bibtex(self) -> None:
        project = self.create_project()
        with self.assertRaises(serve.GenerationPreconditionError) as context:
            serve.build_research_prompt(project, "reference_insertion")
        self.assertEqual(
            context.exception.missing,
            ["intro", "related_work", "experiments", "abstract"],
        )
        run_dir = self.runs_root / project["id"]
        for section in ("intro", "related_work", "experiments", "abstract"):
            content = (
                "\\begin{abstract}\n" + "Completed abstract content. " * 60 + "\\end{abstract}"
                if section == "abstract"
                else f"\\section{{{serve.SECTION_LABELS[section]}}}\n"
                + "Completed citation target content. " * 7
            )
            serve.write_json_atomic(
                serve.section_output_path(run_dir, section),
                {section: content},
            )
            project["sections"][section]["status"] = "ready"
        serve.save_project(project)
        prompt = serve.build_research_prompt(project, "reference_insertion")
        self.assertIn("existing_references", prompt)
        self.assertIn("prior_research", prompt)
        self.assertIn("20 to 25", prompt)

    def test_reference_result_requires_complete_citation_coverage(self) -> None:
        project = self.create_project()
        result = self.reference_result()
        serve.validate_research_result(project, "reference_insertion", result)
        result["updated_sections"]["intro"] = result["updated_sections"]["intro"].replace(
            "\\cite{Ref01,Ref02,Ref03}", ""
        )
        with self.assertRaisesRegex(ValueError, "第一、二段"):
            serve.validate_research_result(project, "reference_insertion", result)

    def test_related_work_requires_plan_then_research_then_generation(self) -> None:
        project = self.create_project()
        self.seed_research(project, "intro_research", self.intro_research_result())
        run_dir = self.runs_root / project["id"]
        serve.write_json_atomic(
            serve.section_output_path(run_dir, "intro"),
            {"intro": "A complete Introduction with sufficient content to bind the Related Work scope, terminology, and technical challenge."},
        )
        project["sections"]["intro"]["status"] = "ready"
        serve.save_project(project)

        plan_prompt = serve.build_research_prompt(project, "related_work_plan")
        self.assertIn(
            json.dumps(str(serve.section_output_path(run_dir, "intro").resolve()))[1:-1],
            plan_prompt,
        )
        self.assertIn("intro_research", plan_prompt)
        with self.assertRaises(serve.GenerationPreconditionError) as context:
            serve.build_research_prompt(project, "related_work_research")
        self.assertEqual(context.exception.missing, ["related_work_plan"])

        plan = {
            "subsections": [
                {
                    "title": title,
                    "scope": "A focused technical scope that avoids overlap with the other planned topics.",
                    "connection_to_paper": "This topic establishes the literature context for the paper's technical challenge.",
                    "search_queries": ["query one", "query two", "query three"],
                }
                for title in ("Sensing Models", "Feature Fusion", "Robust Recognition")
            ]
        }
        self.seed_research(project, "related_work_plan", plan)
        research_prompt = serve.build_research_prompt(project, "related_work_research")
        self.assertIn("related_work_plan", research_prompt)
        with self.assertRaises(serve.GenerationPreconditionError) as context:
            serve.build_resolved_prompt(project, "related_work")
        self.assertEqual(context.exception.missing, ["related_work_research"])

    def test_rerunning_research_marks_existing_manuscript_stale(self) -> None:
        project = self.create_project()
        run_dir = self.runs_root / project["id"]
        self.seed_research(project, "intro_research", self.intro_research_result())
        serve.write_json_atomic(
            serve.section_output_path(run_dir, "intro"),
            {"intro": "An existing Introduction that is long enough to represent previously generated manuscript content."},
        )
        project["sections"]["intro"]["status"] = "ready"
        serve.save_project(project)
        serve.invalidate_after_research(project, "intro_research")
        self.assertEqual(project["sections"]["intro"]["status"], "stale")

    def test_ready_upstream_section_is_included_in_later_prompt(self) -> None:
        project = self.create_project()
        run_dir = self.runs_root / project["id"]
        serve.write_json_atomic(
            serve.section_output_path(run_dir, "intro"),
            {"intro": "A sufficiently long generated introduction that establishes the research scope and terminology for all later sections."},
        )
        project["sections"]["intro"]["status"] = "ready"
        serve.save_project(project)
        prompt = serve.build_resolved_prompt(project, "method")
        intro_path = str(serve.section_output_path(run_dir, "intro").resolve())
        self.assertIn(json.dumps(intro_path)[1:-1], prompt)
        view = serve.project_view(project)
        method = next(item for item in view["sections"] if item["key"] == "method")
        self.assertEqual(method["missing_dependencies"], [])

    def test_templates_contain_no_machine_specific_paths(self) -> None:
        templates = serve.load_templates()
        for section, record in templates.items():
            template = "\n".join(record["template"])
            self.assertNotRegex(template, r"[A-Za-z]:[\\/]")
            self.assertIn("<<PATH_CONTEXT_JSON>>", template, section)
        research_templates = serve.load_research_templates()
        for action, record in research_templates.items():
            template = "\n".join(record["template"])
            self.assertNotRegex(template, r"[A-Za-z]:[\\/]")
            self.assertIn("<<PATH_CONTEXT_JSON>>", template, action)
        latex_template = "\n".join(serve.load_latex_prompt_template()["template"])
        self.assertNotRegex(latex_template, r"[A-Za-z]:[\\/]")
        self.assertIn("<<PATH_CONTEXT_JSON>>", latex_template)
        reference_schema = serve.REFERENCE_OUTPUT_SCHEMA_PATH.read_text(encoding="utf-8")
        self.assertNotIn("uniqueItems", reference_schema)

    def test_research_job_writes_evidence_without_generating_intro(self) -> None:
        project = self.create_project()
        project["research"]["intro_research"]["status"] = "running"
        serve.save_project(project)
        job = serve.ResearchJob(project["id"], "intro_research", "empty")
        result = self.intro_research_result()
        with patch.object(serve, "invoke_codex_json", return_value=result):
            serve.GENERATION_MANAGER._run_research(job)
        updated = serve.load_project(project["id"])
        run_dir = self.runs_root / project["id"]
        self.assertEqual(updated["research"]["intro_research"]["status"], "ready")
        self.assertEqual(updated["sections"]["intro"]["status"], "empty")
        self.assertFalse(serve.section_output_path(run_dir, "intro").exists())
        self.assertEqual(
            json.loads(serve.research_output_path(run_dir, "intro_research").read_text(encoding="utf-8")),
            result,
        )
        reference = json.loads(
            serve.reference_output_path(run_dir).read_text(encoding="utf-8")
        )
        self.assertEqual(updated["research"]["reference_insertion"]["status"], "draft")
        self.assertEqual(reference["phase"], "research")
        self.assertEqual(len(reference["references"]), 7)
        self.assertTrue(serve.reference_bib_path(run_dir).is_file())

    def test_legacy_research_is_deduplicated_and_synced_to_reference_draft(self) -> None:
        project = self.create_project()
        run_dir = self.runs_root / project["id"]
        intro = self.intro_research_result()
        for item in intro["paragraph_1_evidence"]:
            for field in ("authors", "year", "venue", "doi", "citation_key", "bibtex"):
                item.pop(field, None)
        for item in intro["paragraph_2_papers"]:
            for field in ("authors", "citation_key", "bibtex"):
                item.pop(field, None)
        intro["paragraph_1_evidence"][0]["source_title"] = intro["paragraph_2_papers"][0]["title"]
        duplicate = dict(intro["paragraph_2_papers"][0])
        additional = {
            **duplicate,
            "title": "A legacy paper found only by Related Work research",
            "lead_author": "Legacy Author",
            "year": 2019,
            "venue": "Legacy Conference",
            "doi": "10.0000/legacy.related",
            "source_url": "https://example.org/legacy-related",
        }
        related = {
            "subsections": [{"title": "Legacy Topic", "papers": [duplicate, additional]}],
            "evidence_boundaries": [],
        }
        serve.write_json_atomic(
            serve.research_output_path(run_dir, "intro_research"), intro
        )
        serve.write_json_atomic(
            serve.research_output_path(run_dir, "related_work_research"), related
        )
        project["research"]["intro_research"]["status"] = "ready"
        project["research"]["related_work_research"]["status"] = "ready"
        project["research"]["reference_insertion"].update(
            {"status": "failed", "error": "Legacy schema failure"}
        )
        serve.save_project(project)

        serve.migrate_existing_research_references()

        updated = serve.load_project(project["id"])
        reference = json.loads(
            serve.reference_output_path(run_dir).read_text(encoding="utf-8")
        )
        self.assertEqual(updated["research"]["reference_insertion"]["status"], "draft")
        self.assertEqual(reference["phase"], "research")
        self.assertEqual(len(reference["references"]), 7)
        self.assertTrue(all(item["citation_key"] for item in reference["references"]))
        self.assertTrue(all(item["bibtex"].startswith("@misc{") for item in reference["references"]))
        duplicated = next(
            item
            for item in reference["references"]
            if item["title"] == duplicate["title"]
        )
        self.assertEqual(
            set(duplicated["used_in"]),
            {"intro_p1", "intro_p2", "related_work"},
        )
        self.assertEqual(
            set(duplicated["source_actions"]),
            {"intro_research", "related_work_research"},
        )
        self.assertTrue(serve.reference_bib_path(run_dir).is_file())

    def test_reference_job_updates_sections_bibtex_and_preserves_abstract(self) -> None:
        project = self.create_project()
        run_dir = self.runs_root / project["id"]
        for section in ("intro", "related_work", "experiments"):
            serve.write_json_atomic(
                serve.section_output_path(run_dir, section),
                {
                    section: f"\\section{{{serve.SECTION_LABELS[section]}}}\n"
                    + "Completed citation target content. " * 8
                },
            )
            project["sections"][section]["status"] = "ready"
        serve.write_json_atomic(
            serve.section_output_path(run_dir, "abstract"),
            {
                "abstract": "\\begin{abstract}\n"
                + "Existing complete abstract content. " * 40
                + "\\end{abstract}"
            },
        )
        project["sections"]["abstract"]["status"] = "ready"
        project["research"]["reference_insertion"]["status"] = "running"
        serve.save_project(project)

        result = self.reference_result()
        job = serve.ResearchJob(project["id"], "reference_insertion", "empty")
        with patch.object(serve, "invoke_codex_json", return_value=result):
            serve.GENERATION_MANAGER._run_research(job)

        updated = serve.load_project(project["id"])
        stored = json.loads(
            serve.reference_output_path(run_dir).read_text(encoding="utf-8")
        )
        self.assertEqual(updated["research"]["reference_insertion"]["status"], "ready")
        self.assertEqual(updated["sections"]["abstract"]["status"], "ready")
        self.assertEqual(stored["phase"], "inserted")
        self.assertEqual(len(stored["references"]), 20)
        self.assertEqual(
            serve.reference_bib_path(run_dir).read_text(encoding="utf-8").strip(),
            result["bibtex"],
        )
        for section, content in result["updated_sections"].items():
            self.assertEqual(serve.section_content(run_dir, section), content)

    def test_related_work_research_must_preserve_three_planned_titles(self) -> None:
        project = self.create_project()
        plan = {
            "subsections": [
                {
                    "title": title,
                    "scope": "A precise technical scope for representative methods in this research line.",
                    "connection_to_paper": "This line establishes the most relevant context for the paper's challenge.",
                    "search_queries": ["query one", "query two", "query three"],
                }
                for title in ("Sensing Models", "Feature Fusion", "Robust Recognition")
            ]
        }
        self.seed_research(project, "related_work_plan", plan)
        valid = {
            "subsections": [
                {
                    "title": item["title"],
                    "thesis": "This subsection follows one coherent and technically relevant research line.",
                    "papers": [
                        {
                            "title": f"Verified representative paper {paper_index}",
                            "lead_author": f"Author{paper_index}",
                            "authors": f"Author{paper_index} and Collaborator{paper_index}",
                            "year": 2020 + paper_index,
                            "venue": "Test Conference",
                            "method_name": f"Method{paper_index}",
                            "mechanism": "The paper introduces a concrete mechanism verified from its primary source.",
                            "development_role": "The work advances this technical line toward the target research setting.",
                            "source_url": f"https://example.org/related-{paper_index}",
                            "doi": f"10.0000/related.{paper_index}",
                            "citation_key": f"RelatedPaper{paper_index}",
                            "bibtex": f"@article{{RelatedPaper{paper_index}, title={{Verified representative paper {paper_index}}}, author={{Author and Collaborator}}, year={{{2020 + paper_index}}}}}",
                        }
                        for paper_index in range(1, 4)
                    ],
                    "synthesis": "The papers are connected by changes in their mechanisms and assumptions.",
                    "unresolved_gap": "The line still leaves the present technical challenge unresolved.",
                }
                for item in plan["subsections"]
            ],
            "evidence_boundaries": [],
        }
        serve.validate_research_result(project, "related_work_research", valid)
        valid["subsections"][1]["title"] = "Changed Topic"
        with self.assertRaises(ValueError):
            serve.validate_research_result(project, "related_work_research", valid)

    def test_publication_keeps_latex_zip_when_pdf_compilation_is_unavailable(self) -> None:
        project = self.create_project()
        run_dir = self.runs_root / project["id"]
        for section in serve.SECTION_ORDER:
            content = (
                "\\begin{abstract}\n" + "Complete abstract content. " * 10 + "\\end{abstract}"
                if section == "abstract"
                else f"\\section{{{serve.SECTION_LABELS[section]}}}\n" + "Complete academic content. " * 8
            )
            serve.write_json_atomic(
                serve.section_output_path(run_dir, section),
                {section: content},
            )
            project["sections"][section]["status"] = "ready"
        serve.write_json_atomic(
            serve.reference_output_path(run_dir),
            {"phase": "inserted", "references": [{"citation_key": "ReferenceOne"}]},
        )
        serve.reference_bib_path(run_dir).write_text(
            "@article{ReferenceOne, title={Reference One}, author={Author}, year={2024}}\n",
            encoding="utf-8",
        )
        project["research"]["reference_insertion"]["status"] = "ready"
        output_dir = serve.publication_dir(run_dir)
        source_root = output_dir / "source"
        source_root.mkdir(parents=True)
        main_tex = source_root / "main.tex"
        main_tex.write_text(
            "\\documentclass{article}\n\\begin{document}\nSample\n\\end{document}\n",
            encoding="utf-8",
        )
        project["publication"].update(
            {
                "status": "running",
                "template": {"name": "template.zip", "size": 100, "main_tex": "main.tex"},
            }
        )
        serve.save_project(project)
        adapted = (
            "\\documentclass{article}\n\\begin{document}\n\\begin{abstract}\n"
            + "Adapted abstract content. " * 10
            + "\\end{abstract}\n"
            + "\n".join(
                f"\\section{{{serve.SECTION_LABELS[section]}}}\n" + "Adapted academic content. " * 6
                for section in serve.BASE_SECTION_ORDER
            )
            + "\n\\bibliography{references}\n\\end{document}\n"
        )
        job = serve.PublicationJob(project["id"], "empty", "main.tex")
        with (
            patch.object(serve, "invoke_codex_json", return_value={"content": adapted}),
            patch.object(serve, "compile_latex", side_effect=RuntimeError("compiler unavailable")),
        ):
            serve.GENERATION_MANAGER._run_publication(job)

        updated = serve.load_project(project["id"])
        self.assertEqual(updated["publication"]["status"], "partial")
        self.assertTrue((output_dir / "manuscript-latex.zip").is_file())
        self.assertIsNone(updated["publication"]["pdf"])
        self.assertIn("compiler unavailable", updated["publication"]["error"])

    def test_generation_writes_section_and_marks_downstream_stale(self) -> None:
        project = self.create_project()
        run_dir = self.runs_root / project["id"]
        self.seed_research(project, "intro_research", self.intro_research_result())
        serve.write_json_atomic(
            serve.section_output_path(run_dir, "method"),
            {"method": "An existing method section with enough content to represent a previously generated downstream manuscript section."},
        )
        project["sections"]["method"]["status"] = "ready"
        project["sections"]["intro"]["status"] = "running"
        serve.save_project(project)
        job = serve.GenerationJob(project["id"], "intro", "ready")
        content = (
            "\\section{Introduction}\n\n"
            "This generated introduction contains enough precise academic English to pass the output validation and to provide stable context for the later manuscript sections."
        )
        with patch.object(serve, "invoke_codex", return_value=content):
            serve.GENERATION_MANAGER._run(job)
        updated = serve.load_project(project["id"])
        self.assertEqual(updated["sections"]["intro"]["status"], "ready")
        self.assertEqual(updated["sections"]["method"]["status"], "stale")
        self.assertEqual(
            json.loads(serve.section_output_path(run_dir, "intro").read_text(encoding="utf-8")),
            {"intro": content},
        )


if __name__ == "__main__":
    unittest.main()
