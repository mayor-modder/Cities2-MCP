from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


class EvalSummaryTests(unittest.TestCase):
    def test_generates_reviewable_digest_from_verdicts(self) -> None:
        from evals.runner.summary import generate_digest

        with tempfile.TemporaryDirectory(prefix="cities2-eval-summary-") as tmp:
            root = Path(tmp)
            first = root / "first" / "verdict.json"
            second = root / "second" / "verdict.json"
            first.parent.mkdir()
            second.parent.mkdir()
            first.write_text(
                json.dumps(
                    {
                        "metadata": {
                            "scenario_id": "cities2-debugging-runtime-no-logs",
                            "condition_id": "with-cities2-mod-debugging",
                            "trial": 2,
                            "backend_name": "codex",
                            "repo_commit": "abc123",
                            "run_started_at": "2026-06-06T18:00:00Z",
                            "skill_checksums": {
                                "cities2-mod-debugging": "sha256:skill",
                            },
                        },
                        "final": "fail",
                        "final_reason": "one or more post-checks failed",
                        "checks": [
                            {
                                "name": "handoff-present",
                                "phase": "post",
                                "status": "fail",
                                "detail": "no concrete next evidence handoff",
                            },
                            {
                                "name": "requests-runtime-evidence",
                                "phase": "post",
                                "status": "pass",
                                "detail": "asked for Modding.log",
                            },
                        ],
                        "trace_path": "coding-agent-tool-calls.jsonl",
                        "transcript_path": "transcript.txt",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            second.write_text(
                json.dumps(
                    {
                        "metadata": {
                            "scenario_id": "cities2-debugging-runtime-no-logs",
                            "condition_id": "no-skill",
                            "trial": 1,
                            "backend_name": "codex",
                            "repo_commit": "abc123",
                            "run_started_at": "2026-06-06T17:00:00Z",
                            "skill_checksums": {},
                        },
                        "final": "pass",
                        "final_reason": "all checks passed",
                        "checks": [],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            digest = generate_digest([first, second])

        self.assertIn("# Eval results digest", digest)
        self.assertIn("## Short version", digest)
        self.assertIn("Verdicts summarized: 2", digest)
        no_skill_row = (
            "| codex | cities2-debugging-runtime-no-logs | no-skill | 1 | pass | none |"
        )
        with_skill_row = (
            "| codex | cities2-debugging-runtime-no-logs | with-cities2-mod-debugging | 2 | fail | handoff-present |"
        )
        self.assertIn(no_skill_row, digest)
        self.assertIn(with_skill_row, digest)
        self.assertLess(digest.index(no_skill_row), digest.index(with_skill_row))
        self.assertIn("- `handoff-present`: fail=1", digest)
        self.assertIn("## Failure patterns", digest)
        self.assertIn("## Representative behavior", digest)
        self.assertIn("## Interpretation", digest)
        self.assertIn("## Follow-up status", digest)
        self.assertIn("## Privacy note", digest)
        self.assertIn("These results cover only the listed backend runs.", digest)
        self.assertNotIn(str(root), digest)
        self.assertNotIn("coding-agent-tool-calls.jsonl", digest)
        self.assertNotIn("transcript.txt", digest)

    def test_summarizes_verdicts_without_raw_paths(self) -> None:
        from evals.runner.summary import summarize_verdicts

        with tempfile.TemporaryDirectory(prefix="cities2-eval-summary-") as tmp:
            root = Path(tmp)
            run = root / "evals" / "results" / "run-1"
            run.mkdir(parents=True)
            verdict = {
                "metadata": {
                    "scenario_id": "cities2-debugging-runtime-no-logs",
                    "condition_id": "with-cities2-mod-debugging",
                    "trial": 1,
                    "backend_name": "codex",
                    "repo_commit": "abc123",
                    "skill_checksums": {
                        "cities2-mod-debugging": "sha256:1234",
                    },
                },
                "final": "pass",
                "final_reason": "all checks passed",
                "checks": [
                    {
                        "name": "requests-runtime-evidence",
                        "phase": "post",
                        "status": "pass",
                        "detail": "searched runtime evidence terms",
                    }
                ],
                "trace_path": "coding-agent-tool-calls.jsonl",
                "transcript_path": "transcript.txt",
            }
            (run / "verdict.json").write_text(
                json.dumps(verdict, indent=2) + "\n",
                encoding="utf-8",
            )

            summary = summarize_verdicts([run / "verdict.json"])

        self.assertIn("cities2-debugging-runtime-no-logs", summary)
        self.assertIn("with-cities2-mod-debugging", summary)
        self.assertIn("Backends: codex", summary)
        self.assertIn("pass=1", summary)
        self.assertIn("sha256:1234", summary)
        self.assertNotIn(str(root), summary)
        self.assertNotIn("coding-agent-tool-calls.jsonl", summary)
        self.assertNotIn("transcript.txt", summary)


if __name__ == "__main__":
    unittest.main()
