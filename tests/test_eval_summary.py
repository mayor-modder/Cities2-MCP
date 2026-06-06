from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


class EvalSummaryTests(unittest.TestCase):
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
