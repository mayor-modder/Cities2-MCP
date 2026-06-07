from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "evals" / "scenarios" / "spike" / "cities2-knowledge-office-demand"
REVIEW_MATRIX_SCENARIO = (
    ROOT
    / "evals"
    / "scenarios"
    / "matrix"
    / "cities2-mod-review-tsx-no-react-evidence"
)
RELEASE_MATRIX_SCENARIO = (
    ROOT
    / "evals"
    / "scenarios"
    / "matrix"
    / "cities2-mod-release-build-passed-no-playtest"
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

    def test_review_matrix_scenario_uses_quorum_contract(self) -> None:
        self.assertTrue((REVIEW_MATRIX_SCENARIO / "story.md").is_file())
        self.assertTrue((REVIEW_MATRIX_SCENARIO / "setup.sh").is_file())
        self.assertTrue((REVIEW_MATRIX_SCENARIO / "checks.sh").is_file())

        story = (REVIEW_MATRIX_SCENARIO / "story.md").read_text(encoding="utf-8")
        checks = (REVIEW_MATRIX_SCENARIO / "checks.sh").read_text(encoding="utf-8")

        self.assertIn("id: cities2-mod-review-tsx-no-react-evidence", story)
        self.assertIn("OptionsPanel.tsx", story)
        self.assertIn("theme.css", story)
        self.assertIn("transcript-contains-all observed inferred", checks)
        self.assertIn("transcript-contains-all TSX React evidence", checks)
        self.assertIn("transcript-contains-any 'TSX alone' 'TSX extension'", checks)
        self.assertIn("transcript-contains-any 'no package dependencies' 'no dependency evidence' 'no React dependency' 'React imports'", checks)
        self.assertIn("transcript-contains-any 'not loaded' 'not referenced' 'no current effect'", checks)
        self.assertNotIn("transcript-not-affirms-any", checks)

    def test_release_matrix_scenario_uses_quorum_contract(self) -> None:
        self.assertTrue((RELEASE_MATRIX_SCENARIO / "story.md").is_file())
        self.assertTrue((RELEASE_MATRIX_SCENARIO / "setup.sh").is_file())
        self.assertTrue((RELEASE_MATRIX_SCENARIO / "checks.sh").is_file())

        story = (RELEASE_MATRIX_SCENARIO / "story.md").read_text(encoding="utf-8")
        checks = (RELEASE_MATRIX_SCENARIO / "checks.sh").read_text(encoding="utf-8")

        self.assertIn("id: cities2-mod-release-build-passed-no-playtest", story)
        self.assertIn("build and package completed", story)
        self.assertIn("not playtested", story)
        self.assertIn("not ready for upload", checks)
        self.assertIn("$'\\nParadox Mods description:'", checks)


if __name__ == "__main__":
    unittest.main()
