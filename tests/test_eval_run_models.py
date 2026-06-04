from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


class EvalRunModelsTests(unittest.TestCase):
    def test_verdict_serializes_metadata_and_checks(self) -> None:
        from evals.runner.models import CheckRecord, RunMetadata, Verdict

        metadata = RunMetadata(
            scenario_id="cities2-knowledge-office-demand",
            scenario_version="1",
            condition_id="with-cities2-knowledge",
            trial=1,
            backend_name="codex",
            backend_executable="codex",
            repo_commit="abc1234",
            runner_version="1",
            run_started_at="2026-06-01T12:00:00Z",
            skill_checksums={"cities2-knowledge": "sha256:1234"},
        )
        verdict = Verdict(
            metadata=metadata,
            final="pass",
            final_reason="all checks passed",
            checks=[
                CheckRecord(
                    name="source_status_called",
                    phase="post",
                    status="pass",
                    detail="source_status appeared before search",
                )
            ],
            trace_path="coding-agent-tool-calls.jsonl",
            transcript_path="transcript.txt",
        )

        data = verdict.to_dict()

        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["metadata"]["scenario_id"], "cities2-knowledge-office-demand")
        self.assertEqual(data["metadata"]["skill_checksums"]["cities2-knowledge"], "sha256:1234")
        self.assertEqual(data["checks"][0]["status"], "pass")

    def test_run_paths_are_inside_run_directory(self) -> None:
        from evals.runner.models import RunPaths

        with tempfile.TemporaryDirectory(prefix="cities2-eval-run-") as tmp:
            paths = RunPaths.from_run_dir(Path(tmp))

            self.assertEqual(paths.workdir, Path(tmp) / "coding-agent-workdir")
            self.assertEqual(paths.agent_home, Path(tmp) / "coding-agent-config")
            self.assertEqual(paths.raw_events, Path(tmp) / "codex-events.jsonl")
            self.assertEqual(paths.tool_calls, Path(tmp) / "coding-agent-tool-calls.jsonl")
            self.assertEqual(paths.transcript, Path(tmp) / "transcript.txt")
            self.assertEqual(paths.verdict, Path(tmp) / "verdict.json")

    def test_verdict_json_is_plain_data(self) -> None:
        from evals.runner.models import CheckRecord

        record = CheckRecord(
            name="agent_home_contained",
            phase="pre",
            status="fail",
            detail="agent home was outside the run directory",
        )

        json.dumps(record.to_dict())


if __name__ == "__main__":
    unittest.main()
