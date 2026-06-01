from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "evals" / "scenarios" / "spike" / "cities2-knowledge-office-demand"


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


if __name__ == "__main__":
    unittest.main()
