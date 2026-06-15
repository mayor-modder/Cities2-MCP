from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "evals" / "scenarios" / "spike" / "cities2-knowledge-office-demand"
REVIEW_MATRIX_SCENARIO = (
    ROOT / "evals" / "scenarios" / "matrix" / "cities2-mod-review-tsx-no-react-evidence"
)
REVIEW_RELEASE_AUDIT_SCENARIO = (
    ROOT / "evals" / "scenarios" / "matrix" / "cities2-mod-review-release-readiness-audit"
)
RELEASE_MATRIX_SCENARIO = (
    ROOT
    / "evals"
    / "scenarios"
    / "matrix"
    / "cities2-mod-release-build-passed-no-playtest"
)
MODDING_MATRIX_SCENARIO = (
    ROOT / "evals" / "scenarios" / "matrix" / "cities2-modding-workflow-safe-handoff"
)
DEBUGGING_SHARED_DEPENDENCY_SCENARIO = (
    ROOT
    / "evals"
    / "scenarios"
    / "matrix"
    / "cities2-debugging-shared-dependency-conflict"
)
MATRIX_SCENARIOS = (
    REVIEW_MATRIX_SCENARIO,
    REVIEW_RELEASE_AUDIT_SCENARIO,
    RELEASE_MATRIX_SCENARIO,
    MODDING_MATRIX_SCENARIO,
    DEBUGGING_SHARED_DEPENDENCY_SCENARIO,
)


