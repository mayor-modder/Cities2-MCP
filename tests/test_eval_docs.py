from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALUATION = (
    ROOT
    / "docs"
    / "superpowers"
    / "evaluations"
    / "2026-06-01-cities2-knowledge-runner-spike.md"
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

        self.assertIn("Required offline smoke protocol", evaluation)
        self.assertIn("Optional real-client smoke direction", evaluation)
        self.assertIn("Required offline fake-Codex smoke", evaluation)
        self.assertIn("`codex`", evaluation)
        self.assertIn("`claude`", evaluation)
        self.assertIn("`agy`", evaluation)
