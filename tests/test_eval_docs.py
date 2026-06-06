from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALUATION = (
    ROOT
    / "docs"
    / "superpowers"
    / "evaluations"
    / "2026-06-04-cities2-knowledge-runner-spike.md"
)
DEBUGGING_DOSSIER = (
    ROOT
    / "docs"
    / "superpowers"
    / "evaluations"
    / "2026-06-06-cities2-debugging-runtime-no-logs-results-dossier.md"
)
DEBUGGING_DOSSIER_PLAN = (
    ROOT / "docs" / "superpowers" / "plans" / "2026-06-06-eval-results-dossier.md"
)
DEBUGGING_DOSSIER_SPEC = (
    ROOT
    / "docs"
    / "superpowers"
    / "specs"
    / "2026-06-06-eval-results-dossier-design.md"
)
DEBUGGING_DOSSIER_DOCS = (
    DEBUGGING_DOSSIER,
    DEBUGGING_DOSSIER_PLAN,
    DEBUGGING_DOSSIER_SPEC,
)


class EvalDocsTests(unittest.TestCase):
    def test_docs_explain_offline_smoke_without_local_paths_or_secrets(self) -> None:
        readme = (ROOT / "evals" / "README.md").read_text(encoding="utf-8")
        evaluation = EVALUATION.read_text(encoding="utf-8")

        for text in (readme, evaluation):
            self.assertIn("evals/results/", text)
            self.assertIn("gitignored", text.lower())
            self.assertNotIn("C:" + "\\" + "Users", text)
            self.assertNotIn("\\" + "Users" + "\\", text)
            self.assertNotIn("/" + "Users" + "/", text)
            self.assertNotIn("OPENAI_API_KEY" + "=", text)
            self.assertNotIn("sk-", text)

    def test_evaluation_note_records_decision_point(self) -> None:
        evaluation = EVALUATION.read_text(encoding="utf-8")

        self.assertIn("Reuse Quorum directly", evaluation)
        self.assertIn("Keep the local compatible subset", evaluation)

    def test_evaluation_note_records_client_matrix(self) -> None:
        evaluation = EVALUATION.read_text(encoding="utf-8")

        self.assertIn("What was actually tested", evaluation)
        self.assertIn("What was not tested", evaluation)
        self.assertIn("Required offline smoke protocol", evaluation)
        self.assertIn("Optional real-client smoke direction", evaluation)
        self.assertIn("Required offline runner smoke", evaluation)
        self.assertIn("does not call a real model", evaluation)
        self.assertIn("`codex`", evaluation)
        self.assertIn("`claude`", evaluation)
        self.assertIn("`agy`", evaluation)

    def test_debugging_results_dossier_has_reviewable_structure(self) -> None:
        dossier = DEBUGGING_DOSSIER.read_text(encoding="utf-8")

        expected_sections = [
            "# Cities2 debugging runtime-no-logs results dossier",
            "## Executive summary",
            "## Run matrix",
            "## Per-run observations",
            "## Cross-run patterns",
            "## Interpretation",
            "## Next decisions",
            "## Artifact hygiene",
        ]
        last_index = -1
        for section in expected_sections:
            index = dossier.find(section)
            self.assertNotEqual(index, -1)
            self.assertGreater(index, last_index)
            last_index = index

        expected_rows = [
            "| no-skill trial 1 | fail | `handoff-present`, `post-checks` |",
            "| no-skill trial 2 | fail | `requests-runtime-evidence`, `handoff-present`, `post-checks` |",
            "| no-skill trial 3 | fail | `requests-runtime-evidence`, `handoff-present`, `post-checks` |",
            "| with-cities2-mod-debugging trial 1 | fail | `no-unverified-fix-claim`, `handoff-present`, `post-checks` |",
            "| with-cities2-mod-debugging trial 2 | pass | none |",
            "| with-cities2-mod-debugging trial 3 | fail | `no-unverified-fix-claim`, `handoff-present`, `post-checks` |",
        ]
        for row in expected_rows:
            self.assertIn(row, dossier)

        self.assertIn("handoff-present", dossier)
        self.assertIn("no-unverified-fix-claim", dossier)
        self.assertIn("requests-runtime-evidence", dossier)
        self.assertIn("current behavior", dossier)
        self.assertIn("does not justify editing `cities2-mod-debugging`", dossier)

    def test_debugging_results_dossier_avoids_raw_artifacts_and_private_paths(
        self,
    ) -> None:
        docs = "\n".join(path.read_text(encoding="utf-8") for path in DEBUGGING_DOSSIER_DOCS)

        forbidden = [
            "coding-agent-tool-calls.jsonl",
            "transcript.txt",
            "verdict.json",
            "C:" + "\\" + "Users",
            "\\" + "Users" + "\\",
            "/" + "Users" + "/",
            "OPENAI_API_KEY" + "=",
        ]
        for needle in forbidden:
            self.assertNotIn(needle, docs)
        self.assertIsNone(re.search(r"sk-[A-Za-z0-9_-]{20,}", docs))
