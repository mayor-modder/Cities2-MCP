from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "evals" / "reports"
EVALUATION = (
    REPORTS
    / "2026-06-04-cities2-knowledge-runner-spike.md"
)
DEBUGGING_DOSSIER = (
    REPORTS
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
SKILL_MATRIX_DOSSIER = (
    REPORTS
    / "2026-06-07-cities2-codex-skill-effectiveness-matrix.md"
)
KNOWLEDGE_RELEASE_RERUN = (
    REPORTS
    / "2026-06-13-cities2-knowledge-release-rerun.md"
)
MODDING_MULTIAGENT_PROTOCOL = (
    REPORTS
    / "2026-06-13-cities2-modding-multiagent-protocol.md"
)
MODDING_HANDOFF_CONSISTENCY = (
    REPORTS
    / "2026-06-14-cities2-modding-handoff-consistency.md"
)
MOD_REVIEW_ACTIONABLE_FINDINGS = (
    REPORTS
    / "2026-06-14-cities2-mod-review-actionable-findings.md"
)
MOD_REVIEW_IMPROVEMENT_RERUN = (
    REPORTS
    / "2026-06-14-cities2-mod-review-improvement-rerun.md"
)
DEBUGGING_SHARED_DEPENDENCY_RERUN = (
    REPORTS
    / "2026-06-15-cities2-debugging-shared-dependency-conflict.md"
)
CLAUDE_BACKEND_PILOT = (
    REPORTS
    / "2026-06-20-claude-backend-pilot.md"
)
CLAUDE_KNOWLEDGE_MODDING_MATRIX = (
    REPORTS
    / "2026-06-20-claude-knowledge-modding-matrix.md"
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

    def test_skill_effectiveness_matrix_dossier_has_actionable_structure(self) -> None:
        dossier = SKILL_MATRIX_DOSSIER.read_text(encoding="utf-8")

        expected_sections = [
            "# Cities2 Codex skill effectiveness matrix",
            "## Executive summary",
            "## Scenario matrix",
            "## Deterministic check results",
            "## Acceptance-criteria review results",
            "## Skill verdicts",
            "## Per-skill observations",
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

        self.assertIn("directional evidence", dossier)
        self.assertIn("not a guarantee", dossier)
        self.assertIn("deterministic", dossier)
        self.assertIn("acceptance criteria", dossier)
        self.assertIn("indeterminate environment failure", dossier)
        self.assertIn("readiness honesty", dossier)
        self.assertIn("Scenario too weak", dossier)
        self.assertIn("main skill-quality target", dossier)

    def test_skill_effectiveness_matrix_dossier_avoids_raw_artifacts_and_private_paths(
        self,
    ) -> None:
        dossier = SKILL_MATRIX_DOSSIER.read_text(encoding="utf-8")

        forbidden = [
            "coding-agent-tool-calls.jsonl",
            "transcript.txt",
            "verdict.json",
            "coding-agent-config",
            "coding-agent-workdir",
            "C:" + "\\" + "Users",
            "\\" + "Users" + "\\",
            "/" + "Users" + "/",
            "OPENAI_API_KEY" + "=",
        ]
        for needle in forbidden:
            self.assertNotIn(needle, dossier)
        self.assertIsNone(re.search(r"sk-[A-Za-z0-9_-]{20,}", dossier))

    def test_knowledge_release_rerun_report_has_actionable_structure(self) -> None:
        report = KNOWLEDGE_RELEASE_RERUN.read_text(encoding="utf-8")

        expected_sections = [
            "# Cities2 knowledge and release focused rerun",
            "## Executive summary",
            "## Run matrix",
            "## What changed",
            "## Knowledge result",
            "## Release result",
            "## Next decisions",
            "## Artifact hygiene",
        ]
        last_index = -1
        for section in expected_sections:
            index = report.find(section)
            self.assertNotEqual(index, -1)
            self.assertGreater(index, last_index)
            last_index = index

        self.assertIn("`cities2-knowledge`", report)
        self.assertIn("`cities2-mod-release`", report)
        self.assertIn("0/3", report)
        self.assertIn("3/3", report)
        self.assertIn("clear positive delta", report)
        self.assertIn("mixed positive delta", report)

    def test_knowledge_release_rerun_report_avoids_raw_artifacts_and_private_paths(
        self,
    ) -> None:
        report = KNOWLEDGE_RELEASE_RERUN.read_text(encoding="utf-8")

        forbidden = [
            "coding-agent-tool-calls.jsonl",
            "transcript.txt",
            "verdict.json",
            "coding-agent-config",
            "coding-agent-workdir",
            "C:" + "\\" + "Users",
            "\\" + "Users" + "\\",
            "/" + "Users" + "/",
            "OPENAI_API_KEY" + "=",
        ]
        for needle in forbidden:
            self.assertNotIn(needle, report)
        self.assertIsNone(re.search(r"sk-[A-Za-z0-9_-]{20,}", report))

    def test_modding_multiagent_protocol_has_actionable_structure(self) -> None:
        report = MODDING_MULTIAGENT_PROTOCOL.read_text(encoding="utf-8")

        expected_sections = [
            "# Cities2 modding multiagent eval protocol",
            "## Executive summary",
            "## What changed",
            "## Pilot matrix",
            "## Evidence model",
            "## Success gates",
            "## Artifact hygiene",
        ]
        last_index = -1
        for section in expected_sections:
            index = report.find(section)
            self.assertNotEqual(index, -1)
            self.assertGreater(index, last_index)
            last_index = index

        self.assertIn("`cities2-modding-workflow-safe-handoff`", report)
        self.assertIn("WorkflowHandoffMod/package/package-state.txt", report)
        self.assertIn("Exploratory only", report)
        self.assertIn("indeterminate instrumentation states", report)
        self.assertIn("deterministic evidence separately from manual acceptance review", report)

    def test_modding_multiagent_protocol_avoids_raw_artifacts_and_private_paths(
        self,
    ) -> None:
        report = MODDING_MULTIAGENT_PROTOCOL.read_text(encoding="utf-8")

        forbidden = [
            "coding-agent-tool-calls.jsonl",
            "transcript.txt",
            "verdict.json",
            "coding-agent-config",
            "coding-agent-workdir",
            "C:" + "\\" + "Users",
            "\\" + "Users" + "\\",
            "/" + "Users" + "/",
            "OPENAI_API_KEY" + "=",
        ]
        for needle in forbidden:
            self.assertNotIn(needle, report)
        self.assertIsNone(re.search(r"sk-[A-Za-z0-9_-]{20,}", report))

    def test_modding_handoff_consistency_report_has_actionable_structure(self) -> None:
        report = MODDING_HANDOFF_CONSISTENCY.read_text(encoding="utf-8")

        expected_sections = [
            "# Cities2 modding handoff consistency rerun",
            "## Short version",
            "## Run matrix",
            "## Verdict table",
            "## Failure patterns",
            "## Interpretation",
            "## Follow-up status",
            "## Privacy note",
        ]
        last_index = -1
        for section in expected_sections:
            index = report.find(section)
            self.assertNotEqual(index, -1)
            self.assertGreater(index, last_index)
            last_index = index

        self.assertIn("`no-skill`: 0/3 passed", report)
        self.assertIn("`with-cities2-modding`: 3/3 passed", report)
        self.assertIn("clear positive delta", report)
        self.assertIn("package-state evidence", report)
        self.assertIn("tail-only path candidates remain strict", report)

    def test_modding_handoff_consistency_report_avoids_raw_artifacts_and_private_paths(
        self,
    ) -> None:
        report = MODDING_HANDOFF_CONSISTENCY.read_text(encoding="utf-8")

        forbidden = [
            "coding-agent-tool-calls.jsonl",
            "transcript.txt",
            "verdict.json",
            "coding-agent-config",
            "coding-agent-workdir",
            "C:" + "\\" + "Users",
            "\\" + "Users" + "\\",
            "/" + "Users" + "/",
            "OPENAI_API_KEY" + "=",
        ]
        for needle in forbidden:
            self.assertNotIn(needle, report)
        self.assertIsNone(re.search(r"sk-[A-Za-z0-9_-]{20,}", report))

    def test_mod_review_actionable_findings_report_has_actionable_structure(self) -> None:
        report = MOD_REVIEW_ACTIONABLE_FINDINGS.read_text(encoding="utf-8")

        expected_sections = [
            "# Cities2 mod-review actionable findings rerun",
            "## Short version",
            "## Run matrix",
            "## Verdict table",
            "## Failure patterns",
            "## Interpretation",
            "## Follow-up status",
            "## Privacy note",
        ]
        last_index = -1
        for section in expected_sections:
            index = report.find(section)
            self.assertNotEqual(index, -1)
            self.assertGreater(index, last_index)
            last_index = index

        self.assertIn("`no-skill`: 0/3 passed", report)
        self.assertIn("`with-cities2-mod-review`: 0/3 passed", report)
        self.assertIn("not a pass for `cities2-mod-review`", report)
        self.assertIn("meaningful partial delta", report)
        self.assertIn("readiness evidence", report)
        self.assertIn("Do not treat `cities2-mod-review` as proven", report)
        self.assertIn("Code/eval commit reported by runner", report)
        self.assertIn("actionable findings", report)

    def test_mod_review_actionable_findings_report_avoids_raw_artifacts_and_private_paths(
        self,
    ) -> None:
        report = MOD_REVIEW_ACTIONABLE_FINDINGS.read_text(encoding="utf-8")

        forbidden = [
            "coding-agent-tool-calls.jsonl",
            "transcript.txt",
            "verdict.json",
            "coding-agent-config",
            "coding-agent-workdir",
            "C:" + "\\" + "Users",
            "\\" + "Users" + "\\",
            "/" + "Users" + "/",
            "OPENAI_API_KEY" + "=",
        ]
        for needle in forbidden:
            self.assertNotIn(needle, report)
        self.assertIsNone(re.search(r"sk-[A-Za-z0-9_-]{20,}", report))

    def test_mod_review_improvement_rerun_report_has_actionable_structure(self) -> None:
        report = MOD_REVIEW_IMPROVEMENT_RERUN.read_text(encoding="utf-8")

        expected_sections = [
            "# Cities2 mod-review improvement rerun",
            "## Short version",
            "## Run matrix",
            "## Verdict table",
            "## Interpretation",
            "## Post-review hardening",
            "## Follow-up status",
            "## Privacy note",
        ]
        last_index = -1
        for section in expected_sections:
            index = report.find(section)
            self.assertNotEqual(index, -1)
            self.assertGreater(index, last_index)
            last_index = index

        self.assertIn("`cities2-mod-review-tsx-no-react-evidence`", report)
        self.assertIn("`cities2-mod-review-release-readiness-audit`", report)
        self.assertIn("`no-skill`: 0/3 passed", report)
        self.assertIn("`with-cities2-mod-review`: 3/3 passed", report)
        self.assertIn("clear positive delta", report)
        self.assertIn("release-readiness audit", report)
        self.assertIn(
            "Post-review checker hardening commits: `f365cbc`, `cd9359e`, `d10b875`, `7ab5aba`, `0378c11`, `5b0c695`, `d112026`",
            report,
        )
        self.assertIn("not a rerun of the 12 live agent trials", report)
        self.assertIn("passive unsafe approval", report)
        self.assertIn("release can proceed", report)
        self.assertIn("inverted missing-evidence condition", report)
        self.assertIn("publish-before-evidence conditions", report)
        self.assertIn("safe conditional release guidance", report)
        self.assertIn("you may release this publicly", report)
        self.assertIn("although public release is blocked for now", report)
        self.assertIn("non-UI release evidence", report)

    def test_mod_review_improvement_rerun_report_avoids_raw_artifacts_and_private_paths(
        self,
    ) -> None:
        report = MOD_REVIEW_IMPROVEMENT_RERUN.read_text(encoding="utf-8")

        forbidden = [
            "coding-agent-tool-calls.jsonl",
            "transcript.txt",
            "verdict.json",
            "coding-agent-config",
            "coding-agent-workdir",
            "C:" + "\\" + "Users",
            "\\" + "Users" + "\\",
            "/" + "Users" + "/",
            "OPENAI_API_KEY" + "=",
        ]
        for needle in forbidden:
            self.assertNotIn(needle, report)
        self.assertIsNone(re.search(r"sk-[A-Za-z0-9_-]{20,}", report))

    def test_debugging_shared_dependency_report_has_actionable_structure(self) -> None:
        report = DEBUGGING_SHARED_DEPENDENCY_RERUN.read_text(encoding="utf-8")

        expected_sections = [
            "# Cities2 debugging shared dependency conflict eval",
            "## Short version",
            "## Run matrix",
            "## Verdict table",
            "## Failure patterns",
            "## Interpretation",
            "## Follow-up status",
            "## Privacy note",
        ]
        last_index = -1
        for section in expected_sections:
            index = report.find(section)
            self.assertNotEqual(index, -1)
            self.assertGreater(index, last_index)
            last_index = index

        self.assertIn("`no-skill`: 3/3 passed", report)
        self.assertIn("`with-cities2-mod-debugging`: 3/3 passed", report)
        self.assertIn("shared-dependency evidence: 6/6 passed", report)
        self.assertIn("not proven as a skill improvement", report)
        self.assertIn("checker false-positive regressions are covered", report)
        self.assertIn("checker false-pass regressions are covered", report)
        self.assertIn("No positive skill delta", report)

    def test_debugging_shared_dependency_report_avoids_raw_artifacts_and_private_paths(
        self,
    ) -> None:
        report = DEBUGGING_SHARED_DEPENDENCY_RERUN.read_text(encoding="utf-8")

        forbidden = [
            "coding-agent-tool-calls.jsonl",
            "transcript.txt",
            "verdict.json",
            "coding-agent-config",
            "coding-agent-workdir",
            "C:" + "\\" + "Users",
            "\\" + "Users" + "\\",
            "/" + "Users" + "/",
            "OPENAI_API_KEY" + "=",
        ]
        for needle in forbidden:
            self.assertNotIn(needle, report)
        self.assertIsNone(re.search(r"sk-[A-Za-z0-9_-]{20,}", report))

    def test_claude_backend_pilot_report_has_actionable_structure(self) -> None:
        report = CLAUDE_BACKEND_PILOT.read_text(encoding="utf-8")

        expected_sections = [
            "# Claude backend exploratory pilot",
            "## Short version",
            "## Run matrix",
            "## Verdict table",
            "## Failure patterns",
            "## Interpretation",
            "## Follow-up status",
            "## Privacy note",
        ]
        last_index = -1
        for section in expected_sections:
            index = report.find(section)
            self.assertNotEqual(index, -1)
            self.assertGreater(index, last_index)
            last_index = index

        self.assertIn("`cities2-knowledge-office-demand`: `no-skill` failed", report)
        self.assertIn("`with-cities2-knowledge` | 102 | pass", report)
        self.assertIn("`cities2-modding-workflow-safe-handoff`: both conditions failed", report)
        self.assertIn("exploratory client-adapter evidence", report)
        self.assertIn("checker calibration work for Claude wording", report)

    def test_claude_backend_pilot_report_avoids_raw_artifacts_and_private_paths(
        self,
    ) -> None:
        report = CLAUDE_BACKEND_PILOT.read_text(encoding="utf-8")

        forbidden = [
            "coding-agent-tool-calls.jsonl",
            "transcript.txt",
            "verdict.json",
            "coding-agent-config",
            "coding-agent-workdir",
            "C:" + "\\" + "Users",
            "\\" + "Users" + "\\",
            "/" + "Users" + "/",
            "OPENAI_API_KEY" + "=",
        ]
        for needle in forbidden:
            self.assertNotIn(needle, report)
        self.assertIsNone(re.search(r"sk-[A-Za-z0-9_-]{20,}", report))

    def test_claude_knowledge_modding_matrix_report_has_actionable_structure(
        self,
    ) -> None:
        report = CLAUDE_KNOWLEDGE_MODDING_MATRIX.read_text(encoding="utf-8")

        expected_sections = [
            "# Claude knowledge and modding matrix",
            "## Short version",
            "## Run matrix",
            "## Verdict table",
            "## Failure patterns",
            "## Knowledge result",
            "## Modding result",
            "## Follow-up status",
            "## Privacy note",
        ]
        last_index = -1
        for section in expected_sections:
            index = report.find(section)
            self.assertNotEqual(index, -1)
            self.assertGreater(index, last_index)
            last_index = index

        self.assertIn("`cities2-knowledge-office-demand`: `no-skill` failed 3/3", report)
        self.assertIn("`with-cities2-knowledge` | 203 | pass", report)
        self.assertIn("`cities2-modding-workflow-safe-handoff`: `no-skill` failed 3/3", report)
        self.assertIn("`with-cities2-modding` failed 3/3", report)
        self.assertIn("question-style readiness heading", report)
        self.assertIn("not proven by this matrix", report)

    def test_claude_knowledge_modding_matrix_report_avoids_raw_artifacts_and_private_paths(
        self,
    ) -> None:
        report = CLAUDE_KNOWLEDGE_MODDING_MATRIX.read_text(encoding="utf-8")

        forbidden = [
            "coding-agent-tool-calls.jsonl",
            "transcript.txt",
            "verdict.json",
            "coding-agent-config",
            "coding-agent-workdir",
            "C:" + "\\" + "Users",
            "\\" + "Users" + "\\",
            "/" + "Users" + "/",
            "OPENAI_API_KEY" + "=",
        ]
        for needle in forbidden:
            self.assertNotIn(needle, report)
        self.assertIsNone(re.search(r"sk-[A-Za-z0-9_-]{20,}", report))
