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
MATRIX_DOSSIER = (
    ROOT
    / "docs"
    / "superpowers"
    / "evaluations"
    / "2026-06-07-cities2-codex-skill-effectiveness-matrix.md"
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

    def test_codex_skill_effectiveness_matrix_has_reviewable_structure(self) -> None:
        dossier = MATRIX_DOSSIER.read_text(encoding="utf-8")

        expected_sections = [
            "# Cities2 Codex skill effectiveness matrix",
            "## Executive summary",
            "## Scenario matrix",
            "## Skill verdicts",
            "## Per-skill observations",
            "## Cross-skill patterns",
            "## Check and instrumentation notes",
            "## Next decisions",
            "## Artifact hygiene",
        ]
        last_index = -1
        for section in expected_sections:
            index = dossier.find(section)
            self.assertNotEqual(index, -1)
            self.assertGreater(index, last_index)
            last_index = index

        for skill in (
            "cities2-knowledge",
            "cities2-modding",
            "cities2-mod-review",
            "cities2-mod-debugging",
            "cities2-mod-release",
        ):
            self.assertIn(skill, dossier)

        for scenario_id in (
            "cities2-knowledge-office-demand",
            "cities2-modding-workflow-safe-handoff",
            "cities2-mod-review-tsx-no-react-evidence",
            "cities2-debugging-runtime-no-logs",
            "cities2-mod-release-build-passed-no-playtest",
        ):
            self.assertIn(scenario_id, dossier)

        self.assertIn("directional evidence", dossier)
        self.assertIn("not a guarantee", dossier)
        self.assertIn("2026-06-06 debugging dossier", dossier)
        self.assertIn("rerun", dossier)
        self.assertIn("run-to-run variance", dossier)

    def test_codex_skill_effectiveness_matrix_keeps_verdicts_conservative(self) -> None:
        dossier = MATRIX_DOSSIER.read_text(encoding="utf-8")

        self.assertIn(
            "| `cities2-mod-debugging` | `cities2-debugging-runtime-no-logs` runtime UI missing with no logs | 3 no-skill, 3 with-skill | no-skill 0/3 pass; with-skill 2/3 pass |",
            dossier,
        )
        self.assertIn(
            "| `cities2-mod-debugging` | `cities2-debugging-runtime-no-logs` runtime UI missing with no logs | 3 no-skill, 3 with-skill | no-skill 0/3 pass; with-skill 2/3 pass | runtime-evidence request and handoff in the one failing with-skill trial; all no-skill trials missed the handoff | clear positive delta |",
            dossier,
        )
        self.assertIn(
            "| `cities2-mod-release` | `cities2-mod-release-build-passed-no-playtest` build passed but no playtest evidence | 3 no-skill, 3 with-skill | no-skill 0/3 pass; with-skill 0/3 pass |",
            dossier,
        )
        self.assertIn(
            "| `cities2-mod-release` | `cities2-mod-release-build-passed-no-playtest` build passed but no playtest evidence | 3 no-skill, 3 with-skill | no-skill 0/3 pass; with-skill 0/3 pass | no-skill missed release blocking and override language; with-skill only missed skill-call event | inconclusive / check issue |",
            dossier,
        )
        self.assertIn("Only `cities2-mod-debugging` showed a measured pass-count delta.", dossier)
        self.assertIn(
            "| `cities2-knowledge` | `cities2-knowledge-office-demand` office demand gameplay answer | 3 no-skill, 3 with-skill | no-skill 0/3 pass; with-skill 0/3 pass | both conditions missed skill-call, `source_status`, and `search`; 2 no-skill trials also missed the source label | inconclusive / check issue |",
            dossier,
        )
        self.assertIn(
            "| `cities2-modding` | `cities2-modding-workflow-safe-handoff` workflow-safe local handoff | 3 no-skill, 3 with-skill | no-skill 0/3 pass; with-skill 0/3 pass | skill-call event, workspace-evidence wording, release/debug routing, build-claim wording | inconclusive / check issue |",
            dossier,
        )
        self.assertIn(
            "| `cities2-mod-review` | `cities2-mod-review-tsx-no-react-evidence` TSX/CSS review without React evidence | 3 no-skill, 3 with-skill | no-skill 0/3 pass; with-skill 0/3 pass | skill-call event, required observed/inferred wording, required CSS-not-loaded wording | inconclusive / check issue |",
            dossier,
        )
        self.assertEqual(2, dossier.count("clear positive delta"))
        self.assertNotIn("mixed positive delta", dossier)
        self.assertNotIn("`cities2-mod-release`: positive delta", dossier)
        non_debugging_skills = (
            "cities2-knowledge",
            "cities2-modding",
            "cities2-mod-review",
            "cities2-mod-release",
            "knowledge",
            "modding",
            "review",
            "release",
        )
        overclaim_words = re.compile(
            r"\b(?:positive|improved|improvement|stronger|strongest|better|win|wins)\b",
            re.IGNORECASE,
        )
        for line in dossier.splitlines():
            if "positive delta" in line:
                self.assertIn("cities2-mod-debugging", line)
            if any(skill in line for skill in non_debugging_skills):
                self.assertIsNone(overclaim_words.search(line))

    def test_codex_skill_effectiveness_matrix_avoids_raw_artifacts_and_private_paths(
        self,
    ) -> None:
        dossier = MATRIX_DOSSIER.read_text(encoding="utf-8")

        forbidden = [
            "coding-agent-tool-calls.jsonl",
            "transcript.txt",
            "verdict.json",
            "coding-agent-config",
            "C:" + "\\" + "Users",
            "\\" + "Users" + "\\",
            "/" + "Users" + "/",
            "OPENAI_API_KEY" + "=",
        ]
        for needle in forbidden:
            self.assertNotIn(needle, dossier)
        self.assertIsNone(re.search(r"sk-[A-Za-z0-9_-]{20,}", dossier))
