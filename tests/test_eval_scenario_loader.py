from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "evals" / "scenarios" / "spike" / "cities2-knowledge-office-demand"


class EvalScenarioLoaderTests(unittest.TestCase):
    def test_loads_committed_knowledge_spike(self) -> None:
        from evals.runner.scenario import load_scenario

        scenario = load_scenario(SCENARIO)

        self.assertEqual(scenario.id, "cities2-knowledge-office-demand")
        self.assertEqual(
            scenario.title,
            "Cities2 knowledge skill answers an office demand question with retrieved sources",
        )
        self.assertEqual(scenario.path, SCENARIO.resolve())
        self.assertEqual(scenario.story, SCENARIO.resolve() / "story.md")
        self.assertEqual(scenario.setup, SCENARIO.resolve() / "setup.sh")
        self.assertEqual(scenario.checks, SCENARIO.resolve() / "checks.sh")

    def test_rejects_missing_required_files(self) -> None:
        from evals.runner.scenario import ScenarioError, load_scenario

        with tempfile.TemporaryDirectory(prefix="cities2-eval-scenario-") as tmp:
            scenario_dir = Path(tmp) / "sample"
            scenario_dir.mkdir()
            (scenario_dir / "story.md").write_text(
                "---\nid: sample\n---\n\n## Acceptance Criteria\n",
                encoding="utf-8",
            )
            (scenario_dir / "checks.sh").write_text("pre() { :; }\npost() { :; }\n", encoding="utf-8")

            with self.assertRaisesRegex(ScenarioError, "setup.sh"):
                load_scenario(scenario_dir)

    def test_rejects_story_without_acceptance_criteria(self) -> None:
        from evals.runner.scenario import ScenarioError, load_scenario

        with tempfile.TemporaryDirectory(prefix="cities2-eval-scenario-") as tmp:
            scenario_dir = Path(tmp) / "sample"
            scenario_dir.mkdir()
            _write_minimal_scenario(scenario_dir)
            (scenario_dir / "story.md").write_text(
                "---\nid: sample\ntitle: Sample scenario\n---\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ScenarioError, "Acceptance Criteria"):
                load_scenario(scenario_dir)

    def test_rejects_story_without_title(self) -> None:
        from evals.runner.scenario import ScenarioError, load_scenario

        with tempfile.TemporaryDirectory(prefix="cities2-eval-scenario-") as tmp:
            scenario_dir = Path(tmp) / "sample"
            scenario_dir.mkdir()
            _write_minimal_scenario(scenario_dir)
            (scenario_dir / "story.md").write_text(
                textwrap.dedent(
                    """\
                    ---
                    id: sample
                    ---

                    ## Acceptance Criteria

                    - It loads.
                    """
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ScenarioError, "frontmatter missing title"):
                load_scenario(scenario_dir)

    def test_rejects_checks_without_pre_and_post(self) -> None:
        from evals.runner.scenario import ScenarioError, load_scenario

        with tempfile.TemporaryDirectory(prefix="cities2-eval-scenario-") as tmp:
            scenario_dir = Path(tmp) / "sample"
            scenario_dir.mkdir()
            _write_minimal_scenario(scenario_dir)
            (scenario_dir / "checks.sh").write_text("pre() { :; }\n", encoding="utf-8")

            with self.assertRaisesRegex(ScenarioError, "pre\\(\\).*post\\(\\)"):
                load_scenario(scenario_dir)

    def test_rejects_checks_with_only_commented_pre_and_post(self) -> None:
        from evals.runner.scenario import ScenarioError, load_scenario

        with tempfile.TemporaryDirectory(prefix="cities2-eval-scenario-") as tmp:
            scenario_dir = Path(tmp) / "sample"
            scenario_dir.mkdir()
            _write_minimal_scenario(scenario_dir)
            (scenario_dir / "checks.sh").write_text(
                "# pre() { :; }\n# post() { :; }\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ScenarioError, "pre\\(\\).*post\\(\\)"):
                load_scenario(scenario_dir)


def _write_minimal_scenario(path: Path) -> None:
    (path / "story.md").write_text(
        textwrap.dedent(
            """\
            ---
            id: sample
            title: Sample scenario
            ---

            ## Acceptance Criteria

            - It loads.
            """
        ),
        encoding="utf-8",
    )
    (path / "setup.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    (path / "checks.sh").write_text("pre() { :; }\npost() { :; }\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
