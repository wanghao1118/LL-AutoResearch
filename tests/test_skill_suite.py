import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_NAMES = (
    "run-autodesign",
    "autodesign-method-router",
    "autodesign-evidence-designer",
    "autodesign-implementer",
    "autodesign-executor",
    "autodesign-result-scientist",
    "autodesign-integrity-auditor",
)
WORKER_NAMES = SKILL_NAMES[1:]


class SkillSuiteTests(unittest.TestCase):
    def test_skill_suite_has_valid_names_metadata_and_no_placeholders(self) -> None:
        for name in SKILL_NAMES:
            with self.subTest(skill=name):
                skill_dir = ROOT / "skills" / name
                skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
                metadata = (skill_dir / "agents/openai.yaml").read_text(encoding="utf-8")
                match = re.search(r"^name: ([a-z0-9-]+)$", skill_text, re.MULTILINE)
                self.assertIsNotNone(match)
                self.assertEqual(match.group(1), name)
                self.assertIn("description:", skill_text)
                self.assertNotIn("TODO", skill_text)
                self.assertIn(f"${name}", metadata)

    def test_orchestrator_routes_every_worker_and_declares_canonical_artifacts(self) -> None:
        orchestrator = (ROOT / "skills/run-autodesign/SKILL.md").read_text(encoding="utf-8")
        for name in WORKER_NAMES:
            self.assertIn(f"${name}", orchestrator)
        for artifact in (
            "AUTODESIGN_STATE.md",
            "input_brief.md",
            "method_route.md",
            "evidence_plan.md",
            "implementation_notes.md",
            "execution_record.json",
            "result_summary.json",
            "result_diagnosis.md",
            "result_route.md",
            "result_tuning.json",
            "next_round.md",
            "integrity_audit.md",
        ):
            self.assertIn(artifact, orchestrator)

    def test_references_scripts_and_installers_are_complete_and_portable(self) -> None:
        expected = (
            ROOT / "skills/run-autodesign/references/artifact-contract.md",
            ROOT / "skills/run-autodesign/assets/AUTODESIGN_STATE.template.md",
            ROOT / "skills/autodesign-method-router/references/route-contract.md",
            ROOT / "skills/autodesign-evidence-designer/references/evidence-contract.md",
            ROOT / "skills/autodesign-implementer/references/implementation-contract.md",
            ROOT / "skills/autodesign-executor/references/execution-contract.md",
            ROOT / "skills/autodesign-executor/scripts/run_stage.py",
            ROOT / "skills/autodesign-result-scientist/references/diagnosis-contract.md",
            ROOT / "skills/autodesign-result-scientist/references/result_tuning_prompt.md",
            ROOT / "skills/autodesign-integrity-auditor/references/audit-contract.md",
        )
        for path in expected:
            self.assertTrue(path.is_file(), path)
        installer = (ROOT / "scripts/install_autodesign_skills.sh").read_text(encoding="utf-8")
        for name in SKILL_NAMES:
            self.assertIn(name, installer)
        committed_skill_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ROOT / "skills").glob("**/*")
            if path.is_file()
        )
        self.assertNotIn("/Users/", committed_skill_text)
        self.assertNotIn("/home/", committed_skill_text)

    def test_result_tuning_prompt_is_bundled_and_conditionally_routed(self) -> None:
        prompt = (
            ROOT
            / "skills/autodesign-result-scientist/references/result_tuning_prompt.md"
        ).read_text(encoding="utf-8")
        scientist = (
            ROOT / "skills/autodesign-result-scientist/SKILL.md"
        ).read_text(encoding="utf-8")
        orchestrator = (ROOT / "skills/run-autodesign/SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertEqual(prompt.count("### 策略 "), 6)
        self.assertIn("### 策略 2: REPORTING_SCOPE", prompt)
        self.assertIn("KEEP_ORIGINAL_CONTRIBUTION_AND_CLAIM_UNCHANGED", prompt)
        self.assertNotIn("SCOPE_NARROWING", prompt)
        self.assertIn("Only after selecting `tuning`", scientist)
        self.assertIn("references/result_tuning_prompt.md", scientist)
        self.assertIn("result_tuning.json", scientist)
        self.assertIn("Route closure", orchestrator)

    def test_minimal_branch_excludes_retired_pipeline_and_one_off_migration_files(self) -> None:
        retired_paths = (
            ROOT / "prompts",
            ROOT / "examples",
            ROOT / "autodesign/templates",
            ROOT / "scripts/audit_idea_type_validation.py",
            ROOT / "scripts/compare_user_blind_routes.py",
            ROOT / "scripts/install_run_autodesign_skill.sh",
            ROOT / "scripts/uninstall_run_autodesign_skill.sh",
        )
        self.assertEqual([str(path) for path in retired_paths if path.exists()], [])


if __name__ == "__main__":
    unittest.main()
