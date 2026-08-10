from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from autobench.admission_agent import build_admission_proposals
from autobench.catalog import load_catalog
from autobench.leakage import LeakageError, enforce_blind_input
from autobench.iteration_report import compare_iterations
from autobench.literature_audit import evaluate_literature_audit, prepare_literature_audit
from autobench.match_agent import score_candidate
from autobench.models import MethodInput, SearchHit
from autobench.pipeline import AutoBenchPipeline
from autobench.profile_agent import build_profile
from autobench.query_agent import build_queries
from autobench.review_gate import evaluate_review_matrix, evaluate_reviews
from autobench.review_workflow import prepare_review_bundle
from autobench.search_agent import _compile_query, _is_relevant
from autobench.synthesis_agent import synthesize_records, verify_synthetic_records
from autobench.workflow import run_workflow
from step15_audit_completion import determine_completion_status, load_automatic_reviews


ROOT = Path(__file__).resolve().parents[1]


class AutoBenchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog_path = ROOT / "configs/benchmark_catalog.json"
        cls.catalog = load_catalog(cls.catalog_path)
        cls.pipeline = AutoBenchPipeline(cls.catalog_path)

    def test_catalog_has_primary_sources_and_unique_ids(self) -> None:
        ids = [record.benchmark_id for record in self.catalog]
        self.assertGreaterEqual(len(ids), 15)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(record.source_url.startswith("https://arxiv.org/") for record in self.catalog))
        self.assertIn("leetcodehardgym", ids)
        self.assertIn("multipl_e", ids)
        self.assertIn("game_of_24", ids)
        self.assertIn("realtoxicityprompts", ids)
        self.assertIn("ambignq", ids)
        self.assertIn("triviaqa", ids)
        self.assertIn("svamp", ids)
        self.assertIn("tabmwp", ids)

    def test_holdout_feedback_generalizes_to_task_and_modality_boundaries(self) -> None:
        holdout_1 = MethodInput.from_dict(
            json.loads(
                (ROOT / "assets/input/untouched_holdout_cases/holdout_001.json").read_text()
            )
        )
        holdout_2 = MethodInput.from_dict(
            json.loads(
                (ROOT / "assets/input/untouched_holdout_2_cases/holdout_002.json").read_text()
            )
        )
        plan_1 = self.pipeline.run(holdout_1)
        plan_2 = self.pipeline.run(holdout_2)
        self.assertIn("math_reasoning", plan_1.profile.task_families)
        self.assertIn("online_store", plan_1.profile.environments)
        self.assertIn("selected_product", plan_1.profile.output_types)
        self.assertEqual(
            set(plan_1.selected_benchmarks),
            {"game_of_24", "hotpotqa", "humaneval", "mbpp", "webshop"},
        )
        self.assertNotIn("visualwebarena", plan_1.selected_benchmarks)
        self.assertNotIn("api_tool_use", plan_2.profile.task_families)
        self.assertEqual(
            plan_2.profile.task_benchmark_counts,
            {"knowledge_intensive_qa": 3, "math_reasoning": 3},
        )
        self.assertEqual(
            set(plan_2.selected_benchmarks),
            {
                "ambignq",
                "gsm8k",
                "hotpotqa",
                "realtoxicityprompts",
                "svamp",
                "tabmwp",
                "triviaqa",
            },
        )
        self.assertNotIn("toolbench", plan_2.selected_benchmarks)

    def test_completion_audit_loads_only_verified_automatic_reviews(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            review_root = root / "reviews"
            review_root.mkdir()
            (review_root / "automatic.json").write_text(
                json.dumps(
                    {
                        "reviewer": "AUTO_LITERATURE_EVALUATOR",
                        "status": "AUTOMATED_LITERATURE_AUDIT_CONFIRMED",
                        "evidence_class": "fresh_holdout",
                        "human_submission_required": False,
                        "case_count": 2,
                        "decision_counts": {"MATCH": 2, "PARTIAL": 0, "MISMATCH": 0},
                        "all_source_evidence_complete": True,
                        "all_blind_checks_passed": True,
                    }
                ),
                encoding="utf-8",
            )
            (review_root / "unrelated.json").write_text(
                json.dumps({"reviewer": "LEGACY_REVIEWER"}),
                encoding="utf-8",
            )
            reviews = load_automatic_reviews("reviews", workspace_root=root)
            self.assertEqual(len(reviews), 1)
            self.assertEqual(reviews[0]["artifact"], "reviews/automatic.json")
            self.assertEqual(reviews[0]["decision_counts"]["MATCH"], 2)

    def test_completion_status_preserves_automatic_quality_gaps(self) -> None:
        self.assertEqual(
            determine_completion_status(
                machine_ready=False,
                automatic_validation_complete=False,
                automatic_validation_passed=False,
            ),
            "MACHINE_WORKFLOW_NEEDS_ITERATION",
        )
        self.assertEqual(
            determine_completion_status(
                machine_ready=True,
                automatic_validation_complete=False,
                automatic_validation_passed=False,
            ),
            "AUTOMATIC_LITERATURE_REVIEW_PENDING",
        )
        self.assertEqual(
            determine_completion_status(
                machine_ready=True,
                automatic_validation_complete=True,
                automatic_validation_passed=False,
            ),
            "AUTOMATED_LITERATURE_VALIDATION_NEEDS_ITERATION",
        )
        self.assertEqual(
            determine_completion_status(
                machine_ready=True,
                automatic_validation_complete=True,
                automatic_validation_passed=True,
            ),
            "COMPLETE",
        )

    def test_blind_cases_have_no_catalog_alias(self) -> None:
        for path in sorted((ROOT / "assets/input/blind_cases").glob("case_*.json")):
            method_input = MethodInput.from_dict(json.loads(path.read_text(encoding="utf-8")))
            report = enforce_blind_input(method_input, self.catalog)
            self.assertTrue(report.passed, path.name)
            self.assertEqual(report.benchmark_alias_hits, [])

    def test_leakage_gate_rejects_benchmark_name(self) -> None:
        payload = MethodInput(
            case_id="leak",
            introduction="Evaluate the method on HotpotQA.",
            method="Retrieve evidence and answer questions.",
        )
        with self.assertRaises(LeakageError):
            enforce_blind_input(payload, self.catalog)

    def test_blind_runner_source_does_not_reference_hidden_label_directory(self) -> None:
        source = (ROOT / "step2_run_blind_matching.py").read_text(encoding="utf-8")
        hidden_directory_token = "blind" + "_gold"
        self.assertNotIn(hidden_directory_token, source)

    def test_literature_cases_recover_all_primary_benchmarks_in_top_six(self) -> None:
        for case_path in sorted((ROOT / "assets/input/blind_cases").glob("case_*.json")):
            method_input = MethodInput.from_dict(json.loads(case_path.read_text(encoding="utf-8")))
            plan = self.pipeline.run(method_input)
            gold_path = ROOT / "assets/input/blind_gold" / f"{method_input.case_id}.gold.json"
            gold = json.loads(gold_path.read_text(encoding="utf-8"))
            top_six = {candidate.benchmark_id for candidate in plan.ranked_candidates[:6]}
            self.assertTrue(set(gold["primary_benchmark_ids"]) <= top_six, method_input.case_id)
            self.assertEqual(plan.route, gold["expected_route"])
            self.assertEqual(plan.status, "AUTOMATIC_LITERATURE_CHECK_PENDING")
            self.assertFalse(plan.automatic_review["human_submission_required"])
            self.assertEqual(plan.human_review["status"], "NOT_REQUIRED")

    def test_paper_identity_is_revealed_only_in_post_run_gold(self) -> None:
        for case_path in sorted((ROOT / "assets/input/blind_cases").glob("case_*.json")):
            case = json.loads(case_path.read_text(encoding="utf-8"))
            gold_path = ROOT / "assets/input/blind_gold" / f"{case['case_id']}.gold.json"
            gold = json.loads(gold_path.read_text(encoding="utf-8"))
            visible_text = f"{case['introduction']} {case['method']}".casefold()
            self.assertNotIn(gold["source_title"].casefold(), visible_text)
            self.assertNotIn(gold["source_arxiv_id"], visible_text)
            self.assertTrue(gold["source_url"].startswith("https://arxiv.org/abs/"))
            self.assertTrue(gold["benchmark_evidence"])

    def test_every_gold_benchmark_name_is_hidden_from_matcher_input(self) -> None:
        catalog_by_id = {record.benchmark_id: record for record in self.catalog}
        for case_path in sorted((ROOT / "assets/input/blind_cases").glob("case_*.json")):
            case = json.loads(case_path.read_text(encoding="utf-8"))
            gold = json.loads(
                (ROOT / "assets/input/blind_gold" / f"{case['case_id']}.gold.json").read_text(
                    encoding="utf-8"
                )
            )
            visible = f"{case['introduction']} {case['method']}".casefold()
            hidden_names: set[str] = set()
            for evidence in gold["benchmark_evidence"]:
                benchmark_id = evidence.get("benchmark_id")
                if benchmark_id:
                    record = catalog_by_id[benchmark_id]
                    hidden_names.update((record.name, *record.aliases))
                if evidence.get("benchmark_name"):
                    hidden_names.add(evidence["benchmark_name"])
            for name in hidden_names:
                self.assertNotIn(name.casefold(), visible, (case["case_id"], name))
        react = json.loads((ROOT / "assets/input/blind_cases/case_001.json").read_text())
        self.assertIn("reactively", react["introduction"].casefold())
        self.assertNotIn("method_xively", react["introduction"].casefold())

    def test_base_adaptation_and_new_synthesis_routes(self) -> None:
        base = MethodInput(
            case_id="base",
            introduction=(
                "An agent follows a laboratory protocol in an interactive simulator and observes assay outcomes."
            ),
            method=(
                "It performs a sequential experimental procedure with reagent actions and long horizon planning."
            ),
        )
        novel = MethodInput(
            case_id="novel",
            introduction="A system generates polyphonic music from audio motifs.",
            method="It emits multi-track audio while preserving harmony, timbre, and rhythm.",
        )
        base_plan = self.pipeline.run(base)
        novel_plan = self.pipeline.run(novel)
        self.assertEqual(base_plan.route, "base_benchmark_adaptation")
        self.assertTrue(base_plan.synthesis_plan["required"])
        self.assertEqual(novel_plan.route, "new_benchmark_synthesis")

    def test_human_feedback_driven_profiles_and_portfolios(self) -> None:
        plans = {}
        for case_path in sorted((ROOT / "assets/input/blind_cases").glob("case_*.json")):
            method_input = MethodInput.from_dict(json.loads(case_path.read_text()))
            plans[method_input.case_id] = self.pipeline.run(method_input)
        self.assertNotIn("api_tool_use", plans["case_002"].profile.task_families)
        self.assertIn("code_debugging", plans["case_003"].profile.task_families)
        self.assertNotIn("image", plans["case_003"].profile.modalities)
        for case_id, plan in plans.items():
            gold = json.loads(
                (ROOT / "assets/input/blind_gold" / f"{case_id}.gold.json").read_text()
            )
            modeled_gold = set(gold["primary_benchmark_ids"] + gold["secondary_benchmark_ids"])
            self.assertTrue(modeled_gold <= set(plan.selected_benchmarks), case_id)
            self.assertEqual(set(plan.selected_benchmarks), set(plan.portfolio_roles))
        self.assertEqual(
            plans["case_003"].portfolio_roles["humanevalfix"],
            "core_task_coverage",
        )
        case_2 = plans["case_002"]
        self.assertIn("multilingual_code_generation", case_2.profile.capabilities)
        self.assertEqual(
            set(case_2.selected_benchmarks),
            {"alfworld", "hotpotqa", "humaneval", "leetcodehardgym", "mbpp", "multipl_e"},
        )
        self.assertNotIn("scienceworld", case_2.selected_benchmarks)
        self.assertEqual(case_2.route, "direct_portfolio")

    def test_task_balanced_ranking_preserves_cross_domain_holdout_coverage(self) -> None:
        visible = MethodInput.from_dict(
            json.loads(
                (ROOT / "assets/input/untouched_holdout_cases/holdout_001.json").read_text()
            )
        )
        gold = json.loads(
            (ROOT / "assets/input/untouched_holdout_gold/holdout_001.gold.json").read_text()
        )
        plan = self.pipeline.run(visible)
        top_six = {candidate.benchmark_id for candidate in plan.ranked_candidates[:6]}
        selected = set(plan.selected_benchmarks)
        self.assertGreaterEqual(len(top_six & set(gold["primary_benchmark_ids"])), 3)
        self.assertGreaterEqual(len(selected & set(gold["primary_benchmark_ids"])), 3)
        self.assertTrue({"humaneval", "mbpp"} <= top_six)

    def test_catalog_admission_resolves_the_second_holdout_coverage_gap(self) -> None:
        visible = MethodInput.from_dict(
            json.loads(
                (ROOT / "assets/input/untouched_holdout_2_cases/holdout_002.json").read_text()
            )
        )
        plan = self.pipeline.run(visible)
        self.assertEqual(plan.route, "direct_portfolio")
        self.assertEqual(plan.coverage_ratio, 1.0)
        self.assertEqual(
            set(plan.selected_benchmarks),
            {
                "triviaqa",
                "realtoxicityprompts",
                "gsm8k",
                "hotpotqa",
                "svamp",
                "ambignq",
                "tabmwp",
            },
        )
        self.assertEqual(len(plan.selected_benchmarks), 7)

    def test_hyphenated_task_phrases_use_the_same_profile_normalization(self) -> None:
        method_input = MethodInput(
            case_id="hyphen-normalization",
            introduction="We evaluate interactive question-answering and multi-hop reasoning.",
            method="The model searches external evidence before returning an answer.",
        )
        profile = build_profile(method_input)
        self.assertIn("knowledge_intensive_qa", profile.task_families)
        self.assertIn("question answering", profile.evidence_terms["task:knowledge_intensive_qa"])
        self.assertIn("multi-hop", profile.evidence_terms["task:knowledge_intensive_qa"])

    def test_online_literature_hit_contributes_to_candidate_score(self) -> None:
        method_input = MethodInput(
            case_id="online-evidence",
            introduction="An agent answers multi-hop questions using external evidence.",
            method="It retrieves supporting documents before returning a short answer.",
        )
        profile = self.pipeline.run(method_input).profile
        record = next(item for item in self.catalog if item.benchmark_id == "hotpotqa")
        baseline = score_candidate(profile, record, [])
        hit = SearchHit(
            title="HotpotQA benchmark analysis",
            summary="An evaluation of multi-hop question answering with supporting evidence.",
            url="https://arxiv.org/abs/TEST",
            query="multi-hop question answering benchmark",
        )
        with_hit = score_candidate(profile, record, [hit])
        self.assertEqual(with_hit.component_scores["literature"], 1.0)
        self.assertGreater(with_hit.score, baseline.score)
        self.assertIn(hit.url, with_hit.evidence)

    def test_topical_online_hit_without_benchmark_name_adds_partial_evidence(self) -> None:
        method_input = MethodInput(
            case_id="topical-evidence",
            introduction="An agent answers multi-hop questions from retrieved documents.",
            method="It returns an answer and supporting evidence.",
        )
        profile = build_profile(method_input)
        record = next(item for item in self.catalog if item.benchmark_id == "hotpotqa")
        baseline = score_candidate(profile, record, [])
        hit = SearchHit(
            title="A New Multi-hop Question Answering Evaluation",
            summary="We study evidence retrieval without naming an existing dataset.",
            url="https://arxiv.org/abs/9999.00002",
            query="multi-hop question answering benchmark",
        )
        with_hit = score_candidate(profile, record, [hit])
        self.assertEqual(with_hit.component_scores["literature"], 0.5)
        self.assertGreater(with_hit.score, baseline.score)
        self.assertIn(hit.url, with_hit.evidence)

    def test_benchmark_like_online_hit_becomes_review_only_admission_proposal(self) -> None:
        method_input = MethodInput(
            case_id="admission-proposal",
            introduction="An agent answers knowledge-intensive multi-hop questions.",
            method="It retrieves evidence and returns a short grounded answer.",
        )
        profile = build_profile(method_input)
        benchmark_hit = SearchHit(
            title="ExampleQA: A Multi-hop Question Answering Benchmark",
            summary="We introduce a dataset for evaluating evidence-grounded question answering.",
            url="https://arxiv.org/abs/9999.00003",
            query='"knowledge intensive qa" benchmark dataset evaluation text',
        )
        ordinary_hit = SearchHit(
            title="Improving Question Answering with Retrieval",
            summary="We analyze a retrieval model and report its accuracy.",
            url="https://arxiv.org/abs/9999.00004",
            query=benchmark_hit.query,
        )
        proposals = build_admission_proposals(profile, [benchmark_hit, ordinary_hit])
        self.assertEqual(len(proposals), 1)
        proposal = proposals[0]
        self.assertEqual(proposal.proposal_id, "arxiv_9999_00003")
        self.assertEqual(proposal.matched_task_families, ["knowledge_intensive_qa"])
        self.assertFalse(proposal.selection_eligible)
        self.assertEqual(proposal.status, "CATALOG_ADMISSION_REVIEW_REQUIRED")
        self.assertIn("official_metrics", proposal.missing_required_fields)
        self.assertIn("license_note", proposal.missing_required_fields)

        with patch("autobench.pipeline.search_arxiv", return_value=[benchmark_hit]):
            plan = self.pipeline.run(method_input, online_search=True)
        payload = plan.to_dict()
        self.assertEqual(len(payload["catalog_admission_proposals"]), 1)
        self.assertNotIn(proposal.proposal_id, payload["selected_benchmarks"])
        self.assertEqual(
            payload["synthesis_plan"]["catalog_admission_proposals"],
            [proposal.proposal_id],
        )

    def test_benchmarking_study_is_not_a_catalog_resource_proposal(self) -> None:
        profile = build_profile(
            MethodInput(
                case_id="benchmarking-verb",
                introduction="A model performs question-answering and toxicity reduction.",
                method="It retrieves evidence, checks each answer, and rewrites toxic content.",
            )
        )
        study = SearchHit(
            title="Benchmarking and Improving Generator-Validator Consistency",
            summary="We analyze model consistency across several existing datasets.",
            url="https://arxiv.org/abs/9999.00005",
            query='"knowledge intensive qa" benchmark dataset evaluation text',
        )
        method_paper = SearchHit(
            title="Causal Detoxification for Language Models",
            summary="We introduce a method evaluated on several toxicity datasets.",
            url="https://arxiv.org/abs/9999.00006",
            query='"toxicity reduction" benchmark dataset evaluation text',
        )
        self.assertEqual(build_admission_proposals(profile, [study, method_paper]), [])

    def test_catalog_admission_maps_search_alias_back_to_profile_task(self) -> None:
        profile = build_profile(
            MethodInput(
                case_id="alias-admission",
                introduction="The method performs toxicity reduction.",
                method="It critiques and rewrites toxic content.",
            )
        )
        hit = SearchHit(
            title="PromptResource: Evaluating Toxic Degeneration",
            summary="We create and release PromptResource, a dataset of scored text prompts.",
            url="https://arxiv.org/abs/9999.00007",
            query='"toxic degeneration" benchmark dataset evaluation text',
        )
        proposals = build_admission_proposals(profile, [hit])
        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0].matched_task_families, ["toxicity_reduction"])

    def test_uncovered_explicit_task_forces_adaptation_and_synthesis(self) -> None:
        method_input = MethodInput(
            case_id="mixed-covered-uncovered",
            introduction=(
                "The system performs question-answering and follows a laboratory protocol "
                "for a new wet lab assay."
            ),
            method=(
                "It retrieves evidence, plans reagent actions, observes measurements, "
                "and revises the experimental procedure."
            ),
        )
        plan = self.pipeline.run(method_input)
        self.assertIn("knowledge_intensive_qa", plan.profile.task_families)
        self.assertIn("scientific_experiment_planning", plan.profile.task_families)
        self.assertEqual(plan.route, "base_benchmark_adaptation")
        self.assertTrue(plan.synthesis_plan["required"])
        self.assertIn("scientific_experiment_planning", plan.synthesis_plan["target_task_families"])

    def test_synthetic_records_preserve_provenance_and_pending_state(self) -> None:
        records = [{"id": "r1", "input": "x", "expected_output": "y"}]
        drafts = synthesize_records(records, "base_benchmark", "train", "interaction_wrapper")
        self.assertEqual(drafts[0]["source_record_ids"], ["r1"])
        self.assertEqual(drafts[0]["source_split"], "train")
        self.assertEqual(drafts[0]["automatic_validation_status"], "PENDING")
        self.assertEqual(drafts[0]["input"]["allowed_actions"], ["inspect", "submit"])
        self.assertEqual(drafts[0]["expected_output"], {"final_answer": "y"})
        self.assertIn("source_expected_output_preserved", drafts[0]["deterministic_checks"])

    def test_synthesis_rejects_test_sources_and_verifies_exact_gold(self) -> None:
        records = [{"id": "r1", "input": "x", "expected_output": "y"}]
        with self.assertRaisesRegex(ValueError, "at least one"):
            synthesize_records([], "base_benchmark", "train", "interaction_wrapper")
        with self.assertRaisesRegex(ValueError, "test"):
            synthesize_records(records, "base_benchmark", "hidden_test", "interaction_wrapper")
        drafts = synthesize_records(records, "base_benchmark", "train", "interaction_wrapper")
        verification = verify_synthetic_records(
            records,
            drafts,
            "base_benchmark",
            "train",
            "interaction_wrapper",
        )
        self.assertEqual(verification["status"], "PASS")
        self.assertEqual(verification["verified_expected_outputs"], 1)
        drafts[0]["expected_output"] = {"final_answer": "changed"}
        with self.assertRaisesRegex(ValueError, "source gold"):
            verify_synthetic_records(
                records,
                drafts,
                "base_benchmark",
                "train",
                "interaction_wrapper",
            )

    def test_single_command_workflow_covers_all_three_routes(self) -> None:
        direct = MethodInput.from_dict(
            json.loads((ROOT / "assets/input/blind_cases/case_001.json").read_text())
        )
        base = MethodInput(
            case_id="workflow-base",
            introduction=(
                "An agent follows a laboratory protocol in an interactive simulator and observes assay outcomes."
            ),
            method=(
                "It performs a sequential experimental procedure with reagent actions and long horizon planning."
            ),
        )
        novel = MethodInput(
            case_id="workflow-novel",
            introduction="A system generates polyphonic music from audio motifs.",
            method="It emits multi-track audio while preserving harmony, timbre, and rhythm.",
        )
        records = [
            {
                "id": "train-001",
                "input": {"goal": "prepare sample A"},
                "expected_output": {"state": "prepared"},
                "counterfactual": {
                    "input": {"goal": "prepare sample B"},
                    "expected_output": {"state": "prepared-B"},
                    "deterministic_check": "sample_b_state_matches",
                },
            },
            {
                "id": "train-002",
                "input": {"goal": "measure sample A"},
                "expected_output": {"state": "measured"},
                "counterfactual": {
                    "input": {"goal": "measure sample B"},
                    "expected_output": {"state": "measured-B"},
                    "deterministic_check": "sample_b_measurement_matches",
                },
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records_path = root / "base_records.jsonl"
            records_path.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            direct_manifest = run_workflow(
                direct,
                self.catalog_path,
                root / "direct",
            )
            base_manifest = run_workflow(
                base,
                self.catalog_path,
                root / "base",
                base_records_path=records_path,
                source_benchmark="scienceworld",
                source_split="train",
                transformations=(
                    "interaction_wrapper",
                    "compositional_recombination",
                    "counterfactual_perturbation",
                ),
            )
            novel_manifest = run_workflow(
                novel,
                self.catalog_path,
                root / "novel",
            )
            self.assertEqual(direct_manifest["route"], "direct_portfolio")
            self.assertEqual(direct_manifest["synthesis_execution"]["status"], "NOT_REQUIRED")
            self.assertEqual(base_manifest["route"], "base_benchmark_adaptation")
            self.assertEqual(
                base_manifest["synthesis_execution"]["status"],
                "DRAFTS_READY_FOR_AUTOMATIC_VALIDATION",
            )
            self.assertEqual(
                [item["records"] for item in base_manifest["synthesis_execution"]["modules"]],
                [2, 1, 2],
            )
            base_plan = json.loads((root / "base/benchmark_plan.json").read_text())
            self.assertIn("interactive_environment", base_plan["profile"]["interactions"])
            self.assertNotIn("static", base_plan["profile"]["interactions"])
            self.assertEqual(novel_manifest["route"], "new_benchmark_synthesis")
            self.assertEqual(
                novel_manifest["synthesis_execution"]["status"],
                "BASE_RECORDS_REQUIRED",
            )
            self.assertEqual(
                novel_manifest["synthesis_execution"]["target_task_families"],
                ["audio_music_generation"],
            )
            novel_plan = json.loads((root / "novel/benchmark_plan.json").read_text())
            self.assertIn("audio", novel_plan["profile"]["modalities"])
            self.assertIn("generated_audio", novel_plan["profile"]["output_types"])
            self.assertEqual(
                novel_plan["profile"]["uncovered_task_families"],
                ["audio_music_generation"],
            )
            self.assertTrue(
                any("audio music generation" in query for query in novel_plan["search_queries"])
            )
            for folder in ("direct", "base", "novel"):
                self.assertTrue((root / folder / "workflow_manifest.json").is_file())
                self.assertTrue((root / folder / "automatic_review_input.json").is_file())
                manifest = json.loads((root / folder / "workflow_manifest.json").read_text())
                self.assertFalse(manifest["human_submission_required"])
                self.assertIn("automatic_validation", manifest)
                self.assertFalse((root / folder / "human_review").exists())

    def test_human_review_gate_requires_independent_reviewers(self) -> None:
        scores = {
            "construct_alignment": 4,
            "task_representativeness": 4,
            "metric_validity": 4,
            "data_quality": 4,
            "leakage_control": 5,
            "execution_feasibility": 4,
        }
        one = [
            {
                "reviewer_slot": "REVIEWER_1",
                "reviewer_id": "domain-expert-a",
                "scores": scores,
                "provenance_confirmed": True,
                "independence_attested": True,
                "decision": "APPROVE",
                "notes": "The benchmark directly measures the method capability.",
            }
        ]
        two = one + [
            {
                "reviewer_slot": "REVIEWER_2",
                "reviewer_id": "domain-expert-b",
                "scores": scores,
                "provenance_confirmed": True,
                "independence_attested": True,
                "decision": "APPROVE",
                "notes": "The tasks and metrics match the intended evaluation construct.",
            }
        ]
        self.assertEqual(evaluate_reviews(one)["status"], "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(evaluate_reviews(two)["status"], "APPROVED")

    def test_explicit_human_rejection_overrides_high_scores(self) -> None:
        scores = {dimension: 5 for dimension in (
            "construct_alignment",
            "task_representativeness",
            "metric_validity",
            "data_quality",
            "leakage_control",
            "execution_feasibility",
        )}
        reviews = [
            {
                "reviewer_slot": slot,
                "reviewer_id": reviewer,
                "scores": scores,
                "provenance_confirmed": True,
                "independence_attested": True,
                "decision": decision,
                "notes": "The written decision is intentional and evidence based.",
            }
            for slot, reviewer, decision in (
                ("REVIEWER_1", "domain-expert-a", "APPROVE"),
                ("REVIEWER_2", "domain-expert-b", "REJECT"),
            )
        ]
        self.assertEqual(evaluate_reviews(reviews)["status"], "REJECTED")

    def test_incomplete_human_template_stays_pending(self) -> None:
        reviews = [
            {
                "reviewer_id": "R1",
                "scores": {dimension: None for dimension in (
                    "construct_alignment",
                    "task_representativeness",
                    "metric_validity",
                    "data_quality",
                    "leakage_control",
                    "execution_feasibility",
                )},
                "provenance_confirmed": None,
            },
            {
                "reviewer_id": "R2",
                "scores": {},
                "provenance_confirmed": None,
            },
        ]
        self.assertEqual(evaluate_reviews(reviews)["status"], "HUMAN_REVIEW_REQUIRED")

    def test_arxiv_query_compiler_keeps_task_phrase_and_filters_noise(self) -> None:
        query, core = _compile_query('"code issue resolution" benchmark dataset evaluation code')
        self.assertIn('all:"code issue resolution"', query)
        self.assertIn("all:benchmark", query)
        self.assertEqual(core, {"issue", "resolution"})
        self.assertTrue(_is_relevant("A benchmark for issue resolution", "repository repair", core))
        self.assertFalse(_is_relevant("Hydrodynamic decay", "particle physics", core))

    def test_query_planner_expands_task_aliases_without_paper_identity(self) -> None:
        profile = build_profile(
            MethodInput(
                case_id="toxicity-query",
                introduction="The system performs toxicity reduction for generated text.",
                method="It critiques and rewrites toxic content.",
            )
        )
        queries = build_queries(profile)
        self.assertTrue(any('"toxic degeneration"' in query for query in queries))
        self.assertTrue(any('"text detoxification"' in query for query in queries))
        self.assertTrue(all("CRITIC" not in query for query in queries))

    def test_review_matrix_never_hides_an_incomplete_item(self) -> None:
        complete_scores = {
            "construct_alignment": 4,
            "task_representativeness": 4,
            "metric_validity": 4,
            "data_quality": 4,
            "leakage_control": 4,
            "execution_feasibility": 4,
        }
        rows = [
            {
                "case_id": "c1",
                "benchmark_id": "b1",
                "reviewer_slot": slot,
                "reviewer_id": reviewer,
                "scores": complete_scores,
                "provenance_confirmed": True,
                "independence_attested": True,
                "decision": "APPROVE",
                "notes": "The proposal is aligned and executable.",
            }
            for slot, reviewer in (
                ("REVIEWER_1", "domain-expert-a"),
                ("REVIEWER_2", "domain-expert-b"),
            )
        ]
        rows.extend(
            [
                {
                    "case_id": "c1",
                    "benchmark_id": "b2",
                    "reviewer_slot": slot,
                    "reviewer_id": reviewer,
                    "scores": {},
                    "provenance_confirmed": None,
                    "independence_attested": True,
                    "decision": None,
                    "notes": None,
                }
                for slot, reviewer in (
                    ("REVIEWER_1", "domain-expert-a"),
                    ("REVIEWER_2", "domain-expert-b"),
                )
            ]
        )
        verdict = evaluate_review_matrix(rows)
        self.assertEqual(verdict["status"], "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(len(verdict["items"]), 2)
        self.assertEqual(verdict["items"][0]["status"], "APPROVED")

    def test_frozen_scope_prevents_omitted_item_approval(self) -> None:
        scores = {dimension: 4 for dimension in (
            "construct_alignment",
            "task_representativeness",
            "metric_validity",
            "data_quality",
            "leakage_control",
            "execution_feasibility",
        )}
        rows = [
            {
                "case_id": "c1",
                "benchmark_id": "b1",
                "reviewer_slot": slot,
                "reviewer_id": reviewer,
                "scores": scores,
                "provenance_confirmed": True,
                "independence_attested": True,
                "decision": "APPROVE",
                "notes": "The submitted item meets every suitability requirement.",
            }
            for slot, reviewer in (
                ("REVIEWER_1", "domain-expert-a"),
                ("REVIEWER_2", "domain-expert-b"),
            )
        ]
        verdict = evaluate_review_matrix(rows, expected_pairs={("c1", "b1"), ("c1", "b2")})
        self.assertEqual(verdict["status"], "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(verdict["expected_item_count"], 2)
        self.assertEqual(verdict["submitted_item_count"], 1)
        self.assertEqual(verdict["items"][1]["reason"], "review rows are missing for this frozen-scope item")

    def test_independent_html_assignments_include_full_context_without_gold(self) -> None:
        case_path = ROOT / "assets/input/blind_cases/case_001.json"
        method_input = MethodInput.from_dict(json.loads(case_path.read_text(encoding="utf-8")))
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            plan = self.pipeline.run(method_input)
            plan_paths = self.pipeline.write_outputs(plan, tmp / "plan")
            bundle = prepare_review_bundle([plan_paths["json"]], tmp / "review")
            self.assertEqual(bundle["item_count"], len(plan.selected_benchmarks))
            first = json.loads(Path(bundle["assignments"]["REVIEWER_1"]).read_text(encoding="utf-8"))
            second = json.loads(Path(bundle["assignments"]["REVIEWER_2"]).read_text(encoding="utf-8"))
            self.assertEqual(first["reviewer_slot"], "REVIEWER_1")
            self.assertEqual(second["reviewer_slot"], "REVIEWER_2")
            self.assertEqual(first["items"], second["items"])
            self.assertEqual(first["items"][0]["visible_input"]["method"], method_input.method)
            self.assertFalse(first["items"][0]["matching_provenance"]["blind_gold_loaded"])
            serialized = json.dumps(first, ensure_ascii=False)
            self.assertNotIn("primary_benchmark_ids", serialized)
            self.assertNotIn("/Users/", serialized)
            html_text = Path(bundle["html_packets"]["REVIEWER_1"]).read_text(encoding="utf-8")
            self.assertIn("assignment-data", html_text)
            self.assertIn("校验并下载 JSON", html_text)

    def test_source_revealed_literature_audit_contains_direct_comparison(self) -> None:
        evaluation = ROOT / "assets/output/blind_evaluation.json"
        with tempfile.TemporaryDirectory() as raw_tmp:
            result = prepare_literature_audit(evaluation, raw_tmp, workspace_root=ROOT)
            audit = json.loads(Path(result["audit_json"]).read_text(encoding="utf-8"))
            self.assertEqual(len(audit["cases"]), 3)
            react = next(case for case in audit["cases"] if case["case_id"] == "case_001")
            self.assertEqual(react["source_arxiv_id"], "2210.03629")
            self.assertEqual(react["source_input_sections"]["introduction"], ["Introduction"])
            self.assertEqual(
                react["source_input_sections"]["method"],
                ["ReAct: Synergizing Reasoning + Acting"],
            )
            self.assertEqual(
                set(react["comparison"]["selected_primary_matches"]),
                {"alfworld", "fever", "hotpotqa", "webshop"},
            )
            self.assertEqual(react["comparison"]["primary_missing_from_selected"], [])
            self.assertEqual(
                set(react["comparison"]["selected_not_used_in_paper"]),
                {"triviaqa", "webarena"},
            )
            html_text = Path(result["audit_html"]).read_text(encoding="utf-8")
            self.assertIn("ReAct: Synergizing Reasoning and Acting in Language Models", html_text)
            self.assertIn("https://arxiv.org/abs/2210.03629", html_text)
            self.assertIn("Benchmarks actually used by the paper", html_text)

    def test_untouched_holdout_was_frozen_with_separate_gold(self) -> None:
        case_root = ROOT / "assets/input/untouched_holdout_cases"
        gold_root = ROOT / "assets/input/untouched_holdout_gold"
        manifest = json.loads((case_root / "freeze_manifest.json").read_text(encoding="utf-8"))
        self.assertTrue(manifest["paper_selected_before_matching"])
        self.assertTrue(manifest["fixture_frozen_before_first_matching"])
        self.assertFalse(manifest["gold_directory_passed_to_matcher"])

        visible = json.loads((case_root / "holdout_001.json").read_text(encoding="utf-8"))
        gold = json.loads((gold_root / "holdout_001.gold.json").read_text(encoding="utf-8"))
        self.assertEqual(set(visible), {"case_id", "introduction", "method", "constraints"})
        self.assertTrue(enforce_blind_input(MethodInput.from_dict(visible), self.catalog).passed)

        visible_text = f"{visible['introduction']} {visible['method']}".casefold()
        hidden_names = [
            gold["source_title"],
            gold["source_arxiv_id"],
            "LATS",
            "HotPotQA",
            "HumanEval",
            "MBPP",
            "WebShop",
            "Game of 24",
        ]
        for name in hidden_names:
            self.assertNotIn(name.casefold(), visible_text)

    def test_untouched_holdout_first_result_is_preserved(self) -> None:
        output_root = ROOT / "assets/output/untouched_holdout"
        record = json.loads((output_root / "first_run_record.json").read_text(encoding="utf-8"))
        evaluation = json.loads(
            (output_root / "first_run_evaluation.json").read_text(encoding="utf-8")
        )
        run_manifest = json.loads(
            (output_root / "runs/run_manifest.json").read_text(encoding="utf-8")
        )
        self.assertTrue(record["fixture_frozen_before_first_matching"])
        self.assertFalse(record["matcher_changed_after_gold_reveal"])
        self.assertEqual(record["evaluation_exit_status"], 1)
        self.assertEqual(record["first_run_verdict"], "NEEDS_ITERATION")
        self.assertEqual(evaluation["aggregate"]["mean_primary_recall_at_5"], 0.25)
        self.assertEqual(evaluation["aggregate"]["mean_primary_recall_at_6"], 0.5)
        self.assertEqual(evaluation["aggregate"]["mean_selected_modeled_recall"], 0.75)
        self.assertTrue(evaluation["aggregate"]["all_leakage_checks_passed"])
        self.assertFalse(evaluation["aggregate"]["any_matcher_loaded_hidden_labels"])
        self.assertEqual([item["case_id"] for item in run_manifest["cases"]], ["holdout_001"])
        self.assertFalse(run_manifest["cases"][0]["hidden_labels_present_in_sandbox"])

    def test_untouched_holdout_has_an_independent_human_audit(self) -> None:
        audit_root = ROOT / "assets/output/untouched_holdout/human_audit"
        audit = json.loads((audit_root / "literature_audit.json").read_text(encoding="utf-8"))
        pending = json.loads((audit_root / "pending_verdict.json").read_text(encoding="utf-8"))
        template = json.loads(
            (audit_root / "literature_audit_review_template.json").read_text(encoding="utf-8")
        )
        self.assertEqual([case["case_id"] for case in audit["cases"]], ["holdout_001"])
        self.assertEqual(audit["iteration"], 2)
        self.assertEqual(
            audit["submission_filename"],
            "literature_audit_submission_holdout_1_round_2.json",
        )
        self.assertEqual(audit["cases"][0]["carried_review_evidence"]["from_iteration"], 1)
        self.assertEqual(pending["status"], "HUMAN_LITERATURE_AUDIT_REQUIRED")
        self.assertEqual(pending["pending_case_ids"], ["holdout_001"])
        self.assertEqual([item["case_id"] for item in template["reviews"]], ["holdout_001"])
        html_text = (audit_root / "literature_audit.html").read_text(encoding="utf-8")
        self.assertIn("Auto-Bench Untouched Holdout Literature Audit", html_text)
        self.assertIn("literature_audit_submission_holdout_1_round_2.json", html_text)
        self.assertNotIn("/Users/", html_text)

    def test_second_holdout_was_frozen_before_the_first_revision_run(self) -> None:
        case_root = ROOT / "assets/input/untouched_holdout_2_cases"
        gold_root = ROOT / "assets/input/untouched_holdout_2_gold"
        manifest = json.loads((case_root / "freeze_manifest.json").read_text(encoding="utf-8"))
        visible = json.loads((case_root / "holdout_002.json").read_text(encoding="utf-8"))
        gold = json.loads((gold_root / "holdout_002.gold.json").read_text(encoding="utf-8"))
        self.assertTrue(manifest["paper_selected_before_holdout_001_driven_matcher_revision"])
        self.assertTrue(manifest["fixture_frozen_before_matcher_revision"])
        self.assertTrue(manifest["matcher_has_not_seen_holdout_002_gold"])
        self.assertFalse(manifest["gold_directory_passed_to_matcher"])
        self.assertEqual(set(visible), {"case_id", "introduction", "method", "constraints"})
        self.assertTrue(enforce_blind_input(MethodInput.from_dict(visible), self.catalog).passed)

        visible_text = f"{visible['introduction']} {visible['method']}"
        hidden_names = [
            gold["source_title"],
            gold["source_arxiv_id"],
            "CRITIC",
            "HotPotQA",
            "GSM8K",
            *gold["unmodeled_benchmarks"],
        ]
        for name in hidden_names:
            pattern = r"(?<![A-Za-z0-9])" + re.escape(name) + r"(?![A-Za-z0-9])"
            self.assertIsNone(re.search(pattern, visible_text, re.IGNORECASE), name)

    def test_second_holdout_first_result_is_preserved_before_feedback_changes(self) -> None:
        output_root = ROOT / "assets/output/untouched_holdout_2"
        record = json.loads((output_root / "first_run_record.json").read_text(encoding="utf-8"))
        evaluation = json.loads(
            (output_root / "first_run_evaluation.json").read_text(encoding="utf-8")
        )
        case = evaluation["cases"][0]
        self.assertEqual(record["matcher_revision_basis"], [
            "assets/output/untouched_holdout/first_run_evaluation.json"
        ])
        self.assertFalse(record["matcher_changed_after_holdout_002_gold_reveal"])
        self.assertEqual(record["evaluation_exit_status"], 1)
        self.assertEqual(evaluation["aggregate"]["mean_primary_recall_at_5"], 1.0)
        self.assertEqual(evaluation["aggregate"]["mean_primary_recall_at_6"], 1.0)
        self.assertEqual(evaluation["aggregate"]["mean_selected_modeled_recall"], 1.0)
        self.assertEqual(evaluation["aggregate"]["route_accuracy"], 0.0)
        self.assertEqual(case["comparison"]["selected_primary_matches"], ["hotpotqa", "gsm8k"])
        self.assertEqual(case["route"], "direct_portfolio")
        self.assertEqual(case["expected_route"], "base_benchmark_adaptation")
        self.assertTrue(case["leakage_passed"])
        self.assertFalse(case["matcher_loaded_hidden_labels"])

    def test_second_holdout_has_an_independent_human_audit(self) -> None:
        audit_root = ROOT / "assets/output/untouched_holdout_2/human_audit"
        audit = json.loads((audit_root / "literature_audit.json").read_text(encoding="utf-8"))
        pending = json.loads((audit_root / "pending_verdict.json").read_text(encoding="utf-8"))
        self.assertEqual([case["case_id"] for case in audit["cases"]], ["holdout_002"])
        self.assertEqual(audit["submission_filename"], "literature_audit_submission_holdout_2.json")
        self.assertEqual(pending["status"], "HUMAN_LITERATURE_AUDIT_REQUIRED")
        self.assertEqual(pending["pending_case_ids"], ["holdout_002"])
        html_text = (audit_root / "literature_audit.html").read_text(encoding="utf-8")
        self.assertIn("Auto-Bench Untouched Holdout 002 Literature Audit", html_text)
        self.assertNotIn("/Users/", html_text)

    def test_second_holdout_catalog_admission_resolves_missing_domain(self) -> None:
        visible = json.loads(
            (ROOT / "assets/input/untouched_holdout_2_cases/holdout_002.json").read_text(
                encoding="utf-8"
            )
        )
        plan = self.pipeline.run(MethodInput.from_dict(visible))
        self.assertIn("toxicity_reduction", plan.profile.task_families)
        self.assertEqual(plan.route, "direct_portfolio")
        self.assertIn("realtoxicityprompts", plan.selected_benchmarks)
        self.assertFalse(plan.synthesis_plan["required"])
        self.assertEqual(plan.synthesis_plan["target_task_families"], [])

    def test_current_second_holdout_plan_has_a_separate_human_gate(self) -> None:
        audit_root = ROOT / "assets/output/untouched_holdout_2/current_human_audit"
        audit = json.loads((audit_root / "literature_audit.json").read_text(encoding="utf-8"))
        pending = json.loads((audit_root / "pending_verdict.json").read_text(encoding="utf-8"))
        self.assertEqual([case["case_id"] for case in audit["cases"]], ["holdout_002"])
        self.assertEqual(
            audit["submission_filename"],
            "literature_audit_submission_holdout_2_round_2.json",
        )
        self.assertEqual(audit["iteration"], 2)
        self.assertEqual(audit["cases"][0]["carried_review_evidence"]["from_iteration"], 1)
        self.assertEqual(audit["aggregate"]["route_accuracy"], 1.0)
        self.assertEqual(pending["status"], "HUMAN_LITERATURE_AUDIT_REQUIRED")

    def test_literature_audit_requires_complete_human_comparison(self) -> None:
        scope = json.loads(
            (ROOT / "assets/output/literature_audit/literature_audit.json").read_text(encoding="utf-8")
        )
        blank = {"reviewer_id": None, "reviews": []}
        self.assertEqual(
            evaluate_literature_audit(blank, scope)["status"],
            "HUMAN_LITERATURE_AUDIT_REQUIRED",
        )
        null_notes = {
            "audit_id": scope["audit_id"],
            "iteration": scope["iteration"],
            "scope_snapshot": scope["submission_scope_snapshot"],
            "reviewer_id": "research-owner",
            "reviews": [
                {
                    "case_id": case["case_id"],
                    "source_verified": True,
                    "actual_benchmarks_verified": True,
                    "comparison_reviewed": True,
                    "route_and_fallback_reviewed": True,
                    "decision": "MATCH",
                    "notes": None,
                }
                for case in scope["cases"]
            ],
        }
        self.assertEqual(
            evaluate_literature_audit(null_notes, scope)["status"],
            "HUMAN_LITERATURE_AUDIT_REQUIRED",
        )
        submission = {
            "audit_id": scope["audit_id"],
            "iteration": scope["iteration"],
            "scope_snapshot": scope["submission_scope_snapshot"],
            "reviewer_id": "research-owner",
            "reviews": [
                {
                    "case_id": case["case_id"],
                    "source_verified": True,
                    "actual_benchmarks_verified": True,
                    "comparison_reviewed": True,
                    "route_and_fallback_reviewed": True,
                    "decision": "MATCH",
                    "notes": "The paper evidence and recommendation comparison were checked.",
                }
                for case in scope["cases"]
            ],
        }
        self.assertEqual(
            evaluate_literature_audit(submission, scope)["status"],
            "LITERATURE_AUDIT_CONFIRMED",
        )
        submission["reviews"][0]["route_and_fallback_reviewed"] = False
        self.assertEqual(
            evaluate_literature_audit(submission, scope)["status"],
            "LITERATURE_AUDIT_CONFIRMED",
        )
        stale_submission = json.loads(json.dumps(submission))
        stale_submission["audit_id"] = "earlier_round"
        stale_verdict = evaluate_literature_audit(stale_submission, scope)
        self.assertEqual(stale_verdict["status"], "HUMAN_LITERATURE_AUDIT_REQUIRED")
        self.assertIn("scope does not match", stale_verdict["reason"])
        stale_snapshot = json.loads(json.dumps(submission))
        stale_snapshot["scope_snapshot"][0]["selected_benchmark_ids"] = ["older_selection"]
        snapshot_verdict = evaluate_literature_audit(stale_snapshot, scope)
        self.assertEqual(snapshot_verdict["status"], "HUMAN_LITERATURE_AUDIT_REQUIRED")
        self.assertIn("snapshot does not match", snapshot_verdict["reason"])
        submission["reviews"][0]["decision"] = "PARTIAL"
        self.assertEqual(
            evaluate_literature_audit(submission, scope)["status"],
            "LITERATURE_AUDIT_PARTIAL",
        )
        submission["reviews"][0]["decision"] = "MISMATCH"
        self.assertEqual(
            evaluate_literature_audit(submission, scope)["status"],
            "LITERATURE_AUDIT_MISMATCH",
        )

    def test_round_comparison_preserves_human_feedback_and_exposes_remaining_gap(self) -> None:
        history = ROOT / "assets/output/literature_audit/history/round_1"
        round_2 = ROOT / "assets/output/literature_audit/history/round_2"
        previous = json.loads((history / "blind_evaluation.json").read_text(encoding="utf-8"))
        current = json.loads((round_2 / "blind_evaluation.json").read_text(encoding="utf-8"))
        verdict = json.loads((history / "final_verdict.json").read_text(encoding="utf-8"))
        comparison = compare_iterations(previous, current, verdict)
        self.assertEqual(comparison["aggregate"]["previous_human_status"], "LITERATURE_AUDIT_PARTIAL")
        case_2 = next(case for case in comparison["cases"] if case["case_id"] == "case_002")
        self.assertEqual(case_2["previous_human_decision"], "PARTIAL")
        self.assertEqual(case_2["before"]["selected_matches"], ["humaneval", "hotpotqa"])
        self.assertEqual(case_2["after"]["selected_missing"], [])
        self.assertEqual(case_2["unmodeled_gold"], ["LeetcodeHardGym", "MultiPL-E language ports"])
        with tempfile.TemporaryDirectory() as raw_tmp:
            result = prepare_literature_audit(
                round_2 / "blind_evaluation.json",
                raw_tmp,
                workspace_root=ROOT,
                iteration=2,
                iteration_comparison=comparison,
                prior_audit_path=(
                    ROOT / "assets/output/literature_audit/history/round_1/literature_audit.json"
                ),
                prior_submission_path=(
                    ROOT / "assets/output/literature_audit/history/round_1/literature_audit_submission.json"
                ),
            )
            audit = json.loads(Path(result["audit_json"]).read_text(encoding="utf-8"))
            template = json.loads(Path(result["review_template"]).read_text(encoding="utf-8"))
            html_text = Path(result["audit_html"]).read_text(encoding="utf-8")
            self.assertEqual(result["carried_source_and_gold_checks"], 3)
            self.assertEqual(audit["protocol"]["carried_source_and_gold_checks"], 3)
            self.assertEqual(template["schema_version"], 2)
            self.assertEqual(template["audit_id"], audit["audit_id"])
            self.assertEqual(template["scope_snapshot"], audit["submission_scope_snapshot"])
            self.assertEqual(template["reviewer_id"], "yzb")
            self.assertTrue(all(item["source_verified"] for item in template["reviews"]))
            self.assertTrue(all(item["actual_benchmarks_verified"] for item in template["reviews"]))
            self.assertTrue(all(item["comparison_reviewed"] is None for item in template["reviews"]))
            self.assertTrue(all("route_and_fallback_reviewed" not in item for item in template["reviews"]))
            self.assertIn("What changed after your Round 1 audit", html_text)
            self.assertIn("Source paper and actual benchmark list carried from Round 1", html_text)
            self.assertIn('value="yzb"', html_text)
            self.assertNotIn('data-field="route_and_fallback_reviewed"', html_text)
            self.assertIn('"submission_filename": "literature_audit_submission_round_2.json"', html_text)
            self.assertIn(f'"audit_id": "{audit["audit_id"]}"', html_text)
            self.assertIn("anchor.download = scope.submission_filename", html_text)
            self.assertNotIn("/Users/", html_text)

            current_submission = json.loads(json.dumps(template))
            for item in current_submission["reviews"]:
                item["comparison_reviewed"] = True
                item["decision"] = "MATCH"
                item["notes"] = "Updated recommendations were compared with the unchanged paper benchmark list."
            self.assertEqual(
                evaluate_literature_audit(current_submission, audit)["status"],
                "LITERATURE_AUDIT_CONFIRMED",
            )

        legacy_scope = json.loads(
            (ROOT / "assets/output/literature_audit/history/round_1/literature_audit.json").read_text()
        )
        legacy_submission = json.loads(
            (ROOT / "assets/output/literature_audit/history/round_1/literature_audit_submission.json").read_text()
        )
        self.assertEqual(
            evaluate_literature_audit(legacy_submission, legacy_scope)["status"],
            "LITERATURE_AUDIT_PARTIAL",
        )

    def test_round_three_delta_audit_targets_only_the_feedback_case(self) -> None:
        round_2 = ROOT / "assets/output/literature_audit/history/round_2"
        previous = json.loads((round_2 / "blind_evaluation.json").read_text(encoding="utf-8"))
        current = json.loads((ROOT / "assets/output/blind_evaluation.json").read_text(encoding="utf-8"))
        verdict = json.loads((round_2 / "final_verdict.json").read_text(encoding="utf-8"))
        comparison = compare_iterations(
            previous,
            current,
            verdict,
            previous_iteration=2,
            current_iteration=3,
        )
        self.assertEqual(comparison["comparison"], "literature_audit_round_2_to_round_3")
        case_2 = next(case for case in comparison["cases"] if case["case_id"] == "case_002")
        self.assertEqual(case_2["newly_selected"], ["leetcodehardgym", "multipl_e"])
        self.assertEqual(case_2["removed_selected"], ["scienceworld"])
        self.assertEqual(
            case_2["resolved_unmodeled_gold"],
            ["LeetcodeHardGym", "MultiPL-E language ports"],
        )
        self.assertEqual(case_2["after"]["selected_missing"], [])
        self.assertEqual(case_2["after"]["selected_actual_precision"], 1.0)

        with tempfile.TemporaryDirectory() as raw_tmp:
            result = prepare_literature_audit(
                ROOT / "assets/output/blind_evaluation.json",
                raw_tmp,
                workspace_root=ROOT,
                iteration=3,
                iteration_comparison=comparison,
                prior_audit_path=round_2 / "literature_audit.json",
                prior_submission_path=round_2 / "literature_audit_submission_round_2.json",
                case_ids=["case_002"],
                display_label="Auto-Bench Blind Literature Audit — Round 3 Delta",
                submission_filename="literature_audit_submission_round_3.json",
            )
            audit = json.loads(Path(result["audit_json"]).read_text(encoding="utf-8"))
            template = json.loads(Path(result["review_template"]).read_text(encoding="utf-8"))
            html_text = Path(result["audit_html"]).read_text(encoding="utf-8")
            self.assertEqual(result["case_count"], 1)
            self.assertEqual(result["carried_source_and_gold_checks"], 1)
            self.assertEqual([case["case_id"] for case in audit["cases"]], ["case_002"])
            self.assertEqual(audit["protocol"]["full_evaluation_case_count"], 3)
            self.assertEqual(audit["protocol"]["changed_case_filter"], ["case_002"])
            self.assertEqual(template["reviewer_id"], "yzb")
            self.assertTrue(template["reviews"][0]["source_verified"])
            self.assertTrue(template["reviews"][0]["actual_benchmarks_verified"])
            self.assertIn("What changed after your Round 2 audit", html_text)
            self.assertIn("literature_audit_submission_round_3.json", html_text)
            self.assertNotIn("/Users/", html_text)

            stale = json.loads(
                (round_2 / "literature_audit_submission_round_2.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                evaluate_literature_audit(stale, audit)["status"],
                "HUMAN_LITERATURE_AUDIT_REQUIRED",
            )


if __name__ == "__main__":
    unittest.main()