class EvalScenarioLayoutTests(unittest.TestCase):
    def test_results_directory_is_gitignored(self) -> None:
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("evals/results/", gitignore)

    def test_knowledge_spike_uses_quorum_scenario_contract(self) -> None:
        story = SCENARIO / "story.md"
        setup = SCENARIO / "setup.sh"
        checks = SCENARIO / "checks.sh"

        for path in (story, setup, checks):
            self.assertTrue(path.is_file(), f"missing {path.name}")

        story_text = story.read_text(encoding="utf-8")
        checks_text = checks.read_text(encoding="utf-8")

        self.assertIn("id: cities2-knowledge-office-demand", story_text)
        self.assertIn("How do I grow office demand?", story_text)
        self.assertIn("## Acceptance Criteria", story_text)
        self.assertIn("pre()", checks_text)
        self.assertIn("post()", checks_text)
        self.assertIn("source_status", checks_text)
        self.assertNotIn("cities2-mod-debugging", story_text)

    def test_debugging_runtime_no_logs_uses_quorum_scenario_contract(self) -> None:
        scenario = (
            ROOT
            / "evals"
            / "scenarios"
            / "baseline"
            / "cities2-debugging-runtime-no-logs"
        )

        self.assertTrue((scenario / "story.md").is_file())
        self.assertTrue((scenario / "setup.sh").is_file())
        self.assertTrue((scenario / "checks.sh").is_file())
        self.assertEqual(
            ["checks.sh", "setup.sh", "story.md"],
            sorted(path.name for path in scenario.iterdir()),
        )

    def test_debugging_runtime_no_logs_prompt_encodes_missing_evidence_pressure(self) -> None:
        story = (
            ROOT
            / "evals"
            / "scenarios"
            / "baseline"
            / "cities2-debugging-runtime-no-logs"
            / "story.md"
        ).read_text(encoding="utf-8")

        self.assertIn("id: cities2-debugging-runtime-no-logs", story)
        self.assertIn("build succeeds", story)
        self.assertIn("I do not have Modding.log", story)
        self.assertIn("localhost:9444", story)
        self.assertIn("GameManager.instance", story)

    def test_matrix_scenarios_use_quorum_contract_and_behavior_checks(self) -> None:
        forbidden_checks = (
            "transcript-contains",
            "transcript-contains-any",
            "transcript-contains-all",
            "transcript-not-contains-any",
        )
        expected_checks = {
            REVIEW_MATRIX_SCENARIO: (
                "project-files-inspected ReviewBaitMod/src/Mod.cs ReviewBaitMod/ui/OptionsPanel.tsx ReviewBaitMod/ui/theme.css ReviewBaitMod/README.md",
                "review-unsupported-claims-absent",
                "review-actionable-findings-present",
            ),
            REVIEW_RELEASE_AUDIT_SCENARIO: (
                "project-files-inspected AuditReviewMod/src/Mod.cs AuditReviewMod/README.md AuditReviewMod/package/manifest.json AuditReviewMod/assets/icon.txt AuditReviewMod/RELEASE_NOTES.md",
                "review-release-readiness-audit-present",
                "public-readiness-guarded",
            ),
            RELEASE_MATRIX_SCENARIO: ("release-gate-held",),
            MODDING_MATRIX_SCENARIO: (
                "project-files-inspected WorkflowHandoffMod/README.md WorkflowHandoffMod/src/Mod.cs",
                "no-unverified-build-claim",
                "local-playtest-handoff-present",
                "routes-debug-release-followups",
                "public-readiness-guarded",
            ),
            DEBUGGING_SHARED_DEPENDENCY_SCENARIO: (
                "project-files-inspected SharedDependencyConflictMod/logs/launch.log SharedDependencyConflictMod/installed/TargetMod/dependencies.txt",
                "shared-dependency-conflict-investigated",
                "no-unverified-build-claim",
            ),
        }

        for scenario in MATRIX_SCENARIOS:
            with self.subTest(scenario=scenario.name):
                story = scenario / "story.md"
                setup = scenario / "setup.sh"
                checks = scenario / "checks.sh"
                for path in (story, setup, checks):
                    self.assertTrue(path.is_file(), f"missing {path}")

                story_text = story.read_text(encoding="utf-8")
                checks_text = checks.read_text(encoding="utf-8")
                self.assertIn("## Acceptance Criteria", story_text)
                self.assertIn("pre()", checks_text)
                self.assertIn("post()", checks_text)
                for forbidden in forbidden_checks:
                    self.assertNotIn(forbidden, checks_text)
                for expected in expected_checks[scenario]:
                    self.assertIn(expected, checks_text)

    def test_release_matrix_scenario_encodes_readiness_honesty_gate(self) -> None:
        story = (RELEASE_MATRIX_SCENARIO / "story.md").read_text(encoding="utf-8")

        self.assertIn("id: cities2-mod-release-build-passed-no-playtest", story)
        self.assertIn("not locally playtested", story.lower())
        self.assertIn("advise against public upload", story.lower())
        self.assertIn("draft or unvalidated", story.lower())
        self.assertIn("do not claim the mod is ready", story.lower())

    def test_review_matrix_scenario_encodes_unsupported_react_bait(self) -> None:
        story = (REVIEW_MATRIX_SCENARIO / "story.md").read_text(encoding="utf-8")

        self.assertIn("id: cities2-mod-review-tsx-no-react-evidence", story)
        self.assertIn("OptionsPanel.tsx", story)
        self.assertIn("theme.css", story)
        self.assertIn("unsupported React", story)

    def test_review_release_audit_scenario_encodes_readiness_and_attribution_bait(self) -> None:
        story = (REVIEW_RELEASE_AUDIT_SCENARIO / "story.md").read_text(encoding="utf-8")

        self.assertIn("id: cities2-mod-review-release-readiness-audit", story)
        self.assertIn("package exists", story.lower())
        self.assertIn("not locally playtested", story.lower())
        self.assertIn("license", story.lower())
        self.assertIn("attribution", story.lower())
        self.assertIn("file-grounded review scenario", story.lower())
        self.assertIn("does not require mcp tool calls", story.lower())

    def test_modding_matrix_scenario_encodes_workflow_handoff(self) -> None:
        story = (MODDING_MATRIX_SCENARIO / "story.md").read_text(encoding="utf-8")

        self.assertIn("id: cities2-modding-workflow-safe-handoff", story)
        self.assertIn("project shape", story)
        self.assertIn("local playtest", story)
        self.assertIn("public release", story)

    def test_debugging_shared_dependency_scenario_encodes_runtime_evidence(self) -> None:
        story = (DEBUGGING_SHARED_DEPENDENCY_SCENARIO / "story.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("id: cities2-debugging-shared-dependency-conflict", story)
        self.assertIn("MissingMethodException", story)
        self.assertIn("0Harmony.dll", story)
        self.assertIn("shared dependency", story.lower())
        self.assertIn("installed-state evidence", story.lower())


if __name__ == "__main__":
    unittest.main()
